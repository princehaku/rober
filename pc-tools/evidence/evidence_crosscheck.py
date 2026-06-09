#!/usr/bin/env python3
"""软件侧 fixed-route 回盘对账工具（只读）。

用于核对 status、route_replay 与 task_record 的同 evidence_ref 字段链路。
本脚本只做软件 proof 对账，不代表真实巡航、真实 HIL、真实投递成功。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

# 复盘证据始终是软件侧边界，不允许把 pass 直接映射为现场成功。
REHEARSAL_ARTIFACT_SCHEMA = "trashbot.route_task_rehearsal_artifact"
REHEARSAL_ARTIFACT_VERSION = 1
REHEARSAL_EVIDENCE_BOUNDARY = "software_proof_docker_route_task_rehearsal_artifact_gate"

# 只做 route/task 回盘所需的最小字段集合，避免 overfit 到现场硬件形态。
FIELD_SET = (
    "checkpoint",
    "current_index",
    "target",
    "failure_code",
    "evidence_ref",
)

# 这类证据仍保持 not_proven，即便 software 对账通过。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "wave_rover_motion",
    "real_serial_or_uart_feedback",
    "real_hil_pass",
    "delivery_success",
)

# 在摘要和 artifact 中统一脱敏，避免把串口、凭证、traceback 泄露到可共享材料。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^\s,]+"), "Authorization: [REDACTED]"),
    (
        re.compile(
            r"(?i)\b(oss[_-]?secret|access[_-]?key[_-]?secret|ak|sk|root[_-]?password)\b\s*[:=]\s*[^\s,]+"
        ),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^\s,]+"),
        r"\1_url=[REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^\s,]+"),
        "[REDACTED_URL]",
    ),
    (
        re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"),
        "/dev/[REDACTED_SERIAL]",
    ),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_BAUD]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
)


def _safe_text(value: Any) -> str:
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


def _load_json(path: str, label: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"{label} not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} must be a JSON object")
    return payload


def _load_json_lines(path: str, label: str) -> list[dict[str, Any]]:
    # route replay 用 jsonl 保存逐行状态，缺失时按可读方式降级。
    file_path = Path(path)
    if not file_path.exists():
        print(f"WARN {label}: {_safe_text(file_path)} missing; treat as empty replay")
        return []
    rows: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as stream:
        for index, raw in enumerate(stream, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{label} line {index} invalid JSON: {exc}")
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {index} is not an object")
            rows.append(value)
    return rows


def _derive_replay_path(status_payload: dict[str, Any]) -> str:
    if isinstance(status_payload, dict):
        software_proof = _dict_get(status_payload, "software_proof", {})
        if isinstance(software_proof, dict):
            artifact_path = _dict_get(software_proof, "artifact_path", "")
            if artifact_path:
                return str(artifact_path)
        debug_status_file = _dict_get(status_payload, "debug_status_file", "")
        if debug_status_file:
            return f"{debug_status_file}.software_proof.route_replay.jsonl"
    return ""


def _find_task_record_by_evidence_ref(task_record_dir: Path, evidence_ref: str) -> str:
    # 按 evidence_ref/result_path/top-level 与 nav 里的 route_progress 三类入口回放定位同一 run 的任务记录。
    if not task_record_dir.exists() or not task_record_dir.is_dir():
        return ""
    needle = evidence_ref.strip()
    if not needle:
        return ""

    def _has_ref(payload: dict[str, Any], expected_ref: str) -> bool:
        if str(payload.get("evidence_ref", "")).strip() == expected_ref:
            return True
        if str(payload.get("result_path", "")).strip() == expected_ref:
            return True
        route_progress = payload.get("route_progress")
        if isinstance(route_progress, dict):
            if str(route_progress.get("evidence_ref", "")).strip() == expected_ref:
                return True
        nav_results = payload.get("nav_results")
        if isinstance(nav_results, list):
            for nav_result in reversed(nav_results):
                if not isinstance(nav_result, dict):
                    continue
                evidence = nav_result.get("evidence")
                if not isinstance(evidence, dict):
                    continue
                nav_route_progress = evidence.get("route_progress")
                if isinstance(nav_route_progress, dict):
                    if str(nav_route_progress.get("evidence_ref", "")).strip() == expected_ref:
                        return True
        return False

    for candidate in task_record_dir.glob("*.json"):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if _has_ref(payload, needle):
            return str(candidate)
    return ""


def _select_task_record_payload(
    task_record: str,
    task_record_dir: str,
    evidence_ref: str,
) -> tuple[dict[str, Any], str, str]:
    if task_record:
        return _load_json(task_record, "task_record"), str(task_record), ""
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
        payload = _load_json(path, "hil_gate")
    except FileNotFoundError as exc:
        return {}, f"hil_gate: {exc}"
    except ValueError as exc:
        return {}, f"hil_gate: {exc}"
    if not isinstance(payload, dict):
        return {}, "hil_gate: payload is not a JSON object"
    return payload, ""


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


def _extract_last_route_progress(task_record: dict[str, Any]) -> dict[str, Any]:
    nav_results = task_record.get("nav_results")
    if not isinstance(nav_results, list) or not nav_results:
        return {}
    last_nav = nav_results[-1]
    if not isinstance(last_nav, dict):
        return {}
    evidence = last_nav.get("evidence")
    if not isinstance(evidence, dict):
        return {}
    route_progress = evidence.get("route_progress")
    return route_progress if isinstance(route_progress, dict) else {}


def _compare_task_record(
    task_record: dict[str, Any],
    status_fields: dict[str, Any],
    mismatches: list[str],
    expected_evidence_ref: str,
) -> None:
    if not task_record:
        print("INFO task_record not provided: cross-check skipped")
        return

    task_evidence_ref = str(task_record.get("evidence_ref", "")).strip()
    task_route_progress = task_record.get("route_progress") if isinstance(task_record.get("route_progress"), dict) else {}
    route_progress_from_nav = _extract_last_route_progress(task_record)

    # 顶层 evidence_ref 为空时，不把该 task_record 视作同一 run 的合规证据源。
    # 这样可避免“字段都能对上但 run 身份不清”导致误判。
    if task_evidence_ref:
        _compare(
            "task_record.evidence_ref == status.evidence_ref",
            task_evidence_ref,
            str(status_fields.get("evidence_ref") or ""),
            mismatches,
        )
    elif expected_evidence_ref:
        # 兼容测试场景：显式按 evidence_ref 选中的文件若缺顶层 evidence_ref，直接判为不合规。
        mismatches.append(
            "task_record.nav_results[-1].evidence.route_progress.evidence_ref missing top-level evidence_ref"
        )
        print(
            "FAIL task_record.nav_results[-1].evidence.route_progress.evidence_ref: "
            "missing top-level evidence_ref"
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
        if not task_route_progress and expected_evidence_ref and task_evidence_ref:
            _compare(
                "task_record.evidence_ref == status.evidence_ref",
                task_evidence_ref,
                str(status_fields.get("evidence_ref") or ""),
                mismatches,
            )
    elif not task_route_progress:
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
    hil_mismatches: list[str],
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
        print("INFO hil_gate not provided: route/task alignment remains software proof only")
        return summary

    print(f"hil_gate: {_safe_text(gate_path)}")
    if gate_load_mismatch:
        summary["status"] = "load_failed"
        summary["detail"] = _safe_text(f"not real HIL; {gate_load_mismatch}")
        hil_mismatches.append(_safe_text(gate_load_mismatch))
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
        hil_mismatches.append("hil_gate.status: missing")
        print("FAIL hil_gate.status: missing")
    elif status == "hil_pass":
        # 即使 HIL 通过，也不能让 software proof 的 pass 自动升级为真实实跑成功。
        summary["alignment_status"] = "hil_pass_pending_ref_check"
        summary["detail"] = "HIL gate status is hil_pass; evidence_ref still must match."
        print("PASS hil_gate.status: 'hil_pass'")
    elif status == "blocked":
        detail = blocked_reason or ", ".join(str(item) for item in failure_detail) or "blocked"
        summary["detail"] = _safe_text(f"not real HIL; blocked ({detail})")
        hil_mismatches.append(_safe_text(f"hil_gate.status: blocked ({detail})"))
        print(f"FAIL hil_gate.status: blocked ({_safe_text(detail)})")
    elif status == "software_proof":
        detail = blocked_reason or "software proof only; not real HIL"
        summary["detail"] = _safe_text(f"not real HIL; software proof only ({detail})")
        hil_mismatches.append(_safe_text(f"hil_gate.status: software proof only ({detail})"))
        print(f"FAIL hil_gate.status: software proof only ({_safe_text(detail)})")
    else:
        summary["detail"] = _safe_text(f"not real HIL; unsupported HIL gate status {status!r}")
        hil_mismatches.append(f"hil_gate.status: unsupported {_safe_repr(status)}")
        print(f"FAIL hil_gate.status: unsupported {_safe_repr(status)}")

    if not gate_evidence_ref:
        hil_mismatches.append("hil_gate.evidence_ref: missing")
        print("FAIL hil_gate.evidence_ref: missing")
        return summary

    _compare(
        "hil_gate.evidence_ref == run evidence_ref",
        gate_evidence_ref,
        evidence_ref,
        hil_mismatches,
    )

    if status == "hil_pass" and hil_mismatches == [] and str(evidence_ref) == gate_evidence_ref:
        summary["alignment_status"] = "hil_pass_aligned"
        summary["evidence_ref_match"] = True
        summary["detail"] = "hil_pass gate is evidence_ref aligned; boundary remains software proof"
    else:
        summary["alignment_status"] = "not_proven"
        if status == "hil_pass":
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
    # Artifact 只表达 status/replay/task_record 软件复账，避免把 real-route/hil 声明混进软件排练材料。
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


def _match_expected_evidence_ref(status_payload: dict[str, Any], expected_evidence_ref: str) -> str:
    status_evidence_ref = str(
        _dict_get(status_payload, "evidence_ref")
        or _dict_get(status_payload, "software_proof", {}).get("evidence_ref", "")
    ).strip()
    return expected_evidence_ref.strip() or status_evidence_ref or ""


def _resolve_argument_aliases(args: argparse.Namespace) -> tuple[str, str, str, str]:
    task_record_path = args.task_record.strip() if isinstance(args.task_record, str) else ""
    task_record_dir = args.task_record_dir.strip() if isinstance(args.task_record_dir, str) else ""
    hil_gate = args.hil_gate.strip() if isinstance(args.hil_gate, str) else ""
    rehearsal_artifact = args.output_artifact.strip() if isinstance(args.output_artifact, str) else ""
    return task_record_path, task_record_dir, hil_gate, rehearsal_artifact


def run_crosscheck(
    route_status_file: str,
    task_record_path: str,
    task_record_dir: str,
    expected_evidence_ref: str,
    hil_gate: str,
    output_artifact: str,
) -> int:
    software_mismatches: list[str] = []
    hil_mismatches: list[str] = []

    try:
        status_payload = _load_json(route_status_file, "route_status")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {_safe_text(exc)}")
        return 1
    if not isinstance(status_payload, dict):
        print("FAIL route_status payload is not a JSON object")
        return 1

    status_evidence_ref = _match_expected_evidence_ref(status_payload, expected_evidence_ref)
    evidence_ref = status_evidence_ref or str(route_status_file)
    if expected_evidence_ref:
        _compare("provided evidence_ref equals status.evidence_ref", expected_evidence_ref, status_evidence_ref, software_mismatches)
    print(f"evidence_ref: {_safe_text(evidence_ref)}")

    replay_path = _derive_replay_path(status_payload)
    try:
        replay_rows = _load_json_lines(replay_path, f"route_replay:{replay_path}")
    except ValueError as exc:
        print(f"FAIL {_safe_text(exc)}")
        return 1

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

    task_payload, resolved_task_record, task_record_lookup_mismatch = _select_task_record_payload(
        task_record_path,
        task_record_dir,
        evidence_ref,
    )
    print(f"\ntask_record: {_safe_text(resolved_task_record) if resolved_task_record else 'not provided'}")
    if task_record_lookup_mismatch:
        software_mismatches.append(_safe_text(task_record_lookup_mismatch))
        print(f"FAIL {_safe_text(task_record_lookup_mismatch)}")
    _compare_task_record(task_payload, status_fields, software_mismatches, expected_evidence_ref)

    hil_payload, gate_load_mismatch = _select_hil_gate_payload(hil_gate)
    hil_summary = _compare_hil_gate_output(
        hil_payload,
        gate_load_mismatch,
        hil_gate,
        evidence_ref,
        hil_mismatches,
    )

    if output_artifact:
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
            output_artifact,
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
        if output_artifact and not software_mismatches:
            # 软件复账通过时仍可产出 artifact；HIL 对齐失败不代表现场完成，仅记录 not_proven。
            print("INFO artifact pass remains software proof only; HIL alignment is not_proven")
            return 0
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only run-level evidence cross-check for fixed-route software proof."
    )
    parser.add_argument("route_status", help="fixed-route status json file")
    parser.add_argument(
        "--task-record",
        default="",
        help="task_record json file",
    )
    parser.add_argument(
        "--task-record-dir",
        default="",
        help="folder to pick task_record by evidence_ref/result_path when --task-record is absent",
    )
    parser.add_argument(
        "--evidence-ref",
        default="",
        help="expected evidence_ref override for run-level alignment",
    )
    parser.add_argument(
        "--hil-gate",
        "--hil-gate-output",
        default="",
        dest="hil_gate",
        help="hil evidence packet gate JSON output file",
    )
    parser.add_argument(
        "--output-artifact",
        "--rehearsal-artifact",
        default="",
        dest="output_artifact",
        help="write route/task rehearsal artifact JSON with software-proof evidence boundary",
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    task_record_path, task_record_dir, hil_gate, output_artifact = _resolve_argument_aliases(args)
    return run_crosscheck(
        str(Path(args.route_status).expanduser()),
        task_record_path,
        task_record_dir,
        args.evidence_ref,
        str(Path(hil_gate).expanduser()) if hil_gate else "",
        str(Path(output_artifact).expanduser()) if output_artifact else "",
    )


if __name__ == "__main__":
    raise SystemExit(main())
