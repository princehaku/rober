#!/usr/bin/env python3
"""生成 field evidence rerun execution result acceptance backfill review decision。

该 PC gate 接在 `field_evidence_rerun_execution_result_acceptance_backfill`
后面，只读取上一轮 artifact / summary / Robot diagnostics safe alias 或
wrapper/nested JSON。它把八类材料的 completeness、same evidence_ref alignment
和 safe metadata 转成人工复核决策；它不扫描材料目录，不读取真实 ROS/Nav2
runtime、硬件、真实电梯、外部云、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_backfill as backfill
import route_task_field_retest_material_pack as material_pack


# review decision 是 acceptance backfill 后的 PC 复核契约，不能复用上游 schema。
DECISION_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate"

# 只允许上一轮 acceptance backfill artifact / summary；wrapper 只能包住这些 schema。
SOURCE_SCHEMAS = {backfill.BACKFILL_SCHEMA, backfill.BACKFILL_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {backfill.BACKFILL_BOUNDARY}
READY_BACKFILL_STATUS = "ready_for_field_evidence_rerun_execution_result_acceptance_backfill_not_proven"

# 本 gate 仍然只证明 PC 侧复核决策，不证明现场、硬件、手机或云能力。
READY_DECISION = "ready_for_field_rerun_result_acceptance_review_handoff"
NEEDS_MORE_MATERIAL = "needs_more_material"
EVIDENCE_REF_MISMATCH = "evidence_ref_mismatch"
UNSAFE_REJECTED = "unsafe_rejected"
BLOCKED_MISSING_BACKFILL = "blocked_missing_backfill"
ALLOWED_REVIEW_DECISIONS = (
    READY_DECISION,
    NEEDS_MORE_MATERIAL,
    EVIDENCE_REF_MISMATCH,
    UNSAFE_REJECTED,
    BLOCKED_MISSING_BACKFILL,
)

REQUIRED_MATERIALS = backfill.REQUIRED_MATERIALS
NOT_PROVEN = backfill.NOT_PROVEN

# rg 围栏依赖这些 literal，人工复盘也能快速识别证据边界。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_backfill_review_decision; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_field_rerun_result_acceptance_review_handoff; "
    "needs_more_material; evidence_ref_mismatch; unsafe_rejected; "
    "blocked_missing_backfill; task record; Nav2/fixed-route runtime log; "
    "route completion signal; elevator door state; target floor confirmation; "
    "human assistance record; dropoff/cancel completion or delivery result; "
    "true phone/browser evidence"
)

# 设计约束 01：本 gate 只消费上一轮 acceptance backfill 的 safe artifact/summary。
# 设计约束 02：本 gate 不重新读取 material-dir，避免把 raw 现场材料引入下游。
# 设计约束 03：ready 分支只表示可进入 acceptance review handoff，不表示现场通过。
# 设计约束 04：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 05：source=software_proof 和 not_proven 是跨 gate 的硬边界。
# 设计约束 06：same evidence_ref 是 task/Nav2/elevator/mobile 材料复账主键。
# 设计约束 07：弱类型 same_evidence_ref_required 必须阻断，避免字符串 true 误通过。
# 设计约束 08：缺 backfill、坏 JSON、unsupported schema 都归入 blocked_missing_backfill。
# 设计约束 09：缺材料、rejected 材料或 completeness 未满都归入 needs_more_material。
# 设计约束 10：任何 raw path、secret、ROS topic、serial/UART/WAVE ROVER copy 都拒绝。
# 设计约束 11：任何 success/control claim 都拒绝，防止 Docker proof 被升级成现场证明。
# 设计约束 12：summary 是 Robot/mobile 只读 safe alias，不携带 raw artifact。
# 设计约束 13：wrapper/nested JSON 只递归固定 key，避免采信任意 payload。
# 设计约束 14：八类材料只是安全元数据概念，不证明真实材料已经合格。
# 设计约束 15：task record 只作为类别名，不读取真实 task record。
# 设计约束 16：Nav2/fixed-route runtime log 只作为类别名，不读取 runtime log。
# 设计约束 17：route completion signal 只作为类别名，不声明真实 route completion。
# 设计约束 18：elevator door/floor/human assistance 只作为类别名，不证明真实电梯。
# 设计约束 19：dropoff/cancel 或 delivery result 只作为类别名，不声明 delivery success。
# 设计约束 20：true phone/browser evidence 只作为类别名，不证明真实设备通过。
# 设计约束 21：blocked artifact 也返回 exit code 0，便于 CI 和 sprint 证据落盘。
# 设计约束 22：输出最终递归脱敏，防止新增字段绕过安全扫描。
# 设计约束 23：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 24：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 25：所有技术注释保持中文，解释 fail-closed 原因。


def _utc_now() -> str:
    # UTC 时间便于多台 PC/Docker 主机生成 artifact 后按时间线复盘。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常也要输出 blocked decision，避免 review gate 静默缺席。
    if not path:
        return {}, "acceptance_backfill_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "acceptance_backfill_json_missing"
    except json.JSONDecodeError:
        return {}, "acceptance_backfill_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "acceptance_backfill_json_read_error"
    if not isinstance(payload, dict):
        return {}, "acceptance_backfill_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串化 JSON 不作为可信输入。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot/mobile 摘要字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 输出只保留短字符串清单，避免复制完整上游 material_states。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = _first_text(item.get("name"), item.get("material"), item.get("id"), default="")
            else:
                text = _first_text(item, default="")
            if text:
                items.append(material_pack._safe_text(text))
        return items
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw material payload 混入 source。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision",
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        "field_evidence_rerun_execution_result_acceptance_backfill",
        "field_evidence_rerun_execution_result_acceptance_backfill_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary",
        "acceptance_backfill",
        "acceptance_backfill_summary",
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


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 missing/unsupported 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时白名单化，防止跨 gate artifact 被误复核。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可来自顶层、safe_copy、owner_handoff、Robot 或 mobile 面。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    owner_handoff = _dict(source, "owner_handoff")
    return material_pack._safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            owner_handoff.get("safe_evidence_ref"),
            owner_handoff.get("evidence_ref"),
            default="",
        )
    )


def _source_backfill_status(source: dict[str, Any]) -> str:
    # 只有 ready_not_proven 的 acceptance backfill 能进入 ready review decision。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("backfill_status"),
            source.get("status"),
            robot.get("backfill_status"),
            robot.get("status"),
            mobile.get("backfill_status"),
            mobile.get("status"),
            safe_copy.get("backfill_status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串不能通过；必须保持 JSON boolean true。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return source.get(
        "same_evidence_ref_required",
        robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
    )


def _source_is_safe(source: dict[str, Any]) -> bool:
    # source=software_proof、not_proven 和三类 false flag 是跨 gate 保守边界。
    encoded = material_pack._encoded(source)
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_lineage(source: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制上游已经安全化的短字段，不追 raw upstream artifact。
    lineage = {"source_acceptance_backfill_schema": material_pack._safe_text(source.get("schema", ""))}
    status = _source_backfill_status(source)
    if status:
        lineage["source_acceptance_backfill_status"] = status
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"backfill_{material_pack._safe_text(key)}"] = text
    return lineage


def _material_status(source: dict[str, Any]) -> dict[str, Any]:
    # 优先读取 top-level completeness，再兼容 safe_copy 中的只读摘要。
    safe_copy = _dict(source, "safe_copy")
    completeness = _dict(source, "material_completeness") or _dict(safe_copy, "material_completeness")
    gap_summary = _dict(source, "acceptance_backfill_gap_summary") or _dict(safe_copy, "acceptance_backfill_gap_summary")
    rejected_map = source.get("rejected_materials")
    if not isinstance(rejected_map, dict):
        rejected_map = gap_summary.get("rejected_materials") if isinstance(gap_summary.get("rejected_materials"), dict) else {}
    accepted = _safe_list(completeness.get("accepted_materials"))
    missing = _safe_list(completeness.get("missing_materials") or gap_summary.get("missing_materials"))
    rejected = _safe_list(completeness.get("rejected_materials") or sorted(rejected_map.keys()))
    return {
        "status": "accepted" if accepted and not missing and not rejected else ("missing" if missing else ("rejected" if rejected else "unknown")),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": int(completeness.get("accepted_count", len(accepted)) or 0),
        "required_count": int(completeness.get("required_count", len(REQUIRED_MATERIALS)) or 0),
        "is_complete": bool(completeness.get("is_complete", False)),
        "gap_count": int(gap_summary.get("gap_count", len(missing) + len(rejected)) or 0),
        "rejected_reasons": material_pack._safe_value(rejected_map),
    }


def _alignment_status(source: dict[str, Any]) -> dict[str, Any]:
    # same evidence_ref 对齐状态必须显式进入 review decision，不能只看材料数量。
    safe_copy = _dict(source, "safe_copy")
    alignment = _dict(source, "same_evidence_ref_alignment") or _dict(safe_copy, "same_evidence_ref_alignment")
    return {
        "required": True,
        "status": material_pack._safe_text(alignment.get("status", "missing")),
        "mismatched_materials": _safe_list(alignment.get("mismatched_materials")),
        "missing_evidence_ref_materials": _safe_list(alignment.get("missing_evidence_ref_materials")),
    }


def _has_true_control_flag(value: Any) -> bool:
    # JSON boolean 可能藏在 safe_copy 或 nested summary，必须递归检查。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _review_decision(
    load_issue: str,
    source_state: dict[str, Any],
    source_backfill_status: str,
    effective_ref: str,
    requested_ref: str,
    source_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    unsafe_source: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
    alignment: dict[str, Any],
) -> tuple[str, list[str]]:
    # fail closed 顺序固定：输入可信性和安全边界优先于普通材料缺口。
    reasons: list[str] = []
    if load_issue:
        return BLOCKED_MISSING_BACKFILL, [load_issue]
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING_BACKFILL, ["unsupported_acceptance_backfill_schema_or_boundary"]
    if not effective_ref:
        return BLOCKED_MISSING_BACKFILL, ["missing_safe_evidence_ref"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return EVIDENCE_REF_MISMATCH, ["requested_evidence_ref_mismatch"]
    if same_ref_required is not True:
        return EVIDENCE_REF_MISMATCH, ["same_evidence_ref_required_not_boolean_true"]
    if not source_safe:
        return UNSAFE_REJECTED, ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"]
    if unsafe_source:
        return UNSAFE_REJECTED, ["unsafe_or_raw_copy_detected"]
    if success_or_control_claim:
        return UNSAFE_REJECTED, ["success_or_control_claim_detected"]
    if source_backfill_status != READY_BACKFILL_STATUS:
        reasons.append("acceptance_backfill_not_ready")
    if alignment["mismatched_materials"] or alignment["missing_evidence_ref_materials"]:
        return EVIDENCE_REF_MISMATCH, reasons + ["same_evidence_ref_alignment_not_aligned"]
    if material_status["missing_materials"] or material_status["rejected_materials"]:
        return NEEDS_MORE_MATERIAL, reasons + ["missing_or_rejected_backfill_materials"]
    if material_status["accepted_count"] != material_status["required_count"] or not material_status["is_complete"] or alignment["status"] != "aligned":
        return NEEDS_MORE_MATERIAL, reasons + ["material_completeness_not_ready"]
    if reasons:
        return NEEDS_MORE_MATERIAL, reasons
    return READY_DECISION, ["all_safe_backfill_materials_ready_for_review_handoff"]


def _next_required_evidence(decision: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # next evidence 是 PC/owner 材料修复清单，不是机器人动作指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == READY_DECISION:
        return [
            f"review acceptance backfill summary for evidence_ref={ref}",
            "prepare owner handoff without enabling Robot/mobile primary actions",
            "real field rerun result, route/elevator pass, HIL, and phone/browser proof remain outside this gate",
        ]
    if decision == NEEDS_MORE_MATERIAL:
        required = [f"provide missing material: {name} for evidence_ref={ref}" for name in material_status["missing_materials"]]
        required.extend([f"repair rejected material: {name} for evidence_ref={ref}" for name in material_status["rejected_materials"]])
        return required or [f"rerun acceptance backfill with complete safe metadata for evidence_ref={ref}"]
    if decision == EVIDENCE_REF_MISMATCH:
        return [f"rerun packet/backfill so all eight material classes share evidence_ref={ref}"]
    if decision == UNSAFE_REJECTED:
        return ["remove unsafe/raw/success/control claims and rerun the PC-only backfill gate"]
    return [f"provide supported acceptance backfill artifact or summary for evidence_ref={ref}", *reasons]


def _owner_handoff(decision: str, evidence_ref: str, material_status: dict[str, Any], next_required_evidence: list[str]) -> dict[str, Any]:
    # handoff 只交给 owner 复核和材料修复，不给 mobile/Robot 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": decision,
        "review_decision": decision,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "material_status": material_status["status"],
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "next_required_evidence": next_required_evidence,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py --acceptance-packet-json <acceptance_packet.json> --material-dir <sanitized_material_dir> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill_review_decision.py --acceptance-backfill-json <acceptance_backfill.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _safe_copy(
    decision: str,
    evidence_ref: str,
    lineage: dict[str, str],
    material_status: dict[str, Any],
    decision_reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": decision_reasons,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "safe_lineage": lineage,
        "material_status": material_status["status"],
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    alignment: dict[str, Any],
    decision_reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_status": material_status,
        "same_evidence_ref_alignment": alignment,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
    acceptance_backfill_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance backfill JSON，生成 fail-closed review decision artifact。"""
    payload, load_issue = _load_json(acceptance_backfill_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    effective_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source) if source else True
    source_state = _source_status(load_issue, source)
    source_backfill_status = _source_backfill_status(source) if source else "missing"
    material_status = _material_status(source) if source else {
        "status": "unknown",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(REQUIRED_MATERIALS),
        "is_complete": False,
        "gap_count": 0,
        "rejected_reasons": {},
    }
    alignment = _alignment_status(source) if source else {"required": True, "status": "missing", "mismatched_materials": [], "missing_evidence_ref_materials": []}
    source_safe = bool(source) and _source_is_safe(source)
    unsafe_source = bool(payload) and (material_pack._has_forbidden_copy(source) or material_pack._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and (material_pack._has_success_or_control_claim(source) or _has_true_control_flag(source))
    decision, decision_reasons = _review_decision(
        load_issue,
        source_state,
        source_backfill_status,
        effective_ref,
        requested_ref,
        source_ref,
        same_ref_required,
        source_safe,
        unsafe_source,
        success_or_control_claim,
        material_status,
        alignment,
    )

    lineage = _source_lineage(source)
    next_required_evidence = _next_required_evidence(decision, effective_ref, material_status, decision_reasons)
    owner_handoff = _owner_handoff(decision, effective_ref, material_status, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": source_backfill_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(decision, effective_ref, lineage, material_status, decision_reasons, owner_handoff, next_required_evidence, rerun_commands)
    summary = _summary_payload(
        decision,
        effective_ref,
        source_summary,
        lineage,
        material_status,
        alignment,
        decision_reasons,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "allowed_review_decisions": list(ALLOWED_REVIEW_DECISIONS),
        "decision_reasons": decision_reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_status": material_status,
        "same_evidence_ref_alignment": alignment,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_task_record",
            "raw_nav2_runtime_log",
            "raw_fixed_route_runtime_log",
            "raw_route_completion_signal",
            "raw_elevator_door_state",
            "raw_target_floor_confirmation",
            "raw_human_assistance_record",
            "raw_dropoff_cancel_completion",
            "raw_delivery_result",
            "raw_true_phone_browser_evidence",
            "raw_diagnostics",
            "material_dir_scan",
            "ros_graph",
            "serial_uart",
            "wave_rover",
            "real_elevator",
            "external_cloud",
            "real_phone_or_browser",
            "robot_action",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = UNSAFE_REJECTED
        artifact["review_decision"] = UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["status"] = UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["review_decision"] = UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["status"] = UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["review_decision"] = UNSAFE_REJECTED
        summary["status"] = UNSAFE_REJECTED
        summary["review_decision"] = UNSAFE_REJECTED
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun acceptance backfill review decision artifact")
    parser.add_argument("--acceptance-backfill-json", required=True, help="acceptance backfill artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review decision gate")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
        args.acceptance_backfill_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_backfill_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_backfill_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
