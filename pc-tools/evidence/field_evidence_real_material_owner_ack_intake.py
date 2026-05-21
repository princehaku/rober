#!/usr/bin/env python3
"""生成 field_evidence_real_material_owner_ack_intake PC gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_followup_escalation_status as followup
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_real_material_owner_ack_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_owner_ack_intake_summary.v1"
ROBOT_SUMMARY_SCHEMA = "trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_real_material_owner_ack_intake"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_real_material_owner_ack_intake_gate"

# 上游必须是 followup escalation 的安全 surface，不能绕过真实材料追责链。
SOURCE_SCHEMAS = {followup.SCHEMA, followup.SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {followup.EVIDENCE_BOUNDARY}
SOURCE_READY_STATUSES = {followup.READY_STATUS, followup.BACKFILL_STATUS}

# owner ack packet 允许无 schema，便于 field owner 先用脱敏 JSON 表单回填。
ACK_SCHEMAS = {
    "",
    "trashbot.field_evidence_real_material_owner_ack_packet.v1",
    "trashbot.field_evidence_real_material_owner_ack_packet_summary.v1",
}

READY_STATUS = "ready_for_field_evidence_real_material_owner_ack_intake_not_proven"
MISSING_ACK_STATUS = "missing_field_material_owner_ack_intake_not_proven"
REJECTED_STATUS = "blocked_rejected_or_unsafe_field_material_owner_ack_intake_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_material_owner_ack_intake_source"
MISMATCH_STATUS = "evidence_ref_mismatch_field_material_owner_ack_intake_blocked"

DEFAULT_EVIDENCE_REF = "field-real-material-owner-ack-2026-05-21T21-22Z"
SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,96}$")
ACK_TRUE_VALUES = {"ack", "acked", "acknowledged", "accepted", "received", "confirmed", "approved"}
ACK_FALSE_VALUES = {"", "missing", "none", "pending", "needs_owner_ack", "rejected", "blocked"}

REQUIRED_CATEGORIES = (
    "route_elevator_runtime_materials",
    "task_record_and_completion_materials",
    "elevator_door_floor_materials",
    "dropoff_cancel_delivery_result_materials",
    "diagnostics_mobile_safe_summary_materials",
)

NOT_PROVEN_ITEMS = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime_log",
    "real_route_completion_signal",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_field_task_record",
    "real_dropoff_completion_material",
    "real_cancel_completion_material",
    "real_delivery_result",
    "real_delivery_success",
    "hil_pass",
    "o5_external_proof",
    "true_phone_browser_proof",
)

FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
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
    "Traceback",
    "checksum",
    "complete artifact",
    "raw artifact",
)

SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\broute/elevator\s+(success|succeeded|passed|validated)\b"),
    re.compile(r"(?i)\bcontrol\s+(enabled|allowed|authorized)\b"),
)

BOUNDARY_NOTE = (
    "field_evidence_real_material_owner_ack_intake; "
    "software_proof_docker_field_evidence_real_material_owner_ack_intake_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "owner acknowledgement intake only, route/elevator and delivery outcome remain unproven"
)

# 设计约束 01：本 gate 只消费 followup escalation 安全摘要和 owner ack packet。
# 设计约束 02：ack 只是现场 owner 已接收/分类缺口，不是现场材料已通过。
# 设计约束 03：source=software_proof、not_proven 与三类 false flag 必须逐层保留。
# 设计约束 04：同一 safe evidence_ref 是唯一串联主键，错配必须 fail closed。
# 设计约束 05：owner ack 缺失时只能输出 missing，不能自动生成 acknowledged。
# 设计约束 06：accepted/missing/rejected/blocked 是材料类别状态，不是交付结果。
# 设计约束 07：不输出 raw ROS topic、串口、WAVE ROVER、路径、凭证或 checksum。
# 设计约束 08：任何 success/control claim 都必须阻断 ready intake。
# 设计约束 09：summary 是 Robot/mobile 唯一建议消费面，不含 raw ack packet。
# 设计约束 10：CLI dependency-free，不访问 ROS graph、真实硬件、云或手机。
# 设计约束 11：blocked artifact 仍返回 exit 0，方便 Docker-only sprint 留痕。
# 设计约束 12：本文件不新增硬件参数，因此不读取 vendor 细节。


def _utc_now() -> str:
    # UTC 让不同 PC/Docker 主机产物能按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个消费层重复 false flags，避免下游读取局部对象时误启动作。
    return {
        "source": "software_proof",
        "status": "not_proven",
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖所有嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any) -> str:
    # 复用既有 material pack 脱敏逻辑，保持 PC evidence 家族一致。
    return material_pack._safe_text(value)


def _safe_ref(value: Any) -> str:
    # evidence_ref 统一走既有短文本脱敏，避免路径或 raw id 泄漏。
    return material_pack._safe_ref(str(value if value is not None else ""))


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串 JSON 不当可信嵌套对象。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot alias 字段位置不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都走 fail-closed，不构造 ready intake。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
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
    # 递归白名单 key 覆盖 artifact/summary/Robot alias，但不采信 raw payload。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_owner_ack_intake",
        "field_evidence_real_material_owner_ack_intake_summary",
        "field_evidence_real_material_owner_ack_packet",
        "field_evidence_real_material_owner_ack_packet_summary",
        "field_evidence_real_material_followup_escalation_status",
        "field_evidence_real_material_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
        "diagnostics",
        "latest_status",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中 followup escalation 时才作为可信 source。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # ack 可以是有 schema 的 packet，也可以是 owner-safe 表单字段。
    for candidate in _candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in ACK_SCHEMAS and (_ack_state(candidate) != "missing" or _ack_ref(candidate)):
            return candidate
    return payload


def _source_boundary(source: dict[str, Any]) -> str:
    # 兼容 evidence_boundary / boundary 两种既有字段。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()


def _source_schema(source: dict[str, Any]) -> str:
    # schema 单独抽取，便于 blocked reason 可读。
    return _safe_text(source.get("schema", "")).strip()


def _source_status(source: dict[str, Any]) -> str:
    # followup_status 是业务映射核心，status 只作兜底解释。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("field_evidence_real_material_followup_escalation_status"),
            source.get("followup_status"),
            safe_copy.get("field_evidence_real_material_followup_escalation_status"),
            safe_copy.get("followup_status"),
            source.get("status"),
            default="",
        )
    ).strip()


def _source_ref(source: dict[str, Any]) -> str:
    # evidence_ref 是 followup 到 owner ack intake 的唯一串联主键。
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(_first_text(source.get("safe_evidence_ref"), source.get("evidence_ref"), safe_copy.get("safe_evidence_ref"), safe_copy.get("evidence_ref"), default=""))


def _requested_ref(value: str, source_ref: str) -> tuple[str, str]:
    # CLI evidence_ref 允许为空；非空时必须短文本且不能路径化。
    ref = str(value or source_ref or DEFAULT_EVIDENCE_REF).strip()
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    return _safe_ref(ref), ""


def _same_ref_required(payload: dict[str, Any]) -> Any:
    # 字符串 true 不接受，避免弱 typing 绕过同证据号要求。
    safe_copy = _dict(payload, "safe_copy")
    return payload.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))


def _source_software_not_proven(source: dict[str, Any]) -> bool:
    # 五个边界字段必须同时满足，不能只靠 schema 判断安全。
    safe_copy = _dict(source, "safe_copy")
    encoded = _encoded(source)
    source_text = _first_text(source.get("source"), safe_copy.get("source"), default="")
    return (
        source_text == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control", safe_copy.get("safe_to_control")) is False
        and source.get("delivery_success", safe_copy.get("delivery_success")) is False
        and source.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled")) is False
    )


def _has_unsafe_copy(value: Any) -> bool:
    # 输入里若夹带凭证、raw artifact 或 success claim，就不能生成 ready intake。
    encoded = _encoded(value)
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _ack_ref(ack: dict[str, Any]) -> str:
    # ack evidence_ref 也必须同一 safe id，不接受 owner 自造新 ref。
    return _safe_ref(_first_text(ack.get("safe_evidence_ref"), ack.get("evidence_ref"), default=""))


def _ack_schema(ack: dict[str, Any]) -> str:
    # 空 schema 代表安全表单输入；非空必须在白名单内。
    return _safe_text(ack.get("schema", "")).strip()


def _ack_state(ack: dict[str, Any]) -> str:
    # 只接受显式 acknowledged；普通说明文字不当 ACK。
    for key in (
        "owner_acknowledgement_state",
        "owner_acknowledgment_state",
        "acknowledgement_state",
        "acknowledgment_state",
        "ack_status",
        "status",
    ):
        value = str(ack.get(key, "")).strip().lower()
        if value in ACK_TRUE_VALUES:
            return "acknowledged"
        if value in ACK_FALSE_VALUES:
            return "missing"
    for key in ("owner_ack", "ack", "acknowledged", "accepted", "received", "confirmed"):
        value = ack.get(key)
        if value is True:
            return "acknowledged"
        if isinstance(value, str) and value.strip().lower() in ACK_TRUE_VALUES:
            return "acknowledged"
    return "missing"


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 输出只保留短文本类别，不搬运 raw packet。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("category"), item.get("material"), item.get("name"), item.get("item"))
            else:
                text = str(item if item is not None else "")
            safe = _safe_text(text).strip()
            if safe:
                items.append(safe)
        return list(dict.fromkeys(items))
    if isinstance(value, dict):
        return [_safe_text(key).strip() for key, enabled in value.items() if enabled and _safe_text(key).strip()][:limit]
    if value in (None, ""):
        return []
    text = _safe_text(value).strip()
    return [text] if text else []


def _ack_categories(ack: dict[str, Any], status: str) -> dict[str, list[str]]:
    # 四类材料状态让后续 reviewer 知道该补什么，但不表示真实验收。
    accepted = _safe_list(ack.get("accepted_materials") or ack.get("accepted_evidence") or ack.get("received_materials"))
    missing = _safe_list(ack.get("missing_materials") or ack.get("missing_evidence"))
    rejected = _safe_list(ack.get("rejected_materials") or ack.get("rejected_evidence"))
    blocked = _safe_list(ack.get("blocked_materials") or ack.get("blocked_evidence") or ack.get("blocked_next_evidence"))
    if status == READY_STATUS and not any((accepted, missing, rejected, blocked)):
        missing = list(REQUIRED_CATEGORIES)
    if status != READY_STATUS and not missing and not rejected and not blocked:
        blocked = ["owner_acknowledgement_not_ready_for_material_classification"]
    return {"accepted": accepted, "missing": missing, "rejected": rejected, "blocked": blocked}


def _status_for_inputs(
    *,
    source_load_issue: str,
    ack_load_issue: str,
    source: dict[str, Any],
    ack: dict[str, Any],
    source_ref: str,
    ack_ref: str,
    requested_ref: str,
    ref_error: str,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，坏输入不会落入 ready intake。
    if ref_error:
        return MISMATCH_STATUS, [ref_error]
    if source_load_issue:
        return UNSUPPORTED_STATUS, [source_load_issue]
    if _has_unsafe_copy(source):
        return REJECTED_STATUS, ["unsafe_or_success_control_claim_in_followup_source"]
    if _source_schema(source) not in SOURCE_SCHEMAS or _source_boundary(source) not in SOURCE_BOUNDARIES:
        return UNSUPPORTED_STATUS, ["unsupported_followup_schema_or_boundary"]
    if not _source_software_not_proven(source):
        return UNSUPPORTED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if _same_ref_required(source) is not True:
        return MISMATCH_STATUS, ["source_same_evidence_ref_required_not_true"]
    if not source_ref or requested_ref != source_ref:
        return MISMATCH_STATUS, [f"requested_ref:{requested_ref}!={source_ref or 'missing'}"]
    if _source_status(source) not in SOURCE_READY_STATUSES:
        return UNSUPPORTED_STATUS, [f"source_followup_status:{_source_status(source) or 'missing'}"]
    if ack_load_issue:
        return MISSING_ACK_STATUS, [ack_load_issue]
    if _has_unsafe_copy(ack):
        return REJECTED_STATUS, ["unsafe_or_success_control_claim_in_owner_ack_packet"]
    if _ack_schema(ack) not in ACK_SCHEMAS:
        return UNSUPPORTED_STATUS, ["unsupported_owner_ack_schema"]
    if _same_ref_required(ack) is not True:
        return MISMATCH_STATUS, ["ack_same_evidence_ref_required_not_true"]
    if not ack_ref or requested_ref != ack_ref:
        return MISMATCH_STATUS, [f"ack_ref:{ack_ref or 'missing'}!={requested_ref}"]
    if _ack_state(ack) != "acknowledged":
        return MISSING_ACK_STATUS, ["owner_acknowledgement_missing_or_pending"]
    return READY_STATUS, ["owner_acknowledgement_received_but_real_materials_remain_not_proven"]


def _owner_ack_summary(ack: dict[str, Any], ack_ref: str, status: str) -> dict[str, Any]:
    # ack summary 只复制安全 owner 元数据和分类，不包含 raw packet 文案。
    return {
        **_safe_flags(),
        "schema": _ack_schema(ack) or "owner_safe_ack_form",
        "owner_acknowledgement_state": _ack_state(ack),
        "acknowledged_owner": _safe_text(_first_text(ack.get("owner_id"), ack.get("owner"), ack.get("ack_owner"), default="field-owner")).strip(),
        "acknowledged_at": _safe_text(_first_text(ack.get("acknowledged_at"), ack.get("received_at"), ack.get("reviewed_at"), default="not_provided")).strip(),
        "safe_evidence_ref": ack_ref,
        "same_evidence_ref_required": _same_ref_required(ack) if ack else True,
        "material_categories": _ack_categories(ack, status),
        "safe_note": _safe_text(_first_text(ack.get("safe_note"), ack.get("note"), default="owner ack intake keeps all route/elevator outcomes not_proven")).strip(),
    }


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    # source summary 只保留 followup gate 的合同字段，避免完整 source 复制。
    return {
        **_safe_flags(),
        "schema": _source_schema(source),
        "evidence_boundary": _source_boundary(source),
        "followup_status": _source_status(source),
        "safe_evidence_ref": _source_ref(source),
        "same_evidence_ref_required": _same_ref_required(source) if source else True,
        "source_is_software_proof_not_proven": _source_software_not_proven(source) if source else False,
    }


def _owner_next_steps(categories: dict[str, list[str]], status: str) -> list[str]:
    # next steps 只描述人工补材料动作，不暗示机器人可以执行。
    if status == READY_STATUS:
        steps = ["review_owner_acknowledgement_categories_before_material_review"]
        if categories["missing"]:
            steps.append("collect_missing_real_materials_under_same_safe_evidence_ref")
        if categories["rejected"] or categories["blocked"]:
            steps.append("repair_rejected_or_blocked_owner_material_categories")
        return steps
    if status == MISSING_ACK_STATUS:
        return ["provide_owner_safe_ack_packet_before_material_review"]
    if status == MISMATCH_STATUS:
        return ["repair_same_evidence_ref_alignment_before_owner_ack_intake"]
    return ["remove_unsafe_or_unsupported_owner_ack_copy_and_rerun_gate"]


def _safe_copy(status: str, reasons: list[str], evidence_ref: str, source_view: dict[str, Any], owner_ack: dict[str, Any], next_steps: list[str]) -> dict[str, Any]:
    # safe_copy 是唯一复制面，保持短字段和明确 false flags。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        **_safe_flags(),
        "capability": CAPABILITY,
        "owner_ack_intake_status": status,
        "field_evidence_real_material_owner_ack_intake_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_followup": source_view,
        "owner_acknowledgement": owner_ack,
        "owner_next_steps": next_steps,
        "blocked_reason": ";".join(reasons),
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
    }


def _summary_payload(
    status: str,
    reasons: list[str],
    evidence_ref: str,
    source_view: dict[str, Any],
    owner_ack: dict[str, Any],
    next_steps: list[str],
    safe_copy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    # summary 镜像 artifact 的稳定消费字段，供 Robot/mobile 只读展示。
    return {
        "schema": SUMMARY_SCHEMA,
        "robot_diagnostics_schema": ROBOT_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "owner_ack_intake_status": status,
        "field_evidence_real_material_owner_ack_intake_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_followup": source_view,
        "owner_acknowledgement": owner_ack,
        "material_categories": owner_ack["material_categories"],
        "owner_next_steps": next_steps,
        "blocked_reason": ";".join(reasons),
        "review_refs": {"pr5_thread_id": followup.PR5_REVIEW_THREAD_ID},
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "boundary_note": BOUNDARY_NOTE,
    }


def build_field_evidence_real_material_owner_ack_intake(
    followup_json: str,
    owner_ack_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 followup safe source 与 owner ack packet，生成 ack intake artifact。"""
    source_payload, source_issue = _load_json(followup_json, "followup_json")
    ack_payload, ack_issue = _load_json(owner_ack_json, "owner_ack_json")
    source = _find_source(source_payload) if source_payload else {}
    ack = _find_ack(ack_payload) if ack_payload else {}
    source_ref = _source_ref(source) if source else ""
    requested_ref, ref_error = _requested_ref(evidence_ref, source_ref)
    ack_ref = _ack_ref(ack) if ack else ""
    status, reasons = _status_for_inputs(
        source_load_issue=source_issue,
        ack_load_issue=ack_issue,
        source=source,
        ack=ack,
        source_ref=source_ref,
        ack_ref=ack_ref,
        requested_ref=requested_ref,
        ref_error=ref_error,
    )
    generated_at = _utc_now()
    source_view = _source_summary(source)
    owner_ack = _owner_ack_summary(ack, ack_ref, status)
    next_steps = _owner_next_steps(owner_ack["material_categories"], status)
    safe_copy = _safe_copy(status, reasons, requested_ref, source_view, owner_ack, next_steps)
    summary = _summary_payload(status, reasons, requested_ref, source_view, owner_ack, next_steps, safe_copy, generated_at)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "owner_ack_intake_status": status,
        "field_evidence_real_material_owner_ack_intake_status": status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_followup": source_view,
        "owner_acknowledgement": owner_ack,
        "material_categories": owner_ack["material_categories"],
        "owner_next_steps": next_steps,
        "blocked_reason": ";".join(reasons),
        "review_refs": {"pr5_thread_id": followup.PR5_REVIEW_THREAD_ID},
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "field_evidence_real_material_owner_ack_intake_summary": summary,
        "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "non_access_scope": [
            "raw_field_materials",
            "real route/elevator runtime",
            "real delivery result",
            "real phone browser runtime",
            "robot control channels",
            "hardware serial or transport details",
            "host filesystem locations",
            "credential_or_database_queue_connection_material",
        ],
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary):
        # 最后一层防线：脱敏后仍不安全时保留 false flags 并切到 rejected。
        for output in (artifact, summary):
            output["owner_ack_intake_status"] = REJECTED_STATUS
            output["field_evidence_real_material_owner_ack_intake_status"] = REJECTED_STATUS
            output["blocked_reason"] = "unsafe_copy_after_sanitization"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径只用于落盘；payload 自身不回写绝对路径。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只做本地 JSON gate，可在 Docker-only 主机重复运行。
    parser = argparse.ArgumentParser(
        description=(
            "Generate field_evidence_real_material_owner_ack_intake software_proof gate; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--followup-json", required=True, help="followup escalation artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--owner-ack-json", required=True, help="owner-safe acknowledgement packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for owner ack intake")
    parser.add_argument("--output", default="", help="optional owner ack intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional owner ack intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print owner ack intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_owner_ack_intake(args.followup_json, args.owner_ack_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_owner_ack_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_real_material_owner_ack_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"owner_ack_intake_status: {artifact['owner_ack_intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
