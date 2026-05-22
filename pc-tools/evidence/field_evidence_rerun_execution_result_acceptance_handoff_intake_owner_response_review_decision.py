#!/usr/bin/env python3
"""生成 acceptance handoff intake owner response review decision gate。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`
之后，只读取上一环 safe artifact / summary / Robot safe alias 与脱敏 review
packet。输出只把同一 safe evidence_ref 下的 owner response review 归档为
review decision metadata；ready 也只是后续 handoff readiness，不读取真实现场日志、
不证明 route/elevator/phone/cloud/hardware，也不启用控制。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake as intake
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary.v1"
REVIEW_PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_packet.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision"
SOURCE_CAPABILITY = intake.CAPABILITY
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate"
SOURCE_BOUNDARY = intake.EVIDENCE_BOUNDARY

READY = "ready_for_owner_response_review_handoff_not_proven"
NEEDS_REWORK = "review_needs_owner_rework"
REF_MISMATCH = "review_evidence_ref_mismatch"
UNSAFE_REJECTED = "review_unsafe_rejected"
BLOCKED_MISSING_INTAKE = "blocked_missing_owner_response_intake"
ALLOWED_REVIEW_DECISIONS = (READY, NEEDS_REWORK, REF_MISMATCH, UNSAFE_REJECTED, BLOCKED_MISSING_INTAKE)

REQUIRED_REVIEW_MATERIALS = intake.REQUIRED_OWNER_RESPONSE_MATERIALS

SOURCE_SCHEMAS = {
    intake.SCHEMA,
    intake.SUMMARY_SCHEMA,
    intake.ROBOT_ALIAS,
    f"trashbot.{intake.ROBOT_ALIAS}.v1",
}
REVIEW_PACKET_SCHEMAS = {"", REVIEW_PACKET_SCHEMA, f"{REVIEW_PACKET_SCHEMA}.summary"}

# 设计约束 01：本 gate 只处理安全 review metadata，不读取 raw field logs。
# 设计约束 02：上一环必须是 owner response intake，不能跳过 intake 直接 review。
# 设计约束 03：review packet 只能确认材料类别，不复制材料正文或完整 artifact。
# 设计约束 04：同一 safe evidence_ref 是 source 与 review packet 的硬约束。
# 设计约束 05：ready 只表示 ready_for_handoff_not_proven，不表示现场通过。
# 设计约束 06：missing material 进入 rework，不用 happy path 覆盖缺项。
# 设计约束 07：evidence_ref mismatch 有专用状态，方便后续 owner 修正复账号。
# 设计约束 08：unsafe、success/control、O5 external、O1 HIL、PR #5 resolution 一律 rejected。
# 设计约束 09：缺 source、坏 JSON、wrong boundary 一律 blocked_missing_owner_response_intake。
# 设计约束 10：source=software_proof、not_proven 与三个 false flag 必须逐层保留。
# 设计约束 11：PR #5 thread X 固定 unresolved / hardware_material_pending。
# 设计约束 12：输出 safe_copy 是 Robot/mobile 只读面，不包含 raw source 或 raw review。
# 设计约束 13：wrapper/nested JSON 只递归白名单 key，防止误采信任意 payload。
# 设计约束 14：CLI 只在 ready 时返回 0，其余分类都返回非 0。
# 设计约束 15：dependency-free，方便 macOS PC、Docker 和 unittest 离线复跑。
# 设计约束 16：本文件不查 vendor，因为不新增硬件参数、串口、波特率或协议假设。
# 设计约束 17：所有技术注释使用中文，解释 fail-closed 原因和字段取舍。
# 设计约束 18：最终 artifact/summary 递归脱敏，防止新字段绕过扫描。
# 设计约束 19：本 gate 不更新 Robot diagnostics、mobile/web、OKR 或 sprint closeout。
# 设计约束 20：所有状态枚举严格限制为本 sprint tech-plan 的五个值。
# 设计约束 21：next_required_evidence 是人工补证建议，不是机器人控制命令。
# 设计约束 22：no OKR percentage lift 必须留在 artifact、summary 和 safe_copy 中。

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate; "
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "ready_for_owner_response_review_handoff_not_proven; review_needs_owner_rework; "
    "review_evidence_ref_mismatch; review_unsafe_rejected; blocked_missing_owner_response_intake; "
    "no OKR percentage lift"
)

WRAPPER_KEYS = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
    "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
    intake.ROBOT_ALIAS,
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_packet",
    "owner_response_review_packet",
    "review_packet",
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
    "reviewer_resolution",
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
)


def _scrub_allowed_category_terms(text: str) -> str:
    # required checklist 类别名允许出现，扫描只拦截“已证明/已完成”语义。
    scrubbed = text
    for term in REQUIRED_REVIEW_MATERIALS:
        scrubbed = scrubbed.replace(term, "<allowed_required_material_category>")
    return scrubbed


def _utc_now() -> str:
    # UTC 时间让 PC、Docker 和未来 CI 的产物可以按同一时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 稳定 JSON 字符串用于递归安全扫描，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短单行，避免 raw log 或多行 artifact 穿透。
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
    # wrapper 只接受 object，字符串化 JSON 不作为可信 safe source。
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
    # 只递归 safe wrapper key，避免 raw payload 被误当作可信输入。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一环 owner_response_intake schema/capability。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _has_review_material(payload: dict[str, Any]) -> bool:
    # 用白名单字段判断 review packet，避免展开未知正文。
    for key in ("materials", "material_reviews", "reviewed_materials", "confirmed_materials", "missing_materials", "rejected_materials"):
        value = payload.get(key)
        if isinstance(value, (dict, list)) and value:
            return True
    return False


def _find_review_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # review packet 可直传安全表单，也可包在 safe_copy / payload 中。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        if schema in REVIEW_PACKET_SCHEMAS and _has_review_material(candidate):
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/proof/resolution 类别时拒绝，不回显敏感值。
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
    # 任何层把 false-state flag 改成 true，都不能进入 ready。
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
    # 只输出类别原因，不把命中的原始片段带进 rejected artifact。
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
    # source 内多个 evidence_ref 不一致时直接 mismatch，保护同一证据号链路。
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
    safe_copy = _dict(source.get("safe_copy"))
    ref, ref_errors = _source_ref(source) if source else ("", [])
    return {
        "read_issue": read_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")) or SOURCE_CAPABILITY,
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or safe_copy.get("evidence_boundary")),
        "owner_response_status": _safe_text(source.get("owner_response_status") or safe_copy.get("owner_response_status")),
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "accepted_materials": _safe_list(source.get("accepted_materials") or safe_copy.get("accepted_materials")),
        "missing_materials": _safe_list(source.get("missing_materials") or safe_copy.get("missing_materials")),
        "rejected_materials": _safe_list(source.get("rejected_materials") or safe_copy.get("rejected_materials")),
        "blocked_materials": _safe_list(source.get("blocked_materials") or safe_copy.get("blocked_materials")),
        "required_materials": _safe_list(source.get("required_owner_response_materials") or source.get("required_materials")),
        "owner_response_reasons": _safe_list(source.get("owner_response_reasons") or source.get("decision_reasons")),
        "previous_followup_reference": _dict(source.get("previous_followup_reference")),
        "pr5_thread": _dict(source.get("pr5_thread") or safe_copy.get("pr5_thread")),
        "source_is_safe": _surface_is_safe(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_ready(source: dict[str, Any], requested_ref: str) -> tuple[bool, list[str], bool]:
    # source 不 ready 时不消费 review packet，防止新 review 掩盖坏上游。
    reasons: list[str] = []
    schema_ok = source["schema"] in SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    if source["read_issue"]:
        reasons.append(source["read_issue"])
    if not schema_ok:
        reasons.append("unsupported_owner_response_intake_schema")
    if source["evidence_boundary"] != SOURCE_BOUNDARY:
        reasons.append("missing_or_wrong_owner_response_intake_boundary")
    if source["owner_response_status"] != intake.ACCEPTED:
        reasons.append("previous_owner_response_intake_not_accepted")
    if source["unsafe_reasons"]:
        reasons.extend(source["unsafe_reasons"])
    if not source["source_is_safe"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if requested_ref and source["safe_evidence_ref"] and requested_ref != source["safe_evidence_ref"]:
        reasons.append("evidence_ref_mismatch")
    # 只有真实 ref 不一致进入 mismatch；缺 source/ref 仍按缺上一环 intake 处理。
    is_ref_mismatch = any(reason in {"evidence_ref_mismatch", "review_packet_evidence_ref_mismatch"} for reason in reasons)
    return not reasons, list(dict.fromkeys(reasons)), is_ref_mismatch


def _review_material_map(packet: dict[str, Any]) -> dict[str, Any]:
    # 支持 dict/list 表单，统一为 material name -> review item。
    for key in ("materials", "material_reviews", "reviewed_materials"):
        value = packet.get(key)
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


def _listed_materials(packet: dict[str, Any], key: str) -> set[str]:
    # 简写列表让 reviewer 只提交类别索引，也能进入分类流程。
    value = packet.get(key)
    if isinstance(value, list):
        return {_safe_text(item.get("name") if isinstance(item, dict) else item) for item in value if _safe_text(item.get("name") if isinstance(item, dict) else item)}
    if isinstance(value, dict):
        return {_safe_text(name) for name in value if _safe_text(name)}
    return set()


def _classify_review_item(name: str, item: Any, expected_ref: str, packet_ref: str, packet_missing: bool) -> tuple[str, list[str]]:
    # 单项 review 保守处理：缺项 needs_rework，显式 confirmed 才进入 ready。
    if packet_missing:
        return NEEDS_REWORK, ["owner_response_review_packet_not_provided"]
    if item is None:
        return NEEDS_REWORK, ["required_review_material_absent"]
    if not isinstance(item, dict):
        return UNSAFE_REJECTED, ["review_material_item_not_object"]

    explicit = _safe_text(item.get("classification") or item.get("status") or item.get("review_status")).lower()
    item_ref = _safe_ref(item.get("safe_evidence_ref") or item.get("evidence_ref") or packet_ref)
    if not item_ref:
        return REF_MISMATCH, ["missing_safe_evidence_ref"]
    if item_ref != expected_ref:
        return REF_MISMATCH, ["evidence_ref_mismatch"]
    if _unsafe_reasons(item):
        return UNSAFE_REJECTED, ["unsafe_owner_response_review_material"]
    if item.get("rejected") is True or item.get("unsafe") is True or explicit in {"rejected", "unsafe", "review_unsafe_rejected"}:
        return UNSAFE_REJECTED, ["reviewer_marked_unsafe_or_rejected_not_proven"]
    if item.get("missing") is True or item.get("needs_rework") is True or explicit in {"missing", "needs_rework", "review_needs_owner_rework"}:
        return NEEDS_REWORK, ["reviewer_marked_needs_rework_not_proven"]
    if item.get("confirmed") is True or item.get("accepted") is True or explicit in {"confirmed", "accepted", "reviewed_not_proven", "ready"}:
        return READY, ["confirmed_for_owner_response_review_handoff_not_proven"]
    return NEEDS_REWORK, ["missing_explicit_safe_review_status"]


def _classify_review_materials(packet: dict[str, Any], packet_issue: str, expected_ref: str) -> tuple[dict[str, list[str]], list[dict[str, Any]], list[str], str]:
    # 逐项分类后汇总 readiness；partial review 不能被 happy path 覆盖。
    material_map = _review_material_map(packet)
    packet_ref = _safe_ref(packet.get("safe_evidence_ref") or packet.get("evidence_ref"))
    packet_ref_issue = ""
    if packet and not packet_ref:
        packet_ref_issue = "review_packet_missing_safe_evidence_ref"
    elif packet_ref and packet_ref != expected_ref:
        packet_ref_issue = "review_packet_evidence_ref_mismatch"
    confirmed_names = _listed_materials(packet, "confirmed_materials") | _listed_materials(packet, "accepted_materials")
    missing_names = _listed_materials(packet, "missing_materials")
    rejected_names = _listed_materials(packet, "rejected_materials") | _listed_materials(packet, "unsafe_materials")
    categories = {READY: [], NEEDS_REWORK: [], REF_MISMATCH: [], UNSAFE_REJECTED: []}
    details: list[dict[str, Any]] = []

    for name in REQUIRED_REVIEW_MATERIALS:
        item = material_map.get(name)
        if item is None and name in confirmed_names:
            item = {"name": name, "status": "confirmed", "safe_evidence_ref": packet_ref, "summary": "confirmed category index only"}
        elif item is None and name in missing_names:
            item = {"name": name, "status": "missing", "safe_evidence_ref": packet_ref}
        elif item is None and name in rejected_names:
            item = {"name": name, "status": "rejected", "safe_evidence_ref": packet_ref}
        status, reasons = _classify_review_item(name, item, expected_ref, packet_ref, bool(packet_issue))
        if packet_ref_issue and status not in (NEEDS_REWORK,):
            status = REF_MISMATCH
            reasons = [packet_ref_issue]
        categories[status].append(name)
        details.append(
            {
                "name": name,
                "classification": status,
                "classification_reasons": reasons,
                "safe_evidence_ref": expected_ref,
                "ready_means": "ready_for_owner_response_review_handoff_not_proven" if status == READY else "not_ready",
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        )
    packet_unsafe = _unsafe_reasons(packet) if packet else []
    if packet_unsafe:
        # 顶层 packet unsafe 使所有非 rework 材料 rejected，避免局部绕过。
        for key in (READY, REF_MISMATCH):
            categories[UNSAFE_REJECTED].extend(categories[key])
            categories[key] = []
        for detail in details:
            if detail["classification"] != NEEDS_REWORK:
                detail["classification"] = UNSAFE_REJECTED
                detail["classification_reasons"] = ["unsafe_owner_response_review_packet"]
    return categories, details, packet_unsafe, packet_ref_issue


def _review_decision(
    source_ok: bool,
    source_reasons: list[str],
    source_ref_mismatch: bool,
    packet_issue: str,
    categories: dict[str, list[str]],
    packet_unsafe: list[str],
    packet_ref_issue: str,
) -> tuple[str, list[str], int]:
    # 总分类严格输出五个 allowed states，便于后续 Robot/mobile 只读消费。
    if source_ref_mismatch:
        return REF_MISMATCH, source_reasons, 4
    if not source_ok:
        return BLOCKED_MISSING_INTAKE, source_reasons, 2
    if packet_ref_issue or categories[REF_MISMATCH]:
        return REF_MISMATCH, [packet_ref_issue or "review_material_evidence_ref_mismatch"], 4
    if packet_unsafe or categories[UNSAFE_REJECTED]:
        return UNSAFE_REJECTED, packet_unsafe or ["unsafe_owner_response_review_material_not_proven"], 5
    if packet_issue:
        return NEEDS_REWORK, [packet_issue], 3
    if categories[NEEDS_REWORK]:
        return NEEDS_REWORK, ["missing_or_incomplete_required_review_material_not_proven"], 3
    return READY, ["ready_for_owner_response_review_handoff_not_proven"], 0


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


def _next_required_evidence(decision: str, evidence_ref: str, categories: dict[str, list[str]], reasons: list[str]) -> list[str]:
    # next evidence 是人工补证清单，不是 Robot action 指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == READY:
        return [
            f"handoff owner response review decision metadata for evidence_ref={ref} without enabling controls",
            "keep source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false",
            "keep PR #5 hardware material pending until reviewer live-resolves PRRT_kwDOSWB9286CJ3tX outside this gate",
        ]
    if decision == REF_MISMATCH:
        return [f"rerun owner response review packet with the same safe evidence_ref={ref}", *reasons]
    if decision == UNSAFE_REJECTED:
        return [f"resubmit sanitized owner response review packet without unsafe/overclaim material for evidence_ref={ref}"]
    if decision == BLOCKED_MISSING_INTAKE:
        return [f"provide supported owner response intake safe artifact/summary/Robot alias for evidence_ref={ref}"]
    return [f"provide sanitized owner response review material category: {name} for evidence_ref={ref}" for name in categories[NEEDS_REWORK]] or [
        f"backfill owner response review packet for evidence_ref={ref}",
        *reasons,
    ]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py --followup-status-json <followup_status.json> --owner-response-json <owner_response_packet.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.py --owner-response-intake-json <owner_response_intake.json> --owner-response-review-json <owner_response_review_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift",
    ]


def _pr5_thread() -> dict[str, str]:
    # PR #5 状态固定保守表达，除非真实 reviewer evidence 更新。
    return {
        "thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
    }


def _safe_copy(decision: str, evidence_ref: str, reasons: list[str], categories: dict[str, list[str]], source_view: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是后续 review/diagnostics/mobile 的白名单消费面。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "owner_response_review_decision": decision,
        "allowed_owner_response_review_decision_states": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "accepted_materials": source_view["accepted_materials"],
        "missing_materials": source_view["missing_materials"],
        "rejected_materials": source_view["rejected_materials"],
        "blocked_materials": source_view["blocked_materials"],
        "review_confirmed_materials": categories[READY],
        "review_needs_rework_materials": categories[NEEDS_REWORK],
        "review_ref_mismatch_materials": categories[REF_MISMATCH],
        "review_unsafe_rejected_materials": categories[UNSAFE_REJECTED],
        "source_owner_response_status": source_view["owner_response_status"],
        "source_boundary": SOURCE_BOUNDARY,
        "ready_means": "ready_for_owner_response_review_handoff_not_proven",
        "pr5_thread": _pr5_thread(),
    }


def build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
    owner_response_intake_json: str,
    owner_response_review_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取上一环 owner response intake 与 review packet，生成 fail-closed review decision。"""
    source_payload, source_issue = _load_json(owner_response_intake_json, "owner_response_intake_json")
    source_view = _source_view(source_payload, source_issue)
    requested_ref = _safe_ref(evidence_ref) or source_view["safe_evidence_ref"]
    source_ok, source_reasons, source_ref_mismatch = _source_ready(source_view, requested_ref)

    review_payload, review_issue = _load_json(owner_response_review_json, "owner_response_review_json")
    review_packet = _find_review_packet(review_payload) if review_payload else {}
    review_schema = _safe_text(review_packet.get("schema"))
    if review_packet and review_schema not in REVIEW_PACKET_SCHEMAS:
        review_issue = "owner_response_review_json_unsupported_schema"
    categories, material_details, packet_unsafe, packet_ref_issue = _classify_review_materials(review_packet, review_issue, requested_ref)
    decision, reasons, exit_code = _review_decision(
        source_ok,
        source_reasons,
        source_ref_mismatch,
        review_issue,
        categories,
        packet_unsafe,
        packet_ref_issue,
    )
    if not requested_ref:
        # 缺 safe ref 时仍输出 blocked artifact，但不伪造证据号。
        requested_ref = "missing_safe_evidence_ref"
    reasons = list(dict.fromkeys(reasons or [decision]))
    generated_at = _utc_now()
    next_required_evidence = _next_required_evidence(decision, requested_ref, categories, reasons)
    rerun_commands = _rerun_commands(requested_ref)
    safe_copy = _safe_copy(decision, requested_ref, reasons, categories, source_view)
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "owner_response_review_decision": decision,
        "allowed_owner_response_review_decision_states": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": reasons,
        "accepted_materials": source_view["accepted_materials"],
        "missing_materials": source_view["missing_materials"],
        "rejected_materials": source_view["rejected_materials"],
        "blocked_materials": source_view["blocked_materials"],
        "required_review_materials": list(REQUIRED_REVIEW_MATERIALS),
        "review_material_details": material_details,
        "review_confirmed_materials": categories[READY],
        "review_needs_rework_materials": categories[NEEDS_REWORK],
        "review_ref_mismatch_materials": categories[REF_MISMATCH],
        "review_unsafe_rejected_materials": categories[UNSAFE_REJECTED],
        "ready_means": "ready_for_owner_response_review_handoff_not_proven",
        "previous_owner_response_intake_reference": {
            "capability": SOURCE_CAPABILITY,
            "schema": source_view["schema"],
            "evidence_boundary": source_view["evidence_boundary"],
            "owner_response_status": source_view["owner_response_status"],
            "safe_evidence_ref": source_view["safe_evidence_ref"],
        },
        "pr5_thread": _pr5_thread(),
        "blocked_claims": [
            "raw_field_logs",
            "route_elevator_field_pass",
            "nav2_fixed_route_runtime_pass",
            "phone_browser_proof",
            "cloud_external_proof",
            "hil_pass",
            "wave_rover_uart_proof",
            "verified_terminal_result",
            "dropoff_cancel_completion",
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
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
            "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate",
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            READY,
            NEEDS_REWORK,
            REF_MISMATCH,
            UNSAFE_REJECTED,
            BLOCKED_MISSING_INTAKE,
        ],
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision": decision,
        **common,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision": decision,
        "source_owner_response_intake": {
            "ready": source_ok,
            "read_issue": source_issue,
            "schema": source_view["schema"],
            "evidence_boundary": source_view["evidence_boundary"],
            "owner_response_status": source_view["owner_response_status"],
            "unsafe_reasons": source_view["unsafe_reasons"],
            "source_reasons": source_reasons,
        },
        "owner_response_review_packet": {
            "load_issue": review_issue,
            "schema": review_schema,
            "unsafe_reasons": packet_unsafe,
            "response_ref_issue": packet_ref_issue,
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
            "Build trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.v1 "
            "from a sanitized owner response intake artifact/summary/Robot alias plus sanitized owner response review "
            "packet. Keeps source=software_proof, software_proof, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, and no OKR percentage lift."
        )
    )
    parser.add_argument("--owner-response-intake-json", required=True, help="sanitized owner response intake artifact, summary, or Robot alias JSON")
    parser.add_argument("--owner-response-review-json", required=True, help="sanitized owner response review packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional owner response review decision artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
        args.owner_response_intake_json,
        args.owner_response_review_json,
        args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_review_decision_summary_file:{material_pack._safe_ref(args.summary_output)}")
        print(f"owner_response_review_decision:{artifact['owner_response_review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
