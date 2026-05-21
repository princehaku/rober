#!/usr/bin/env python3
"""生成 field evidence real material response review handoff artifact。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_real_material_response_review_decision as decision
import route_task_field_retest_material_pack as material_pack


HANDOFF_SCHEMA = "trashbot.field_evidence_real_material_response_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_response_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_field_evidence_real_material_response_review_handoff_gate"

# 只消费上一轮 review-decision 的安全 surface，防止 raw response 材料越级进入 handoff。
SOURCE_SCHEMAS = {decision.DECISION_SCHEMA, decision.DECISION_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {decision.DECISION_BOUNDARY}

READY_HANDOFF = "ready_for_field_owner_handoff_not_proven"
BACKFILL_HANDOFF = "needs_material_backfill_handoff_not_proven"
REJECTED_HANDOFF = "rejected_unsafe_or_mixed_handoff_not_proven"
BLOCKED_HANDOFF = "blocked_real_environment_unavailable_handoff_not_proven"

# handoff 仍是 software proof，所以所有可能被误读成完成的声明都放入 blocked_claims。
BLOCKED_CLAIMS = tuple(
    dict.fromkeys(
        list(decision.BLOCKED_CLAIMS)
        + [
            "field_owner_handoff_as_field_pass",
            "response_review_handoff_as_delivery_success",
            "response_review_handoff_as_pr5_resolution",
            "response_review_handoff_as_hil_or_wave_rover_proof",
        ]
    )
)

BOUNDARY_NOTE = (
    "field_evidence_real_material_response_review_handoff; "
    "software_proof_docker_field_evidence_real_material_response_review_handoff_gate; "
    "ready_for_field_owner_handoff_not_proven; "
    "needs_material_backfill_handoff_not_proven; "
    "rejected_unsafe_or_mixed_handoff_not_proven; "
    "blocked_real_environment_unavailable_handoff_not_proven; "
    "source=software_proof; status=not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "same_evidence_ref_required=true"
)

# 设计约束 01：handoff 只读取 review decision artifact/summary/Robot alias。
# 设计约束 02：schema 与 evidence_boundary 必须同时匹配上一轮 decision。
# 设计约束 03：source=software_proof、not_proven 与 false flags 不可放松。
# 设计约束 04：ready 只表示可交给 field owner，不表示现场通过。
# 设计约束 05：backfill 只列缺失材料，不能自动补齐或触发机器人动作。
# 设计约束 06：rejected/unsafe/mixed ref 统一 fail closed，避免误收材料。
# 设计约束 07：blocked 表示真实环境或 source 不可用，不表示复跑完成。
# 设计约束 08：same_evidence_ref_required 必须是 JSON boolean true。
# 设计约束 09：CLI 指定 evidence_ref 与 source 不一致时必须 rejected。
# 设计约束 10：Robot alias 只作为 safe alias，不提升证据等级。
# 设计约束 11：safe copy 只给只读消费者，不启用 Start/Confirm/Cancel。
# 设计约束 12：raw ROS topic、serial、UART、WAVE ROVER 细节不得进入输出。
# 设计约束 13：凭证、本机路径、checksum、traceback 不得进入输出。
# 设计约束 14：success/control claim 命中后必须 rejected fail-closed。
# 设计约束 15：summary 是 Robot/mobile 的稳定消费面，不搬运完整 source。
# 设计约束 16：最终输出递归脱敏，防止新增字段绕过安全扫描。
# 设计约束 17：blocked artifact 也 exit 0，便于 Docker-only sprint 留痕。
# 设计约束 18：所有技术注释使用中文，解释保守边界和取舍。


def _utc_now() -> str:
    # UTC 便于 PC gate、Docker artifact 和 sprint 文档按统一时间线归档。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺 source 时不能构造 ready handoff，必须显式 blocked。
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
    # 只信任 object wrapper，字符串化 JSON 不作为 canonical safe source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy、Robot alias 的字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 只输出短文本列表，避免把完整上游 artifact 复制给现场 owner。
    if isinstance(value, list):
        return [material_pack._safe_text(item) for item in value[:limit] if material_pack._safe_text(item)]
    if isinstance(value, tuple):
        return [material_pack._safe_text(item) for item in list(value)[:limit] if material_pack._safe_text(item)]
    if value in (None, ""):
        return []
    text = material_pack._safe_text(value)
    return [text] if text else []


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 递归范围限定在已知 safe wrapper，避免 raw field material 被误当 source。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_response_review_handoff",
        "field_evidence_real_material_response_review_handoff_summary",
        "field_evidence_real_material_response_review_decision",
        "field_evidence_real_material_response_review_decision_summary",
        "robot_diagnostics_field_evidence_real_material_response_review_decision_summary",
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
    # schema 命中 review decision 时才可信；否则保留顶层用于 unsupported 解释。
    for candidate in _candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_state(load_issue: str, source: dict[str, Any]) -> dict[str, str]:
    # schema 与 boundary 必须同时命中，防止其他 gate 的 decision 越权交接。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是 decision 到 handoff 的唯一串联主键。
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


def _source_review_decision(source: dict[str, Any]) -> str:
    # handoff 不重新解释 material_responses，只消费上一轮 review_decision。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return material_pack._safe_text(
        _first_text(
            source.get("review_decision"),
            safe_copy.get("review_decision"),
            robot.get("review_decision"),
            mobile.get("review_decision"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 字符串 true 不接受，避免弱 typing 绕过同证据号要求。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    return source.get(
        "same_evidence_ref_required",
        safe_copy.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True))),
    )


def _is_software_proof_not_proven(source: dict[str, Any]) -> bool:
    # 五个边界字段同时满足，才能把 decision 继续转换为 handoff。
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
    # 禁词、路径、凭证、硬件细节、success/control claim 都必须 fail closed。
    return (
        material_pack._has_forbidden_copy(value)
        or material_pack._has_raw_path_copy(value)
        or material_pack._has_success_or_control_claim(value)
    )


def _source_materials(source: dict[str, Any], key: str) -> list[str]:
    # 材料列表优先取 summary 短字段，缺失时从 safe_copy 兜底。
    safe_copy = _dict(source, "safe_copy")
    return _safe_list(source.get(key) if key in source else safe_copy.get(key))


def _source_summary(source_state: dict[str, str], source: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    # source summary 是审计线索，不包含完整上游 artifact。
    return {
        **source_state,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "review_decision": _source_review_decision(source),
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": _same_ref_required(source),
        "source_is_software_proof_not_proven": _is_software_proof_not_proven(source),
        "unsafe_copy": bool(source) and _unsafe_copy(source),
    }


def _handoff_status(
    source_state: dict[str, str],
    source_summary: dict[str, Any],
    evidence_ref_mismatch: bool,
) -> tuple[str, list[str]]:
    # 决策顺序先检查 source 安全性，再做 review_decision 到 handoff 的映射。
    if source_state.get("load_issue"):
        return BLOCKED_HANDOFF, [source_state["load_issue"]]
    if source_state.get("schema_status") != "supported":
        return REJECTED_HANDOFF, ["unsupported_review_decision_schema_or_boundary"]
    if evidence_ref_mismatch:
        return REJECTED_HANDOFF, ["evidence_ref_mismatch"]
    if source_summary.get("same_evidence_ref_required") is not True:
        return REJECTED_HANDOFF, ["same_evidence_ref_required_not_true"]
    if not source_summary.get("source_is_software_proof_not_proven"):
        return REJECTED_HANDOFF, ["source_not_software_proof_not_proven_or_false_flags_changed"]
    if source_summary.get("unsafe_copy"):
        return REJECTED_HANDOFF, ["unsafe_or_sensitive_review_decision_copy"]

    review_decision = str(source_summary.get("review_decision", ""))
    if review_decision == decision.ACCEPTED_DECISION:
        return READY_HANDOFF, ["review_decision_ready_for_field_owner_handoff_only"]
    if review_decision == decision.BACKFILL_DECISION:
        return BACKFILL_HANDOFF, ["review_decision_requires_material_backfill"]
    if review_decision == decision.REJECTED_DECISION:
        return REJECTED_HANDOFF, ["review_decision_rejected_unsafe_or_mixed"]
    if review_decision in (decision.BLOCKED_DECISION, decision.MISSING_SOURCE_DECISION):
        return BLOCKED_HANDOFF, ["review_decision_blocked_real_environment_or_source_unavailable"]
    return REJECTED_HANDOFF, ["unknown_review_decision_status"]


def _next_required_real_materials(source: dict[str, Any], handoff_status: str) -> list[str]:
    # ready 仍要求 field owner 后续补真实材料；不是算法或机器人自动完成。
    missing = _source_materials(source, "missing_materials")
    blocked = _source_materials(source, "blocked_materials")
    rejected = _source_materials(source, "rejected_materials")
    if handoff_status == BACKFILL_HANDOFF:
        return missing or list(decision.intake.REQUIRED_MATERIALS)
    if handoff_status == BLOCKED_HANDOFF:
        return blocked or list(decision.intake.REQUIRED_MATERIALS)
    if handoff_status == REJECTED_HANDOFF:
        return rejected or list(decision.intake.REQUIRED_MATERIALS)
    return list(decision.intake.REQUIRED_MATERIALS)


def _field_owner_handoff(handoff_status: str, reasons: list[str], evidence_ref: str, materials: list[str]) -> dict[str, Any]:
    # owner_handoff 只描述人工材料动作，明确禁止机器人控制动作。
    if handoff_status == READY_HANDOFF:
        action = "field_owner_review_sanitized_response_decision_without_marking_field_pass"
    elif handoff_status == BACKFILL_HANDOFF:
        action = "backfill_missing_required_materials_under_same_evidence_ref"
    elif handoff_status == REJECTED_HANDOFF:
        action = "resubmit_safe_same_evidence_ref_decision_without_unsafe_mixed_success_or_control_claims"
    else:
        action = "collect_real_environment_materials_or_valid_review_decision_before_handoff_can_continue"
    return {
        "owner": "field-owner",
        "action": action,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "handoff_reasons": reasons,
        "next_required_real_materials": materials,
        "not_delivery_result": True,
        "not_delivery_success": True,
        "safe_to_control": False,
    }


def _rerun_backfill_guidance(handoff_status: str, evidence_ref: str, materials: list[str]) -> dict[str, Any]:
    # guidance 给人复跑/补料路径，不给脚本自动执行控制命令。
    return {
        "required": handoff_status != READY_HANDOFF,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "materials": materials,
        "command_template": (
            "python3 pc-tools/evidence/field_evidence_real_material_response_review_decision.py "
            "--response-intake-json <same_ref_response_intake.json> "
            f"--evidence-ref {evidence_ref} --once-json"
        ),
        "guidance": "rerun_or_backfill_only_with_sanitized_same_evidence_ref_materials",
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def _safe_phone_copy(handoff_status: str, evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # phone copy 是只读提示；不能被前端误用为按钮启用条件。
    return {
        "title": "现场真实材料响应复核交接",
        "handoff_status": handoff_status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "message": "ready 只表示可交给 field owner，仍不是现场通过或交付成功。",
        "blocked_reason": ";".join(reasons),
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "delivery_success": False,
    }


def _safe_copy(
    handoff_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    owner_handoff: dict[str, Any],
    materials: list[str],
    guidance: dict[str, Any],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 的 canonical 消费面，保持短字段和 false flags。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": "not_proven",
        "handoff_status": handoff_status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "blocked_reason": ";".join(reasons),
        "missing_required_materials": materials if handoff_status == BACKFILL_HANDOFF else [],
        "next_required_evidence": materials,
        "field_owner_handoff": owner_handoff,
        "rerun_backfill_guidance": guidance,
        "safe_phone_copy": _safe_phone_copy(handoff_status, evidence_ref, reasons),
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    handoff_status: str,
    reasons: list[str],
    evidence_ref: str,
    source_summary: dict[str, Any],
    owner_handoff: dict[str, Any],
    materials: list[str],
    guidance: dict[str, Any],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 镜像关键 artifact 字段，方便 Robot diagnostics safe alias 消费。
    return {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "status": "not_proven",
        "handoff_status": handoff_status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "blocked_reason": ";".join(reasons),
        "missing_required_materials": materials if handoff_status == BACKFILL_HANDOFF else [],
        "next_required_evidence": materials,
        "field_owner_handoff": owner_handoff,
        "rerun_backfill_guidance": guidance,
        "safe_phone_copy": _safe_phone_copy(handoff_status, evidence_ref, reasons),
        "safe_copy": safe_copy,
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": ["not_proven"],
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_real_material_response_review_handoff(
    review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review-decision safe source，生成 fail-closed field-owner handoff。"""
    source_payload, load_issue = _load_json(review_decision_json)
    source_raw = _find_source(source_payload) if source_payload else {}
    state = _source_state(load_issue, source_raw)
    source_ref = _source_evidence_ref(source_raw) if source_raw else ""
    requested_ref = material_pack._safe_ref(evidence_ref) or source_ref
    mismatch = bool(evidence_ref and source_ref and requested_ref != source_ref)
    source_summary = _source_summary(state, source_raw, source_ref)
    handoff_status, reasons = _handoff_status(state, source_summary, mismatch)
    materials = _next_required_real_materials(source_raw, handoff_status)
    owner_handoff = _field_owner_handoff(handoff_status, reasons, requested_ref, materials)
    guidance = _rerun_backfill_guidance(handoff_status, requested_ref, materials)
    safe_copy = _safe_copy(handoff_status, reasons, requested_ref, source_summary, owner_handoff, materials, guidance)
    summary = _summary_payload(handoff_status, reasons, requested_ref, source_summary, owner_handoff, materials, guidance, safe_copy)
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "status": "not_proven",
        "handoff_status": handoff_status,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "field_owner_handoff": owner_handoff,
        "next_required_evidence": materials,
        "missing_required_materials": materials if handoff_status == BACKFILL_HANDOFF else [],
        "blocked_reason": ";".join(reasons),
        "rerun_backfill_guidance": guidance,
        "safe_phone_copy": _safe_phone_copy(handoff_status, requested_ref, reasons),
        "safe_copy": safe_copy,
        "field_evidence_real_material_response_review_handoff_summary": summary,
        "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
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
        # 最后一层防线：脱敏后仍有禁词时维持 false flags 并切到 rejected。
        for payload in (artifact, summary):
            payload["status"] = "not_proven"
            payload["handoff_status"] = REJECTED_HANDOFF
            payload["blocked_reason"] = "unsafe_copy_after_sanitization"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出路径可选；指定时自动创建目录，方便 sprint artifact 落盘。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 不依赖 ROS 或硬件，保持 PC/Docker-only 围栏可重复执行。
    parser = argparse.ArgumentParser(description="Generate a field evidence real material response review handoff artifact")
    parser.add_argument("--review-decision-json", required=True, help="review decision artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref for review handoff")
    parser.add_argument("--output", default="", help="optional review handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_response_review_handoff(
        args.review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_response_review_handoff: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"response_review_handoff_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
