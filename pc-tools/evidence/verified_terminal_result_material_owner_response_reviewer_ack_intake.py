#!/usr/bin/env python3
"""生成 verified terminal result owner-response reviewer ACK intake gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as material_pack
import verified_terminal_result_material_owner_response_review_handoff as previous_handoff


SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
ACK_PACKET_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_packet.v1"
SCHEMA_VERSION = 1

CAPABILITY = "verified_terminal_result_material_owner_response_reviewer_ack_intake"
SOURCE_CAPABILITY = "verified_terminal_result_material_owner_response_review_handoff"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate"
SOURCE_BOUNDARY = previous_handoff.EVIDENCE_BOUNDARY
PR5_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
NO_OKR_LIFT = "no OKR percentage lift"

ACK_ACKNOWLEDGED = "reviewer_acknowledged_not_proven"
ACK_NEEDS_REASSIGNMENT = "reviewer_ack_needs_reassignment"
ACK_EVIDENCE_REF_MISMATCH = "reviewer_ack_evidence_ref_mismatch"
ACK_REJECTED_UNSAFE = "reviewer_ack_rejected_unsafe"
BLOCKED_MISSING_HANDOFF = "blocked_missing_terminal_result_owner_response_review_handoff"
ALLOWED_ACK_STATES = (
    ACK_ACKNOWLEDGED,
    ACK_NEEDS_REASSIGNMENT,
    ACK_EVIDENCE_REF_MISMATCH,
    ACK_REJECTED_UNSAFE,
    BLOCKED_MISSING_HANDOFF,
)

SUPPORTED_SOURCE_SCHEMAS = {
    previous_handoff.ARTIFACT_SCHEMA,
    previous_handoff.SUMMARY_SCHEMA,
    previous_handoff.ROBOT_ALIAS_SCHEMA,
    previous_handoff.ROBOT_ALIAS,
}
ACK_SCHEMAS = {
    "",
    ACK_PACKET_SCHEMA,
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_packet_summary.v1",
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
    "verified_terminal_result_material_owner_response_reviewer_ack_packet",
    "verified_terminal_result_material_owner_response_reviewer_ack_packet_summary",
    "reviewer_ack_packet",
    "reviewer_ack",
    "ack_packet",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
URL_OR_QUEUE_RE = re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb|oss|s3)://|https?://")
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
    "github_thread_resolved",
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
    "verified_terminal_result_material_owner_response_reviewer_ack_intake; "
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate; "
    "verified_terminal_result_material_owner_response_review_handoff; "
    "software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; PRRT_kwDOSWB9286CJ3tX unresolved hardware_material_pending"
)
NOT_PROVEN_ITEMS = (
    "real_terminal_delivery_result",
    "real_terminal_dropoff_result",
    "real_terminal_cancel_result",
    "verified_terminal_result",
    "delivery_success",
    "true_phone_browser_proof",
    "route_elevator_field_pass",
    "public_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "o1_hil_or_wave_rover_uart_feedback",
    "pr5_reviewer_resolution",
    "okr_percentage_lift",
)


def _utc_now() -> str:
    # UTC 时间让本地 PC 和 Docker 产物能按字符串稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个输出层都重复安全旗标，避免下游局部读取时误启用动作。
    return {
        "source": SOURCE,
        "software_proof": True,
        "status": STATUS,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": False,
        "okr_lift_note": NO_OKR_LIFT,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只能作为短单行标签输出，避免 raw JSON、日志或多行 body 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return material_pack._safe_text(text)[:240] or default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 列表只保留短标签；路径、URL、空值和重复项会被剔除。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("step") or item.get("reason") or item.get("summary") or item.get("label"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _read_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 读取错误统一变成可审计 blocked reason，不把 traceback 暴露给用户触点。
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
    # 稳定 JSON 用于递归安全扫描；不可序列化对象降级为短文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，不解析字符串化 JSON，避免 raw payload 被绕过。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any], wrapper_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper key，控制输入可信面。
    candidates = [payload]
    for key in wrapper_keys:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child, wrapper_keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一跳 handoff schema、capability 或 Robot safe alias。
    for candidate in _candidates(payload, SOURCE_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY or SOURCE_CAPABILITY in _encoded(candidate):
            return candidate
    return payload


def _find_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # reviewer ACK 支持 schema 化 packet，也支持最小安全 ACK form。
    for candidate in _candidates(payload, ACK_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        if schema in ACK_SCHEMAS and (_ack_ref(candidate) or _ack_state(candidate)):
            return candidate
    return payload


def _safe_ref(value: Any) -> str:
    # evidence_ref 和 command_id 只能是短安全标识，不能是路径、URL 或凭证。
    text = material_pack._safe_ref(_safe_text(value))
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _source_ref(source: dict[str, Any]) -> str:
    # 上一跳 summary 可能在 top-level 或 safe_copy/handoff packet 里重复 ref。
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
    # 输入可用短状态，输出统一使用本 gate canonical 状态。
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
    # handoff_status 在 artifact/summary/safe_copy 中位置可能不同。
    for candidate in _candidates(source, SOURCE_WRAPPER_KEYS):
        status = _safe_text(candidate.get("handoff_status") or candidate.get("status"))
        if status:
            return status
    return ""


def _source_boundary(source: dict[str, Any]) -> str:
    # boundary 可以用 evidence_boundary 或 boundary 表达，但必须等于上一跳边界。
    return _safe_text(source.get("evidence_boundary") or source.get("boundary"))


def _source_schema(source: dict[str, Any]) -> str:
    # schema 是防止串错 gate 的第一层合同。
    return _safe_text(source.get("schema"))


def _source_has_required_capability(source: dict[str, Any]) -> bool:
    # capability 允许嵌套在 safe_copy 中，因为 Robot/mobile 常消费 summary wrapper。
    return _safe_text(source.get("capability")) == SOURCE_CAPABILITY or SOURCE_CAPABILITY in _encoded(source)


def _has_supported_source_contract(source: dict[str, Any]) -> bool:
    # schema、boundary、capability 三者同时满足才允许进入 reviewer ACK intake。
    return (
        bool(source)
        and _source_schema(source) in SUPPORTED_SOURCE_SCHEMAS
        and _source_boundary(source) == SOURCE_BOUNDARY
        and _source_has_required_capability(source)
    )


def _is_software_not_proven(payload: dict[str, Any]) -> bool:
    # source 和 ACK 都必须保留 software_proof/not_proven/三类 false flag。
    encoded = _encoded(payload)
    return (
        _safe_text(payload.get("source")) == SOURCE
        and "not_proven" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 只记录命中的字段路径类别，不回显敏感字段值。
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
    # unsafe 输出只保留类别，避免二次泄漏 ACK 或 handoff 原文。
    if not value:
        return []
    reasons: list[str] = []
    encoded = _encoded(value)
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_hardware_hil_o5_or_resolution_fields")
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded) or any(pattern.search(encoded) for pattern in FORBIDDEN_CLAIM_PATTERNS):
        reasons.append("unsafe_raw_path_credential_ros_control_hardware_success_o5_hil_or_pr5_claim")
    if _has_true_control_flag(value):
        reasons.append("true_control_or_success_flag_overclaim")
    if material_pack._has_forbidden_copy(value) or material_pack._has_raw_path_copy(value):
        reasons.append("material_pack_forbidden_copy_or_raw_path")
    return list(dict.fromkeys(reasons))


def _ack_fields(ack: dict[str, Any]) -> dict[str, Any]:
    # ACK 只允许 reviewer 身份标签、原因和三方下一步，不复制 raw reviewer body。
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
    # acknowledged 必须能让 owner/support/reviewer 都知道下一步。
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
    effective_ref = requested or source_ref or ack_ref or "missing_safe_evidence_ref"
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
        "safe_command_id": _safe_ref(source.get("safe_command_id") or source.get("command_id")) if source else "",
        "terminal_result_type": _safe_text(source.get("terminal_result_type")) if source else "",
        "unsafe_reasons": list(dict.fromkeys((_unsafe_reasons(source) if source else []) + (_unsafe_reasons(ack) if ack else []))),
    }


def _ack_decision(normalized: dict[str, Any]) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：缺 source -> unsafe -> ref mismatch -> ACK 字段。
    if normalized["source_issue"]:
        return BLOCKED_MISSING_HANDOFF, [normalized["source_issue"]], 2
    if not normalized["source_supported"]:
        return BLOCKED_MISSING_HANDOFF, ["unsupported_or_missing_terminal_result_owner_response_review_handoff_schema_boundary_or_capability"], 2
    if normalized["source_handoff_status"] != previous_handoff.ACCEPTED_STATUS:
        return BLOCKED_MISSING_HANDOFF, ["source_owner_response_review_handoff_not_accepted"], 2
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


def _pr5_thread() -> dict[str, str]:
    # 本地 gate 只记录保守状态，不做 GitHub API mutation。
    return {
        "thread_id": PR5_THREAD_ID,
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
    }


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
        "safe_command_id": normalized["safe_command_id"],
        "command_id": normalized["safe_command_id"],
        "terminal_result_type": normalized["terminal_result_type"],
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
        "pr5_thread": _pr5_thread(),
    }


def _next_required_evidence(state: str, normalized: dict[str, Any], reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证和复核动作，不包含机器人命令。
    fields = normalized["ack_fields"]
    if state == ACK_ACKNOWLEDGED:
        return fields["next_required_evidence"] or [
            "keep reviewer ACK attached to the same safe evidence_ref",
            "wait for real terminal-result materials before delivery or PR #5 resolution claims",
        ]
    if state == ACK_NEEDS_REASSIGNMENT:
        return fields["next_required_evidence"] or [
            "assign reviewer role and identity under the same safe evidence_ref",
            "resubmit reviewer ACK reason plus owner/support/reviewer next steps",
        ]
    if state == ACK_EVIDENCE_REF_MISMATCH:
        return ["rerun previous handoff and reviewer ACK packet under the same safe evidence_ref"]
    if state == ACK_REJECTED_UNSAFE:
        return ["remove raw material bodies, paths, credentials, success/control/O5/O1/HIL/PR #5 resolution claims and rerun"]
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
        "safe_command_id": normalized["safe_command_id"],
        "command_id": normalized["safe_command_id"],
        "terminal_result_type": normalized["terminal_result_type"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": normalized["source_boundary"],
        "source_handoff_status": normalized["source_handoff_status"],
        "pr5_thread": _pr5_thread(),
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
        "verified_terminal_result_material_owner_response_reviewer_ack_intake": state,
        "allowed_reviewer_ack_states": list(ALLOWED_ACK_STATES),
        "ack_reasons": reasons,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "safe_command_id": normalized["safe_command_id"],
        "command_id": normalized["safe_command_id"],
        "terminal_result_type": normalized["terminal_result_type"],
        "source_owner_response_review_handoff": source_summary,
        "reviewer_acknowledgement": ack_summary,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "pr5_thread": _pr5_thread(),
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "non_access_scope": [
            "raw_terminal_result_materials",
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
            PR5_THREAD_ID,
            "hardware_material_pending",
            ACK_ACKNOWLEDGED,
            ACK_NEEDS_REASSIGNMENT,
            BLOCKED_MISSING_HANDOFF,
            ACK_EVIDENCE_REF_MISMATCH,
            ACK_REJECTED_UNSAFE,
        ],
    }


def build_verified_terminal_result_material_owner_response_reviewer_ack_intake(
    owner_response_review_handoff_json: str,
    reviewer_ack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 reviewer ACK intake；ACK 成功仍只表示 not_proven metadata。"""
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
        # 最终防线：如果通用 sanitizer 仍判定危险，强制降级为 unsafe。
        artifact["reviewer_ack_state"] = ACK_REJECTED_UNSAFE
        artifact["status"] = STATUS
        summary["reviewer_ack_state"] = ACK_REJECTED_UNSAFE
        summary["status"] = STATUS
        exit_code = 5
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint evidence bundle 和人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK mutation 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1 from previous "
            "verified_terminal_result_material_owner_response_review_handoff safe metadata and reviewer ACK packet. "
            "Keeps source=software_proof, software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, PRRT_kwDOSWB9286CJ3tX unresolved / "
            "hardware_material_pending, and no OKR percentage lift."
        )
    )
    parser.add_argument("--owner-response-review-handoff-json", required=True, help="previous owner response review handoff artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--reviewer-ack-json", required=True, help="reviewer-safe ACK packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output-dir", type=Path, help="optional directory for reviewer ACK intake artifact and summary")
    parser.add_argument("--output", type=Path, help="optional reviewer ACK intake artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional reviewer ACK intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print reviewer ACK intake artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_owner_response_reviewer_ack_intake(
        args.owner_response_review_handoff_json,
        args.reviewer_ack_json,
        args.evidence_ref,
    )
    output = args.output
    summary_output = args.summary_output
    if args.output_dir:
        output = output or args.output_dir / "verified_terminal_result_material_owner_response_reviewer_ack_intake.json"
        summary_output = summary_output or args.output_dir / "verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.json"
    if output:
        _write_json(output, artifact)
    if summary_output:
        _write_json(summary_output, summary)
    if args.once_json or not (output or summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{CAPABILITY}: artifact_file:{_safe_text(output)}")
        if summary_output:
            print(f"{CAPABILITY}_summary_file:{_safe_text(summary_output)}")
        print(f"reviewer_ack_state:{artifact['reviewer_ack_state']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
