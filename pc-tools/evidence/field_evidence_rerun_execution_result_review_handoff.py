#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_result_review_handoff 的 fail-closed PC gate。

该 gate 只读取上一轮 `field_evidence_rerun_execution_result_review_decision`
artifact、summary、Robot safe alias 或 wrapper/nested JSON，把 safe review
decision 转成 owner handoff artifact。它不读取真实现场材料、不访问 ROS graph、
Nav2 / fixed-route runtime、serial/UART、WAVE ROVER、真实电梯、外部云、真实
手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HANDOFF_SCHEMA = "trashbot.field_evidence_rerun_execution_result_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate"

SOURCE_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_result_review_decision.v1",
    "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate"
ROBOT_SAFE_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary"

REVIEW_DECISIONS = {
    "accepted_for_review",
    "needs_material_backfill",
    "rejected",
    "blocked",
}

NEXT_REQUIRED_REAL_MATERIALS = (
    "same_safe_evidence_ref_task_record",
    "route_elevator_runtime_logs",
    "route_completion_signal",
    "elevator_door_floor_evidence",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
    "diagnostics_mobile_safe_summary",
    "true_phone_browser_evidence",
)

NOT_PROVEN = (
    "real_field_evidence_rerun_execution",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_field_task_record",
    "real_elevator_door_summary",
    "real_target_floor_or_floor_arrival_summary",
    "real_human_assistance_summary",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_delivery_result",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_browser_evidence",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "pr_5_resolved",
    "pr_6_runtime_proof",
)

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate; "
    "owner_handoff; next_required_real_materials; source=software_proof; "
    "not_proven; safe_to_control=false; delivery_success=false; "
    "primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只消费 review decision，不读取真实材料目录。
# 设计约束 02：handoff 只表达 owner 补证交接，不证明现场复跑完成。
# 设计约束 03：accepted_for_review 仍必须保持 not_proven，不能变成 field pass。
# 设计约束 04：same evidence_ref 是现场复账主键，缺失或不一致必须 blocked。
# 设计约束 05：source=software_proof 与 not_proven 必须从上游延续到输出。
# 设计约束 06：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 07：Robot safe alias 可消费，但 raw artifact 和 raw material 不可信。
# 设计约束 08：summary 是 Robot/mobile 消费面，只输出白名单字段。
# 设计约束 09：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 10：next_required_real_materials 固定列真实 field-owner 回填集合。
# 设计约束 11：reconciliation guidance 只说明人工复账，不做自动合并。
# 设计约束 12：rerun guidance 使用占位路径，避免本机路径泄漏。
# 设计约束 13：unsafe copy、success claim 和 control claim 必须 fail closed。
# 设计约束 14：PR #5/PR #6/O5 claims 均不能从 handoff 推导为完成。
# 设计约束 15：exit code 保持 0，让 blocked handoff 也能落盘审计。
# 设计约束 16：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 17：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 18：safe_copy 不包含完整 artifact、材料正文、路径或 secret。
# 设计约束 19：所有状态名用 snake_case，便于 rg 和下游解析。
# 设计约束 20：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。

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
    "db_url",
    "database_url",
    "queue_url",
    "ROS topic",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "low-level control",
    "low_level_control",
    "motor command",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw artifact",
    "raw robot response",
)

SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed|result)\b"),
    re.compile(r"(?i)\bfield\s+rerun\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bphone/browser\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|granted|authorized)\b"),
    re.compile(r"(?i)\bO5\s+external\s+proof\b"),
    re.compile(r"(?i)\bPR\s*#?5\s+(resolved|closed|complete|completed)\b"),
    re.compile(r"(?i)\bPR\s*#?6\s+runtime\s+proof\b"),
)

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"(?i)\bROS\s+topic\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机产物可按字符串排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，blocked 分支也不回显敏感原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 被误填成本机路径时只保留 basename，避免路径扩散到 UI。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中说明输入不适合进入 Robot/mobile 摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自由文案都检查，避免 success/control claim 穿透。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 fail-closed artifact，便于自动化留痕。
    if not path:
        return {}, "review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_decision_missing"
    except json.JSONDecodeError:
        return {}, "review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "review_decision_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段；字符串 wrapper 不可信。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _list_text(value: Any, limit: int = 32) -> list[str]:
    # 下游摘要只接受扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                label = _first_text(item.get("material"), item.get("name"), item.get("id"), item.get("action"), default="")
                if label:
                    items.append(_safe_text(label).strip())
            elif isinstance(item, (str, int, float, bool)):
                items.append(_safe_text(item).strip())
        return [item for item in items if item]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [_safe_text(value).strip()]
    return []


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_review_decision",
        "field_evidence_rerun_execution_result_review_decision_summary",
        ROBOT_SAFE_ALIAS,
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # summary 优先；artifact 和 Robot safe alias 也可消费，但必须符合 schema/boundary。
    candidates = _source_candidates(payload)
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1":
            return candidate
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == "trashbot.field_evidence_rerun_execution_result_review_decision.v1":
            return candidate
    return payload


def _schema(source: dict[str, Any]) -> str:
    # schema 字段只用于契约判断和输出解释。
    return _safe_text(source.get("schema", "")).strip()


def _boundary(source: dict[str, Any]) -> str:
    # boundary 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    return _schema(source) in SOURCE_SCHEMAS and _boundary(source) == SOURCE_BOUNDARY


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # 上游必须明确 software_proof/not_proven，不能把真实通过口径塞进本 gate。
    encoded = _encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded


def _flags_ok(source: dict[str, Any]) -> bool:
    # 三个动作旗标必须显式保持关闭；缺字段按不合格处理。
    return (
        source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层或 safe_copy/diagnostics/mobile 取。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _source_decision(source: dict[str, Any]) -> str:
    # review_decision 是上游状态主键；status/result_review_decision 用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("review_decision"),
            source.get("result_review_decision"),
            safe_copy.get("review_decision"),
            safe_copy.get("result_review_decision"),
            source.get("status"),
            safe_copy.get("status"),
            default="",
        )
    ).strip()


def _same_ref_status(source: dict[str, Any]) -> str:
    # same-evidence-ref 状态兼容字符串字段；非 matched/ready 都保守 blocked。
    safe_copy = _dict(source, "safe_copy")
    value = _first_text(source.get("same_evidence_ref_status"), safe_copy.get("same_evidence_ref_status"), default="")
    return _safe_text(value or "missing_evidence_ref").strip()


def _copy_probe(source: dict[str, Any]) -> dict[str, Any]:
    # 只扫描可能进入 safe summary 的字段，避免 non_access_scope 枚举触发误伤。
    return {
        "decision_reasons": source.get("decision_reasons"),
        "status_reasons": source.get("status_reasons"),
        "owner_handoff": source.get("owner_handoff"),
        "next_required_evidence": source.get("next_required_evidence"),
        "reconciliation_hint": source.get("reconciliation_hint"),
        "blocker_summary": source.get("blocker_summary"),
        "safe_copy": source.get("safe_copy"),
    }


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_decision: str,
    same_ref_status: str,
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 owner_handoff_ready。
    if success_claim:
        return "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff", ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "blocked_unsupported_field_evidence_rerun_execution_result_review_decision", [load_issue or "unsupported_review_decision_schema_or_boundary"]
    if not _source_is_software_not_proven(source):
        return "blocked_unsupported_field_evidence_rerun_execution_result_review_decision", ["source_not_software_proof_or_missing_not_proven"]
    if not _flags_ok(source):
        return "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff", ["source_action_flags_not_false"]
    if source.get("same_evidence_ref_required", True) is not True:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff", ["same_evidence_ref_required_not_true"]
    if not source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff", ["safe_evidence_ref_missing"]
    if requested_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref_status not in {"matched", "ready"}:
        return "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff", [f"same_evidence_ref:{same_ref_status}"]
    if source_decision not in REVIEW_DECISIONS:
        return "blocked_unsupported_field_evidence_rerun_execution_result_review_decision", [f"unsupported_review_decision:{source_decision or 'missing'}"]
    if source_decision == "accepted_for_review":
        return "ready_for_field_evidence_rerun_execution_result_review_owner_handoff_not_proven", ["source_review_decision_accepted_for_review_only"]
    if source_decision == "needs_material_backfill":
        return "needs_field_owner_material_backfill_for_execution_result_review_handoff_not_proven", ["source_review_decision_needs_material_backfill"]
    if source_decision == "rejected":
        return "rejected_field_evidence_rerun_execution_result_review_handoff_not_proven", ["source_review_decision_rejected"]
    return "blocked_field_evidence_rerun_execution_result_review_handoff_not_proven", ["source_review_decision_blocked"]


def _source_reasons(source: dict[str, Any]) -> list[str]:
    # 上游原因只作为上下文，不改变本 gate 状态机优先级。
    blocker = _dict(source, "blocker_summary")
    return _list_text(source.get("decision_reasons")) or _list_text(source.get("status_reasons")) or _list_text(blocker.get("status_reasons"))


def _blocker_summary(handoff_status: str, source_decision: str, reasons: list[str]) -> dict[str, Any]:
    # blocker summary 是手机/诊断安全摘要，不回显 raw material。
    return {
        "handoff_status": handoff_status,
        "source_review_decision": source_decision or "missing",
        "status_reasons": reasons[:8],
        "blocked_by_missing_real_materials": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_handoff(handoff_status: str, evidence_ref: str, source_owner: Any) -> dict[str, Any]:
    # owner_handoff 只分派人工补证责任，不授权 Robot/mobile 控制面。
    ref = evidence_ref or "<same_evidence_ref>"
    actions = {
        "ready_for_field_evidence_rerun_execution_result_review_owner_handoff_not_proven": "prepare_field_owner_backfill_request_from_sanitized_review_decision",
        "needs_field_owner_material_backfill_for_execution_result_review_handoff_not_proven": "request_field_owner_backfill_set_for_same_safe_evidence_ref",
        "rejected_field_evidence_rerun_execution_result_review_handoff_not_proven": "return_execution_result_material_for_owner_correction",
        "blocked_field_evidence_rerun_execution_result_review_handoff_not_proven": "repair_review_decision_source_before_handoff",
    }
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": actions.get(handoff_status, "regenerate_review_decision_without_unsafe_copy_or_success_claim"),
        "safe_evidence_ref": ref,
        "field_owner_backfill_required": True,
        "next_required_real_materials": list(NEXT_REQUIRED_REAL_MATERIALS),
        "source_owner_handoff": _safe_value(source_owner),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(handoff_status: str, evidence_ref: str, reasons: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if "unsupported" in handoff_status:
        return [f"Provide supported review-decision summary for evidence_ref={ref}.", *reasons[:4]]
    if "mismatch" in handoff_status:
        return [f"Regenerate result intake, review decision, and handoff with one safe evidence_ref={ref}."]
    if "unsafe" in handoff_status:
        return ["Regenerate review decision without raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, raw artifacts, tracebacks, control claims, or success claims."]
    if handoff_status.startswith("rejected"):
        return [f"Correct rejected execution result material for evidence_ref={ref}, then rerun result intake and review decision before handoff."]
    if handoff_status.startswith("blocked"):
        return [f"Repair blocked review decision for evidence_ref={ref}, then rerun review handoff.", *reasons[:4]]
    return [f"Backfill field-owner real material set for evidence_ref={ref}: {', '.join(NEXT_REQUIRED_REAL_MATERIALS)}."]


def _reconciliation_guidance(source_decision: str, handoff_status: str, evidence_ref: str) -> dict[str, Any]:
    # reconciliation guidance 只描述 same-ref 人工复账，不做自动状态合并。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "safe_evidence_ref": ref,
        "source_review_decision": source_decision or "missing",
        "handoff_status": handoff_status,
        "same_evidence_ref_required": True,
        "required_reconciliation": "match_task_record_route_elevator_runtime_completion_dropoff_delivery_and_phone_evidence_to_same_safe_evidence_ref",
        "accepted_is_field_pass": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_guidance(evidence_ref: str) -> dict[str, Any]:
    # rerun guidance 使用占位文件名，避免真实路径或材料目录进入 artifact。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "commands": [
            "python3 pc-tools/evidence/field_evidence_rerun_execution_result_intake.py --result-packet-json <safe_execution_result_packet.json> --evidence-ref "
            f"{ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_execution_result_review_decision.py --result-intake-json <field_result_intake.json> --evidence-ref "
            f"{ref} --once-json",
            "python3 pc-tools/evidence/field_evidence_rerun_execution_result_review_handoff.py --review-decision-json <field_result_review_decision.json> --evidence-ref "
            f"{ref} --once-json",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    source_decision: str,
    owner_handoff: dict[str, Any],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料正文。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": handoff_status,
        "handoff_status": handoff_status,
        "source_review_decision": source_decision,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "owner_handoff": owner_handoff,
        "next_required_real_materials": list(NEXT_REQUIRED_REAL_MATERIALS),
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_review_handoff(
    review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 execution result review decision summary，生成 metadata-only handoff artifact。"""
    payload, load_issue = _load_json(review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_decision = _source_decision(source) if source else ""
    same_ref_status = _same_ref_status(source) if source else "missing_evidence_ref"
    unsafe = bool(payload) and _has_forbidden_copy(_copy_probe(source))
    success_claim = bool(payload) and _has_success_claim(_copy_probe(source))
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_decision,
        same_ref_status,
        unsafe,
        success_claim,
    )
    source_reasons = _source_reasons(source) if source else []
    all_reasons = [*status_reasons, *source_reasons]
    source_owner = source.get("owner_handoff") if source else {}
    owner_handoff = _owner_handoff(handoff_status, evidence_ref_out, source_owner)
    next_required = _next_required_evidence(handoff_status, evidence_ref_out, all_reasons)
    blocker_summary = _blocker_summary(handoff_status, source_decision, all_reasons)
    reconciliation_guidance = _reconciliation_guidance(source_decision, handoff_status, evidence_ref_out)
    rerun_guidance = _rerun_guidance(evidence_ref_out)
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, source_decision, owner_handoff, next_required)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": all_reasons,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "owner_handoff": owner_handoff,
        "blocker_summary": blocker_summary,
        "next_required_real_materials": list(NEXT_REQUIRED_REAL_MATERIALS),
        "next_required_evidence": next_required,
        "reconciliation_guidance": reconciliation_guidance,
        "rerun_guidance": rerun_guidance,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff is software_proof only and does not read or validate real field materials.",
            "Keep not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until independent real evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": all_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_field_evidence_rerun_execution_result_review_decision": {
            "load_issue": load_issue,
            "schema": _schema(source) if source else "",
            "evidence_boundary": _boundary(source) if source else "",
            "source_review_decision": source_decision,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "owner_handoff": owner_handoff,
        "blocker_summary": blocker_summary,
        "next_required_real_materials": list(NEXT_REQUIRED_REAL_MATERIALS),
        "next_required_evidence": next_required,
        "reconciliation_guidance": reconciliation_guidance,
        "rerun_guidance": rerun_guidance,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_artifact",
            "raw_field_material_content",
            "local_path",
            "checksum",
            "credentials",
            "db_queue_url",
            "ros_topic",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "phone_device",
            "robot_action",
            "field_rerun_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return _safe_value(artifact), _safe_value(summary), 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution result review handoff artifact")
    parser.add_argument("--review-decision-json", required=True, help="review decision artifact, summary, Robot safe alias, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_review_handoff(
        args.review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_result_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
