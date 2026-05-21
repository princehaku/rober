#!/usr/bin/env python3
"""生成 field evidence real material owner ack review decision artifact。

该 PC gate 只消费上一轮 `field_evidence_real_material_owner_ack_intake` 的
artifact、summary 或 Robot diagnostics safe alias。它把 owner ack intake 的
accepted/missing/rejected/blocked 分类转成三值 review decision，并输出
owner handoff、next required evidence 与 phone-safe copy。它不读取 raw 现场
材料、ROS graph、Nav2 runtime、硬件、云端或真实手机/browser runtime。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_owner_ack_intake as intake
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.field_evidence_real_material_owner_ack_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_owner_ack_review_decision_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "field_evidence_real_material_owner_ack_review_decision"
EVIDENCE_BOUNDARY = "software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate"

# 只允许 owner ack intake safe surface，防止跳过上一轮 ACK 归档 gate。
SOURCE_SCHEMAS = {intake.SCHEMA, intake.SUMMARY_SCHEMA, intake.ROBOT_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {intake.EVIDENCE_BOUNDARY}

ACCEPTED = "accepted"
NEEDS_MORE_EVIDENCE = "needs_more_evidence"
REJECTED = "rejected"
DECISIONS = (ACCEPTED, NEEDS_MORE_EVIDENCE, REJECTED)

MISSING_SOURCE_STATUS = "blocked_missing_field_evidence_real_material_owner_ack_intake_not_proven"
UNSUPPORTED_STATUS = "blocked_unsupported_field_evidence_real_material_owner_ack_intake_source"
MISMATCH_STATUS = "evidence_ref_mismatch_field_material_owner_ack_review_decision_blocked"

# 这些状态来自上一轮 intake；review decision 只解释安全摘要，不重新读材料。
READY_SOURCE_STATUS = intake.READY_STATUS
MISSING_ACK_STATUS = intake.MISSING_ACK_STATUS
REJECTED_SOURCE_STATUS = intake.REJECTED_STATUS
UNSUPPORTED_SOURCE_STATUS = intake.UNSUPPORTED_STATUS
MISMATCH_SOURCE_STATUS = intake.MISMATCH_STATUS

BOUNDARY_NOTE = (
    "field_evidence_real_material_owner_ack_review_decision; "
    "software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate; "
    "decision enum accepted|needs_more_evidence|rejected; source=software_proof; "
    "status=not_proven; safe_to_control=false; delivery_success=false; "
    "primary_actions_enabled=false; same_evidence_ref_required=true"
)

# 设计约束 01：本 gate 只读 owner_ack_intake safe surface，不读取 raw materials。
# 设计约束 02：schema 和 evidence boundary 必须同时命中上一轮 intake。
# 设计约束 03：source=software_proof、not_proven 与三类 false flag 不可放松。
# 设计约束 04：accepted 只表示 owner ack 分类可进入后续人工复核。
# 设计约束 05：missing/blocked category 映射 needs_more_evidence，不静默接受。
# 设计约束 06：rejected、mixed evidence_ref、unsafe copy 必须整体 rejected。
# 设计约束 07：缺 source 或 unsupported source 必须 fail closed。
# 设计约束 08：CLI 指定 evidence_ref 与 source 不一致时必须 rejected。
# 设计约束 09：Robot alias 只作为 safe alias，不提升证据等级。
# 设计约束 10：owner handoff 只给补材料动作，不给机器人控制动作。
# 设计约束 11：phone copy 必须只读，不能启用 Start/Confirm/Cancel。
# 设计约束 12：raw ROS topic、serial/UART/WAVE ROVER detail 不进输出。
# 设计约束 13：credential、本机路径、checksum、traceback 不进输出。
# 设计约束 14：delivery_success/control claim 必须阻断。
# 设计约束 15：summary 面向 Robot/mobile，只保留安全计数与短字段。
# 设计约束 16：safe_copy 字段稳定给后续 diagnostics/mobile 复用。
# 设计约束 17：最终 payload 再递归脱敏，防止新增字段绕过扫描。
# 设计约束 18：blocked artifact 也返回 exit code 0，便于 Docker-only 留痕。
# 设计约束 19：所有技术注释使用中文，解释保守边界和参数取舍。


def _utc_now() -> str:
    # UTC 时间便于 PC/Docker artifact 与 sprint 记录按统一时间线排序。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常必须显式 blocked，避免无 source 时输出默认 accepted。
    if not path:
        return {}, "owner_ack_intake_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "owner_ack_intake_json_missing"
    except json.JSONDecodeError:
        return {}, "owner_ack_intake_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "owner_ack_intake_json_read_error"
    if not isinstance(payload, dict):
        return {}, "owner_ack_intake_json_not_object"
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
    # 输出只保留短文本列表，避免把完整上游 artifact 复制到 decision。
    if isinstance(value, list):
        return [material_pack._safe_text(item).strip() for item in value[:limit] if material_pack._safe_text(item).strip()]
    if isinstance(value, tuple):
        return [material_pack._safe_text(item).strip() for item in list(value)[:limit] if material_pack._safe_text(item).strip()]
    if value in (None, ""):
        return []
    text = material_pack._safe_text(value).strip()
    return [text] if text else []


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw material payload 被误当 source。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_owner_ack_review_decision",
        "field_evidence_real_material_owner_ack_review_decision_summary",
        "field_evidence_real_material_owner_ack_intake",
        "field_evidence_real_material_owner_ack_intake_summary",
        "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary",
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
    # schema 命中上一轮 owner_ack_intake 时才可信；否则保留顶层解释 blocked。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时匹配，防止跨 gate artifact 被复核。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", "")).strip()
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是 intake 与 review decision 串联的唯一主键。
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
    # review decision 只消费 owner_ack_intake_status，不自行解释 raw ack。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_text(
        _first_text(
            source.get("field_evidence_real_material_owner_ack_intake_status"),
            source.get("owner_ack_intake_status"),
            safe_copy.get("field_evidence_real_material_owner_ack_intake_status"),
            safe_copy.get("owner_ack_intake_status"),
            robot.get("field_evidence_real_material_owner_ack_intake_status"),
            robot.get("owner_ack_intake_status"),
            mobile.get("field_evidence_real_material_owner_ack_intake_status"),
            mobile.get("owner_ack_intake_status"),
            default="missing",
        )
    ).strip()


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


def _material_categories(source: dict[str, Any]) -> dict[str, list[str]]:
    # material_categories 是上一轮 ACK 分类的唯一可信来源。
    safe_copy = _dict(source, "safe_copy")
    owner_ack = _dict(source, "owner_acknowledgement")
    categories = source.get("material_categories")
    if not isinstance(categories, dict):
        categories = safe_copy.get("material_categories")
    if not isinstance(categories, dict):
        categories = owner_ack.get("material_categories")
    if not isinstance(categories, dict):
        categories = {}
    return {
        "accepted": _safe_list(categories.get("accepted")),
        "missing": _safe_list(categories.get("missing")),
        "rejected": _safe_list(categories.get("rejected")),
        "blocked": _safe_list(categories.get("blocked")),
    }


def _category_counts(categories: dict[str, list[str]]) -> dict[str, int]:
    # 计数只用于 review 摘要和 handoff，不代表真实材料通过率。
    return {name: len(categories.get(name, [])) for name in ("accepted", "missing", "rejected", "blocked")}


def _source_summary(source_state: dict[str, str], source: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    # source summary 是后续 Robot/mobile 的审计线索，不包含 raw ack packet。
    return {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")).strip(),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip(),
        "owner_ack_intake_status": _source_intake_status(source),
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
) -> tuple[str, str, list[str]]:
    # 决策优先级：无 source/unsupported -> rejected；unsafe -> rejected；
    # missing/blocked -> needs_more_evidence；全 accepted 且 ready 才 accepted。
    if source_state.get("load_issue"):
        return REJECTED, MISSING_SOURCE_STATUS, [source_state["load_issue"]]
    if source_state.get("schema_status") != "supported":
        return REJECTED, UNSUPPORTED_STATUS, ["unsupported_owner_ack_intake_schema_or_boundary"]
    if evidence_ref_mismatch:
        return REJECTED, MISMATCH_STATUS, ["evidence_ref_mismatch"]
    if source_summary.get("same_evidence_ref_required") is not True:
        return REJECTED, MISMATCH_STATUS, ["same_evidence_ref_required_not_true"]
    if not source_summary.get("source_is_software_proof_not_proven"):
        return REJECTED, UNSUPPORTED_STATUS, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if source_summary.get("unsafe_copy"):
        return REJECTED, REJECTED_SOURCE_STATUS, ["unsafe_or_sensitive_owner_ack_intake_copy"]

    source_status = str(source_summary.get("owner_ack_intake_status", ""))
    if source_status in (REJECTED_SOURCE_STATUS, UNSUPPORTED_SOURCE_STATUS, MISMATCH_SOURCE_STATUS):
        return REJECTED, REJECTED_SOURCE_STATUS, [f"source_owner_ack_intake_status:{source_status}"]
    if counts.get("rejected", 0) > 0 or "rejected" in source_status:
        return REJECTED, REJECTED_SOURCE_STATUS, ["owner_ack_rejected_material_categories_present"]
    if source_status == MISSING_ACK_STATUS or "missing" in source_status:
        return NEEDS_MORE_EVIDENCE, MISSING_ACK_STATUS, ["owner_acknowledgement_missing_or_pending"]
    if counts.get("missing", 0) > 0:
        return NEEDS_MORE_EVIDENCE, MISSING_ACK_STATUS, ["owner_ack_missing_material_categories_present"]
    if counts.get("blocked", 0) > 0:
        return NEEDS_MORE_EVIDENCE, MISSING_ACK_STATUS, ["owner_ack_blocked_material_categories_present"]
    if source_status == READY_SOURCE_STATUS and counts.get("accepted", 0) > 0:
        return ACCEPTED, READY_SOURCE_STATUS, ["owner_ack_categories_safe_for_structured_review_only"]
    return NEEDS_MORE_EVIDENCE, MISSING_ACK_STATUS, ["owner_ack_intake_not_ready_for_review_decision"]


def _next_required_evidence(decision: str, categories: dict[str, list[str]]) -> list[dict[str, Any]]:
    # 下一步 evidence 是人工/现场材料动作，不是机器人控制动作。
    if decision == ACCEPTED:
        return [
            {
                "owner": "Product Manager / OKR Owner",
                "action": "schedule_structured_owner_ack_review_without_marking_field_pass",
                "materials": categories.get("accepted", []),
            }
        ]
    if decision == NEEDS_MORE_EVIDENCE:
        return [
            {
                "owner": "field-owner",
                "action": "backfill_missing_or_blocked_owner_ack_categories_under_same_evidence_ref",
                "materials": categories.get("missing", []) + categories.get("blocked", []),
            }
        ]
    return [
        {
            "owner": "field-owner",
            "action": "resubmit_sanitized_same_evidence_ref_owner_ack_intake_without_unsafe_or_rejected_claims",
            "materials": categories.get("rejected", []) or list(intake.REQUIRED_CATEGORIES),
        }
    ]


def _owner_handoff(decision: str, reasons: list[str], evidence_ref: str, categories: dict[str, list[str]]) -> dict[str, Any]:
    # handoff 明确下一责任人与禁止声明，防止 accepted 被误读成现场通过。
    if decision == ACCEPTED:
        owner = "Product Manager / OKR Owner"
        action = "review owner ack categories later; keep not_proven"
    elif decision == NEEDS_MORE_EVIDENCE:
        owner = "field-owner"
        action = "backfill missing or blocked owner ack categories under the same safe evidence_ref"
    else:
        owner = "field-owner"
        action = "remove unsafe, rejected, mixed, raw, success, control, credential, path, or hardware-detail claims"
    return {
        "owner": owner,
        "action": action,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "decision_reasons": reasons,
        "accepted_materials": categories.get("accepted", []),
        "missing_materials": categories.get("missing", []),
        "rejected_materials": categories.get("rejected", []),
        "blocked_materials": categories.get("blocked", []),
        "not_delivery_result": True,
        "not_delivery_success": True,
    }


def _safe_phone_copy(decision: str, evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # phone copy 只说明状态与下一步，不暴露 raw artifact 或控制入口。
    return {
        "title": "现场真实材料 owner ack 复核决策",
        "review_decision": decision,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "message": "accepted 只表示 owner ack 分类可进入后续复核，仍不是现场通过或交付成功。",
        "decision_reasons": reasons,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "delivery_success": False,
    }


def _safe_copy(
    decision: str,
    decision_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    categories: dict[str, list[str]],
    counts: dict[str, int],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 建议消费面，字段稳定且全为短字段。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": "not_proven",
        "capability": CAPABILITY,
        "review_decision": decision,
        "decision_status": decision_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_ack_intake": source_summary,
        "decision_reasons": reasons,
        "material_category_counts": counts,
        "material_categories": categories,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "decision_enum": list(DECISIONS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    decision_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    categories: dict[str, list[str]],
    counts: dict[str, int],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 与 artifact 保持同一 decision，便于 Robot diagnostics safe alias。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "status": "not_proven",
        "capability": CAPABILITY,
        "review_decision": decision,
        "decision_status": decision_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_ack_intake": source_summary,
        "decision_reasons": reasons,
        "material_category_counts": counts,
        "material_categories": categories,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, evidence_ref, reasons),
        "safe_copy": safe_copy,
        "decision_enum": list(DECISIONS),
        "not_proven": ["not_proven"],
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_real_material_owner_ack_review_decision(
    owner_ack_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 owner-ack-intake safe source，生成 fail-closed review decision。"""
    source_payload, load_issue = _load_json(owner_ack_intake_json)
    source_raw = _find_source(source_payload) if source_payload else {}
    source_state = _source_status(load_issue, source_raw)
    source_ref = _source_evidence_ref(source_raw) if source_raw else ""
    requested_ref = material_pack._safe_ref(evidence_ref) or source_ref
    evidence_ref_mismatch = bool(evidence_ref and source_ref and requested_ref != source_ref)
    categories = _material_categories(source_raw) if source_raw else {"accepted": [], "missing": [], "rejected": [], "blocked": []}
    counts = _category_counts(categories)
    source_summary = _source_summary(source_state, source_raw, source_ref)
    decision, decision_status, reasons = _review_decision(source_state, source_summary, counts, evidence_ref_mismatch)
    owner_handoff = _owner_handoff(decision, reasons, requested_ref, categories)
    next_required_evidence = _next_required_evidence(decision, categories)
    safe_copy = _safe_copy(
        decision,
        decision_status,
        reasons,
        requested_ref,
        source_summary,
        categories,
        counts,
        owner_handoff,
        next_required_evidence,
    )
    summary = _summary_payload(
        decision,
        decision_status,
        reasons,
        requested_ref,
        source_summary,
        categories,
        counts,
        owner_handoff,
        next_required_evidence,
        safe_copy,
    )
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "status": "not_proven",
        "capability": CAPABILITY,
        "review_decision": decision,
        "decision_status": decision_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_owner_ack_intake": source_summary,
        "decision_reasons": reasons,
        "material_category_counts": counts,
        "material_categories": categories,
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "safe_phone_copy": _safe_phone_copy(decision, requested_ref, reasons),
        "safe_copy": safe_copy,
        "field_evidence_real_material_owner_ack_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "accepted_means": "accepted_owner_ack_review_decision_not_field_pass",
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
        "decision_enum": list(DECISIONS),
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
            payload["review_decision"] = REJECTED
            payload["decision_status"] = REJECTED_SOURCE_STATUS
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
    parser = argparse.ArgumentParser(description="Generate a field evidence real material owner ack review decision artifact")
    parser.add_argument("--owner-ack-intake-json", required=True, help="owner ack intake artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for review decision")
    parser.add_argument("--output", default="", help="optional owner ack review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional owner ack review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print owner ack review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_owner_ack_review_decision(
        args.owner_ack_intake_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_owner_ack_review_decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_ack_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
