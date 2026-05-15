#!/usr/bin/env python3
"""生成 elevator assist dry-run 主链路只读 rehearsal evidence artifact。

该 gate 只产出 Docker/local software proof，供 Robot task_orchestrator 在
dry-run 下按 phase evidence 只读消费。它不访问 ROS graph、Nav2 runtime、
真实电梯、硬件、外部云、OSS/CDN、DB/queue 或 4G 网络。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 单独命名，避免 Robot 把现场 execution pack 或旧 review artifact 当成本轮输入。
ARTIFACT_SCHEMA = "trashbot.elevator_assist_rehearsal_evidence.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_elevator_evidence_driven_mainline_gate"
SOURCE = "software_proof"

# Robot dry-run 只消费这五个阶段；缺阶段会让后续行为层无法稳定复现电梯主链路。
REQUIRED_PHASES = (
    "waiting_elevator_open",
    "entering_elevator",
    "requesting_floor_help",
    "waiting_target_floor",
    "exiting_elevator",
)

# not_proven 用机器可读 key 隔开 software proof 与真实上车、真实导航和真实交付。
NOT_PROVEN = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_record",
    "real_nav2_fixed_route_run",
    "real_robot_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 验收会检索这两个固定字段；人工复盘时也能直接看到 fail-closed 边界。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; elevator_assist_rehearsal_evidence_not_real_delivery=true"
)

# phone-safe summary 和 artifact 都不能扩散控制 topic、设备、凭证、路径或完整原始材料。
FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
    "token",
    "password",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

# 自由文本中不能出现 delivery/dropoff/cancel 完成类 claim，避免被误读为现场闭环。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)

# 输入字段只允许短安全 token；这样 evidence_ref 可以进入 task record 而不泄漏本机路径。
SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")
SAFE_FLOOR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,31}$")


def _utc_now() -> str:
    # UTC 时间便于 Docker/local 与后续 Robot task record 按同一时间轴复盘。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 本 gate 不接收自由 raw 材料，但仍统一转短文本，防止 None 或对象泄漏。
    text = str(value if value is not None else "").strip()
    return text[:240]


def _encoded(value: Any) -> str:
    # forbidden 和 success 检查用稳定 JSON，确保键和值都会被扫描。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 只要 artifact 内出现控制、设备、凭证或 raw 线索，就必须 fail closed。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim(value: Any) -> bool:
    # `delivery_success=false` 是允许字段；这里拦截的是自由文本完成声明和 hil_pass=true。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _safe_token(value: str, pattern: re.Pattern[str]) -> str:
    # 非法 token 不做猜测修复，返回空值交给 validation verdict 拦截。
    text = _safe_text(value)
    return text if pattern.fullmatch(text) else ""


def _phase_evidence(evidence_ref: str, target_floor: str) -> dict[str, dict[str, Any]]:
    # phase evidence 是 Robot dry-run 的主输入，不代表真实传感器、真实开门或真实到层。
    return {
        "waiting_elevator_open": {
            "phase": "waiting_elevator_open",
            "evidence_ref": evidence_ref,
            "evidence_state": "rehearsal_phase_declared_not_proven",
            "operator_observable": "door-open evidence must be supplied by a later field run",
            "robot_consumption": "dry_run_readonly_phase_event",
        },
        "entering_elevator": {
            "phase": "entering_elevator",
            "evidence_ref": evidence_ref,
            "evidence_state": "rehearsal_phase_declared_not_proven",
            "operator_observable": "entry path and stop path must be checked during the field run",
            "robot_consumption": "dry_run_readonly_phase_event",
        },
        "requesting_floor_help": {
            "phase": "requesting_floor_help",
            "evidence_ref": evidence_ref,
            "evidence_state": "rehearsal_phase_declared_not_proven",
            "target_floor": target_floor,
            "operator_observable": "human assistance note must confirm the requested target floor later",
            "robot_consumption": "dry_run_readonly_phase_event",
        },
        "waiting_target_floor": {
            "phase": "waiting_target_floor",
            "evidence_ref": evidence_ref,
            "evidence_state": "rehearsal_phase_declared_not_proven",
            "target_floor": target_floor,
            "operator_observable": "target-floor evidence must be supplied by a later field run",
            "robot_consumption": "dry_run_readonly_phase_event",
        },
        "exiting_elevator": {
            "phase": "exiting_elevator",
            "evidence_ref": evidence_ref,
            "evidence_state": "rehearsal_phase_declared_not_proven",
            "operator_observable": "exit path evidence must be supplied before any real delivery claim",
            "robot_consumption": "dry_run_readonly_phase_event",
        },
    }


def _failure(failure_phase: str, reason: str, manual_takeover_reason: str) -> dict[str, str] | None:
    # failure 存在时 Robot 必须 fail closed；不传则表示本地 rehearsal artifact 无失败注入。
    phase = _safe_token(failure_phase, SAFE_TOKEN_RE)
    if not phase:
        return None
    return {
        "phase": phase,
        "reason": _safe_text(reason) or "operator_marked_rehearsal_phase_blocked",
        "manual_takeover_reason": _safe_text(manual_takeover_reason) or "manual_takeover_required_before_field_motion",
    }


def _phone_safe_summary(
    verdict: str,
    evidence_ref: str,
    target_floor: str,
    phase_evidence: dict[str, dict[str, Any]],
    failure: dict[str, str] | None,
) -> dict[str, Any]:
    # summary 是 full-stack 和 Robot diagnostics 的只读面，字段短且不含 raw 控制材料。
    summary = {
        "schema": "trashbot.elevator_assist_rehearsal_evidence_summary.v1",
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": verdict,
        "evidence_ref": evidence_ref,
        "target_floor": target_floor,
        "same_evidence_ref_required": True,
        "phase_names": list(phase_evidence.keys()),
        "failure": failure or {},
        "not_proven": list(NOT_PROVEN),
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return summary


def _validation_verdict(evidence_ref: str, target_floor: str, artifact: dict[str, Any]) -> str:
    # validation 保守排序：先拦截必要字段，再拦截安全边界，最后才允许 Robot 只读消费。
    if not evidence_ref:
        return "blocked_invalid_evidence_ref"
    if not target_floor:
        return "blocked_invalid_target_floor"
    if sorted(artifact["phase_evidence"].keys()) != sorted(REQUIRED_PHASES):
        return "blocked_missing_phase_evidence"
    if artifact.get("same_evidence_ref_required") is not True:
        return "blocked_same_evidence_ref_required_not_true"
    if _has_forbidden_copy(artifact):
        return "blocked_unsafe_copy"
    if _has_success_claim(artifact):
        return "blocked_success_claim"
    return "ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven"


def build_rehearsal_evidence(
    evidence_ref: str,
    target_floor: str,
    failure_phase: str = "",
    failure_reason: str = "",
    manual_takeover_reason: str = "",
) -> tuple[dict[str, Any], int]:
    # 测试和 CLI 共用入口，保证 artifact contract 可在本机 Python 环境复现。
    safe_ref = _safe_token(evidence_ref, SAFE_TOKEN_RE)
    safe_floor = _safe_token(target_floor, SAFE_FLOOR_RE)
    phases = _phase_evidence(safe_ref, safe_floor)
    failure = _failure(failure_phase, failure_reason, manual_takeover_reason)
    artifact: dict[str, Any] = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "target_floor": safe_floor,
        "same_evidence_ref_required": True,
        "phase_evidence": phases,
        "failure": failure or {},
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    verdict = _validation_verdict(safe_ref, safe_floor, artifact)
    if failure:
        verdict = "blocked_rehearsal_failure_injected_not_proven"
    artifact["rehearsal_evidence_verdict"] = verdict
    artifact["overall_status"] = verdict
    artifact["phone_safe_summary"] = _phone_safe_summary(verdict, safe_ref, safe_floor, phases, failure)
    return artifact, 0


def write_rehearsal_evidence(artifact: dict[str, Any], output: str) -> None:
    # 指定 output 时自动建目录，方便 sprint 或 Robot 参数引用同一 JSON。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只收显式目标楼层与 evidence_ref，不猜测现场运行或硬件状态。
    parser = argparse.ArgumentParser(description="Generate elevator assist dry-run rehearsal evidence artifact")
    parser.add_argument("--evidence-ref", required=True, help="safe evidence_ref for Robot task record consumption")
    parser.add_argument("--target-floor", required=True, help="safe target floor label for rehearsal evidence")
    parser.add_argument("--failure-phase", default="", help="optional phase to force Robot dry-run fail closed")
    parser.add_argument("--failure-reason", default="", help="optional failure reason when --failure-phase is set")
    parser.add_argument(
        "--manual-takeover-reason",
        default="",
        help="optional manual takeover reason when --failure-phase is set",
    )
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_rehearsal_evidence(
        args.evidence_ref,
        args.target_floor,
        args.failure_phase,
        args.failure_reason,
        args.manual_takeover_reason,
    )
    write_rehearsal_evidence(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator assist rehearsal evidence: evidence_ref={artifact['evidence_ref']}")
        print(f"rehearsal_evidence_verdict: {artifact['rehearsal_evidence_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
