#!/usr/bin/env python3
"""Read-only run-level evidence cross-check helper for fixed-route replay.

Checks fields from:
- fixed-route status payload (`route_progress` + `software_proof` replay)
- optional task_record file (e.g. task orchestrator output)
- optional HIL evidence packet gate output for real-run alignment

The script is non-mutating and only reads JSON/jsonl input files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


# artifact 只表达本地/Docker 软件排练，边界常量集中放置，避免后续输出误写成真实 HIL。
REHEARSAL_ARTIFACT_SCHEMA = "trashbot.route_task_rehearsal_artifact"
REHEARSAL_ARTIFACT_VERSION = 1
REHEARSAL_EVIDENCE_BOUNDARY = "software_proof_docker_route_task_rehearsal_artifact_gate"

FIELD_SET = (
    "checkpoint",
    "current_index",
    "target",
    "failure_code",
    "evidence_ref",
)

NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "delivery_success",
)

# summary 会进入 sprint/OKR 证据材料，先做保守脱敏，避免把密钥或硬件细节扩散到 artifact。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(oss[_-]?secret|access[_-]?key[_-]?secret|ak|sk|root[_-]?password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_SERIAL]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_BAUD]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
)


def _load_json(path: str, label: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f'{label} not found: {p}')
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_json_lines(path: str, label: str):
    p = Path(path)
    if not p.exists():
        return []
    entries = []
    with p.open("r", encoding="utf-8") as f:
        for index, raw in enumerate(f, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                entries.append(json.loads(text))
            except json.JSONDecodeError as exc:
                raise ValueError(f'{label} line {index} invalid JSON: {exc}')
    return entries


def _find_task_record_by_evidence_ref(root: Path, evidence_ref: str):
    if not root.exists() or not root.is_dir():
        return ""
    needle = evidence_ref.strip()
    if not needle:
        return ""

    def matches_ref(payload: dict[str, Any]) -> bool:
        if str(payload.get("evidence_ref", "")).strip() == needle:
            return True
        if str(payload.get("result_path", "")).strip() == needle:
            return True
        route_progress = payload.get("route_progress")
        if isinstance(route_progress, dict):
            if str(route_progress.get("evidence_ref", "")).strip() == needle:
                return True
        nav_results = payload.get("nav_results")
        if isinstance(nav_results, list):
            for nav_result in reversed(nav_results):
                if not isinstance(nav_result, dict):
                    continue
                evidence = nav_result.get("evidence")
                if not isinstance(evidence, dict):
                    continue
                route_progress = evidence.get("route_progress")
                if isinstance(route_progress, dict):
                    if str(route_progress.get("evidence_ref", "")).strip() == needle:
                        return True
        return False

    for candidate in root.glob("*.json"):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if matches_ref(payload):
            return str(candidate)
    return ""


def _select_task_record_payload(path: str, task_record_dir: str, evidence_ref: str) -> tuple[dict[str, Any], str, str]:
    if path:
        return _load_json(path, "task_record"), str(path), ""
    if evidence_ref and task_record_dir:
        found = _find_task_record_by_evidence_ref(Path(task_record_dir), evidence_ref)
        if found:
            return _load_json(found, "task_record"), found, ""
        return (
            {},
            "",
            f"task_record_dir: no matching task_record for evidence_ref/result_path {evidence_ref!r}",
        )
    return {}, "", ""


def _select_hil_gate_payload(path: str) -> tuple[dict[str, Any], str]:
    if not path:
        return {}, ""
    try:
        payload = _load_json(path, "hil_gate_output")
    except FileNotFoundError as exc:
        return {}, f"hil_gate_output: {exc}"
    except json.JSONDecodeError as exc:
        return {}, f"hil_gate_output: invalid JSON: {exc}"
    if not isinstance(payload, dict):
        return {}, "hil_gate_output: payload is not a JSON object"
    return payload, ""


def _print_kv(label: str, value: Any):
    print(f"{label}: {_safe_value(value)}")


def _safe_text(value: Any) -> str:
    # 所有对外可见 summary 字段先经过统一过滤，保持 artifact 可分享。
    text = str(value)
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_safe_value(item) for item in value)
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_repr(value: Any) -> str:
    return repr(_safe_value(value))


def _dict_get(mapping: dict[str, Any], key: str, fallback: Any = ""):
    if not isinstance(mapping, dict):
        return fallback
    value = mapping.get(key)
    return fallback if value is None else value


def _compare(name: str, left: Any, right: Any, mismatches: list[str]) -> bool:
    if left == right:
        print(f"PASS {name}: {_safe_repr(left)}")
        return True
    mismatches.append(f"{name}: {_safe_repr(left)} != {_safe_repr(right)}")
    print(f"FAIL {name}: left={_safe_repr(left)} right={_safe_repr(right)}")
    return False


def _get_status_and_route_fields(status_payload: dict[str, Any], replay_payload: dict[str, Any]):
    status_route = status_payload.get("route_progress") if isinstance(status_payload, dict) else None
    if not isinstance(status_route, dict):
        status_route = {k: None for k in FIELD_SET}
    status_evidence_ref = str(
        _dict_get(status_payload, "evidence_ref") or _dict_get(status_route, "evidence_ref")
    )
    replay_fields = {field: _dict_get(replay_payload, field) for field in FIELD_SET}
    status_fields = {
        "checkpoint": _dict_get(status_payload, "checkpoint", _dict_get(status_route, "checkpoint")),
        "current_index": _dict_get(status_payload, "current_index", _dict_get(status_route, "current_index")),
        "target": _dict_get(status_payload, "target", _dict_get(status_route, "target")),
        "failure_code": _dict_get(status_payload, "failure_code", _dict_get(status_route, "failure_code")),
        "evidence_ref": status_evidence_ref,
    }
    route_progress_fields = {
        field: _dict_get(status_route, field) if field != "evidence_ref" else str(
            _dict_get(status_route, field)
        )
        for field in FIELD_SET
    }
    return status_fields, route_progress_fields, replay_fields


def _compare_task_record(
    task_record: dict[str, Any],
    status_payload: dict[str, Any],
    status_fields: dict[str, Any],
    mismatches: list[str],
):
    if not task_record:
        print("INFO task_record not provided: cross-check skipped")
        return

    task_evidence_ref = str(task_record.get("evidence_ref", "")).strip()
    nav_results = task_record.get("nav_results") if isinstance(task_record.get("nav_results"), list) else []
    evidence_from_nav: dict[str, Any] = {}
    if nav_results:
        last_nav = nav_results[-1]
        if isinstance(last_nav, dict):
            evidence_from_nav = last_nav.get("evidence", {}) if isinstance(last_nav.get("evidence"), dict) else {}
    route_progress_from_nav = evidence_from_nav.get("route_progress", {}) if isinstance(evidence_from_nav, dict) else {}
    task_route_progress = task_record.get("route_progress", {}) if isinstance(task_record.get("route_progress"), dict) else {}
    _compare(
        "task_record.evidence_ref == status.evidence_ref",
        task_evidence_ref,
        str(status_fields.get("evidence_ref") or ""),
        mismatches,
    )

    if task_route_progress:
        for field in FIELD_SET:
            if field in task_route_progress:
                _compare(
                    f"task_record.route_progress.{field}",
                    status_fields.get(field),
                    task_route_progress.get(field),
                    mismatches,
                )

    if route_progress_from_nav:
        for field in FIELD_SET:
            if field in route_progress_from_nav:
                _compare(
                    f"task_record.nav_results[-1].evidence.route_progress.{field}",
                    status_fields.get(field),
                    route_progress_from_nav.get(field),
                    mismatches,
                )

    if task_route_progress and route_progress_from_nav:
        for field in FIELD_SET:
            if field in task_route_progress and field in route_progress_from_nav:
                _compare(
                    f"task_record.route_progress == nav route_progress:{field}",
                    task_route_progress.get(field),
                    route_progress_from_nav.get(field),
                    mismatches,
                )
    elif not task_route_progress and not route_progress_from_nav:
        mismatches.append("task_record.route_progress: missing")
        mismatches.append("task_record.nav_results[-1].evidence.route_progress: missing")
        print("FAIL task_record.route_progress: missing")
        print("FAIL task_record.nav_results[-1].evidence.route_progress: missing")


def _task_record_summary(task_record: dict[str, Any], resolved_task_record: str, lookup_mismatch: str) -> dict[str, Any]:
    nav_results = task_record.get("nav_results") if isinstance(task_record.get("nav_results"), list) else []
    evidence_from_nav: dict[str, Any] = {}
    if nav_results and isinstance(nav_results[-1], dict):
        maybe_evidence = nav_results[-1].get("evidence")
        evidence_from_nav = maybe_evidence if isinstance(maybe_evidence, dict) else {}
    return {
        "provided": bool(task_record),
        "resolved_task_record": _safe_text(resolved_task_record) if resolved_task_record else "",
        "lookup_status": "missing" if lookup_mismatch else ("found" if resolved_task_record else "not_provided"),
        "lookup_detail": _safe_text(lookup_mismatch) if lookup_mismatch else "",
        "task_id": _safe_text(task_record.get("task_id", "")) if isinstance(task_record, dict) else "",
        "evidence_ref": _safe_text(task_record.get("evidence_ref", "")) if isinstance(task_record, dict) else "",
        "final_status": _safe_text(task_record.get("final_status", "")) if isinstance(task_record, dict) else "",
        "failure_code": _safe_text(task_record.get("failure_code", "")) if isinstance(task_record, dict) else "",
        "has_route_progress": isinstance(task_record.get("route_progress"), dict) and bool(task_record.get("route_progress")),
        "has_nav_route_progress": isinstance(evidence_from_nav.get("route_progress"), dict)
        and bool(evidence_from_nav.get("route_progress")),
    }


def _compare_hil_gate_output(
    hil_gate_output: dict[str, Any],
    gate_load_mismatch: str,
    gate_path: str,
    evidence_ref: str,
    mismatches: list[str],
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "provided": bool(gate_path),
        "status": "not_provided",
        "alignment_status": "not_proven",
        "evidence_ref": "",
        "evidence_ref_match": False,
        "detail": "not real HIL; HIL gate output not provided",
    }
    print("\nHIL gate -> run alignment")
    if not gate_path:
        print("INFO hil_gate_output not provided: route/task alignment remains software proof only")
        return summary

    print(f"hil_gate_output: {_safe_text(gate_path)}")
    if gate_load_mismatch:
        summary["status"] = "load_failed"
        summary["detail"] = _safe_text(f"not real HIL; {gate_load_mismatch}")
        mismatches.append(_safe_text(gate_load_mismatch))
        print(f"FAIL {_safe_text(gate_load_mismatch)}")
        return summary

    status = str(hil_gate_output.get("status", "")).strip()
    gate_evidence_ref = str(hil_gate_output.get("evidence_ref") or "").strip()
    blocked_reason = str(hil_gate_output.get("blocked_reason") or "").strip()
    failures = hil_gate_output.get("failures")
    failure_detail = failures if isinstance(failures, list) else []
    summary["status"] = _safe_text(status or "missing")
    summary["evidence_ref"] = _safe_text(gate_evidence_ref)

    if not status:
        mismatches.append("hil_gate_output.status: missing")
        print("FAIL hil_gate_output.status: missing")
    elif status == "hil_pass":
        summary["alignment_status"] = "hil_pass_pending_ref_check"
        summary["detail"] = "HIL gate reports hil_pass; evidence_ref still must match"
        print("PASS hil_gate_output.status: 'hil_pass'")
    elif status == "blocked":
        detail = blocked_reason or ", ".join(str(item) for item in failure_detail) or "blocked"
        summary["detail"] = _safe_text(f"not real HIL; blocked ({detail})")
        mismatches.append(_safe_text(f"hil_gate_output.status: blocked ({detail})"))
        print(f"FAIL hil_gate_output.status: blocked ({_safe_text(detail)})")
    elif status == "software_proof":
        detail = blocked_reason or "software proof only; not real HIL"
        summary["detail"] = _safe_text(f"not real HIL; software proof only ({detail})")
        mismatches.append(_safe_text(f"hil_gate_output.status: software proof only ({detail})"))
        print(f"FAIL hil_gate_output.status: software proof only ({_safe_text(detail)})")
    else:
        summary["detail"] = _safe_text(f"not real HIL; unsupported HIL gate status {status!r}")
        mismatches.append(f"hil_gate_output.status: unsupported {_safe_repr(status)}")
        print(f"FAIL hil_gate_output.status: unsupported {_safe_repr(status)}")

    if not gate_evidence_ref:
        mismatches.append("hil_gate_output.evidence_ref: missing")
        print("FAIL hil_gate_output.evidence_ref: missing")
        return summary

    ref_match = _compare(
        "hil_gate_output.evidence_ref == run evidence_ref",
        gate_evidence_ref,
        evidence_ref,
        mismatches,
    )
    summary["evidence_ref_match"] = ref_match
    if status == "hil_pass" and ref_match:
        summary["alignment_status"] = "hil_pass_aligned"
        summary["detail"] = "hil_pass gate is evidence_ref aligned; route/task artifact boundary remains software proof"
    elif status == "hil_pass":
        summary["alignment_status"] = "not_proven"
        summary["detail"] = "not real aligned HIL; hil_pass evidence_ref did not match run evidence_ref"
    return summary


def _route_status_summary(
    status_payload: dict[str, Any],
    route_status_file: str,
    replay_path: str,
    replay_rows: list[dict[str, Any]],
    status_fields: dict[str, Any],
    route_progress_fields: dict[str, Any],
) -> dict[str, Any]:
    software_proof = status_payload.get("software_proof") if isinstance(status_payload.get("software_proof"), dict) else {}
    return {
        "route_status_file": _safe_text(route_status_file),
        "state": _safe_text(status_payload.get("state", "")),
        "status": _safe_text(status_payload.get("status", "")),
        "mode": _safe_text(status_payload.get("mode", "")),
        "route_contract_version": _safe_text(status_payload.get("route_contract_version", "")),
        "route_id": _safe_text(status_payload.get("route_id", "")),
        "checkpoint": _safe_value(status_fields.get("checkpoint")),
        "current_index": _safe_value(status_fields.get("current_index")),
        "target": _safe_value(status_fields.get("target")),
        "failure_code": _safe_value(status_fields.get("failure_code")),
        "route_progress": _safe_value(route_progress_fields),
        "software_proof": {
            "type": _safe_text(software_proof.get("type", "")),
            "artifact_format": _safe_text(software_proof.get("artifact_format", "")),
            "artifact_path": _safe_text(replay_path),
            "evidence_ref": _safe_text(software_proof.get("evidence_ref", "")),
            "replay_lines": len(replay_rows),
        },
    }


def _write_rehearsal_artifact(
    artifact_path: str,
    evidence_ref: str,
    route_summary: dict[str, Any],
    task_summary: dict[str, Any],
    software_mismatches: list[str],
    hil_mismatches: list[str],
    hil_summary: dict[str, Any],
) -> None:
    p = Path(artifact_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    # pass 只看 status/replay/task_record 软件对账，HIL 另列，防止 blocked HIL 拉低本地复账产物。
    software_pass = not software_mismatches
    hil_not_proven = hil_summary.get("alignment_status") != "hil_pass_aligned"
    not_proven = list(NOT_PROVEN)
    if not hil_not_proven:
        not_proven = [item for item in not_proven if item != "real_hil_pass"]
    artifact = {
        "schema": REHEARSAL_ARTIFACT_SCHEMA,
        "schema_version": REHEARSAL_ARTIFACT_VERSION,
        "evidence_boundary": REHEARSAL_EVIDENCE_BOUNDARY,
        "evidence_ref": _safe_text(evidence_ref),
        "route_status_summary": route_summary,
        "task_record_summary": task_summary,
        "crosscheck_status": {
            "status": "pass" if software_pass else "fail",
            "scope": "status/replay/task_record software alignment only",
            "software_mismatches": [_safe_text(item) for item in software_mismatches],
            "artifact_pass_does_not_prove": list(NOT_PROVEN),
        },
        "hil_alignment_status": {
            **_safe_value(hil_summary),
            "mismatches": [_safe_text(item) for item in hil_mismatches],
            "not_real_hil_when_status_is_missing_blocked_or_software_proof": hil_not_proven,
        },
        "not_proven": not_proven,
    }
    p.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"route/task rehearsal artifact: {_safe_text(str(p))}")


def _derive_replay_path(status_payload: dict[str, Any]) -> str:
    if isinstance(status_payload, dict):
        software_proof = _dict_get(status_payload, "software_proof", {})
        if isinstance(software_proof, dict):
            artifact_path = _dict_get(software_proof, "artifact_path", "")
            if artifact_path:
                return str(artifact_path)
    status_file = _dict_get(status_payload, "debug_status_file")
    if status_file:
        return f"{status_file}.software_proof.route_replay.jsonl"
    return ""


def run_crosscheck(
    route_status_file: str,
    task_record: str,
    task_record_dir: str,
    expected_evidence_ref: str,
    hil_gate_output: str,
    rehearsal_artifact: str,
) -> int:
    software_mismatches: list[str] = []
    hil_mismatches: list[str] = []
    status_payload = _load_json(route_status_file, "route_status")
    if not isinstance(status_payload, dict):
        raise ValueError("route_status payload is not a JSON object")

    status_evidence_ref = str(
        _dict_get(status_payload, "evidence_ref")
        or _dict_get(status_payload, "software_proof", {}).get("evidence_ref", "")
    ).strip()

    evidence_ref = expected_evidence_ref.strip() or status_evidence_ref or str(route_status_file)
    print(f"evidence_ref: {_safe_text(evidence_ref)}")

    replay_path = _derive_replay_path(status_payload)
    replay_rows = _load_json_lines(replay_path, f"route_replay:{replay_path}")
    if replay_rows:
        print(f"route_replay_lines: {len(replay_rows)}")
        latest_replay = replay_rows[-1]
    else:
        print(f"WARN route_replay file missing or empty: {_safe_text(replay_path)}")
        latest_replay = {}

    status_fields, route_progress_fields, replay_fields = _get_status_and_route_fields(
        status_payload,
        latest_replay,
    )

    print("\nRoute status -> progress alignment")
    for field in FIELD_SET:
        _compare(
            f"status vs route_progress:{field}",
            status_fields.get(field),
            route_progress_fields.get(field),
            software_mismatches,
        )

    print("\nReplay -> status progress alignment")
    for field in FIELD_SET:
        _compare(
            f"status:{field} vs replay:{field}",
            status_fields.get(field),
            replay_fields.get(field),
            software_mismatches,
        )

    if expected_evidence_ref:
        _compare(
            "provided evidence_ref equals status.evidence_ref",
            expected_evidence_ref,
            status_evidence_ref,
            software_mismatches,
        )

    task_payload, resolved_task_record, task_record_lookup_mismatch = _select_task_record_payload(
        task_record,
        task_record_dir,
        evidence_ref,
    )
    print(f"\ntask_record: {_safe_text(resolved_task_record) if resolved_task_record else 'not provided'}")
    if task_record_lookup_mismatch:
        software_mismatches.append(_safe_text(task_record_lookup_mismatch))
        print(f"FAIL {_safe_text(task_record_lookup_mismatch)}")
    _compare_task_record(task_payload, status_payload, status_fields, software_mismatches)

    gate_payload, gate_load_mismatch = _select_hil_gate_payload(hil_gate_output)
    hil_summary = _compare_hil_gate_output(
        gate_payload,
        gate_load_mismatch,
        hil_gate_output,
        evidence_ref,
        hil_mismatches,
    )

    if rehearsal_artifact:
        route_summary = _route_status_summary(
            status_payload,
            route_status_file,
            replay_path,
            replay_rows,
            status_fields,
            route_progress_fields,
        )
        task_summary = _task_record_summary(
            task_payload,
            resolved_task_record,
            task_record_lookup_mismatch,
        )
        _write_rehearsal_artifact(
            rehearsal_artifact,
            evidence_ref,
            route_summary,
            task_summary,
            software_mismatches,
            hil_mismatches,
            hil_summary,
        )

    mismatches = software_mismatches + hil_mismatches
    print(
        f"\nCHECK summary: mismatches={len(mismatches)} "
        f"software_mismatches={len(software_mismatches)} hil_mismatches={len(hil_mismatches)}"
    )
    if mismatches:
        print("\nMismatch detail:")
        for item in mismatches:
            print(f"- {_safe_text(item)}")
        if rehearsal_artifact and not software_mismatches:
            print("INFO artifact pass remains software proof only; HIL alignment is not_proven")
            return 0
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Check fixed-route status/replay/task_record alignment")
    parser.add_argument("route_status", help="fixed_route status json file")
    parser.add_argument("--task-record", dest="task_record", default="", help="task_record json file")
    parser.add_argument(
        "--task-record-dir",
        default="",
        help="folder to auto-pick task_record by evidence_ref/result_path when --task-record is absent",
    )
    parser.add_argument("--evidence-ref", default="", help="expected evidence_ref override for run-level alignment")
    parser.add_argument(
        "--hil-gate-output",
        default="",
        help="hil_evidence_packet_gate.py JSON output file for real-run HIL alignment",
    )
    parser.add_argument(
        "--rehearsal-artifact",
        default="",
        help="write a route/task rehearsal artifact JSON with software-proof evidence boundary",
    )
    args = parser.parse_args()

    task_record_path = args.task_record
    if args.task_record and task_record_path:
        task_record_path = str(Path(task_record_path).expanduser())
    task_record_dir = str(Path(args.task_record_dir).expanduser()) if args.task_record_dir else ""

    return run_crosscheck(
        str(Path(args.route_status).expanduser()),
        task_record_path,
        task_record_dir,
        args.evidence_ref,
        str(Path(args.hil_gate_output).expanduser()) if args.hil_gate_output else "",
        str(Path(args.rehearsal_artifact).expanduser()) if args.rehearsal_artifact else "",
    )


if __name__ == "__main__":
    raise SystemExit(main())
