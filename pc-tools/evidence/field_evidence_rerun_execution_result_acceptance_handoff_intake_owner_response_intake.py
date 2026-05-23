#!/usr/bin/env python3
"""生成 acceptance handoff intake owner response intake gate。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`
之后，只读取上一环 safe artifact / summary / Robot safe alias 与脱敏 owner
response packet。输出只把同一 safe evidence_ref 下的 owner response 分类为
accepted、missing、rejected 或 blocked；accepted 也只是后续 review metadata，
不读取真实现场日志、不验证 route/elevator/phone/cloud/hardware，也不启用控制。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status as followup
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1"
OWNER_RESPONSE_PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_packet.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake"
SOURCE_CAPABILITY = followup.CAPABILITY
BRIDGE_CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge"
BRIDGE_SOURCE_CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status"
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate"
SOURCE_BOUNDARY = followup.BOUNDARY
BRIDGE_EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate"
BRIDGE_SOURCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate"
BRIDGE_SOURCE_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.v1"
BRIDGE_SOURCE_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
BRIDGE_SOURCE_ROBOT_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
BRIDGE_SOURCE_STATUSES = (
    "pending_reviewer_ack_followup_not_proven",
    "overdue_reviewer_ack_followup_not_proven",
    "escalated_missing_real_material_not_proven",
    "blocked_missing_reviewer_ack_review_handoff_not_proven",
    "ready_for_real_material_reviewer_followup_not_proven",
)

ACCEPTED = "accepted"
MISSING = "missing"
REJECTED = "rejected"
BLOCKED = "blocked"
ALLOWED_OWNER_RESPONSE_STATUSES = (ACCEPTED, MISSING, REJECTED, BLOCKED)

REQUIRED_OWNER_RESPONSE_MATERIALS = (
    "real task record",
    "Nav2/fixed-route runtime log",
    "route completion signal",
    "dropoff/cancel completion",
    "elevator door status",
    "floor confirmation",
    "human assistance note",
    "delivery result",
    "route/elevator field pass",
    "true phone/browser evidence",
    "PR #5 hardware material remains pending unless PRRT_kwDOSWB9286CJ3tX is live resolved by reviewer",
)

SAFE_SOURCE_STATUSES = ("pending", "overdue", "escalated")
SOURCE_SCHEMAS = {
    followup.SCHEMA,
    followup.SUMMARY_SCHEMA,
    followup.ROBOT_ALIAS,
    f"trashbot.{followup.ROBOT_ALIAS}.v1",
    BRIDGE_SOURCE_SCHEMA,
    BRIDGE_SOURCE_SUMMARY_SCHEMA,
    BRIDGE_SOURCE_ROBOT_ALIAS,
    f"trashbot.{BRIDGE_SOURCE_ROBOT_ALIAS}.v1",
}
OWNER_RESPONSE_SCHEMAS = {"", OWNER_RESPONSE_PACKET_SCHEMA, f"{OWNER_RESPONSE_PACKET_SCHEMA}.summary"}

# 设计约束 01：本 gate 只处理安全 metadata，不读取 raw field logs。
# 设计约束 02：上一环必须是 follow-up escalation status，不能跳过 handoff intake 链。
# 设计约束 03：accepted 只表示 accepted_for_review_not_proven，不证明真实交付成功。
# 设计约束 04：missing/rejected/blocked 都是 fail-closed，不启用任何 primary action。
# 设计约束 05：safe evidence_ref 是跨 source 与 owner response 的唯一复账主键。
# 设计约束 06：source=software_proof、not_proven 与三个 false flag 必须逐层保留。
# 设计约束 07：required checklist 是材料类别名，不是材料正文或真实日志路径。
# 设计约束 08：PR #5 线程只能保持 hardware_material_pending，不能在本 gate resolved。
# 设计约束 09：success/control/O5 external proof/O1 HIL/PR #5 resolution claim 一律 blocked。
# 设计约束 10：raw/local path、credential、ROS topic、serial、WAVE ROVER 文案一律 blocked。
# 设计约束 11：输出 safe_copy 是 Robot/mobile 只读面，不包含 raw source 或 raw response。
# 设计约束 12：wrapper/nested JSON 只递归白名单 key，防止误采信任意 payload。
# 设计约束 13：CLI 只在 accepted 时返回 0，其余分类都返回非 0。
# 设计约束 14：dependency-free，方便 macOS PC、Docker 和 unittest 离线复跑。
# 设计约束 15：本文件不查 vendor，因为不新增硬件参数、串口、波特率或协议假设。
# 设计约束 16：所有技术注释使用中文，解释 fail-closed 原因和字段取舍。
# 设计约束 17：最终 artifact/summary 仍会递归脱敏，防止新字段绕过扫描。
# 设计约束 18：本 gate 不更新 Robot diagnostics、mobile/web、OKR 或 sprint closeout。
# 设计约束 19：状态名保持四个短枚举，便于 UI、docs 和 rg 围栏复用。
# 设计约束 20：owner response 缺失或材料缺项使用 missing，而不是伪造 accepted。
# 设计约束 21：显式 rejected 表示 owner 回复不可进入 review，但仍是 not_proven。
# 设计约束 22：blocked 表示 source、证据号或安全边界失效，需要重跑上一环。
# 设计约束 23：所有 rerun_commands 只覆盖 PC evidence gate，不含 ROS/硬件/云命令。
# 设计约束 24：no OKR percentage lift 必须留在 artifact、summary 和 safe_copy 中。

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate; "
    "source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; accepted; missing; rejected; blocked; "
    "no OKR percentage lift"
)

WRAPPER_KEYS = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
    "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary",
    "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_packet",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response",
    "owner_response_packet",
    "owner_response",
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "artifact",
    "summary",
    "payload",
    "data",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
FORBIDDEN_KEY_TERMS = (
    "raw",
    "raw_artifact",
    "raw_log",
    "raw_payload",
    "artifact_path",
    "local_path",
    "file_path",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "signed_url",
    "cmd_vel",
    "ros_topic",
    "ros_service",
    "serial_device",
    "uart_device",
    "wave_rover",
    "hil_pass",
    "field_pass",
    "cloud_proof",
    "external_proof",
    "phone_proof",
    "review_thread_resolved",
    "ack_cursor",
    "ack_mutation",
    "github_mutation",
    "upload_action",
    "review_action",
    "robot_command",
)
UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw\s+field\s+log|raw\s+artifact|complete\s+artifact|checksum|traceback)\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result|route|elevator|nav2|fixed[-_ ]route)\s+(success|succeeded|completed|complete|verified|passed)\b"),
    re.compile(r"(?i)\b(success|control|dispatch|start|confirm|cancel)\s+(claim|command|action)\b"),
    re.compile(r"(?i)\bobjective\s*5\s+external\s+proof\b|\bo5\s+external\s+proof\b|\bexternal\s+proof\b"),
    re.compile(r"(?i)\bo1\s+hil\b|\bhil\s+(pass|passed|complete|completed|verified|proof)\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX[^,;]{0,100}\b(resolved|closed|live\s+resolved)\b"),
    re.compile(r"(?i)\bpr\s*#?5[^,;]{0,100}\b(resolved|resolution|closed)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(ack|cursor)\s+(mutation|advance|update|write)\b"),
    re.compile(r"(?i)\b(github|review|upload)\s+(mutation|action|submit|resolve|comment)\b"),
    re.compile(r"(?i)\b(robot|base|nav2|fixed[-_ ]route)\s+(command|hint|instruction)\b"),
)


def _scrub_allowed_category_terms(text: str) -> str:
    # required checklist 类别名本身允许出现，扫描时只拦截“已证明/已完成”语义。
    allowed_terms = list(REQUIRED_OWNER_RESPONSE_MATERIALS) + list(followup.REQUIRED_FOLLOWUP_MATERIALS)
    allowed_terms.extend(
        [
            "objective_5_external_cloud_4g_oss_cdn_db_queue_proof",
            "route_elevator_field_pass",
            "verified_terminal_result",
            "dropoff_cancel_completion",
            "delivery_result",
            "true_phone_browser_or_device_proof",
            "pr5_hardware_material_resolution",
            "reviewer ACK followup acknowledgement without reviewer-resolution claim",
            "support escalation owner decision or due-date response under the same safe evidence_ref",
            "owner response material that preserves source=software_proof and not_proven",
        ]
    )
    allowed_terms.extend(
        [
            "PR #5 hardware material remains pending unless PRRT_kwDOSWB9286CJ3tX is live resolved",
            "PR #5 hardware material remains pending unless PRRT_kwDOSWB9286CJ3tX is live resolved by reviewer",
        ]
    )
    scrubbed = text
    for term in allowed_terms:
        scrubbed = scrubbed.replace(term, "<allowed_required_material_category>")
    return scrubbed


def _utc_now() -> str:
    # UTC 时间让 PC、Docker 和未来 CI 的产物可以按同一时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 稳定 JSON 字符串用于递归扫描，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短摘要，避免 raw log 或多行正文穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _safe_ref(value: Any) -> str:
    # evidence_ref 只能是短安全标识；路径、空值和弱字符串都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text):
        return text
    return ""


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表字段只输出短文本，避免复制完整 raw item。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("category") or item.get("summary"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，字符串化 JSON 不自动展开。
    return value if isinstance(value, dict) else {}


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成可审计分类原因。
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
    # 只递归 safe wrapper key，不把任意 raw payload 当可信输入。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一环 followup schema/capability，避免跳链 intake。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SOURCE_SCHEMAS or capability in {SOURCE_CAPABILITY, BRIDGE_SOURCE_CAPABILITY}:
            return candidate
    return payload


def _source_bridge(source: dict[str, Any]) -> str:
    # reviewer-ACK followup 只能作为桥接 source，不新建 owner-response mainline。
    schema = _safe_text(source.get("schema"))
    capability = _safe_text(source.get("capability"))
    if schema in {
        BRIDGE_SOURCE_SCHEMA,
        BRIDGE_SOURCE_SUMMARY_SCHEMA,
        BRIDGE_SOURCE_ROBOT_ALIAS,
        f"trashbot.{BRIDGE_SOURCE_ROBOT_ALIAS}.v1",
    } or capability == BRIDGE_SOURCE_CAPABILITY:
        return BRIDGE_SOURCE_CAPABILITY
    return ""


def _has_response_material(payload: dict[str, Any]) -> bool:
    # 用白名单字段判断 owner response，避免展开未知正文。
    for key in ("materials", "material_responses", "responses", "accepted_materials", "missing_materials", "rejected_materials"):
        value = payload.get(key)
        if isinstance(value, (dict, list)) and value:
            return True
    return False


def _find_response(payload: dict[str, Any]) -> dict[str, Any]:
    # response 可直传安全表单，也可包在 safe_copy / payload 中。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        if schema in OWNER_RESPONSE_SCHEMAS and _has_response_material(candidate):
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/proof 类别时拒绝，但不回显敏感值。
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
    # 任何层把 false-state flag 改成 true，都不能进入 accepted。
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
    # 只输出类别原因，不把命中的原始片段带进 blocked artifact。
    if value in ({}, None, ""):
        return []
    reasons: list[str] = []
    encoded = _scrub_allowed_category_terms(_encoded(value))
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_path_resolution_or_proof_fields")
    if PATH_LIKE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_credential_ros_control_hardware_success_or_resolution_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


def _surface_is_safe(payload: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是最低消费边界。
    encoded = _encoded(payload)
    return (
        _safe_text(payload.get("source")) == SOURCE
        and "not_proven" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _source_ref(source: dict[str, Any]) -> tuple[str, list[str]]:
    # source 内多个 evidence_ref 不一致时直接 blocked，保护同一证据号链路。
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


def _source_view(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 source 合同判断的数据面。
    source = _find_source(payload) if payload else {}
    ref, ref_errors = _source_ref(source) if source else ("", [])
    source_bridge = _source_bridge(source)
    return {
        "read_issue": read_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")) or (source_bridge or SOURCE_CAPABILITY),
        "source_bridge": source_bridge,
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary")),
        "followup_status": _safe_text(source.get("followup_status") or source.get("due_state") or source.get("status")),
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", True),
        "required_materials": _safe_list(source.get("required_materials")),
        "material_status": _dict(source.get("material_status")),
        "source_is_safe": _surface_is_safe(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source),
    }


def _source_ready(source: dict[str, Any]) -> tuple[bool, list[str]]:
    # source 不 ready 时不消费 owner response，防止新材料掩盖坏上游。
    reasons: list[str] = []
    source_bridge = source.get("source_bridge") == BRIDGE_SOURCE_CAPABILITY
    schema_ok = source["schema"] in SOURCE_SCHEMAS or source["capability"] in {SOURCE_CAPABILITY, BRIDGE_SOURCE_CAPABILITY}
    boundary_ok = source["evidence_boundary"] == (BRIDGE_SOURCE_BOUNDARY if source_bridge else SOURCE_BOUNDARY)
    status_ok = (
        source["followup_status"] in BRIDGE_SOURCE_STATUSES
        if source_bridge
        else source["followup_status"] in SAFE_SOURCE_STATUSES
    )
    if source["read_issue"]:
        reasons.append(source["read_issue"])
    if not schema_ok:
        reasons.append("unsupported_followup_escalation_status_schema")
    if not boundary_ok:
        reasons.append("missing_or_wrong_followup_escalation_status_boundary")
    if not status_ok:
        reasons.append("previous_followup_status_not_safe_for_owner_response_intake")
    if source_bridge and _safe_text(source.get("source_bridge")) != BRIDGE_SOURCE_CAPABILITY:
        reasons.append("missing_or_unsafe_reviewer_ack_owner_response_intake_bridge")
    if source["unsafe_reasons"]:
        reasons.extend(source["unsafe_reasons"])
    if not source["source_is_safe"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    return not reasons, list(dict.fromkeys(reasons))


def _response_material_map(response: dict[str, Any]) -> dict[str, Any]:
    # 支持 dict/list 表单，统一为 material name -> response item。
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


def _listed_materials(response: dict[str, Any], key: str) -> set[str]:
    # 简写列表让 owner 只提交类别索引，也能进入分类流程。
    value = response.get(key)
    if isinstance(value, list):
        return {_safe_text(item.get("name") if isinstance(item, dict) else item) for item in value if _safe_text(item.get("name") if isinstance(item, dict) else item)}
    if isinstance(value, dict):
        return {_safe_text(name) for name in value if _safe_text(name)}
    return set()


def _classify_item(name: str, item: Any, expected_ref: str, response_ref: str, response_missing: bool) -> tuple[str, list[str]]:
    # 单项分类保守处理：缺项 missing，显式 accepted 才进入 accepted。
    if response_missing:
        return MISSING, ["owner_response_packet_not_provided"]
    if item is None:
        return MISSING, ["required_owner_response_material_absent"]
    if not isinstance(item, dict):
        return REJECTED, ["owner_response_material_item_not_object"]

    explicit = _safe_text(item.get("classification") or item.get("status") or item.get("response_status")).lower()
    item_ref = _safe_ref(item.get("safe_evidence_ref") or item.get("evidence_ref") or response_ref)
    reasons: list[str] = []
    if not item_ref:
        reasons.append("missing_safe_evidence_ref")
    elif item_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if _unsafe_reasons(item):
        reasons.append("unsafe_owner_response_material")
    if reasons:
        return BLOCKED, list(dict.fromkeys(reasons))
    if item.get("rejected") is True or explicit == REJECTED:
        return REJECTED, ["owner_marked_rejected_not_proven"]
    if item.get("unsafe") is True or explicit == "unsafe":
        return BLOCKED, ["owner_marked_unsafe_not_proven"]
    if item.get("missing") is True or explicit == MISSING:
        return MISSING, ["owner_marked_missing_not_proven"]
    if item.get("accepted") is True or explicit in {ACCEPTED, "received_not_reviewed"}:
        return ACCEPTED, ["accepted_for_review_not_proven"]
    return REJECTED, ["missing_explicit_safe_owner_response_status"]


def _classify_materials(response: dict[str, Any], response_issue: str, expected_ref: str) -> tuple[dict[str, list[str]], list[dict[str, Any]], list[str], str]:
    # 逐项分类后汇总 readiness；partial response 不能被 happy path 覆盖。
    material_map = _response_material_map(response)
    response_ref = _safe_ref(response.get("safe_evidence_ref") or response.get("evidence_ref"))
    response_ref_issue = ""
    if response and not response_ref:
        response_ref_issue = "owner_response_missing_safe_evidence_ref"
    elif response_ref and response_ref != expected_ref:
        response_ref_issue = "owner_response_evidence_ref_mismatch"
    accepted_names = _listed_materials(response, "accepted_materials") | _listed_materials(response, "received_materials")
    missing_names = _listed_materials(response, "missing_materials")
    rejected_names = _listed_materials(response, "rejected_materials")
    categories = {ACCEPTED: [], MISSING: [], REJECTED: [], BLOCKED: []}
    details: list[dict[str, Any]] = []

    for name in REQUIRED_OWNER_RESPONSE_MATERIALS:
        item = material_map.get(name)
        if item is None and name in accepted_names:
            item = {"name": name, "status": ACCEPTED, "safe_evidence_ref": response_ref, "summary": "accepted category index only"}
        elif item is None and name in missing_names:
            item = {"name": name, "status": MISSING, "safe_evidence_ref": response_ref}
        elif item is None and name in rejected_names:
            item = {"name": name, "status": REJECTED, "safe_evidence_ref": response_ref}
        status, reasons = _classify_item(name, item, expected_ref, response_ref, bool(response_issue))
        if response_ref_issue and status != MISSING:
            status = BLOCKED
            reasons = [response_ref_issue]
        categories[status].append(name)
        details.append(
            {
                "name": name,
                "classification": status,
                "classification_reasons": reasons,
                "safe_evidence_ref": expected_ref,
                "accepted_means": "accepted_for_review_not_proven" if status == ACCEPTED else "not_accepted",
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        )
    response_unsafe = _unsafe_reasons(response) if response else []
    if response_unsafe:
        # 顶层 response unsafe 使所有非 missing 材料 blocked，避免局部绕过。
        for key in (ACCEPTED, REJECTED):
            categories[BLOCKED].extend(categories[key])
            categories[key] = []
        for detail in details:
            if detail["classification"] != MISSING:
                detail["classification"] = BLOCKED
                detail["classification_reasons"] = ["unsafe_owner_response_packet"]
    return categories, details, response_unsafe, response_ref_issue


def _owner_response_status(source_ok: bool, source_reasons: list[str], response_issue: str, categories: dict[str, list[str]], response_unsafe: list[str], response_ref_issue: str) -> tuple[str, list[str], int]:
    # 总分类只用四个短枚举，便于后续 review 和 UI 只读消费。
    if not source_ok:
        return BLOCKED, source_reasons, 2
    if response_ref_issue:
        return BLOCKED, [response_ref_issue], 4
    if response_unsafe or categories[BLOCKED]:
        return BLOCKED, response_unsafe or ["blocked_owner_response_material_not_proven"], 5
    if response_issue:
        return MISSING, [response_issue], 3
    if categories[REJECTED]:
        return REJECTED, ["rejected_owner_response_material_not_proven"], 6
    if categories[MISSING]:
        return MISSING, ["missing_required_owner_response_material_not_proven"], 3
    return ACCEPTED, ["accepted_for_review_not_proven"], 0


def _safe_flags() -> dict[str, Any]:
    # false flags 在 artifact、summary、safe_copy 中重复，避免局部消费误启控制。
    return {
        "source": SOURCE,
        "software_proof": True,
        "not_proven": True,
        "status": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": "no OKR percentage lift",
    }


def _non_access_scope() -> list[str]:
    # 明确不可访问范围，避免把本 gate 误解为现场 proof。
    return [
        "raw_task_record",
        "raw_nav2_runtime_log",
        "raw_fixed_route_runtime_log",
        "raw_route_completion_signal",
        "raw_elevator_door_state",
        "raw_target_floor_confirmation",
        "raw_human_assistance_record",
        "raw_dropoff_cancel_completion",
        "raw_delivery_result",
        "raw_route_elevator_field_pass",
        "raw_true_phone_browser_evidence",
        "raw_diagnostics",
        "ros_graph",
        "serial_uart",
        "wave_rover",
        "real_elevator",
        "external_cloud",
        "real_phone_or_browser",
        "verified_terminal_result",
        "pr5_resolution",
        "robot_action",
    ]


def _next_required_evidence(owner_status: str, evidence_ref: str, categories: dict[str, list[str]], reasons: list[str]) -> list[str]:
    # next evidence 是人工补证清单，不是 Robot action 指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if owner_status == ACCEPTED:
        return [
            f"route accepted owner response metadata for evidence_ref={ref} into later review without enabling controls",
            "keep source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false",
            "keep PR #5 hardware material pending until reviewer live-resolves PRRT_kwDOSWB9286CJ3tX outside this gate",
        ]
    missing = [f"provide sanitized owner response material category: {name} for evidence_ref={ref}" for name in categories[MISSING]]
    rejected = [f"replace rejected owner response material category: {name} for evidence_ref={ref}" for name in categories[REJECTED]]
    blocked = [f"rerun safe owner response intake without unsafe/overclaim material category: {name} for evidence_ref={ref}" for name in categories[BLOCKED]]
    return missing + rejected + blocked or [f"rerun owner response intake for evidence_ref={ref}", *reasons]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.py --review-handoff-json <review_handoff.json> --followup-policy-json <followup_policy.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py --followup-status-json <followup_status.json> --owner-response-json <owner_response_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift",
    ]


def _safe_copy(owner_status: str, evidence_ref: str, reasons: list[str], categories: dict[str, list[str]], source_view: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是后续 review/diagnostics/mobile 的白名单消费面。
    bridge_enabled = source_view.get("source_bridge") == BRIDGE_SOURCE_CAPABILITY
    output_boundary = BRIDGE_EVIDENCE_BOUNDARY if bridge_enabled else EVIDENCE_BOUNDARY
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "bridge_capability": BRIDGE_CAPABILITY if bridge_enabled else "",
        "evidence_boundary": output_boundary,
        "bridge_evidence_boundary": BRIDGE_EVIDENCE_BOUNDARY if bridge_enabled else "",
        "source_bridge": BRIDGE_SOURCE_CAPABILITY if bridge_enabled else "",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "owner_response_status": owner_status,
        "allowed_owner_response_statuses": list(ALLOWED_OWNER_RESPONSE_STATUSES),
        "owner_response_reasons": reasons,
        "accepted_materials": categories[ACCEPTED],
        "missing_materials": categories[MISSING],
        "rejected_materials": categories[REJECTED],
        "blocked_materials": categories[BLOCKED],
        "source_followup_status": source_view["followup_status"],
        "source_boundary": source_view["evidence_boundary"] or (BRIDGE_SOURCE_BOUNDARY if bridge_enabled else SOURCE_BOUNDARY),
        "accepted_means": "accepted_for_review_not_proven",
        "pr5_thread": {
            "thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "resolution_rule": "pending unless live resolved by reviewer outside this gate",
        },
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
    followup_status_json: str,
    owner_response_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取上一环 follow-up status 与 owner response，生成 fail-closed intake。"""
    source_payload, source_issue = _load_json(followup_status_json, "followup_status_json")
    source_view = _source_view(source_payload, source_issue)
    source_ok, source_reasons = _source_ready(source_view)
    requested_ref = _safe_ref(evidence_ref) or source_view["safe_evidence_ref"]
    if evidence_ref and requested_ref != source_view["safe_evidence_ref"]:
        # CLI 指定 ref 与 source 不一致时，按同证据号硬约束失败。
        source_ok = False
        source_reasons.append("evidence_ref_mismatch")

    response_payload, response_issue = _load_json(owner_response_json, "owner_response_json")
    response = _find_response(response_payload) if response_payload else {}
    response_schema = _safe_text(response.get("schema"))
    if response and response_schema not in OWNER_RESPONSE_SCHEMAS:
        response_issue = "owner_response_json_unsupported_schema"
    categories, material_details, response_unsafe, response_ref_issue = _classify_materials(response, response_issue, requested_ref)
    owner_status, reasons, exit_code = _owner_response_status(source_ok, source_reasons, response_issue, categories, response_unsafe, response_ref_issue)
    generated_at = _utc_now()
    next_required_evidence = _next_required_evidence(owner_status, requested_ref, categories, reasons)
    rerun_commands = _rerun_commands(requested_ref)
    safe_copy = _safe_copy(owner_status, requested_ref, reasons, categories, source_view)
    bridge_enabled = source_view.get("source_bridge") == BRIDGE_SOURCE_CAPABILITY
    output_boundary = BRIDGE_EVIDENCE_BOUNDARY if bridge_enabled else EVIDENCE_BOUNDARY
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "bridge_capability": BRIDGE_CAPABILITY if bridge_enabled else "",
        "source_capability": SOURCE_CAPABILITY,
        "bridge_source_capability": BRIDGE_SOURCE_CAPABILITY if bridge_enabled else "",
        "evidence_boundary": output_boundary,
        "bridge_evidence_boundary": BRIDGE_EVIDENCE_BOUNDARY if bridge_enabled else "",
        "source_bridge": BRIDGE_SOURCE_CAPABILITY if bridge_enabled else "",
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "owner_response_status": owner_status,
        "allowed_owner_response_statuses": list(ALLOWED_OWNER_RESPONSE_STATUSES),
        "owner_response_reasons": list(dict.fromkeys(reasons)),
        "accepted_materials": categories[ACCEPTED],
        "missing_materials": categories[MISSING],
        "rejected_materials": categories[REJECTED],
        "blocked_materials": categories[BLOCKED],
        "required_owner_response_materials": list(REQUIRED_OWNER_RESPONSE_MATERIALS),
        "material_response_details": material_details,
        "accepted_means": "accepted_for_review_not_proven",
        "previous_followup_reference": {
            "capability": source_view["capability"],
            "schema": source_view["schema"],
            "evidence_boundary": source_view["evidence_boundary"],
            "followup_status": source_view["followup_status"],
            "safe_evidence_ref": source_view["safe_evidence_ref"],
            "source_bridge": BRIDGE_SOURCE_CAPABILITY if bridge_enabled else "",
            "bridge_capability": BRIDGE_CAPABILITY if bridge_enabled else "",
        },
        "pr5_thread": {
            "thread_id": "PRRT_kwDOSWB9286CJ3tX",
            "state": "unresolved",
            "material_state": "hardware_material_pending",
            "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
        },
        "blocked_claims": [
            "raw_field_logs",
            "route_elevator_field_pass",
            "phone_browser_proof",
            "cloud_external_proof",
            "hil_pass",
            "delivery_success",
            "safe_control",
            "pr5_resolution",
            "okr_percentage_lift",
        ],
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "safety_markers": [
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            BRIDGE_CAPABILITY,
            BRIDGE_EVIDENCE_BOUNDARY,
            "source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status",
            "no OKR percentage lift",
            ACCEPTED,
            MISSING,
            REJECTED,
            BLOCKED,
        ],
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake": owner_status,
        **common,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake": owner_status,
        "source_followup_status": {
            "ready": source_ok,
            "read_issue": source_issue,
            "schema": source_view["schema"],
            "evidence_boundary": source_view["evidence_boundary"],
            "unsafe_reasons": source_view["unsafe_reasons"],
            "source_reasons": source_reasons,
        },
        "owner_response_packet": {
            "load_issue": response_issue,
            "schema": response_schema,
            "unsafe_reasons": response_unsafe,
            "response_ref_issue": response_ref_issue,
        },
        **common,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "non_access_scope": _non_access_scope(),
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1 "
            "from a sanitized follow-up escalation status artifact/summary/Robot alias plus sanitized owner response "
            "metadata. Keeps source=software_proof, software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift."
        )
    )
    parser.add_argument("--followup-status-json", required=True, help="sanitized follow-up escalation status artifact, summary, or Robot alias JSON")
    parser.add_argument("--owner-response-json", required=True, help="sanitized owner response packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional owner response intake artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
        args.followup_status_json,
        args.owner_response_json,
        args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_intake_summary_file:{material_pack._safe_ref(args.summary_output)}")
        print(f"owner_response_status:{artifact['owner_response_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
