#!/usr/bin/env python3
"""生成 field evidence rerun execution result acceptance review handoff。

该 PC-only gate 接在
`field_evidence_rerun_execution_result_acceptance_backfill_review_decision`
之后，只读取上一轮 review-decision artifact / summary / Robot diagnostics
safe alias 或 wrapper/nested JSON。输出是给 field owner、support reviewer 和
Product closeout 使用的脱敏 handoff package；它不读取真实 ROS/Nav2 runtime、
硬件、手机/browser、外部云或 raw artifact，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_backfill_review_decision as review_decision
import route_task_field_retest_material_pack as material_pack


HANDOFF_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate"

# 上游必须是上一轮 acceptance backfill review-decision，不能跳过 review 阶段。
SOURCE_SCHEMAS = {review_decision.DECISION_SCHEMA, review_decision.DECISION_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {review_decision.DECISION_BOUNDARY}
READY_SOURCE_DECISION = review_decision.READY_DECISION

# handoff state 是本 gate 的独立语义，不能复用上游 review_decision 状态名。
READY_HANDOFF = "ready_for_field_owner_support_reviewer_handoff_not_proven"
HANDOFF_NEEDS_MORE_MATERIAL = "handoff_needs_more_material"
HANDOFF_EVIDENCE_REF_MISMATCH = "handoff_evidence_ref_mismatch"
HANDOFF_UNSAFE_REJECTED = "handoff_unsafe_rejected"
BLOCKED_MISSING_REVIEW_DECISION = "blocked_missing_review_decision"
ALLOWED_HANDOFF_STATES = (
    READY_HANDOFF,
    HANDOFF_NEEDS_MORE_MATERIAL,
    HANDOFF_EVIDENCE_REF_MISMATCH,
    HANDOFF_UNSAFE_REJECTED,
    BLOCKED_MISSING_REVIEW_DECISION,
)

# checklist 使用“true”前缀提醒后续 owner 必须回填真实材料；本 gate 不读取这些材料。
HANDOFF_CHECKLIST = (
    "true task record",
    "true Nav2/fixed-route runtime log",
    "route completion signal",
    "true elevator door state",
    "target floor confirmation",
    "human assistance record",
    "dropoff/cancel completion or delivery result",
    "true phone/browser evidence",
)

NOT_PROVEN = review_decision.NOT_PROVEN

# rg 围栏依赖这些 literal；同时给人工复核一个压缩边界说明。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "ready_for_field_owner_support_reviewer_handoff_not_proven; "
    "handoff_needs_more_material; handoff_evidence_ref_mismatch; "
    "handoff_unsafe_rejected; blocked_missing_review_decision; "
    "ready_for_field_rerun_result_acceptance_review_handoff; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate"
)

# 设计约束 01：本 gate 只消费 review-decision safe output，不读 raw artifact。
# 设计约束 02：handoff 只表示 owner/support/reviewer 可接手，不表示现场通过。
# 设计约束 03：source=software_proof 与 not_proven 必须从上游延续到输出。
# 设计约束 04：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 05：上一轮 decision 必须是 ready_for_field_rerun_result_acceptance_review_handoff。
# 设计约束 06：上一轮 boundary 必须固定，防止跨 gate 输入误接入。
# 设计约束 07：same evidence_ref 是现场复账主键，缺失或不一致必须 fail closed。
# 设计约束 08：弱类型 same_evidence_ref_required 不能通过，必须是 JSON boolean true。
# 设计约束 09：checklist 只是后续真实材料清单，不读取真实 Nav2 或电梯材料。
# 设计约束 10：unsafe copy、credentials、raw path、ROS topic 和硬件细节必须拒绝。
# 设计约束 11：success/control/HIL/O5/PR #5 resolution claim 必须拒绝。
# 设计约束 12：Robot/mobile 只能消费 summary/safe_copy，不拿完整 raw source。
# 设计约束 13：wrapper/nested JSON 只递归固定 key，避免采信任意 payload。
# 设计约束 14：blocked artifact 也返回 exit code 0，便于 CI 和 sprint 留痕。
# 设计约束 15：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 16：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 17：输出最终递归脱敏，防止新增字段绕过安全扫描。
# 设计约束 18：所有技术注释使用中文，解释 fail-closed 取舍。
# 设计约束 19：本 gate 不更新 Robot/mobile/OKR/sprint closeout 文件。
# 设计约束 20：状态名保持 snake_case，便于 rg 和下游解析。


def _utc_now() -> str:
    # UTC 字符串方便不同 Docker/PC 主机按文本排序审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常也生成 blocked handoff，避免审计链路静默中断。
    if not path:
        return {}, "review_decision_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_decision_json_missing"
    except json.JSONDecodeError:
        return {}, "review_decision_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "review_decision_json_read_error"
    if not isinstance(payload, dict):
        return {}, "review_decision_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object；字符串化 JSON 不作为可信 safe alias。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot alias 字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 输出清单只保留短字符串，避免复制完整上游 nested artifact。
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
    # 只递归已知 safe wrapper key，避免 raw diagnostics 或 material body 混入。
    candidates = [payload]
    for key in (
        "field_evidence_rerun_execution_result_acceptance_review_handoff",
        "field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision",
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        "acceptance_backfill_review_decision",
        "acceptance_backfill_review_decision_summary",
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
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 blocked 诊断。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 和 boundary 必须同时白名单化，不能跨 family 消费。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可来自顶层、safe_copy、owner_handoff 或下游只读摘要。
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


def _source_review_decision(source: dict[str, Any]) -> str:
    # 上游 ready decision 是进入 handoff 的必要条件，不能从材料数量推断。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("review_decision"),
            source.get("status"),
            robot.get("review_decision"),
            robot.get("status"),
            mobile.get("review_decision"),
            mobile.get("status"),
            safe_copy.get("review_decision"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 只接受布尔 true；字符串 true 会在不同语言端产生歧义。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return source.get(
        "same_evidence_ref_required",
        robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
    )


def _source_is_safe(source: dict[str, Any]) -> bool:
    # software_proof、not_proven 和三个 false flag 是 handoff 的最低安全边界。
    encoded = material_pack._encoded(source)
    return (
        source.get("source") == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _has_true_control_flag(value: Any) -> bool:
    # JSON boolean true 比自由文本更危险，必须递归阻断。
    if isinstance(value, dict):
        if value.get("safe_to_control") is True or value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _has_forbidden_proof_claim(value: Any) -> bool:
    # 本 gate 额外阻断宽泛自由文本，但不误伤 not_proven 里的 snake_case 否定态。
    encoded = material_pack._encoded(value).lower()
    forbidden_phrases = (
        "external proof",
        "objective 5 proof",
        "objective 5 external proof",
        "o5 proof",
        "o5 external proof",
        "hil pass",
        "hil passed",
        "hil complete",
        "pr #5 resolved",
        "pr#5 resolved",
        "pr 5 resolved",
        "pr #5 resolution",
        "pr#5 resolution",
        "pr 5 resolution",
    )
    return any(phrase in encoded for phrase in forbidden_phrases)


def _material_status(source: dict[str, Any]) -> dict[str, Any]:
    # 兼容上一轮 summary 的 material_status 与 safe_copy 摘要。
    safe_copy = _dict(source, "safe_copy")
    material_status = _dict(source, "material_status") or _dict(safe_copy, "material_status")
    missing = _safe_list(material_status.get("missing_materials") or safe_copy.get("missing_materials"))
    rejected = _safe_list(material_status.get("rejected_materials") or safe_copy.get("rejected_materials"))
    accepted = _safe_list(material_status.get("accepted_materials") or safe_copy.get("accepted_materials"))
    accepted_count = int(material_status.get("accepted_count", len(accepted)) or 0)
    required_count = int(material_status.get("required_count", len(review_decision.REQUIRED_MATERIALS)) or 0)
    is_complete = bool(material_status.get("is_complete", accepted_count == required_count and required_count > 0 and not missing and not rejected))
    return {
        "status": material_pack._safe_text(material_status.get("status", "accepted" if is_complete else "unknown")),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": accepted_count,
        "required_count": required_count,
        "is_complete": is_complete,
    }


def _source_lineage(source: dict[str, Any]) -> dict[str, str]:
    # lineage 只复制短字段，避免复制完整上游 artifact。
    lineage = {
        "source_review_decision_schema": material_pack._safe_text(source.get("schema", "")),
        "source_review_decision_status": _source_review_decision(source),
    }
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"review_decision_{material_pack._safe_text(key)}"] = text
    return lineage


def _handoff_decision(
    load_issue: str,
    source_state: dict[str, Any],
    source_review_status: str,
    requested_ref: str,
    source_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    unsafe_source: bool,
    success_or_control_claim: bool,
    material_status: dict[str, Any],
) -> tuple[str, list[str]]:
    # fail-closed 顺序固定：输入可信性和安全边界优先于材料缺口。
    if load_issue:
        return BLOCKED_MISSING_REVIEW_DECISION, [load_issue]
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING_REVIEW_DECISION, ["unsupported_review_decision_schema_or_boundary"]
    if not (requested_ref or source_ref):
        return BLOCKED_MISSING_REVIEW_DECISION, ["missing_safe_evidence_ref"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return HANDOFF_EVIDENCE_REF_MISMATCH, ["requested_evidence_ref_mismatch"]
    if same_ref_required is not True:
        return HANDOFF_EVIDENCE_REF_MISMATCH, ["same_evidence_ref_required_not_boolean_true"]
    if not source_safe:
        return HANDOFF_UNSAFE_REJECTED, ["source_not_software_proof_not_proven_or_fail_closed_flags_missing"]
    if unsafe_source:
        return HANDOFF_UNSAFE_REJECTED, ["unsafe_or_raw_copy_detected"]
    if success_or_control_claim:
        return HANDOFF_UNSAFE_REJECTED, ["success_or_control_claim_detected"]
    if source_review_status != READY_SOURCE_DECISION:
        return HANDOFF_NEEDS_MORE_MATERIAL, ["review_decision_not_ready_for_handoff"]
    if material_status["missing_materials"] or material_status["rejected_materials"]:
        return HANDOFF_NEEDS_MORE_MATERIAL, ["missing_or_rejected_review_decision_materials"]
    if not material_status["is_complete"]:
        return HANDOFF_NEEDS_MORE_MATERIAL, ["material_status_not_complete"]
    return READY_HANDOFF, ["review_decision_ready_for_sanitized_owner_support_reviewer_handoff"]


def _handoff_checklist(evidence_ref: str, state: str) -> list[dict[str, Any]]:
    # checklist 明确后续需要真实材料，但本 gate 只输出 pending/ready 元数据。
    return [
        {
            "name": item,
            "evidence_ref": evidence_ref or "<same_evidence_ref>",
            "required_for_real_acceptance": True,
            "status": "required_not_proven" if state == READY_HANDOFF else "blocked_until_safe_review_decision",
        }
        for item in HANDOFF_CHECKLIST
    ]


def _next_required_evidence(state: str, evidence_ref: str, material_status: dict[str, Any], reasons: list[str]) -> list[str]:
    # next evidence 是 owner/support/reviewer 交接清单，不是机器人动作指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if state == READY_HANDOFF:
        return [
            f"handoff same evidence_ref={ref} to field owner, support reviewer, and Product closeout",
            "collect true task record, true Nav2/fixed-route runtime log, route completion signal, elevator/floor/human assistance evidence, dropoff/cancel or delivery result, and true phone/browser evidence",
            "keep Robot/mobile primary actions disabled until real reviewed material exists",
        ]
    if state == HANDOFF_NEEDS_MORE_MATERIAL:
        required = [f"repair missing material before handoff: {name} for evidence_ref={ref}" for name in material_status["missing_materials"]]
        required.extend([f"repair rejected material before handoff: {name} for evidence_ref={ref}" for name in material_status["rejected_materials"]])
        return required or [f"rerun acceptance backfill review-decision until it emits {READY_SOURCE_DECISION} for evidence_ref={ref}"]
    if state == HANDOFF_EVIDENCE_REF_MISMATCH:
        return [f"rerun acceptance packet/backfill/review-decision so all summaries share evidence_ref={ref}"]
    if state == HANDOFF_UNSAFE_REJECTED:
        return ["remove unsafe/raw/success/control/external-proof/HIL/PR-resolution claims and rerun the PC-only gate"]
    return [f"provide supported acceptance backfill review-decision artifact or summary for evidence_ref={ref}", *reasons]


def _owner_handoff(state: str, evidence_ref: str, checklist: list[dict[str, Any]], next_required_evidence: list[str]) -> dict[str, Any]:
    # owner_handoff 只授权人工复核和补证，不给 Robot/mobile 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": state,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "handoff_checklist": checklist,
        "next_required_evidence": next_required_evidence,
        "reviewer_boundary": "support_reviewer_handoff_only_not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill_review_decision.py --acceptance-backfill-json <acceptance_backfill.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_review_handoff.py --review-decision-json <review_decision.json> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false",
    ]


def _safe_copy(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "handoff_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    state: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    checklist: list[dict[str, Any]],
    reasons: list[str],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "handoff_checklist": checklist,
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


def build_field_evidence_rerun_execution_result_acceptance_review_handoff(
    review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance backfill review-decision JSON，生成 fail-closed handoff。"""
    payload, load_issue = _load_json(review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    effective_ref = requested_ref or source_ref
    source_state = _source_status(load_issue, source)
    source_review_status = _source_review_decision(source) if source else "missing"
    same_ref_required = _same_ref_required(source) if source else True
    source_safe = bool(source) and _source_is_safe(source)
    unsafe_source = bool(payload) and (material_pack._has_forbidden_copy(source) or material_pack._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and (
        material_pack._has_success_or_control_claim(source)
        or _has_true_control_flag(source)
        or _has_forbidden_proof_claim(source)
    )
    material_status = _material_status(source) if source else {
        "status": "unknown",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(review_decision.REQUIRED_MATERIALS),
        "is_complete": False,
    }

    state, reasons = _handoff_decision(
        load_issue,
        source_state,
        source_review_status,
        requested_ref,
        source_ref,
        same_ref_required,
        source_safe,
        unsafe_source,
        success_or_control_claim,
        material_status,
    )
    lineage = _source_lineage(source)
    checklist = _handoff_checklist(effective_ref, state)
    next_required_evidence = _next_required_evidence(state, effective_ref, material_status, reasons)
    owner_handoff = _owner_handoff(state, effective_ref, checklist, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "review_decision": source_review_status,
        "status": source_review_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(
        state,
        effective_ref,
        source_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
    )
    summary = _summary_payload(
        state,
        effective_ref,
        source_summary,
        lineage,
        material_status,
        checklist,
        reasons,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": state,
        "handoff_status": state,
        "allowed_handoff_states": list(ALLOWED_HANDOFF_STATES),
        "handoff_reasons": reasons,
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "safe_lineage": lineage,
        "material_status": material_status,
        "handoff_checklist": checklist,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_review_handoff_summary": summary,
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
        artifact["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["robot_diagnostics_summary"]["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["status"] = HANDOFF_UNSAFE_REJECTED
        artifact["mobile_readonly_summary"]["handoff_status"] = HANDOFF_UNSAFE_REJECTED
        summary["status"] = HANDOFF_UNSAFE_REJECTED
        summary["handoff_status"] = HANDOFF_UNSAFE_REJECTED
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
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun acceptance review handoff artifact")
    parser.add_argument("--review-decision-json", required=True, help="acceptance backfill review-decision artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this handoff gate")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_review_handoff(
        args.review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_review_handoff: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_review_handoff_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
