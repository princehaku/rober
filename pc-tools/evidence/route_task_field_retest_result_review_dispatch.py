#!/usr/bin/env python3
"""生成 route/task field retest result review dispatch artifact。

该 gate 只读取上一轮 result backfill review decision artifact / summary /
compatible wrapper，并把 PC 复核结果转成现场派发清单。它不读取 raw upstream
artifact，不扫描材料目录，也不访问 ROS2、Nav2、硬件、外部云、真实手机/browser
或现场环境。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as material_pack
import route_task_field_retest_result_backfill_review_decision as review_decision


# review dispatch 是 review decision 之后的 PC 现场派发契约，不能复用上游 schema。
DISPATCH_SCHEMA = "trashbot.route_task_field_retest_result_review_dispatch.v1"
DISPATCH_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_review_dispatch_summary.v1"
SCHEMA_VERSION = 1
DISPATCH_BOUNDARY = "software_proof_docker_route_task_field_retest_result_review_dispatch_gate"

# 输入只允许上一轮 review decision artifact / summary；wrapper 只能包住这些 schema。
SOURCE_SCHEMAS = {review_decision.DECISION_SCHEMA, review_decision.DECISION_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {review_decision.DECISION_BOUNDARY}
READY_REVIEW_STATUS = "ready_for_field_retest_result_backfill_review_decision_not_proven"

# 继续沿用材料链路的真实能力缺口，避免派发 artifact 被误读为现场通过。
NOT_PROVEN = material_pack.NOT_PROVEN

# rg 围栏依赖这些 literal，人工复盘也能快速识别输出边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_result_review_dispatch; "
    "software_proof_docker_route_task_field_retest_result_review_dispatch_gate; "
    "accepted_materials; missing_materials; rejected_materials; owner_work_orders; "
    "callback_packet_requirements; rerun_commands; same_evidence_ref_required=true; "
    "safe_copy; not_proven; delivery_success=false; primary_actions_enabled=false"
)


def _utc_now() -> str:
    # UTC 时间让 Docker-only 主机上的派发 artifact 可以稳定排序审计。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常也要输出 blocked artifact，避免 dispatch gate 静默缺席。
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


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 上游可能给 list 或单值；输出限制数量，避免复制完整上游 artifact。
    if isinstance(value, list):
        return [material_pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把 raw upstream artifact 或任意 payload 当成 review decision。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_review_dispatch",
        "route_task_field_retest_result_review_dispatch_summary",
        "route_task_field_retest_result_backfill_review_decision",
        "route_task_field_retest_result_backfill_review_decision_summary",
        "review_decision",
        "review_decision_summary",
        "source_review_decision",
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
    # schema 与 boundary 必须同时白名单化，防止跨 gate artifact 被误派发。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # same evidence_ref 是 review decision 到 dispatch 派发的唯一主键。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_ref(
        _first_text(
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
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


def _source_review_status(source: dict[str, Any]) -> str:
    # 只有 ready_not_proven 的 review decision 能进入 dispatch ready 分支。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("status"),
            robot.get("status"),
            mobile.get("status"),
            safe_copy.get("status"),
            default="missing",
        )
    )


def _source_review_decision(source: dict[str, Any]) -> dict[str, Any]:
    # review_decision 只复制上游安全化短字段，不追 raw upstream artifact。
    decision = _dict(source, "review_decision")
    safe_copy_decision = _dict(_dict(source, "safe_copy"), "review_decision")
    return material_pack._safe_value(decision or safe_copy_decision)


def _material_categories(source: dict[str, Any]) -> dict[str, list[str]]:
    # material categories 是现场派发分组，保持 accepted/missing/rejected 三类稳定字段。
    safe_copy = _dict(source, "safe_copy")
    return {
        "accepted_materials": _safe_list(source.get("accepted_materials") or safe_copy.get("accepted_materials")),
        "missing_materials": _safe_list(source.get("missing_materials") or safe_copy.get("missing_materials")),
        "rejected_materials": _safe_list(source.get("rejected_materials") or safe_copy.get("rejected_materials")),
    }


def _lineage(source: dict[str, Any]) -> dict[str, str]:
    # lineage 只用于排查来源，不允许放 raw path、topic、串口或凭证。
    safe_lineage = _dict(source, "safe_lineage")
    lineage = {
        "source_review_decision_schema": material_pack._safe_text(source.get("schema", "")),
        "source_review_decision_status": _source_review_status(source),
    }
    for key, value in safe_lineage.items():
        text = material_pack._safe_text(value)
        if text:
            lineage[f"review_decision_{material_pack._safe_text(key)}"] = text
    return lineage


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
    source_review_status: str,
    evidence_ref: str,
    source_ref: str,
    same_ref_required: Any,
    requested_ref: str,
    categories: dict[str, list[str]],
    unsafe_source: bool,
    success_or_control_claim: bool,
) -> str:
    # fail closed 顺序固定：输入可信性和安全边界优先于普通材料缺口。
    if load_issue in {"review_decision_json_bad_json", "review_decision_json_read_error", "review_decision_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result_backfill_review_decision"
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
    if source_review_status != READY_REVIEW_STATUS:
        return "blocked_review_decision_not_ready"
    if categories["missing_materials"]:
        return "blocked_missing_materials"
    if categories["rejected_materials"]:
        return "blocked_rejected_materials"
    if not categories["accepted_materials"]:
        return "blocked_missing_accepted_materials"
    return "ready_for_field_retest_result_review_dispatch_not_proven"


def _owner_work_orders(status: str, evidence_ref: str, categories: dict[str, list[str]]) -> list[dict[str, Any]]:
    # work orders 是现场准备清单，不是机器人控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    orders = [
        {
            "owner": "Autonomy Algorithm Engineer",
            "work_order": "stage accepted route/elevator result materials for PC-side dispatch review",
            "evidence_ref": ref,
            "materials": categories["accepted_materials"],
            "status": "ready_not_proven" if status == "ready_for_field_retest_result_review_dispatch_not_proven" else "blocked",
        },
        {
            "owner": "Robot Platform Engineer",
            "work_order": "prepare read-only diagnostics handoff for same evidence_ref without enabling primary actions",
            "evidence_ref": ref,
            "materials": categories["accepted_materials"],
            "status": "metadata_only",
        },
        {
            "owner": "Product Manager / OKR Owner",
            "work_order": "confirm callback packet completeness before any real field rerun claim",
            "evidence_ref": ref,
            "materials": categories["accepted_materials"],
            "status": "not_proven_review_required",
        },
    ]
    if categories["missing_materials"] or categories["rejected_materials"]:
        orders.append(
            {
                "owner": "Autonomy Algorithm Engineer",
                "work_order": "repair missing or rejected review materials before dispatch",
                "evidence_ref": ref,
                "missing_materials": categories["missing_materials"],
                "rejected_materials": categories["rejected_materials"],
                "status": "blocked",
            }
        )
    return material_pack._safe_value(orders)


def _callback_packet_requirements(evidence_ref: str, categories: dict[str, list[str]]) -> list[dict[str, Any]]:
    # callback packet 只描述现场回传包要求，不包含 raw log、绝对路径或控制 topic。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": "same_evidence_ref_manifest",
            "required": True,
            "evidence_ref": ref,
            "safe_copy_only": True,
            "description": "callback packet must use the same evidence_ref across all accepted materials",
        },
        {
            "name": "accepted_materials_index",
            "required": True,
            "evidence_ref": ref,
            "safe_copy_only": True,
            "materials": categories["accepted_materials"],
        },
        {
            "name": "field_retest_result_callback",
            "required": True,
            "evidence_ref": ref,
            "safe_copy_only": True,
            "description": "future field callback must keep delivery_success=false until external review closes",
        },
    ]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC evidence gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py --acceptance-backfill-json <acceptance_backfill.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_result_review_dispatch.py --review-decision-json <review_decision.json> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field review closes",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    source_review_decision: dict[str, Any],
    categories: dict[str, list[str]],
    owner_work_orders: list[dict[str, Any]],
    callback_packet_requirements: list[dict[str, Any]],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{DISPATCH_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "source_review_decision": source_review_decision,
        "material_categories": categories,
        "accepted_materials": categories["accepted_materials"],
        "missing_materials": categories["missing_materials"],
        "rejected_materials": categories["rejected_materials"],
        "owner_work_orders": owner_work_orders,
        "callback_packet_requirements": callback_packet_requirements,
        "rerun_commands": rerun_commands,
        "evidence_boundary": DISPATCH_BOUNDARY,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    source_review_decision: dict[str, Any],
    categories: dict[str, list[str]],
    owner_work_orders: list[dict[str, Any]],
    callback_packet_requirements: list[dict[str, Any]],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack 的只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": DISPATCH_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "source_review_decision_payload": source_review_decision,
        "material_categories": categories,
        "accepted_materials": categories["accepted_materials"],
        "missing_materials": categories["missing_materials"],
        "rejected_materials": categories["rejected_materials"],
        "owner_work_orders": owner_work_orders,
        "callback_packet_requirements": callback_packet_requirements,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_review_dispatch(
    review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 review decision JSON，生成 fail-closed review dispatch artifact。"""
    payload, load_issue = _load_json(review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _source_evidence_ref(source)
    effective_ref = requested_ref or source_ref
    same_ref_required = _same_ref_required(source) if source else True
    source_status = _source_status(load_issue, source)
    source_review_status = _source_review_status(source) if source else "missing"
    categories = _material_categories(source) if source else {"accepted_materials": [], "missing_materials": [], "rejected_materials": []}
    unsafe_source = bool(payload) and (material_pack._has_forbidden_copy(source) or material_pack._has_raw_path_copy(source))
    success_or_control_claim = bool(payload) and (material_pack._has_success_or_control_claim(source) or _has_true_control_flag(source))
    status = _status(
        load_issue,
        source_status,
        source_review_status,
        effective_ref,
        source_ref,
        same_ref_required,
        requested_ref,
        categories,
        unsafe_source,
        success_or_control_claim,
    )

    source_review_decision = _source_review_decision(source)
    owner_work_orders = _owner_work_orders(status, effective_ref, categories)
    callback_packet_requirements = _callback_packet_requirements(effective_ref, categories)
    rerun_commands = _rerun_commands(effective_ref)
    source_summary = {
        **source_status,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": source_review_status,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "review_decision": source_review_decision,
        "safe_lineage": _lineage(source),
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(success_or_control_claim),
    }
    safe_copy = _safe_copy(
        status,
        effective_ref,
        source_review_decision,
        categories,
        owner_work_orders,
        callback_packet_requirements,
        rerun_commands,
    )
    summary = _summary_payload(
        status,
        effective_ref,
        source_summary,
        source_review_decision,
        categories,
        owner_work_orders,
        callback_packet_requirements,
        rerun_commands,
        safe_copy,
    )
    artifact = {
        "schema": DISPATCH_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_review_decision": source_summary,
        "source_review_decision_payload": source_review_decision,
        "material_categories": categories,
        "accepted_materials": categories["accepted_materials"],
        "missing_materials": categories["missing_materials"],
        "rejected_materials": categories["rejected_materials"],
        "owner_work_orders": owner_work_orders,
        "callback_packet_requirements": callback_packet_requirements,
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result review dispatch artifact")
    parser.add_argument("--review-decision-json", required=True, help="review decision artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this review dispatch gate")
    parser.add_argument("--output", default="", help="optional review dispatch artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review dispatch summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review dispatch artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_review_dispatch(
        args.review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result review dispatch: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"review_dispatch_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"review_dispatch_status: {artifact['status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
