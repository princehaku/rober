#!/usr/bin/env python3
"""生成 reviewer ACK followup escalation status 的 PC-only evidence gate。

该 gate 只消费上一轮
`field_evidence_material_resolution_reviewer_ack_review_handoff` 的 safe
artifact、summary、Robot alias 或常见 wrapper。输出告诉 support 当前 reviewer ACK
handoff 是否还在等 field owner response、是否逾期升级、是否可进入 owner response
intake；它仍然只是 Docker/local software proof，不证明真实 phone/browser、外部云、
HIL、route/elevator field pass、delivery success、PR #5 closure 或 OKR lift。
"""

from __future__ import annotations

# 设计约束 01：只读取 reviewer ACK review-handoff safe surface，不读取 raw ACK。
# 设计约束 02：followup status 只表达人工补证进度，不代表 owner response 已通过。
# 设计约束 03：source=software_proof、not_proven 与三类 false flag 必须逐层固定。
# 设计约束 04：safe evidence_ref 是 review-handoff 到 followup 的唯一串联主键。
# 设计约束 05：缺输入、坏 JSON、unsupported schema 或 wrong boundary 一律 blocked。
# 设计约束 06：success/control/cloud/phone/HIL/PR resolution claim 一律 rejected。
# 设计约束 07：输出不得复制 raw artifact、路径、凭证、checksum、stack trace 或控制命令。
# 设计约束 08：gate 不访问 ROS graph、Nav2 runtime、硬件、云、GitHub 或真实手机。
# 设计约束 09：exit code 只表达 PC gate 状态，不表达真实 delivery result。
# 设计约束 10：中文注释保留证据边界，避免后续误把 followup 写成 completion。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_reviewer_ack_review_handoff as handoff_gate


SCHEMA = "trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
SOURCE_CAPABILITY = handoff_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate"
SOURCE_BOUNDARY = handoff_gate.EVIDENCE_BOUNDARY

OWNER_RESPONSE_PENDING = "owner_response_pending_not_proven"
OWNER_RESPONSE_OVERDUE = "owner_response_overdue_escalate_not_proven"
BLOCKED_MISSING_REQUIRED_MATERIALS = "blocked_missing_required_materials_not_proven"
BLOCKED_UNSAFE_MATERIAL_CLAIMS = "blocked_unsafe_material_claims_not_proven"
ACCEPTED_FOR_OWNER_RESPONSE_INTAKE = "accepted_for_owner_response_intake_not_proven"
BLOCKED_MISSING_REVIEWER_ACK_HANDOFF = "blocked_missing_reviewer_ack_handoff_not_proven"
FOLLOWUP_STATUSES = (
    OWNER_RESPONSE_PENDING,
    OWNER_RESPONSE_OVERDUE,
    BLOCKED_MISSING_REQUIRED_MATERIALS,
    BLOCKED_UNSAFE_MATERIAL_CLAIMS,
    ACCEPTED_FOR_OWNER_RESPONSE_INTAKE,
    BLOCKED_MISSING_REVIEWER_ACK_HANDOFF,
)

SUPPORTED_SOURCE_SCHEMAS = {
    handoff_gate.SCHEMA,
    handoff_gate.SUMMARY_SCHEMA,
    handoff_gate.ROBOT_ALIAS,
    f"trashbot.{handoff_gate.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    "field_evidence_material_resolution_reviewer_ack_review_handoff",
    "field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
    "field_evidence_material_resolution_reviewer_ack_followup_escalation_status",
    "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
    handoff_gate.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
    "diagnostics",
    "latest_status",
)

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")

FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "raw_fields",
    "raw_materials",
    "raw_log",
    "artifact_path",
    "local_path",
    "file_path",
    "log_path",
    "complete_artifact",
    "checksum",
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
    "ack_cursor",
    "control_command",
    "cmd_vel",
    "twist",
    "ros_topic",
    "ros_service",
    "ros_action",
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
    "pr5_resolution",
    "reviewer_resolution",
    "review_thread_resolved",
    "verified_terminal_result",
    "delivery_success_claim",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|delivery_pass|verified_terminal_result)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial)\b"),
    re.compile(r"(?i)\b(real phone proof|true phone proof|cloud proof|field proof|HIL proof|Objective 5 external proof)\b"),
    re.compile(r"(?i)\bTraceback \(most recent call last\):"),
)

DEFAULT_MISSING_REQUIRED_EVIDENCE = (
    "field owner response under the same safe evidence_ref",
    "reviewer ACK followup acknowledgement without reviewer-resolution claim",
    "support escalation owner decision or due-date response",
    "owner response intake material that preserves source=software_proof and not_proven",
)

NOT_PROVEN_ITEMS = (
    "real_reviewer_resolution",
    "real_owner_acceptance",
    "real_owner_response_intake_completion",
    "real_route_elevator_field_pass",
    "verified_terminal_result",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "hardware_or_hil_pass",
    "delivery_success",
    "pr5_reviewer_resolution",
    "okr_percentage_lift",
)

BOUNDARY_NOTE = (
    "field_evidence_material_resolution_reviewer_ack_followup_escalation_status; "
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "owner response intake readiness only, not real phone/browser, external proof, HIL, or delivery success"
)


def _utc_now() -> str:
    # UTC 时间戳让 Docker-only evidence 在跨时区 review 时排序稳定。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary 或 nested safe copy，因此每层都重复 fail-closed 旗标。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _encoded(value: Any) -> str:
    # 递归安全扫描用稳定 JSON，覆盖 nested key/value 的越界 claim。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 输出只保留短单行摘要，避免 raw log、stack trace 或完整 JSON 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_list(value: Any, limit: int = 40) -> list[str]:
    # 列表字段只输出短文本，并过滤本机路径类片段。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(
                item.get("name")
                or item.get("material")
                or item.get("action")
                or item.get("summary")
                or item.get("reason")
                or item.get("owner")
            )
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 blocked handoff，不抛 traceback。
    if not path:
        return {}, "reviewer_ack_review_handoff_input_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "reviewer_ack_review_handoff_input_missing"
    except json.JSONDecodeError:
        return {}, "reviewer_ack_review_handoff_input_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "reviewer_ack_review_handoff_input_read_error"
    if not isinstance(payload, dict):
        return {}, "reviewer_ack_review_handoff_input_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object；字符串化 JSON 不自动展开，避免绕过 safe summary。
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
    # 优先选择 schema/capability 命中的 reviewer ACK review-handoff surface。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _boundary(payload: dict[str, Any]) -> str:
    # source boundary 可以在 evidence_boundary 或 boundary 字段中出现。
    return _safe_text(payload.get("evidence_boundary") or payload.get("boundary"))


def _source_ref(source: dict[str, Any]) -> tuple[str, list[str]]:
    # 多个 safe evidence_ref 必须一致，避免不同现场材料被拼成一个 followup。
    refs: list[str] = []
    for candidate in _candidates(source):
        for key in ("safe_evidence_ref", "evidence_ref"):
            text = _safe_text(candidate.get(key))
            if text:
                refs.append(text)
    unique_refs = list(dict.fromkeys(refs))
    reasons: list[str] = []
    for ref in unique_refs:
        if not SAFE_EVIDENCE_REF_RE.fullmatch(ref) or PATH_LIKE_RE.search(ref):
            reasons.append("unsafe_evidence_ref")
    if len(unique_refs) > 1:
        reasons.append("evidence_ref_mismatch")
    return (unique_refs[0] if unique_refs and not reasons else ""), list(dict.fromkeys(reasons))


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/hardware 类别时拒绝，不回显敏感值。
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


def _truthy_false_flags(value: Any) -> list[str]:
    # 输入任何层把 false-state flag 改成 true，都不能进入 followup ready。
    reasons: list[str] = []
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if value.get(key) is True:
                reasons.append(f"{key}_true_overclaim")
        for child in value.values():
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, list):
        for child in value:
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, str):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value):
                reasons.append(f"{key}_true_overclaim")
    return reasons


def _unsafe_reasons(value: dict[str, Any]) -> list[str]:
    # 只输出类别原因，不输出命中的原始片段，保持 blocked artifact 脱敏。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_hardware_resolution_or_checksum_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_credential_ros_control_hardware_success_or_resolution_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


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
    # schema 或 capability 命中，并且边界必须是上一轮 reviewer ACK handoff gate。
    if normalized["schema"] in SUPPORTED_SOURCE_SCHEMAS and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    return False


def _normalize_source(payload: dict[str, Any], read_issue: str, expected_ref: str) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，输出不会直接引用输入原对象。
    source = _find_source(payload) if payload else {}
    safe_copy = _dict(source.get("safe_copy"))
    field_owner_handoff = _dict(source.get("field_owner_handoff"))
    support_handoff = _dict(source.get("support_handoff"))
    safe_ref, ref_errors = _source_ref(source) if source else ("", [])
    if expected_ref and safe_ref and expected_ref != safe_ref:
        ref_errors.append("evidence_ref_mismatch")
    source_handoff_status = _safe_text(
        source.get("handoff_status")
        or source.get("field_evidence_material_resolution_reviewer_ack_review_handoff")
        or safe_copy.get("handoff_status")
    )
    return {
        "read_issue": read_issue,
        "source": source,
        "schema": _safe_text(source.get("schema")),
        "source_boundary": _boundary(source),
        "source_capability": _safe_text(source.get("capability")),
        "source_handoff_status": source_handoff_status,
        "source_review_decision": _safe_text(source.get("source_review_decision") or safe_copy.get("source_review_decision")),
        "reviewer_ack_state": _safe_text(source.get("reviewer_ack_state") or safe_copy.get("reviewer_ack_state")),
        "ack_owner": _safe_text(source.get("ack_owner") or "reviewer"),
        "field_owner_handoff": field_owner_handoff,
        "field_owner_next_action": _safe_text(field_owner_handoff.get("next_action")),
        "support_escalation_owner": _safe_text(support_handoff.get("role") or "support"),
        "safe_evidence_ref": safe_ref,
        "ref_errors": list(dict.fromkeys(ref_errors)),
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "handoff_reasons": _safe_list(source.get("handoff_reasons") or safe_copy.get("handoff_reasons")),
        "decision_reasons": _safe_list(source.get("decision_reasons") or safe_copy.get("decision_reasons")),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or safe_copy.get("next_required_evidence")),
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
        "source_is_software_not_proven": _source_is_software_not_proven(source) if source else False,
    }


def _followup_status(normalized: dict[str, Any], due_status: str) -> tuple[str, list[str]]:
    # fail-closed 优先级：缺输入/不支持 -> unsafe -> weak ref -> handoff 状态 -> due 状态。
    if normalized["read_issue"]:
        return BLOCKED_MISSING_REVIEWER_ACK_HANDOFF, [normalized["read_issue"]]
    if not _schema_supported(normalized):
        return BLOCKED_MISSING_REVIEWER_ACK_HANDOFF, ["unsupported_reviewer_ack_review_handoff_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return BLOCKED_UNSAFE_MATERIAL_CLAIMS, normalized["unsafe_reasons"]
    if not normalized["source_is_software_not_proven"]:
        return BLOCKED_UNSAFE_MATERIAL_CLAIMS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or normalized["same_evidence_ref_required"] is not True:
        return BLOCKED_MISSING_REVIEWER_ACK_HANDOFF, normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"]
    if normalized["source_handoff_status"] == handoff_gate.HANDOFF_REJECTED:
        return BLOCKED_UNSAFE_MATERIAL_CLAIMS, ["source_reviewer_ack_handoff_rejected_unsafe"]
    if normalized["source_handoff_status"] != handoff_gate.HANDOFF_READY:
        return BLOCKED_MISSING_REQUIRED_MATERIALS, ["source_reviewer_ack_handoff_not_ready_for_followup"]
    if due_status == "pending":
        return OWNER_RESPONSE_PENDING, ["reviewer_ack_handoff_sent_owner_response_pending"]
    if due_status == "overdue":
        return OWNER_RESPONSE_OVERDUE, ["reviewer_ack_handoff_sent_owner_response_overdue_escalate"]
    if due_status == "accepted":
        return ACCEPTED_FOR_OWNER_RESPONSE_INTAKE, ["reviewer_ack_handoff_ready_for_owner_response_intake_only"]
    return BLOCKED_MISSING_REQUIRED_MATERIALS, ["unsupported_due_status"]


def _next_required(status: str, normalized: dict[str, Any]) -> list[str]:
    # next_required_evidence 只描述人工补证动作，不描述机器人命令。
    if status == ACCEPTED_FOR_OWNER_RESPONSE_INTAKE:
        return ["run owner response intake under the same safe evidence_ref without success/control claims"]
    if status == OWNER_RESPONSE_PENDING:
        return ["wait for field owner response under the same safe evidence_ref"] + list(DEFAULT_MISSING_REQUIRED_EVIDENCE)
    if status == OWNER_RESPONSE_OVERDUE:
        return ["escalate overdue field owner response to support escalation owner"] + list(DEFAULT_MISSING_REQUIRED_EVIDENCE)
    if status == BLOCKED_UNSAFE_MATERIAL_CLAIMS:
        return ["resubmit sanitized reviewer ACK review handoff without unsafe raw, control, credential, or success claims"]
    if status == BLOCKED_MISSING_REVIEWER_ACK_HANDOFF:
        return ["provide supported reviewer ACK review handoff artifact, summary, or Robot safe alias"]
    return normalized["next_required_evidence"] or list(DEFAULT_MISSING_REQUIRED_EVIDENCE)


def _field_owner_handoff(normalized: dict[str, Any], followup_status: str, due_status: str, next_required: list[str]) -> dict[str, Any]:
    # field owner 只拿补证/路由流程，不拿 raw ACK、raw handoff 或控制入口。
    if followup_status == ACCEPTED_FOR_OWNER_RESPONSE_INTAKE:
        action = "prepare_owner_response_intake_under_same_safe_evidence_ref"
    elif followup_status == OWNER_RESPONSE_OVERDUE:
        action = "respond_to_overdue_escalation_with_missing_required_evidence"
    elif followup_status == OWNER_RESPONSE_PENDING:
        action = "collect_owner_response_material_without_success_or_control_claims"
    else:
        action = "repair_reviewer_ack_handoff_or_missing_materials_before_owner_response_intake"
    return {
        **_safe_flags(),
        "role": "field owner",
        "followup_status": followup_status,
        "due_status": due_status,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "source_handoff_status": normalized["source_handoff_status"],
        "reviewer_ack_status": normalized["reviewer_ack_state"] or "missing",
        "next_action": action,
        "next_required_evidence": next_required,
    }


def _support_escalation(normalized: dict[str, Any], followup_status: str, due_status: str, reasons: list[str], next_required: list[str]) -> dict[str, Any]:
    # support escalation 只生成可读状态，不生成 ACK/cursor/fetch/robot command。
    return {
        **_safe_flags(),
        "role": "support escalation owner",
        "owner": normalized["support_escalation_owner"] or "support",
        "followup_status": followup_status,
        "due_status": due_status,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "escalate": followup_status == OWNER_RESPONSE_OVERDUE,
        "blocked_or_rejected_reasons": reasons if followup_status.startswith("blocked_") else [],
        "next_required_evidence": next_required,
    }


def _phone_safe_copy(followup_status: str, due_status: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # phone-safe copy 是字段白名单，便于 Robot/mobile 显示但不携带 raw artifact。
    return {
        **_safe_flags(),
        "capability": CAPABILITY,
        "followup_status": followup_status,
        "due_status": due_status,
        "source_handoff_status": normalized["source_handoff_status"] or "missing",
        "reviewer_ack_status": normalized["reviewer_ack_state"] or "missing",
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "copy": (
            f"{CAPABILITY}: followup_status={followup_status}; due_status={due_status}; "
            f"source_handoff_status={normalized['source_handoff_status'] or 'missing'}; "
            f"reviewer_ack_status={normalized['reviewer_ack_state'] or 'missing'}; "
            f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; "
            f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; not_proven; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        ),
    }


def build_field_evidence_material_resolution_reviewer_ack_followup_escalation_status(
    reviewer_ack_review_handoff_json: str,
    due_status: str = "overdue",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 reviewer ACK followup escalation；accepted 也只是 intake readiness。"""
    normalized_due_status = due_status if due_status in {"pending", "overdue", "accepted"} else "overdue"
    payload, read_issue = _read_json(reviewer_ack_review_handoff_json)
    normalized = _normalize_source(payload, read_issue, evidence_ref)
    followup_status, reasons = _followup_status(normalized, normalized_due_status)
    next_required = _next_required(followup_status, normalized)
    field_owner_handoff = _field_owner_handoff(normalized, followup_status, normalized_due_status, next_required)
    support_escalation = _support_escalation(normalized, followup_status, normalized_due_status, reasons, next_required)
    phone_safe_copy = _phone_safe_copy(followup_status, normalized_due_status, normalized)
    missing_required = next_required if followup_status != ACCEPTED_FOR_OWNER_RESPONSE_INTAKE else []
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "followup_status": followup_status,
        "allowed_followup_statuses": list(FOLLOWUP_STATUSES),
        "due_status": normalized_due_status if followup_status != BLOCKED_MISSING_REVIEWER_ACK_HANDOFF else "blocked_missing_reviewer_ack_handoff",
        "source_handoff_status": normalized["source_handoff_status"],
        "reviewer_ack_status": normalized["reviewer_ack_state"] or "missing",
        "source_review_decision": normalized["source_review_decision"],
        "ack_owner": normalized["ack_owner"],
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "followup_reasons": reasons,
        "missing_required_evidence": missing_required,
        "rejected_or_unsafe_reasons": reasons if followup_status == BLOCKED_UNSAFE_MATERIAL_CLAIMS else [],
        "next_required_evidence": next_required,
        "field_owner_handoff": field_owner_handoff,
        "support_escalation_owner": support_escalation,
        "phone_safe_copy": phone_safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "safe_copy": phone_safe_copy["copy"],
        "proof_flags": {
            **_safe_flags(),
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            CAPABILITY,
            EVIDENCE_BOUNDARY,
            "source=software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            OWNER_RESPONSE_PENDING,
            OWNER_RESPONSE_OVERDUE,
            BLOCKED_MISSING_REQUIRED_MATERIALS,
            BLOCKED_UNSAFE_MATERIAL_CLAIMS,
            ACCEPTED_FOR_OWNER_RESPONSE_INTAKE,
            BLOCKED_MISSING_REVIEWER_ACK_HANDOFF,
        ],
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_material_resolution_reviewer_ack_followup_escalation_status": followup_status,
        **common,
        "source_reviewer_ack_handoff_diagnostics": {
            "schema_supported": _schema_supported(normalized),
            "read_issue": read_issue,
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
    artifact["field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"] = summary
    artifact[ROBOT_ALIAS] = summary
    artifact["robot_diagnostics_summary"] = summary
    artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0 if followup_status in {OWNER_RESPONSE_PENDING, OWNER_RESPONSE_OVERDUE, ACCEPTED_FOR_OWNER_RESPONSE_INTAKE} else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 不提供 fetch、ACK、cursor 或 robot command，只处理本地 safe JSON。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status.v1 from a "
            "sanitized field_evidence_material_resolution_reviewer_ack_review_handoff artifact, summary, or Robot alias. "
            "Keeps source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, "
            "safe_to_control=false."
        )
    )
    parser.add_argument("--input", default="", help="sanitized reviewer ACK review handoff artifact, summary, or Robot alias JSON")
    parser.add_argument(
        "--due-status",
        choices=("pending", "overdue", "accepted"),
        default="overdue",
        help="owner response due state to encode without proving completion",
    )
    parser.add_argument("--evidence-ref", default="", help="optional expected safe evidence_ref; mismatch fails closed")
    parser.add_argument("--output", type=Path, help="optional path for sanitized followup artifact JSON")
    parser.add_argument("--summary-output", type=Path, help="optional path for sanitized followup summary JSON")
    parser.add_argument("--output-dir", type=Path, help="optional directory for default artifact and summary names")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_reviewer_ack_followup_escalation_status(
        args.input,
        args.due_status,
        args.evidence_ref,
    )
    if args.output_dir:
        _write_json(args.output_dir / "field_evidence_material_resolution_reviewer_ack_followup_escalation_status.json", artifact)
        _write_json(args.output_dir / "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if not (args.output_dir or args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
