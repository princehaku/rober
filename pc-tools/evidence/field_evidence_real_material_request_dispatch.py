#!/usr/bin/env python3
"""生成 field evidence real material request dispatch artifact。

该 PC gate 接在 `field_evidence_rerun_execution_result_acceptance_backfill`
后面，只读取 acceptance backfill artifact / summary / wrapper 中已经脱敏的
safe state。它把同一 safe `evidence_ref` 下仍缺的真实现场材料转成 field
owner 请求清单，供后续真实材料采集、回填和人工复核使用。
它不读取真实 ROS runtime、硬件、现场日志、credentials、raw artifact，也不
触发机器人动作或声明 delivery success。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_backfill as backfill
import route_task_field_retest_material_pack as material_pack


# request dispatch 是 acceptance backfill 后的 field-owner 材料请求契约。
DISPATCH_SCHEMA = "trashbot.field_evidence_real_material_request_dispatch.v1"
DISPATCH_SUMMARY_SCHEMA = "trashbot.field_evidence_real_material_request_dispatch_summary.v1"
SCHEMA_VERSION = 1
DISPATCH_BOUNDARY = "software_proof_docker_field_evidence_real_material_request_dispatch_gate"

# 只接受上一轮 acceptance backfill 的 artifact/summary，避免绕过 backfill 状态。
SOURCE_SCHEMAS = {backfill.BACKFILL_SCHEMA, backfill.BACKFILL_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {backfill.BACKFILL_BOUNDARY}
READY_BACKFILL_STATUS = "ready_for_field_evidence_rerun_execution_result_acceptance_backfill_not_proven"

# 九类材料是本轮新增真实材料请求范围；所有条目必须绑定同一 safe evidence_ref。
REQUIRED_MATERIALS = (
    "task_record",
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "elevator_door_floor_evidence",
    "human_assistance_note",
    "dropoff_cancel_completion",
    "delivery_result",
    "true_phone_browser_evidence",
    "diagnostics_mobile_safe_summary",
)

# blocked claims 明确告诉 downstream：本 gate 是请求派发，不是现场证明。
BLOCKED_CLAIMS = (
    "real_field_rerun",
    "true_phone_browser_proof",
    "nav2_fixed_route_proof",
    "route_elevator_field_pass",
    "hil_pass",
    "o5_external_proof",
    "pr5_thread_resolved",
    "delivery_result",
    "delivery_success",
)

# rg 围栏依赖这些 literal 保留证据边界和 fail-closed flag。
BOUNDARY_NOTE = (
    "field_evidence_real_material_request_dispatch; "
    "software_proof_docker_field_evidence_real_material_request_dispatch_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; "
    "task_record; nav2_fixed_route_runtime_log; route_completion_signal; "
    "elevator_door_floor_evidence; human_assistance_note; "
    "dropoff_cancel_completion; delivery_result; "
    "true_phone_browser_evidence; diagnostics_mobile_safe_summary"
)

MATERIAL_LABELS = {
    "task_record": "field task record",
    "nav2_fixed_route_runtime_log": "Nav2/fixed-route runtime log",
    "route_completion_signal": "route completion signal",
    "elevator_door_floor_evidence": "elevator door and target-floor evidence",
    "human_assistance_note": "human assistance note",
    "dropoff_cancel_completion": "dropoff/cancel completion",
    "delivery_result": "delivery result",
    "true_phone_browser_evidence": "true phone/browser evidence",
    "diagnostics_mobile_safe_summary": "diagnostics/mobile safe summary",
}

# 设计约束 01：本 gate 只读上一轮 backfill safe state，不读取完整 raw artifact。
# 设计约束 02：source schema、boundary 和 ready_not_proven status 必须同时匹配。
# 设计约束 03：source=software_proof、not_proven 和三类 false flag 必须保留。
# 设计约束 04：safe evidence_ref 是九类材料后续回填的唯一对齐主键。
# 设计约束 05：CLI 指定 evidence_ref 与 source 不一致时必须 fail closed。
# 设计约束 06：弱类型 same_evidence_ref_required 不能通过。
# 设计约束 07：本 gate 只生成 request，不验收真实材料内容。
# 设计约束 08：输出不包含 raw topic、硬件协议、凭证、本机路径或校验和。
# 设计约束 09：true phone/browser 只是待采材料，不证明真实设备通过。
# 设计约束 10：Nav2/fixed-route runtime log 只是待采材料，不证明路线通过。
# 设计约束 11：elevator door/floor evidence 只是待采材料，不证明电梯通过。
# 设计约束 12：human assistance note 只是现场记录请求，不是人工协助已发生。
# 设计约束 13：dropoff/cancel completion 只是待采材料，不声明投放或取消完成。
# 设计约束 14：delivery_result 是待采材料类别，不得转成 delivery_success。
# 设计约束 15：diagnostics/mobile safe summary 是只读摘要请求，不读取 raw diagnostics。
# 设计约束 16：blocked claims 显式阻断 HIL、O5 external proof 和 PR #5 resolved。
# 设计约束 17：wrapper/nested JSON 只递归白名单 key，避免采信任意 raw payload。
# 设计约束 18：最终输出再递归脱敏，防止新增字段绕过扫描。
# 设计约束 19：blocked artifact 也返回 exit code 0，便于 CI 和 sprint 留痕。
# 设计约束 20：所有技术注释保持中文，解释 fail-closed 原因。


def _utc_now() -> str:
    # UTC 时间便于不同 PC/Docker 主机生成的 request artifact 排序。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常统一转成 blocked request，避免空输入误派发。
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
    # wrapper 字段必须是 object，字符串形式 JSON 不当作可信 source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 Robot/mobile 摘要字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 safe wrapper key，避免 raw material payload 混入 source。
    candidates = [payload]
    for key in (
        "field_evidence_real_material_request_dispatch",
        "field_evidence_rerun_execution_result_acceptance_backfill",
        "field_evidence_rerun_execution_result_acceptance_backfill_summary",
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
    # 优先消费 schema 命中的嵌套对象；未命中时保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _safe_source_view(source: dict[str, Any]) -> dict[str, Any]:
    # 只复制 dispatch 需要的白名单字段；先保留原文供 unsafe 扫描，最终输出再脱敏。
    safe_copy = _dict(source, "safe_copy")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    completeness = source.get("material_completeness")
    if not isinstance(completeness, dict):
        completeness = safe_copy.get("material_completeness") if isinstance(safe_copy.get("material_completeness"), dict) else {}
    gap_summary = source.get("acceptance_backfill_gap_summary")
    if not isinstance(gap_summary, dict):
        gap_summary = safe_copy.get("acceptance_backfill_gap_summary") if isinstance(safe_copy.get("acceptance_backfill_gap_summary"), dict) else {}
    return {
        "schema": _first_text(source.get("schema"), safe_copy.get("schema"), default=""),
        "schema_version": source.get("schema_version", safe_copy.get("schema_version", "")),
        "source": _first_text(source.get("source"), safe_copy.get("source"), robot.get("source"), mobile.get("source"), default=""),
        "evidence_boundary": _first_text(
            source.get("evidence_boundary"),
            source.get("boundary"),
            safe_copy.get("evidence_boundary"),
            default="",
        ),
        "status": _first_text(
            source.get("backfill_status"),
            source.get("status"),
            safe_copy.get("backfill_status"),
            safe_copy.get("status"),
            robot.get("backfill_status"),
            robot.get("status"),
            mobile.get("backfill_status"),
            mobile.get("status"),
            default="missing",
        ),
        "safe_evidence_ref": _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            default="",
        ),
        "same_evidence_ref_required": source.get(
            "same_evidence_ref_required",
            safe_copy.get("same_evidence_ref_required", robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", True))),
        ),
        "material_completeness": completeness,
        "acceptance_backfill_gap_summary": gap_summary,
        "safe_to_control": source.get("safe_to_control", safe_copy.get("safe_to_control", robot.get("safe_to_control", mobile.get("safe_to_control")))),
        "delivery_success": source.get("delivery_success", safe_copy.get("delivery_success", robot.get("delivery_success", mobile.get("delivery_success")))),
        "primary_actions_enabled": source.get(
            "primary_actions_enabled",
            safe_copy.get("primary_actions_enabled", robot.get("primary_actions_enabled", mobile.get("primary_actions_enabled"))),
        ),
        "not_proven": source.get("not_proven", safe_copy.get("not_proven", "not_proven")),
    }


def _source_status(load_issue: str, source_view: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时匹配，防止跨 gate 结果误入真实材料请求。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source_view.get("schema", ""))
    boundary = material_pack._safe_text(source_view.get("evidence_boundary", ""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_is_safe(source_view: dict[str, Any]) -> bool:
    # source=software_proof、not_proven 和三类 false flag 是跨 gate 保守边界。
    encoded = material_pack._encoded(source_view)
    return (
        source_view.get("source") == "software_proof"
        and "not_proven" in encoded
        and source_view.get("safe_to_control") is False
        and source_view.get("delivery_success") is False
        and source_view.get("primary_actions_enabled") is False
    )


def _source_evidence_ref(source_view: dict[str, Any]) -> str:
    # evidence_ref 若被误填成本机路径，只保留 basename 形式。
    return material_pack._safe_ref(_first_text(source_view.get("safe_evidence_ref"), source_view.get("evidence_ref"), default=""))


def _status(
    load_issue: str,
    source_status: dict[str, Any],
    source_view: dict[str, Any],
    evidence_ref: str,
    same_ref_required: Any,
    source_safe: bool,
    unsafe_source: bool,
    source_success_or_control_claim: bool,
) -> str:
    # fail closed 顺序固定，危险 copy 优先于普通缺状态。
    if load_issue in {"acceptance_backfill_json_bad_json", "acceptance_backfill_json_read_error", "acceptance_backfill_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_field_evidence_rerun_execution_result_acceptance_backfill"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not source_safe or unsafe_source:
        return "blocked_unsafe_source_state"
    if source_success_or_control_claim:
        return "blocked_success_or_control_claim"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if source_view.get("status") != READY_BACKFILL_STATUS:
        return "blocked_acceptance_backfill_not_ready"
    return "ready_for_field_owner_real_material_request_not_proven"


def _request_items(evidence_ref: str) -> list[dict[str, Any]]:
    # 每个 request item 只描述要采什么，不携带或要求上传 raw content 到本 gate。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": name,
            "label": MATERIAL_LABELS[name],
            "request_status": "requested_not_collected",
            "evidence_ref": ref,
            "same_evidence_ref_required": True,
            "field_owner_instruction": f"provide sanitized {MATERIAL_LABELS[name]} index for evidence_ref={ref}",
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
        for name in REQUIRED_MATERIALS
    ]


def _owner_handoff(status: str, evidence_ref: str) -> dict[str, Any]:
    # owner handoff 是材料采集任务，不包含机器人动作或控制指令。
    ref = evidence_ref or "<same_evidence_ref>"
    next_action = (
        "field owner collects the nine real-material categories under the same safe evidence_ref"
        if status == "ready_for_field_owner_real_material_request_not_proven"
        else "repair acceptance backfill safe state before dispatching real-material requests"
    )
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": [
            "Robot Platform Engineer",
            "User Touchpoint Full-Stack Engineer",
            "Hardware Infra Engineer",
            "Product Manager / OKR Owner",
        ],
        "handoff_status": status,
        "safe_evidence_ref": ref,
        "evidence_ref": ref,
        "next_action": next_action,
        "required_materials": list(REQUIRED_MATERIALS),
        "blocked_claims": list(BLOCKED_CLAIMS),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_steps(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC gate 顺序，不包含 ROS、硬件、云或手机 runtime 命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"collect sanitized field-owner materials for evidence_ref={ref}",
        "keep task_record, nav2_fixed_route_runtime_log, route_completion_signal, elevator_door_floor_evidence, human_assistance_note, dropoff_cancel_completion, delivery_result, true_phone_browser_evidence, and diagnostics_mobile_safe_summary under the same evidence_ref",
        "run the future material intake/review gate only after real field-owner materials exist",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until real review closes",
    ]


def _safe_copy(
    status: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    request_items: list[dict[str, Any]],
    owner_handoff: dict[str, Any],
    next_steps: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{DISPATCH_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "request_dispatch_status": status,
        "evidence_boundary": DISPATCH_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "request_items": request_items,
        "owner_handoff": owner_handoff,
        "next_steps": next_steps,
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven": "not_proven",
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    request_items: list[dict[str, Any]],
    owner_handoff: dict[str, Any],
    next_steps: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 只读对接面，字段稳定且默认 fail-closed。
    return {
        "schema": DISPATCH_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "request_dispatch_status": status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "request_items": request_items,
        "owner_handoff": owner_handoff,
        "next_steps": next_steps,
        "blocked_claims": list(BLOCKED_CLAIMS),
        "safe_copy": safe_copy,
        "not_proven": ["not_proven"],
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_real_material_request_dispatch(
    acceptance_backfill_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance backfill safe state，生成 fail-closed real-material request。"""
    payload, load_issue = _load_json(acceptance_backfill_json)
    source = _find_source(payload) if payload else {}
    source_view = _safe_source_view(source) if source else {}
    source_ref = _source_evidence_ref(source_view)
    requested_ref = material_pack._safe_ref(evidence_ref) or source_ref
    same_ref_required = source_view.get("same_evidence_ref_required", True) if source_view else True
    if evidence_ref and source_ref and requested_ref != source_ref:
        # CLI 指定证据号与 backfill 不一致时，按同证据号硬约束失败。
        same_ref_required = False

    source_status = _source_status(load_issue, source_view)
    source_safe = bool(source_view) and _source_is_safe(source_view)
    source_safe_copy = _dict(source, "safe_copy") if source else {}
    source_robot_summary = _dict(source, "robot_diagnostics_summary") if source else {}
    source_mobile_summary = _dict(source, "mobile_readonly_summary") if source else {}
    unsafe_source = bool(source_view) and (
        material_pack._has_forbidden_copy(source_view) or material_pack._has_raw_path_copy(source_view)
        or material_pack._has_forbidden_copy(source_safe_copy) or material_pack._has_raw_path_copy(source_safe_copy)
        or material_pack._has_forbidden_copy(source_robot_summary) or material_pack._has_raw_path_copy(source_robot_summary)
        or material_pack._has_forbidden_copy(source_mobile_summary) or material_pack._has_raw_path_copy(source_mobile_summary)
    )
    source_success_or_control_claim = bool(source_view) and (
        material_pack._has_success_or_control_claim(source_view)
        or material_pack._has_success_or_control_claim(source_safe_copy)
        or material_pack._has_success_or_control_claim(source_robot_summary)
        or material_pack._has_success_or_control_claim(source_mobile_summary)
    )
    status = _status(
        load_issue,
        source_status,
        source_view,
        requested_ref,
        same_ref_required,
        source_safe,
        unsafe_source,
        source_success_or_control_claim,
    )

    source_summary = {
        **source_status,
        "schema": material_pack._safe_text(source_view.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(source_view.get("evidence_boundary", "")),
        "status": material_pack._safe_text(source_view.get("status", "missing")),
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(source_success_or_control_claim),
        "material_completeness": source_view.get("material_completeness", {}),
        "acceptance_backfill_gap_summary": source_view.get("acceptance_backfill_gap_summary", {}),
    }
    request_items = _request_items(requested_ref)
    owner_handoff = _owner_handoff(status, requested_ref)
    next_steps = _next_steps(requested_ref)
    safe_copy = _safe_copy(status, requested_ref, source_summary, request_items, owner_handoff, next_steps)
    summary = _summary_payload(status, requested_ref, source_summary, request_items, owner_handoff, next_steps, safe_copy)
    artifact = {
        "schema": DISPATCH_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": DISPATCH_BOUNDARY,
        "boundary": DISPATCH_BOUNDARY,
        "status": status,
        "request_dispatch_status": status,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_backfill": source_summary,
        "required_materials": list(REQUIRED_MATERIALS),
        "request_items": request_items,
        "owner_handoff": owner_handoff,
        "next_steps": next_steps,
        "blocked_claims": list(BLOCKED_CLAIMS),
        "safe_copy": safe_copy,
        "field_evidence_real_material_request_dispatch_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "non_access_scope": [
            "raw task records",
            "raw navigation runtime",
            "raw route completion payload",
            "raw elevator material",
            "raw phone browser proof",
            "raw diagnostics",
            "robot control runtime",
            "hardware transport details",
            "external cloud proof",
            "credentials",
            "local file paths",
            "full upstream artifacts",
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
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = "blocked_unsafe_source_state"
        artifact["request_dispatch_status"] = "blocked_unsafe_source_state"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_source_state"
        artifact["robot_diagnostics_summary"]["request_dispatch_status"] = "blocked_unsafe_source_state"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_source_state"
        artifact["mobile_readonly_summary"]["request_dispatch_status"] = "blocked_unsafe_source_state"
        summary["status"] = "blocked_unsafe_source_state"
        summary["request_dispatch_status"] = "blocked_unsafe_source_state"
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；未指定时由 CLI 打印到 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence real material request dispatch artifact")
    parser.add_argument("--acceptance-backfill-json", required=True, help="acceptance backfill artifact, summary, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this request dispatch gate")
    parser.add_argument("--output", default="", help="optional real-material request dispatch artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional real-material request dispatch summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print request dispatch artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_real_material_request_dispatch(
        args.acceptance_backfill_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_real_material_request_dispatch: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"request_dispatch_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"request_dispatch_status: {artifact['request_dispatch_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
