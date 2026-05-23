#!/usr/bin/env python3
"""生成 verified_terminal_result_material_followup_escalation_status 的 PC-only evidence gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只消费上一轮 review-handoff 的 safe artifact/summary/Robot alias。
# 设计约束 02：followup_status 只表达补证跟进状态，不表达 terminal result 已验证。
# 设计约束 03：所有输出都固定保留 software_proof、not_proven 和三个 false 控制旗标。
# 设计约束 04：safe evidence_ref 与 command_id 只能作为短标识，不能是路径、URL 或凭证。
# 设计约束 05：raw artifact、本机路径、DB/queue/OSS、ROS/control、硬件和 ACK/replay/resubmit hints 必须拒绝。
# 设计约束 06：escalated 只说明人工 owner/support/reviewer 路由已形成，不打开 Start/Confirm/Cancel。
# 设计约束 07：blocked/rejected 仍写脱敏 artifact/summary，方便 Product closeout 引用失败类别。
# 设计约束 08：exit code 只表达 PC gate 状态，不代表 delivery/dropoff/cancel result 通过。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.verified_terminal_result_material_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1"
ROBOT_ALIAS_SCHEMA = "trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "verified_terminal_result_material_followup_escalation_status"
SOURCE_CAPABILITY = "verified_terminal_result_material_review_handoff"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate"
SOURCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_review_handoff_gate"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary"
SOURCE_ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_review_handoff_summary"
NO_OKR_LIFT = "no OKR percentage lift"

SUPPORTED_INPUT_SCHEMAS = {
    "trashbot.verified_terminal_result_material_review_handoff.v1",
    "trashbot.verified_terminal_result_material_review_handoff_summary.v1",
    SOURCE_ROBOT_ALIAS,
    f"trashbot.{SOURCE_ROBOT_ALIAS}.v1",
}
WRAPPER_KEYS = (
    "verified_terminal_result_material_review_handoff",
    "verified_terminal_result_material_review_handoff_summary",
    SOURCE_ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "summary",
    "artifact",
    "data",
    "payload",
    "diagnostics",
    "latest_status",
)

TERMINAL_RESULT_TYPES = ("delivery", "dropoff", "cancel")
SOURCE_HANDOFF_STATUSES = ("ready_for_owner_handoff", "needs_material_backfill", "rejected", "blocked")
FOLLOWUP_ESCALATED = "escalated_for_terminal_result_material_followup_not_proven"
FOLLOWUP_WAITING = "waiting_for_terminal_result_material_backfill_not_proven"
FOLLOWUP_REASSIGN = "needs_support_owner_reassignment_not_proven"
FOLLOWUP_REJECTED = "rejected_unsafe_terminal_result_followup_not_proven"
FOLLOWUP_BLOCKED = "blocked_missing_terminal_result_review_handoff_not_proven"
FOLLOWUP_STATUSES = (
    FOLLOWUP_ESCALATED,
    FOLLOWUP_WAITING,
    FOLLOWUP_REASSIGN,
    FOLLOWUP_REJECTED,
    FOLLOWUP_BLOCKED,
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
URL_OR_QUEUE_RE = re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb|oss|s3)://|https?://")

# 字段名命中这些类别时，说明输入已不是 safe summary，不能继续给 support/field owner。
FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "complete_artifact",
    "artifact_path",
    "raw_path",
    "local_path",
    "file_path",
    "log_path",
    "screenshot_path",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "api_key",
    "cookie",
    "db_url",
    "database_url",
    "queue_url",
    "signed_url",
    "ros_topic",
    "ros_service",
    "ros_action",
    "control_command",
    "cmd_vel",
    "twist",
    "motor",
    "hardware_detail",
    "hardware_details",
    "serial_device",
    "uart",
    "wave_rover",
    "esp32",
    "orange_pi",
    "baudrate",
    "voltage",
    "pin",
    "wiring",
    "firmware",
    "cursor",
    "replay",
    "resubmit",
    "reviewer_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(control_enabled|hil_pass|field_pass|reviewer_resolved)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified|passed)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial device)\b"),
    re.compile(r"(?i)\b(ack|cursor|replay|resubmit)\b.*\b(command|mutation|hint|retry|lookup)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved)\b"),
)

DEFAULT_BACKFILL_ITEMS = (
    "real_terminal_delivery_result",
    "real_terminal_dropoff_result",
    "real_terminal_cancel_result",
    "same_safe_evidence_ref_task_record",
    "real_nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "real_elevator_door_floor_evidence",
    "human_assistance_or_operator_note",
    "true_phone_browser_or_device_evidence",
)
NOT_PROVEN_ITEMS = (
    "verified_terminal_delivery_result",
    "verified_terminal_dropoff_result",
    "verified_terminal_cancel_result",
    "real_delivery_success",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_elevator_field_pass",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)
BOUNDARY_NOTE = (
    "verified_terminal_result_material_followup_escalation_status; "
    "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; no OKR percentage lift"
)


def _utc_now() -> str:
    # UTC 让 Docker-only evidence 在不同时区的 sprint artifact 中保持稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary，所以 artifact、summary 和 Robot alias 都重复固定旗标。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": False,
        "okr_lift_note": NO_OKR_LIFT,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 输出文本只保留短摘要，避免把日志、路径或完整 JSON 带到 escalation artifact。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _encoded(value: Any) -> str:
    # 递归扫描 dict/list，防止敏感内容藏在 wrapper 或数组里。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    # 缺输入或坏 JSON 也生成 blocked artifact，而不是抛出未处理异常。
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "input_missing"
    except json.JSONDecodeError:
        return {}, "input_invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "input_read_error"
    if not isinstance(payload, dict):
        return {}, "input_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 兼容只接受 object，避免把原始文本误当 safe summary 展开。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，不把任意 raw payload 都当 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema/capability 命中的 review-handoff artifact/summary/alias。
    candidates = _candidates(payload)
    for candidate in candidates:
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if (schema in SUPPORTED_INPUT_SCHEMAS or capability == SOURCE_CAPABILITY) and candidate.get("source") == SOURCE:
            return candidate
    for candidate in candidates:
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_INPUT_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _safe_ref(value: Any) -> tuple[str, str]:
    # evidence_ref/command_id 都按短标识处理，路径、URL 和凭证形态直接拒绝。
    ref = _safe_text(value)
    if not ref:
        return "", "missing_safe_ref"
    if not SAFE_REF_RE.fullmatch(ref):
        return "", "unsafe_ref_format"
    if PATH_LIKE_RE.search(ref) or URL_OR_QUEUE_RE.search(ref):
        return "", "unsafe_ref_path_or_url"
    return ref, ""


def _collect_refs(value: Any) -> list[str]:
    # 只收集明确 ref 字段，用于 same-evidence-ref 一致性检查。
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in {"evidence_ref", "safe_evidence_ref"}:
                text = _safe_text(child)
                if text:
                    refs.append(text)
            refs.extend(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_collect_refs(child))
    return refs


def _dedupe(values: list[str]) -> list[str]:
    # 保序去重让 summary 稳定，便于 Robot/mobile 做快照对比。
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _ref_state(source: dict[str, Any], payload: dict[str, Any]) -> tuple[str, list[str]]:
    # 多个 safe evidence_ref 必须一致，避免把不同现场材料拼成一个 escalation。
    ref_value = source.get("safe_evidence_ref") or source.get("evidence_ref") or payload.get("safe_evidence_ref") or payload.get("evidence_ref")
    safe_ref, ref_error = _safe_ref(ref_value)
    errors: list[str] = [ref_error] if ref_error else []
    for ref in _collect_refs(source) + _collect_refs(payload):
        checked, error = _safe_ref(ref)
        if error:
            errors.append(error)
        elif safe_ref and checked != safe_ref:
            errors.append("evidence_ref_mismatch")
    return safe_ref, _dedupe(errors)


def _safe_name_list(value: Any, limit: int = 40) -> list[str]:
    # material 对象只保留 name/status/reason，不把原始材料字段带入输出。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    names: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            name = _safe_text(item.get("name") or item.get("material") or item.get("material_name") or item.get("summary"))
            reason = _safe_text(item.get("reason") or item.get("status"))
            text = f"{name}:{reason}" if name and reason else name or reason
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            names.append(text)
    return _dedupe(names)


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/hardware/ACK/replay 直接拒绝，避免 safe_copy 泄漏动作暗示。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if any(term in key_text.lower() for term in FORBIDDEN_KEY_TERMS):
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _any_true_key(value: Any, key: str) -> bool:
    # true flag 可能藏在 nested summary 或字符串 note；false 是允许的 fail-closed 旗标。
    if isinstance(value, dict):
        return any((str(k) == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _unsafe_reasons(value: dict[str, Any]) -> list[str]:
    # 只返回类别，不回显命中原文，避免 rejected 输出泄漏敏感片段。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_path_credential_db_queue_ros_control_hardware_ack_replay_or_resolution_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded):
        reasons.append("unsafe_raw_artifact_path_url_db_queue_oss_or_local_path")
    if any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_credential_ros_control_hardware_ack_replay_resolution_or_success_claim")
    for key in ("delivery_success", "primary_actions_enabled", "safe_to_control", "control_enabled", "hil_pass", "field_pass"):
        if _any_true_key(value, key):
            reasons.append(f"{key}_true_overclaim")
    return _dedupe(reasons)


def _source_is_software_not_proven(source: dict[str, Any]) -> bool:
    # source 合同必须保持 software_proof / not_proven / false flags。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and source.get("safe_to_control") is False
    )


def _schema_supported(normalized: dict[str, Any]) -> bool:
    # schema 或 Robot safe alias 都要匹配，source boundary 也要停留在 handoff gate。
    schema = normalized["schema"]
    boundary = normalized["source_boundary"]
    if schema in SUPPORTED_INPUT_SCHEMAS and boundary in {"", SOURCE_BOUNDARY}:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and boundary == SOURCE_BOUNDARY:
        return True
    return False


def _owner_value(source: dict[str, Any], key: str, default: str) -> str:
    # owner 字段允许顶层或 owner_handoff 内给出；缺失时走保守默认。
    owner_handoff = _dict(source.get("owner_handoff"))
    if key in source:
        return _safe_text(source.get(key))
    if key in owner_handoff:
        return _safe_text(owner_handoff.get(key))
    return default


def _normalize_source(payload: dict[str, Any], read_state: str) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，避免输出直接引用输入原对象。
    source = _find_source(payload) if payload else {}
    material_summary = _dict(source.get("material_status_summary"))
    safe_ref, ref_errors = _ref_state(source, payload) if source else ("", [])
    command_id, command_error = _safe_ref(source.get("safe_command_id") or source.get("command_id")) if source.get("safe_command_id") or source.get("command_id") else ("", "")
    source_handoff_status = _safe_text(source.get("handoff_status") or source.get("verified_terminal_result_material_review_handoff")).lower()
    missing = _safe_name_list(source.get("missing_required_materials") or material_summary.get("missing_required_materials") or source.get("next_required_evidence"))
    rejected = _safe_name_list(source.get("rejected_material_refs") or material_summary.get("rejected_material_refs"))
    next_required = _safe_name_list(source.get("next_required_evidence") or missing)
    return {
        "read_state": read_state,
        "source": source,
        "schema": _safe_text(source.get("schema")),
        "source_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary")),
        "source_capability": _safe_text(source.get("capability")),
        "source_handoff_status": source_handoff_status,
        "safe_evidence_ref": safe_ref,
        "ref_errors": _dedupe(ref_errors + ([command_error] if command_error else [])),
        "safe_command_id": command_id,
        "terminal_result_type": _safe_text(source.get("terminal_result_type")),
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "assigned_owner": _owner_value(source, "assigned_owner", "field_terminal_result_material_owner"),
        "support_owner": _owner_value(source, "support_owner", "support_terminal_result_material_owner"),
        "reviewer_route": _owner_value(source, "reviewer_route", "terminal_result_material_reviewer"),
        "required_material_backfill": missing or list(DEFAULT_BACKFILL_ITEMS),
        "rejected_material_refs": rejected,
        "next_required_evidence": next_required,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
        "source_is_software_not_proven": _source_is_software_not_proven(source) if source else False,
    }


def _needs_reassignment(normalized: dict[str, Any]) -> bool:
    # 三个 owner route 都必须有短安全值，否则只能提示 support owner 重新分派。
    return not all(
        _safe_text(normalized[key])
        and not PATH_LIKE_RE.search(_safe_text(normalized[key]))
        and not URL_OR_QUEUE_RE.search(_safe_text(normalized[key]))
        for key in ("assigned_owner", "support_owner", "reviewer_route")
    )


def _followup_status(normalized: dict[str, Any]) -> tuple[str, list[str]]:
    # 决策顺序：输入契约 -> 安全 -> source 证明边界 -> evidence_ref -> terminal type -> handoff 映射。
    if normalized["read_state"]:
        return FOLLOWUP_BLOCKED, [normalized["read_state"]]
    if not _schema_supported(normalized):
        return FOLLOWUP_BLOCKED, ["unsupported_review_handoff_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return FOLLOWUP_REJECTED, normalized["unsafe_reasons"]
    if not normalized["source_is_software_not_proven"]:
        return FOLLOWUP_REJECTED, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or normalized["same_evidence_ref_required"] is not True:
        return FOLLOWUP_BLOCKED, normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"]
    if normalized["terminal_result_type"] not in TERMINAL_RESULT_TYPES:
        return FOLLOWUP_BLOCKED, ["unsupported_terminal_result_type"]
    if _needs_reassignment(normalized):
        return FOLLOWUP_REASSIGN, ["missing_assigned_owner_support_owner_or_reviewer_route"]
    source_status = normalized["source_handoff_status"]
    if source_status == "ready_for_owner_handoff":
        return FOLLOWUP_ESCALATED, ["owner_support_reviewer_followup_route_escalated_not_proven"]
    if source_status == "needs_material_backfill":
        return FOLLOWUP_WAITING, ["waiting_for_same_evidence_ref_terminal_result_material_backfill"]
    if source_status == "rejected":
        return FOLLOWUP_REJECTED, ["source_review_handoff_rejected_or_unsafe"]
    if source_status == "blocked":
        return FOLLOWUP_BLOCKED, ["source_review_handoff_blocked_before_followup"]
    return FOLLOWUP_REJECTED, ["unknown_review_handoff_status"]


def _next_required(normalized: dict[str, Any], followup_status: str, reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证状态，不包含 ACK、cursor、replay 或 robot command。
    if followup_status == FOLLOWUP_ESCALATED:
        return [
            "Field owner tracks terminal result material follow-up under the same safe evidence_ref.",
            "Support owner keeps primary actions disabled until real terminal result material is backfilled.",
            "Reviewer route checks the backfill later without claiming reviewer-resolution now.",
        ]
    if followup_status == FOLLOWUP_WAITING:
        return [f"Waiting for same safe evidence_ref material backfill: {name}" for name in normalized["required_material_backfill"][:10]]
    if followup_status == FOLLOWUP_REASSIGN:
        return ["Assign field owner, support owner, and reviewer route before terminal result follow-up can continue."]
    if followup_status == FOLLOWUP_REJECTED:
        rejected = normalized["rejected_material_refs"] or reasons
        return [f"Replace unsafe terminal result follow-up summary: {name}" for name in rejected[:10]]
    return ["Provide a supported verified_terminal_result_material_review_handoff artifact, summary, or Robot safe alias."]


def _blocked_reason(followup_status: str, reasons: list[str]) -> str:
    # blocked_reason 只输出短类别，便于 Product closeout 和 Robot alias 引用。
    if followup_status in {FOLLOWUP_ESCALATED, FOLLOWUP_WAITING}:
        return ""
    return _safe_text(";".join(reasons), "blocked")


def _safe_copy(followup_status: str, normalized: dict[str, Any]) -> str:
    # safe_copy 给 Robot/mobile 复制用，只包含短字段和固定边界。
    return (
        f"{CAPABILITY}: followup_status={followup_status}; "
        f"source_handoff_status={normalized['source_handoff_status'] or 'blocked'}; "
        f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; "
        f"command_id={normalized['safe_command_id'] or 'none'}; "
        f"terminal_result_type={normalized['terminal_result_type'] or 'blocked'}; "
        f"assigned_owner={normalized['assigned_owner'] or 'unassigned'}; "
        f"support_owner={normalized['support_owner'] or 'unassigned'}; "
        f"reviewer_route={normalized['reviewer_route'] or 'unassigned'}; "
        f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; software_proof; not_proven; "
        "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; no OKR percentage lift."
    )


def build_verified_terminal_result_material_followup_escalation_status(input_path: Path) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 follow-up escalation artifact 与 summary；escalated 也不是 delivery success。"""
    payload, read_state = _read_json(input_path)
    normalized = _normalize_source(payload, read_state)
    followup_status, reasons = _followup_status(normalized)
    next_required = _next_required(normalized, followup_status, reasons)
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "source_handoff_status": normalized["source_handoff_status"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "followup_status": followup_status,
        "allowed_followup_statuses": list(FOLLOWUP_STATUSES),
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "safe_command_id": normalized["safe_command_id"],
        "command_id": normalized["safe_command_id"],
        "same_evidence_ref_required": True,
        "terminal_result_type": normalized["terminal_result_type"],
        "allowed_terminal_result_types": list(TERMINAL_RESULT_TYPES),
        "allowed_source_handoff_statuses": list(SOURCE_HANDOFF_STATUSES),
        "assigned_owner": normalized["assigned_owner"],
        "support_owner": normalized["support_owner"],
        "reviewer_route": normalized["reviewer_route"],
        "required_material_backfill": normalized["required_material_backfill"],
        "escalation_reason": _safe_text(";".join(reasons), "followup_status_evaluated"),
        "blocked_reason": _blocked_reason(followup_status, reasons),
        "next_required_evidence": next_required,
        "safe_copy": _safe_copy(followup_status, normalized),
        "summary_alias": ROBOT_ALIAS,
        "robot_alias_schema": ROBOT_ALIAS_SCHEMA,
        "fail_closed_flags": {
            "source": SOURCE,
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "okr_percentage_lift": False,
            "okr_lift_note": NO_OKR_LIFT,
        },
        "safety_markers": [
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            NO_OKR_LIFT,
        ],
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "verified_terminal_result_material_followup_escalation_status": followup_status,
        **common,
        "source_review_handoff_detail": {
            "schema_supported": _schema_supported(normalized),
            "read_state": read_state,
            "source_is_software_proof_not_proven": normalized["source_is_software_not_proven"],
            "unsafe_reasons": normalized["unsafe_reasons"],
            "ref_errors": normalized["ref_errors"],
        },
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **common,
    }
    return artifact, summary, 0 if followup_status in {FOLLOWUP_ESCALATED, FOLLOWUP_WAITING} else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # output-dir 由 CLI 创建，便于 sprint evidence bundle 一次落盘。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只接受上一轮 review handoff 输入，不新增控制、ACK、review mutation 或 raw artifact 路径。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_followup_escalation_status.v1 software_proof artifact "
            "from --input; keeps source=software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift."
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="prior review handoff artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for sanitized follow-up escalation JSON files")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_followup_escalation_status(args.input)
    _write_json(args.output_dir / "verified_terminal_result_material_followup_escalation_status.json", artifact)
    _write_json(args.output_dir / "verified_terminal_result_material_followup_escalation_status_summary.json", summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
