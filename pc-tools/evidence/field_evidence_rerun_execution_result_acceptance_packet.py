#!/usr/bin/env python3
"""生成 field_evidence_rerun_execution_result_acceptance_packet 的 PC gate。

该 gate 接在 `field_evidence_rerun_execution_result_review_handoff` 后面，
只读取 handoff 的 safe summary，再读取 field owner 提交的脱敏 acceptance
packet。它核对 task record、Nav2/fixed-route runtime、route completion
signal、elevator evidence、dropoff/cancel、delivery result、true phone/browser
和 diagnostics/mobile safe summary 是否使用同一 safe evidence_ref；它不读取
真实材料正文、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、
真实电梯、外部云、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_review_handoff as handoff


PACKET_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1"
PACKET_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1"
SCHEMA_VERSION = 1
PACKET_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate"

SOURCE_SCHEMAS = {
    handoff.HANDOFF_SCHEMA,
    handoff.HANDOFF_SUMMARY_SCHEMA,
}
SOURCE_BOUNDARY = handoff.HANDOFF_BOUNDARY
READY_HANDOFF_STATUS = "ready_for_field_evidence_rerun_execution_result_review_owner_handoff_not_proven"

ACCEPTANCE_PACKET_SCHEMAS = {
    "trashbot.field_evidence_rerun_execution_result_acceptance_packet_input.v1",
    "trashbot.field_evidence_rerun_execution_result_acceptance_packet_materials.v1",
    "trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1",
}

REQUIRED_MATERIALS = (
    "task_record",
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "elevator_evidence",
    "dropoff_cancel_completion",
    "delivery_result",
    "true_phone_browser_evidence",
    "diagnostics_mobile_safe_summary",
)

ALLOWED_VERDICTS = (
    "ready_for_field_owner_acceptance_review_not_proven",
    "needs_material_backfill",
    "blocked_evidence_ref_mismatch",
    "blocked_unsafe_material",
    "rejected_success_claim",
    "blocked_missing_acceptance_packet",
)

NOT_PROVEN = handoff.NOT_PROVEN

BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_packet; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate; "
    "same_evidence_ref; required_materials; task record; Nav2; fixed-route; "
    "route completion signal; elevator evidence; dropoff; cancel; delivery result; "
    "true phone/browser; source=software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false"
)

# 设计约束 01：本 gate 只接收上一轮 review handoff 的 safe artifact/summary。
# 设计约束 02：acceptance packet 是现场 owner 的脱敏材料索引，不是材料正文。
# 设计约束 03：required_materials 是固定集合，输入不能裁剪必需现场证据。
# 设计约束 04：same evidence_ref 是现场复账主键，缺失或不一致必须阻断。
# 设计约束 05：ready verdict 只表示可进入 field owner acceptance review。
# 设计约束 06：ready verdict 仍然 not_proven，不能变成 delivery result。
# 设计约束 07：delivery_success、primary_actions_enabled、safe_to_control 永远 false。
# 设计约束 08：任何 success/control 文案都必须 rejected_success_claim。
# 设计约束 09：raw path、credential、ROS topic、serial/UART/WAVE ROVER 必须阻断。
# 设计约束 10：summary 只输出白名单字段，供 Robot/mobile 后续 safe alias 使用。
# 设计约束 11：blocked 也返回 exit code 0，便于 CI 和 sprint 留档落盘。
# 设计约束 12：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 13：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 14：Nav2/fixed-route 只作为材料类别名，不读取 runtime log。
# 设计约束 15：true phone/browser 只作为材料类别名，不证明真实手机已通过。
# 设计约束 16：dropoff/cancel 只作为 completion 材料类别，不声明完成。
# 设计约束 17：elevator evidence 只作为材料类别，不声明真实电梯通过。
# 设计约束 18：Robot/mobile safe summary 只作为材料类别，不读取 raw diagnostics。
# 设计约束 19：wrapper/nested JSON 只递归白名单 key，避免采信任意 payload。
# 设计约束 20：所有技术注释保持中文，解释 fail-closed 原因。


def _utc_now() -> str:
    # UTC 时间让多台 PC/Docker 主机生成的 artifact 可排序。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成明确 blocked verdict。
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


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 嵌套字段只接受 object；字符串化 JSON 不进入信任边界。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 的字段位置不同，取首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 只允许扁平短字符串清单进入下游 summary。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                name = _first_text(item.get("material"), item.get("name"), item.get("id"), item.get("type"), default="")
                if name:
                    items.append(handoff._safe_text(name))
            elif isinstance(item, (str, int, float, bool)):
                items.append(handoff._safe_text(item))
        return [item for item in items if item]
    if value in (None, ""):
        return []
    if isinstance(value, (str, int, float, bool)):
        return [handoff._safe_text(value)]
    return []


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw material payload 混入 source。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_review_handoff",
        "field_evidence_rerun_execution_result_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary",
        "review_handoff",
        "review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_handoff_source(payload: dict[str, Any]) -> dict[str, Any]:
    # summary 优先，因为它是 Robot/mobile 预计消费的 canonical safe 面。
    candidates = _source_candidates(payload)
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == handoff.HANDOFF_SUMMARY_SCHEMA:
            return candidate
    for candidate in candidates:
        if str(candidate.get("schema", "")).strip() == handoff.HANDOFF_SCHEMA:
            return candidate
    return payload


def _packet_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # acceptance material packet 也只递归白名单字段，避免复制完整现场材料。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_packet",
        "field_evidence_rerun_execution_result_acceptance_packet_input",
        "field_evidence_rerun_execution_result_acceptance_packet_materials",
        "acceptance_packet",
        "acceptance_materials",
        "materials_packet",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_packet_candidates(value))
    return candidates


def _find_acceptance_packet(payload: dict[str, Any]) -> dict[str, Any]:
    # 有 schema 时优先命中 schema；无 schema 的简单 packet 也可被顶层消费。
    for candidate in _packet_candidates(payload):
        if str(candidate.get("schema", "")).strip() in ACCEPTANCE_PACKET_SCHEMAS:
            return candidate
    return payload


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 必须同时匹配，防止绕过 review handoff。
    schema = handoff._safe_text(source.get("schema", "")).strip()
    boundary = handoff._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可来自顶层、safe_copy、Robot 或 mobile 摘要。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return handoff._safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        )
    )


def _source_status(source: dict[str, Any]) -> str:
    # handoff_status 是本 gate 的前置状态主键。
    safe_copy = _dict(source, "safe_copy")
    return handoff._safe_text(_first_text(source.get("handoff_status"), source.get("status"), safe_copy.get("handoff_status"), safe_copy.get("status"), default="")).strip()


def _source_flags_ok(source: dict[str, Any]) -> bool:
    # 上游必须显式保留三类 fail-closed flags。
    return (
        source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_is_safe(source: dict[str, Any]) -> bool:
    # source=software_proof 和 not_proven 是跨 gate 保守边界。
    encoded = handoff._encoded(source)
    return source.get("source") == "software_proof" and "not_proven" in encoded and source.get("same_evidence_ref_required", True) is True


def _packet_ref(packet: dict[str, Any]) -> str:
    # packet 的 evidence_ref 必须和 handoff 同一 safe ref。
    safe_copy = _dict(packet, "safe_copy")
    return handoff._safe_ref(
        _first_text(
            packet.get("safe_evidence_ref"),
            packet.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _material_names(packet: dict[str, Any], key: str) -> list[str]:
    # accepted/missing/rejected/blocked 允许 list[str] 或 list[object] 简写。
    safe_copy = _dict(packet, "safe_copy")
    return _safe_list(packet.get(key), limit=len(REQUIRED_MATERIALS) * 2) or _safe_list(safe_copy.get(key), limit=len(REQUIRED_MATERIALS) * 2)


def _material_evidence_refs(packet: dict[str, Any]) -> dict[str, str]:
    # material_refs 可选；若提供，每项也必须对齐同一 evidence_ref。
    raw = packet.get("material_evidence_refs") or _dict(packet, "safe_copy").get("material_evidence_refs")
    refs: dict[str, str] = {}
    if isinstance(raw, dict):
        for name in REQUIRED_MATERIALS:
            refs[name] = handoff._safe_ref(raw.get(name, ""))
    materials = packet.get("materials")
    if isinstance(materials, dict):
        for name in REQUIRED_MATERIALS:
            item = materials.get(name)
            if isinstance(item, dict) and item.get("evidence_ref") is not None:
                refs[name] = handoff._safe_ref(item.get("evidence_ref"))
    return refs


def _accepted_materials(packet: dict[str, Any]) -> list[str]:
    # accepted_materials 可由显式清单或 materials[material].status 推导。
    accepted = _material_names(packet, "accepted_materials")
    materials = packet.get("materials")
    if isinstance(materials, dict):
        for name in REQUIRED_MATERIALS:
            item = materials.get(name)
            if isinstance(item, dict) and handoff._safe_text(item.get("status", "")).strip() in {"accepted", "provided", "received", "ready"}:
                accepted.append(name)
    return sorted({item for item in accepted if item in REQUIRED_MATERIALS})


def _missing_materials(packet: dict[str, Any], accepted: list[str]) -> list[str]:
    # 缺口优先取 packet 显式字段，再补算未 accepted 的 required material。
    missing = [item for item in _material_names(packet, "missing_materials") if item in REQUIRED_MATERIALS]
    for item in REQUIRED_MATERIALS:
        if item not in accepted and item not in missing:
            missing.append(item)
    return missing


def _rejected_materials(packet: dict[str, Any]) -> list[str]:
    # rejected/blocked 都进入人工修正路径。
    rejected = [item for item in _material_names(packet, "rejected_materials") if item in REQUIRED_MATERIALS]
    blocked = [item for item in _material_names(packet, "blocked_materials") if item in REQUIRED_MATERIALS]
    return sorted(set(rejected + blocked))


def _packet_same_ref_status(packet: dict[str, Any], source_ref: str, accepted: list[str]) -> tuple[str, list[str]]:
    # packet 顶层和每个 material ref 都必须和 source_ref 对齐。
    packet_ref = _packet_ref(packet)
    if packet.get("same_evidence_ref_required", True) is not True:
        return "blocked", ["same_evidence_ref_required_not_true"]
    if not source_ref or not packet_ref:
        return "blocked", ["safe_evidence_ref_missing"]
    if packet_ref != source_ref:
        return "blocked", [f"packet_ref:{packet_ref}!={source_ref}"]
    mismatched: list[str] = []
    refs = _material_evidence_refs(packet)
    for name in accepted:
        ref = refs.get(name)
        if ref and ref != source_ref:
            mismatched.append(name)
    if mismatched:
        return "blocked", [f"material_ref_mismatch:{','.join(mismatched)}"]
    return "matched", []


def _unsafe(packet: dict[str, Any], source: dict[str, Any]) -> bool:
    # 只扫描会进入摘要的字段，避免 raw material 正文被带出。
    probe = {
        "source": {
            "status_reasons": source.get("status_reasons"),
            "owner_handoff": source.get("owner_handoff"),
            "safe_copy": source.get("safe_copy"),
        },
        "packet": {
            "accepted_materials": packet.get("accepted_materials"),
            "missing_materials": packet.get("missing_materials"),
            "rejected_materials": packet.get("rejected_materials"),
            "blocked_materials": packet.get("blocked_materials"),
            "owner_next_steps": packet.get("owner_next_steps"),
            "material_evidence_refs": packet.get("material_evidence_refs"),
            "safe_copy": packet.get("safe_copy"),
        },
    }
    return handoff._has_forbidden_copy(probe)


def _success_claim(packet: dict[str, Any], source: dict[str, Any]) -> bool:
    # 布尔 claim 和自由文本 claim 都不能进入 acceptance readiness。
    if (
        packet.get("safe_to_control") is True
        or packet.get("delivery_success") is True
        or packet.get("primary_actions_enabled") is True
        or source.get("safe_to_control") is True
        or source.get("delivery_success") is True
        or source.get("primary_actions_enabled") is True
    ):
        return True
    probe = {
        "source_flags": {
            "safe_to_control": source.get("safe_to_control"),
            "delivery_success": source.get("delivery_success"),
            "primary_actions_enabled": source.get("primary_actions_enabled"),
        },
        "packet": {
            "safe_to_control": packet.get("safe_to_control"),
            "delivery_success": packet.get("delivery_success"),
            "primary_actions_enabled": packet.get("primary_actions_enabled"),
            "accepted_materials": packet.get("accepted_materials"),
            "owner_next_steps": packet.get("owner_next_steps"),
            "safe_copy": packet.get("safe_copy"),
        },
    }
    return handoff._has_success_claim(probe)


def _verdict(
    source_load_issue: str,
    packet_load_issue: str,
    source: dict[str, Any],
    source_status: str,
    same_ref_status: str,
    ref_reasons: list[str],
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免 bad packet 落入 ready。
    if success_claim:
        return "rejected_success_claim", ["success_or_control_claim_detected"]
    if unsafe:
        return "blocked_unsafe_material", ["unsafe_material_copy_detected"]
    if source_load_issue or not _schema_supported(source):
        return "blocked_missing_acceptance_packet", [source_load_issue or "unsupported_review_handoff_schema_or_boundary"]
    if not _source_is_safe(source) or not _source_flags_ok(source):
        return "blocked_unsafe_material", ["source_not_software_proof_or_flags_not_false"]
    if source_status != READY_HANDOFF_STATUS:
        return "needs_material_backfill", [f"source_handoff_not_ready:{source_status or 'missing'}"]
    if packet_load_issue:
        return "blocked_missing_acceptance_packet", [packet_load_issue]
    if same_ref_status != "matched":
        return "blocked_evidence_ref_mismatch", ref_reasons
    if rejected:
        return "needs_material_backfill", ["rejected_materials:" + ",".join(rejected)]
    if missing:
        return "needs_material_backfill", ["missing_materials:" + ",".join(missing)]
    if set(accepted) >= set(REQUIRED_MATERIALS):
        return "ready_for_field_owner_acceptance_review_not_proven", ["all_required_materials_indexed_same_evidence_ref_not_proven"]
    return "needs_material_backfill", ["required_materials_incomplete"]


def _next_required_evidence(verdict: str, evidence_ref: str, missing: list[str], rejected: list[str]) -> list[str]:
    # 下一步只列补证动作，不写现场通过或成功措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict == "ready_for_field_owner_acceptance_review_not_proven":
        return [f"Field owner reviews acceptance packet for evidence_ref={ref} without changing not_proven boundary."]
    if verdict == "blocked_evidence_ref_mismatch":
        return [f"Regenerate task record, Nav2/fixed-route log, route completion signal, elevator evidence, dropoff/cancel, delivery result, true phone/browser, and diagnostics/mobile summary with one evidence_ref={ref}."]
    if verdict == "blocked_unsafe_material":
        return ["Regenerate acceptance packet without raw paths, credentials, ROS topics, serial/UART detail, WAVE ROVER fields, checksums, raw artifacts, tracebacks, control claims, or success claims."]
    if verdict == "rejected_success_claim":
        return ["Remove delivery_success=true, primary_actions_enabled=true, safe_to_control=true, field-pass, HIL-pass, phone-pass, or delivery-success wording before rerun."]
    if verdict == "blocked_missing_acceptance_packet":
        return [f"Provide safe acceptance material packet for evidence_ref={ref}."]
    gaps = missing or rejected or list(REQUIRED_MATERIALS)
    return [f"Backfill required_materials for evidence_ref={ref}: {', '.join(gaps)}."]


def _owner_handoff(verdict: str, evidence_ref: str, missing: list[str], rejected: list[str]) -> dict[str, Any]:
    # owner handoff 是人工验收/补证责任，不授权 Robot/mobile 控制面。
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "action": "field_owner_acceptance_review" if verdict == "ready_for_field_owner_acceptance_review_not_proven" else "field_owner_material_backfill",
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "missing_materials": missing,
        "rejected_materials": rejected,
        "required_materials": list(REQUIRED_MATERIALS),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _safe_copy(
    verdict: str,
    evidence_ref: str,
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw task record、runtime log 或手机材料。
    return {
        "schema": f"{PACKET_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": verdict,
        "acceptance_verdict": verdict,
        "evidence_boundary": PACKET_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_materials": list(REQUIRED_MATERIALS),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "next_required_evidence": next_required,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_packet(
    review_handoff_json: str,
    acceptance_packet_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review handoff 与 safe material packet，生成验收 readiness artifact。"""
    source_payload, source_load_issue = _load_json(review_handoff_json, "review_handoff_json")
    packet_payload, packet_load_issue = _load_json(acceptance_packet_json, "acceptance_packet_json")
    source = _find_handoff_source(source_payload) if source_payload else {}
    packet = _find_acceptance_packet(packet_payload) if packet_payload else {}
    source_ref = _source_ref(source) if source else ""
    requested_ref = handoff._safe_ref(evidence_ref)
    evidence_ref_out = requested_ref or source_ref or _packet_ref(packet)
    source_status = _source_status(source) if source else ""
    accepted = _accepted_materials(packet) if packet else []
    missing = _missing_materials(packet, accepted) if packet else list(REQUIRED_MATERIALS)
    rejected = _rejected_materials(packet) if packet else []
    same_ref_status, ref_reasons = _packet_same_ref_status(packet, requested_ref or source_ref, accepted) if packet else ("blocked", ["acceptance_packet_missing"])
    unsafe = bool(source_payload or packet_payload) and _unsafe(packet, source)
    success_claim = bool(source_payload or packet_payload) and _success_claim(packet, source)
    verdict, reasons = _verdict(
        source_load_issue,
        packet_load_issue,
        source,
        source_status,
        same_ref_status,
        ref_reasons,
        accepted,
        missing,
        rejected,
        unsafe,
        success_claim,
    )
    if verdict in {"blocked_evidence_ref_mismatch", "blocked_missing_acceptance_packet"}:
        reasons = reasons or ref_reasons
    next_required = _next_required_evidence(verdict, evidence_ref_out, missing, rejected)
    owner_handoff = _owner_handoff(verdict, evidence_ref_out, missing, rejected)
    safe_copy = _safe_copy(verdict, evidence_ref_out, accepted, missing, rejected, next_required)
    acceptance_gap_summary = {
        "verdict": verdict,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "same_evidence_ref_status": same_ref_status,
        "status_reasons": reasons,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = {
        "schema": PACKET_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": verdict,
        "acceptance_verdict": verdict,
        "allowed_verdicts": list(ALLOWED_VERDICTS),
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "required_materials": list(REQUIRED_MATERIALS),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "acceptance_gap_summary": acceptance_gap_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": PACKET_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": PACKET_BOUNDARY,
        "boundary": PACKET_BOUNDARY,
        "status": verdict,
        "acceptance_verdict": verdict,
        "status_reasons": reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_review_handoff": {
            "load_issue": source_load_issue,
            "schema": handoff._safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": handoff._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "handoff_status": source_status,
            "safe_evidence_ref": source_ref,
        },
        "acceptance_packet_source": {
            "load_issue": packet_load_issue,
            "schema": handoff._safe_text(packet.get("schema", "")) if packet else "",
            "safe_evidence_ref": _packet_ref(packet) if packet else "",
        },
        "required_materials": list(REQUIRED_MATERIALS),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "acceptance_gap_summary": acceptance_gap_summary,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_packet_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_task_record",
            "raw_nav2_runtime_log",
            "raw_fixed_route_runtime_log",
            "raw_route_completion_signal",
            "raw_elevator_evidence",
            "raw_dropoff_cancel_completion",
            "raw_delivery_result",
            "raw_true_phone_browser_evidence",
            "raw_diagnostics",
            "ros_graph",
            "robot_action",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    return handoff._safe_value(artifact), handoff._safe_value(summary), 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，方便 PC、Docker 和 unittest 一致调用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution result acceptance packet artifact")
    parser.add_argument("--review-handoff-json", required=True, help="review handoff artifact, summary, Robot safe alias, or wrapper/nested JSON")
    parser.add_argument("--acceptance-packet-json", required=True, help="safe field-owner acceptance material packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this acceptance packet")
    parser.add_argument("--output", default="", help="optional acceptance packet artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance packet summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance packet artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_packet(
        args.review_handoff_json,
        args.acceptance_packet_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_packet: artifact_file:{handoff._safe_ref(args.output)}")
        if args.summary_output:
            print(f"field_evidence_rerun_execution_result_acceptance_packet_summary_file: {handoff._safe_ref(args.summary_output)}")
        print(f"acceptance_verdict: {artifact['acceptance_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
