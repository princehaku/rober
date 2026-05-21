#!/usr/bin/env python3
"""生成 field_evidence_material_resolution_intake PC gate。

该 dependency-light CLI 只消费上一轮 blocker escalation 的安全 artifact、
summary 或 Robot alias，以及 owner 提供的脱敏 resolution packet。输出固定
software_proof / not_proven，不证明现场路线、电梯、终态交付、真实手机或硬件通过。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_material_blocker_escalation_pack as blocker_pack
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_material_resolution_intake.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_material_resolution_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_field_evidence_material_resolution_intake_summary"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_material_resolution_intake"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_material_resolution_intake_gate"

# 只允许 blocker escalation pack 家族作为 source，避免直接消费 raw field materials。
SOURCE_SCHEMAS = {blocker_pack.SCHEMA, blocker_pack.SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {blocker_pack.EVIDENCE_BOUNDARY}

# owner packet 允许无 schema，方便现场 owner 先用脱敏 JSON 表单回传分类结论。
RESOLUTION_SCHEMAS = {
    "",
    "trashbot.field_evidence_material_resolution_packet.v1",
    "trashbot.field_evidence_material_resolution_packet_summary.v1",
}

DECISIONS = {"accepted", "missing", "rejected", "blocked"}
READY_STATUS = "field_evidence_material_resolution_intake_ready_not_proven"
MISSING_STATUS = "field_evidence_material_resolution_intake_missing_not_proven"
REJECTED_STATUS = "field_evidence_material_resolution_intake_rejected_not_proven"
BLOCKED_STATUS = "field_evidence_material_resolution_intake_blocked_not_proven"

DEFAULT_EVIDENCE_REF = "field-material-resolution-intake-2026-05-22T06-07Z"
BOUNDARY_NOTE = (
    "field_evidence_material_resolution_intake; "
    "software_proof_docker_field_evidence_material_resolution_intake_gate; "
    "source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; same_evidence_ref_required=true"
)

NOT_PROVEN_ITEMS = (
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_runtime",
    "real_terminal_delivery_or_dropoff_or_cancel_result",
    "real_public_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "real_phone_device_or_browser_acceptance",
    "real_hardware_or_hil_pass",
    "review_thread_or_owner_material_final_resolution",
)

FORBIDDEN_COPY = (
    "Authorization",
    "Bearer ",
    "access_key",
    "secret",
    "token",
    "password",
    "credential",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "db_url",
    "database_url",
    "queue_url",
    "signed_url",
    "ROS topic",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "sha256:",
    "md5:",
    "complete artifact",
    "raw artifact",
    "raw_fields",
    "raw_materials",
    "raw_log",
    "raw_body",
)

SUCCESS_WORDS = (
    "delivery success",
    "delivery_success=true",
    "primary_actions_enabled=true",
    "safe_to_control=true",
    "field pass",
    "hil pass",
    "control enabled",
    "actions enabled",
    "successfully completed",
)

# 设计约束 01：source 必须是上一轮 blocker escalation 的 safe surface。
# 设计约束 02：owner resolution packet 只表达材料分类，不表达真实验收通过。
# 设计约束 03：accepted/missing/rejected/blocked 是唯一决策枚举。
# 设计约束 04：同一 safe evidence_ref 是 source 与 owner packet 的唯一串联主键。
# 设计约束 05：缺 source 或 ref mismatch 均 blocked，缺 owner packet 记为 missing。
# 设计约束 06：unsafe owner material 进入 rejected，不尝试清洗成 accepted。
# 设计约束 07：任何 success/control claim 都阻断 ready 分支。
# 设计约束 08：summary 是 Robot/mobile 唯一建议消费面，不复制 raw packet。
# 设计约束 09：输出固定 false flags，不能由输入覆盖。
# 设计约束 10：本 gate 不访问 ROS graph、Nav2 runtime、硬件、云或手机。
# 设计约束 11：blocked/rejected artifact 仍 exit 0，便于 Docker-only 留证。
# 设计约束 12：代码注释保留中文，说明 fail-closed 的取舍原因。


def _utc_now() -> str:
    # UTC 让 Docker-only artifact 在跨时区 closeout 时可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每层重复 false flags，避免下游只读局部对象时误解为可控制。
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
    # 安全扫描使用稳定 JSON，覆盖嵌套 key 与 value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any) -> str:
    # 复用同族 material pack 的脱敏逻辑，保持 evidence gate 输出一致。
    return material_pack._safe_text(value).strip()


def _safe_ref(value: Any) -> str:
    # evidence_ref 禁止携带路径；既有 helper 会把路径降级成 basename。
    return material_pack._safe_ref(str(value if value is not None else "")).strip()


def _safe_value(value: Any) -> Any:
    # 输出落盘前做递归脱敏，blocked artifact 也不能携带敏感内容。
    return material_pack._safe_value(value)


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 必须是 object；字符串 JSON 不当可信 safe source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot alias 的字段位置不完全一致。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 24) -> list[str]:
    # 列表只保留短文本摘要，避免复制 owner packet 的完整材料正文。
    if isinstance(value, list):
        result: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("item"), item.get("material"), item.get("summary"), item.get("name"))
            else:
                text = str(item if item is not None else "")
            safe = _safe_text(text)
            if safe:
                result.append(safe)
        return list(dict.fromkeys(result))
    if isinstance(value, dict):
        return [_safe_text(key) for key, enabled in value.items() if enabled and _safe_text(key)][:limit]
    if value in (None, ""):
        return []
    text = _safe_text(value)
    return [text] if text else []


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 fail-closed 状态，不抛 traceback。
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
    # 只递归白名单 wrapper key，避免把任意 raw payload 当 safe summary。
    candidates = [payload]
    for key in (
        "field_evidence_material_resolution_intake",
        "field_evidence_material_resolution_intake_summary",
        "field_evidence_material_resolution_packet",
        "field_evidence_material_resolution_packet_summary",
        "field_evidence_material_blocker_escalation_pack",
        "field_evidence_material_blocker_escalation_pack_summary",
        "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary",
        "robot_diagnostics_field_evidence_material_resolution_intake_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "field_safe_copy",
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
    # source 只在 schema 命中 blocker escalation 时可信。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _find_resolution(payload: dict[str, Any]) -> dict[str, Any]:
    # owner packet 可为无 schema 表单，但必须有 ref 或 decision 才当候选。
    for candidate in _candidates(payload):
        schema = str(candidate.get("schema", "")).strip()
        if schema in RESOLUTION_SCHEMAS and (_resolution_ref(candidate) or _resolution_decision(candidate)):
            return candidate
    return payload


def _schema(payload: dict[str, Any]) -> str:
    # schema 单独抽取，便于 blocked reason 精准说明。
    return _safe_text(payload.get("schema", ""))


def _boundary(payload: dict[str, Any]) -> str:
    # evidence_boundary / boundary 都是同族 gate 的常见字段。
    return _safe_text(_first_text(payload.get("evidence_boundary"), payload.get("boundary"), default=""))


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可在顶层、safe_copy 或 field_safe_copy 中出现。
    safe_copy = _dict(source, "safe_copy")
    field_safe = _dict(source, "field_safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            field_safe.get("safe_evidence_ref"),
            field_safe.get("evidence_ref"),
            default="",
        )
    )


def _resolution_ref(packet: dict[str, Any]) -> str:
    # owner resolution 必须复用 source 的 safe evidence_ref。
    safe_copy = _dict(packet, "safe_copy")
    return _safe_ref(
        _first_text(
            packet.get("safe_evidence_ref"),
            packet.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _requested_ref(value: str, source_ref: str) -> str:
    # CLI evidence_ref 为空时沿用 source；仍必须经过 safe_ref。
    return _safe_ref(value or source_ref or DEFAULT_EVIDENCE_REF)


def _same_ref_required(payload: dict[str, Any]) -> Any:
    # 字符串 true 不接受，避免弱类型绕过同证据号要求。
    safe_copy = _dict(payload, "safe_copy")
    field_safe = _dict(payload, "field_safe_copy")
    return payload.get(
        "same_evidence_ref_required",
        safe_copy.get("same_evidence_ref_required", field_safe.get("same_evidence_ref_required", True)),
    )


def _software_not_proven(payload: dict[str, Any]) -> bool:
    # 五个边界字段同时满足，才允许进入后续材料分类。
    safe_copy = _dict(payload, "safe_copy")
    field_safe = _dict(payload, "field_safe_copy")
    encoded = _encoded(payload)
    source = _first_text(payload.get("source"), safe_copy.get("source"), field_safe.get("source"), default="")
    return (
        source == "software_proof"
        and "not_proven" in encoded
        and payload.get("delivery_success", safe_copy.get("delivery_success", field_safe.get("delivery_success"))) is False
        and payload.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled", field_safe.get("primary_actions_enabled"))) is False
        and payload.get("safe_to_control", safe_copy.get("safe_to_control", field_safe.get("safe_to_control"))) is False
    )


def _has_truthy_false_flags(value: Any) -> bool:
    # 三个 false-state flag 只要为 true 就必须 fail closed。
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if value.get(key) is True:
                return True
        return any(_has_truthy_false_flags(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_truthy_false_flags(item) for item in value)
    return False


def _has_unsafe_copy(value: Any) -> bool:
    # forbidden token、路径、成功文案、控制文案都不能进入 ready 输出。
    encoded = _encoded(value)
    lowered = encoded.lower()
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(word in lowered for word in SUCCESS_WORDS)
        or material_pack._has_forbidden_copy(value)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
        or _has_truthy_false_flags(value)
    )


def _resolution_schema(packet: dict[str, Any]) -> str:
    # 空 schema 表示 owner safe form，非空必须命中白名单。
    return _safe_text(packet.get("schema", ""))


def _resolution_decision(packet: dict[str, Any]) -> str:
    # owner packet 只能给四态决策，其他词不做“近似理解”。
    safe_copy = _dict(packet, "safe_copy")
    value = _first_text(
        packet.get("resolution_decision"),
        packet.get("decision"),
        packet.get("material_resolution_decision"),
        packet.get("status"),
        safe_copy.get("resolution_decision"),
        safe_copy.get("decision"),
        default="",
    ).lower()
    return value if value in DECISIONS else ""


def _resolution_note(packet: dict[str, Any], decision: str) -> str:
    # note 只作为短摘要，不能把 raw 材料正文转给下游。
    if packet and _has_unsafe_copy(packet):
        return "owner_resolution_packet_rejected_unsafe_copy_not_proven"
    text = _safe_text(
        _first_text(
            packet.get("safe_note"),
            packet.get("summary"),
            packet.get("owner_resolution_summary"),
            default=f"owner_material_resolution_decision_{decision or 'missing'}",
        )
    )
    return text[:240] if text else f"owner_material_resolution_decision_{decision or 'missing'}"


def _resolution_materials(packet: dict[str, Any], decision: str) -> dict[str, list[str]]:
    # 四类材料摘要保留在白名单结构内，供 Product/Robot/mobile 只读消费。
    accepted = _safe_list(packet.get("accepted_materials") or packet.get("accepted_resolution_materials"))
    missing = _safe_list(packet.get("missing_materials") or packet.get("missing_required_materials"))
    rejected = _safe_list(packet.get("rejected_materials") or packet.get("rejected_resolution_materials"))
    blocked = _safe_list(packet.get("blocked_materials") or packet.get("blocked_resolution_materials"))
    if decision == "accepted" and not accepted:
        missing = missing or ["owner_resolution_material_summary_required"]
    if decision == "missing" and not missing:
        missing = ["owner_resolution_packet_missing_required_materials"]
    if decision == "rejected" and not rejected:
        rejected = ["owner_resolution_packet_rejected_or_unsafe"]
    if decision == "blocked" and not blocked:
        blocked = ["owner_resolution_packet_blocked"]
    return {"accepted": accepted, "missing": missing, "rejected": rejected, "blocked": blocked}


def _source_summary(source: dict[str, Any]) -> dict[str, Any]:
    # source summary 只复制 blocker escalation 的合同字段，不复制完整 artifact。
    return {
        **_safe_flags(),
        "schema": _schema(source),
        "evidence_boundary": _boundary(source),
        "blocker_escalation_status": _safe_text(source.get("field_evidence_material_blocker_escalation_pack_status", "")),
        "safe_evidence_ref": _source_ref(source),
        "same_evidence_ref_required": _same_ref_required(source) if source else True,
        "source_is_software_proof_not_proven": _software_not_proven(source) if source else False,
    }


def _owner_resolution_summary(packet: dict[str, Any], decision: str, resolution_ref: str) -> dict[str, Any]:
    # owner summary 是下游可见面，禁止 raw packet 字段穿透。
    materials = _resolution_materials(packet, decision)
    return {
        **_safe_flags(),
        "schema": _resolution_schema(packet) or "owner_safe_resolution_form",
        "resolution_decision": decision or "missing",
        "safe_evidence_ref": resolution_ref,
        "same_evidence_ref_required": _same_ref_required(packet) if packet else True,
        "material_categories": materials,
        "safe_note": _resolution_note(packet, decision),
    }


def _status_for_inputs(
    *,
    source_issue: str,
    packet_issue: str,
    source: dict[str, Any],
    packet: dict[str, Any],
    source_ref: str,
    packet_ref: str,
    requested_ref: str,
    decision: str,
) -> tuple[str, str, list[str]]:
    # fail-closed 优先级固定：source/ref 问题 blocked，owner 缺料 missing，unsafe rejected。
    if source_issue:
        return "blocked", BLOCKED_STATUS, [source_issue]
    if _schema(source) not in SOURCE_SCHEMAS or _boundary(source) not in SOURCE_BOUNDARIES:
        return "blocked", BLOCKED_STATUS, ["unsupported_blocker_escalation_schema_or_boundary"]
    if _has_unsafe_copy(source):
        return "blocked", BLOCKED_STATUS, ["unsafe_or_success_control_claim_in_blocker_escalation_source"]
    if not _software_not_proven(source):
        return "blocked", BLOCKED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if _same_ref_required(source) is not True:
        return "blocked", BLOCKED_STATUS, ["source_same_evidence_ref_required_not_true"]
    if not source_ref or requested_ref != source_ref:
        return "blocked", BLOCKED_STATUS, [f"source_ref:{source_ref or 'missing'}!={requested_ref}"]
    if packet_issue:
        return "missing", MISSING_STATUS, [packet_issue]
    if _has_unsafe_copy(packet):
        return "rejected", REJECTED_STATUS, ["unsafe_or_success_control_claim_in_owner_resolution_packet"]
    if _resolution_schema(packet) not in RESOLUTION_SCHEMAS:
        return "blocked", BLOCKED_STATUS, ["unsupported_owner_resolution_schema"]
    if _same_ref_required(packet) is not True:
        return "blocked", BLOCKED_STATUS, ["owner_resolution_same_evidence_ref_required_not_true"]
    if not packet_ref or requested_ref != packet_ref:
        return "blocked", BLOCKED_STATUS, [f"owner_resolution_ref:{packet_ref or 'missing'}!={requested_ref}"]
    if decision not in DECISIONS:
        return "missing", MISSING_STATUS, ["owner_resolution_decision_missing_or_unsupported"]
    if decision == "accepted" and not _resolution_materials(packet, decision)["accepted"]:
        return "missing", MISSING_STATUS, ["accepted_resolution_material_summary_missing"]
    if decision == "rejected":
        return "rejected", REJECTED_STATUS, ["owner_resolution_packet_rejected_materials"]
    if decision == "blocked":
        return "blocked", BLOCKED_STATUS, ["owner_resolution_packet_blocked"]
    if decision == "missing":
        return "missing", MISSING_STATUS, ["owner_resolution_packet_missing_required_materials"]
    return "accepted", READY_STATUS, ["owner_resolution_packet_accepted_but_materials_remain_not_proven"]


def _next_required(decision: str, reasons: list[str], owner_resolution: dict[str, Any]) -> list[str]:
    # next_required 只表达人工补证动作，不能变成机器人运行命令。
    materials = owner_resolution["material_categories"]
    if decision == "accepted":
        return ["review_sanitized_owner_resolution_packet_before_product_closeout"]
    if decision == "missing":
        return materials["missing"] or ["provide_owner_safe_resolution_packet_under_same_evidence_ref"]
    if decision == "rejected":
        return materials["rejected"] or ["remove_unsafe_or_rejected_owner_resolution_copy_and_rerun_gate"]
    return materials["blocked"] or reasons or ["repair_blocker_escalation_source_or_same_evidence_ref_before_rerun"]


def _safe_copy(
    *,
    decision: str,
    status: str,
    reasons: list[str],
    evidence_ref: str,
    source_view: dict[str, Any],
    owner_resolution: dict[str, Any],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 的白名单消费面，不包含 raw artifact 或本机路径。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        **_safe_flags(),
        "capability": CAPABILITY,
        "resolution_intake_status": status,
        "field_evidence_material_resolution_intake_status": status,
        "decision": decision,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_blocker_escalation": source_view,
        "owner_resolution": owner_resolution,
        "next_required_evidence": next_required,
        "decision_reasons": reasons,
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
    }


def _summary_payload(
    *,
    decision: str,
    status: str,
    reasons: list[str],
    evidence_ref: str,
    source_view: dict[str, Any],
    owner_resolution: dict[str, Any],
    next_required: list[str],
    safe_copy: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    # summary 镜像 artifact 的稳定字段，供 Robot alias 与 mobile 只读展示。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "resolution_intake_status": status,
        "field_evidence_material_resolution_intake_status": status,
        "decision": decision,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_blocker_escalation": source_view,
        "owner_resolution": owner_resolution,
        "material_categories": owner_resolution["material_categories"],
        "next_required_evidence": next_required,
        "decision_reasons": reasons,
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "boundary_note": BOUNDARY_NOTE,
    }


def build_field_evidence_material_resolution_intake(
    blocker_escalation_json: str,
    owner_resolution_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 blocker escalation 与 owner resolution packet，生成 fail-closed intake。"""
    source_payload, source_issue = _load_json(blocker_escalation_json, "blocker_escalation_json")
    packet_payload, packet_issue = _load_json(owner_resolution_json, "owner_resolution_json")
    source = _find_source(source_payload) if source_payload else {}
    packet = _find_resolution(packet_payload) if packet_payload else {}
    source_ref = _source_ref(source) if source else ""
    requested_ref = _requested_ref(evidence_ref, source_ref)
    packet_ref = _resolution_ref(packet) if packet else ""
    packet_decision = _resolution_decision(packet) if packet else ""
    decision, status, reasons = _status_for_inputs(
        source_issue=source_issue,
        packet_issue=packet_issue,
        source=source,
        packet=packet,
        source_ref=source_ref,
        packet_ref=packet_ref,
        requested_ref=requested_ref,
        decision=packet_decision,
    )
    generated_at = _utc_now()
    source_view = _source_summary(source)
    owner_resolution = _owner_resolution_summary(packet, packet_decision or decision, packet_ref)
    next_required = _next_required(decision, reasons, owner_resolution)
    safe_copy = _safe_copy(
        decision=decision,
        status=status,
        reasons=reasons,
        evidence_ref=requested_ref,
        source_view=source_view,
        owner_resolution=owner_resolution,
        next_required=next_required,
    )
    summary = _summary_payload(
        decision=decision,
        status=status,
        reasons=reasons,
        evidence_ref=requested_ref,
        source_view=source_view,
        owner_resolution=owner_resolution,
        next_required=next_required,
        safe_copy=safe_copy,
        generated_at=generated_at,
    )
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **_safe_flags(),
        "capability": CAPABILITY,
        "resolution_intake_status": status,
        "field_evidence_material_resolution_intake_status": status,
        "decision": decision,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_blocker_escalation": source_view,
        "owner_resolution": owner_resolution,
        "material_categories": owner_resolution["material_categories"],
        "next_required_evidence": next_required,
        "decision_reasons": reasons,
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "safe_copy": safe_copy,
        "field_evidence_material_resolution_intake_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "non_access_scope": [
            "raw_field_materials",
            "real_route_elevator_runtime",
            "real_terminal_result_runtime",
            "real_cloud_or_phone_runtime",
            "robot_control_channels",
            "hardware_transport_runtime",
        ],
        "boundary_note": BOUNDARY_NOTE,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_unsafe_copy(artifact) or _has_unsafe_copy(summary):
        # 最后一层防线：若新增输出字段触碰敏感词，统一降级为 rejected。
        for output in (artifact, summary):
            output["decision"] = "rejected"
            output["resolution_intake_status"] = REJECTED_STATUS
            output["field_evidence_material_resolution_intake_status"] = REJECTED_STATUS
            output["decision_reasons"] = ["unsafe_copy_after_sanitization"]
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径只用于落盘，不写入 payload，避免本机路径泄漏。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只做本地 JSON gate；缺输入也输出 fail-closed artifact。
    parser = argparse.ArgumentParser(
        description=(
            "Generate field_evidence_material_resolution_intake software_proof gate; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--blocker-escalation-json", default="", help="blocker escalation artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--owner-resolution-json", default="", help="owner-safe resolution packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", default="", help="optional resolution intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional resolution intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout instead of status line")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_material_resolution_intake(
        args.blocker_escalation_json,
        args.owner_resolution_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(artifact["field_evidence_material_resolution_intake_status"])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
