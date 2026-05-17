#!/usr/bin/env python3
"""生成 route/task field retest result backfill review decision artifact。

该 gate 只读取上一轮 acceptance backfill artifact / summary / wrapper，并把
accepted / missing / rejected material 状态转成 PC 侧 review decision、owner
handoff、next required evidence 与 rerun commands。它不读取 raw upstream artifact，
不扫描材料目录，也不访问 ROS2、Nav2、硬件、外部云、真实手机/browser 或现场环境。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as material_pack
import route_task_field_retest_result_acceptance_backfill as backfill


# review decision 是 acceptance backfill 后的 PC 复核契约，不能复用上游 schema。
DECISION_SCHEMA = "trashbot.route_task_field_retest_result_backfill_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate"

# 只允许上一轮 acceptance backfill artifact / summary；wrapper 只能包住这些 schema。
SOURCE_SCHEMAS = {backfill.BACKFILL_SCHEMA, backfill.BACKFILL_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {backfill.BACKFILL_BOUNDARY}
READY_BACKFILL_STATUS = "ready_for_field_retest_result_acceptance_backfill_not_proven"

# 本 gate 仍然只证明 PC 侧材料复核状态，不证明现场、硬件、手机或云能力。
NOT_PROVEN = material_pack.NOT_PROVEN

# rg 围栏依赖这些 literal，人工复盘也能快速识别证据边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "accepted_materials; missing_materials; rejected_materials; owner_handoff; "
    "next_required_evidence; rerun_commands"
)


def _utc_now() -> str:
    # UTC 时间便于 Docker-only 主机和后续 sprint artifact 按时间线复盘。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常也要输出 blocked artifact，避免 review decision gate 静默缺席。
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
    # artifact、summary、safe_copy 和 nested wrapper 的字段位置不完全一致。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游可能给 list 或单值；输出限制数量，避免复制完整上游 artifact。
    if isinstance(value, list):
        return [material_pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把 raw upstream artifact 或任意 payload 当成 backfill。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_backfill_review_decision",
        "route_task_field_retest_result_backfill_review_decision_summary",
        "route_task_field_retest_result_acceptance_backfill",
        "route_task_field_retest_result_acceptance_backfill_summary",
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
    # schema 命中时优先返回嵌套对象；否则保留顶层用于 unsupported 诊断。
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
    # safe evidence_ref 是 backfill 与 review decision 串联的唯一主键。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    owner_handoff = _dict(source, "owner_handoff")
    return material_pack._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            owner_handoff.get("evidence_ref"),
            default="",
        )
    )


def _source_backfill_status(source: dict[str, Any]) -> str:
    # 只有 ready_not_proven 的 acceptance backfill 能进入 review accepted 分支。
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
        "required_count": int(completeness.get("required_count", len(backfill.REQUIRED_RESULT_MATERIALS)) or 0),
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
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
        return any(_has_true_control_flag(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(item) for item in value)
    return False


def _status(
    load_issue: str,
    source_status: dict[str, Any],
    source_backfill_status: str,
    evidence_ref: str,
    source_ref: str,
    same_ref_required: Any,
    requested_ref: str,
    material_status: dict[str, Any],
    alignment: dict[str, Any],
    unsafe_source: bool,
    success_or_control_claim: bool,
) -> str:
    # fail closed 顺序固定：输入可信性和安全边界优先于普通材料缺口。
    if load_issue in {"acceptance_backfill_json_bad_json", "acceptance_backfill_json_read_error", "acceptance_backfill_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result_acceptance_backfill"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if requested_ref and source_ref and requested_ref != source_ref:
        return "blocked_same_evidence_ref_mismatch"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_source:
        return "blocked_unsafe_copy"
    if success_or_control_claim:
        return "blocked_success_or_control_claim"
    if source_backfill_status != READY_BACKFILL_STATUS:
        return "blocked_acceptance_backfill_not_ready"
    if alignment["status"] != "aligned":
        return "blocked_same_evidence_ref_mismatch"
    if material_status["missing_materials"]:
        return "blocked_missing_materials"
    if material_status["rejected_materials"]:
        return "blocked_rejected_materials"
    if material_status["accepted_count"] != material_status["required_count"] or not material_status["is_complete"]:
        return "blocked_material_completeness_unknown"
    return "ready_for_field_retest_result_backfill_review_decision_not_proven"


def _review_decision(status: str, material_status: dict[str, Any]) -> dict[str, Any]:
    # review decision 只给 PC/owner 下一步，不允许表达 delivery pass。
    if status == "ready_for_field_retest_result_backfill_review_decision_not_proven":
        decision = "accepted_for_owner_review_not_proven"
        reason = "all acceptance backfill materials are accepted under the same evidence_ref"
    elif material_status["missing_materials"]:
        decision = "missing_materials_before_review"
        reason = "one or more required acceptance backfill materials are missing"
    elif material_status["rejected_materials"]:
        decision = "rejected_materials_before_review"
        reason = "one or more acceptance backfill materials were rejected by the upstream gate"
    else:
        decision = "blocked_before_review"
        reason = status
    return {
        "decision": decision,
        "status": status,
        "reason": reason,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(status: str, evidence_ref: str, material_status: dict[str, Any]) -> list[str]:
    # next evidence 是 PC/owner 材料修复清单，不是机器人动作指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_result_backfill_review_decision_not_proven":
        return [
            f"Product/Robot owner review of accepted backfill summary for evidence_ref={ref}",
            "real route/elevator field pass evidence remains required outside this Docker-only gate",
            "keep delivery_success=false and primary_actions_enabled=false until field review closes",
        ]
    required: list[str] = []
    required.extend([f"provide missing material: {name} for evidence_ref={ref}" for name in material_status["missing_materials"]])
    required.extend([f"repair rejected material: {name} for evidence_ref={ref}" for name in material_status["rejected_materials"]])
    if not required:
        required.append(f"rerun acceptance backfill with supported schema, ready status, and evidence_ref={ref}")
    return required


def _owner_handoff(status: str, evidence_ref: str, material_status: dict[str, Any], next_required_evidence: list[str]) -> dict[str, Any]:
    # handoff 只交给 owner 复核和材料修复，不给 mobile/Robot 开控制权限。
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": status,
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "material_status": material_status["status"],
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "next_required_evidence": next_required_evidence,
        "next_action": "review accepted backfill summary" if not material_status["missing_materials"] and not material_status["rejected_materials"] else "repair missing or rejected backfill materials",
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py --acceptance-packet-json <acceptance_packet.json> --material-dir <material_dir> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py --acceptance-backfill-json <acceptance_backfill.json> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field review closes",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    lineage: dict[str, str],
    material_status: dict[str, Any],
    review_decision: dict[str, Any],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "review_decision": review_decision,
        "material_status": material_status["status"],
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "evidence_boundary": DECISION_BOUNDARY,
        "evidence_ref": evidence_ref,
        "safe_lineage": lineage,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    lineage: dict[str, str],
    material_status: dict[str, Any],
    review_decision: dict[str, Any],
    owner_handoff: dict[str, Any],
    next_required_evidence: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "safe_lineage": lineage,
        "review_decision": review_decision,
        "material_status": material_status["status"],
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_backfill_review_decision(
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
    source_status = _source_status(load_issue, source)
    source_backfill_status = _source_backfill_status(source) if source else "missing"
    material_status = _material_status(source) if source else {
        "status": "unknown",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "accepted_count": 0,
        "required_count": len(backfill.REQUIRED_RESULT_MATERIALS),
        "is_complete": False,
        "gap_count": 0,
        "rejected_reasons": {},
    }
    alignment = _alignment_status(source) if source else {"required": True, "status": "missing", "mismatched_materials": [], "missing_evidence_ref_materials": []}
    unsafe_source = bool(payload) and (material_pack._has_forbidden_copy(source) or material_pack._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and (material_pack._has_success_or_control_claim(source) or _has_true_control_flag(source))
    status = _status(
        load_issue,
        source_status,
        source_backfill_status,
        effective_ref,
        source_ref,
        same_ref_required,
        requested_ref,
        material_status,
        alignment,
        unsafe_source,
        success_or_control_claim,
    )

    lineage = _source_lineage(source)
    review_decision = _review_decision(status, material_status)
    next_required_evidence = _next_required_evidence(status, effective_ref, material_status)
    owner_handoff = _owner_handoff(status, effective_ref, material_status, next_required_evidence)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_status,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": source_backfill_status,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "same_evidence_ref_alignment": alignment,
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(status, effective_ref, lineage, material_status, review_decision, owner_handoff, next_required_evidence, rerun_commands)
    summary = _summary_payload(
        status,
        effective_ref,
        source_summary,
        lineage,
        material_status,
        review_decision,
        owner_handoff,
        next_required_evidence,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": status,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "safe_lineage": lineage,
        "review_decision": review_decision,
        "material_status": material_status["status"],
        "material_status_detail": material_status,
        "accepted_materials": material_status["accepted_materials"],
        "missing_materials": material_status["missing_materials"],
        "rejected_materials": material_status["rejected_materials"],
        "owner_handoff": owner_handoff,
        "next_required_evidence": next_required_evidence,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_upstream_artifact",
            "material_dir_scan",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
            "route_elevator_field_pass",
            "hardware_transport",
            "hardware_feedback",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_phone_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if material_pack._has_forbidden_copy(artifact) or material_pack._has_forbidden_copy(summary):
        # 最终防线：输出仍含禁词时强制降级，并保留 fail-closed flags。
        artifact["status"] = "blocked_unsafe_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_copy"
        summary["status"] = "blocked_unsafe_copy"
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result backfill review decision artifact")
    parser.add_argument("--acceptance-backfill-json", required=True, help="acceptance backfill artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review decision gate")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_backfill_review_decision(
        args.acceptance_backfill_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result backfill review decision: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"backfill_review_decision_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"backfill_review_decision_status: {artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
