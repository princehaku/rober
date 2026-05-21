#!/usr/bin/env python3
"""生成 field evidence real material response review decision artifact。

该 PC gate 只消费上一轮 `field_evidence_real_material_response_intake` 的
artifact、summary 或 Robot diagnostics safe alias。它把 response intake 的
accepted/missing/rejected/blocked 分类转成保守 review decision，并输出 owner
handoff、next required evidence 与 phone-safe copy。它不读取 raw 现场材料、ROS
graph、Nav2 runtime、硬件、云端或真实手机/browser runtime。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_response_intake as intake
import route_task_field_retest_material_pack as material_pack


DECISION_SCHEMA = "trashbot.field_evidence_real_material_response_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_response_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_field_evidence_real_material_response_review_decision_gate"

# 只允许 response-intake artifact/summary，Robot alias 也必须保留同一 schema/boundary。
SOURCE_SCHEMAS = {intake.INTAKE_SCHEMA, intake.INTAKE_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {intake.INTAKE_BOUNDARY}
READY_INTAKE_STATUS = "ready_for_field_evidence_real_material_review_not_proven"

ACCEPTED_DECISION = "accepted_for_later_review_not_proven"
BACKFILL_DECISION = "needs_material_backfill_not_proven"
REJECTED_DECISION = "rejected_unsafe_or_mixed_response_not_proven"
BLOCKED_DECISION = "blocked_real_environment_unavailable_not_proven"
MISSING_SOURCE_DECISION = "blocked_missing_field_evidence_real_material_response_intake_not_proven"

REVIEW_DECISIONS = (
    ACCEPTED_DECISION,
    BACKFILL_DECISION,
    REJECTED_DECISION,
    BLOCKED_DECISION,
    MISSING_SOURCE_DECISION,
)

# blocked claims 明确隔离 later review 与真实路线/电梯/投放/硬件/云证明。
BLOCKED_CLAIMS = tuple(
    dict.fromkeys(
        list(intake.BLOCKED_CLAIMS)
        + [
            "route_elevator_review_accepted_as_field_pass",
            "accepted_for_later_review_as_delivery_success",
            "real_material_response_review_as_pr5_resolution",
        ]
    )
)

BOUNDARY_NOTE = (
    "field_evidence_real_material_response_review_decision; "
    "software_proof_docker_field_evidence_real_material_response_review_decision_gate; "
    "accepted_for_later_review_not_proven; needs_material_backfill_not_proven; "
    "rejected_unsafe_or_mixed_response_not_proven; "
    "blocked_real_environment_unavailable_not_proven; "
    "source=software_proof; status=not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; same_evidence_ref_required=true"
)

# 设计约束 01：本 gate 只读 response-intake safe surface，不读取 raw materials。
# 设计约束 02：source schema 和 evidence boundary 必须同时命中上一轮 intake。
# 设计约束 03：source=software_proof、not_proven 与三类 false flag 不可放松。
# 设计约束 04：accepted decision 仅表示后续人工/软件 review 可继续。
# 设计约束 05：missing material 映射 backfill，不得静默当作 accepted。
# 设计约束 06：rejected、mixed evidence_ref、unsafe copy 必须整体 rejected。
# 设计约束 07：blocked material 映射真实环境不可用，不表示失败复跑完成。
# 设计约束 08：缺少 valid response-intake source 时必须 fail closed。
# 设计约束 09：CLI 指定 evidence_ref 与 source 不一致时必须 rejected。
# 设计约束 10：Robot alias 只作为 safe alias，不提升证据等级。
# 设计约束 11：owner handoff 只给下一步材料动作，不给机器人控制动作。
# 设计约束 12：phone copy 必须只读，不能启用 Start/Confirm/Cancel。
# 设计约束 13：raw ROS topic、/cmd_vel、serial/UART/WAVE ROVER detail 不进输出。
# 设计约束 14：credential、本机路径、checksum、traceback 不进输出。
# 设计约束 15：delivery_success/control claim 必须阻断，不能降级为 backfill。
# 设计约束 16：summary 面向 Robot/mobile，只保留安全计数与短字段。
# 设计约束 17：safe_copy 字段稳定给后续 diagnostics/mobile 复用。
# 设计约束 18：最终 payload 再递归脱敏，防止新增字段绕过扫描。
# 设计约束 19：blocked artifact 也返回 exit code 0，便于 Docker-only 留痕。
# 设计约束 20：所有技术注释使用中文，解释保守边界和参数取舍。


def _utc_now() -> str:
    # UTC 时间便于 PC/Docker artifact 与 sprint 记录按统一时间线排序。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常必须显式 blocked，避免无 source 时输出默认 accepted。
    if not path:
        return {}, "response_intake_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "response_intake_json_missing"
    except json.JSONDecodeError:
        return {}, "response_intake_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "response_intake_json_read_error"
    if not isinstance(payload, dict):
        return {}, "response_intake_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object，字符串化 JSON 不作为可信 safe source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy、Robot alias 的字段位置不完全一致。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 输出只保留短文本列表，避免把完整上游 artifact 复制到 review decision。
    if isinstance(value, list):
        return [material_pack._safe_text(item) for item in value[:limit]]
    if isinstance(value, tuple):
        return [material_pack._safe_text(item) for item in list(value)[:limit]]
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw material payload 被误当 source。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_response_review_decision",
        "field_evidence_real_material_response_review_decision_summary",
        "field_evidence_real_material_response_intake",
        "field_evidence_real_material_response_intake_summary",
        "robot_diagnostics_field_evidence_real_material_response_intake_summary",
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
    # schema 命中上一轮 intake 时才可信；否则保留顶层用于 unsupported 解释。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时匹配，防止跨 gate artifact 被复核。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是 response-intake 与 review-decision 串联的唯一主键。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_ref(
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


def _source_intake_status(source: dict[str, Any]) -> str:
    # review decision 只消费 response_intake_status，不自行解释 raw response。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_text(
        _first_text(
            source.get("response_intake_status"),
            source.get("status"),
            safe_copy.get("response_intake_status"),
            safe_copy.get("status"),
            robot.get("response_intake_status"),
            robot.get("status"),
            mobile.get("response_intake_status"),
            mobile.get("status"),
            default="missing",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 必须是 JSON boolean true；字符串 true 不视为满足同证据号硬约束。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return source.get(
        "same_evidence_ref_required",
        safe_copy.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True))),
    )


def _is_software_proof_not_proven(source: dict[str, Any]) -> bool:
    # 五个固定边界同时满足后，review decision 才能进入非 rejected 分支。
    encoded = material_pack._encoded(source)
    safe_copy = _dict(source, "safe_copy")
    source_text = _first_text(source.get("source"), safe_copy.get("source"), default="")
    return (
        source_text == "software_proof"
        and "not_proven" in encoded
        and source.get("safe_to_control", safe_copy.get("safe_to_control")) is False
        and source.get("delivery_success", safe_copy.get("delivery_success")) is False
        and source.get("primary_actions_enabled", safe_copy.get("primary_actions_enabled")) is False
    )


def _unsafe_copy(value: Any) -> bool:
    # 禁词、路径、凭证、硬件细节和 success/control claim 都整体 fail closed。
    return (
        material_pack._has_forbidden_copy(value)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _material_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    # material_responses 只复制安全短字段，review decision 不搬运 raw response。
    safe_copy = _dict(source, "safe_copy")
    value = source.get("material_responses")
    if not isinstance(value, list):
        value = safe_copy.get("material_responses")
    if not isinstance(value, list):
        return []
    items: list[dict[str, Any]] = []
    for item in value[: len(intake.REQUIRED_MATERIALS)]:
        if not isinstance(item, dict):
            continue
        name = material_pack._safe_text(item.get("name", ""))
        classification = material_pack._safe_text(item.get("classification", "missing"))
        if name:
            items.append(
                {
                    "name": name,
                    "classification": classification,
                    "safe_evidence_ref": material_pack._safe_ref(_first_text(item.get("safe_evidence_ref"), item.get("evidence_ref"), default="")),
                    "ready_for_later_review_only": bool(item.get("ready_for_later_review_only", False)),
                    "safe_summary": material_pack._safe_text(item.get("safe_summary", ""))[:240],
                }
            )
    return items


def _classification_counts(source: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, int]:
    # 优先消费 intake 计数；缺失时从 material_responses 重新汇总。
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("material_classification_counts")
    if not isinstance(raw, dict):
        raw = safe_copy.get("material_classification_counts")
    counts = {status: 0 for status in intake.RESPONSE_STATUSES}
    if isinstance(raw, dict):
        for status in counts:
            try:
                counts[status] = int(raw.get(status, 0) or 0)
            except (TypeError, ValueError):
                counts[status] = 0
    if not any(counts.values()) and items:
        for item in items:
            classification = str(item.get("classification", "missing"))
            if classification in counts:
                counts[classification] += 1
    return counts


def _material_lists(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    # owner handoff 只需要按分类列出类别名，不需要复制材料正文。
    grouped = {status: [] for status in intake.RESPONSE_STATUSES}
    for item in items:
        classification = str(item.get("classification", "missing"))
        name = material_pack._safe_text(item.get("name", ""))
        if classification in grouped and name:
            grouped[classification].append(name)
    return grouped


def _source_summary(source_state: dict[str, str], source: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    # source summary 是后续 Robot/mobile 的审计线索，不包含 raw response。
    return {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "response_intake_status": _source_intake_status(source),
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": _same_ref_required(source),
        "source_is_software_proof_not_proven": _is_software_proof_not_proven(source),
        "unsafe_copy": bool(source) and _unsafe_copy(source),
    }


def _review_decision(
    source_state: dict[str, str],
    source_summary: dict[str, Any],
    counts: dict[str, int],
    evidence_ref_mismatch: bool,
) -> tuple[str, list[str]]:
    # 决策优先级：无 source/unsupported -> blocked/rejected；unsafe -> rejected；
    # blocked -> environment unavailable；missing -> backfill；全 accepted 才 later review。
    reasons: list[str] = []
    if source_state.get("load_issue"):
        return MISSING_SOURCE_DECISION, [source_state["load_issue"]]
    if source_state.get("schema_status") != "supported":
        return REJECTED_DECISION, ["unsupported_response_intake_schema_or_boundary"]
    if evidence_ref_mismatch:
        return REJECTED_DECISION, ["evidence_ref_mismatch"]
    if source_summary.get("same_evidence_ref_required") is not True:
        return REJECTED_DECISION, ["same_evidence_ref_required_not_true"]
    if not source_summary.get("source_is_software_proof_not_proven"):
        return REJECTED_DECISION, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if source_summary.get("unsafe_copy"):
        return REJECTED_DECISION, ["unsafe_or_sensitive_response_intake_copy"]

    source_status = str(source_summary.get("response_intake_status", ""))
    if counts.get("rejected", 0) > 0 or "rejected" in source_status:
        reasons.append("source_response_intake_rejected_or_unsafe")
    if reasons:
        return REJECTED_DECISION, reasons
    if counts.get("blocked", 0) > 0 or "dependency_unavailable" in source_status:
        return BLOCKED_DECISION, ["field_environment_or_dependency_unavailable"]
    if counts.get("missing", 0) > 0 or "missing" in source_status:
        return BACKFILL_DECISION, ["required_real_material_backfill_needed"]
    if source_status == READY_INTAKE_STATUS and counts.get("accepted", 0) >= len(intake.REQUIRED_MATERIALS):
        return ACCEPTED_DECISION, ["all_required_material_categories_safe_and_same_ref_for_later_review_only"]
    return BLOCKED_DECISION, ["response_intake_not_ready_for_review_decision"]


def _next_required_evidence(decision: str, grouped: dict[str, list[str]]) -> list[dict[str, Any]]:
    # 下一步 evidence 是人工/现场材料动作，不是机器人控制动作。
    if decision == ACCEPTED_DECISION:
        return [
            {
                "owner": "Product Manager / OKR Owner",
                "action": "schedule_later_human_review_without_marking_field_pass",
                "materials": list(intake.REQUIRED_MATERIALS),
            }
        ]
    if decision == BACKFILL_DECISION:
        return [
            {
                "owner": "field-owner",
                "action": "backfill_missing_real_material_categories_under_same_evidence_ref",
                "materials": grouped.get("missing", []) or list(intake.REQUIRED_MATERIALS),
            }
        ]
    if decision == REJECTED_DECISION:
        return [
            {
                "owner": "field-owner",
                "action": "resubmit_sanitized_same_evidence_ref_response_intake_without_unsafe_or_mixed_claims",
                "materials": grouped.get("rejected", []) or list(intake.REQUIRED_MATERIALS),
            }
        ]
    if decision == BLOCKED_DECISION:
        return [
            {
                "owner": "field-owner",
                "action": "capture_real_route_elevator_phone_or_hardware_materials_before_review_can_continue",
                "materials": grouped.get("blocked", []) or list(intake.REQUIRED_MATERIALS),
            }
        ]
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "action": "provide_valid_field_evidence_real_material_response_intake_artifact_or_summary",
            "materials": list(intake.REQUIRED_MATERIALS),
        }
    ]


def _owner_handoff(decision: str, reasons: list[str], evidence_ref: str, grouped: dict[str, list[str]]) -> dict[str, Any]:
    # handoff 明确下一责任人与禁止声明，防止 accepted 被误读成现场通过。
    if decision == ACCEPTED_DECISION:
        owner = "Product Manager / OKR Owner"
        action = "review sanitized material indexes later; keep not_proven"
    elif decision == BACKFILL_DECISION:
        owner = "field-owner"
        action = "backfill missing categories under the same safe evidence_ref"
    elif decision == REJECTED_DECISION:
        owner = "field-owner"
        action = "remove unsafe, mixed, raw, success, control, credential, path, or hardware-detail claims"
    elif decision == BLOCKED_DECISION:
        owner = "field-owner"
        action = "collect real environment materials before review can proceed"
    else:
        owner = "Autonomy Algorithm Engineer"
        action = "rerun response-intake and provide a valid sanitized source"
    return {
        "owner": owner,
        "action": action,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "decision_reasons": reasons,
        "accepted_materials": grouped.get("accepted", []),
        "missing_materials": grouped.get("missing", []),
        "rejected_materials": grouped.get("rejected", []),
        "blocked_materials": grouped.get("blocked", []),
        "not_delivery_result": True,
        "not_delivery_success": True,
    }


def _safe_phone_copy(decision: str, evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # phone copy 只说明状态与下一步，不暴露 raw artifact 或控制入口。
    return {
        "title": "现场真实材料响应复核决策",
        "review_decision": decision,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "message": "accepted 只表示后续复核可继续，仍不是现场通过或交付成功。",
        "decision_reasons": reasons,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "delivery_success": False,
    }


def _safe_copy(
    decision: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    grouped: dict[str, list[str]],
    counts: dict[str, int],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 建议消费面，字段稳定且全为短字段。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": "not_proven",
        "review_decision": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_response_intake": source_summary,
        "decision_reasons": reasons,
        "material_classification_counts": counts,
        "accepted_materials": grouped.get("accepted", []),
        "missing_materials": grouped.get("missing", []),
        "rejected_materials": grouped.get("rejected", []),
        "blocked_materials": grouped.get("blocked", []),
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    grouped: dict[str, list[str]],
    counts: dict[str, int],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 与 artifact 保持同一 decision，便于 Robot diagnostics safe alias。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "status": "not_proven",
        "review_decision": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_response_intake": source_summary,
        "decision_reasons": reasons,
        "material_classification_counts": counts,
        "accepted_materials": grouped.get("accepted", []),
        "missing_materials": grouped.get("missing", []),
        "rejected_materials": grouped.get("rejected", []),
        "blocked_materials": grouped.get("blocked", []),
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "safe_copy": safe_copy,
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": ["not_proven"],
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_real_material_response_review_decision(
    response_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 response-intake safe source，生成 fail-closed review decision。"""
    source_payload, load_issue = _load_json(response_intake_json)
    source_raw = _find_source(source_payload) if source_payload else {}
    source_state = _source_status(load_issue, source_raw)
    source_ref = _source_evidence_ref(source_raw) if source_raw else ""
    requested_ref = material_pack._safe_ref(evidence_ref) or source_ref
    evidence_ref_mismatch = bool(evidence_ref and source_ref and requested_ref != source_ref)
    items = _material_items(source_raw) if source_raw else []
    counts = _classification_counts(source_raw, items)
    grouped = _material_lists(items)
    source_summary = _source_summary(source_state, source_raw, source_ref)
    decision, reasons = _review_decision(source_state, source_summary, counts, evidence_ref_mismatch)
    owner_handoff = _owner_handoff(decision, reasons, requested_ref, grouped)
    next_required_evidence = _next_required_evidence(decision, grouped)
    safe_copy = _safe_copy(decision, reasons, requested_ref, source_summary, grouped, counts, owner_handoff, next_required_evidence)
    summary = _summary_payload(decision, reasons, requested_ref, source_summary, grouped, counts, owner_handoff, next_required_evidence, safe_copy)
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "status": "not_proven",
        "review_decision": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_response_intake": source_summary,
        "decision_reasons": reasons,
        "material_classification_counts": counts,
        "material_review_groups": grouped,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, requested_ref, reasons),
        "safe_copy": safe_copy,
        "field_evidence_real_material_response_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "accepted_means": "accepted_for_later_review_not_proven_only",
        "blocked_claims": list(BLOCKED_CLAIMS),
        "non_access_scope": [
            "raw_field_materials",
            "low_level_robot_bus_topics",
            "motion_command_channels",
            "hardware_transport_details",
            "credential_or_database_queue_connection_material",
            "host_filesystem_locations",
            "debug_stack_hash_or_full_payload_material",
            "real robot runtime",
            "real phone browser runtime",
        ],
        "not_proven": ["not_proven"],
        "boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制 rejected，且保留 false flags。
        for payload in (artifact, summary):
            payload["status"] = "not_proven"
            payload["review_decision"] = REJECTED_DECISION
            payload["decision_reasons"] = ["unsafe_copy_after_sanitization"]
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence real material response review decision artifact")
    parser.add_argument("--response-intake-json", required=True, help="response intake artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for review decision")
    parser.add_argument("--output", default="", help="optional response review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional response review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print response review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_response_review_decision(
        args.response_intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_response_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"response_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
