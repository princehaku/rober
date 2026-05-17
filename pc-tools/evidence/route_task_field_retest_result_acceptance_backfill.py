#!/usr/bin/env python3
"""生成 route/task field retest result acceptance backfill artifact。

该 gate 接在 route_task_field_retest_result_acceptance_packet 后面，只读取
acceptance packet artifact / summary / wrapper 与 PC 侧 `--material-dir`。它校验
八类现场回填材料是否和 packet 的 safe `evidence_ref` 对齐，并输出给 Robot /
mobile 只读消费的 artifact / summary。它不读取 raw upstream artifact，不访问真实
Nav2、serial/UART、WAVE ROVER、云、4G、OSS/CDN、DB/queue 或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import route_task_field_retest_material_pack as material_pack
import route_task_field_retest_result_acceptance_packet as packet


# backfill 是 acceptance packet 后的 PC 侧结果材料回填契约。
BACKFILL_SCHEMA = "trashbot.route_task_field_retest_result_acceptance_backfill.v1"
BACKFILL_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1"
SCHEMA_VERSION = 1
BACKFILL_BOUNDARY = "software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate"

# 只允许上一轮 acceptance packet 作为 source，避免跳过 packet 直接验收材料目录。
SOURCE_SCHEMAS = {packet.PACKET_SCHEMA, packet.PACKET_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {packet.PACKET_BOUNDARY}
READY_PACKET_STATUS = "ready_for_field_retest_result_acceptance_packet_not_proven"

# 八类材料沿用 route/task field-retest 链路固定清单，不允许调用方裁剪。
REQUIRED_RESULT_MATERIALS = material_pack.REQUIRED_MATERIALS
NOT_PROVEN = material_pack.NOT_PROVEN

# rg 围栏和人工复盘都依赖这些 literal 明确边界。
BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "Nav2/fixed-route runtime log; door state; delivery result"
)

# 给 summary 展示的短标签，不进入材料扫描逻辑。
MATERIAL_LABELS = {
    "nav2_or_fixed_route_runtime_log": "Nav2/fixed-route runtime log",
    "route_completion_signal": "route completion signal",
    "task_record": "task record",
    "door_state": "door state",
    "target_floor_confirmation": "target floor confirmation",
    "human_assistance_note": "human assistance note",
    "dropoff_or_cancel_completion": "dropoff/cancel completion",
    "delivery_result": "delivery result",
}


def _utc_now() -> str:
    # UTC 时间便于 Docker/local 主机之间按时间线复盘 artifact。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常统一转为 blocked backfill，避免材料回填悄悄缺席。
    if not path:
        return {}, "acceptance_packet_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "acceptance_packet_json_missing"
    except json.JSONDecodeError:
        return {}, "acceptance_packet_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "acceptance_packet_json_read_error"
    if not isinstance(payload, dict):
        return {}, "acceptance_packet_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # wrapper 字段必须是 object，字符串形式 JSON 不能被当作可信 source。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 diagnostics 的字段位置可能不同。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # backfill 只需要短清单，限长避免复制完整上游材料。
    if isinstance(value, list):
        return [material_pack._safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [material_pack._safe_text(value)]


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 key，避免把 raw handoff 或任意 payload 当成 packet。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_acceptance_backfill",
        "route_task_field_retest_result_acceptance_backfill_summary",
        "route_task_field_retest_result_acceptance_packet",
        "route_task_field_retest_result_acceptance_packet_summary",
        "acceptance_packet",
        "acceptance_packet_summary",
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


def _source_status(load_issue: str, source: dict[str, Any]) -> dict[str, Any]:
    # schema 与 boundary 必须同时受支持，防止跨 gate 结果误入回填验收。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 是 packet 与 backfill material 目录串联的唯一主键。
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


def _source_packet_status(source: dict[str, Any]) -> str:
    # 只有 ready_not_proven packet 才能触发 ready backfill。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("acceptance_packet_status"),
            source.get("status"),
            robot.get("acceptance_packet_status"),
            robot.get("status"),
            mobile.get("acceptance_packet_status"),
            mobile.get("status"),
            safe_copy.get("acceptance_packet_status"),
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
    # lineage 只复制 packet 已经白名单化的安全字段，不追 raw upstream artifact。
    lineage = {"source_acceptance_packet_schema": material_pack._safe_text(source.get("schema", ""))}
    status = _source_packet_status(source)
    if status:
        lineage["source_acceptance_packet_status"] = status
    safe_lineage = source.get("safe_lineage")
    if isinstance(safe_lineage, dict):
        for key, value in safe_lineage.items():
            text = material_pack._safe_text(value)
            if text:
                lineage[f"packet_{material_pack._safe_text(key)}"] = text
    return lineage


def _material_states(material_dir: str, evidence_ref: str) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[str]], list[str]]:
    # 材料扫描复用 material_pack helper，保证 alias、placeholder 和脱敏策略一致。
    material_path, dir_status = material_pack._source_dir_status(material_dir)
    states: list[dict[str, Any]] = []
    rejected: dict[str, list[str]] = {}
    missing: list[str] = []
    if material_path is None:
        for name in REQUIRED_RESULT_MATERIALS:
            states.append(
                {
                    "name": name,
                    "label": MATERIAL_LABELS[name],
                    "status": "missing",
                    "accepted": False,
                    "same_evidence_ref_required": True,
                    "rejected_reasons": ["missing_material"],
                }
            )
            missing.append(name)
        return states, dir_status, rejected, missing

    for name in REQUIRED_RESULT_MATERIALS:
        entry, reasons = material_pack._scan_material(material_path, name, evidence_ref)
        state = {
            "name": name,
            "label": MATERIAL_LABELS[name],
            "status": entry.get("status", "missing"),
            "accepted": bool(entry.get("accepted", False)),
            "file_ref": entry.get("file_ref", ""),
            "evidence_ref": entry.get("evidence_ref", ""),
            "same_evidence_ref_required": True,
            "metadata": entry.get("metadata", {}),
            "rejected_reasons": reasons,
        }
        states.append(state)
        if "missing_material" in reasons:
            missing.append(name)
        elif reasons:
            rejected[name] = reasons
    return states, dir_status, rejected, missing


def _material_completeness(states: list[dict[str, Any]], missing: list[str], rejected: dict[str, list[str]]) -> dict[str, Any]:
    # completeness 只说明回填目录状态，不证明真实 fixed-route / delivery 成功。
    accepted = [entry["name"] for entry in states if entry.get("accepted") is True]
    return {
        "required_count": len(REQUIRED_RESULT_MATERIALS),
        "accepted_count": len(accepted),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": sorted(rejected.keys()),
        "is_complete": len(accepted) == len(REQUIRED_RESULT_MATERIALS),
    }


def _same_ref_alignment(evidence_ref: str, states: list[dict[str, Any]], missing: list[str], same_ref_required: Any) -> dict[str, Any]:
    # evidence_ref 对齐失败必须显式暴露，不能靠 accepted_count 隐含表达。
    mismatched = [
        entry["name"]
        for entry in states
        if entry.get("evidence_ref") and evidence_ref and entry.get("evidence_ref") != evidence_ref
    ]
    missing_ref = [entry["name"] for entry in states if entry.get("status") != "missing" and not entry.get("evidence_ref")]
    return {
        "required": True,
        "input_required_value": same_ref_required,
        "evidence_ref": evidence_ref,
        "status": "aligned" if evidence_ref and same_ref_required is True and not missing and not mismatched and not missing_ref else "blocked",
        "missing_materials": missing,
        "mismatched_materials": mismatched,
        "missing_evidence_ref_materials": missing_ref,
    }


def _gap_summary(missing: list[str], rejected: dict[str, list[str]], alignment: dict[str, Any]) -> dict[str, Any]:
    # gap summary 是支持侧修复入口，不包含 raw log、task record 或现场文件正文。
    rejected_count = sum(len(reasons) for reasons in rejected.values())
    return {
        "missing_materials": missing,
        "rejected_materials": rejected,
        "same_evidence_ref_alignment": alignment["status"],
        "gap_count": len(missing) + rejected_count + len(alignment["mismatched_materials"]) + len(alignment["missing_evidence_ref_materials"]),
        "gap_policy": "fail_closed_until_packet_and_all_backfill_materials_share_same_evidence_ref",
    }


def _has_material_reason(rejected: dict[str, list[str]], reason: str) -> bool:
    # fail-closed 优先级需要快速判断某类拒绝原因是否出现。
    return any(reason in reasons for reasons in rejected.values())


def _status(
    load_issue: str,
    source_status: dict[str, Any],
    source_packet_status: str,
    evidence_ref: str,
    same_ref_required: Any,
    dir_status: dict[str, Any],
    missing: list[str],
    rejected: dict[str, list[str]],
    alignment: dict[str, Any],
    unsafe_source: bool,
    source_success_or_control_claim: bool,
) -> str:
    # fail closed 顺序固定，危险 copy 优先于普通缺材料。
    if load_issue in {"acceptance_packet_json_bad_json", "acceptance_packet_json_read_error", "acceptance_packet_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_route_task_field_retest_result_acceptance_packet"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not evidence_ref:
        return "blocked_missing_evidence_ref"
    if same_ref_required is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_source or _has_material_reason(rejected, "unsafe_copy") or _has_material_reason(rejected, "raw_path_copy"):
        return "blocked_unsafe_material_copy"
    if source_success_or_control_claim or _has_material_reason(rejected, "success_or_control_claim"):
        return "blocked_success_or_control_claim"
    if source_packet_status != READY_PACKET_STATUS:
        return "blocked_acceptance_packet_not_ready"
    if dir_status["load_issue"]:
        return "blocked_missing_material_dir"
    if alignment["mismatched_materials"] or alignment["missing_evidence_ref_materials"]:
        return "blocked_same_evidence_ref_mismatch"
    if missing:
        return "blocked_missing_materials"
    if _has_material_reason(rejected, "placeholder_only"):
        return "blocked_placeholder_only_materials"
    if rejected:
        return "blocked_rejected_materials"
    return "ready_for_field_retest_result_acceptance_backfill_not_proven"


def _owner_handoff(status: str, evidence_ref: str, missing: list[str], rejected: dict[str, list[str]]) -> dict[str, Any]:
    # owner handoff 只要求修材料和重跑 PC gate，不指示机器人动作。
    ref = evidence_ref or "<same_evidence_ref>"
    next_action = (
        "review backfill summary with Robot/mobile read-only consumers"
        if status == "ready_for_field_retest_result_acceptance_backfill_not_proven"
        else "repair acceptance packet or material directory before backfill review"
    )
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": status,
        "evidence_ref": ref,
        "next_action": next_action,
        "missing_owner_focus": missing,
        "rejected_owner_focus": rejected,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py --reconciliation-json <reconciliation.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py --acceptance-packet-json <acceptance_packet.json> --material-dir <material_dir> --evidence-ref {ref}",
        "keep delivery_success=false and primary_actions_enabled=false until real field review closes",
    ]


def _pass_fail_decision_inputs(evidence_ref: str) -> dict[str, list[str]]:
    # 这些是下次现场复测材料回填的判断输入，不是本轮真实通过结论。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "pass": [
            f"acceptance packet status is {READY_PACKET_STATUS}",
            f"all eight backfill materials use evidence_ref={ref}",
            "Nav2/fixed-route runtime log, door state, and delivery result material states are accepted",
            "delivery_success remains false and primary_actions_enabled remains false in this backfill artifact",
        ],
        "fail": [
            "source packet schema or evidence_boundary is unsupported",
            "any required backfill material is missing, placeholder, rejected, or uses another evidence_ref",
            "unsafe copy, raw path, credential, ROS topic, hardware transport detail, or success/control claim appears",
            "real Nav2/fixed-route, elevator, dropoff/cancel, phone/browser, HIL, or cloud proof is absent",
        ],
    }


def _safe_copy(
    status: str,
    evidence_ref: str,
    lineage: dict[str, str],
    completeness: dict[str, Any],
    gap_summary: dict[str, Any],
    owner_handoff: dict[str, Any],
    rerun_commands: list[str],
    pass_fail_inputs: dict[str, list[str]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{BACKFILL_SUMMARY_SCHEMA}.safe_copy",
        "status": status,
        "backfill_status": status,
        "evidence_boundary": BACKFILL_BOUNDARY,
        "evidence_ref": evidence_ref,
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "material_completeness": completeness,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_decision_inputs": pass_fail_inputs,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    source_summary: dict[str, Any],
    lineage: dict[str, str],
    states: list[dict[str, Any]],
    completeness: dict[str, Any],
    rejected: dict[str, list[str]],
    alignment: dict[str, Any],
    gap_summary: dict[str, Any],
    owner_handoff: dict[str, Any],
    rerun_commands: list[str],
    pass_fail_inputs: dict[str, list[str]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 只读对接面，字段稳定且默认 fail-closed。
    safe_states = [
        {
            "name": entry["name"],
            "label": entry["label"],
            "status": entry["status"],
            "accepted": entry["accepted"],
            "evidence_ref": entry.get("evidence_ref", ""),
            "rejected_reasons": entry.get("rejected_reasons", []),
        }
        for entry in states
    ]
    return {
        "schema": BACKFILL_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": BACKFILL_BOUNDARY,
        "boundary": BACKFILL_BOUNDARY,
        "status": status,
        "backfill_status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_packet": source_summary,
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "material_states": safe_states,
        "material_completeness": completeness,
        "rejected_materials": rejected,
        "same_evidence_ref_alignment": alignment,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_decision_inputs": pass_fail_inputs,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_acceptance_backfill(
    acceptance_packet_json: str,
    material_dir: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 packet JSON 和 material-dir，生成 fail-closed backfill artifact。"""
    payload, load_issue = _load_json(acceptance_packet_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref) or _source_evidence_ref(source)
    source_ref = _source_evidence_ref(source)
    same_ref_required = _same_ref_required(source) if source else True
    if evidence_ref and source_ref and requested_ref != source_ref:
        # CLI 指定证据号与 packet 不一致时，按同证据号硬约束失败。
        same_ref_required = False

    source_status = _source_status(load_issue, source)
    source_packet_status = _source_packet_status(source) if source else "missing"
    states, dir_status, rejected, missing = _material_states(material_dir, requested_ref)
    completeness = _material_completeness(states, missing, rejected)
    alignment = _same_ref_alignment(requested_ref, states, missing, same_ref_required)
    unsafe_source = bool(payload) and (material_pack._has_forbidden_copy(source) or material_pack._has_raw_path_copy(source))
    source_success_or_control_claim = bool(payload) and material_pack._has_success_or_control_claim(source)
    status = _status(
        load_issue,
        source_status,
        source_packet_status,
        requested_ref,
        same_ref_required,
        dir_status,
        missing,
        rejected,
        alignment,
        unsafe_source,
        source_success_or_control_claim,
    )

    lineage = _source_lineage(source)
    gap_summary = _gap_summary(missing, rejected, alignment)
    owner_handoff = _owner_handoff(status, requested_ref, missing, rejected)
    rerun_commands = _rerun_commands(requested_ref)
    pass_fail_inputs = _pass_fail_decision_inputs(requested_ref)
    safe_copy = _safe_copy(status, requested_ref, lineage, completeness, gap_summary, owner_handoff, rerun_commands, pass_fail_inputs)
    source_summary = {
        **source_status,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": source_packet_status,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "unsafe_copy": bool(unsafe_source),
        "success_or_control_claim": bool(source_success_or_control_claim),
    }
    summary = _summary_payload(
        status,
        requested_ref,
        source_summary,
        lineage,
        states,
        completeness,
        rejected,
        alignment,
        gap_summary,
        owner_handoff,
        rerun_commands,
        pass_fail_inputs,
        safe_copy,
    )

    artifact = {
        "schema": BACKFILL_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": BACKFILL_BOUNDARY,
        "boundary": BACKFILL_BOUNDARY,
        "status": status,
        "backfill_status": status,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_packet": source_summary,
        "source_material_dir": dir_status,
        "safe_lineage": lineage,
        "required_result_materials": list(REQUIRED_RESULT_MATERIALS),
        "material_states": states,
        "material_completeness": completeness,
        "rejected_materials": rejected,
        "same_evidence_ref_alignment": alignment,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "pass_fail_decision_inputs": pass_fail_inputs,
        "safe_copy": safe_copy,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_upstream_artifact",
            "ros_graph",
            "real_nav2_runtime",
            "real_fixed_route_runtime",
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
        # 最终防线：输出仍含禁词时强制降级，且不改变 fail-closed flags。
        artifact["status"] = "blocked_unsafe_material_copy"
        artifact["backfill_status"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["robot_diagnostics_summary"]["backfill_status"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_material_copy"
        artifact["mobile_readonly_summary"]["backfill_status"] = "blocked_unsafe_material_copy"
        summary["status"] = "blocked_unsafe_material_copy"
        summary["backfill_status"] = "blocked_unsafe_material_copy"
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result acceptance backfill artifact")
    parser.add_argument("--acceptance-packet-json", required=True, help="acceptance packet artifact, summary, or wrapper JSON")
    parser.add_argument("--material-dir", required=True, help="directory containing eight backfill material files")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this backfill gate")
    parser.add_argument("--output", default="", help="optional acceptance backfill artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance backfill summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance backfill artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_acceptance_backfill(
        args.acceptance_packet_json,
        args.material_dir,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field retest result acceptance backfill: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_backfill_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"acceptance_backfill_status: {artifact['backfill_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
