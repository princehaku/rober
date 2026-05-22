#!/usr/bin/env python3
"""生成 reviewer ACK intake 的 PC-only evidence gate。

该 gate 只消费上一轮
`field_evidence_material_resolution_owner_response_review_handoff` 的 safe
artifact、summary、Robot alias 或 wrapper，并读取 reviewer/support/field-owner 的
脱敏 ACK material。输出 canonical ACK artifact / summary，但仍固定为
Docker-only software proof，不证明真实云、真实手机、HIL、PR #5 resolved、
route/elevator field pass、verified terminal result 或 delivery success。
"""

from __future__ import annotations

# 设计约束 01：只读取上一轮 handoff safe surface，不读取 raw 现场材料。
# 设计约束 02：ACK 只表达 reviewer/support/field-owner 已接收或要求转派。
# 设计约束 03：acknowledged 不是 reviewer resolution，也不是 PR thread resolved。
# 设计约束 04：needs_reassignment 只描述 owner 路由变化，不触发机器人动作。
# 设计约束 05：source=software_proof、not_proven 和三个 false flag 必须固定。
# 设计约束 06：同一 safe evidence_ref 是 handoff 到 ACK intake 的唯一主键。
# 设计约束 07：缺 handoff、坏 JSON、unsupported schema 或弱 ref 一律 blocked。
# 设计约束 08：success/control/cloud/phone/HIL/PR resolution claim 一律 rejected。
# 设计约束 09：输出不得复制 raw material、路径、凭证、checksum 或控制命令。
# 设计约束 10：CLI 不访问 ROS graph、Nav2、硬件、云、GitHub 或真实手机。
# 设计约束 11：中文注释保留边界，避免 ACK 被误读成真实验收。
# 设计约束 12：本文件不新增硬件假设，因此不读取 vendor 资料细节。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_resolution_owner_response_review_handoff as handoff_gate


SCHEMA = "trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_reviewer_ack_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_reviewer_ack_intake"
SOURCE_CAPABILITY = handoff_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate"
SOURCE_BOUNDARY = handoff_gate.EVIDENCE_BOUNDARY

ACK_ACKNOWLEDGED = "acknowledged"
ACK_NEEDS_REASSIGNMENT = "needs_reassignment"
ACK_BLOCKED_MISSING_HANDOFF = "blocked_missing_handoff"
ACK_REJECTED_UNSAFE = "rejected_unsafe_ack"
ACK_STATES = (
    ACK_ACKNOWLEDGED,
    ACK_NEEDS_REASSIGNMENT,
    ACK_BLOCKED_MISSING_HANDOFF,
    ACK_REJECTED_UNSAFE,
)

SUPPORTED_SOURCE_SCHEMAS = {
    handoff_gate.SCHEMA,
    handoff_gate.SUMMARY_SCHEMA,
    handoff_gate.ROBOT_ALIAS,
    f"trashbot.{handoff_gate.ROBOT_ALIAS}.v1",
}

ACK_SCHEMAS = {
    "",
    "trashbot.field_evidence_material_resolution_reviewer_ack_packet.v1",
    "trashbot.field_evidence_material_resolution_reviewer_ack_packet_summary.v1",
}

WRAPPER_KEYS = (
    "field_evidence_material_resolution_owner_response_review_handoff",
    "field_evidence_material_resolution_owner_response_review_handoff_summary",
    handoff_gate.ROBOT_ALIAS,
    "field_evidence_material_resolution_reviewer_ack_packet",
    "field_evidence_material_resolution_reviewer_ack_packet_summary",
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
    "cursor",
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
    re.compile(r"(?i)\b(real phone proof|true phone proof|cloud proof|field proof|HIL proof)\b"),
)

NOT_PROVEN_ITEMS = (
    "real_reviewer_resolution",
    "real_owner_acceptance",
    "real_material_review_completion",
    "real_route_elevator_field_pass",
    "verified_terminal_result",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "hardware_or_hil_pass",
    "delivery_success",
    "pr5_reviewer_resolution",
)

BOUNDARY_NOTE = (
    "field_evidence_material_resolution_reviewer_ack_intake; "
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false"
)


def _utc_now() -> str:
    # UTC 时间戳让 Docker-only evidence 在跨时区 review 时排序稳定。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个消费层重复 false flags，避免局部 summary 被误当可控状态。
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
    # 安全扫描使用稳定 JSON，覆盖 nested key/value 的越界 claim。
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


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 列表字段只输出短文本，并过滤本机路径类片段。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("action") or item.get("summary") or item.get("reason"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _read_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 blocked/rejected，不抛 traceback。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
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
    # 优先选择 schema/capability 命中的 owner-response handoff surface。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _find_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # ACK packet 可带 schema，也可作为 owner-safe 表单输入。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        if schema in ACK_SCHEMAS and (_ack_state(candidate) in {ACK_ACKNOWLEDGED, ACK_NEEDS_REASSIGNMENT} or _ack_ref(candidate)):
            return candidate
    return payload


def _boundary(payload: dict[str, Any]) -> str:
    # source boundary 可以在 evidence_boundary 或 boundary 字段中出现。
    return _safe_text(payload.get("evidence_boundary") or payload.get("boundary"))


def _source_ref(source: dict[str, Any]) -> tuple[str, list[str]]:
    # 多个 safe evidence_ref 必须一致，避免不同现场材料被拼成一个 ACK。
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


def _ack_ref(ack: dict[str, Any]) -> str:
    # ACK evidence_ref 必须和 handoff 使用同一 safe id。
    return _safe_text(ack.get("safe_evidence_ref") or ack.get("evidence_ref"))


def _ack_schema(ack: dict[str, Any]) -> str:
    # 空 schema 代表脱敏表单输入；非空必须在白名单内。
    return _safe_text(ack.get("schema"))


def _ack_state(ack: dict[str, Any]) -> str:
    # 只接受本 gate 的两个正向 ACK 输入；其他值 fail closed。
    for key in (
        "reviewer_ack_state",
        "reviewer_acknowledgement_state",
        "reviewer_acknowledgment_state",
        "ack_state",
        "acknowledgement_state",
        "acknowledgment_state",
        "status",
    ):
        value = _safe_text(ack.get(key)).lower()
        if value in {ACK_ACKNOWLEDGED, ACK_NEEDS_REASSIGNMENT}:
            return value
    if ack.get("acknowledged") is True or ack.get("reviewer_acknowledged") is True:
        return ACK_ACKNOWLEDGED
    return ACK_BLOCKED_MISSING_HANDOFF


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
    # 输入任何层把 false-state flag 改成 true，都不能进入 ACK intake。
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


def _software_not_proven(value: dict[str, Any]) -> bool:
    # source/ACK 合同必须保持 software_proof / not_proven / false flags。
    encoded = _encoded(value)
    return (
        _safe_text(value.get("source")) == SOURCE
        and "not_proven" in encoded
        and value.get("delivery_success") is False
        and value.get("primary_actions_enabled") is False
        and value.get("safe_to_control") is False
    )


def _source_supported(normalized: dict[str, Any]) -> bool:
    # schema 或 capability 命中，并且边界必须是上一轮 handoff gate。
    if normalized["source_schema"] in SUPPORTED_SOURCE_SCHEMAS and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and normalized["source_boundary"] == SOURCE_BOUNDARY:
        return True
    return False


def _normalize(
    source_payload: dict[str, Any],
    source_issue: str,
    ack_payload: dict[str, Any],
    ack_issue: str,
    requested_ref: str,
) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，输出不会直接引用输入原对象。
    source = _find_source(source_payload) if source_payload else {}
    ack = _find_ack(ack_payload) if ack_payload else {}
    source_ref, ref_errors = _source_ref(source) if source else ("", [])
    ack_ref = _ack_ref(ack) if ack else ""
    expected_ref = _safe_text(requested_ref or source_ref)
    if expected_ref and (not SAFE_EVIDENCE_REF_RE.fullmatch(expected_ref) or PATH_LIKE_RE.search(expected_ref)):
        ref_errors.append("unsafe_requested_evidence_ref")
    return {
        "source_issue": source_issue,
        "ack_issue": ack_issue,
        "source": source,
        "ack": ack,
        "source_schema": _safe_text(source.get("schema")),
        "source_boundary": _boundary(source),
        "source_capability": _safe_text(source.get("capability")),
        "source_handoff_status": _safe_text(source.get("handoff_status") or source.get("field_evidence_material_resolution_owner_response_review_handoff")),
        "safe_evidence_ref": expected_ref if expected_ref and not ref_errors else "",
        "source_ref": source_ref,
        "ack_ref": ack_ref,
        "ref_errors": list(dict.fromkeys(ref_errors)),
        "ack_schema": _ack_schema(ack),
        "ack_state": _ack_state(ack),
        "ack_owner": _safe_text(ack.get("ack_owner") or ack.get("owner") or ack.get("reviewer") or ack.get("support_owner"), "reviewer"),
        "acknowledged_at": _safe_text(ack.get("acknowledged_at") or ack.get("received_at") or ack.get("reviewed_at"), "not_provided"),
        "reassignment_target": _safe_text(ack.get("reassignment_target") or ack.get("new_owner") or ack.get("target_owner"), "not_provided"),
        "ack_reasons": _safe_list(ack.get("ack_reasons") or ack.get("reasons") or ack.get("notes")),
        "next_required_evidence": _safe_list(source.get("next_required_evidence")),
        "source_is_software_not_proven": _software_not_proven(source) if source else False,
        "ack_is_software_not_proven": _software_not_proven(ack) if ack else False,
        "unsafe_reasons": (_unsafe_reasons(source) if source else []) + (_unsafe_reasons(ack) if ack else []),
        "same_ref_required": source.get("same_evidence_ref_required", True) if source else True,
        "ack_same_ref_required": ack.get("same_evidence_ref_required", True) if ack else True,
    }


def _ack_intake_state(normalized: dict[str, Any]) -> tuple[str, list[str]]:
    # fail-closed 优先级：缺 source -> unsafe -> ref mismatch -> ACK 映射。
    if normalized["source_issue"]:
        return ACK_BLOCKED_MISSING_HANDOFF, [normalized["source_issue"]]
    if not _source_supported(normalized):
        return ACK_BLOCKED_MISSING_HANDOFF, ["unsupported_owner_response_review_handoff_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return ACK_REJECTED_UNSAFE, list(dict.fromkeys(normalized["unsafe_reasons"]))
    if not normalized["source_is_software_not_proven"]:
        return ACK_REJECTED_UNSAFE, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or normalized["same_ref_required"] is not True:
        return ACK_BLOCKED_MISSING_HANDOFF, normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"]
    if normalized["source_ref"] != normalized["safe_evidence_ref"]:
        return ACK_BLOCKED_MISSING_HANDOFF, [f"source_ref:{normalized['source_ref'] or 'missing'}!={normalized['safe_evidence_ref']}"]
    if normalized["source_handoff_status"] not in {
        handoff_gate.HANDOFF_READY,
        handoff_gate.HANDOFF_NEEDS_MORE,
        handoff_gate.HANDOFF_REJECTED,
        handoff_gate.HANDOFF_BLOCKED,
    }:
        return ACK_BLOCKED_MISSING_HANDOFF, ["unsupported_or_missing_source_handoff_status"]
    if normalized["ack_issue"]:
        return ACK_BLOCKED_MISSING_HANDOFF, [normalized["ack_issue"]]
    if normalized["ack_schema"] not in ACK_SCHEMAS:
        return ACK_REJECTED_UNSAFE, ["unsupported_reviewer_ack_schema"]
    if not normalized["ack_is_software_not_proven"]:
        return ACK_REJECTED_UNSAFE, ["ack_not_software_proof_not_proven_or_false_flags_changed"]
    if normalized["ack_same_ref_required"] is not True:
        return ACK_BLOCKED_MISSING_HANDOFF, ["ack_same_evidence_ref_required_not_true"]
    if normalized["ack_ref"] != normalized["safe_evidence_ref"]:
        return ACK_BLOCKED_MISSING_HANDOFF, [f"ack_ref:{normalized['ack_ref'] or 'missing'}!={normalized['safe_evidence_ref']}"]
    if normalized["ack_state"] == ACK_ACKNOWLEDGED:
        return ACK_ACKNOWLEDGED, ["reviewer_acknowledgement_received_but_all_outcomes_remain_not_proven"]
    if normalized["ack_state"] == ACK_NEEDS_REASSIGNMENT:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_requested_safe_owner_reassignment_without_success_claim"]
    return ACK_BLOCKED_MISSING_HANDOFF, ["reviewer_ack_missing_or_unsupported_state"]


def _next_required(normalized: dict[str, Any], ack_state: str, reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证动作，不描述机器人命令。
    if ack_state == ACK_ACKNOWLEDGED:
        return [
            "keep reviewer ACK attached to the same safe evidence_ref",
            "wait for separate real materials before any field/cloud/phone/HIL/delivery claim",
        ]
    if ack_state == ACK_NEEDS_REASSIGNMENT:
        return [
            f"route sanitized handoff to {normalized['reassignment_target']} under the same safe evidence_ref",
            "collect replacement owner ACK before material review continues",
        ]
    if ack_state == ACK_REJECTED_UNSAFE:
        return reasons
    return ["provide_supported_owner_response_review_handoff_and_reviewer_ack_packet_under_same_safe_evidence_ref"]


def _reviewer_acknowledgement(normalized: dict[str, Any], ack_state: str, reasons: list[str]) -> dict[str, Any]:
    # ACK summary 只复制安全 owner 元数据和分类，不包含 raw packet 文案。
    return {
        **_safe_flags(),
        "schema": normalized["ack_schema"] or "reviewer_safe_ack_form",
        "reviewer_ack_state": ack_state,
        "allowed_ack_states": list(ACK_STATES),
        "ack_owner": normalized["ack_owner"],
        "acknowledged_at": normalized["acknowledged_at"],
        "reassignment_target": normalized["reassignment_target"] if ack_state == ACK_NEEDS_REASSIGNMENT else "",
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "ack_reasons": normalized["ack_reasons"] or reasons,
    }


def _source_summary(normalized: dict[str, Any]) -> dict[str, Any]:
    # source summary 只保留 handoff gate 的合同字段，避免完整 source 复制。
    return {
        **_safe_flags(),
        "schema": normalized["source_schema"],
        "capability": normalized["source_capability"],
        "evidence_boundary": normalized["source_boundary"],
        "handoff_status": normalized["source_handoff_status"],
        "safe_evidence_ref": normalized["source_ref"],
        "evidence_ref": normalized["source_ref"],
        "same_evidence_ref_required": normalized["same_ref_required"] is True,
        "source_is_software_proof_not_proven": normalized["source_is_software_not_proven"],
    }


def _safe_copy(ack_state: str, normalized: dict[str, Any], reasons: list[str]) -> str:
    # safe_copy 是短文本白名单，便于 Robot/mobile 显示但不携带 raw artifact。
    return (
        f"{CAPABILITY}: reviewer_ack_state={ack_state}; "
        f"source_handoff_status={normalized['source_handoff_status'] or 'blocked'}; "
        f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; "
        f"reason={';'.join(reasons)[:120]}; "
        f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; not_proven; "
        "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )


def build_field_evidence_material_resolution_reviewer_ack_intake(
    handoff_json: str,
    reviewer_ack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 reviewer ACK intake；acknowledged 也只是 not_proven。"""
    source_payload, source_issue = _read_json(handoff_json, "handoff_json")
    ack_payload, ack_issue = _read_json(reviewer_ack_json, "reviewer_ack_json")
    normalized = _normalize(source_payload, source_issue, ack_payload, ack_issue, evidence_ref)
    ack_state, reasons = _ack_intake_state(normalized)
    next_required = _next_required(normalized, ack_state, reasons)
    source_view = _source_summary(normalized)
    reviewer_ack = _reviewer_acknowledgement(normalized, ack_state, reasons)
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["source_schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "reviewer_ack_state": ack_state,
        "field_evidence_material_resolution_reviewer_ack_intake": ack_state,
        "allowed_ack_states": list(ACK_STATES),
        "source_handoff_status": normalized["source_handoff_status"],
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "ack_reasons": reasons,
        "source_handoff": source_view,
        "reviewer_acknowledgement": reviewer_ack,
        "next_required_evidence": next_required,
        "summary_alias": ROBOT_ALIAS,
        "safe_copy": _safe_copy(ack_state, normalized, reasons),
        "proof_flags": {
            **_safe_flags(),
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
        "non_access_scope": [
            "raw_field_materials",
            "real route/elevator runtime",
            "real delivery result",
            "real phone browser runtime",
            "robot control channels",
            "hardware serial or transport details",
            "github reviewer resolution mutation",
            "credential_or_database_queue_connection_material",
        ],
        "safety_markers": [
            CAPABILITY,
            EVIDENCE_BOUNDARY,
            "source=software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            ACK_ACKNOWLEDGED,
            ACK_NEEDS_REASSIGNMENT,
            ACK_BLOCKED_MISSING_HANDOFF,
            ACK_REJECTED_UNSAFE,
        ],
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **common,
        "reviewer_ack_intake_diagnostics": {
            "source_supported": _source_supported(normalized),
            "source_issue": source_issue,
            "ack_issue": ack_issue,
            "source_is_software_proof_not_proven": normalized["source_is_software_not_proven"],
            "ack_is_software_proof_not_proven": normalized["ack_is_software_not_proven"],
            "unsafe_reasons": list(dict.fromkeys(normalized["unsafe_reasons"])),
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
    artifact["field_evidence_material_resolution_reviewer_ack_intake_summary"] = summary
    artifact[ROBOT_ALIAS] = summary
    artifact["robot_diagnostics_summary"] = summary
    artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0 if ack_state in {ACK_ACKNOWLEDGED, ACK_NEEDS_REASSIGNMENT} else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 不提供 fetch、GitHub resolve、ACK cursor 或 robot command，只处理 safe JSON。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1 from a sanitized "
            "field_evidence_material_resolution_owner_response_review_handoff safe artifact/summary/Robot alias plus "
            "a reviewer-safe ACK packet. Keeps source=software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--handoff-json", default="", help="sanitized owner response review handoff artifact, summary, or Robot alias JSON")
    parser.add_argument("--reviewer-ack-json", default="", help="reviewer/support/field-owner safe ACK packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for reviewer ACK intake")
    parser.add_argument("--output", type=Path, help="optional path for sanitized ACK intake artifact JSON")
    parser.add_argument("--summary-output", type=Path, help="optional path for sanitized ACK intake summary JSON")
    parser.add_argument("--output-dir", type=Path, help="optional directory for default artifact and summary names")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_material_resolution_reviewer_ack_intake(
        args.handoff_json,
        args.reviewer_ack_json,
        args.evidence_ref,
    )
    if args.output_dir:
        _write_json(args.output_dir / "field_evidence_material_resolution_reviewer_ack_intake.json", artifact)
        _write_json(args.output_dir / "field_evidence_material_resolution_reviewer_ack_intake_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if not (args.output_dir or args.output or args.summary_output):
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
