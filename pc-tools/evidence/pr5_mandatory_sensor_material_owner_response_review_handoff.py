#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor material owner-response review-handoff gate。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pr5_mandatory_sensor_material_owner_response_review_decision as decision_gate
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
SCHEMA_VERSION = 1
CAPABILITY = "pr5_mandatory_sensor_material_owner_response_review_handoff"
SOURCE_CAPABILITY = decision_gate.CAPABILITY
BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate"
SOURCE_BOUNDARY = decision_gate.BOUNDARY
THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

READY = "ready_for_owner_response_review_handoff_not_proven"
NEEDS_MORE = "needs_more_material_before_owner_response_review_handoff_not_proven"
REJECTED_UNSAFE = "rejected_unsafe_owner_response_review_handoff_not_proven"
BLOCKED_MISSING = "blocked_missing_owner_response_review_decision_not_proven"
BLOCKED_REF = "blocked_evidence_ref_mismatch_not_proven"
HANDOFF_STATUSES = (READY, NEEDS_MORE, REJECTED_UNSAFE, BLOCKED_MISSING, BLOCKED_REF)

SUPPORTED_SOURCE_SCHEMAS = {
    decision_gate.SCHEMA,
    decision_gate.SUMMARY_SCHEMA,
    f"trashbot.{decision_gate.ROBOT_ALIAS}.v1",
    decision_gate.ROBOT_ALIAS,
}

# 设计约束 01：本 gate 只消费上一轮 review-decision 的 safe artifact/summary。
# 设计约束 02：handoff 只是人工 owner/support/reviewer 路由，不证明真实传感器。
# 设计约束 03：ready 状态也必须保留 hardware_material_pending 和 not_proven。
# 设计约束 04：同一 safe evidence_ref 是 PR #5 材料链的复账主键。
# 设计约束 05：缺 source、unsupported schema、证据号不一致全部 fail closed。
# 设计约束 06：raw owner response、完整 artifact、凭证、本机路径和 checksum 全部拒绝。
# 设计约束 07：ROS topic、/cmd_vel、serial/UART、baudrate 和 WAVE ROVER runtime 不能穿透。
# 设计约束 08：HIL/pass、LiDAR/ToF installed、delivery success、O5 external proof 都不能被采信。
# 设计约束 09：PRRT_kwDOSWB9286CJ3tX 继续保持 unresolved / hardware_material_pending。
# 设计约束 10：comment 3269642220 只能是 software-proof reply publication，不是 resolution。
# 设计约束 11：vendor refs 只做来源归因，不做 procurement/install/calibration/HIL proof。
# 设计约束 12：summary 是 Robot/mobile/Product 唯一安全消费面，不透出 raw source。
# 设计约束 13：safe_copy 重复 false flags，防止下游只读局部 JSON 时误启用动作。
# 设计约束 14：CLI 不访问 ROS、GitHub、网络、串口、真实 WAVE ROVER 或真实传感器。
# 设计约束 15：代码注释用中文说明为什么 fail closed，方便硬件履约复盘。
# 设计约束 16：最终 artifact/summary 再做安全扫描，避免新增字段绕过前置规则。
# 设计约束 17：本实现不修改 launch defaults、hardware config、vendor files 或 factory firmware。
# 设计约束 18：本实现不修改 Robot/mobile/sprint closeout，避免覆盖并行 worker。
# 证据边界 01：source review-decision 是唯一输入，因为上一 rung 已经隔离 raw owner response。
# 证据边界 02：accepted review-decision 只代表可进入 reviewer closeout 人工复核。
# 证据边界 03：handoff route 不等于 reviewer resolution，也不等于 GitHub mutation。
# 证据边界 04：source attribution 不等于真实 2D LiDAR / ToF SKU 或采购收据。
# 证据边界 05：Orange Pi 文档不证明本机接线，WAVE ROVER vendor app 不证明 UART 通。
# 证据边界 06：json_cmd.h 命令编号不证明当前固件或底盘已经 HIL 通过。
# 证据边界 07：所有输出固定 delivery_success=false、primary_actions_enabled=false。
# 证据边界 08：所有输出固定 safe_to_control=false，不能进入控制面。
# 证据边界 09：ready handoff 只给人工 Hardware/Product/Robot/Full-Stack 继续补证。
# 证据边界 10：needs_more/rejected/blocked 保留 next_required_evidence，便于后续重试。

VENDOR_REFS = decision_gate.VENDOR_REFS
NOT_PROVEN = decision_gate.NOT_PROVEN

BOUNDARY_NOTE = (
    "pr5_mandatory_sensor_material_owner_response_review_handoff; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate; "
    "pr5_mandatory_sensor_material_owner_response_review_decision; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate; "
    "source=software_proof; software_proof; hardware_material_pending; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; "
    "PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending; "
    "comment 3269642220 is software-proof reply publication only; "
    "docs/vendor/VENDOR_INDEX.md; no OKR percentage lift"
)

WRAPPER_KEYS = (
    CAPABILITY,
    f"{CAPABILITY}_summary",
    SOURCE_CAPABILITY,
    f"{SOURCE_CAPABILITY}_summary",
    decision_gate.ROBOT_ALIAS,
    ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "artifact",
    "summary",
    "payload",
    "data",
)


def _utc_now() -> str:
    # UTC 让 Docker/local 多轮 artifact 可以按字面时间排序。
    return datetime.now(timezone.utc).isoformat()


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖嵌套 key/value。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短单行，避免 raw body 或日志穿透输出。
    text = str(value if value is not None else default).replace("\n", " ").replace("\r", " ").strip()
    return material_pack._safe_text(text)[:240] if text else default


def _safe_list(value: Any, limit: int = 64) -> list[str]:
    # 列表元素只保留短标签；dict 只取 name/ref/status 这类元数据。
    if isinstance(value, list):
        output: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                text = item.get("name") or item.get("ref") or item.get("id") or item.get("status") or item.get("title")
            else:
                text = item
            safe = _safe_text(text)
            if safe:
                output.append(safe)
        return output
    if isinstance(value, dict):
        return [_safe_text(key) for key, item in value.items() if bool(item)]
    if value in (None, ""):
        return []
    safe = _safe_text(value)
    return [safe] if safe else []


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 输入不可读时直接 blocked，不把 traceback 或本机路径写进 summary。
    if not path:
        return {}, "owner_response_review_decision_json_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "owner_response_review_decision_json_missing"
    except json.JSONDecodeError:
        return {}, "owner_response_review_decision_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "owner_response_review_decision_json_read_error"
    if not isinstance(payload, dict):
        return {}, "owner_response_review_decision_json_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 字符串化 JSON 不展开，避免 raw payload 伪装成 safe wrapper。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归已知 wrapper key，避免任意 JSON 被当作 review-decision safe object。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # schema 命中时优先；否则保留顶层用于 unsupported 诊断。
    for candidate in _source_candidates(payload):
        if _safe_text(candidate.get("schema")) in SUPPORTED_SOURCE_SCHEMAS:
            return candidate
    return payload


def _safe_ref_from(payload: dict[str, Any]) -> str:
    # evidence_ref 允许出现在 source、safe_copy 或 owner_handoff 中。
    safe_copy = _dict(payload, "safe_copy")
    handoff = _dict(payload, "owner_handoff")
    return material_pack._safe_ref(
        payload.get("safe_evidence_ref")
        or payload.get("evidence_ref")
        or safe_copy.get("safe_evidence_ref")
        or safe_copy.get("evidence_ref")
        or handoff.get("safe_evidence_ref")
        or handoff.get("evidence_ref")
        or ""
    )


def _is_safe_surface(source: dict[str, Any]) -> bool:
    # 下游只接受 software_proof/not_proven/hardware_material_pending/false flags。
    encoded = _encoded(source)
    return (
        source.get("source") == "software_proof"
        and "software_proof" in encoded
        and "not_proven" in encoded
        and "hardware_material_pending" in encoded
        and source.get("safe_to_control") is False
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
    )


def _source_state(source: dict[str, Any], load_issue: str) -> dict[str, str]:
    # schema/capability/boundary 必须同时匹配上一 rung。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    schema = _safe_text(source.get("schema"))
    boundary = _safe_text(source.get("evidence_boundary") or source.get("boundary") or source.get("proof_boundary"))
    capability = _safe_text(source.get("capability") or SOURCE_CAPABILITY)
    if schema in SUPPORTED_SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY and capability == SOURCE_CAPABILITY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _source_review_decision(source: dict[str, Any]) -> str:
    # review decision 可能在 status、review_decision 或 safe_copy 中，均只读 safe 字段。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(source.get("review_decision") or source.get("status") or safe_copy.get("review_decision") or safe_copy.get("status") or "blocked")


def _material_status(source: dict[str, Any]) -> dict[str, Any]:
    # material_status 从 review-decision safe summary 派生，不能读取 raw owner-response body。
    source_status = _dict(source, "material_status")
    safe_copy = _dict(source, "safe_copy")
    copy_status = _dict(safe_copy, "material_status")
    status = source_status or copy_status
    return {
        "required_refs": _safe_list(status.get("required_refs") or decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
        "accepted_refs": _safe_list(status.get("accepted_refs") or status.get("material_refs") or status.get("accepted_materials")),
        "missing_refs": _safe_list(status.get("missing_refs") or status.get("missing_materials")),
        "rejected_refs": _safe_list(status.get("rejected_refs") or status.get("rejected_materials")),
        "accepted_count": int(status.get("accepted_count") or len(_safe_list(status.get("accepted_refs") or status.get("material_refs") or status.get("accepted_materials")))),
        "required_count": int(status.get("required_count") or len(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS)),
        "is_complete": bool(status.get("is_complete")),
    }


def _source_handoff(source: dict[str, Any]) -> dict[str, Any]:
    # 上一 rung 的 owner_handoff 只作为人工路由来源，不携带控制建议。
    handoff = _dict(source, "owner_handoff") or _dict(_dict(source, "safe_copy"), "owner_handoff")
    return {
        "source_primary_owner": _safe_text(handoff.get("primary_owner") or handoff.get("owner_role"), "Hardware Infra Engineer"),
        "source_owner_id": _safe_text(handoff.get("source_owner_id") or handoff.get("owner_id"), "unknown_owner"),
        "source_reviewer_next_step": _safe_text(handoff.get("reviewer_next_step"), "reviewer_closeout_candidate_not_proven"),
        "source_ready_for_reviewer_closeout": bool(handoff.get("ready_for_reviewer_closeout")),
    }


def _classify(
    load_issue: str,
    source_state: dict[str, str],
    source_decision: str,
    requested_ref: str,
    source_ref: str,
    source_safe: bool,
    unsafe_copy: bool,
    forbidden_claim: bool,
) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：输入、schema、证据号、安全扫描、上一 rung 状态。
    if load_issue:
        return BLOCKED_MISSING, [load_issue], 2
    if source_state["schema_status"] != "supported":
        return BLOCKED_MISSING, ["missing_or_unsupported_pr5_mandatory_sensor_material_owner_response_review_decision"], 2
    if not (requested_ref or source_ref):
        return BLOCKED_REF, ["missing_safe_evidence_ref"], 4
    if requested_ref and source_ref and requested_ref != source_ref:
        return BLOCKED_REF, ["owner_response_review_decision_evidence_ref_mismatch"], 4
    if not source_safe:
        return BLOCKED_MISSING, ["owner_response_review_decision_not_software_proof_not_proven_or_fail_closed_flags_missing"], 5
    if unsafe_copy:
        return REJECTED_UNSAFE, ["unsafe_or_raw_owner_response_review_decision_material_detected"], 5
    if forbidden_claim:
        return REJECTED_UNSAFE, ["hil_pr_resolution_o5_external_delivery_or_control_claim_detected"], 5
    if source_decision == decision_gate.ACCEPTED:
        return READY, ["owner_response_review_decision_accepted_for_handoff_not_proven"], 0
    if source_decision == decision_gate.NEEDS_MORE:
        return NEEDS_MORE, ["owner_response_review_decision_needs_more_material_not_proven"], 3
    if source_decision == decision_gate.REJECTED_UNSAFE:
        return REJECTED_UNSAFE, ["owner_response_review_decision_rejected_or_unsafe_not_proven"], 5
    if source_decision == decision_gate.BLOCKED_REF:
        return BLOCKED_REF, ["owner_response_review_decision_evidence_ref_mismatch"], 4
    return BLOCKED_MISSING, ["owner_response_review_decision_not_ready_for_handoff"], 2


def _next_required_evidence(handoff_status: str, evidence_ref: str, materials: dict[str, Any], reasons: list[str]) -> list[str]:
    # 下一步仍是人工材料履约，不是机器人控制、GitHub 写入或 OKR lift。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == READY:
        return [
            f"handoff sanitized owner-response review-decision summary to reviewer at evidence_ref={ref}",
            "collect real 2D LiDAR and ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL materials outside this gate",
            f"keep PR thread {THREAD_ID} unresolved and hardware_material_pending until live reviewer resolution evidence exists",
        ]
    if handoff_status == NEEDS_MORE:
        missing = materials["missing_refs"] or list(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS)
        return [f"provide missing safe owner response review material: {item} at evidence_ref={ref}" for item in missing]
    if handoff_status == REJECTED_UNSAFE:
        rejected = materials["rejected_refs"] or ["replace unsafe/raw/overclaim owner-response review-decision input"]
        return [f"replace rejected or unsafe handoff source material: {item} at evidence_ref={ref}" for item in rejected]
    return [f"rerun {CAPABILITY} with supported review-decision summary for evidence_ref={ref}", *reasons]


def _handoff_packet(
    handoff_status: str,
    evidence_ref: str,
    source_handoff: dict[str, Any],
    reasons: list[str],
    next_required: list[str],
) -> dict[str, Any]:
    # 三方 handoff 是人工复核对象，不是 transport envelope 或 action command。
    return {
        "primary_owner": "Hardware Infra Engineer",
        "support_owner": "Product Manager / OKR Owner",
        "reviewer_route": "PR #5 reviewer closeout route",
        "source_primary_owner": source_handoff["source_primary_owner"],
        "source_owner_id": source_handoff["source_owner_id"],
        "source_reviewer_next_step": source_handoff["source_reviewer_next_step"],
        "handoff_status": handoff_status,
        "safe_evidence_ref": evidence_ref or "<same_evidence_ref>",
        "evidence_ref": evidence_ref or "<same_evidence_ref>",
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "hardware_material_status": "hardware_material_pending",
        "ready_for_reviewer_handoff": handoff_status == READY,
        "ready_for_reviewer_closeout": False,
        "blocked": handoff_status in {BLOCKED_MISSING, BLOCKED_REF, REJECTED_UNSAFE},
        "handoff_reasons": reasons,
        "next_required_evidence": next_required,
        "source": "software_proof",
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS、serial、GitHub 写接口或网络。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_review_handoff.py --owner-response-review-decision-json <owner_response_review_decision_summary.json> --evidence-ref {ref}",
        "keep source=software_proof, hardware_material_pending, not_proven, delivery_success=false, primary_actions_enabled=false, and safe_to_control=false",
        f"keep PR thread {THREAD_ID} unresolved until live reviewer state changes outside this gate",
    ]


def _non_access_scope() -> list[str]:
    # 明确不可访问范围，防止把 handoff gate 误读为现场 proof。
    return [
        "raw_owner_response_body",
        "real_material_payload",
        "github_write_or_thread_resolution",
        "ros_graph",
        "serial_uart_devices",
        "wave_rover_runtime",
        "orange_pi_runtime",
        "real_2d_lidar",
        "real_tof",
        "sensor_driver_runtime",
        "hil",
        "field_run",
        "objective_5_external_infrastructure",
        "network",
        "delivery_execution",
    ]


def _source_summary(source: dict[str, Any], state: dict[str, str], source_decision: str, source_ref: str, source_safe: bool) -> dict[str, Any]:
    # source summary 只复制 safe 元数据，不复制完整 review-decision artifact。
    return {
        **state,
        "schema": _safe_text(source.get("schema")),
        "capability": SOURCE_CAPABILITY,
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or source.get("proof_boundary")),
        "source_review_decision": source_decision,
        "source_status": source_decision,
        "safe_evidence_ref": source_ref,
        "evidence_ref": source_ref,
        "source_is_software_proof_not_proven": bool(source_safe),
        "hardware_material_status": "hardware_material_pending",
    }


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    materials: dict[str, Any],
    handoff: dict[str, Any],
    next_required: list[str],
    rerun_commands: list[str],
) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，只保留状态和缺口摘要。
    return {
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "allowed_handoff_statuses": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "evidence_boundary": BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_review_decision": source_summary,
        "material_status": materials,
        "review_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": "not_proven",
        "software_proof": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _summary_payload(
    handoff_status: str,
    evidence_ref: str,
    reasons: list[str],
    source_summary: dict[str, Any],
    materials: dict[str, Any],
    handoff: dict[str, Any],
    next_required: list[str],
    rerun_commands: list[str],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是跨 Robot/Full-stack/Product 的稳定只读合同。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "allowed_handoff_statuses": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_review_decision": source_summary,
        "material_status": materials,
        "review_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "comment_3269642220_boundary": "software_proof_reply_publication_not_pr5_resolution",
        "no_okr_percentage_lift": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def build_pr5_mandatory_sensor_material_owner_response_review_handoff(
    owner_response_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 owner-response review-decision safe surface，生成 review-handoff artifact。"""

    payload, load_issue = _load_json(owner_response_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = material_pack._safe_ref(evidence_ref)
    source_ref = _safe_ref_from(source)
    effective_ref = requested_ref or source_ref
    state = _source_state(source, load_issue)
    source_decision = _source_review_decision(source) if source else "blocked"
    source_safe = bool(source) and _is_safe_surface(source)
    materials = _material_status(source) if source else {
        "required_refs": list(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
        "accepted_refs": [],
        "missing_refs": list(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
        "rejected_refs": [],
        "accepted_count": 0,
        "required_count": len(decision_gate.intake_gate.REQUIRED_RESPONSE_REFS),
        "is_complete": False,
    }
    unsafe_copy = bool(payload) and decision_gate._has_unsafe_copy(payload)
    forbidden_claim = bool(payload) and decision_gate._has_forbidden_claim(payload)
    handoff_status, reasons, exit_code = _classify(
        load_issue,
        state,
        source_decision,
        requested_ref,
        source_ref,
        source_safe,
        unsafe_copy,
        forbidden_claim,
    )
    source_summary = _source_summary(source, state, source_decision, source_ref, source_safe)
    source_handoff = _source_handoff(source) if source else {
        "source_primary_owner": "Hardware Infra Engineer",
        "source_owner_id": "unknown_owner",
        "source_reviewer_next_step": "reviewer_closeout_candidate_not_proven",
        "source_ready_for_reviewer_closeout": False,
    }
    next_required = _next_required_evidence(handoff_status, effective_ref, materials, reasons)
    handoff = _handoff_packet(handoff_status, effective_ref, source_handoff, reasons, next_required)
    rerun_commands = _rerun_commands(effective_ref)
    safe_copy = _safe_copy(handoff_status, effective_ref, reasons, source_summary, materials, handoff, next_required, rerun_commands)
    summary = _summary_payload(handoff_status, effective_ref, reasons, source_summary, materials, handoff, next_required, rerun_commands, safe_copy)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": "software_proof",
        "capability": CAPABILITY,
        "evidence_boundary": BOUNDARY,
        "boundary": BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "allowed_handoff_statuses": list(HANDOFF_STATUSES),
        "handoff_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "safe_evidence_ref": effective_ref,
        "evidence_ref": effective_ref,
        "same_evidence_ref_required": True,
        "source_owner_response_review_decision": source_summary,
        "material_status": materials,
        "review_handoff": handoff,
        "next_required_evidence": next_required,
        "rerun_commands": rerun_commands,
        "safe_copy": safe_copy,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_proof",
        "hardware_material_status": "hardware_material_pending",
        "not_proven": list(NOT_PROVEN),
        "software_proof": True,
        "non_access_scope": _non_access_scope(),
        "boundary_note": BOUNDARY_NOTE,
        "comment_3269642220_boundary": "software_proof_reply_publication_not_pr5_resolution",
        "no_okr_percentage_lift": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    if decision_gate._has_unsafe_copy(artifact) or decision_gate._has_unsafe_copy(summary) or decision_gate._has_forbidden_claim(artifact) or decision_gate._has_forbidden_claim(summary):
        # 最终防线：输出若仍含禁词，强制 rejected_unsafe 并保持 false flags。
        artifact["status"] = REJECTED_UNSAFE
        artifact["handoff_status"] = REJECTED_UNSAFE
        summary["status"] = REJECTED_UNSAFE
        summary["handoff_status"] = REJECTED_UNSAFE
        artifact["handoff_reasons"] = ["final_output_safety_scan_failed"]
        summary["handoff_reasons"] = ["final_output_safety_scan_failed"]
        artifact[f"{CAPABILITY}_summary"] = summary
        artifact[ROBOT_ALIAS] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
        exit_code = 5
    return artifact, summary, exit_code


def write_json(payload: dict[str, Any], output: str) -> None:
    # 写文件只是生成本地软件证明，不代表真实材料、PR resolution 或 HIL 到位。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 复跑。
    parser = argparse.ArgumentParser(
        description=(
            "Generate PR #5 mandatory sensor material owner-response review-handoff "
            "software-proof gate; keeps delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--owner-response-review-decision-json", "--input", dest="owner_response_review_decision_json", required=True, help="previous pr5_mandatory_sensor_material_owner_response_review_decision artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--evidence-ref", default="", help="expected safe evidence_ref shared by review-decision and review-handoff output")
    parser.add_argument("--output", default="", help="optional artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_pr5_mandatory_sensor_material_owner_response_review_handoff(
        args.owner_response_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pr5_mandatory_sensor_material_owner_response_review_handoff: artifact_file:{material_pack._safe_ref(args.output)}")
        if args.summary_output:
            print(f"owner_response_review_handoff_summary_file: {material_pack._safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
