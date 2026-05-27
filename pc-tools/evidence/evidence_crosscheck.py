#!/usr/bin/env python3
"""task_record 兼容核对入口。

该脚本只恢复 onboard 测试依赖的最小 evidence_crosscheck 契约。
它不读取硬件、不执行 ROS2、不判断 HIL 通过，也不把 software proof 外推为交付成功。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REDACTIONS = (
    ("/dev/ttyUSB0", "/dev/[REDACTED_DEVICE]"),
    ("/dev/ttyACM0", "/dev/[REDACTED_DEVICE]"),
    ("115200", "[REDACTED_BAUDRATE]"),
)


def _sanitize(text: str) -> str:
    """脱敏硬件路径和波特率，避免 software proof 输出被误当成真实串口证据。"""
    safe = text
    for raw, replacement in REDACTIONS:
        safe = safe.replace(raw, replacement)
    return safe


def _load_json(path: Path) -> dict[str, Any]:
    """只读取 JSON 文件；坏 JSON 直接作为核对失败，而不是继续猜字段。"""
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: json root must be object")
    return value


def _route_progress(record: dict[str, Any]) -> dict[str, Any] | None:
    """task_record.route_progress 是主契约；nav_results 只用于错误定位提示。"""
    value = record.get("route_progress")
    return value if isinstance(value, dict) else None


def _nav_route_progress_ref(record: dict[str, Any]) -> str:
    """读取最后一次 nav route ref 只为解释漂移，不把它当作 task_record 顶层匹配依据。"""
    nav_results = record.get("nav_results")
    if not isinstance(nav_results, list) or not nav_results:
        return ""
    last = nav_results[-1]
    if not isinstance(last, dict):
        return ""
    evidence = last.get("evidence")
    if not isinstance(evidence, dict):
        return ""
    progress = evidence.get("route_progress")
    if not isinstance(progress, dict):
        return ""
    return str(progress.get("evidence_ref") or "")


def _find_task_record(task_record: str, task_record_dir: str, evidence_ref: str) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    """按显式文件优先，其次在目录内只用顶层 evidence_ref 找匹配记录。"""
    diagnostics: list[str] = []
    if task_record:
        path = Path(task_record)
        return path, _load_json(path), diagnostics

    if not task_record_dir:
        diagnostics.append("task_record: missing")
        return None, None, diagnostics

    directory = Path(task_record_dir)
    for path in sorted(directory.glob("*.json")):
        record = _load_json(path)
        if str(record.get("evidence_ref") or "") == evidence_ref:
            return path, record, diagnostics
        nav_ref = _nav_route_progress_ref(record)
        if nav_ref == evidence_ref:
            diagnostics.append("task_record.nav_results[-1].evidence.route_progress.evidence_ref matched but task_record.evidence_ref missing")

    diagnostics.append("no matching task_record")
    return None, None, diagnostics


def _status_route_progress(status: dict[str, Any]) -> dict[str, Any] | None:
    """status.route_progress 是 route debug 的主输入；缺失时保持 mismatch。"""
    value = status.get("route_progress")
    return value if isinstance(value, dict) else None


def _compare_route_progress(status: dict[str, Any], task_record: dict[str, Any] | None, evidence_ref: str) -> list[str]:
    """只比较测试契约需要的 evidence_ref 和 route_progress 存在性。"""
    mismatches: list[str] = []
    status_progress = _status_route_progress(status)
    if not isinstance(status_progress, dict):
        mismatches.append("status.route_progress: missing")
    elif str(status_progress.get("evidence_ref") or "") != evidence_ref:
        mismatches.append("status.route_progress.evidence_ref: mismatch")

    if task_record is None:
        return mismatches

    task_progress = _route_progress(task_record)
    if not isinstance(task_progress, dict):
        mismatches.append("task_record.route_progress: missing")
        nav_ref = _nav_route_progress_ref(task_record)
        if nav_ref:
            mismatches.append("task_record.nav_results[-1].evidence.route_progress.evidence_ref present but top-level route_progress missing")
        return mismatches

    if str(task_progress.get("evidence_ref") or "") != evidence_ref:
        mismatches.append("task_record.route_progress.evidence_ref: mismatch")
    return mismatches


def _hil_alignment(hil_gate_output: str) -> dict[str, Any]:
    """HIL gate 只生成 not_proven 对齐摘要；不复述串口路径或波特率。"""
    if not hil_gate_output:
        return {
            "alignment_status": "not_proven",
            "source": "not_provided",
            "blocked_reason": "hil_gate_output_not_provided",
        }
    try:
        gate = _load_json(Path(hil_gate_output))
    except Exception as exc:  # noqa: BLE001
        return {
            "alignment_status": "not_proven",
            "source": "read_error",
            "blocked_reason": _sanitize(str(exc)),
        }
    return {
        "alignment_status": "not_proven",
        "source": "software_proof_hil_gate_summary",
        "status": _sanitize(str(gate.get("status") or "blocked")),
        "blocked_reason": _sanitize(str(gate.get("blocked_reason") or "real_hil_pass_not_proven")),
    }


def _write_rehearsal_artifact(
    path: str,
    evidence_ref: str,
    mismatches: list[str],
    hil_gate_output: str,
) -> None:
    """写入只读 rehearsal artifact，明确 blocked HIL/not_proven 边界。"""
    if not path:
        return
    artifact = {
        "schema": "trashbot.route_task_rehearsal_artifact",
        "evidence_boundary": "software_proof_docker_route_task_rehearsal_artifact_gate",
        "source": "software_proof",
        "proof_status": "not_proven",
        "evidence_ref": evidence_ref,
        "crosscheck_status": {
            "status": "pass" if not mismatches else "fail",
            "mismatches": [_sanitize(item) for item in mismatches],
        },
        "hil_alignment_status": _hil_alignment(hil_gate_output),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "not_proven": [
            "real_hil_pass",
            "real_uart_feedback",
            "real_delivery_success",
        ],
    }
    Path(path).write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cross-check route status and task_record software proof.")
    parser.add_argument("status_json")
    parser.add_argument("--task-record", default="")
    parser.add_argument("--task-record-dir", default="")
    parser.add_argument("--evidence-ref", default="")
    parser.add_argument("--hil-gate-output", default="")
    parser.add_argument("--rehearsal-artifact", default="")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    status = _load_json(Path(args.status_json))
    evidence_ref = args.evidence_ref or str(status.get("evidence_ref") or "")
    task_path, task_record, diagnostics = _find_task_record(args.task_record, args.task_record_dir, evidence_ref)
    mismatches = [*diagnostics, *_compare_route_progress(status, task_record, evidence_ref)]

    print(f"status: {Path(args.status_json)}")
    print(f"task_record: {task_path if task_path else 'not_found'}")
    for item in mismatches:
        print(_sanitize(item))
    print(f"CHECK summary: mismatches={len(mismatches)}")

    _write_rehearsal_artifact(args.rehearsal_artifact, evidence_ref, mismatches, args.hil_gate_output)
    if args.rehearsal_artifact:
        print(f"route/task rehearsal artifact: {Path(args.rehearsal_artifact)}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
