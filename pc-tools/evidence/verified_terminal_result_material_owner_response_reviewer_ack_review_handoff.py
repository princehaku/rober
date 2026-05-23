#!/usr/bin/env python3
"""生成 verified terminal-result reviewer ACK review-handoff gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import verified_terminal_result_material_owner_response_reviewer_ack_review_decision as decision_gate


SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
SCHEMA_VERSION = 1

CAPABILITY = "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff"
SOURCE_CAPABILITY = decision_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate"
SOURCE_BOUNDARY = decision_gate.EVIDENCE_BOUNDARY
PR5_THREAD_ID = decision_gate.PR5_THREAD_ID

READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF = "ready_for_real_material_reviewer_handoff_not_proven"
MISSING_MATERIAL = "missing_material_not_proven"
REASSIGNMENT_REQUIRED = "reassignment_required_not_proven"
REJECTED_UNSAFE = "rejected_unsafe_not_proven"
BLOCKED_MISSING_SOURCE_REVIEW_DECISION = "blocked_missing_source_review_decision_not_proven"
EVIDENCE_REF_MISMATCH = "evidence_ref_mismatch_not_proven"
HANDOFF_STATUSES = (
    READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF,
    MISSING_MATERIAL,
    REASSIGNMENT_REQUIRED,
    REJECTED_UNSAFE,
    BLOCKED_MISSING_SOURCE_REVIEW_DECISION,
    EVIDENCE_REF_MISMATCH,
)

# 设计约束 01：本 gate 只消费上一轮 review-decision 的 safe surface。
# 设计约束 02：ready 只表示可交给人工 reviewer，不代表真实材料已通过。
# 设计约束 03：source=software_proof、not_proven 与三类 false flag 必须逐层固定。
# 设计约束 04：safe evidence_ref 是 decision 到 handoff 的唯一串联主键。
# 设计约束 05：缺输入、坏 JSON、unsupported schema 或 wrong boundary 一律 blocked。
# 设计约束 06：success/control/cloud/phone/HIL/pass/PR resolution claim 一律 rejected。
# 设计约束 07：输出不得复制 raw artifact、路径、凭证、checksum、traceback 或控制命令。
# 设计约束 08：handoff 不访问 ROS graph、Nav2 runtime、硬件、云、GitHub 或真实手机。
# 设计约束 09：本文件不新增硬件假设，因此无需读取 vendor 硬件资料。
# 设计约束 10：blocked/rejected 仍输出 artifact，便于 Docker-only sprint 复盘。

SUPPORTED_SOURCE_SCHEMAS = {
    decision_gate.SCHEMA,
    decision_gate.SUMMARY_SCHEMA,
    decision_gate.ROBOT_ALIAS,
    f"trashbot.{decision_gate.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    CAPABILITY,
    f"{CAPABILITY}_summary",
    SOURCE_CAPABILITY,
    f"{SOURCE_CAPABILITY}_summary",
    decision_gate.ROBOT_ALIAS,
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
    "pr5_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
    "verified_terminal_result",
    "complete_artifact",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw|complete)\s+artifact(s)?\b"),
    re.compile(r"(?i)\bTraceback\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified)\b"),
    re.compile(r"(?i)\b(verified\s+terminal\s+result|route/elevator\s+field\s+pass|field\s+pass)\b"),
    re.compile(r"(?i)\b(hil|o1)\s+(pass|passed|proof|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(pr\s*#\s*5|PRRT_[A-Za-z0-9]+).*(resolved|closed)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action|command)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(real phone proof|true phone proof|true browser proof|cloud proof|field proof|HIL proof)\b"),
)

NOT_PROVEN_ITEMS = (
    "real_material_reviewer_acceptance",
    "real_reviewer_resolution",
    "real_terminal_result",
    "real_delivery_dropoff_cancel_result",
    "real_route_elevator_field_pass",
    "true_phone_browser_proof",
    "public_https_tls_or_4g_or_oss_cdn_or_db_queue_proof",
    "wave_rover_uart_or_hil_pass",
    "delivery_success",
    "pr5_reviewer_resolution",
    "okr_percentage_lift",
)

BOUNDARY_NOTE = (
    "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff; "
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; no OKR percentage lift; "
    f"PR #5 {PR5_THREAD_ID} unresolved hardware_material_pending"
)


def _utc_now() -> str:
    # UTC 时间戳让 PC artifact 在 Docker-only 审计链里排序稳定。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary 或 safe_copy，因此每层都重复 fail-closed 旗标。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": False,
        "okr_lift_note": "no OKR percentage lift",
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


def _safe_ref(value: Any) -> str:
    # evidence_ref/command_id 只能是短安全标识；路径、URL、空值都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _safe_list(value: Any, limit: int = 40) -> list[str]:
    # 列表字段只输出短文本，并过滤本机路径、URL 和重复项。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("action") or item.get("summary") or item.get("reason"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object；字符串化 JSON 不自动展开，避免绕过 safe summary。
    return value if isinstance(value, dict) else {}


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 blocked handoff，不抛 traceback。
    if not path:
        return {}, "reviewer_ack_review_decision_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "reviewer_ack_review_decision_json_missing"
    except json.JSONDecodeError:
        return {}, "reviewer_ack_review_decision_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "reviewer_ack_review_decision_json_read_error"
    if not isinstance(payload, dict):
        return {}, "reviewer_ack_review_decision_json_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，不把任意 raw payload 都当 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一轮 review-decision schema/capability。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


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
    # 输入任何层把 false-state flag 改成 true，都不能进入 ready handoff。
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


def _unsafe_reasons(value: Any) -> list[str]:
    # unsafe 输出只保留类别原因，避免二次泄漏 source 原文。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_path_hardware_or_resolution_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_url_credential_ros_control_hardware_success_hil_or_pr5_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


def _source_refs(source: dict[str, Any]) -> tuple[str, list[str]]:
    # source 内多个 evidence_ref 不一致时直接 fail closed 到 mismatch。
    refs: list[str] = []
    for candidate in _candidates(source):
        for key in ("safe_evidence_ref", "evidence_ref"):
            ref = _safe_ref(candidate.get(key))
            if ref:
                refs.append(ref)
            elif candidate.get(key):
                refs.append("__unsafe_ref__")
    unique = list(dict.fromkeys(refs))
    reasons: list[str] = []
    if "__unsafe_ref__" in unique:
        reasons.append("unsafe_evidence_ref")
    clean = [ref for ref in unique if ref != "__unsafe_ref__"]
    if len(clean) > 1:
        reasons.append("evidence_ref_mismatch")
    return (clean[0] if clean and not reasons else ""), reasons


def _source_is_software_proof_not_proven(source: dict[str, Any]) -> bool:
    # 上一跳合同必须保持 software_proof / not_proven / false flags。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and source.get("safe_to_control") is False
    )


def _source_view(payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 handoff 判断的数据面。
    source = _find_source(payload) if payload else {}
    safe_copy = _dict(source.get("safe_copy"))
    evidence_ref, ref_errors = _source_refs(source) if source else ("", [])
    pr5_thread = _dict(source.get("pr5_thread") or safe_copy.get("pr5_thread"))
    return {
        "load_issue": load_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or safe_copy.get("evidence_boundary")),
        "source_review_decision": _safe_text(source.get("review_decision") or safe_copy.get("review_decision")),
        "reviewer_ack_state": _safe_text(source.get("reviewer_ack_state") or safe_copy.get("reviewer_ack_state")),
        "safe_evidence_ref": evidence_ref,
        "safe_command_id": _safe_ref(source.get("safe_command_id") or source.get("command_id") or safe_copy.get("safe_command_id")),
        "terminal_result_type": _safe_text(source.get("terminal_result_type") or safe_copy.get("terminal_result_type")),
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "decision_reasons": _safe_list(source.get("decision_reasons") or safe_copy.get("decision_reasons")),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or safe_copy.get("next_required_evidence")),
        "reviewer_role": _safe_text(source.get("reviewer_role") or safe_copy.get("reviewer_role") or "real-material-reviewer"),
        "reviewer_identity_label": _safe_text(source.get("reviewer_identity_label") or safe_copy.get("reviewer_identity_label")),
        "reassignment_target": _safe_text(source.get("reassignment_target") or safe_copy.get("reassignment_target")),
        "owner_action": _safe_text(source.get("owner_action") or safe_copy.get("owner_action")),
        "review_handoff_recommendation": _safe_text(source.get("review_handoff_recommendation")),
        "pr5_thread_state": _safe_text(pr5_thread.get("state")),
        "pr5_material_state": _safe_text(pr5_thread.get("material_state")),
        "source_is_software_proof_not_proven": _source_is_software_proof_not_proven(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_block_reasons(source: dict[str, Any], requested_ref: str) -> list[str]:
    # source 合同错误说明 review-decision 本身不可消费。
    reasons: list[str] = []
    schema_ok = source["schema"] in SUPPORTED_SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    boundary_ok = source["evidence_boundary"] == SOURCE_BOUNDARY
    if source["load_issue"]:
        reasons.append(source["load_issue"])
    if not schema_ok:
        reasons.append("unsupported_reviewer_ack_review_decision_schema")
    if not boundary_ok:
        reasons.append("missing_or_wrong_reviewer_ack_review_decision_proof_boundary")
    if not source["source_is_software_proof_not_proven"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if requested_ref and source["safe_evidence_ref"] and requested_ref != source["safe_evidence_ref"]:
        reasons.append("evidence_ref_mismatch")
    return list(dict.fromkeys(reasons))


def _handoff_status(source: dict[str, Any], requested_ref: str) -> tuple[str, list[str], int]:
    # 决策优先级固定：缺 source -> blocked；unsafe -> rejected；ref mismatch -> mismatch；再按上一跳 decision 映射。
    block_reasons = _source_block_reasons(source, requested_ref)
    if source["load_issue"] or "unsupported_reviewer_ack_review_decision_schema" in block_reasons or "missing_or_wrong_reviewer_ack_review_decision_proof_boundary" in block_reasons:
        return BLOCKED_MISSING_SOURCE_REVIEW_DECISION, block_reasons, 2
    if source["unsafe_reasons"]:
        return REJECTED_UNSAFE, source["unsafe_reasons"], 5
    if "evidence_ref_mismatch" in block_reasons or "missing_or_weak_same_evidence_ref" in block_reasons or "unsafe_evidence_ref" in block_reasons:
        return EVIDENCE_REF_MISMATCH, block_reasons, 3
    if block_reasons:
        return REJECTED_UNSAFE, block_reasons, 5
    if source["source_review_decision"] == decision_gate.ACCEPTED_FOR_REVIEW:
        return READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF, ["review-decision accepted; prepare sanitized real-material reviewer handoff only"], 0
    if source["source_review_decision"] == decision_gate.MISSING_MATERIAL:
        return MISSING_MATERIAL, source["decision_reasons"] or ["review-decision still requires missing material"], 0
    if source["source_review_decision"] == decision_gate.REASSIGNMENT_REQUIRED:
        return REASSIGNMENT_REQUIRED, ["review-decision requires reassignment before reviewer handoff"], 0
    if source["source_review_decision"] == decision_gate.REJECTED_UNSAFE:
        return REJECTED_UNSAFE, source["decision_reasons"] or ["source review-decision rejected unsafe"], 5
    if source["source_review_decision"] == decision_gate.BLOCKED_MISSING_SOURCE_INTAKE:
        return BLOCKED_MISSING_SOURCE_REVIEW_DECISION, source["decision_reasons"] or ["source review-decision blocked missing intake"], 2
    if source["source_review_decision"] == decision_gate.EVIDENCE_REF_MISMATCH:
        return EVIDENCE_REF_MISMATCH, source["decision_reasons"] or ["source review-decision evidence_ref mismatch"], 3
    return BLOCKED_MISSING_SOURCE_REVIEW_DECISION, ["review_decision_missing_or_unsupported"], 2


def _pr5_thread() -> dict[str, str]:
    # 本地 gate 只记录保守状态，不做 GitHub API mutation。
    return {
        "thread_id": PR5_THREAD_ID,
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
    }


def _next_required_evidence(handoff_status: str, source: dict[str, Any], reasons: list[str]) -> list[dict[str, Any]]:
    # 下一步都是人工补证/复核动作，不是机器人控制动作。
    if handoff_status == READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF:
        return [{"owner": "reviewer", "action": "handoff_sanitized_review_decision_to_real_material_reviewer_without_success_or_resolution_claims", "materials": ["review-decision summary", "same safe evidence_ref"]}]
    if handoff_status == MISSING_MATERIAL:
        return [{"owner": "field-owner", "action": "backfill_missing_material_before_reviewer_handoff", "materials": source["next_required_evidence"] or reasons}]
    if handoff_status == REASSIGNMENT_REQUIRED:
        return [{"owner": source["reassignment_target"] or "reviewer", "action": "route_sanitized_reviewer_handoff_to_reassigned_owner", "materials": ["reassignment target", "same safe evidence_ref"]}]
    if handoff_status == REJECTED_UNSAFE:
        return [{"owner": "reviewer", "action": "resubmit_sanitized_review_decision_without_raw_success_control_credential_path_hardware_or_resolution_claims", "materials": ["sanitized reviewer ACK review-decision summary"]}]
    if handoff_status == EVIDENCE_REF_MISMATCH:
        return [{"owner": "reviewer", "action": "repair_same_safe_evidence_ref_before_reviewer_handoff", "materials": ["same safe evidence_ref", SOURCE_BOUNDARY]}]
    return [{"owner": "reviewer", "action": "provide_supported_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_safe_summary", "materials": ["review-decision summary", SOURCE_BOUNDARY]}]


def _handoff_action(handoff_status: str) -> str:
    # action 文案明确责任边界，防止 ready 被误读成材料完成。
    if handoff_status == READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF:
        return "prepare sanitized real-material reviewer handoff; keep not_proven and no OKR lift"
    if handoff_status == MISSING_MATERIAL:
        return "ask field owner to backfill missing material before reviewer handoff"
    if handoff_status == REASSIGNMENT_REQUIRED:
        return "route sanitized reviewer handoff to reassigned owner"
    if handoff_status == REJECTED_UNSAFE:
        return "remove unsafe raw, success, control, credential, path, hardware, HIL, or PR #5 resolution claims"
    if handoff_status == EVIDENCE_REF_MISMATCH:
        return "repair evidence_ref alignment before reviewer handoff"
    return "rerun reviewer ACK review-decision and provide the safe source summary"


def _previous_decision_reference(source: dict[str, Any]) -> dict[str, Any]:
    # 上一环引用只保留合同字段，避免把完整 decision artifact 带进输出。
    return {
        "capability": SOURCE_CAPABILITY,
        "schema": source["schema"],
        "evidence_boundary": source["evidence_boundary"],
        "review_decision": source["source_review_decision"],
        "reviewer_ack_state": source["reviewer_ack_state"],
        "safe_evidence_ref": source["safe_evidence_ref"],
        "safe_command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
    }


def _reviewer_handoff_packet(handoff_status: str, source: dict[str, Any], reasons: list[str], next_required: list[dict[str, Any]]) -> dict[str, Any]:
    # reviewer packet 只暴露脱敏摘要，不包含完整 artifact、路径或控制入口。
    return {
        **_safe_flags(),
        "role": "real-material-reviewer",
        "handoff_status": handoff_status,
        "safe_evidence_ref": source["safe_evidence_ref"],
        "evidence_ref": source["safe_evidence_ref"],
        "source_review_decision": source["source_review_decision"],
        "reviewer_next_action": _handoff_action(handoff_status),
        "handoff_reasons": reasons,
        "next_required_evidence": next_required,
        "reviewer_resolution_required_now": False,
        "pr5_thread": _pr5_thread(),
    }


def _safe_phone_copy(handoff_status: str, evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # phone copy 只说明状态与下一步，不暴露 raw artifact 或控制入口。
    return {
        "title": "verified terminal-result reviewer ACK review handoff",
        "handoff_status": handoff_status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "message": "handoff only routes sanitized reviewer ACK review metadata; it is not real material approval, terminal result, phone/browser, HIL, PR #5 resolution, or delivery success.",
        "handoff_reasons": reasons,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _safe_copy(
    handoff_status: str,
    reasons: list[str],
    evidence_ref: str,
    source: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是后续 diagnostics/mobile 建议消费面，字段稳定且全为短字段。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": source["evidence_boundary"],
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "previous_decision_reference": _previous_decision_reference(source),
        "source_review_decision": source["source_review_decision"] or "missing",
        "handoff_status": handoff_status,
        "safe_handoff_label": handoff_status.replace("_", " "),
        "handoff_status_enum": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "reviewer_role": source["reviewer_role"],
        "reviewer_identity_label": source["reviewer_identity_label"],
        "reassignment_target": source["reassignment_target"] if handoff_status == REASSIGNMENT_REQUIRED else "",
        "next_required_evidence": next_required_evidence,
        "handoff_action": _handoff_action(handoff_status),
        "reviewer_handoff": _reviewer_handoff_packet(handoff_status, source, reasons, next_required_evidence),
        "pr5_thread": _pr5_thread(),
        "safe_phone_copy": _safe_phone_copy(handoff_status, evidence_ref, reasons),
    }


def _summary_payload(
    handoff_status: str,
    reasons: list[str],
    evidence_ref: str,
    source: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 与 artifact 保持同一 handoff_status，便于 Robot diagnostics safe alias。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **_safe_flags(),
        "capability": CAPABILITY,
        "summary_alias": ROBOT_ALIAS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "previous_decision_reference": _previous_decision_reference(source),
        "source_review_decision": source["source_review_decision"] or "missing",
        "reviewer_ack_state": source["reviewer_ack_state"] or "missing",
        "handoff_status": handoff_status,
        "safe_handoff_label": handoff_status.replace("_", " "),
        "handoff_status_enum": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "reviewer_role": source["reviewer_role"],
        "reviewer_identity_label": source["reviewer_identity_label"],
        "reassignment_target": source["reassignment_target"] if handoff_status == REASSIGNMENT_REQUIRED else "",
        "next_required_evidence": next_required_evidence,
        "handoff_action": _handoff_action(handoff_status),
        "reviewer_handoff": _reviewer_handoff_packet(handoff_status, source, reasons, next_required_evidence),
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        "safe_phone_copy": _safe_phone_copy(handoff_status, evidence_ref, reasons),
        "not_proven_items": list(NOT_PROVEN_ITEMS),
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
            READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF,
            MISSING_MATERIAL,
            REASSIGNMENT_REQUIRED,
            REJECTED_UNSAFE,
            BLOCKED_MISSING_SOURCE_REVIEW_DECISION,
            EVIDENCE_REF_MISMATCH,
        ],
    }


def build_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
    reviewer_ack_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 reviewer-ACK-review-decision safe source，生成 fail-closed handoff。"""
    source_payload, load_issue = _read_json(reviewer_ack_review_decision_json)
    source = _source_view(source_payload, load_issue)
    requested_ref = _safe_ref(evidence_ref) or source["safe_evidence_ref"]
    handoff_status, reasons, exit_code = _handoff_status(source, requested_ref)
    if not requested_ref:
        # 缺 safe ref 时仍输出 blocked artifact，但不伪造有效证据号。
        requested_ref = "missing_safe_evidence_ref"
    reasons = list(dict.fromkeys(reasons or [handoff_status]))
    next_required_evidence = _next_required_evidence(handoff_status, source, reasons)
    safe_copy = _safe_copy(handoff_status, reasons, requested_ref, source, next_required_evidence)
    summary = _summary_payload(handoff_status, reasons, requested_ref, source, next_required_evidence, safe_copy)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "previous_decision_reference": _previous_decision_reference(source),
        "source_review_decision": source["source_review_decision"] or "missing",
        "reviewer_ack_state": source["reviewer_ack_state"] or "missing",
        "handoff_status": handoff_status,
        "safe_handoff_label": handoff_status.replace("_", " "),
        "handoff_status_enum": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "reviewer_role": source["reviewer_role"],
        "reviewer_identity_label": source["reviewer_identity_label"],
        "reassignment_target": source["reassignment_target"] if handoff_status == REASSIGNMENT_REQUIRED else "",
        "next_required_evidence": next_required_evidence,
        "handoff_action": _handoff_action(handoff_status),
        "reviewer_handoff": _reviewer_handoff_packet(handoff_status, source, reasons, next_required_evidence),
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "blocked_claims": list(NOT_PROVEN_ITEMS),
        "safety_markers": summary["safety_markers"],
    }
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1 "
            "from a sanitized verified_terminal_result_material_owner_response_reviewer_ack_review_decision "
            "artifact, summary, or Robot alias. Keeps source=software_proof, not_proven, "
            "delivery_success=false, primary_actions_enabled=false, and safe_to_control=false."
        )
    )
    parser.add_argument("--reviewer-ack-review-decision-json", required=True, help="sanitized reviewer ACK review decision artifact, summary, or Robot alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional reviewer ACK review handoff artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional reviewer ACK review handoff summary JSON output path")
    parser.add_argument("--output-dir", type=Path, help="optional directory for canonical artifact and summary filenames")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
        args.reviewer_ack_review_decision_json,
        args.evidence_ref,
    )
    if args.output_dir:
        _write_json(args.output_dir / f"{CAPABILITY}.json", artifact)
        _write_json(args.output_dir / f"{CAPABILITY}_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output or args.output_dir):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{CAPABILITY}: artifact_file:{args.output or args.output_dir / f'{CAPABILITY}.json'}")
        print(f"reviewer_ack_review_handoff_summary_file:{args.summary_output or args.output_dir / f'{CAPABILITY}_summary.json'}")
        print(f"handoff_status:{artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
