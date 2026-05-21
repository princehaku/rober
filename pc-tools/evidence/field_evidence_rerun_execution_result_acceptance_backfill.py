#!/usr/bin/env python3
"""生成 field evidence rerun execution result acceptance backfill artifact。

该 PC gate 接在 `field_evidence_rerun_execution_result_acceptance_packet` 后面，
只读取 acceptance packet artifact / summary / wrapper 与现场 owner 提交的
脱敏 `--material-dir`。它校验八类 required material 是否和 packet 的 safe
`evidence_ref` 对齐，并输出 Robot/mobile 可消费的只读 artifact / summary。
它不读取真实 Nav2 runtime、ROS graph、serial/UART、WAVE ROVER、真实电梯、
外部云、真实手机/browser，也不触发机器人动作。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import field_evidence_rerun_execution_result_acceptance_packet as packet
import route_task_field_retest_material_pack as material_pack


# backfill 是 acceptance packet 后的 PC 侧现场材料复账契约。
BACKFILL_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1"
BACKFILL_SUMMARY_SCHEMA = "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_summary.v1"
SCHEMA_VERSION = 1
BACKFILL_BOUNDARY = "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate"

# 只允许上一轮 field acceptance packet 作为 source，避免绕过 packet 直接采信材料目录。
SOURCE_SCHEMAS = {packet.PACKET_SCHEMA, packet.PACKET_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {packet.PACKET_BOUNDARY}
READY_PACKET_STATUS = "ready_for_field_owner_acceptance_review_not_proven"

# 八类材料沿用 acceptance packet 固定清单；调用方不能裁剪 required set。
REQUIRED_MATERIALS = packet.REQUIRED_MATERIALS
NOT_PROVEN = packet.NOT_PROVEN

# rg 围栏和人工复盘依赖这些 literal 明确证据边界。
BOUNDARY_NOTE = (
    "field_evidence_rerun_execution_result_acceptance_backfill; "
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate; "
    "source=software_proof; not_proven; safe_to_control=false; "
    "delivery_success=false; primary_actions_enabled=false; same_evidence_ref; "
    "task_record; nav2_fixed_route_runtime_log; route_completion_signal; "
    "elevator_evidence; dropoff_cancel_completion; delivery_result; "
    "true_phone_browser_evidence; diagnostics_mobile_safe_summary"
)

# 文件名别名只影响脱敏材料发现，不会把本机路径写入输出。
MATERIAL_ALIASES: dict[str, tuple[str, ...]] = {
    "task_record": ("task_record.json",),
    "nav2_fixed_route_runtime_log": (
        "nav2_fixed_route_runtime_log.json",
        "nav2_fixed_route_runtime_log.log",
        "nav2_fixed_route_runtime_log.txt",
        "fixed_route_runtime_log.json",
        "runtime_log.json",
    ),
    "route_completion_signal": ("route_completion_signal.json", "completion_signal.json"),
    "elevator_evidence": ("elevator_evidence.json", "elevator_evidence.md"),
    "dropoff_cancel_completion": (
        "dropoff_cancel_completion.json",
        "dropoff_completion.json",
        "cancel_completion.json",
    ),
    "delivery_result": ("delivery_result.json", "delivery_result.md"),
    "true_phone_browser_evidence": (
        "true_phone_browser_evidence.json",
        "phone_browser_evidence.json",
        "browser_evidence.json",
    ),
    "diagnostics_mobile_safe_summary": (
        "diagnostics_mobile_safe_summary.json",
        "mobile_safe_summary.json",
        "diagnostics_summary.json",
    ),
}

# 给 summary 展示的短标签，避免下游 UI 复制 raw material 正文。
MATERIAL_LABELS = {
    "task_record": "task record",
    "nav2_fixed_route_runtime_log": "Nav2/fixed-route runtime log",
    "route_completion_signal": "route completion signal",
    "elevator_evidence": "elevator evidence",
    "dropoff_cancel_completion": "dropoff/cancel completion",
    "delivery_result": "delivery result",
    "true_phone_browser_evidence": "true phone/browser evidence",
    "diagnostics_mobile_safe_summary": "diagnostics/mobile safe summary",
}

# 设计约束 01：本 gate 只消费上一轮 acceptance packet，不读取 raw upstream artifact。
# 设计约束 02：material-dir 只允许脱敏 JSON/manifest/text 索引，不承载真实 runtime。
# 设计约束 03：ready 状态仍是 not_proven，不能转成现场通过或 delivery success。
# 设计约束 04：safe_to_control、delivery_success、primary_actions_enabled 永远 false。
# 设计约束 05：safe evidence_ref 是跨 task/Nav2/elevator/mobile 材料复账主键。
# 设计约束 06：缺 evidence_ref、弱类型 same_evidence_ref_required 或 mismatch 必须阻断。
# 设计约束 07：missing、placeholder、unsafe、sensitive、success claim 全部 fail closed。
# 设计约束 08：summary 只输出短字段，供 Robot/mobile 只读消费。
# 设计约束 09：wrapper/nested JSON 只递归白名单 key，避免采信任意 raw payload。
# 设计约束 10：blocked artifact 也返回 exit code 0，便于 CI 和 sprint 证据落盘。
# 设计约束 11：材料扫描复用已有脱敏 helper，保持 raw path/token/ROS topic 策略一致。
# 设计约束 12：本文件不访问 docs/vendor，因为不新增硬件参数或协议假设。
# 设计约束 13：Nav2/fixed-route 只作为材料类别名，不读取 runtime log。
# 设计约束 14：true phone/browser 只作为材料类别名，不证明真实设备通过。
# 设计约束 15：elevator evidence 只作为材料类别名，不证明真实电梯通过。
# 设计约束 16：dropoff/cancel 只作为 completion 材料类别，不声明完成。
# 设计约束 17：Robot/mobile diagnostics 只作为 safe summary 类别，不读取 raw diagnostics。
# 设计约束 18：输出最终再递归脱敏，防止新增字段绕过材料扫描。
# 设计约束 19：dependency-free，便于 macOS PC、Docker 和 unittest 直接复跑。
# 设计约束 20：所有技术注释保持中文，解释 fail-closed 原因。


def _utc_now() -> str:
    # UTC 时间便于不同 PC/Docker 主机生成的 artifact 按时间线复盘。
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入异常统一转成 blocked backfill，避免空输入误判为 ready。
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
        "field_evidence_rerun_execution_result_acceptance_backfill",
        "field_evidence_rerun_execution_result_acceptance_backfill_summary",
        "field_evidence_rerun_execution_result_acceptance_packet",
        "field_evidence_rerun_execution_result_acceptance_packet_summary",
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
    # schema 与 boundary 必须同时匹配，防止跨 gate 结果误入回填验收。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = material_pack._safe_text(source.get("schema", ""))
    boundary = material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))
    if schema in SOURCE_SCHEMAS and boundary in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_evidence_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 可来自 artifact、summary、safe_copy、Robot 或 mobile 面。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
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
            default="",
        )
    )


def _source_packet_status(source: dict[str, Any]) -> str:
    # 只有上一轮 ready_not_proven packet 才能进入 backfill ready 判断。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return material_pack._safe_text(
        _first_text(
            source.get("acceptance_verdict"),
            source.get("status"),
            robot.get("acceptance_verdict"),
            robot.get("status"),
            mobile.get("acceptance_verdict"),
            mobile.get("status"),
            safe_copy.get("acceptance_verdict"),
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
    safe_copy = _dict(source, "safe_copy")
    for key in ("acceptance_verdict", "same_evidence_ref_status", "evidence_boundary"):
        text = material_pack._safe_text(_first_text(source.get(key), safe_copy.get(key), default=""))
        if text:
            lineage[f"packet_{key}"] = text
    return lineage


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


def _find_material_file(material_dir: Path, material_name: str) -> Path | None:
    # 只按白名单文件名查找，避免任意目录文件被包装进 artifact。
    for alias in MATERIAL_ALIASES[material_name]:
        candidate = material_dir / alias
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _scan_material(material_dir: Path, material_name: str, expected_ref: str) -> tuple[dict[str, Any], list[str]]:
    # 单类材料只返回状态、短 metadata 和拒绝原因，绝不把正文写入输出。
    path = _find_material_file(material_dir, material_name)
    if path is None:
        return {
            "name": material_name,
            "label": MATERIAL_LABELS[material_name],
            "status": "missing",
            "accepted": False,
            "same_evidence_ref_required": True,
            "rejected_reasons": ["missing_material"],
        }, ["missing_material"]
    text, payload, read_issue = material_pack._read_material(path)
    evidence_ref = material_pack._material_ref(payload, text, expected_ref)
    reasons: list[str] = []
    if read_issue:
        reasons.append(read_issue)
    if material_pack._placeholder_material(text, payload, read_issue):
        reasons.append("placeholder_only")
    if expected_ref and evidence_ref and evidence_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if not evidence_ref:
        reasons.append("missing_evidence_ref")
    if material_pack._has_forbidden_copy(text) or material_pack._has_forbidden_copy(payload):
        reasons.append("unsafe_copy")
    if material_pack._has_raw_path_copy(text) or material_pack._has_raw_path_copy(payload):
        reasons.append("raw_path_copy")
    if material_pack._has_success_or_control_claim(text) or material_pack._has_success_or_control_claim(payload):
        reasons.append("success_or_control_claim")
    entry = {
        "name": material_name,
        "label": MATERIAL_LABELS[material_name],
        "status": "accepted" if not reasons else "rejected",
        "accepted": not reasons,
        "file_ref": f"file:{path.name}",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "metadata": material_pack._metadata_summary(payload, text),
        "rejected_reasons": reasons,
    }
    return entry, reasons


def _material_states(material_dir: str, evidence_ref: str) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, list[str]], list[str]]:
    # material-dir 缺席时仍输出八类材料缺口，方便 owner 定位补证范围。
    material_path, dir_status = material_pack._source_dir_status(material_dir)
    states: list[dict[str, Any]] = []
    rejected: dict[str, list[str]] = {}
    missing: list[str] = []
    if material_path is None:
        for name in REQUIRED_MATERIALS:
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

    for name in REQUIRED_MATERIALS:
        entry, reasons = _scan_material(material_path, name, evidence_ref)
        states.append(entry)
        if "missing_material" in reasons:
            missing.append(name)
        elif reasons:
            rejected[name] = reasons
    return states, dir_status, rejected, missing


def _material_completeness(states: list[dict[str, Any]], missing: list[str], rejected: dict[str, list[str]]) -> dict[str, Any]:
    # completeness 只说明材料目录状态，不证明真实现场复跑成功。
    accepted = [entry["name"] for entry in states if entry.get("accepted") is True]
    return {
        "required_count": len(REQUIRED_MATERIALS),
        "accepted_count": len(accepted),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": sorted(rejected.keys()),
        "is_complete": len(accepted) == len(REQUIRED_MATERIALS),
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
    source_safe: bool,
) -> str:
    # fail closed 顺序固定，危险 copy 优先于普通缺材料。
    if load_issue in {"acceptance_packet_json_bad_json", "acceptance_packet_json_read_error", "acceptance_packet_json_not_object"}:
        return "blocked_bad_json"
    if load_issue:
        return "blocked_missing_field_evidence_rerun_execution_result_acceptance_packet"
    if source_status["schema_status"] != "supported":
        return "blocked_unsupported_schema"
    if not source_safe:
        return "blocked_unsafe_material_copy"
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
    return "ready_for_field_evidence_rerun_execution_result_acceptance_backfill_not_proven"


def _owner_handoff(status: str, evidence_ref: str, missing: list[str], rejected: dict[str, list[str]]) -> dict[str, Any]:
    # owner handoff 只要求修材料和重跑 PC gate，不指示机器人动作。
    ref = evidence_ref or "<same_evidence_ref>"
    next_action = (
        "review acceptance backfill summary with Robot/mobile read-only consumers"
        if status == "ready_for_field_evidence_rerun_execution_result_acceptance_backfill_not_proven"
        else "repair acceptance packet or sanitized material directory before backfill review"
    )
    return {
        "primary_owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer", "Product Manager / OKR Owner"],
        "handoff_status": status,
        "safe_evidence_ref": ref,
        "evidence_ref": ref,
        "next_action": next_action,
        "missing_owner_focus": missing,
        "rejected_owner_focus": rejected,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # rerun commands 只覆盖 PC gate 顺序，不包含 ROS/Nav2/硬件/云/手机命令。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_packet.py --review-handoff-json <review_handoff.json> --acceptance-packet-json <acceptance_packet_input.json> --evidence-ref {ref}",
        f"python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_backfill.py --acceptance-packet-json <acceptance_packet.json> --material-dir <sanitized_material_dir> --evidence-ref {ref}",
        "keep source=software_proof, not_proven, safe_to_control=false, delivery_success=false, and primary_actions_enabled=false until real review closes",
    ]


def _decision_inputs(evidence_ref: str) -> dict[str, list[str]]:
    # 这些是下次人工验收判断输入，不是本轮真实通过结论。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "ready_review_inputs": [
            f"acceptance packet status is {READY_PACKET_STATUS}",
            f"all required backfill materials use evidence_ref={ref}",
            "task record, Nav2/fixed-route runtime log, route completion, elevator evidence, dropoff/cancel, delivery result, true phone/browser, and diagnostics/mobile summary are accepted as sanitized material indexes",
            "safe_to_control=false, delivery_success=false, and primary_actions_enabled=false remain unchanged",
        ],
        "blocked_inputs": [
            "source packet schema or evidence_boundary is unsupported",
            "any required material is missing, placeholder, rejected, unsafe, sensitive, or uses another evidence_ref",
            "success/control claim appears in packet or material input",
            "real Nav2/fixed-route, elevator, dropoff/cancel, phone/browser, HIL, cloud, or delivery proof is absent",
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
    decision_inputs: dict[str, list[str]],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不携带 raw artifact 或本机路径。
    return {
        "schema": f"{BACKFILL_SUMMARY_SCHEMA}.safe_copy",
        "source": "software_proof",
        "status": status,
        "backfill_status": status,
        "evidence_boundary": BACKFILL_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_completeness": completeness,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "decision_inputs": decision_inputs,
        "not_proven": "not_proven",
        "safe_to_control": False,
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
    decision_inputs: dict[str, list[str]],
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
        "source": "software_proof",
        "evidence_boundary": BACKFILL_BOUNDARY,
        "boundary": BACKFILL_BOUNDARY,
        "status": status,
        "backfill_status": status,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_packet": source_summary,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_states": safe_states,
        "material_completeness": completeness,
        "rejected_materials": rejected,
        "same_evidence_ref_alignment": alignment,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "decision_inputs": decision_inputs,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_field_evidence_rerun_execution_result_acceptance_backfill(
    acceptance_packet_json: str,
    material_dir: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 acceptance packet JSON 和 material-dir，生成 fail-closed backfill artifact。"""
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
    source_safe = bool(source) and _source_is_safe(source)
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
        source_safe,
    )

    lineage = _source_lineage(source)
    gap_summary = _gap_summary(missing, rejected, alignment)
    owner_handoff = _owner_handoff(status, requested_ref, missing, rejected)
    rerun_commands = _rerun_commands(requested_ref)
    decision_inputs = _decision_inputs(requested_ref)
    safe_copy = _safe_copy(status, requested_ref, lineage, completeness, gap_summary, owner_handoff, rerun_commands, decision_inputs)
    source_summary = {
        **source_status,
        "schema": material_pack._safe_text(source.get("schema", "")),
        "evidence_boundary": material_pack._safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": source_packet_status,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "same_evidence_ref_required": same_ref_required,
        "source_is_software_proof_not_proven": bool(source_safe),
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
        decision_inputs,
        safe_copy,
    )
    artifact = {
        "schema": BACKFILL_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "evidence_boundary": BACKFILL_BOUNDARY,
        "boundary": BACKFILL_BOUNDARY,
        "status": status,
        "backfill_status": status,
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "source_acceptance_packet": source_summary,
        "source_material_dir": dir_status,
        "safe_lineage": lineage,
        "required_materials": list(REQUIRED_MATERIALS),
        "material_states": states,
        "material_completeness": completeness,
        "rejected_materials": rejected,
        "same_evidence_ref_alignment": alignment,
        "acceptance_backfill_gap_summary": gap_summary,
        "owner_handoff": owner_handoff,
        "rerun_commands": rerun_commands,
        "decision_inputs": decision_inputs,
        "safe_copy": safe_copy,
        "field_evidence_rerun_execution_result_acceptance_backfill_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "raw_task_record",
            "raw_nav2_runtime_log",
            "raw_fixed_route_runtime_log",
            "raw_route_completion_signal",
            "raw_elevator_evidence",
            "raw_dropoff_cancel_completion",
            "raw_delivery_result",
            "raw_true_phone_browser_evidence",
            "raw_diagnostics",
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
    # CLI 保持 dependency-free，方便 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(description="Generate a field evidence rerun execution result acceptance backfill artifact")
    parser.add_argument("--acceptance-packet-json", required=True, help="acceptance packet artifact, summary, or wrapper JSON")
    parser.add_argument("--material-dir", required=True, help="directory containing sanitized required backfill material files")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref for this backfill gate")
    parser.add_argument("--output", default="", help="optional acceptance backfill artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional acceptance backfill summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print acceptance backfill artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_field_evidence_rerun_execution_result_acceptance_backfill(
        args.acceptance_packet_json,
        args.material_dir,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"field_evidence_rerun_execution_result_acceptance_backfill: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"acceptance_backfill_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"acceptance_backfill_status: {artifact['backfill_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
