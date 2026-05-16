#!/usr/bin/env python3
"""生成 route/task field retest result reconciliation artifact。

该 gate 只复账上一轮 result intake / session handoff / execution pack 或现场
result wrapper 的 JSON 元数据。它不读取 ROS graph、Nav2 runtime、真实日志、
硬件、外部云、真实手机/browser 或现场文件内容。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_result_intake as intake


# reconciliation 是 result intake 之后的 PC-side 复账契约，不复用上游 schema。
RECONCILIATION_SCHEMA = "trashbot.route_task_field_retest_result_reconciliation.v1"
RECONCILIATION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_reconciliation_summary.v1"
SCHEMA_VERSION = 1
RECONCILIATION_BOUNDARY = "software_proof_docker_route_task_field_retest_result_reconciliation_gate"

# 支持上一轮三类 gate 产物和现场回填 result wrapper；schema/boundary 不匹配时 fail closed。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_result_intake.v1",
    "trashbot.route_task_field_retest_result_intake_summary.v1",
    "trashbot.route_task_field_retest_session_handoff.v1",
    "trashbot.route_task_field_retest_session_handoff_summary.v1",
    "trashbot.route_task_field_retest_execution_pack.v1",
    "trashbot.route_task_field_retest_execution_pack_summary.v1",
    "trashbot.route_task_field_retest_result.v1",
    "trashbot.route_task_field_retest_result_summary.v1",
}
SOURCE_BOUNDARIES = {
    "software_proof_docker_route_task_field_retest_result_intake_gate",
    "software_proof_docker_route_task_field_retest_session_handoff_gate",
    "software_proof_docker_route_task_field_retest_execution_pack_gate",
    "",
}

# 八类现场结果材料是固定复账清单；缺一类也不能进入 ready。
REQUIRED_RESULT_MATERIALS = intake.REQUIRED_RESULT_MATERIALS

# not_proven 明确该 gate 只是 Docker/local 元数据复账，不是现场验收结论。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机生成的 artifact 可以稳定排序审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都转成 blocked artifact，避免无记录失败。
    if not path:
        return {}, "result_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "result_json_missing"
    except json.JSONDecodeError:
        return {}, "result_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "result_json_read_error"
    if not isinstance(payload, dict):
        return {}, "result_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段只接受 object，防止字符串伪装 nested JSON。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # 同一字段可能位于 artifact、summary、diagnostics 或 mobile summary。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把任意 raw input 当成可信来源。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_reconciliation",
        "route_task_field_retest_result_reconciliation_summary",
        "route_task_field_retest_result_intake",
        "route_task_field_retest_result_intake_summary",
        "route_task_field_retest_session_handoff",
        "route_task_field_retest_session_handoff_summary",
        "route_task_field_retest_execution_pack",
        "route_task_field_retest_execution_pack_summary",
        "route_task_field_retest_result",
        "route_task_field_retest_result_summary",
        "result_intake",
        "result_intake_summary",
        "result_artifact",
        "result_summary",
        "field_result",
        "field_result_summary",
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
    # 优先消费 schema 命中的嵌套对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 和 boundary 必须同时受支持，避免跨 gate 材料误入复账。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = intake._safe_text(source.get("schema", ""))
    boundary = intake._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是现场结果复账的主键，不能靠多个来源各自解释。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return intake._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_required(source: dict[str, Any]) -> Any:
    # 弱类型字符串不能通过；必须是 JSON boolean true，避免 wrapper 文案误放行。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return source.get(
        "same_evidence_ref_required",
        robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
    )


def _extract_materials(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 复用 intake 的白名单抽取，并补充 execution pack placeholder 字段。
    materials = intake._extract_materials(source)
    for holder in (source, _dict(source, "session_handoff"), _dict(source, "operator_handoff")):
        for key in ("required_result_materials", "required_field_materials", "material_placeholders", "material_paths"):
            if key not in holder:
                continue
            for fallback_key, raw_material in intake._iter_material_entries(holder.get(key)):
                name = intake._canonical_material(intake._material_name(raw_material, fallback_key))
                if name not in REQUIRED_RESULT_MATERIALS or name in materials:
                    continue
                # execution pack/handoff 只说明需要哪些材料，不能冒充已回填现场结果。
                materials[name] = {
                    "name": name,
                    "status": "placeholder_required_not_collected_by_this_gate",
                    "evidence_ref": _source_evidence_ref(source),
                    "placeholder": True,
                    "metadata": intake._safe_value(intake._material_metadata(raw_material)),
                }
    return materials


def _status(
    load_issue: str,
    source_status: dict[str, Any],
    evidence_ref: str,
    same_ref_required: Any,
    missing: list[str],
    mismatched_refs: list[str],
    placeholder_only: bool,
    unsafe_copy: bool,
    success_or_control_claim: bool,
) -> str:
    # fail closed 的顺序固定，保证危险输入不会被缺材料等低优先级原因遮住。
    if load_issue in {"result_json_bad_json", "result_json_read_error", "result_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_copy:
        return "blocked_unsafe_material_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    if mismatched_refs:
        return "blocked_same_evidence_ref_mismatch"
    if placeholder_only:
        return "blocked_placeholder_only_materials"
    if missing:
        return "blocked_missing_result_materials"
    return "ready_for_field_retest_result_reconciliation_not_proven"


def _mismatch_reasons(
    source_status: dict[str, Any],
    missing: list[str],
    mismatched_refs: list[str],
    same_ref_required: Any,
    unsafe_copy: bool,
    success_or_control_claim: bool,
    placeholder_only: bool,
) -> list[str]:
    # mismatch reasons 是 operator 修复输入的最短路径，不复制原始材料内容。
    reasons: list[str] = []
    if source_status["schema_status"] != "supported":
        reasons.append("source schema or evidence_boundary is not supported")
    if same_ref_required is not True:
        reasons.append("same_evidence_ref_required must be JSON boolean true")
    if missing:
        reasons.append("missing result materials: " + ", ".join(missing))
    if mismatched_refs:
        reasons.append("materials use a different evidence_ref: " + ", ".join(mismatched_refs))
    if placeholder_only:
        reasons.append("all detected result materials are placeholders only")
    if unsafe_copy:
        reasons.append("input contains unsafe material copy or raw local path")
    if success_or_control_claim:
        reasons.append("input contains success phrasing or primary action enablement")
    return reasons


def _same_ref_status(evidence_ref: str, missing: list[str], mismatched_refs: list[str], same_ref_required: Any) -> dict[str, Any]:
    # 这个状态给 diagnostics/mobile 只读展示，不代表真实 field pass。
    return {
        "required": True,
        "input_required_value": same_ref_required,
        "evidence_ref": evidence_ref,
        "status": "aligned" if evidence_ref and same_ref_required is True and not mismatched_refs else "blocked",
        "missing_materials": missing,
        "mismatched_materials": mismatched_refs,
    }


def _operator_next_steps(status: str, evidence_ref: str, missing: list[str], mismatched_refs: list[str]) -> list[str]:
    # 下一步只指导补齐材料和复跑 gate，不允许引导现场成功或手机放行动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_result_reconciliation_not_proven":
        return [
            f"Review reconciliation artifact for evidence_ref={ref} with Product/Robot owner.",
            "Keep Robot diagnostics and mobile/web read-only until terminal decision is separately accepted.",
            "Do not mark delivery complete from this software-proof reconciliation artifact.",
        ]
    steps = [f"Keep evidence_ref={ref} aligned across all eight result materials before rerun."]
    if missing:
        steps.append("Attach or repair missing material summaries: " + ", ".join(missing))
    if mismatched_refs:
        steps.append("Re-collect mismatched material summaries on the same evidence_ref: " + ", ".join(mismatched_refs))
    steps.append("Rerun route_task_field_retest_result_reconciliation.py after metadata is repaired.")
    return steps


def _rerun_summary(evidence_ref: str) -> dict[str, Any]:
    # rerun summary 固定在 PC gate 顺序，避免把设备、云或凭证命令写入 summary。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "evidence_ref": ref,
        "commands": [
            f"rerun route_task_field_retest_result_reconciliation.py --evidence-ref {ref}",
            "rerun route_task_terminal_completion_rehearsal.py only after reconciliation is accepted",
            "rerun route_task_terminal_review_decision.py only after terminal rehearsal is regenerated",
            "keep delivery_success=false and primary_actions_enabled=false until real review closes",
        ],
    }


def _field_callback_checklist(evidence_ref: str) -> list[str]:
    # checklist 保持 phone-safe，只要求回填事实和失败原因。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Confirm all eight field result summaries use evidence_ref={ref}.",
        "Summarize Nav2/fixed-route runtime metadata without copying raw log content.",
        "Include route completion signal and task record terminal branch with failure reason when blocked.",
        "Include door state, target floor confirmation, and human assistance note for elevator flow.",
        "Include dropoff/cancel branch and delivery result review input without success wording.",
        "Keep phone actions disabled; reconciliation is not a delivery success signal.",
    ]


def _phone_safe_summary(status: str, evidence_ref: str, missing: list[str], mismatch_reasons: list[str]) -> dict[str, Any]:
    # phone-safe summary 是白名单消费面，固定不携带 raw artifact 或材料正文。
    return {
        "schema": f"{RECONCILIATION_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "reconciliation_verdict": status,
        "evidence_boundary": RECONCILIATION_BOUNDARY,
        "evidence_ref": evidence_ref,
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    same_ref_status: dict[str, Any],
    missing: list[str],
    mismatch_reasons: list[str],
    operator_next_steps: list[str],
    rerun_summary: dict[str, Any],
    field_callback_checklist: list[str],
    phone_safe_summary: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": RECONCILIATION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": RECONCILIATION_BOUNDARY,
        "boundary": RECONCILIATION_BOUNDARY,
        "status": status,
        "reconciliation_verdict": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "operator_next_steps": operator_next_steps,
        "rerun_summary": rerun_summary,
        "field_callback_checklist": field_callback_checklist,
        "fail_closed_phone_safe_summary": phone_safe_summary,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_reconciliation(
    result_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 result/intake/handoff/execution-pack JSON，生成 fail-closed 复账结果。"""
    payload, load_issue = _load_json(result_json)
    source = _find_source(payload) if payload else {}
    requested_ref = intake._safe_ref(evidence_ref) or _source_evidence_ref(source)
    source_ref = _source_evidence_ref(source)
    same_ref_required = _same_ref_required(source) if source else True
    if evidence_ref and source_ref and requested_ref != source_ref:
        # CLI 传入的 evidence_ref 与输入不一致时，按同证据号硬约束失败。
        same_ref_required = False

    source_status = _source_status(load_issue, source)
    materials = _extract_materials(source) if source else {}
    missing = intake._missing_materials(materials)
    mismatched_refs = intake._mismatched_refs(materials, requested_ref)
    placeholder_only = intake._placeholder_only(materials)
    unsafe_copy = bool(payload) and (intake._has_forbidden_copy(source) or intake._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and intake._has_success_or_control_claim(source)
    status = _status(
        load_issue,
        source_status,
        requested_ref,
        same_ref_required,
        missing,
        mismatched_refs,
        placeholder_only,
        unsafe_copy,
        success_or_control_claim,
    )

    mismatch_reasons = _mismatch_reasons(
        source_status,
        missing,
        mismatched_refs,
        same_ref_required,
        unsafe_copy,
        success_or_control_claim,
        placeholder_only,
    )
    same_ref_status = _same_ref_status(requested_ref, missing, mismatched_refs, same_ref_required)
    next_steps = _operator_next_steps(status, requested_ref, missing, mismatched_refs)
    rerun_summary = _rerun_summary(requested_ref)
    callback = _field_callback_checklist(requested_ref)
    phone_safe = _phone_safe_summary(status, requested_ref, missing, mismatch_reasons)
    summary = _summary_payload(
        status,
        requested_ref,
        same_ref_status,
        missing,
        mismatch_reasons,
        next_steps,
        rerun_summary,
        callback,
        phone_safe,
    )

    artifact = {
        "schema": RECONCILIATION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": RECONCILIATION_BOUNDARY,
        "boundary": RECONCILIATION_BOUNDARY,
        "status": status,
        "reconciliation_verdict": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": same_ref_status,
        "source_result": {
            **source_status,
            "schema": intake._safe_text(source.get("schema", "")),
            "evidence_boundary": intake._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
            "status": intake._safe_text(source.get("status", "")),
            "evidence_ref": source_ref,
            "same_evidence_ref_required": same_ref_required,
            "unsafe_copy": bool(unsafe_copy),
            "success_or_control_claim": bool(success_or_control_claim),
        },
        "result_materials": {
            name: {
                "status": material["status"],
                "evidence_ref": material["evidence_ref"],
                "placeholder": material["placeholder"],
                "metadata": material["metadata"],
            }
            for name, material in sorted(materials.items())
        },
        "missing_materials": missing,
        "mismatch_reasons": mismatch_reasons,
        "operator_next_steps": next_steps,
        "rerun_summary": rerun_summary,
        "field_callback_checklist": callback,
        "fail_closed_phone_safe_summary": phone_safe,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "real_field_file_content",
            "hardware_transport",
            "hardware_feedback",
            "real_phone_or_browser",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "boundary_note": (
            "route_task_field_retest_result_reconciliation is software_proof_docker only; "
            "not_proven; delivery_success=false; primary_actions_enabled=false"
        ),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = intake._safe_value(artifact)
    summary = intake._safe_value(summary)
    if intake._has_forbidden_copy(artifact) or intake._has_forbidden_copy(summary):
        # 最终防线：若输出仍含禁词，强制降级并保留 fail-closed flags。
        artifact["status"] = "blocked_unsafe_material_copy"
        artifact["reconciliation_verdict"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["reconciliation_verdict"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["reconciliation_verdict"] = "blocked_unsafe_material_copy"
        summary["status"] = "blocked_unsafe_material_copy"
        summary["reconciliation_verdict"] = "blocked_unsafe_material_copy"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时交给 stdout 展示 artifact。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，方便 Docker、PC 和 focused unittest 共用同一入口。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result reconciliation artifact")
    parser.add_argument("--result-json", required=True, help="result intake, handoff, execution pack, result, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this reconciliation")
    parser.add_argument("--output", default="", help="optional reconciliation artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional reconciliation summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print reconciliation artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_reconciliation(args.result_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result reconciliation: reconciliation_file:{intake._safe_ref(args.output)}")
        if args.summary_output:
            print(f"reconciliation_summary_file: {intake._safe_ref(args.summary_output)}")
        print(f"reconciliation_verdict: {artifact['reconciliation_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
