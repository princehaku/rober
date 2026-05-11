#!/usr/bin/env python3
"""Read-only run-level evidence cross-check helper for fixed-route replay.

Checks fields from:
- fixed-route status payload (`route_progress` + `software_proof` replay)
- optional task_record file (e.g. task orchestrator output)

The script is non-mutating and only reads JSON/jsonl input files.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


FIELD_SET = (
    "checkpoint",
    "current_index",
    "target",
    "failure_code",
    "evidence_ref",
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
    for candidate in root.glob("*.json"):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if str(payload.get("evidence_ref", "")).strip() == needle:
            return str(candidate)
        if str(payload.get("result_path", "")).strip() == needle:
            return str(candidate)
    return ""


def _select_task_record_payload(path: str, task_record_dir: str, evidence_ref: str) -> tuple[dict[str, Any], str]:
    if path:
        return _load_json(path, "task_record"), str(path)
    if evidence_ref and task_record_dir:
        found = _find_task_record_by_evidence_ref(Path(task_record_dir), evidence_ref)
        if found:
            return _load_json(found, "task_record"), found
    if evidence_ref:
        task_dir = Path.home() / ".ros" / "trashbot_tasks"
        found = _find_task_record_by_evidence_ref(task_dir, evidence_ref)
        if found:
            return _load_json(found, "task_record"), found
    return {}, ""


def _print_kv(label: str, value: Any):
    print(f"{label}: {value}")


def _dict_get(mapping: dict[str, Any], key: str, fallback: Any = ""):
    if not isinstance(mapping, dict):
        return fallback
    value = mapping.get(key)
    return fallback if value is None else value


def _compare(name: str, left: Any, right: Any, mismatches: list[str]) -> bool:
    if left == right:
        print(f"PASS {name}: {left!r}")
        return True
    mismatches.append(f"{name}: {left!r} != {right!r}")
    print(f"FAIL {name}: left={left!r} right={right!r}")
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
) -> int:
    mismatches: list[str] = []
    status_payload = _load_json(route_status_file, "route_status")
    if not isinstance(status_payload, dict):
        raise ValueError("route_status payload is not a JSON object")

    status_evidence_ref = str(
        _dict_get(status_payload, "evidence_ref")
        or _dict_get(status_payload, "software_proof", {}).get("evidence_ref", "")
    ).strip()

    evidence_ref = expected_evidence_ref.strip() or status_evidence_ref or str(route_status_file)
    print(f"evidence_ref: {evidence_ref}")

    replay_path = _derive_replay_path(status_payload)
    replay_rows = _load_json_lines(replay_path, f"route_replay:{replay_path}")
    if replay_rows:
        print(f"route_replay_lines: {len(replay_rows)}")
        latest_replay = replay_rows[-1]
    else:
        print(f"WARN route_replay file missing or empty: {replay_path}")
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
            mismatches,
        )

    print("\nReplay -> status progress alignment")
    for field in FIELD_SET:
        _compare(
            f"status:{field} vs replay:{field}",
            status_fields.get(field),
            replay_fields.get(field),
            mismatches,
        )

    if expected_evidence_ref:
        _compare(
            "provided evidence_ref equals status.evidence_ref",
            expected_evidence_ref,
            status_evidence_ref,
            mismatches,
        )

    task_payload, resolved_task_record = _select_task_record_payload(task_record, task_record_dir, evidence_ref)
    print(f"\ntask_record: {resolved_task_record or 'not provided'}")
    _compare_task_record(task_payload, status_payload, status_fields, mismatches)

    print(f"\nCHECK summary: mismatches={len(mismatches)}")
    if mismatches:
        print("\nMismatch detail:")
        for item in mismatches:
            print(f"- {item}")
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
    )


if __name__ == "__main__":
    raise SystemExit(main())
