"""Elevator field evidence trace diagnostics metadata helpers.

本模块承接 operator_gateway_diagnostics 的 elevator field evidence trace
callback 与 material backfill 摘要逻辑。这里仅迁移 software diagnostics metadata，
不新增电梯硬件、UART、底盘协议、HIL 或实车验收事实。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _redact_route_task_rehearsal_text,
    _route_task_field_run_readiness_copy_is_unsafe,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_task_field_retest import (
    _route_task_field_retest_execution_pack_has_success_wording,
)

# 本域摘要只能表达软件证据边界；保留本地常量可避免从 facade 反向导入形成循环。
EVIDENCE_SOURCE_SOFTWARE = "software_proof"

ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_intake.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_intake_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_callback_intake_gate"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_review_decision.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_review_handoff.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_intake.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_review_handoff.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1"
)
ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_elevator_field_evidence_trace_material_backfill_review_handoff_gate"
)


def _elevator_field_evidence_trace_callback_intake_not_proven(*sources):
    # Robot alias 只说明 safe callback 已进入软件证据链，不能替代任何现场材料或外部证明。
    defaults = [
        "real_route_elevator_field_pass",
        "real_elevator_door_state",
        "real_target_floor_confirmation",
        "real_human_assistance_record",
        "real_nav2_or_fixed_route_runtime",
        "real_route_completion_signal",
        "real_field_task_record",
        "real_dropoff_or_cancel_completion",
        "real_delivery_result",
        "real_phone_browser",
        "real_waverover_uart_hil",
        "objective_5_external_proof",
        "delivery_success",
    ]
    merged = []
    for item in defaults:
        if item not in merged:
            merged.append(item)
    for source in sources:
        if not isinstance(source, dict):
            continue
        for item in source.get("not_proven") if isinstance(source.get("not_proven"), list) else []:
            text = _redact_route_task_rehearsal_text(item).strip()
            if text and text not in merged:
                merged.append(text)
        for key in ("missing_required_materials", "missing_materials"):
            for item in source.get(key) if isinstance(source.get(key), list) else []:
                text = _redact_route_task_rehearsal_text(item).strip()
                if text and text not in merged:
                    merged.append(text)
    return merged


def _default_elevator_field_evidence_trace_callback_intake_summary(
    path,
    intake_status="blocked_missing_elevator_field_evidence_trace_callback_intake_summary",
    read_error="",
):
    # 缺省态必须 fail closed；Robot diagnostics 不能从 raw callback 或 trace 反推出现场成功。
    safe_copy = (
        "Elevator field evidence trace callback intake is metadata-only; "
        "software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": intake_status,
        "intake_status_detail": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace callback intake summary is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_trace": {},
        "source_diagnostics": {},
        "callback_packet": {},
        "accepted_callback_materials": [],
        "missing_required_materials": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_evidence_trace_callback_review_decision_not_proven(*sources):
    # review decision 只能说明复核层可读，不能把 owner handoff 写成现场通过。
    defaults = _elevator_field_evidence_trace_callback_intake_not_proven(
        *[source for source in sources if isinstance(source, dict)]
    )
    for item in (
        "real_reviewed_route_elevator_materials",
        "ready_for_real_field_execution",
    ):
        if item not in defaults:
            defaults.append(item)
    return defaults


def _default_elevator_field_evidence_trace_callback_review_decision_summary(
    path,
    review_decision="blocked_missing_elevator_field_evidence_trace_callback_review_decision_summary",
    read_error="",
):
    # 缺省态必须保持 read-only blocked，避免 Robot diagnostics 把缺材料解释成可执行动作。
    safe_copy = (
        "Elevator field evidence trace callback review decision is metadata-only; "
        "software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "overall_status": "not_proven",
        "review_decision": review_decision,
        "decision_status_detail": {
            "status": review_decision,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace callback review decision summary is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_callback_intake": {},
        "decision_reasons": [],
        "missing_required_materials": [],
        "rejected_callback_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_evidence_trace_callback_review_handoff_not_proven(*sources):
    # handoff 只表示 review decision 结果已经交接，不能证明现场材料、动作执行或成功。
    defaults = _elevator_field_evidence_trace_callback_review_decision_not_proven(
        *[source for source in sources if isinstance(source, dict)]
    )
    for item in (
        "real_review_handoff_ack",
        "real_owner_follow_up",
        "ready_for_real_field_execution",
    ):
        if item not in defaults:
            defaults.append(item)
    return defaults


def _default_elevator_field_evidence_trace_callback_review_handoff_summary(
    path,
    handoff_status="blocked_missing_elevator_field_evidence_trace_callback_review_handoff_summary",
    read_error="",
):
    # 缺省态必须保持 blocked；Robot diagnostics 只能展示安全交接摘要，不能产生 ACK 或控制副作用。
    safe_copy = (
        "Elevator field evidence trace callback review handoff is metadata-only; "
        "software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "overall_status": "not_proven",
        "handoff_status": handoff_status,
        "handoff_status_detail": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace callback review handoff summary is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_review_decision": {},
        "handoff_reasons": [],
        "missing_required_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_callback_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_evidence_trace_material_backfill_intake_not_proven(*sources):
    # backfill intake 只是补材料入口，不能升级成真实 field pass、HIL 或交付成功。
    defaults = _elevator_field_evidence_trace_callback_review_handoff_not_proven(
        *[source for source in sources if isinstance(source, dict)]
    )
    for item in (
        "real_material_backfill_review",
        "real_field_material_collection",
        "real_route_elevator_field_pass",
        "ready_for_real_field_execution",
    ):
        if item not in defaults:
            defaults.append(item)
    return defaults


def _default_elevator_field_evidence_trace_material_backfill_intake_summary(
    path,
    intake_status="blocked_missing_elevator_field_evidence_trace_material_backfill_intake_summary",
    read_error="",
):
    # 缺省态必须维持 blocked/not_proven；Robot 只展示安全摘要，不创建材料回填动作。
    safe_copy = (
        "Elevator field evidence trace material backfill intake is metadata-only; "
        "software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "overall_status": "not_proven",
        "intake_status": intake_status,
        "intake_status_detail": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace material backfill intake summary is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "source_callback_review_handoff": {},
        "accepted_backfill_materials": [],
        "missing_required_materials": [],
        "rejected_backfill_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_material_backfill_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }
















def _elevator_field_evidence_trace_material_backfill_review_decision_not_proven(
    *sources,
):
    # review decision 只是材料复核结论，必须继承 intake 的真实执行边界。
    defaults = _elevator_field_evidence_trace_material_backfill_intake_not_proven(
        *[source for source in sources if isinstance(source, dict)]
    )
    for item in (
        "real_material_backfill_review_handoff",
        "real_required_material_backfill",
        "real_delivery_result",
        "objective_5_external_proof",
    ):
        if item not in defaults:
            defaults.append(item)
    return defaults


def _default_elevator_field_evidence_trace_material_backfill_review_decision_summary(
    path,
    decision_status=(
        "blocked_missing_elevator_field_evidence_trace_material_backfill_review_decision_summary"
    ),
    read_error="",
):
    # 缺省态必须 fail closed；Robot diagnostics 不能从缺失材料复核推导出现场可执行。
    safe_copy = (
        "Elevator field evidence trace material backfill review decision is "
        "metadata-only; software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "overall_status": "not_proven",
        "review_decision": decision_status,
        "review_decision_detail": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace material backfill review decision is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "blocked",
        "source_intake": {},
        "accepted_material_refs": [],
        "missing_required_materials": [],
        "rejected_materials": [],
        "decision_reasons": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_material_backfill_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_evidence_trace_material_backfill_review_handoff_not_proven(
    *sources,
):
    # handoff 只是现场 owner 交接包，必须继承 review decision 的未证实边界。
    defaults = _elevator_field_evidence_trace_material_backfill_review_decision_not_proven(
        *[source for source in sources if isinstance(source, dict)]
    )
    for item in (
        "real_field_owner_material_backfill_rerun",
        "real_material_backfill_review_handoff",
        "real_route_elevator_field_pass",
        "real_phone_browser",
        "delivery_success",
    ):
        if item not in defaults:
            defaults.append(item)
    return defaults


def _default_elevator_field_evidence_trace_material_backfill_review_handoff_summary(
    path,
    handoff_status=(
        "blocked_missing_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
    ),
    read_error="",
):
    # 缺省态必须 fail closed；Robot 不从缺失 handoff 推导现场可 rerun。
    safe_copy = (
        "Elevator field evidence trace material backfill review handoff is "
        "metadata-only; software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "overall_status": "not_proven",
        "handoff_status": handoff_status,
        "handoff_status_detail": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": read_error
            or "elevator field evidence trace material backfill review handoff is not configured",
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "blocked",
        "source_review_decision": {},
        "field_owner_handoff": [],
        "safe_rerun_hints": [],
        "phone_safe_copy": [],
        "missing_required_materials": [],
        "rejected_materials": [],
        "next_required_evidence": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _elevator_field_evidence_trace_material_backfill_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _elevator_field_evidence_trace_callback_intake_source_contract(value):
    # 只信任 Autonomy 产出的 artifact/summary contract；summary 缺 source 时回指本轮 artifact。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_callback_intake_has_disabled_actions(
    intake,
    summary_fragment,
):
    # 顶层 source 和安全 summary 都必须显式 false；缺字段不能被解释成动作授权。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    delivery_success = (
        summary_fragment.get("delivery_success")
        if "delivery_success" in summary_fragment
        else intake.get("delivery_success")
    )
    primary_actions_enabled = (
        summary_fragment.get("primary_actions_enabled")
        if "primary_actions_enabled" in summary_fragment
        else intake.get("primary_actions_enabled")
    )
    return delivery_success is False and primary_actions_enabled is False


def _elevator_field_evidence_trace_callback_intake_has_unsafe_fields(value):
    # 本 alias 不读取 raw callback body、命令、ACK、cursor 或设备字段；发现这类字段直接降级。
    unsafe_key_fragments = (
        "raw",
        "body",
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "artifact_path",
        "local_path",
        "file_path",
        "ros_topic",
        "topic_name",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack_payload",
        "ack_post",
        "remote_ack",
        "terminal_ack",
        "cursor",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _elevator_field_evidence_trace_callback_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(_elevator_field_evidence_trace_callback_intake_has_unsafe_fields(item) for item in value)
    if isinstance(value, str):
        return (
            _route_task_field_run_readiness_copy_is_unsafe(value)
            or _route_task_field_retest_execution_pack_has_success_wording(value)
        )
    return False


def summarize_elevator_field_evidence_trace_callback_intake(source):
    """构建 elevator field evidence trace callback intake 的 metadata-only Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_callback_intake_summary("")
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_callback_intake_summary(
            source_path,
            read_error="elevator field evidence trace callback intake summary is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["intake_status"] = "blocked_missing_elevator_field_evidence_trace_callback_intake_summary"
            summary["intake_status_detail"] = {
                "status": summary["intake_status"],
                "verdict": "not_proven",
                "reason": "elevator field evidence trace callback intake summary artifact missing",
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading elevator field evidence trace callback intake summary: {exc}"
            )
            summary["intake_status"] = "read_error"
            summary["intake_status_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_callback_intake_summary(source_path)
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary["intake_status"] = "read_error"
        summary["intake_status_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake JSON must be an object",
        }
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("elevator_field_evidence_trace_callback_intake_summary"),
            intake.get("robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary"),
            intake.get("robot_compatible_summary"),
            diagnostics.get("elevator_field_evidence_trace_callback_intake_summary"),
            diagnostics.get("robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_callback_intake_source_contract(contract_source)
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
        }
    )
    if (
        not summary_fragment
        and (source_schema or source_boundary)
        and (
            source_schema != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SCHEMA
            or source_boundary != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_GATE
        )
    ):
        summary["intake_status"] = "unsupported_schema"
        summary["intake_status_detail"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake schema or evidence boundary is unsupported",
        }
        return summary
    if not summary_fragment:
        summary["intake_status"] = "blocked_missing_elevator_field_evidence_trace_callback_intake_summary"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake lacks a sanitized summary",
        }
        return summary

    status_source = (
        summary_fragment.get("intake_status_detail")
        if isinstance(summary_fragment.get("intake_status_detail"), dict)
        else {}
    )
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "not_proven"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace callback intake is metadata-only; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "intake_status": intake_status,
            "intake_status_detail": {
                "status": intake_status,
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "elevator field evidence trace callback intake consumed as software_proof"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "source_trace": _safe_pc_route_debug_dict(summary_fragment.get("source_trace")),
            "source_diagnostics": _safe_pc_route_debug_dict(
                summary_fragment.get("source_diagnostics")
            ),
            "callback_packet": _safe_pc_route_debug_dict(
                summary_fragment.get("callback_packet")
            ),
            "accepted_callback_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_callback_materials")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": _elevator_field_evidence_trace_callback_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    if (
        source_schema != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SCHEMA
        or source_boundary != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_GATE
    ):
        summary["intake_status"] = "unsupported_schema"
        summary["intake_status_detail"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake schema or evidence boundary is unsupported",
        }
        summary["source_trace"] = {}
        summary["source_diagnostics"] = {}
        summary["callback_packet"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith("local_path_redacted:"):
        summary["intake_status"] = "blocked_missing_evidence_ref"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake is missing a safe evidence_ref",
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["intake_status"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake evidence_ref values do not match",
        }
        return summary
    if not summary["same_evidence_ref_required"]:
        summary["intake_status"] = "same_evidence_ref_required_false"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": "elevator field evidence trace callback intake must require the same evidence_ref",
        }
        return summary
    if (
        not _elevator_field_evidence_trace_callback_intake_has_disabled_actions(
            intake,
            summary_fragment,
        )
        or _elevator_field_evidence_trace_callback_intake_has_unsafe_fields(summary_fragment)
        or _elevator_field_evidence_trace_callback_intake_has_unsafe_fields(robot_summary)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "Elevator field evidence trace callback intake was blocked because "
            "summary fields could expose raw callback/control data or imply success; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "intake_status": "blocked_unsafe_elevator_field_evidence_trace_callback_intake_summary",
                "intake_status_detail": {
                    "status": "blocked_unsafe_elevator_field_evidence_trace_callback_intake_summary",
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw callback fields, or enabled actions",
                },
                "source_trace": {},
                "source_diagnostics": {},
                "callback_packet": {},
                "accepted_callback_materials": [],
                "missing_required_materials": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def _elevator_field_evidence_trace_callback_review_decision_source_contract(value):
    # summary 可来自 Autonomy artifact、fixture 或上游 diagnostics alias，但 source contract 必须仍回指 Autonomy gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields(value):
    # review decision 只能带安全摘要字段；任何 raw/control/credential/device 字段都要 fail closed。
    unsafe_key_fragments = (
        "raw",
        "body",
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "artifact_path",
        "local_path",
        "file_path",
        "ros_topic",
        "topic_name",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack_payload",
        "ack_post",
        "remote_ack",
        "terminal_ack",
        "cursor",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields(item)
            for item in value
        )
    if isinstance(value, str):
        return (
            _route_task_field_run_readiness_copy_is_unsafe(value)
            or _route_task_field_retest_execution_pack_has_success_wording(value)
        )
    return False


def summarize_elevator_field_evidence_trace_callback_review_decision(source):
    """构建 elevator field evidence trace callback review decision 的只读 Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_callback_review_decision_summary("")
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_callback_review_decision_summary(
            source_path,
            read_error=(
                "elevator field evidence trace callback review decision summary "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["review_decision"] = (
                "blocked_missing_elevator_field_evidence_trace_callback_review_decision_summary"
            )
            summary["decision_status_detail"] = {
                "status": summary["review_decision"],
                "verdict": "not_proven",
                "reason": (
                    "elevator field evidence trace callback review decision summary "
                    "artifact missing"
                ),
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading elevator field evidence trace callback review decision summary: {exc}"
            )
            summary["review_decision"] = "read_error"
            summary["decision_status_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_callback_review_decision_summary(
        source_path
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary["review_decision"] = "read_error"
        summary["decision_status_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision JSON must be an object"
            ),
        }
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        in (
            ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
            ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
        )
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("elevator_field_evidence_trace_callback_review_decision_summary"),
            decision.get(
                "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            diagnostics.get("elevator_field_evidence_trace_callback_review_decision_summary"),
            diagnostics.get(
                "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_callback_review_decision_source_contract(
            contract_source
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
        }
    )
    if not summary_fragment:
        summary["review_decision"] = (
            "blocked_missing_elevator_field_evidence_trace_callback_review_decision_summary"
        )
        summary["decision_status_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision lacks a sanitized summary"
            ),
        }
        return summary

    status_source = (
        summary_fragment.get("decision_status_detail")
        if isinstance(summary_fragment.get("decision_status_detail"), dict)
        else {}
    )
    review_decision = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("review_decision")
        or summary_fragment.get("status")
        or "blocked_missing_elevator_field_evidence_trace_callback_review_decision_summary"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace callback review decision is metadata-only; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(
        decision.get("safe_evidence_ref") or decision.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or ""
            ),
            "overall_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("overall_status") or ""
            ),
            "review_decision": review_decision,
            "decision_status_detail": {
                "status": review_decision,
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "elevator field evidence trace callback review decision "
                        "consumed as software_proof"
                    )
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "source_callback_intake": _safe_pc_route_debug_dict(
                summary_fragment.get("source_callback_intake")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "rejected_callback_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_callback_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_decision,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": (
                _elevator_field_evidence_trace_callback_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    if (
        source_schema != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary["review_decision"] = "unsupported_schema"
        summary["decision_status_detail"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision schema "
                "or evidence boundary is unsupported"
            ),
        }
        summary["source_callback_intake"] = {}
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or summary["overall_status"] != "not_proven":
        summary["review_decision"] = (
            "blocked_unsupported_elevator_field_evidence_trace_callback_review_decision_summary"
        )
        summary["decision_status_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": "review decision must be software_proof and not_proven",
        }
        summary["source_callback_intake"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["review_decision"] = "blocked_missing_evidence_ref"
        summary["decision_status_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision is missing "
                "a safe evidence_ref"
            ),
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_decision"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["decision_status_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision evidence_ref "
                "values do not match"
            ),
        }
        return summary
    if not summary["same_evidence_ref_required"]:
        summary["review_decision"] = "same_evidence_ref_required_false"
        summary["decision_status_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review decision must require "
                "the same evidence_ref"
            ),
        }
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields(
            robot_summary
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "Elevator field evidence trace callback review decision was blocked "
            "because summary fields could expose raw callback/control data or imply success; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision": (
                    "blocked_unsafe_elevator_field_evidence_trace_callback_review_decision_summary"
                ),
                "decision_status_detail": {
                    "status": (
                        "blocked_unsafe_elevator_field_evidence_trace_callback_review_decision_summary"
                    ),
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw callback fields, or enabled actions",
                },
                "source_callback_intake": {},
                "decision_reasons": [],
                "missing_required_materials": [],
                "rejected_callback_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def _elevator_field_evidence_trace_callback_review_handoff_source_contract(value):
    # handoff 可来自 Autonomy artifact、summary 或已包装的 Robot alias，但 source contract 必须仍回指 handoff gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields(value):
    # handoff 只允许 safe metadata；任何 raw/control/ACK/cursor/device 字段都按不安全处理。
    unsafe_key_fragments = (
        "raw",
        "body",
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "artifact_path",
        "local_path",
        "file_path",
        "ros_topic",
        "topic_name",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack_payload",
        "ack_post",
        "remote_ack",
        "terminal_ack",
        "cursor",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields(item)
            for item in value
        )
    if isinstance(value, str):
        return (
            _route_task_field_run_readiness_copy_is_unsafe(value)
            or _route_task_field_retest_execution_pack_has_success_wording(value)
        )
    return False


def summarize_elevator_field_evidence_trace_callback_review_handoff(source):
    """构建 elevator field evidence trace callback review handoff 的只读 Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_callback_review_handoff_summary("")
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_callback_review_handoff_summary(
            source_path,
            read_error=(
                "elevator field evidence trace callback review handoff summary "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["handoff_status"] = (
                "blocked_missing_elevator_field_evidence_trace_callback_review_handoff_summary"
            )
            summary["handoff_status_detail"] = {
                "status": summary["handoff_status"],
                "verdict": "not_proven",
                "reason": (
                    "elevator field evidence trace callback review handoff summary "
                    "artifact missing"
                ),
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading elevator field evidence trace callback review handoff summary: {exc}"
            )
            summary["handoff_status"] = "read_error"
            summary["handoff_status_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_callback_review_handoff_summary(
        source_path
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary["handoff_status"] = "read_error"
        summary["handoff_status_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff JSON must be an object"
            ),
        }
        return summary

    diagnostics = (
        handoff.get("diagnostics")
        if isinstance(handoff.get("diagnostics"), dict)
        else {}
    )
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        in (
            ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
            ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
        )
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("elevator_field_evidence_trace_callback_review_handoff_summary"),
            handoff.get(
                "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary"
            ),
            handoff.get("robot_compatible_summary"),
            diagnostics.get("elevator_field_evidence_trace_callback_review_handoff_summary"),
            diagnostics.get(
                "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_callback_review_handoff_source_contract(
            contract_source
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
        }
    )
    if not summary_fragment:
        summary["handoff_status"] = (
            "blocked_missing_elevator_field_evidence_trace_callback_review_handoff_summary"
        )
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff lacks a sanitized summary"
            ),
        }
        return summary

    status_source = (
        summary_fragment.get("handoff_status_detail")
        if isinstance(summary_fragment.get("handoff_status_detail"), dict)
        else {}
    )
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked_missing_elevator_field_evidence_trace_callback_review_handoff_summary"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace callback review handoff is metadata-only; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(
        handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or ""
            ),
            "overall_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("overall_status") or ""
            ),
            "handoff_status": handoff_status,
            "handoff_status_detail": {
                "status": handoff_status,
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "elevator field evidence trace callback review handoff "
                        "consumed as software_proof"
                    )
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "source_review_decision": _safe_pc_route_debug_dict(
                summary_fragment.get("source_review_decision")
            ),
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": (
                _elevator_field_evidence_trace_callback_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    if (
        source_schema != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary != ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_GATE
    ):
        summary["handoff_status"] = "unsupported_schema"
        summary["handoff_status_detail"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff schema "
                "or evidence boundary is unsupported"
            ),
        }
        summary["source_review_decision"] = {}
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or summary["overall_status"] != "not_proven":
        summary["handoff_status"] = (
            "blocked_unsupported_elevator_field_evidence_trace_callback_review_handoff_summary"
        )
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": "review handoff must be software_proof and not_proven",
        }
        summary["source_review_decision"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["handoff_status"] = "blocked_missing_evidence_ref"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff is missing "
                "a safe evidence_ref"
            ),
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["handoff_status"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff evidence_ref "
                "values do not match"
            ),
        }
        return summary
    if not summary["same_evidence_ref_required"]:
        summary["handoff_status"] = "same_evidence_ref_required_false"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace callback review handoff must require "
                "the same evidence_ref"
            ),
        }
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields(
            robot_summary
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "Elevator field evidence trace callback review handoff was blocked "
            "because summary fields could expose raw callback/control data or imply success; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": (
                    "blocked_unsafe_elevator_field_evidence_trace_callback_review_handoff_summary"
                ),
                "handoff_status_detail": {
                    "status": (
                        "blocked_unsafe_elevator_field_evidence_trace_callback_review_handoff_summary"
                    ),
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw callback fields, or enabled actions",
                },
                "source_review_decision": {},
                "handoff_reasons": [],
                "missing_required_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def _elevator_field_evidence_trace_material_backfill_intake_source_contract(value):
    # summary、artifact 和 Robot alias 都必须回指 Autonomy 的 material backfill intake gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SUMMARY_SCHEMA,
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_ROBOT_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_material_backfill_review_decision_source_contract(
    value,
):
    # review decision 可以来自 artifact、summary 或 Robot alias；summary 必须回指同一 gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA,
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_material_backfill_review_handoff_source_contract(
    value,
):
    # handoff 可以来自 artifact、summary 或 Robot alias；summary 必须回指同一 handoff gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(value):
    # 回填入口只能带白名单元数据；raw、控制、ACK、设备、凭证或成功语义都必须降级。
    unsafe_key_fragments = (
        "raw",
        "body",
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "artifact_path",
        "local_path",
        "file_path",
        "ros_topic",
        "topic_name",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack_payload",
        "ack_post",
        "remote_ack",
        "terminal_ack",
        "cursor",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(item)
            for item in value
        )
    if isinstance(value, str):
        return (
            _route_task_field_run_readiness_copy_is_unsafe(value)
            or _route_task_field_retest_execution_pack_has_success_wording(value)
        )
    return False


def _elevator_field_evidence_trace_material_backfill_review_decision_has_unsafe_fields(
    value,
):
    # 复核结论复用 intake 的红线；任何 raw/控制/设备/成功语义都不能进入 alias。
    return _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(
        value
    )


def _elevator_field_evidence_trace_material_backfill_review_handoff_has_unsafe_fields(
    value,
):
    # handoff 仍只允许安全摘要；rerun hints 不能变成 ACK、cursor 或机器人动作。
    return _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(
        value
    )


def summarize_elevator_field_evidence_trace_material_backfill_intake(source):
    """构建 elevator field evidence trace material backfill intake 的只读 Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_material_backfill_intake_summary("")
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_material_backfill_intake_summary(
            source_path,
            read_error=(
                "elevator field evidence trace material backfill intake summary "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["intake_status"] = (
                "blocked_missing_elevator_field_evidence_trace_material_backfill_intake_summary"
            )
            summary["intake_status_detail"] = {
                "status": summary["intake_status"],
                "verdict": "not_proven",
                "reason": (
                    "elevator field evidence trace material backfill intake summary "
                    "artifact missing"
                ),
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading elevator field evidence trace material backfill "
                f"intake summary: {exc}"
            )
            summary["intake_status"] = "read_error"
            summary["intake_status_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_material_backfill_intake_summary(
        source_path
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary["intake_status"] = "read_error"
        summary["intake_status_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake JSON must be an object"
            ),
        }
        return summary

    diagnostics = (
        intake.get("diagnostics")
        if isinstance(intake.get("diagnostics"), dict)
        else {}
    )
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        in (
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SUMMARY_SCHEMA,
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_ROBOT_SUMMARY_SCHEMA,
        )
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("elevator_field_evidence_trace_material_backfill_intake_summary"),
            intake.get(
                "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary"
            ),
            intake.get("robot_compatible_summary"),
            diagnostics.get("elevator_field_evidence_trace_material_backfill_intake_summary"),
            diagnostics.get(
                "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_material_backfill_intake_source_contract(
            contract_source
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
        }
    )
    if not summary_fragment:
        summary["intake_status"] = (
            "blocked_missing_elevator_field_evidence_trace_material_backfill_intake_summary"
        )
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake lacks "
                "a sanitized summary"
            ),
        }
        return summary

    status_source = (
        summary_fragment.get("intake_status_detail")
        if isinstance(summary_fragment.get("intake_status_detail"), dict)
        else {}
    )
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked_missing_elevator_field_evidence_trace_material_backfill_intake_summary"
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace material backfill intake is metadata-only; "
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(
        intake.get("safe_evidence_ref") or intake.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or ""
            ),
            "overall_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("overall_status") or ""
            ),
            "intake_status": intake_status,
            "intake_status_detail": {
                "status": intake_status,
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "elevator field evidence trace material backfill intake "
                        "consumed as software_proof"
                    )
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "source_callback_review_handoff": _safe_pc_route_debug_dict(
                summary_fragment.get("source_callback_review_handoff")
                or summary_fragment.get("source_review_handoff")
            ),
            "accepted_backfill_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_backfill_materials")
                or summary_fragment.get("accepted_materials")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "rejected_backfill_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_backfill_materials")
                or summary_fragment.get("rejected_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": (
                _elevator_field_evidence_trace_material_backfill_intake_not_proven(
                    intake,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    if (
        source_schema != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SCHEMA
        or source_boundary != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_GATE
    ):
        summary["intake_status"] = "unsupported_schema"
        summary["intake_status_detail"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake schema "
                "or evidence boundary is unsupported"
            ),
        }
        summary["source_callback_review_handoff"] = {}
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or summary["overall_status"] != "not_proven":
        summary["intake_status"] = (
            "blocked_unsupported_elevator_field_evidence_trace_material_backfill_intake_summary"
        )
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": "material backfill intake must be software_proof and not_proven",
        }
        summary["source_callback_review_handoff"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["intake_status"] = "blocked_missing_evidence_ref"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake is missing "
                "a safe evidence_ref"
            ),
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["intake_status"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake evidence_ref "
                "values do not match"
            ),
        }
        return summary
    if not summary["same_evidence_ref_required"]:
        summary["intake_status"] = "same_evidence_ref_required_false"
        summary["intake_status_detail"] = {
            "status": summary["intake_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill intake must require "
                "the same evidence_ref"
            ),
        }
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(
            summary_fragment
        )
        or _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields(
            robot_summary
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "Elevator field evidence trace material backfill intake was blocked "
            "because summary fields could expose raw/control data or imply success; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "intake_status": (
                    "blocked_unsafe_elevator_field_evidence_trace_material_backfill_intake_summary"
                ),
                "intake_status_detail": {
                    "status": (
                        "blocked_unsafe_elevator_field_evidence_trace_material_backfill_intake_summary"
                    ),
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw fields, or enabled actions",
                },
                "source_callback_review_handoff": {},
                "accepted_backfill_materials": [],
                "missing_required_materials": [],
                "rejected_backfill_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_elevator_field_evidence_trace_material_backfill_review_decision(
    source,
):
    """构建 material backfill review decision 的只读 Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_material_backfill_review_decision_summary(
                ""
            )
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_material_backfill_review_decision_summary(
            source_path,
            read_error=(
                "elevator field evidence trace material backfill review decision "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["review_decision"] = (
                "blocked_missing_elevator_field_evidence_trace_material_backfill_review_decision_summary"
            )
            summary["review_decision_detail"] = {
                "status": summary["review_decision"],
                "verdict": "not_proven",
                "reason": (
                    "elevator field evidence trace material backfill review decision "
                    "artifact missing"
                ),
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading elevator field evidence trace material backfill "
                f"review decision: {exc}"
            )
            summary["review_decision"] = "read_error"
            summary["review_decision_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_material_backfill_review_decision_summary(
        source_path
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary["review_decision"] = "read_error"
        summary["review_decision_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review decision JSON "
                "must be an object"
            ),
        }
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    config = (
        decision.get("config") if isinstance(decision.get("config"), dict) else {}
    )
    status = (
        decision.get("status") if isinstance(decision.get("status"), dict) else {}
    )
    # Robot 只消费 summary-only 白名单；artifact 本体如果带 raw 字段会在后续 unsafe gate 降级。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        in (
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA,
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
        )
        or (
            str(decision.get("schema") or "")
            == ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SCHEMA
            and any(
                key in decision
                for key in (
                    "review_decision",
                    "source_intake",
                    "accepted_material_refs",
                    "missing_required_materials",
                    "rejected_materials",
                    "decision_reasons",
                    "owner_handoff",
                    "next_required_evidence",
                )
            )
        )
        else {}
    )
    for candidate in (
        decision.get(
            "elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ),
        decision.get("elevator_field_evidence_trace_material_backfill_review_decision"),
        decision.get(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ),
        decision.get("robot_compatible_summary"),
        decision.get("phone_safe_summary"),
        decision.get("mobile_readonly_summary"),
        diagnostics.get(
            "elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ),
        diagnostics.get("elevator_field_evidence_trace_material_backfill_review_decision"),
        diagnostics.get(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        config.get("elevator_field_evidence_trace_material_backfill_review_decision_summary"),
        status.get("elevator_field_evidence_trace_material_backfill_review_decision_summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_material_backfill_review_decision_source_contract(
            contract_source
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
        }
    )
    if not summary_fragment:
        summary["review_decision"] = (
            "blocked_missing_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        )
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review decision "
                "lacks a sanitized summary"
            ),
        }
        return summary

    decision_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked_missing_elevator_field_evidence_trace_material_backfill_review_decision_summary"
    )
    detail_source = (
        summary_fragment.get("review_decision_detail")
        if isinstance(summary_fragment.get("review_decision_detail"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace material backfill review decision "
            "is metadata-only; software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(
        decision.get("safe_evidence_ref") or decision.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or ""
            ),
            "overall_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("overall_status") or ""
            ),
            "review_decision": decision_status,
            "review_decision_detail": {
                "status": decision_status,
                "verdict": _redact_route_task_rehearsal_text(
                    detail_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    detail_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "elevator field evidence trace material backfill review "
                        "decision consumed as software_proof"
                    )
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("same_evidence_ref_status") or "matched"
            ),
            "source_intake": _safe_pc_route_debug_dict(
                summary_fragment.get("source_intake")
            ),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted_materials")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("owner_handoff")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": (
                _elevator_field_evidence_trace_material_backfill_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    required_summary_fields = (
        summary["review_decision"],
        isinstance(summary["source_intake"], dict),
        isinstance(summary["accepted_material_refs"], list),
        isinstance(summary["missing_required_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["decision_reasons"], list),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["owner_handoff"], list),
    )
    if (
        source_schema
        != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SCHEMA
        or source_boundary
        != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_decision": "unsupported_schema",
                "review_decision_detail": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "elevator field evidence trace material backfill review "
                        "decision schema or evidence boundary is unsupported"
                    ),
                },
                "source_intake": {},
                "accepted_material_refs": [],
                "missing_required_materials": [],
                "rejected_materials": [],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or summary["overall_status"] != "not_proven":
        summary["review_decision"] = (
            "blocked_unsupported_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        )
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": "material backfill review decision must be software_proof and not_proven",
        }
        summary["source_intake"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["review_decision"] = "blocked_missing_evidence_ref"
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review decision "
                "is missing a safe evidence_ref"
            ),
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_decision"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review decision "
                "evidence_ref values do not match"
            ),
        }
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or summary["same_evidence_ref_status"] not in ("matched", "same_evidence_ref_matched")
    ):
        summary["review_decision"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review decision "
                "must require and report the same evidence_ref"
            ),
        }
        return summary
    if not all(required_summary_fields):
        summary["review_decision"] = (
            "blocked_missing_elevator_field_evidence_trace_material_backfill_review_decision_summary"
        )
        summary["review_decision_detail"] = {
            "status": summary["review_decision"],
            "verdict": "not_proven",
            "reason": "material backfill review decision is missing safe summary fields",
        }
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _elevator_field_evidence_trace_material_backfill_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _elevator_field_evidence_trace_material_backfill_review_decision_has_unsafe_fields(
            robot_summary
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "Elevator field evidence trace material backfill review decision was "
            "blocked because summary fields could expose raw/control data or imply "
            "success; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision": (
                    "blocked_unsafe_elevator_field_evidence_trace_material_backfill_review_decision_summary"
                ),
                "review_decision_detail": {
                    "status": (
                        "blocked_unsafe_elevator_field_evidence_trace_material_backfill_review_decision_summary"
                    ),
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw fields, or enabled actions",
                },
                "source_intake": {},
                "accepted_material_refs": [],
                "missing_required_materials": [],
                "rejected_materials": [],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_elevator_field_evidence_trace_material_backfill_review_handoff(source):
    """构建 material backfill review handoff 的只读 Robot diagnostics 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        if not source:
            return _default_elevator_field_evidence_trace_material_backfill_review_handoff_summary(
                ""
            )
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_elevator_field_evidence_trace_material_backfill_review_handoff_summary(
            source_path,
            read_error=(
                "elevator field evidence trace material backfill review handoff "
                "is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["handoff_status"] = (
                "blocked_missing_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
            )
            summary["handoff_status_detail"] = {
                "status": summary["handoff_status"],
                "verdict": "not_proven",
                "reason": (
                    "elevator field evidence trace material backfill review handoff "
                    "artifact missing"
                ),
            }
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading elevator field evidence trace material backfill "
                f"review handoff: {exc}"
            )
            summary["handoff_status"] = "read_error"
            summary["handoff_status_detail"] = {
                "status": "read_error",
                "verdict": "not_proven",
                "reason": safe_error,
            }
            summary["read_error"] = safe_error
            return summary

    summary = _default_elevator_field_evidence_trace_material_backfill_review_handoff_summary(
        source_path
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary["handoff_status"] = "read_error"
        summary["handoff_status_detail"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review handoff JSON "
                "must be an object"
            ),
        }
        return summary

    diagnostics = (
        handoff.get("diagnostics")
        if isinstance(handoff.get("diagnostics"), dict)
        else {}
    )
    config = handoff.get("config") if isinstance(handoff.get("config"), dict) else {}
    status = handoff.get("status") if isinstance(handoff.get("status"), dict) else {}
    # Robot 只信任 Autonomy 已裁剪的 handoff summary；artifact 本体若带 raw 字段会被 unsafe gate 阻断。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        in (
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
            ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
        )
        or (
            str(handoff.get("schema") or "")
            == ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SCHEMA
            and any(
                key in handoff
                for key in (
                    "handoff_status",
                    "source_review_decision",
                    "field_owner_handoff",
                    "safe_rerun_hints",
                    "phone_safe_copy",
                    "missing_required_materials",
                )
            )
        )
        else {}
    )
    for candidate in (
        handoff.get(
            "elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ),
        handoff.get("elevator_field_evidence_trace_material_backfill_review_handoff"),
        handoff.get(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ),
        handoff.get("robot_compatible_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("mobile_readonly_summary"),
        diagnostics.get(
            "elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ),
        diagnostics.get("elevator_field_evidence_trace_material_backfill_review_handoff"),
        diagnostics.get(
            "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
        config.get("elevator_field_evidence_trace_material_backfill_review_handoff_summary"),
        status.get("elevator_field_evidence_trace_material_backfill_review_handoff_summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _elevator_field_evidence_trace_material_backfill_review_handoff_source_contract(
            contract_source
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
        }
    )
    if not summary_fragment:
        summary["handoff_status"] = (
            "blocked_missing_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        )
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review handoff "
                "lacks a sanitized summary"
            ),
        }
        return summary

    handoff_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked_missing_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
    )
    detail_source = (
        summary_fragment.get("handoff_status_detail")
        if isinstance(summary_fragment.get("handoff_status_detail"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Elevator field evidence trace material backfill review handoff "
            "is metadata-only; software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    )
    if "delivery_success=false" not in safe_copy:
        safe_copy = f"{safe_copy}; delivery_success=false; primary_actions_enabled=false."
    source_ref = str(
        handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    phone_safe_copy = _safe_route_task_rehearsal_list(
        summary_fragment.get("phone_safe_copy")
        or summary_fragment.get("phone_copy")
        or summary_fragment.get("safe_phone_copy")
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or ""
            ),
            "overall_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("overall_status") or ""
            ),
            "handoff_status": handoff_status,
            "handoff_status_detail": {
                "status": handoff_status,
                "verdict": _redact_route_task_rehearsal_text(
                    detail_source.get("verdict") or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    detail_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "elevator field evidence trace material backfill review "
                        "handoff consumed as software_proof"
                    )
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("same_evidence_ref_status") or "matched"
            ),
            "source_review_decision": _safe_pc_route_debug_dict(
                summary_fragment.get("source_review_decision")
            ),
            "field_owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("field_owner_handoff")
                or summary_fragment.get("owner_handoff")
            ),
            "safe_rerun_hints": _safe_route_task_rehearsal_list(
                summary_fragment.get("safe_rerun_hints")
            ),
            "phone_safe_copy": phone_safe_copy,
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status,
                "safe_copy": safe_copy,
                "safe_phone_copy": safe_copy,
            },
            "not_proven": (
                _elevator_field_evidence_trace_material_backfill_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        }
    )
    required_summary_fields = (
        summary["handoff_status"],
        isinstance(summary["source_review_decision"], dict)
        and bool(summary["source_review_decision"]),
        isinstance(summary["field_owner_handoff"], list)
        and bool(summary["field_owner_handoff"]),
        isinstance(summary["safe_rerun_hints"], list)
        and bool(summary["safe_rerun_hints"]),
        isinstance(summary["phone_safe_copy"], list)
        and bool(summary["phone_safe_copy"]),
        isinstance(summary["missing_required_materials"], list),
        isinstance(summary["rejected_materials"], list),
        isinstance(summary["next_required_evidence"], list),
    )
    if (
        source_schema
        != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": "unsupported_schema",
                "handoff_status_detail": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": (
                        "elevator field evidence trace material backfill review "
                        "handoff schema or evidence boundary is unsupported"
                    ),
                },
                "source_review_decision": {},
                "field_owner_handoff": [],
                "safe_rerun_hints": [],
                "phone_safe_copy": [],
                "missing_required_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or summary["overall_status"] != "not_proven":
        summary["handoff_status"] = (
            "blocked_unsupported_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
        )
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": "material backfill review handoff must be software_proof and not_proven",
        }
        summary["source_review_decision"] = {}
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["handoff_status"] = "blocked_missing_evidence_ref"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review handoff "
                "is missing a safe evidence_ref"
            ),
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["handoff_status"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review handoff "
                "evidence_ref values do not match"
            ),
        }
        return summary
    if (
        not summary["same_evidence_ref_required"]
        or summary["same_evidence_ref_status"] not in ("matched", "same_evidence_ref_matched")
    ):
        summary["handoff_status"] = "blocked_evidence_ref_mismatch_not_proven"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": (
                "elevator field evidence trace material backfill review handoff "
                "must require and report the same evidence_ref"
            ),
        }
        return summary
    if not all(required_summary_fields):
        summary["handoff_status"] = "needs_field_owner_material_handoff_not_proven"
        summary["handoff_status_detail"] = {
            "status": summary["handoff_status"],
            "verdict": "not_proven",
            "reason": "material backfill review handoff is missing owner handoff fields",
        }
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _elevator_field_evidence_trace_material_backfill_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _elevator_field_evidence_trace_material_backfill_review_handoff_has_unsafe_fields(
            robot_summary
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or any(
            _route_task_field_run_readiness_copy_is_unsafe(str(item))
            or _route_task_field_retest_execution_pack_has_success_wording(str(item))
            for item in phone_safe_copy
        )
    ):
        blocked_copy = (
            "Elevator field evidence trace material backfill review handoff was "
            "blocked because summary fields could expose raw/control data or imply "
            "success; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": (
                    "blocked_unsafe_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
                ),
                "handoff_status_detail": {
                    "status": (
                        "blocked_unsafe_elevator_field_evidence_trace_material_backfill_review_handoff_summary"
                    ),
                    "verdict": "not_proven",
                    "reason": "unsafe copy, success wording, raw fields, or enabled actions",
                },
                "source_review_decision": {},
                "field_owner_handoff": [],
                "safe_rerun_hints": [],
                "phone_safe_copy": [],
                "missing_required_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary
