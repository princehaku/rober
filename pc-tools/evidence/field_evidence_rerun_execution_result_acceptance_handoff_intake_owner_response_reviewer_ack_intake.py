#!/usr/bin/env python3
"""生成 rerun acceptance owner-response reviewer ACK intake gate。

该 PC-only gate 只消费上一跳
`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff`
的 safe artifact、summary、Robot safe alias 或 wrapper，并读取 reviewer ACK
packet。输出只表示 reviewer 已对上一跳 owner/support/reviewer handoff 做脱敏 ACK
或要求转派；它不读取 raw field materials，不访问 ROS/Nav2/硬件/云/手机，也不触发
机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff as previous_handoff
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
ACK_PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_packet.v1"
SCHEMA_VERSION = 1

CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake"
SOURCE_CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate"
SOURCE_BOUNDARY = previous_handoff.HANDOFF_BOUNDARY

ACK_ACKNOWLEDGED = "reviewer_acknowledged_not_proven"
ACK_NEEDS_REASSIGNMENT = "reviewer_ack_needs_reassignment"
ACK_EVIDENCE_REF_MISMATCH = "reviewer_ack_evidence_ref_mismatch"
ACK_REJECTED_UNSAFE = "reviewer_ack_rejected_unsafe"
BLOCKED_MISSING_HANDOFF = "blocked_missing_owner_response_review_handoff"
ALLOWED_ACK_STATES = (
    ACK_ACKNOWLEDGED,
    ACK_NEEDS_REASSIGNMENT,
    ACK_EVIDENCE_REF_MISMATCH,
    ACK_REJECTED_UNSAFE,
    BLOCKED_MISSING_HANDOFF,
)

SUPPORTED_SOURCE_SCHEMAS = {
    previous_handoff.HANDOFF_SCHEMA,
    previous_handoff.HANDOFF_SUMMARY_SCHEMA,
    f"trashbot.robot_diagnostics_{SOURCE_CAPABILITY}_summary.v1",
    ROBOT_ALIAS.replace(CAPABILITY, SOURCE_CAPABILITY),
}

ACK_SCHEMAS = {
    "",
    ACK_PACKET_SCHEMA,
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_packet_summary.v1",
}

SOURCE_WRAPPER_KEYS = (
    SOURCE_CAPABILITY,
    f"{SOURCE_CAPABILITY}_summary",
    f"robot_diagnostics_{SOURCE_CAPABILITY}_summary",
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
)

ACK_WRAPPER_KEYS = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_packet",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_packet_summary",
    "reviewer_ack_packet",
    "reviewer_ack",
    "ack_packet",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
)

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,100}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")

FORBIDDEN_KEY_TERMS = (
    "raw",
    "artifact_path",
    "local_path",
    "file_path",
    "log_path",
    "checksum",
    "credential",
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
    "hil_pass",
    "o5_external",
    "pr5_resolution",
    "review_thread_resolved",
    "verified_terminal_result",
)

FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw|complete)\s+artifact(s)?\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(verified\s+terminal\s+result|route/elevator\s+field\s+pass|field\s+pass)\b"),
    re.compile(r"(?i)\b(objective\s*5|o5)\s+(external\s+)?(proof|resolved|complete|ready)\b"),
    re.compile(r"(?i)\b(hil|o1)\s+(pass|passed|proof|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(pr\s*#?5|PRRT_[A-Za-z0-9]+).*(resolved|resolution|closed)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action|command)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial)\b"),
)

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; reviewer_acknowledged_not_proven; "
    "reviewer_ack_needs_reassignment; blocked_missing_owner_response_review_handoff; "
    "reviewer_ack_evidence_ref_mismatch; reviewer_ack_rejected_unsafe"
)

NOT_PROVEN = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_pass",
    "verified_terminal_result",
    "dropoff_cancel_completion",
    "delivery_result",
    "delivery_success",
    "true_phone_browser_proof",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "o1_hil_or_wave_rover_uart_feedback",
    "pr5_reviewer_resolution",
    "okr_percentage_lift",
)

# 设计约束 01：本 gate 只消费上一跳 review handoff safe output。
# 设计约束 02：reviewer ACK packet 只允许短标签和下一步，不复制 raw material body。
# 设计约束 03：ACK acknowledged 仍是 not_proven，不能被下游当作 reviewer resolution。
# 设计约束 04：needs_reassignment 只改变人工 owner 路由，不启用控制。
# 设计约束 05：source=software_proof、software_proof 和 not_proven 必须固定。
# 设计约束 06：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 07：上一跳 capability、boundary 和 same evidence_ref 必须同时满足。
# 设计约束 08：missing source/status/schema 不能从 ACK packet 推导通过。
# 设计约束 09：unsafe/raw/path/credential/ROS/control/hardware/HIL claim 一律拒绝。
# 设计约束 10：O5 external、O1 HIL、PR #5 resolution 和 success claim 一律拒绝。
# 设计约束 11：输出只给 Robot/mobile 只读 safe summary，不泄漏 ACK body。
# 设计约束 12：本文件不新增硬件参数或协议假设，因此不读取 vendor 资料。


def _utc_now() -> str:
    # UTC 让不同 PC/Docker 主机产物按文本排序稳定。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个嵌套 summary 重复 false flags，避免局部消费面被误解为可控。
    return {
        "source": "software_proof",
        "software_proof": True,
        "status": "not_proven",
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "no_okr_percentage_lift": True,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 输出字段只保留单行短文本，避免 raw JSON 或日志穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return material_pack._safe_text(text)[:240] or default


def _safe_list(value: Any, limit: int = 24) -> list[str]:
    # 列表仅保留短标签；路径类、空值和重复项会被剔除。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("step") or item.get("reason") or item.get("summary") or item.get("label"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _read_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 读取失败转为 fail-closed 状态，不抛 traceback 给调用方。
    if not path:
        return {}, f"{label}_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"{label}_json_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_json_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_json_not_object"
    return payload, ""


def _encoded(value: Any) -> str:
    # 稳定 JSON 便于递归扫描 nested key/value 的越界 claim。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object；字符串化 JSON 不会被自动展开。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any], wrapper_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # 只递归固定 safe wrapper key，防止 raw payload 被当成 source。
    candidates = [payload]
    for key in wrapper_keys:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child, wrapper_keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 需要命中上一跳 schema、capability 或 Robot safe alias。
    for candidate in _candidates(payload, SOURCE_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        encoded = _encoded(candidate)
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY or SOURCE_CAPABILITY in encoded:
            return candidate
    return payload


def _find_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # ACK packet 支持 schema 化输入，也支持现场 reviewer 的最小 safe JSON。
    for candidate in _candidates(payload, ACK_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        if schema in ACK_SCHEMAS and (_ack_ref(candidate) or _ack_state(candidate)):
            return candidate
    return payload


def _safe_ref(value: Any) -> str:
    # same evidence_ref 是唯一关联键，弱 ref 和路径 ref 一律视为缺失。
    ref = material_pack._safe_ref(_safe_text(value))
    if not ref or not SAFE_EVIDENCE_REF_RE.fullmatch(ref) or PATH_LIKE_RE.search(ref):
        return ""
    return ref


def _source_ref(source: dict[str, Any]) -> str:
    # 上一跳 summary 可能把 ref 放在 top-level、safe_copy 或 owner_handoff。
    refs: list[str] = []
    for candidate in _candidates(source, SOURCE_WRAPPER_KEYS):
        for key in ("safe_evidence_ref", "evidence_ref"):
            ref = _safe_ref(candidate.get(key))
            if ref:
                refs.append(ref)
    unique_refs = list(dict.fromkeys(refs))
    return unique_refs[0] if len(unique_refs) == 1 else ""


def _ack_ref(ack: dict[str, Any]) -> str:
    # ACK packet 必须显式带同一个 safe evidence_ref。
    return _safe_ref(ack.get("safe_evidence_ref") or ack.get("evidence_ref"))


def _ack_state(ack: dict[str, Any]) -> str:
    # 兼容 acknowledged/needs_reassignment 输入，但输出使用本 gate 的 canonical 状态。
    for key in ("reviewer_ack_state", "ack_state", "acknowledgement_state", "acknowledgment_state", "status"):
        value = _safe_text(ack.get(key)).lower()
        if value in {ACK_ACKNOWLEDGED, "acknowledged", "reviewer_acknowledged"}:
            return ACK_ACKNOWLEDGED
        if value in {ACK_NEEDS_REASSIGNMENT, "needs_reassignment", "reassignment_requested"}:
            return ACK_NEEDS_REASSIGNMENT
    if ack.get("acknowledged") is True or ack.get("reviewer_acknowledged") is True:
        return ACK_ACKNOWLEDGED
    return ""


def _source_status(source: dict[str, Any]) -> str:
    # 上一跳 handoff 状态字段在 artifact/summary/safe_copy 中位置可能不同。
    for candidate in _candidates(source, SOURCE_WRAPPER_KEYS):
        status = _safe_text(candidate.get("handoff_status") or candidate.get("status"))
        if status:
            return status
    return ""


def _source_boundary(source: dict[str, Any]) -> str:
    # boundary 可以用 evidence_boundary 或 boundary 表达，但必须等于上一跳 boundary。
    return _safe_text(source.get("evidence_boundary") or source.get("boundary"))


def _source_schema(source: dict[str, Any]) -> str:
    # schema 是 source 支持性判断的一部分，避免跨 gate 串链。
    return _safe_text(source.get("schema"))


def _source_has_required_capability(source: dict[str, Any]) -> bool:
    # 任务要求上一跳 safe output 必须包含 previous capability；允许顶层或 safe_copy 中出现。
    return _safe_text(source.get("capability")) == SOURCE_CAPABILITY or SOURCE_CAPABILITY in _encoded(source)


def _has_supported_source_contract(source: dict[str, Any]) -> bool:
    # schema/boundary/capability 三者同时满足，才允许进入 ACK intake。
    return (
        bool(source)
        and _source_schema(source) in SUPPORTED_SOURCE_SCHEMAS
        and _source_boundary(source) == SOURCE_BOUNDARY
        and _source_has_required_capability(source)
    )


def _is_software_not_proven(payload: dict[str, Any]) -> bool:
    # source 和 ACK 都必须保留 software_proof/not_proven/三个 false flags。
    encoded = _encoded(payload)
    return (
        payload.get("source") == "software_proof"
        and "not_proven" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 不回显敏感字段值，只记录命中的字段路径类别。
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


def _has_true_control_flag(value: Any) -> bool:
    # JSON boolean true 比自然语言更危险，必须递归阻断。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True or value.get("safe_to_control") is True:
            return True
        return any(_has_true_control_flag(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(child) for child in value)
    return False


def _unsafe_reasons(value: dict[str, Any]) -> list[str]:
    # unsafe 原因只输出类别，不输出命中的原始内容。
    if not value:
        return []
    reasons: list[str] = []
    encoded = _encoded(value)
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_hardware_hil_o5_or_resolution_fields")
    if PATH_LIKE_RE.search(encoded) or any(pattern.search(encoded) for pattern in FORBIDDEN_CLAIM_PATTERNS):
        reasons.append("unsafe_raw_path_credential_ros_control_hardware_success_o5_hil_or_pr5_claim")
    if _has_true_control_flag(value):
        reasons.append("true_control_or_success_flag_overclaim")
    if material_pack._has_forbidden_copy(value) or material_pack._has_raw_path_copy(value):
        reasons.append("material_pack_forbidden_copy_or_raw_path")
    return list(dict.fromkeys(reasons))


def _ack_fields(ack: dict[str, Any]) -> dict[str, Any]:
    # ACK 必填字段是短标签和下一步，不允许 raw body。
    return {
        "reviewer_role": _safe_text(ack.get("reviewer_role") or ack.get("role")),
        "reviewer_identity_label": _safe_text(ack.get("reviewer_identity_label") or ack.get("reviewer_label") or ack.get("reviewer")),
        "ack_reason": _safe_text(ack.get("ack_reason") or ack.get("reason")),
        "owner_next_step": _safe_text(ack.get("owner_next_step")),
        "support_next_step": _safe_text(ack.get("support_next_step")),
        "reviewer_next_step": _safe_text(ack.get("reviewer_next_step")),
        "next_required_evidence": _safe_list(ack.get("next_required_evidence")),
        "reassignment_target": _safe_text(ack.get("reassignment_target") or ack.get("new_owner") or ack.get("target_owner")),
    }


def _missing_ack_fields(fields: dict[str, Any], ack_state: str) -> list[str]:
    # acknowledged 必须具备 reviewer 身份、ACK 原因、三方下一步和下一证据。
    required = [
        "reviewer_role",
        "reviewer_identity_label",
        "ack_reason",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
    ]
    missing = [key for key in required if not fields.get(key)]
    if not fields["next_required_evidence"]:
        missing.append("next_required_evidence")
    if ack_state == ACK_NEEDS_REASSIGNMENT and not fields["reassignment_target"]:
        missing.append("reassignment_target")
    return missing


def _normalize(
    source_payload: dict[str, Any],
    source_issue: str,
    ack_payload: dict[str, Any],
    ack_issue: str,
    requested_ref: str,
) -> dict[str, Any]:
    # normalized 是唯一决策面，artifact 不直接复制输入对象。
    source = _find_source(source_payload) if source_payload else {}
    ack = _find_ack(ack_payload) if ack_payload else {}
    source_ref = _source_ref(source) if source else ""
    ack_ref = _ack_ref(ack) if ack else ""
    requested = _safe_ref(requested_ref)
    effective_ref = requested or source_ref or ack_ref
    ack_state = _ack_state(ack) if ack else ""
    ack_fields = _ack_fields(ack) if ack else {
        "reviewer_role": "",
        "reviewer_identity_label": "",
        "ack_reason": "",
        "owner_next_step": "",
        "support_next_step": "",
        "reviewer_next_step": "",
        "next_required_evidence": [],
        "reassignment_target": "",
    }
    return {
        "source_issue": source_issue,
        "ack_issue": ack_issue,
        "source": source,
        "ack": ack,
        "source_schema": _source_schema(source),
        "source_boundary": _source_boundary(source),
        "source_capability_present": _source_has_required_capability(source),
        "source_handoff_status": _source_status(source),
        "source_ref": source_ref,
        "ack_ref": ack_ref,
        "requested_ref": requested,
        "safe_evidence_ref": effective_ref,
        "ack_schema": _safe_text(ack.get("schema")) if ack else "",
        "ack_state": ack_state,
        "ack_fields": ack_fields,
        "missing_ack_fields": _missing_ack_fields(ack_fields, ack_state),
        "source_is_safe": _is_software_not_proven(source) if source else False,
        "ack_is_safe": _is_software_not_proven(ack) if ack else False,
        "source_supported": _has_supported_source_contract(source),
        "unsafe_reasons": list(dict.fromkeys((_unsafe_reasons(source) if source else []) + (_unsafe_reasons(ack) if ack else []))),
    }


def _ack_decision(normalized: dict[str, Any]) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：缺 source -> unsafe -> ref mismatch -> ACK 字段。
    if normalized["source_issue"]:
        return BLOCKED_MISSING_HANDOFF, [normalized["source_issue"]], 2
    if not normalized["source_supported"]:
        return BLOCKED_MISSING_HANDOFF, ["unsupported_or_missing_owner_response_review_handoff_schema_boundary_or_capability"], 2
    if normalized["source_handoff_status"] != previous_handoff.READY_HANDOFF:
        return BLOCKED_MISSING_HANDOFF, ["source_owner_response_review_handoff_not_ready"], 2
    if not normalized["source_is_safe"]:
        return ACK_REJECTED_UNSAFE, ["source_not_software_proof_not_proven_or_false_flags_changed"], 5
    if normalized["ack_issue"]:
        return BLOCKED_MISSING_HANDOFF, [normalized["ack_issue"]], 2
    if normalized["unsafe_reasons"]:
        return ACK_REJECTED_UNSAFE, normalized["unsafe_reasons"], 5
    if normalized["ack_schema"] not in ACK_SCHEMAS:
        return ACK_REJECTED_UNSAFE, ["unsupported_reviewer_ack_schema"], 5
    if not normalized["ack_is_safe"]:
        return ACK_REJECTED_UNSAFE, ["ack_not_software_proof_not_proven_or_false_flags_changed"], 5
    if not normalized["safe_evidence_ref"] or not normalized["source_ref"] or not normalized["ack_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["missing_safe_evidence_ref"], 3
    if normalized["requested_ref"] and normalized["requested_ref"] != normalized["safe_evidence_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["requested_evidence_ref_mismatch"], 3
    if normalized["source_ref"] != normalized["safe_evidence_ref"] or normalized["ack_ref"] != normalized["safe_evidence_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["source_ack_or_requested_evidence_ref_mismatch"], 3
    if normalized["ack_state"] not in {ACK_ACKNOWLEDGED, ACK_NEEDS_REASSIGNMENT}:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_ack_missing_or_unsupported_state"], 4
    if normalized["missing_ack_fields"]:
        return ACK_NEEDS_REASSIGNMENT, [f"missing_ack_field:{field}" for field in normalized["missing_ack_fields"]], 4
    if normalized["ack_state"] == ACK_NEEDS_REASSIGNMENT:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_requested_safe_reassignment_without_success_claim"], 0
    return ACK_ACKNOWLEDGED, ["reviewer_acknowledged_not_proven_under_same_safe_evidence_ref"], 0


def _source_summary(normalized: dict[str, Any]) -> dict[str, Any]:
    # source summary 只保留上一跳合同字段，不复制完整 handoff artifact。
    return {
        **_safe_flags(),
        "schema": normalized["source_schema"],
        "capability": SOURCE_CAPABILITY,
        "evidence_boundary": normalized["source_boundary"],
        "handoff_status": normalized["source_handoff_status"],
        "safe_evidence_ref": normalized["source_ref"],
        "evidence_ref": normalized["source_ref"],
        "previous_capability_present": bool(normalized["source_capability_present"]),
        "previous_boundary_present": normalized["source_boundary"] == SOURCE_BOUNDARY,
    }


def _reviewer_ack_summary(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # reviewer_ack 只输出角色/标签/下一步，不输出 ACK packet 原文。
    fields = normalized["ack_fields"]
    return {
        **_safe_flags(),
        "schema": normalized["ack_schema"] or "reviewer_safe_ack_form",
        "reviewer_ack_state": state,
        "reviewer_role": fields["reviewer_role"],
        "reviewer_identity_label": fields["reviewer_identity_label"],
        "ack_reason": fields["ack_reason"] or ";".join(reasons)[:160],
        "owner_next_step": fields["owner_next_step"],
        "support_next_step": fields["support_next_step"],
        "reviewer_next_step": fields["reviewer_next_step"],
        "reassignment_target": fields["reassignment_target"] if state == ACK_NEEDS_REASSIGNMENT else "",
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
    }


def _next_required_evidence(state: str, normalized: dict[str, Any], reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证和复核动作，不包含机器人命令。
    fields = normalized["ack_fields"]
    if state == ACK_ACKNOWLEDGED:
        return fields["next_required_evidence"] or [
            "keep reviewer ACK attached to the same safe evidence_ref",
            "wait for separate real materials before field/cloud/phone/HIL/delivery claims",
        ]
    if state == ACK_NEEDS_REASSIGNMENT:
        return fields["next_required_evidence"] or [
            "assign a reviewer role and identity label under the same safe evidence_ref",
            "resubmit reviewer ACK reason plus owner/support/reviewer next steps",
        ]
    if state == ACK_EVIDENCE_REF_MISMATCH:
        return ["rerun previous handoff and reviewer ACK packet under the same safe evidence_ref"]
    if state == ACK_REJECTED_UNSAFE:
        return ["remove raw material bodies, local paths, credentials, success/control/O5/O1/HIL/PR #5 resolution claims and rerun"]
    return ["provide supported owner response review handoff safe output and reviewer ACK packet under the same safe evidence_ref"]


def _safe_copy(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，字段保持短且稳定。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "reviewer_ack_state": state,
        "ack_reasons": reasons,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": normalized["source_boundary"],
        "source_handoff_status": normalized["source_handoff_status"],
        "boundary_note": BOUNDARY_NOTE,
    }


def _common_payload(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # common payload 让 artifact、summary、Robot alias 三个视图保持同一合同。
    source_summary = _source_summary(normalized)
    ack_summary = _reviewer_ack_summary(state, normalized, reasons)
    next_required = _next_required_evidence(state, normalized, reasons)
    safe_copy = _safe_copy(state, normalized, reasons)
    return {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["source_schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "reviewer_ack_state": state,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake": state,
        "allowed_reviewer_ack_states": list(ALLOWED_ACK_STATES),
        "ack_reasons": reasons,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "source_owner_response_review_handoff": source_summary,
        "reviewer_acknowledgement": ack_summary,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_field_materials",
            "raw_owner_response_review_handoff_body",
            "raw_reviewer_ack_body",
            "ros_graph_or_robot_control",
            "hardware_serial_uart_or_wave_rover",
            "external_cloud_or_o5_probe",
            "real_phone_browser_runtime",
            "github_pr5_resolution_mutation",
            "okr_percentage_update",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            CAPABILITY,
            EVIDENCE_BOUNDARY,
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            ACK_ACKNOWLEDGED,
            ACK_NEEDS_REASSIGNMENT,
            BLOCKED_MISSING_HANDOFF,
            ACK_EVIDENCE_REF_MISMATCH,
            ACK_REJECTED_UNSAFE,
        ],
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
    owner_response_review_handoff_json: str,
    reviewer_ack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 reviewer ACK intake；成功 ACK 仍保持 not_proven。"""
    source_payload, source_issue = _read_json(owner_response_review_handoff_json, "owner_response_review_handoff")
    ack_payload, ack_issue = _read_json(reviewer_ack_json, "reviewer_ack")
    normalized = _normalize(source_payload, source_issue, ack_payload, ack_issue, evidence_ref)
    state, reasons, exit_code = _ack_decision(normalized)
    generated_at = _utc_now()
    common = _common_payload(state, normalized, reasons)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **common,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **common,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "reviewer_ack_intake_diagnostics": {
            "source_issue": source_issue,
            "ack_issue": ack_issue,
            "source_supported": normalized["source_supported"],
            "source_is_software_proof_not_proven": normalized["source_is_safe"],
            "ack_is_software_proof_not_proven": normalized["ack_is_safe"],
            "missing_ack_fields": normalized["missing_ack_fields"],
            "unsafe_reasons": normalized["unsafe_reasons"],
        },
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：如果输出仍被通用 sanitizer 判定危险，强制降级为 unsafe。
        artifact["reviewer_ack_state"] = ACK_REJECTED_UNSAFE
        artifact["status"] = "not_proven"
        summary["reviewer_ack_state"] = ACK_REJECTED_UNSAFE
        summary["status"] = "not_proven"
        exit_code = 5
    return artifact, summary, exit_code


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，不访问 ROS graph、GitHub、硬件、外部云或真实手机。
    parser = argparse.ArgumentParser(
        description=(
            "Generate field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake "
            "from previous owner-response review handoff safe output and a reviewer-safe ACK packet. Keeps "
            "source=software_proof, software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--owner-response-review-handoff-json", required=True, help="previous owner-response review handoff artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--reviewer-ack-json", required=True, help="reviewer-safe ACK packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", default="", help="optional ACK intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional ACK intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print ACK intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
        args.owner_response_review_handoff_json,
        args.reviewer_ack_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{CAPABILITY}: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"{CAPABILITY}_summary_file:{material_pack._safe_ref(args.summary_output)}")
        print(f"reviewer_ack_state: {artifact['reviewer_ack_state']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
