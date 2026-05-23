#!/usr/bin/env python3
"""生成 verified_terminal_result_material_owner_response_intake 的 PC-only gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只消费上一轮 follow-up escalation status 的 safe surface。
# 设计约束 02：owner response 只能是脱敏 metadata，不能携带 raw terminal material。
# 设计约束 03：accepted 只表示 owner response 可进入后续 review，不证明真实结果。
# 设计约束 04：缺 owner response 时必须 missing + 非 0，不能伪造 happy path。
# 设计约束 05：source、owner response 与 CLI 指定 ref 必须保持同一个 safe evidence_ref。
# 设计约束 06：所有输出固定 source=software_proof、software_proof、not_proven。
# 设计约束 07：所有输出固定 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 设计约束 08：PR #5 thread PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 设计约束 09：拒绝 raw artifact、完整 JSON dump、raw owner body、凭证、URL、DB/queue、OSS。
# 设计约束 10：拒绝 local path、traceback、ROS topic、/cmd_vel、serial/UART、WAVE ROVER。
# 设计约束 11：拒绝 ACK/cursor/replay/resubmit、reviewer-resolution claim、success/control claim。
# 设计约束 12：状态枚举使用任务要求的长状态，便于 rg 围栏直接审计。
# 设计约束 13：代码不新增硬件参数或协议假设，所以本文件不引用 vendor 细节。
# 设计约束 14：所有技术注释使用中文，解释 fail-closed 和字段取舍。
# 设计约束 15：CLI 不访问网络、GitHub、ROS graph、真实手机、真实硬件或云服务。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_intake.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_intake_summary.v1"
OWNER_RESPONSE_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_packet.v1"
ROBOT_ALIAS_SCHEMA = "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "verified_terminal_result_material_owner_response_intake"
SOURCE_CAPABILITY = "verified_terminal_result_material_followup_escalation_status"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_intake_gate"
SOURCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary"
NO_OKR_LIFT = "no OKR percentage lift"
PR5_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

ACCEPTED_STATUS = "accepted_terminal_result_material_owner_response_not_proven"
MISSING_STATUS = "missing_terminal_result_material_owner_response_not_proven"
REJECTED_STATUS = "rejected_terminal_result_material_owner_response_not_proven"
UNSAFE_STATUS = "unsafe_terminal_result_material_owner_response_not_proven"
BLOCKED_SOURCE_STATUS = "blocked_missing_terminal_result_followup_escalation_status_not_proven"
BLOCKED_REF_STATUS = "blocked_evidence_ref_mismatch_not_proven"
OWNER_RESPONSE_STATUSES = (
    ACCEPTED_STATUS,
    MISSING_STATUS,
    REJECTED_STATUS,
    UNSAFE_STATUS,
    BLOCKED_SOURCE_STATUS,
    BLOCKED_REF_STATUS,
)

SUPPORTED_SOURCE_SCHEMAS = {
    "trashbot.verified_terminal_result_material_followup_escalation_status.v1",
    "trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1",
    "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary",
    "trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1",
}
SUPPORTED_OWNER_RESPONSE_SCHEMAS = {"", OWNER_RESPONSE_SCHEMA, f"{OWNER_RESPONSE_SCHEMA}.summary"}
SAFE_SOURCE_FOLLOWUP_STATUSES = {
    "escalated_for_terminal_result_material_followup_not_proven",
    "waiting_for_terminal_result_material_backfill_not_proven",
    "needs_support_owner_reassignment_not_proven",
}
TERMINAL_RESULT_TYPES = ("delivery", "dropoff", "cancel")
SHORT_RESPONSE_STATUSES = ("accepted", "missing", "rejected", "unsafe")

WRAPPER_KEYS = (
    "verified_terminal_result_material_followup_escalation_status",
    "verified_terminal_result_material_followup_escalation_status_summary",
    "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary",
    "verified_terminal_result_material_owner_response_packet",
    "verified_terminal_result_material_owner_response",
    "owner_response_packet",
    "owner_response",
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "summary",
    "artifact",
    "data",
    "payload",
)

REQUIRED_OWNER_RESPONSE_MATERIALS = (
    "sanitized_owner_response_metadata",
    "same_safe_evidence_ref_confirmation",
    "terminal_result_material_status",
    "field_owner_acknowledgement",
    "support_owner_acknowledgement",
    "reviewer_route_confirmation",
    "pr5_hardware_material_pending_confirmation",
)
NOT_PROVEN_ITEMS = (
    "real_terminal_delivery_result",
    "real_terminal_dropoff_result",
    "real_terminal_cancel_result",
    "real_nav2_fixed_route_run",
    "real_elevator_field_pass",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "pr5_reviewer_resolution",
)
BLOCKED_CLAIMS = (
    "raw_artifacts",
    "complete_json_dump",
    "raw_owner_response_body",
    "raw_terminal_material",
    "credentials",
    "urls",
    "db_queue_oss",
    "local_paths",
    "traceback",
    "ros_topics_or_cmd_vel",
    "serial_uart_wave_rover",
    "ack_cursor_replay_resubmit",
    "reviewer_resolution_claim",
    "success_or_control_claim",
)
BOUNDARY_NOTE = (
    "verified_terminal_result_material_owner_response_intake; "
    "software_proof_docker_verified_terminal_result_material_owner_response_intake_gate; "
    "verified_terminal_result_material_followup_escalation_status; "
    "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "accepted_terminal_result_material_owner_response_not_proven; "
    "missing_terminal_result_material_owner_response_not_proven; "
    "rejected_terminal_result_material_owner_response_not_proven; "
    "unsafe_terminal_result_material_owner_response_not_proven; "
    "blocked_missing_terminal_result_followup_escalation_status_not_proven; "
    "blocked_evidence_ref_mismatch_not_proven; no OKR percentage lift"
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
URL_OR_QUEUE_RE = re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb|oss|s3)://|https?://")
FORBIDDEN_KEY_TERMS = (
    "raw",
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "complete_json",
    "complete_artifact",
    "artifact_path",
    "local_path",
    "file_path",
    "log_path",
    "traceback",
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
    "cmd_vel",
    "control_command",
    "serial_device",
    "uart",
    "wave_rover",
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
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw\s+artifact|complete\s+json|raw\s+owner|raw\s+terminal|traceback)\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result|route|elevator|nav2)\s+(success|succeeded|completed|complete|verified|passed)\b"),
    re.compile(r"(?i)\b(success|control|dispatch|start|confirm|cancel)\s+(claim|command|action)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(ack|cursor|replay|resubmit)\b.*\b(command|mutation|hint|retry|lookup)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved|PR\s*#?5.*resolved)\b"),
)


def _utc_now() -> str:
    # UTC 时间让 Docker-only artifact 在 PC、本地容器和未来 CI 中可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary，所以所有安全旗标在 artifact/summary/safe_copy 重复输出。
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
    # 任意自由文本都压成短单行，避免 raw body 或多行日志穿透输出。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _encoded(value: Any) -> str:
    # 递归安全扫描需要稳定 JSON；不可序列化对象降级为短文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _safe_ref(value: Any) -> str:
    # evidence_ref/command_id 只能是短安全标识，路径、URL、弱字符串都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，不把字符串化 JSON 自动展开为可信输入。
    return value if isinstance(value, dict) else {}


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成可审计分类，而不是抛 traceback。
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


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 safe wrapper key，防止任意 raw payload 被误采信。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一轮 follow-up status schema/capability，避免跳链消费。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _has_owner_response_material(payload: dict[str, Any]) -> bool:
    # 只用白名单字段判断 response 形状，不读取未知正文。
    for key in ("materials", "material_responses", "responses", "accepted_materials", "missing_materials", "rejected_materials", "unsafe_materials"):
        value = payload.get(key)
        if isinstance(value, (dict, list)) and value:
            return True
    return bool(_safe_text(payload.get("owner_response_status") or payload.get("response_status")))


def _find_owner_response(payload: dict[str, Any]) -> dict[str, Any]:
    # owner response 可直传，也可包在 owner_response_packet/payload/summary 里。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        if schema in SUPPORTED_OWNER_RESPONSE_SCHEMAS and _has_owner_response_material(candidate):
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/ACK/reviewer-resolution 类别即拒绝。
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


def _true_flag_reasons(value: Any) -> list[str]:
    # true 控制旗标可能藏在嵌套 dict 或字符串 note 中，必须全局拒绝。
    reasons: list[str] = []
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control", "control_enabled", "hil_pass", "field_pass"):
            if value.get(key) is True:
                reasons.append(f"{key}_true_overclaim")
        for child in value.values():
            reasons.extend(_true_flag_reasons(child))
    elif isinstance(value, list):
        for child in value:
            reasons.extend(_true_flag_reasons(child))
    elif isinstance(value, str):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value):
                reasons.append(f"{key}_true_overclaim")
    return list(dict.fromkeys(reasons))


def _unsafe_reasons(value: Any) -> list[str]:
    # 只输出类别原因，不回显命中的敏感片段。
    if value in ({}, None, ""):
        return []
    reasons: list[str] = []
    encoded = _encoded(value)
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_owner_response_control_credential_path_ack_replay_or_resolution_fields")
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded):
        reasons.append("unsafe_path_url_db_queue_oss_or_local_path")
    if any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_raw_terminal_material_credential_ros_control_hardware_ack_replay_resolution_or_success_claim")
    reasons.extend(_true_flag_reasons(value))
    return list(dict.fromkeys(reasons))


def _surface_is_safe(payload: dict[str, Any]) -> bool:
    # source/response 的最低消费边界：software_proof + not_proven + 三个 false flags。
    encoded = _encoded(payload)
    return (
        _safe_text(payload.get("source")) == SOURCE
        and "not_proven" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _collect_refs(value: Any) -> list[str]:
    # 只收集明确 ref 字段，用于 same safe evidence_ref 一致性检查。
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in {"safe_evidence_ref", "evidence_ref"}:
                refs.append(_safe_ref(child) or "__unsafe_ref__")
            refs.extend(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_collect_refs(child))
    return refs


def _ref_state(payloads: list[dict[str, Any]]) -> tuple[str, list[str]]:
    # 多个 ref 必须一致，避免把不同现场材料拼成一个 intake。
    refs: list[str] = []
    reasons: list[str] = []
    for payload in payloads:
        for ref in _collect_refs(payload):
            refs.append(ref)
    unique = list(dict.fromkeys(refs))
    if "__unsafe_ref__" in unique:
        reasons.append("unsafe_evidence_ref")
    clean = [ref for ref in unique if ref != "__unsafe_ref__"]
    if len(clean) > 1:
        reasons.append("evidence_ref_mismatch")
    if not clean:
        reasons.append("missing_safe_evidence_ref")
    return (clean[0] if clean and not reasons else ""), list(dict.fromkeys(reasons))


def _safe_list(value: Any, limit: int = 80) -> list[str]:
    # 列表字段只输出类别名/短摘要，不复制 raw item。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("category") or item.get("summary"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _material_map(response: dict[str, Any]) -> dict[str, Any]:
    # 支持 dict/list 两类 owner response 表单，统一按 material name 分类。
    for key in ("materials", "material_responses", "responses"):
        value = response.get(key)
        if isinstance(value, dict):
            return {str(name): item for name, item in value.items()}
        if isinstance(value, list):
            mapped: dict[str, Any] = {}
            for item in value:
                if isinstance(item, dict):
                    name = _safe_text(item.get("name") or item.get("material") or item.get("category"))
                    if name:
                        mapped[name] = item
            return mapped
    return {}


def _listed(response: dict[str, Any], key: str) -> list[str]:
    # 简写列表允许 owner 只提交类别索引，不需要 raw 材料正文。
    return _safe_list(response.get(key))


def _source_view(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 source 合同判断的数据面。
    source = _find_source(payload) if payload else {}
    ref, ref_errors = _ref_state([source]) if source else ("", ["missing_safe_evidence_ref"])
    return {
        "read_issue": read_issue,
        "raw": source,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary")),
        "source_followup_status": _safe_text(source.get("followup_status") or source.get("verified_terminal_result_material_followup_escalation_status")),
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "safe_command_id": _safe_ref(source.get("safe_command_id") or source.get("command_id")),
        "terminal_result_type": _safe_text(source.get("terminal_result_type")),
        "field_owner": _safe_text(source.get("field_owner") or source.get("assigned_owner"), "field_terminal_result_material_owner"),
        "support_owner": _safe_text(source.get("support_owner"), "support_terminal_result_material_owner"),
        "reviewer_route": _safe_text(source.get("reviewer_route"), "terminal_result_material_reviewer"),
        "next_required_evidence": _safe_list(source.get("next_required_evidence")),
        "source_is_safe": _surface_is_safe(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source),
    }


def _source_ready(source: dict[str, Any]) -> tuple[bool, list[str]]:
    # source 不 ready 时不消费 owner response，避免用新材料掩盖坏上游。
    reasons: list[str] = []
    schema_ok = source["schema"] in SUPPORTED_SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    if source["read_issue"]:
        reasons.append(source["read_issue"])
    if not schema_ok:
        reasons.append("unsupported_terminal_result_followup_escalation_status_schema")
    if source["evidence_boundary"] != SOURCE_BOUNDARY:
        reasons.append("missing_or_wrong_terminal_result_followup_escalation_status_boundary")
    if source["source_followup_status"] not in SAFE_SOURCE_FOLLOWUP_STATUSES:
        reasons.append("previous_followup_status_not_safe_for_owner_response_intake")
    if source["terminal_result_type"] not in TERMINAL_RESULT_TYPES:
        reasons.append("unsupported_terminal_result_type")
    if source["unsafe_reasons"]:
        reasons.extend(source["unsafe_reasons"])
    if not source["source_is_safe"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    return not reasons, list(dict.fromkeys(reasons))


def _response_view(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized response 只保留 schema、ref、状态和安全材料类别。
    response = _find_owner_response(payload) if payload else {}
    ref, ref_errors = _ref_state([response]) if response else ("", [])
    response_status = _safe_text(response.get("owner_response_status") or response.get("response_status") or response.get("status")).lower()
    return {
        "read_issue": read_issue,
        "raw": response,
        "schema": _safe_text(response.get("schema")),
        "owner_response_status": response_status,
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": response.get("same_evidence_ref_required", True),
        "material_map": _material_map(response),
        "accepted_list": _listed(response, "accepted_materials") or _listed(response, "received_materials"),
        "missing_list": _listed(response, "missing_materials"),
        "rejected_list": _listed(response, "rejected_materials"),
        "unsafe_list": _listed(response, "unsafe_materials"),
        "response_is_safe": _surface_is_safe(response) if response else False,
        "unsafe_reasons": _unsafe_reasons(response),
    }


def _classify_material(name: str, response: dict[str, Any], expected_ref: str) -> tuple[str, list[str]]:
    # 单项只有显式 accepted 才进入 accepted，缺项/拒绝/unsafe 都 fail-closed。
    item = response["material_map"].get(name)
    if item is None and name in response["accepted_list"]:
        item = {"name": name, "status": "accepted", "safe_evidence_ref": response["safe_evidence_ref"]}
    elif item is None and name in response["missing_list"]:
        item = {"name": name, "status": "missing", "safe_evidence_ref": response["safe_evidence_ref"]}
    elif item is None and name in response["rejected_list"]:
        item = {"name": name, "status": "rejected", "safe_evidence_ref": response["safe_evidence_ref"]}
    elif item is None and name in response["unsafe_list"]:
        item = {"name": name, "status": "unsafe", "safe_evidence_ref": response["safe_evidence_ref"]}
    if item is None:
        return "missing", ["required_owner_response_material_absent"]
    if not isinstance(item, dict):
        return "rejected", ["owner_response_material_item_not_object"]
    explicit = _safe_text(item.get("classification") or item.get("status") or item.get("response_status")).lower()
    item_ref = _safe_ref(item.get("safe_evidence_ref") or item.get("evidence_ref") or response["safe_evidence_ref"])
    if not item_ref:
        return "unsafe", ["missing_safe_evidence_ref"]
    if item_ref != expected_ref:
        return "ref_mismatch", ["evidence_ref_mismatch"]
    if _unsafe_reasons(item):
        return "unsafe", ["unsafe_owner_response_material"]
    if item.get("unsafe") is True or explicit == "unsafe":
        return "unsafe", ["owner_marked_unsafe_not_proven"]
    if item.get("rejected") is True or explicit == "rejected":
        return "rejected", ["owner_marked_rejected_not_proven"]
    if item.get("missing") is True or explicit == "missing":
        return "missing", ["owner_marked_missing_not_proven"]
    if item.get("accepted") is True or explicit in {"accepted", "received_not_reviewed"}:
        return "accepted", ["accepted_for_review_not_proven"]
    return "rejected", ["missing_explicit_safe_owner_response_status"]


def _classify_response(source_ok: bool, source_reasons: list[str], source: dict[str, Any], response: dict[str, Any], requested_ref: str) -> tuple[str, dict[str, list[str]], list[str], int]:
    # 总分类优先保护 source/ref，再按 owner response 状态汇总。
    categories = {"accepted": [], "missing": [], "rejected": [], "unsafe": []}
    reasons: list[str] = []
    if not source_ok:
        return BLOCKED_SOURCE_STATUS, categories, source_reasons, 2
    if requested_ref != source["safe_evidence_ref"]:
        return BLOCKED_REF_STATUS, categories, ["cli_evidence_ref_mismatch"], 4
    if response["read_issue"]:
        return MISSING_STATUS, categories, [response["read_issue"]], 3
    schema_ok = response["schema"] in SUPPORTED_OWNER_RESPONSE_SCHEMAS
    if not schema_ok:
        return UNSAFE_STATUS, categories, ["unsupported_owner_response_schema"], 5
    if response["ref_errors"] or not response["safe_evidence_ref"] or response["safe_evidence_ref"] != requested_ref:
        return BLOCKED_REF_STATUS, categories, response["ref_errors"] or ["owner_response_evidence_ref_mismatch"], 4
    if response["same_evidence_ref_required"] is not True:
        return BLOCKED_REF_STATUS, categories, ["same_evidence_ref_required_not_true"], 4
    if response["unsafe_reasons"] or not response["response_is_safe"]:
        unsafe = response["unsafe_reasons"] or ["owner_response_not_software_proof_not_proven_or_false_flags_changed"]
        return UNSAFE_STATUS, categories, unsafe, 5

    for name in REQUIRED_OWNER_RESPONSE_MATERIALS:
        status, item_reasons = _classify_material(name, response, requested_ref)
        if status == "ref_mismatch":
            return BLOCKED_REF_STATUS, categories, item_reasons, 4
        categories[status].append(name)
        reasons.extend(item_reasons)

    declared = response["owner_response_status"]
    if declared and declared not in SHORT_RESPONSE_STATUSES:
        return UNSAFE_STATUS, categories, ["unsupported_owner_response_status"], 5
    if categories["unsafe"] or declared == "unsafe":
        return UNSAFE_STATUS, categories, ["unsafe_terminal_result_material_owner_response_not_proven"], 5
    if categories["rejected"] or declared == "rejected":
        return REJECTED_STATUS, categories, ["rejected_terminal_result_material_owner_response_not_proven"], 6
    if categories["missing"] or declared == "missing":
        return MISSING_STATUS, categories, ["missing_terminal_result_material_owner_response_not_proven"], 3
    return ACCEPTED_STATUS, categories, ["accepted_terminal_result_material_owner_response_not_proven"], 0


def _next_required(owner_status: str, evidence_ref: str, categories: dict[str, list[str]], reasons: list[str]) -> list[str]:
    # next_required_evidence 是人工补证说明，不是 ACK、cursor、replay 或 Robot 指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if owner_status == ACCEPTED_STATUS:
        return [
            f"route sanitized owner response metadata for evidence_ref={ref} into later review without enabling controls",
            "keep PR #5 PRRT_kwDOSWB9286CJ3tX unresolved / hardware_material_pending until reviewer live-resolves it outside this gate",
            "preserve source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false",
        ]
    if owner_status == MISSING_STATUS:
        missing = categories["missing"] or list(REQUIRED_OWNER_RESPONSE_MATERIALS)
        return [f"provide sanitized owner response material category: {name} for evidence_ref={ref}" for name in missing]
    if owner_status == REJECTED_STATUS:
        return [f"replace rejected owner response material category: {name} for evidence_ref={ref}" for name in categories["rejected"]]
    if owner_status == UNSAFE_STATUS:
        return [f"rerun owner response intake with sanitized metadata only for evidence_ref={ref}", *reasons]
    return [f"rerun source follow-up escalation status and owner response with the same safe evidence_ref={ref}", *reasons]


def _blocked_reason(owner_status: str, reasons: list[str]) -> str:
    # blocked_reason 只输出短类别，避免把原始 owner response 泄漏到 summary。
    if owner_status == ACCEPTED_STATUS:
        return ""
    return _safe_text(";".join(list(dict.fromkeys(reasons))), "blocked")


def _safe_copy(owner_status: str, source: dict[str, Any], evidence_ref: str, categories: dict[str, list[str]]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile/review 后续只读消费面，不包含 raw source 或 raw response。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "safe_command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
        "source_followup_status": source["source_followup_status"],
        "owner_response_status": owner_status,
        "field_owner": source["field_owner"],
        "support_owner": source["support_owner"],
        "reviewer_route": source["reviewer_route"],
        "accepted_materials": categories["accepted"],
        "missing_materials": categories["missing"],
        "rejected_materials": categories["rejected"],
        "unsafe_materials": categories["unsafe"],
        "pr5_thread": {
            "thread_id": PR5_THREAD_ID,
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "resolution_rule": "not resolved by this PC-only gate",
        },
        "safe_copy_text": (
            f"{CAPABILITY}: owner_response_status={owner_status}; evidence_ref={evidence_ref}; "
            f"command_id={source['safe_command_id'] or 'none'}; terminal_result_type={source['terminal_result_type']}; "
            f"source_followup_status={source['source_followup_status']}; field_owner={source['field_owner']}; "
            f"support_owner={source['support_owner']}; reviewer_route={source['reviewer_route']}; "
            f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; software_proof; not_proven; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; no OKR percentage lift."
        ),
    }


def build_verified_terminal_result_material_owner_response_intake(
    source_json: str,
    owner_response_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取上一轮 follow-up status 与 owner response，生成 fail-closed intake。"""
    source_payload, source_issue = _load_json(source_json, "source_json")
    source = _source_view(source_payload, source_issue)
    source_ok, source_reasons = _source_ready(source)
    requested_ref = _safe_ref(evidence_ref) if evidence_ref else source["safe_evidence_ref"]
    if not requested_ref:
        source_ok = False
        source_reasons.append("missing_requested_safe_evidence_ref")

    response_payload, response_issue = _load_json(owner_response_json, "owner_response_json")
    response = _response_view(response_payload, response_issue)
    owner_status, categories, reasons, exit_code = _classify_response(source_ok, source_reasons, source, response, requested_ref)
    generated_at = _utc_now()
    next_required = _next_required(owner_status, requested_ref, categories, reasons)
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": source["schema"],
        "source_evidence_boundary": source["evidence_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "allowed_owner_response_statuses": list(OWNER_RESPONSE_STATUSES),
        "owner_response_status": owner_status,
        "source_followup_status": source["source_followup_status"],
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
        "field_owner": source["field_owner"],
        "support_owner": source["support_owner"],
        "reviewer_route": source["reviewer_route"],
        "accepted_materials": categories["accepted"],
        "missing_materials": categories["missing"],
        "rejected_materials": categories["rejected"],
        "unsafe_materials": categories["unsafe"],
        "required_owner_response_materials": list(REQUIRED_OWNER_RESPONSE_MATERIALS),
        "blocked_reason": _blocked_reason(owner_status, reasons),
        "owner_response_reasons": list(dict.fromkeys(reasons)),
        "next_required_evidence": next_required,
        "safe_copy": _safe_copy(owner_status, source, requested_ref, categories),
        "summary_alias": ROBOT_ALIAS,
        "robot_alias_schema": ROBOT_ALIAS_SCHEMA,
        "pr5_thread": {
            "thread_id": PR5_THREAD_ID,
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
        },
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            ACCEPTED_STATUS,
            MISSING_STATUS,
            REJECTED_STATUS,
            UNSAFE_STATUS,
            BLOCKED_SOURCE_STATUS,
            BLOCKED_REF_STATUS,
            NO_OKR_LIFT,
        ],
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "verified_terminal_result_material_owner_response_intake": owner_status,
        **common,
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "verified_terminal_result_material_owner_response_intake": owner_status,
        "source_followup_status_detail": {
            "ready": source_ok,
            "read_issue": source_issue,
            "schema": source["schema"],
            "evidence_boundary": source["evidence_boundary"],
            "unsafe_reasons": source["unsafe_reasons"],
            "source_reasons": source_reasons,
        },
        "owner_response_packet_detail": {
            "load_issue": response_issue,
            "schema": response["schema"],
            "unsafe_reasons": response["unsafe_reasons"],
            "ref_errors": response["ref_errors"],
        },
        **common,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
    }
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint evidence bundle 和人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK、replay 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_owner_response_intake.v1 from --input/--source "
            "verified_terminal_result_material_followup_escalation_status plus optional sanitized --owner-response. "
            "Keeps source=software_proof, software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input", dest="source_json", help="prior follow-up escalation status artifact, summary, or Robot safe alias JSON")
    source_group.add_argument("--source", dest="source_json", help="alias for --input")
    parser.add_argument("--owner-response", default="", help="optional sanitized owner response packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output-dir", type=Path, help="optional directory for owner response intake artifact and summary")
    parser.add_argument("--output", type=Path, help="optional owner response intake artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_owner_response_intake(
        args.source_json,
        args.owner_response,
        args.evidence_ref,
    )
    output = args.output
    summary_output = args.summary_output
    if args.output_dir:
        output = output or args.output_dir / "verified_terminal_result_material_owner_response_intake.json"
        summary_output = summary_output or args.output_dir / "verified_terminal_result_material_owner_response_intake_summary.json"
    if output:
        _write_json(output, artifact)
    if summary_output:
        _write_json(summary_output, summary)
    if args.once_json or not (output or summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"verified_terminal_result_material_owner_response_intake: artifact_file:{_safe_text(output)}")
        if summary_output:
            print(f"verified_terminal_result_material_owner_response_intake_summary_file:{_safe_text(summary_output)}")
        print(f"owner_response_status:{artifact['owner_response_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
