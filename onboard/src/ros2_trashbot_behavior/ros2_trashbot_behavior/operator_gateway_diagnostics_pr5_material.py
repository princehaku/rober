"""PR #5 review/material metadata-only diagnostics helpers.

本模块承接 operator_gateway_diagnostics facade 中 PR5 review/material metadata 诊断逻辑。
它只消费已消毒 summary / wrapper，不读取串口、ROS graph、硬件设备或原始材料。
"""

import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_verified_terminal_material import (
    _task_terminal_field_material_intake_copy_is_unsafe,
    _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls,
)


PR5_REVIEW_THREAD_CLOSEOUT_SCHEMA = "trashbot.pr5_review_thread_closeout.v1"
PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_review_thread_closeout_summary.v1"
)
PR5_REVIEW_THREAD_CLOSEOUT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_review_thread_closeout_summary.v1"
)
PR5_REVIEW_THREAD_CLOSEOUT_GATE = "software_proof_docker_pr5_review_thread_closeout_gate"
PR5_VENDOR_SOURCE_REVIEW_PACKET_SCHEMA = "trashbot.pr5_vendor_source_review_packet.v1"
PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_vendor_source_review_packet_summary.v1"
)
PR5_VENDOR_SOURCE_REVIEW_PACKET_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_vendor_source_review_packet_summary.v1"
)
PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE = (
    "software_proof_docker_pr5_vendor_source_review_packet_gate"
)
PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SCHEMA = (
    "trashbot.pr5_vendor_source_review_reply_dispatch.v1"
)
PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1"
)
PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.v1"
)
PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE = (
    "software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate"
)
PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_source_alignment.v1"
)
PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_source_alignment_summary.v1"
)
PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary.v1"
)
PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_source_alignment_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_followup_escalation_status.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_followup_escalation_status_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATES = (
    "pending",
    "overdue",
    "escalated",
    "blocked",
    "ready_for_reviewer_followup_not_proven",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_intake.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_intake_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_DECISIONS = (
    "accepted",
    "missing",
    "rejected",
    "unsafe",
    "blocked",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_review_decision.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_review_decision_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISIONS = (
    "accepted_for_reviewer_closeout_not_proven",
    "needs_more_material_not_proven",
    "rejected_unsafe_material_not_proven",
    "blocked_missing_owner_response_intake_not_proven",
    "blocked_evidence_ref_mismatch_not_proven",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES = (
    "handoff_ready_not_proven",
    "needs_more_material_not_proven",
    "rejected_unsafe_material_not_proven",
    "blocked_missing_review_decision_not_proven",
    "blocked_evidence_ref_mismatch_not_proven",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.v1"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE = (
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate"
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES = (
    "acknowledged_not_proven",
    "needs_more_material_not_proven",
    "blocked_missing_review_handoff_not_proven",
    "rejected_unsafe_ack_not_proven",
)
PR5_REVIEW_THREAD_CLOSEOUT_REQUIRED_NOT_PROVEN = (
    "real_2d_lidar",
    "real_tof",
    "real_procurement_receipt",
    "real_install_wiring_power_calibration",
    "real_hil_entry",
    "route_elevator_field_pass",
    "delivery_success",
    "objective_5_external_proof",
)
PR5_VENDOR_SOURCE_REVIEW_PACKET_REQUIRED_NOT_PROVEN = (
    "real_2d_lidar_vendor_source",
    "real_tof_vendor_source",
    "real_procurement_receipt",
    "real_installation_wiring_power_calibration",
    "real_hil_entry",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
)
PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_REQUIRED_NOT_PROVEN = (
    "real_2d_lidar_source_material",
    "real_tof_source_material",
    "real_procurement_receipt",
    "real_installation_wiring_power_calibration",
    "real_hardware_validation_entry",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
)
PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_REQUIRED_NOT_PROVEN = (
    "pr5_mandatory_sensor_material_followup_escalation_status_only",
    "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
    "hardware_material_pending",
    "real_2d_lidar_sku_source_receipt_procurement_material",
    "real_tof_sku_source_receipt_procurement_material",
    "mounting_installation_material",
    "wiring_power_budget_material",
    "calibration_plan_or_result",
    "hil_entry_material",
    "operator_hil_report",
    "pr5_reviewer_resolution_evidence",
    "real_sensor_installed_on_robot",
    "real_hil_pass",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REQUIRED_NOT_PROVEN = (
    "pr5_mandatory_sensor_material_owner_response_intake_only",
    "source_followup_escalation_status_not_proven",
    "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
    "hardware_material_pending",
    "real_2d_lidar_sku_source_receipt_procurement_material",
    "real_tof_sku_source_receipt_procurement_material",
    "mounting_installation_material",
    "wiring_power_budget_material",
    "calibration_plan_or_result",
    "hil_entry_material",
    "operator_hil_report",
    "pr5_reviewer_resolution_evidence",
    "real_sensor_installed_on_robot",
    "real_hil_pass",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_REQUIRED_NOT_PROVEN = (
    "pr5_mandatory_sensor_material_owner_response_review_decision_only",
    "source_owner_response_intake_not_proven",
    "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
    "hardware_material_pending",
    "real_2d_lidar_sku_source_receipt_procurement_material",
    "real_tof_sku_source_receipt_procurement_material",
    "mounting_installation_material",
    "wiring_power_budget_material",
    "calibration_plan_or_result",
    "hil_entry_material",
    "operator_hil_report",
    "pr5_reviewer_resolution_evidence",
    "real_sensor_installed_on_robot",
    "real_hil_pass",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)
PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_REQUIRED_NOT_PROVEN = (
    "pr5_mandatory_sensor_material_owner_response_review_handoff_only",
    "source_owner_response_review_decision_not_proven",
    "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
    "hardware_material_pending",
    "real_2d_lidar_sku_source_receipt_procurement_material",
    "real_tof_sku_source_receipt_procurement_material",
    "mounting_installation_material",
    "wiring_power_budget_material",
    "calibration_plan_or_result",
    "hil_entry_material",
    "operator_hil_report",
    "pr5_reviewer_resolution_evidence",
    "real_sensor_installed_on_robot",
    "real_hil_pass",
    "route_elevator_field_pass",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
)








def _dedupe_ordered(values):
    # diagnostics 摘要要保持 Hardware gate 的顺序，同时避免重复 not_proven / missing material 文案刷屏。
    items = []
    for value in values:
        text = _redact_route_task_rehearsal_text(value)
        if text and text not in items:
            items.append(text)
    return items

















def _pr5_review_thread_closeout_not_proven(closeout=None, summary_fragment=None):
    # PR #5 closeout 只表示 review thread 的软件侧消毒摘要，不代表硬件到货、安装、HIL 或送达成功。
    closeout = closeout if isinstance(closeout, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (closeout, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("missing_real_materials"), list):
            source_values.extend(source.get("missing_real_materials"))
        for decision in source.get("thread_decisions", []):
            if isinstance(decision, dict) and isinstance(decision.get("missing_real_materials"), list):
                source_values.extend(decision.get("missing_real_materials"))
    for item in list(source_values) + list(PR5_REVIEW_THREAD_CLOSEOUT_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pr5_vendor_source_review_packet_not_proven(packet=None, summary_fragment=None):
    # vendor/source packet 只复核资料边界，不能被解释为 2D LiDAR/ToF 已采购、安装或实机验证。
    packet = packet if isinstance(packet, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for source in (packet, summary_fragment):
        if isinstance(source.get("not_proven"), list):
            source_values.extend(source.get("not_proven"))
        if isinstance(source.get("missing_materials"), list):
            source_values.extend(source.get("missing_materials"))
        if isinstance(source.get("missing_real_materials"), list):
            source_values.extend(source.get("missing_real_materials"))
    for item in list(source_values) + list(PR5_VENDOR_SOURCE_REVIEW_PACKET_REQUIRED_NOT_PROVEN):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pr5_mandatory_sensor_source_alignment_not_proven(source=None, summary_fragment=None):
    # PR #5 mandatory sensor source alignment 只暴露消毒后的来源对齐状态，不证明传感器实物或控制链路。
    source = source if isinstance(source, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for item_source in (source, summary_fragment):
        if isinstance(item_source.get("not_proven"), list):
            source_values.extend(item_source.get("not_proven"))
        if isinstance(item_source.get("missing_materials"), list):
            source_values.extend(item_source.get("missing_materials"))
        if isinstance(item_source.get("missing_real_materials"), list):
            source_values.extend(item_source.get("missing_real_materials"))
        if isinstance(item_source.get("next_required_evidence"), list):
            source_values.extend(item_source.get("next_required_evidence"))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
    ) + PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_REQUIRED_NOT_PROVEN
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _pr5_mandatory_sensor_material_followup_escalation_status_not_proven(
    source=None,
    summary_fragment=None,
):
    # follow-up status 只是 owner/reviewer 跟进状态，不能证明 PR 已 resolve、传感器已安装或 HIL 通过。
    source = source if isinstance(source, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for item_source in (source, summary_fragment):
        if isinstance(item_source.get("not_proven"), list):
            source_values.extend(item_source.get("not_proven"))
        for key in (
            "missing_required_material_refs",
            "missing_required_evidence",
            "pending_reasons",
            "overdue_reasons",
            "escalated_reasons",
            "blocked_reasons",
            "next_required_evidence",
        ):
            if isinstance(item_source.get(key), list):
                source_values.extend(item_source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
    ) + PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_REQUIRED_NOT_PROVEN
    for item in list(source_values) + list(required):
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL pass 细节只用于阻断；Robot-safe not_proven 里保留材料名和缺口，不保留敏感实现细节。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _pr5_mandatory_sensor_material_owner_response_intake_not_proven(
    source=None,
    summary_fragment=None,
):
    # owner response intake 只说明材料回复被分流，不能证明传感器实物、HIL 或 PR 已关闭。
    source = source if isinstance(source, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for item_source in (source, summary_fragment):
        if isinstance(item_source.get("not_proven"), list):
            source_values.extend(item_source.get("not_proven"))
        for key in (
            "accepted_material_refs",
            "missing_material_refs",
            "rejected_material_refs",
            "unsafe_material_refs",
            "next_required_evidence",
            "blocked_reasons",
        ):
            if isinstance(item_source.get(key), list):
                source_values.extend(item_source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
    ) + PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REQUIRED_NOT_PROVEN
    for item in list(source_values) + list(required):
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum 等只用于阻断，Robot-safe not_proven 只留下可读材料缺口。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _pr5_mandatory_sensor_material_owner_response_review_decision_not_proven(
    source=None,
    summary_fragment=None,
):
    # review decision 只是复核 safe intake metadata，不能被解释成 reviewer 已关闭 PR 或硬件材料真实到位。
    source = source if isinstance(source, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for item_source in (source, summary_fragment):
        if isinstance(item_source.get("not_proven"), list):
            source_values.extend(item_source.get("not_proven"))
        for key in (
            "missing_material_summaries",
            "rejected_material_summaries",
            "unsafe_material_summaries",
            "next_required_evidence",
            "decision_reasons",
        ):
            if isinstance(item_source.get(key), list):
                source_values.extend(item_source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
    ) + PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_REQUIRED_NOT_PROVEN
    for item in list(source_values) + list(required):
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL pass 等只用于 fail-closed 判定，不能回流到 Robot 可见摘要。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _pr5_mandatory_sensor_material_owner_response_review_handoff_not_proven(
    source=None,
    summary_fragment=None,
):
    # review handoff 只把复核结果交给只读 surface，不能被解释为 PR 已关闭或硬件材料到位。
    source = source if isinstance(source, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    for item_source in (source, summary_fragment):
        if isinstance(item_source.get("not_proven"), list):
            source_values.extend(item_source.get("not_proven"))
        for key in (
            "handoff_reasons",
            "missing_material_summaries",
            "next_required_evidence",
            "reviewer_next_step",
            "support_next_step",
        ):
            if isinstance(item_source.get(key), list):
                source_values.extend(item_source.get(key))
            elif isinstance(item_source.get(key), str):
                source_values.append(item_source.get(key))
    required = (
        "not_proven",
        "software_proof",
        "hardware_material_pending",
    ) + PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_REQUIRED_NOT_PROVEN
    for item in list(source_values) + list(required):
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL pass 等只用于阻断，handoff 可见摘要只保留材料缺口和下一步。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if text and text not in values:
            values.append(text)
    return values


    return values




def _default_pr5_review_thread_closeout_summary(
    path,
    status="blocked_missing_pr5_review_thread_closeout_summary",
    read_error="",
):
    # 缺少 Hardware 产出的消毒 summary 时必须保守 blocked，Robot diagnostics 不能从原始 review 内容推断可关闭。
    safe_copy = (
        "PR #5 review thread closeout is metadata-only; software_proof, "
        "not_proven, delivery_success=false and primary_actions_enabled=false."
    )
    return {
        "schema": PR5_REVIEW_THREAD_CLOSEOUT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_REVIEW_THREAD_CLOSEOUT_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {
            "schema": "",
            "evidence_boundary": "",
            "metadata_only": True,
        },
        "status": status,
        "overall_status": "not_proven",
        "closeout_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error or "PR #5 review thread closeout summary is not configured",
        },
        "pr": {"number": 5, "title": ""},
        "thread_decisions": [],
        "missing_real_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _pr5_review_thread_closeout_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "review_thread_closeout_only": True,
        "hardware_material_pending": True,
        "real_hardware_observed": False,
        "sensor_procurement_completed": False,
        "sensor_installed_on_robot": False,
        "sensor_wiring_verified": False,
        "sensor_power_budget_verified": False,
        "sensor_calibrated_on_robot": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "dropoff_completion": False,
        "cancel_completion": False,
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
    }


def _default_pr5_vendor_source_review_packet_summary(
    path,
    status="blocked_missing_pr5_vendor_source_review_packet_summary",
    read_error="",
):
    # 缺少 Hardware 产出的消毒 summary 时 fail closed；Robot 侧不能读取 raw artifact body 补字段。
    safe_copy = (
        "PR #5 vendor/source review packet is metadata-only; software_proof, "
        "not_proven, delivery_success=false and primary_actions_enabled=false."
    )
    return {
        "schema": PR5_VENDOR_SOURCE_REVIEW_PACKET_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "thread_id": "",
        "source": "software_proof",
        "proof_boundary": PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE,
        "vendor_source_boundary": "",
        "status": status,
        "overall_status": "not_proven",
        "missing_materials": [],
        "next_required_evidence": [],
        "safe_copy": safe_copy,
        "not_proven": _pr5_vendor_source_review_packet_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "hardware_read": False,
        "serial_uart_opened": False,
        "ros_graph_accessed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
    }


def _default_pr5_vendor_source_review_reply_dispatch_summary(
    path,
    status="blocked_missing_pr5_vendor_source_review_reply_dispatch_summary",
    read_error="",
):
    # 缺少 Hardware 消毒后的 reply-dispatch summary 时必须阻断，避免 Robot 读取 raw review body。
    safe_copy = (
        "PR #5 vendor/source review reply dispatch is metadata-only; "
        "software_proof, not_proven, hardware_material_pending, delivery_success=false, "
        "primary_actions_enabled=false and safe_to_control=false."
    )
    return {
        "schema": PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "thread_id": "",
        "source": "software_proof",
        "proof_boundary": PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE,
        "status": status,
        "overall_status": "not_proven",
        "reply_dispatch_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error
            or "PR #5 vendor/source review reply dispatch summary is not configured",
        },
        "missing_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "not_proven": _pr5_vendor_source_review_packet_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "hardware_read": False,
        "serial_uart_opened": False,
        "ros_graph_accessed": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "remote_ack_allowed": False,
        "cursor_updates_allowed": False,
        "persistence_updates_allowed": False,
        "terminal_ack_allowed": False,
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
    }


def _default_pr5_mandatory_sensor_source_alignment_summary(
    path,
    status="blocked_missing_pr5_mandatory_sensor_source_alignment_summary",
    read_error="",
):
    # Robot alias 缺少 Hardware sanitized summary 时只能给 blocked 占位，不能读取 raw source material 补全。
    safe_copy = (
        "PR #5 mandatory sensor source alignment is metadata-only; software_proof, "
        "hardware_material_pending, not_proven, delivery_success=false, "
        "primary_actions_enabled=false and safe_to_control=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "thread_id": "",
        "source": "software_proof",
        "source_boundary": "",
        "status": status,
        "overall_status": "not_proven",
        "alignment_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": read_error
            or "PR #5 mandatory sensor source alignment summary is not configured",
        },
        "missing_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "not_proven": _pr5_mandatory_sensor_source_alignment_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "hardware_read": False,
        "raw_materials_exposed": False,
        "serial_uart_opened": False,
        "ros_graph_accessed": False,
        "safe_to_control": False,
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
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
    }


def _default_pr5_mandatory_sensor_material_followup_escalation_status_summary(
    path,
    status="blocked",
    read_error="",
):
    # 缺 summary 时仍返回完整 false 栅栏，避免 diagnostics UI 把“无材料”误读成可控或已 resolve。
    reason = read_error or (
        "PR #5 mandatory sensor material follow-up escalation status summary is not configured"
    )
    safe_copy = (
        "PR #5 mandatory sensor material follow-up escalation status is "
        "metadata-only; source=software_proof; hardware_material_pending; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "proof_boundary": PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "capability": "pr5_mandatory_sensor_material_followup_escalation_status",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": "software_proof",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "evidence_ref": "",
        "followup_status": status,
        "status": status,
        "overall_status": "not_proven",
        "source_alignment_status": "blocked_missing_pr5_mandatory_sensor_source_alignment",
        "followup_status_summary": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "pending_reasons": [],
        "overdue_reasons": [],
        "escalated_reasons": [],
        "blocked_reasons": [reason],
        "missing_required_material_refs": [],
        "owner_next_step": "",
        "reviewer_next_step": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": (
            _pr5_mandatory_sensor_material_followup_escalation_status_not_proven()
        ),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "safe_to_control": False,
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
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "sensor_installed": False,
        "pr_resolved": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }


def _default_pr5_mandatory_sensor_material_owner_response_intake_summary(
    path,
    decision="blocked",
    read_error="",
):
    # 缺省态固定为 fail-closed；Robot diagnostics 不能把缺 owner 材料回复解释成控制就绪。
    reason = read_error or (
        "PR #5 mandatory sensor material owner response intake summary is not configured"
    )
    safe_copy = (
        "PR #5 mandatory sensor material owner response intake is metadata-only; "
        "source=software_proof; hardware_material_pending; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_GATE,
        "proof_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_GATE,
        "capability": "pr5_mandatory_sensor_material_owner_response_intake",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": "software_proof",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "evidence_ref": "",
        "decision": decision,
        "status": decision,
        "overall_status": "not_proven",
        "owner_response_status": {
            "status": decision,
            "decision": decision,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "source_followup_status": "blocked",
        "source_followup_summary": {
            "status": "blocked",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "accepted_material_refs": [],
        "missing_material_refs": [],
        "rejected_material_refs": [],
        "unsafe_material_refs": [],
        "next_required_evidence": [],
        "owner_next_step": "",
        "reviewer_next_step": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": (
            _pr5_mandatory_sensor_material_owner_response_intake_not_proven()
        ),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "safe_to_control": False,
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
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "sensor_installed": False,
        "pr_resolved": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }


def _default_pr5_mandatory_sensor_material_owner_response_review_decision_summary(
    path,
    decision="blocked_missing_owner_response_intake_not_proven",
    read_error="",
):
    # 缺 review-decision summary 时固定输出 blocked，Robot 侧不能读取 raw owner response 或硬件材料正文补齐。
    reason = read_error or (
        "PR #5 mandatory sensor material owner response review decision summary is not configured"
    )
    safe_copy = (
        "PR #5 mandatory sensor material owner response review decision is "
        "metadata-only; source=software_proof; hardware_material_pending; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE,
        "proof_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE,
        "capability": "pr5_mandatory_sensor_material_owner_response_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": "software_proof",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "evidence_ref": "",
        "review_decision": decision,
        "status": decision,
        "overall_status": "not_proven",
        "review_status": {
            "status": decision,
            "decision": decision,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "source_intake_status": "blocked",
        "source_intake_summary": {
            "status": "blocked",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "missing_material_summaries": [],
        "rejected_material_summaries": [],
        "unsafe_material_summaries": [],
        "decision_reasons": [],
        "next_required_evidence": [],
        "reviewer_next_step": "",
        "owner_next_step": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "evidence_boundary_status": "not_proven",
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": (
            _pr5_mandatory_sensor_material_owner_response_review_decision_not_proven()
        ),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "safe_to_control": False,
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
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "sensor_installed": False,
        "pr_resolved": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }


def _default_pr5_mandatory_sensor_material_owner_response_review_handoff_summary(
    path,
    status="blocked_missing_review_decision_not_proven",
    read_error="",
):
    # 缺 handoff summary 时保持 blocked，避免 Robot 侧把上游 review-decision 当成可直接操作的材料闭环。
    reason = read_error or (
        "PR #5 mandatory sensor material owner response review handoff summary is not configured"
    )
    safe_copy = (
        "PR #5 mandatory sensor material owner response review handoff is "
        "metadata-only; source=software_proof; hardware_material_pending; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
        "proof_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
        "capability": "pr5_mandatory_sensor_material_owner_response_review_handoff",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": "software_proof",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "evidence_ref": "",
        "handoff_status": status,
        "status": status,
        "overall_status": "not_proven",
        "handoff_summary": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "source_review_decision_status": "blocked",
        "source_review_decision_summary": {
            "status": "blocked",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "handoff_reasons": [],
        "missing_material_summaries": [],
        "next_required_evidence": [],
        "owner_next_step": "",
        "reviewer_next_step": "",
        "support_next_step": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "evidence_boundary_status": "not_proven",
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": (
            _pr5_mandatory_sensor_material_owner_response_review_handoff_not_proven()
        ),
        "metadata_only": True,
        "summary_required": True,
        "hardware_material_pending": True,
        "safe_to_control": False,
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
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "sensor_installed": False,
        "pr_resolved": False,
        "review_thread_updates_allowed": False,
        "source_payload_exposed": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }


def _default_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary(
    path,
    status="blocked_missing_review_handoff_not_proven",
    read_error="",
):
    # reviewer ACK intake 对 Robot 侧只是只读排队状态；默认必须 blocked，不能暗示 PR 已解决。
    reason = read_error or (
        "PR #5 mandatory sensor material owner response reviewer ACK intake summary is not configured"
    )
    safe_copy = (
        "PR #5 mandatory sensor material owner response reviewer ACK intake is "
        "metadata-only; source=software_proof; hardware_material_pending; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    return {
        "schema": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake",
        "source_schema": "",
        "source_evidence_boundary": "",
        "evidence_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        "proof_boundary": PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        "source": "software_proof",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "ack_intake_status": status,
        "reviewer_ack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": reason,
        },
        "overall_status": "not_proven",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "hardware_material_pending": True,
        "next_required_evidence": [],
        "false_states": {
            "hardware_material_pending": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "review_thread_updates_allowed": False,
            "robot_command_side_effects_allowed": False,
            "source_payload_exposed": False,
        },
        "not_proven": [
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_only",
            "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
            "hardware_material_pending",
            "real_sensor_installed_on_robot",
            "real_hil_pass",
            "route_elevator_field_pass",
            "delivery_success",
            "primary_actions_enabled",
            "safe_to_control",
        ],
        "metadata_only": True,
        "summary_required": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "review_thread_updates_allowed": False,
        "source_payload_exposed": False,
        "robot_command_side_effects_allowed": False,
        "command_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "sensor_installed": False,
        "pr_resolved": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }








def _pr5_review_thread_closeout_source_contract(value):
    # Robot 只接受 Hardware gate 或其 summary wrapper；summary 必须回指同一 PR #5 closeout boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or PR5_REVIEW_THREAD_CLOSEOUT_SCHEMA)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _pr5_vendor_source_review_packet_source_contract(value):
    # Robot 只消费 Hardware 已消毒 packet summary；wrapper 必须回指 PR #5 vendor/source gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema == PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or PR5_VENDOR_SOURCE_REVIEW_PACKET_SCHEMA)
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_vendor_source_review_reply_dispatch_source_contract(value):
    # reply-dispatch 只能来自 Hardware worker 的 sanitized summary，wrapper 也必须回指同一 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema == PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_mandatory_sensor_source_alignment_source_contract(value):
    # mandatory sensor alignment 只接受 Hardware gate 的 summary wrapper，不能从 raw source artifact 旁路读取。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema == PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_mandatory_sensor_material_followup_escalation_status_source_contract(value):
    # PR #5 follow-up status 只能接 Hardware 产出的消毒 summary；artifact wrapper 不能绕过字段白名单。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema == PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_mandatory_sensor_material_owner_response_intake_source_contract(value):
    # Robot 只接受 owner-response intake 的 sanitized summary；raw owner response body 必须停在 PC gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_mandatory_sensor_material_owner_response_review_decision_source_contract(value):
    # review-decision 只能来自 PC gate 的 safe summary；Robot 不信任 raw PR 回复或真实硬件材料 payload。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_mandatory_sensor_material_owner_response_review_handoff_source_contract(value):
    # review-handoff 只能来自 Hardware worker 的 safe summary；Robot 不读取 raw artifact 或远端评审更新结果。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or value.get("proof_boundary") or "")
    if source_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(
            value.get("source_evidence_boundary")
            or value.get("proof_boundary")
            or source_boundary
        )
    return source_schema, source_boundary


def _pr5_review_thread_closeout_copy_is_unsafe(value):
    # 允许安全边界里的 false/not_proven 文案；其余 success/control/HIL/field-pass 语义一律降级。
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "delivery_success=false",
        "primary_actions_enabled=false",
        "not_proven",
        "not proven",
        "metadata-only",
        "software_proof",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "success" in guarded
        or "passed" in guarded
        or "field pass" in guarded
        or "hil pass" in guarded
        or "control enabled" in guarded
        or "start delivery" in guarded
        or "confirm dropoff" in guarded
        or "cancel delivery" in guarded
        or "/cmd_vel" in guarded
        or "ack posted" in guarded
        or "cursor advanced" in guarded
        or any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    )


def _pr5_review_thread_closeout_has_unsafe_fields(value, key_path=""):
    # PR review 原文、控制入口、凭证、本机路径和 raw artifact 都不能泄进 Robot diagnostics。
    unsafe_key_fragments = (
        "raw",
        "body",
        "comment",
        "credential",
        "token",
        "secret",
        "ack",
        "cursor",
        "cmd_vel",
        "command",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text == "not_proven":
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if _pr5_review_thread_closeout_has_unsafe_fields(item, current_path):
                return True
    if isinstance(value, list):
        return any(_pr5_review_thread_closeout_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        return _pr5_review_thread_closeout_copy_is_unsafe(value)
    return False


def summarize_pr5_review_thread_closeout(source):
    """构建 PR #5 review thread closeout 的 metadata-only Robot diagnostics 摘要。"""
    # 这里故意要求 Hardware gate 的 sanitized summary；缺 summary 不能退回读取 raw review thread。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_review_thread_closeout_summary(
        source_path,
        read_error="PR #5 review thread closeout summary is not configured",
    )
    if isinstance(source, dict):
        closeout = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "PR #5 review thread closeout summary artifact missing"
            summary["closeout_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                closeout = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading PR #5 review thread closeout summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["closeout_status"]["reason"] = safe_error
            return summary

    if not isinstance(closeout, dict):
        summary["closeout_status"]["reason"] = "PR #5 review thread closeout JSON must be an object"
        return summary

    raw_schema = str(closeout.get("schema") or "")
    summary_fragment = {}
    source_schema, source_boundary = _pr5_review_thread_closeout_source_contract(closeout)
    if raw_schema == PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = closeout
    else:
        for candidate in (
            closeout.get("pr5_review_thread_closeout_summary"),
            closeout.get("robot_diagnostics_pr5_review_thread_closeout_summary"),
            closeout.get("diagnostics_summary"),
            closeout.get("robot_diagnostics_summary"),
            closeout.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = _pr5_review_thread_closeout_source_contract(
            summary_fragment
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        PR5_REVIEW_THREAD_CLOSEOUT_SCHEMA,
        PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA,
    }
    source_schema_version = (
        closeout.get("schema_version")
        if closeout.get("schema") != PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA
        else closeout.get("source_schema_version") or closeout.get("schema_version")
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or closeout.get("safe_copy")
        or closeout.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status_source = (
        summary_fragment.get("closeout_status")
        if isinstance(summary_fragment.get("closeout_status"), dict)
        else closeout.get("closeout_status")
        if isinstance(closeout.get("closeout_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or closeout.get("status")
        or closeout.get("overall_status")
        or "not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or closeout.get("safe_evidence_ref")
        or closeout.get("evidence_ref", "")
    )
    thread_decision_source = (
        summary_fragment.get("thread_decisions")
        if isinstance(summary_fragment.get("thread_decisions"), list)
        else closeout.get("thread_decisions")
        if isinstance(closeout.get("thread_decisions"), list)
        else []
    )
    thread_decisions = [
        _safe_pc_route_debug_dict(decision)
        for decision in thread_decision_source[:8]
        if isinstance(decision, dict)
    ]
    missing_real_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_real_materials")
        if isinstance(summary_fragment.get("missing_real_materials"), list)
        else closeout.get("missing_real_materials")
    )
    if not missing_real_materials:
        for decision in thread_decisions:
            if isinstance(decision, dict) and isinstance(decision.get("missing_real_materials"), list):
                missing_real_materials.extend(decision.get("missing_real_materials"))
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else closeout.get("robot_diagnostics_summary")
        if isinstance(closeout.get("robot_diagnostics_summary"), dict)
        else {}
    )
    safe_robot_summary = {
        "safe_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_copy") or safe_copy
        ),
        "safe_phone_copy": _redact_route_task_rehearsal_text(
            robot_summary.get("safe_phone_copy") or safe_copy
        ),
    }
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": source_schema_version,
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "closeout_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or closeout.get("reason")
                    or "PR #5 review thread closeout is software_proof only"
                ),
            },
            "pr": _safe_pc_route_debug_dict(summary_fragment.get("pr") or closeout.get("pr")),
            "thread_decisions": thread_decisions,
            "missing_real_materials": _dedupe_ordered(missing_real_materials),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else closeout.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
                if isinstance(summary_fragment.get("owner_handoff"), list)
                else closeout.get("owner_handoff")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_evidence_ref": safe_evidence_ref,
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _pr5_review_thread_closeout_not_proven(closeout, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "summary_required": True,
            "review_thread_closeout_only": True,
            "hardware_material_pending": True,
            "real_hardware_observed": False,
            "sensor_procurement_completed": False,
            "sensor_installed_on_robot": False,
            "sensor_wiring_verified": False,
            "sensor_power_budget_verified": False,
            "sensor_calibrated_on_robot": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "dropoff_completion": False,
            "cancel_completion": False,
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
        }
    )
    if source_schema not in accepted_schemas or source_boundary != PR5_REVIEW_THREAD_CLOSEOUT_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "closeout_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 review thread closeout schema or evidence boundary is unsupported",
                },
                "thread_decisions": [],
                "safe_evidence_ref": "",
            }
        )
        return summary
    if not isinstance(summary_fragment, dict) or not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_pr5_review_thread_closeout_summary",
                "closeout_status": {
                    "status": "blocked_missing_pr5_review_thread_closeout_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 review thread closeout is missing sanitized summary",
                },
                "thread_decisions": [],
                "safe_evidence_ref": "",
            }
        )
        return summary
    if (
        closeout.get("delivery_success") is not False
        or closeout.get("primary_actions_enabled") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _pr5_review_thread_closeout_has_unsafe_fields(closeout)
        or _pr5_review_thread_closeout_has_unsafe_fields(summary_fragment)
        or _pr5_review_thread_closeout_copy_is_unsafe(safe_copy)
        or not safe_evidence_ref
        or safe_evidence_ref.startswith("local_path_redacted:")
    ):
        blocked_copy = (
            "PR #5 review thread closeout was blocked because the summary could expose "
            "raw review/control data or imply success; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_pr5_review_thread_closeout_summary",
                "closeout_status": {
                    "status": "blocked_unsafe_pr5_review_thread_closeout_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 review thread closeout contains unsafe copy, weak evidence_ref, success wording, or enabled actions",
                },
                "thread_decisions": [],
                "safe_evidence_ref": "",
                "safe_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
        return summary
    return summary


def summarize_pr5_vendor_source_review_packet(source):
    """构建 PR #5 vendor/source review packet 的 metadata-only Robot diagnostics 摘要。"""
    # 这里只允许读取 Hardware 的 summary wrapper；即使 artifact 存在，也不能展开 raw body 或硬件材料正文。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_vendor_source_review_packet_summary(
        source_path,
        read_error="PR #5 vendor/source review packet summary is not configured",
    )
    if isinstance(source, dict):
        packet = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "PR #5 vendor/source review packet summary artifact missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                packet = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary["read_error"] = _redact_route_task_rehearsal_text(
                f"failed reading PR #5 vendor/source review packet summary: {exc}"
            )
            return summary

    if not isinstance(packet, dict):
        summary["read_error"] = "PR #5 vendor/source review packet JSON must be an object"
        return summary

    raw_schema = str(packet.get("schema") or "")
    summary_fragment = {}
    source_schema, source_boundary = _pr5_vendor_source_review_packet_source_contract(packet)
    if raw_schema == PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = packet
    else:
        for candidate in (
            packet.get("pr5_vendor_source_review_packet_summary"),
            packet.get("robot_diagnostics_pr5_vendor_source_review_packet_summary"),
            packet.get("diagnostics_summary"),
            packet.get("robot_diagnostics_summary"),
            packet.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = _pr5_vendor_source_review_packet_source_contract(
            summary_fragment
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        PR5_VENDOR_SOURCE_REVIEW_PACKET_SCHEMA,
        PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA,
    }
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or packet.get("safe_copy")
        or packet.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    proof_boundary = _redact_route_task_rehearsal_text(
        summary_fragment.get("proof_boundary")
        or summary_fragment.get("evidence_boundary")
        or packet.get("proof_boundary")
        or packet.get("evidence_boundary")
        or source_boundary
    )
    vendor_source_boundary = _redact_route_task_rehearsal_text(
        summary_fragment.get("vendor_source_boundary")
        or packet.get("vendor_source_boundary")
        or "docs/vendor/VENDOR_INDEX.md source boundary; 2D LiDAR / ToF materials pending"
    )
    missing_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_materials")
        if isinstance(summary_fragment.get("missing_materials"), list)
        else packet.get("missing_materials")
        if isinstance(packet.get("missing_materials"), list)
        else packet.get("missing_real_materials")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                packet.get("source_schema_version")
                if raw_schema == PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA
                else packet.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("thread_id")
                or packet.get("thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or packet.get("source") or "software_proof"
            ),
            "proof_boundary": proof_boundary,
            "vendor_source_boundary": vendor_source_boundary,
            "status": _redact_route_task_rehearsal_text(
                summary_fragment.get("status")
                or summary_fragment.get("overall_status")
                or packet.get("status")
                or packet.get("overall_status")
                or "not_proven"
            ),
            "overall_status": "not_proven",
            "missing_materials": _dedupe_ordered(missing_materials),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else packet.get("next_required_evidence")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "not_proven": _pr5_vendor_source_review_packet_not_proven(
                packet,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "summary_required": True,
            "hardware_read": False,
            "serial_uart_opened": False,
            "ros_graph_accessed": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "collect_triggered": False,
            "dropoff_triggered": False,
            "cancel_triggered": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "command_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
        }
    )
    if source_schema not in accepted_schemas or source_boundary != PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
            }
        )
        return summary
    if not isinstance(summary_fragment, dict) or not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_pr5_vendor_source_review_packet_summary",
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
            }
        )
        return summary
    if (
        summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or packet.get("delivery_success") is not False
        or packet.get("primary_actions_enabled") is not False
        or _pr5_review_thread_closeout_has_unsafe_fields(packet)
        or _pr5_review_thread_closeout_has_unsafe_fields(summary_fragment)
        or _pr5_review_thread_closeout_copy_is_unsafe(safe_copy)
        or proof_boundary != PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE
    ):
        blocked_copy = (
            "PR #5 vendor/source review packet was blocked because the summary could "
            "expose raw artifact/control data or imply success; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_pr5_vendor_source_review_packet_summary",
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "safe_copy": blocked_copy,
            }
        )
        return summary
    return summary


def _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields(value, key_path=""):
    # reply-dispatch 只允许消毒元数据；raw body、令牌、串口/ROS/ACK/cursor/控制字段一律 fail closed。
    unsafe_key_fragments = (
        "raw",
        "body",
        "comment",
        "credential",
        "token",
        "secret",
        "authorization",
        "serial",
        "uart",
        "baud",
        "ros",
        "topic",
        "cmd_vel",
        "control",
        "ack",
        "cursor",
        "command",
        "success",
        "hil",
        "field_pass",
        "field-pass",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "command_allowed",
        "nav2_triggered",
        "hil_pass",
        "field_pass",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text == "not_proven":
                continue
            if key_text in unsafe_true_keys:
                if item is not False:
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(
            _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields(item, key_path)
            for item in value
        )
    if isinstance(value, str):
        return _pr5_review_thread_closeout_copy_is_unsafe(value)
    return False


def summarize_pr5_vendor_source_review_reply_dispatch(source):
    """构建 PR #5 vendor/source review reply-dispatch 的 metadata-only Robot 摘要。"""
    # Robot 只消费 Hardware sanitized summary；raw reply body、credential、ACK/cursor 不能进入 diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_vendor_source_review_reply_dispatch_summary(
        source_path,
        read_error="PR #5 vendor/source review reply dispatch summary is not configured",
    )
    if isinstance(source, dict):
        dispatch = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "PR #5 vendor/source review reply dispatch summary artifact missing"
            summary["reply_dispatch_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                dispatch = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading PR #5 vendor/source review reply dispatch summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reply_dispatch_status"]["reason"] = safe_error
            return summary

    if not isinstance(dispatch, dict):
        summary["read_error"] = "PR #5 vendor/source review reply dispatch JSON must be an object"
        summary["reply_dispatch_status"]["reason"] = summary["read_error"]
        return summary

    raw_schema = str(dispatch.get("schema") or "")
    summary_fragment = {}
    source_schema, source_boundary = _pr5_vendor_source_review_reply_dispatch_source_contract(
        dispatch
    )
    if raw_schema == PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = dispatch
    else:
        for candidate in (
            dispatch.get("pr5_vendor_source_review_reply_dispatch_summary"),
            dispatch.get("robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary"),
            dispatch.get("diagnostics_summary"),
            dispatch.get("robot_diagnostics_summary"),
            dispatch.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_vendor_source_review_reply_dispatch_source_contract(summary_fragment)
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SCHEMA,
        PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA,
    }
    status_source = (
        summary_fragment.get("reply_dispatch_status")
        if isinstance(summary_fragment.get("reply_dispatch_status"), dict)
        else dispatch.get("reply_dispatch_status")
        if isinstance(dispatch.get("reply_dispatch_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or dispatch.get("safe_copy")
        or dispatch.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    proof_boundary = _redact_route_task_rehearsal_text(
        summary_fragment.get("proof_boundary")
        or summary_fragment.get("evidence_boundary")
        or dispatch.get("proof_boundary")
        or dispatch.get("evidence_boundary")
        or source_boundary
    )
    status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or dispatch.get("status")
        or dispatch.get("overall_status")
        or "not_proven"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                dispatch.get("source_schema_version")
                if raw_schema == PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA
                else dispatch.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("thread_id")
                or dispatch.get("thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or dispatch.get("source") or "software_proof"
            ),
            "proof_boundary": proof_boundary,
            "status": status,
            "overall_status": "not_proven",
            "reply_dispatch_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or dispatch.get("reason")
                    or "PR #5 vendor/source review reply dispatch is software_proof only"
                ),
            },
            "missing_materials": _dedupe_ordered(
                _safe_route_task_rehearsal_list(
                    summary_fragment.get("missing_materials")
                    if isinstance(summary_fragment.get("missing_materials"), list)
                    else dispatch.get("missing_materials")
                    if isinstance(dispatch.get("missing_materials"), list)
                    else dispatch.get("missing_real_materials")
                )
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else dispatch.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
                if isinstance(summary_fragment.get("owner_handoff"), list)
                else dispatch.get("owner_handoff")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "not_proven": _pr5_vendor_source_review_packet_not_proven(
                dispatch,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "summary_required": True,
            "hardware_material_pending": True,
            "hardware_read": False,
            "serial_uart_opened": False,
            "ros_graph_accessed": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "collect_triggered": False,
            "dropoff_triggered": False,
            "cancel_triggered": False,
            "ack_post_allowed": False,
            "remote_ack_allowed": False,
            "cursor_updates_allowed": False,
            "persistence_updates_allowed": False,
            "terminal_ack_allowed": False,
            "command_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
            "field_pass": False,
        }
    )
    if source_schema not in accepted_schemas or source_boundary != PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE:
        summary.update(
            {
                "status": "unsupported_schema",
                "reply_dispatch_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 vendor/source review reply dispatch schema or evidence boundary is unsupported",
                },
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if not isinstance(summary_fragment, dict) or not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_pr5_vendor_source_review_reply_dispatch_summary",
                "reply_dispatch_status": {
                    "status": "blocked_missing_pr5_vendor_source_review_reply_dispatch_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 vendor/source review reply dispatch is missing sanitized summary",
                },
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        summary_fragment.get("source") != "software_proof"
        or dispatch.get("source", "software_proof") != "software_proof"
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or dispatch.get("delivery_success") is not False
        or dispatch.get("primary_actions_enabled") is not False
        or dispatch.get("safe_to_control") is not False
        or _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields(dispatch)
        or _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields(summary_fragment)
        or _pr5_review_thread_closeout_copy_is_unsafe(safe_copy)
        or proof_boundary != PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE
    ):
        blocked_copy = (
            "PR #5 vendor/source review reply dispatch was blocked because the summary "
            "could expose raw body/token/serial/UART/ROS/control/ACK/cursor/success/HIL/"
            "field-pass claims; software_proof; not_proven; hardware_material_pending; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_pr5_vendor_source_review_reply_dispatch_summary",
                "reply_dispatch_status": {
                    "status": "blocked_unsafe_pr5_vendor_source_review_reply_dispatch_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 vendor/source review reply dispatch contains unsafe fields, success/control claims, or enabled actions",
                },
                "thread_id": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": blocked_copy,
            }
        )
        return summary
    return summary


def _pr5_mandatory_sensor_source_alignment_copy_is_unsafe(value):
    # 来源对齐 safe copy 只能描述 blocked/not_proven/false-state；HIL、pass、topic 或本地路径词都必须阻断。
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not_proven",
        "not proven",
        "metadata-only",
        "software_proof",
        "hardware_material_pending",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "success" in guarded
        or "passed" in guarded
        or " pass" in guarded
        or "hil" in guarded
        or "delivery success" in guarded
        or "control enabled" in guarded
        or "ros topic" in guarded
        or "/cmd_vel" in guarded
        or "serial" in guarded
        or "uart" in guarded
        or "baud" in guarded
        or any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    )


def _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(value, key_path=""):
    # Robot 只收安全摘要字段；raw material、凭证、路径、串口、ROS 控制面字段出现即 fail closed。
    unsafe_key_fragments = (
        "raw",
        "body",
        "comment",
        "credential",
        "token",
        "secret",
        "authorization",
        "serial",
        "uart",
        "baud",
        "ros",
        "topic",
        "cmd_vel",
        "ack",
        "cursor",
        "command",
        "control_claim",
        "source_material",
        "local_path",
        "path",
        "checksum",
        "hil",
        "pass",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "hardware_read",
        "raw_materials_exposed",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "command_allowed",
        "nav2_triggered",
        "hil_pass",
        "field_pass",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text == "not_proven":
                continue
            if key_text == "false_states":
                if _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(item, current_path):
                    return True
                continue
            if key_text in unsafe_true_keys:
                if item is not False:
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(
            _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(item, key_path)
            for item in value
        )
    if isinstance(value, str):
        return _pr5_mandatory_sensor_source_alignment_copy_is_unsafe(value)
    return False


def _pr5_mandatory_sensor_source_alignment_false_states_ok(source, summary_fragment):
    # Hardware summary 必须显式携带 false states，避免前端把省略值误解成可控或已证明。
    false_states = {}
    for candidate in (
        source.get("false_states") if isinstance(source, dict) else {},
        summary_fragment.get("false_states") if isinstance(summary_fragment, dict) else {},
    ):
        if isinstance(candidate, dict):
            false_states.update(candidate)
    required_false = {
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    for key, expected in required_false.items():
        if false_states.get(key, source.get(key, summary_fragment.get(key))) is not expected:
            return False
    pending = false_states.get(
        "hardware_material_pending",
        source.get("hardware_material_pending", summary_fragment.get("hardware_material_pending")),
    )
    not_proven_state = false_states.get(
        "not_proven",
        source.get("overall_status") == "not_proven"
        or summary_fragment.get("overall_status") == "not_proven",
    )
    return pending is True and not_proven_state is True


def _pr5_mandatory_sensor_material_followup_copy_is_unsafe(value):
    # follow-up 文案允许描述 false-state，但任何成功、安装、HIL、PR resolved 或控制启用暗示都要阻断。
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "source=software_proof",
        "software_proof",
        "hardware_material_pending",
        "not_proven",
        "not proven",
        "not_reviewer_resolution",
        "not resolved",
        "unresolved",
        "metadata-only",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "success" in guarded
        or "passed" in guarded
        or " pass" in guarded
        or "hil" in guarded
        or "installed" in guarded
        or "sensor installed" in guarded
        or "delivery success" in guarded
        or "control enabled" in guarded
        or "primary action" in guarded
        or "external proof" in guarded
        or "public https" in guarded
        or "4g proof" in guarded
        or "reviewer resolved" in guarded
        or "pr resolved" in guarded
        or "thread resolved" in guarded
        or "is_resolved=true" in guarded
        or "ros topic" in guarded
        or "/cmd_vel" in guarded
        or "serial" in guarded
        or "uart" in guarded
        or "wave rover" in guarded
        or "wave_rover" in guarded
        or any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    )


def _pr5_mandatory_sensor_material_followup_has_unsafe_fields(value, key_path=""):
    # 只允许 summary 级材料缺口；raw artifact、路径、checksum、ROS/串口/凭证/控制字段出现即 fail closed。
    unsafe_key_fragments = (
        "raw",
        "body",
        "credential",
        "token",
        "secret",
        "authorization",
        "serial",
        "uart",
        "baud",
        "ros",
        "topic",
        "cmd_vel",
        "ack",
        "cursor",
        "command",
        "control_claim",
        "local_path",
        "path",
        "checksum",
        "traceback",
        "wave_rover",
        "installed_sensor",
        "installed",
        "hil_pass",
        "external_proof",
        "pr_resolution",
        "reviewer_resolution",
        "complete_artifact",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "hardware_read",
        "raw_materials_exposed",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "command_allowed",
        "nav2_triggered",
        "hil_pass",
        "field_pass",
        "sensor_installed",
        "pr_resolved",
        "reviewer_resolved",
    }
    safe_key_fragments = (
        "missing_required_material",
        "pending_reason",
        "overdue_reason",
        "escalated_reason",
        "blocked_reason",
        "not_proven",
        "false_states",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys:
                if item is not False:
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if any(fragment in key_text for fragment in safe_key_fragments):
                continue
            if _pr5_mandatory_sensor_material_followup_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(
            _pr5_mandatory_sensor_material_followup_has_unsafe_fields(item, key_path)
            for item in value
        )
    if isinstance(value, str):
        return _pr5_mandatory_sensor_material_followup_copy_is_unsafe(value)
    return False


def _pr5_mandatory_sensor_material_followup_false_states_ok(source, summary_fragment):
    # Hardware PC summary 必须显式保持三 false 与 hardware_material_pending，省略时保守阻断。
    false_states = {}
    for candidate in (
        source.get("false_states") if isinstance(source, dict) else {},
        summary_fragment.get("false_states") if isinstance(summary_fragment, dict) else {},
    ):
        if isinstance(candidate, dict):
            false_states.update(candidate)
    required_false = {
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    for key, expected in required_false.items():
        if false_states.get(key, source.get(key, summary_fragment.get(key))) is not expected:
            return False
    pending = false_states.get(
        "hardware_material_pending",
        source.get("hardware_material_pending", summary_fragment.get("hardware_material_pending")),
    )
    not_proven_state = false_states.get(
        "not_proven",
        source.get("overall_status") == "not_proven"
        or summary_fragment.get("overall_status") == "not_proven",
    )
    return pending is True and not_proven_state is True


def _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(value):
    # safe_copy 可以描述 false-state；任何成功、安装、HIL 通过、PR resolved 或控制启用暗示都阻断。
    redacted = _redact_route_task_rehearsal_text(value)
    guarded = redacted.lower()
    for phrase in (
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "source=software_proof",
        "software_proof",
        "hardware_material_pending",
        "not_proven",
        "not proven",
        "not_reviewer_resolution",
        "not resolved",
        "unresolved",
        "metadata-only",
        "must not",
        "not real",
        "不证明",
    ):
        guarded = guarded.replace(phrase, "")
    return (
        "success" in guarded
        or "passed" in guarded
        or " pass" in guarded
        or "hil pass" in guarded
        or "installed" in guarded
        or "sensor installed" in guarded
        or "delivery success" in guarded
        or "control enabled" in guarded
        or "primary action" in guarded
        or "external proof" in guarded
        or "public https" in guarded
        or "4g proof" in guarded
        or "reviewer resolved" in guarded
        or "pr resolved" in guarded
        or "thread resolved" in guarded
        or "is_resolved=true" in guarded
        or "ros topic" in guarded
        or "/cmd_vel" in guarded
        or "serial" in guarded
        or "uart" in guarded
        or "wave rover" in guarded
        or "wave_rover" in guarded
        or any(marker in redacted for marker in (
            "[REDACTED_AUTH_HEADER]",
            "Bearer [REDACTED]",
            "[REDACTED_URL]",
            "/dev/[REDACTED_SERIAL]",
            "[REDACTED_BAUD]",
            "[REDACTED_TRACEBACK]",
            "[REDACTED_LOCAL_PATH]",
        ))
    )


def _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(
    value,
    key_path="",
):
    # owner 回复正文可能含 raw body 或现场敏感材料；Robot diagnostics 只允许白名单 summary。
    unsafe_key_fragments = (
        "raw",
        "body",
        "credential",
        "token",
        "secret",
        "authorization",
        "serial",
        "uart",
        "baud",
        "ros",
        "topic",
        "cmd_vel",
        "ack",
        "cursor",
        "command",
        "control_claim",
        "local_path",
        "path",
        "checksum",
        "traceback",
        "wave_rover",
        "installed_sensor",
        "installed",
        "hil_pass",
        "external_proof",
        "pr_resolution",
        "reviewer_resolution",
        "complete_artifact",
        "owner_response_body",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "hardware_read",
        "raw_materials_exposed",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "command_allowed",
        "nav2_triggered",
        "hil_pass",
        "field_pass",
        "sensor_installed",
        "pr_resolved",
        "reviewer_resolved",
    }
    safe_key_fragments = (
        "accepted_material_ref",
        "missing_material_ref",
        "rejected_material_ref",
        "unsafe_material_ref",
        "next_required_evidence",
        "blocked_reason",
        "not_proven",
        "false_states",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys:
                if item is not False:
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if any(fragment in key_text for fragment in safe_key_fragments):
                continue
            if _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(
                item,
                current_path,
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(
                item,
                key_path,
            )
            for item in value
        )
    if isinstance(value, str):
        return _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(value)
    return False


def _pr5_mandatory_sensor_material_owner_response_false_states_ok(
    source,
    summary_fragment,
):
    # PC gate 必须显式保持三 false 与 hardware_material_pending，省略时不能进入 Robot-safe alias。
    false_states = {}
    for candidate in (
        source.get("false_states") if isinstance(source, dict) else {},
        summary_fragment.get("false_states") if isinstance(summary_fragment, dict) else {},
    ):
        if isinstance(candidate, dict):
            false_states.update(candidate)
    required_false = {
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    for key, expected in required_false.items():
        if false_states.get(key, source.get(key, summary_fragment.get(key))) is not expected:
            return False
    pending = false_states.get(
        "hardware_material_pending",
        source.get("hardware_material_pending", summary_fragment.get("hardware_material_pending")),
    )
    not_proven_state = false_states.get(
        "not_proven",
        source.get("overall_status") == "not_proven"
        or summary_fragment.get("overall_status") == "not_proven",
    )
    return pending is True and not_proven_state is True


def _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
    value,
    key_path="",
):
    # 复核摘要会进入 Robot diagnostics，所以这里按字段白名单递归拒绝 raw/hardware/control 线索。
    unsafe_key_fragments = (
        "raw",
        "body",
        "credential",
        "token",
        "secret",
        "authorization",
        "serial",
        "uart",
        "baud",
        "ros",
        "topic",
        "cmd_vel",
        "ack",
        "cursor",
        "command",
        "control_claim",
        "local_path",
        "path",
        "checksum",
        "traceback",
        "wave_rover",
        "installed_sensor",
        "installed",
        "hil_pass",
        "external_proof",
        "pr_resolution",
        "reviewer_resolution",
        "complete_artifact",
        "owner_response_body",
        "material_payload",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "hardware_read",
        "raw_materials_exposed",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "command_allowed",
        "nav2_triggered",
        "hil_pass",
        "field_pass",
        "sensor_installed",
        "pr_resolved",
        "reviewer_resolved",
    }
    safe_key_fragments = (
        "missing_material_summ",
        "rejected_material_summ",
        "unsafe_material_summ",
        "next_required_evidence",
        "decision_reason",
        "not_proven",
        "false_states",
        "review_decision",
        "review_status",
        "source_intake_status",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys:
                if item is not False:
                    return True
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if any(fragment in key_text for fragment in safe_key_fragments):
                continue
            if _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
                item,
                current_path,
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
                item,
                key_path,
            )
            for item in value
        )
    if isinstance(value, str):
        return _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(value)
    return False


def summarize_pr5_mandatory_sensor_source_alignment(source):
    """构建 PR #5 mandatory sensor source alignment 的 metadata-only Robot diagnostics 摘要。"""
    # 这里故意只消费 Hardware gate 的 sanitized summary；raw source material 不进入 Robot diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_mandatory_sensor_source_alignment_summary(
        source_path,
        read_error="PR #5 mandatory sensor source alignment summary is not configured",
    )
    if isinstance(source, dict):
        alignment = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor source alignment summary artifact missing"
            )
            summary["alignment_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                alignment = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading PR #5 mandatory sensor source alignment summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["alignment_status"]["reason"] = safe_error
            return summary

    if not isinstance(alignment, dict):
        summary["read_error"] = "PR #5 mandatory sensor source alignment JSON must be an object"
        summary["alignment_status"]["reason"] = summary["read_error"]
        return summary

    raw_schema = str(alignment.get("schema") or "")
    summary_fragment = {}
    source_schema, source_boundary = _pr5_mandatory_sensor_source_alignment_source_contract(
        alignment
    )
    if raw_schema == PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = alignment
    else:
        for candidate in (
            alignment.get("pr5_mandatory_sensor_source_alignment_summary"),
            alignment.get("robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary"),
            alignment.get("diagnostics_summary"),
            alignment.get("robot_diagnostics_summary"),
            alignment.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_mandatory_sensor_source_alignment_source_contract(summary_fragment)
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SCHEMA,
        PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA,
    }
    status_source = (
        summary_fragment.get("alignment_status")
        if isinstance(summary_fragment.get("alignment_status"), dict)
        else alignment.get("alignment_status")
        if isinstance(alignment.get("alignment_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or alignment.get("safe_copy")
        or alignment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    source_boundary_text = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_boundary")
        or summary_fragment.get("vendor_source_boundary")
        or alignment.get("source_boundary")
        or alignment.get("vendor_source_boundary")
        or "docs/vendor/VENDOR_INDEX.md sanitized source boundary"
    )
    false_states = {
        "hardware_material_pending": True,
        "not_proven": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                alignment.get("source_schema_version")
                if raw_schema == PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA
                else alignment.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("thread_id")
                or alignment.get("thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or alignment.get("source") or "software_proof"
            ),
            "source_boundary": source_boundary_text,
            "status": _redact_route_task_rehearsal_text(
                status_source.get("status")
                or summary_fragment.get("status")
                or summary_fragment.get("overall_status")
                or alignment.get("status")
                or alignment.get("overall_status")
                or "not_proven"
            ),
            "overall_status": "not_proven",
            "alignment_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or alignment.get("status")
                    or "not_proven"
                ),
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or alignment.get("reason")
                    or "PR #5 mandatory sensor source alignment is software_proof only"
                ),
            },
            "missing_materials": _dedupe_ordered(
                _safe_route_task_rehearsal_list(
                    summary_fragment.get("missing_materials")
                    if isinstance(summary_fragment.get("missing_materials"), list)
                    else alignment.get("missing_materials")
                )
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
                if isinstance(summary_fragment.get("next_required_evidence"), list)
                else alignment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
                if isinstance(summary_fragment.get("owner_handoff"), list)
                else alignment.get("owner_handoff")
            ),
            "evidence_boundary": PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_GATE,
            "false_states": false_states,
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_phone_copy": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_phone_copy")
                or alignment.get("safe_phone_copy")
                or safe_copy
            ),
            "not_proven": _pr5_mandatory_sensor_source_alignment_not_proven(
                alignment,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "summary_required": True,
            "hardware_material_pending": True,
            "hardware_read": False,
            "raw_materials_exposed": False,
            "serial_uart_opened": False,
            "ros_graph_accessed": False,
            "safe_to_control": False,
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
            "command_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
            "field_pass": False,
        }
    )
    if (
        source_schema not in accepted_schemas
        or source_boundary != PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "alignment_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 mandatory sensor source alignment schema or evidence boundary is unsupported",
                },
                "thread_id": "",
                "source_boundary": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if not isinstance(summary_fragment, dict) or not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_pr5_mandatory_sensor_source_alignment_summary",
                "alignment_status": {
                    "status": "blocked_missing_pr5_mandatory_sensor_source_alignment_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 mandatory sensor source alignment is missing sanitized summary",
                },
                "thread_id": "",
                "source_boundary": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        summary_fragment.get("source") != "software_proof"
        or alignment.get("source", "software_proof") != "software_proof"
        or not _pr5_mandatory_sensor_source_alignment_false_states_ok(
            alignment,
            summary_fragment,
        )
        or _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(alignment)
        or _pr5_mandatory_sensor_source_alignment_has_unsafe_fields(summary_fragment)
        or _pr5_mandatory_sensor_source_alignment_copy_is_unsafe(safe_copy)
    ):
        blocked_copy = (
            "PR #5 mandatory sensor source alignment was blocked because the summary "
            "could expose raw source material, paths, credentials, serial/UART/ROS/control "
            "details, HIL/pass wording, or success claims; software_proof; "
            "hardware_material_pending; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_pr5_mandatory_sensor_source_alignment_summary",
                "alignment_status": {
                    "status": "blocked_unsafe_pr5_mandatory_sensor_source_alignment_summary",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "PR #5 mandatory sensor source alignment contains unsafe fields, missing false states, or enabled action claims",
                },
                "thread_id": "",
                "source_boundary": "",
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
        return summary
    return summary


def summarize_pr5_mandatory_sensor_material_followup_escalation_status(source):
    """构建 PR #5 mandatory sensor material follow-up escalation 的 Robot-safe 摘要。"""
    # Robot 只消费 Hardware worker 的 PC safe summary；raw manifest 或完整 artifact 一律不进入 diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_mandatory_sensor_material_followup_escalation_status_summary(
        source_path,
        read_error=(
            "PR #5 mandatory sensor material follow-up escalation status summary is not configured"
        ),
    )
    if isinstance(source, dict):
        followup = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor material follow-up escalation status summary artifact missing"
            )
            summary["followup_status_summary"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading PR #5 mandatory sensor material follow-up escalation "
                f"status summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status_summary"]["reason"] = safe_error
            return summary

    if not isinstance(followup, dict):
        summary["followup_status_summary"]["reason"] = (
            "PR #5 mandatory sensor material follow-up escalation status JSON must be an object"
        )
        return summary

    diagnostics = followup.get("diagnostics") if isinstance(followup.get("diagnostics"), dict) else {}
    raw_schema = str(followup.get("schema") or "")
    source_schema, source_boundary = (
        _pr5_mandatory_sensor_material_followup_escalation_status_source_contract(
            followup
        )
    )
    if raw_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        summary_fragment = followup
    else:
        summary_fragment = {}
        for candidate in (
            followup.get(
                "pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            followup.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            followup.get("diagnostics_summary"),
            followup.get("robot_diagnostics_summary"),
            followup.get("robot_compatible_summary"),
            followup.get("summary"),
            diagnostics.get(
                "pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_mandatory_sensor_material_followup_escalation_status_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("followup_status_summary")
        if isinstance(summary_fragment.get("followup_status_summary"), dict)
        else summary_fragment.get("followup_status_detail")
        if isinstance(summary_fragment.get("followup_status_detail"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or followup.get("safe_copy")
        or followup.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游 UI 会直接展示 safe_copy，强制补齐软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    followup_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), str)
        else status_doc.get("status")
        or summary_fragment.get("status")
        or followup.get("followup_status")
        or followup.get("status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup.get("safe_evidence_ref")
        or followup.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        status_doc.get("reason")
        or summary_fragment.get("reason")
        or followup.get("reason")
        or "PR #5 mandatory sensor material follow-up remains software_proof only"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or followup.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or followup.get("source") or "software_proof"
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "evidence_ref": safe_evidence_ref,
            "followup_status": followup_status,
            "status": followup_status,
            "overall_status": "not_proven",
            "source_alignment_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_alignment_status")
                or followup.get("source_alignment_status")
                or "not_proven"
            ),
            "followup_status_summary": {
                "status": followup_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": reason,
            },
            "pending_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("pending_reasons")
            ),
            "overdue_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("overdue_reasons")
            ),
            "escalated_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("escalated_reasons")
            ),
            "blocked_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_reasons")
            ) or [reason],
            "missing_required_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_material_refs")
                if isinstance(summary_fragment.get("missing_required_material_refs"), list)
                else summary_fragment.get("missing_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or followup.get("owner_next_step")
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or followup.get("reviewer_next_step")
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or followup.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or followup.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or followup.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": (
                _pr5_mandatory_sensor_material_followup_escalation_status_not_proven(
                    followup,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        followup_status in PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATES,
        bool(summary["source_alignment_status"]),
        bool(summary["missing_required_material_refs"]),
        bool(summary["owner_next_step"]),
        bool(summary["reviewer_next_step"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] in {"unresolved", "is_resolved=false"},
        summary["pr5_material_state"] == "hardware_material_pending",
    )
    if not summary_fragment:
        summary["followup_status_summary"]["status"] = (
            "blocked_missing_pr5_mandatory_sensor_material_followup_escalation_status_summary"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if (
        source_schema
        != PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary["followup_status_summary"] = {
            "status": (
                "blocked_unsupported_pr5_mandatory_sensor_material_followup_escalation_status"
            ),
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": (
                "PR #5 mandatory sensor material follow-up escalation status schema "
                "or evidence boundary is unsupported"
            ),
        }
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if summary["source"] != "software_proof":
        summary["followup_status_summary"]["status"] = (
            "blocked_unsupported_pr5_mandatory_sensor_material_followup_escalation_status"
        )
        summary["followup_status_summary"]["reason"] = (
            "PR #5 mandatory sensor material follow-up must remain source=software_proof"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["followup_status_summary"]["status"] = (
            "blocked_missing_pr5_mandatory_sensor_material_followup_escalation_status_materials"
        )
        summary["followup_status_summary"]["reason"] = (
            "PR #5 mandatory sensor material follow-up is missing required safe metadata"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if (
        not _pr5_mandatory_sensor_material_followup_false_states_ok(
            followup,
            summary_fragment,
        )
        or _pr5_mandatory_sensor_material_followup_has_unsafe_fields(followup)
        or _pr5_mandatory_sensor_material_followup_has_unsafe_fields(summary_fragment)
        or _pr5_mandatory_sensor_material_followup_has_unsafe_fields(status_doc)
        or _pr5_mandatory_sensor_material_followup_copy_is_unsafe(safe_copy_text)
    ):
        blocked_copy = (
            "PR #5 mandatory sensor material follow-up escalation status was blocked "
            "because summary fields could expose raw artifacts, local paths, checksums, "
            "tracebacks, robot command topics, transport details, hardware details, "
            "credentials, external-proof, HIL, installed-sensor, PR-resolution, "
            "success, or control wording; source=software_proof; "
            "hardware_material_pending; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "followup_status": "blocked",
                "status": (
                    "blocked_unsafe_pr5_mandatory_sensor_material_followup_escalation_status"
                ),
                "followup_status_summary": {
                    "status": (
                        "blocked_unsafe_pr5_mandatory_sensor_material_followup_escalation_status"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "unsafe artifact, raw field, local path, checksum, traceback, "
                        "robot command topic, transport detail, hardware detail, credential, external-proof, "
                        "HIL, installed-sensor, PR-resolution, success, or control material"
                    ),
                },
                "safe_evidence_ref": "",
                "evidence_ref": "",
                "source_alignment_status": "",
                "pending_reasons": [],
                "overdue_reasons": [],
                "escalated_reasons": [],
                "blocked_reasons": [
                    "unsafe summary fields were redacted and blocked"
                ],
                "missing_required_material_refs": [],
                "owner_next_step": "",
                "reviewer_next_step": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_pr5_mandatory_sensor_material_owner_response_intake(source):
    """构建 PR #5 mandatory sensor material owner-response intake 的 Robot-safe 摘要。"""
    # Robot 只消费 PC gate 的 sanitized summary；owner raw body 可能含凭证、路径或硬件细节，必须留在 PC 侧。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_mandatory_sensor_material_owner_response_intake_summary(
        source_path,
        read_error=(
            "PR #5 mandatory sensor material owner response intake summary is not configured"
        ),
    )
    if isinstance(source, dict):
        response_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor material owner response intake summary artifact missing"
            )
            summary["owner_response_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading PR #5 mandatory sensor material owner response "
                f"intake summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["owner_response_status"]["reason"] = safe_error
            return summary

    if not isinstance(response_doc, dict):
        summary["owner_response_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response intake JSON must be an object"
        )
        return summary

    diagnostics = (
        response_doc.get("diagnostics")
        if isinstance(response_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(response_doc.get("schema") or "")
    source_schema, source_boundary = (
        _pr5_mandatory_sensor_material_owner_response_intake_source_contract(
            response_doc
        )
    )
    if raw_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = response_doc
    else:
        summary_fragment = {}
        for candidate in (
            response_doc.get("pr5_mandatory_sensor_material_owner_response_intake_summary"),
            response_doc.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
            ),
            response_doc.get("diagnostics_summary"),
            response_doc.get("robot_diagnostics_summary"),
            response_doc.get("robot_compatible_summary"),
            response_doc.get("summary"),
            diagnostics.get("pr5_mandatory_sensor_material_owner_response_intake_summary"),
            diagnostics.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_mandatory_sensor_material_owner_response_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("owner_response_status")
        if isinstance(summary_fragment.get("owner_response_status"), dict)
        else summary_fragment.get("decision_summary")
        if isinstance(summary_fragment.get("decision_summary"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    source_followup_doc = (
        summary_fragment.get("source_followup_status")
        if isinstance(summary_fragment.get("source_followup_status"), dict)
        else summary_fragment.get("source_followup_summary")
        if isinstance(summary_fragment.get("source_followup_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or response_doc.get("safe_copy")
        or response_doc.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游直接展示 safe_copy，必须显式保留软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("decision")
        or status_doc.get("decision")
        or status_doc.get("status")
        or summary_fragment.get("status")
        or response_doc.get("decision")
        or response_doc.get("status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or response_doc.get("safe_evidence_ref")
        or response_doc.get("evidence_ref", "")
    )
    source_followup_status = _redact_route_task_rehearsal_text(
        source_followup_doc.get("status")
        or summary_fragment.get("source_followup_status")
        or summary_fragment.get("followup_status")
        or response_doc.get("source_followup_status")
        or "blocked"
    )
    reason = _redact_route_task_rehearsal_text(
        status_doc.get("reason")
        or summary_fragment.get("reason")
        or response_doc.get("reason")
        or "PR #5 mandatory sensor material owner response intake remains software_proof only"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or response_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or response_doc.get("source") or "software_proof"
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "evidence_ref": safe_evidence_ref,
            "decision": decision,
            "status": decision,
            "overall_status": "not_proven",
            "owner_response_status": {
                "status": decision,
                "decision": decision,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": reason,
            },
            "source_followup_status": source_followup_status,
            "source_followup_summary": {
                "status": source_followup_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    source_followup_doc.get("reason")
                    or "source follow-up escalation status remains not_proven"
                ),
            },
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted_refs")
                or summary_fragment.get("accepted")
            ),
            "missing_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_refs")
                or summary_fragment.get("missing_refs")
                or summary_fragment.get("missing")
            ),
            "rejected_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_material_refs")
                or summary_fragment.get("rejected_refs")
                or summary_fragment.get("rejected")
            ),
            "unsafe_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_material_refs")
                or summary_fragment.get("unsafe_refs")
                or summary_fragment.get("unsafe")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or response_doc.get("owner_next_step")
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or response_doc.get("reviewer_next_step")
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or response_doc.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or response_doc.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or response_doc.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": (
                _pr5_mandatory_sensor_material_owner_response_intake_not_proven(
                    response_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
        }
    )
    material_lists_present = any(
        summary[key]
        for key in (
            "accepted_material_refs",
            "missing_material_refs",
            "rejected_material_refs",
            "unsafe_material_refs",
        )
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        decision in PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_DECISIONS,
        bool(source_followup_status),
        material_lists_present,
        bool(summary["next_required_evidence"]),
        bool(summary["owner_next_step"]),
        bool(summary["reviewer_next_step"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] in {"unresolved", "is_resolved=false"},
        summary["pr5_material_state"] == "hardware_material_pending",
    )
    if not summary_fragment:
        summary["owner_response_status"]["status"] = (
            "blocked_missing_pr5_mandatory_sensor_material_owner_response_intake_summary"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if (
        source_schema
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA
        or source_boundary
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_GATE
    ):
        summary["owner_response_status"] = {
            "status": (
                "blocked_unsupported_pr5_mandatory_sensor_material_owner_response_intake"
            ),
            "decision": "blocked",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": (
                "PR #5 mandatory sensor material owner response intake schema "
                "or evidence boundary is unsupported"
            ),
        }
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if summary["source"] != "software_proof":
        summary["owner_response_status"]["status"] = (
            "blocked_unsupported_pr5_mandatory_sensor_material_owner_response_intake"
        )
        summary["owner_response_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response intake must remain source=software_proof"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["owner_response_status"]["status"] = (
            "blocked_missing_pr5_mandatory_sensor_material_owner_response_intake_materials"
        )
        summary["owner_response_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response intake is missing required safe metadata"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if (
        not _pr5_mandatory_sensor_material_owner_response_false_states_ok(
            response_doc,
            summary_fragment,
        )
        or _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(response_doc)
        or _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(
            summary_fragment
        )
        or _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(status_doc)
        or _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields(
            source_followup_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(safe_copy_text)
    ):
        blocked_copy = (
            "PR #5 mandatory sensor material owner response intake was blocked "
            "because summary fields could expose raw owner response bodies, local paths, "
            "checksums, tracebacks, robot command topics, serial/UART details, "
            "WAVE ROVER parameters, credentials, external-proof, HIL pass, "
            "installed-sensor, PR-resolution, success, or control wording; "
            "source=software_proof; hardware_material_pending; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "decision": "blocked",
                "status": (
                    "blocked_unsafe_pr5_mandatory_sensor_material_owner_response_intake"
                ),
                "owner_response_status": {
                    "status": (
                        "blocked_unsafe_pr5_mandatory_sensor_material_owner_response_intake"
                    ),
                    "decision": "blocked",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "unsafe raw owner body, local path, checksum, traceback, robot "
                        "command topic, serial/UART detail, WAVE ROVER detail, credential, "
                        "external-proof, HIL pass, installed-sensor, PR-resolution, success, "
                        "or control material"
                    ),
                },
                "safe_evidence_ref": "",
                "evidence_ref": "",
                "source_followup_status": "blocked",
                "source_followup_summary": {
                    "status": "blocked",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "unsafe owner response intake summary was redacted and blocked",
                },
                "accepted_material_refs": [],
                "missing_material_refs": [],
                "rejected_material_refs": [],
                "unsafe_material_refs": [],
                "next_required_evidence": [],
                "owner_next_step": "",
                "reviewer_next_step": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_pr5_mandatory_sensor_material_owner_response_review_decision(source):
    """构建 PR #5 mandatory sensor material owner-response review-decision 的 Robot-safe 摘要。"""
    # Robot 只消费 PC gate safe summary；raw PR 回复和真实硬件 material payload 可能含凭证、路径或串口细节。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_mandatory_sensor_material_owner_response_review_decision_summary(
        source_path,
        read_error=(
            "PR #5 mandatory sensor material owner response review decision summary is not configured"
        ),
    )
    if isinstance(source, dict):
        decision_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor material owner response review decision summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading PR #5 mandatory sensor material owner response "
                f"review decision summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response review decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    source_schema, source_boundary = (
        _pr5_mandatory_sensor_material_owner_response_review_decision_source_contract(
            decision_doc
        )
    )
    if raw_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            decision_doc.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            decision_doc.get("diagnostics_summary"),
            decision_doc.get("robot_diagnostics_summary"),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            diagnostics.get(
                "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_mandatory_sensor_material_owner_response_review_decision_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("decision_summary")
        if isinstance(summary_fragment.get("decision_summary"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    source_intake_doc = (
        summary_fragment.get("source_intake_status")
        if isinstance(summary_fragment.get("source_intake_status"), dict)
        else summary_fragment.get("source_owner_response_intake_status")
        if isinstance(summary_fragment.get("source_owner_response_intake_status"), dict)
        else summary_fragment.get("source_intake_summary")
        if isinstance(summary_fragment.get("source_intake_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or decision_doc.get("safe_copy")
        or decision_doc.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游直接展示 safe_copy，必须显式保留软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or status_doc.get("decision")
        or status_doc.get("status")
        or summary_fragment.get("status")
        or decision_doc.get("review_decision")
        or decision_doc.get("decision")
        or decision_doc.get("status")
        or "blocked_missing_owner_response_intake_not_proven"
    )
    source_intake_status = _redact_route_task_rehearsal_text(
        source_intake_doc.get("status")
        or summary_fragment.get("source_intake_status")
        or summary_fragment.get("source_owner_response_intake_status")
        or summary_fragment.get("owner_response_intake_status")
        or decision_doc.get("source_intake_status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or decision_doc.get("safe_evidence_ref")
        or decision_doc.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        status_doc.get("reason")
        or summary_fragment.get("reason")
        or decision_doc.get("reason")
        or "PR #5 mandatory sensor material owner response review decision remains software_proof only"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or decision_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or decision_doc.get("source") or "software_proof"
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "evidence_ref": safe_evidence_ref,
            "review_decision": review_decision,
            "status": review_decision,
            "overall_status": "not_proven",
            "review_status": {
                "status": review_decision,
                "decision": review_decision,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": reason,
            },
            "source_intake_status": source_intake_status,
            "source_intake_summary": {
                "status": source_intake_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    source_intake_doc.get("reason")
                    or "source owner-response intake remains not_proven"
                ),
            },
            "missing_material_summaries": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_summaries")
                or summary_fragment.get("missing_material_refs")
                or summary_fragment.get("missing")
            ),
            "rejected_material_summaries": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_material_summaries")
                or summary_fragment.get("rejected_material_refs")
                or summary_fragment.get("rejected")
            ),
            "unsafe_material_summaries": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_material_summaries")
                or summary_fragment.get("unsafe_material_refs")
                or summary_fragment.get("unsafe")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or decision_doc.get("owner_next_step")
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or decision_doc.get("reviewer_next_step")
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or decision_doc.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or decision_doc.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or decision_doc.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": (
                _pr5_mandatory_sensor_material_owner_response_review_decision_not_proven(
                    decision_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
        }
    )
    material_summaries_present = any(
        summary[key]
        for key in (
            "missing_material_summaries",
            "rejected_material_summaries",
            "unsafe_material_summaries",
        )
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        review_decision in PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISIONS,
        bool(source_intake_status),
        material_summaries_present,
        bool(summary["next_required_evidence"]),
        bool(summary["reviewer_next_step"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] in {"unresolved", "is_resolved=false"},
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["evidence_boundary_status"] == "not_proven",
    )
    if not summary_fragment:
        summary["review_status"]["status"] = (
            "blocked_missing_owner_response_intake_not_proven"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        source_schema
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        or source_boundary
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE
    ):
        summary["review_status"] = {
            "status": "blocked_missing_owner_response_intake_not_proven",
            "decision": "blocked_missing_owner_response_intake_not_proven",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": (
                "PR #5 mandatory sensor material owner response review decision "
                "schema or evidence boundary is unsupported"
            ),
        }
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if summary["source"] != "software_proof":
        summary["review_status"]["status"] = (
            "rejected_unsafe_material_not_proven"
        )
        summary["review_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response review decision must remain source=software_proof"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_status"]["status"] = (
            "blocked_missing_owner_response_intake_not_proven"
        )
        summary["review_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response review decision is missing required safe metadata"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        not _pr5_mandatory_sensor_material_owner_response_false_states_ok(
            decision_doc,
            summary_fragment,
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            status_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            source_intake_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(safe_copy_text)
    ):
        blocked_copy = (
            "PR #5 mandatory sensor material owner response review decision was "
            "blocked because summary fields could expose raw owner response bodies, "
            "hardware material payloads, local paths, checksums, tracebacks, robot "
            "command topics, serial/UART details, WAVE ROVER parameters, credentials, "
            "external-proof, HIL pass, installed-sensor, PR-resolution, success, or "
            "control wording; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision": "rejected_unsafe_material_not_proven",
                "status": "rejected_unsafe_material_not_proven",
                "review_status": {
                    "status": "rejected_unsafe_material_not_proven",
                    "decision": "rejected_unsafe_material_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "unsafe raw owner body, hardware material payload, local path, "
                        "checksum, traceback, robot command topic, serial/UART detail, "
                        "WAVE ROVER detail, credential, external-proof, HIL pass, "
                        "installed-sensor, PR-resolution, success, or control material"
                    ),
                },
                "safe_evidence_ref": "",
                "evidence_ref": "",
                "source_intake_status": "blocked",
                "source_intake_summary": {
                    "status": "blocked",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "unsafe owner response review decision summary was redacted and blocked",
                },
                "missing_material_summaries": [],
                "rejected_material_summaries": [],
                "unsafe_material_summaries": ["rejected_unsafe_material_not_proven"],
                "decision_reasons": [],
                "next_required_evidence": [],
                "owner_next_step": "",
                "reviewer_next_step": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_pr5_mandatory_sensor_material_owner_response_review_handoff(source):
    """构建 PR #5 mandatory sensor material owner-response review-handoff 的 Robot-safe 摘要。"""
    # handoff 面向 status/diagnostics/phone；这里只允许 PC gate safe summary 进入 Robot 负载。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_pr5_mandatory_sensor_material_owner_response_review_handoff_summary(
        source_path,
        read_error=(
            "PR #5 mandatory sensor material owner response review handoff summary is not configured"
        ),
    )
    if isinstance(source, dict):
        handoff_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor material owner response review handoff summary artifact missing"
            )
            summary["handoff_summary"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading PR #5 mandatory sensor material owner response "
                f"review handoff summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["handoff_summary"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["handoff_summary"]["reason"] = (
            "PR #5 mandatory sensor material owner response review handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _pr5_mandatory_sensor_material_owner_response_review_handoff_source_contract(
            handoff_doc
        )
    )
    if raw_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get(
                "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            handoff_doc.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            handoff_doc.get("diagnostics_summary"),
            handoff_doc.get("robot_diagnostics_summary"),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            diagnostics.get(
                "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _pr5_mandatory_sensor_material_owner_response_review_handoff_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("handoff_summary")
        if isinstance(summary_fragment.get("handoff_summary"), dict)
        else summary_fragment.get("review_handoff_status")
        if isinstance(summary_fragment.get("review_handoff_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    source_review_doc = (
        summary_fragment.get("source_review_decision_summary")
        if isinstance(summary_fragment.get("source_review_decision_summary"), dict)
        else summary_fragment.get("source_review_decision_status")
        if isinstance(summary_fragment.get("source_review_decision_status"), dict)
        else summary_fragment.get("source_review_summary")
        if isinstance(summary_fragment.get("source_review_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff_doc.get("safe_copy")
        or handoff_doc.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 手机/诊断会直接展示 handoff copy，因此必须把边界词补齐到 copy 内。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    handoff_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or status_doc.get("status")
        or handoff_doc.get("handoff_status")
        or handoff_doc.get("status")
        or "blocked_missing_review_decision_not_proven"
    )
    source_review_decision_status = _redact_route_task_rehearsal_text(
        source_review_doc.get("status")
        or summary_fragment.get("source_review_decision_status")
        or handoff_doc.get("source_review_decision_status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or handoff_doc.get("safe_evidence_ref")
        or handoff_doc.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        status_doc.get("reason")
        or summary_fragment.get("reason")
        or handoff_doc.get("reason")
        or "PR #5 mandatory sensor material owner response review handoff remains software_proof only"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or handoff_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or handoff_doc.get("source") or "software_proof"
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "evidence_ref": safe_evidence_ref,
            "handoff_status": handoff_status,
            "status": handoff_status,
            "overall_status": "not_proven",
            "handoff_summary": {
                "status": handoff_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": reason,
            },
            "source_review_decision_status": source_review_decision_status,
            "source_review_decision_summary": {
                "status": source_review_decision_status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    source_review_doc.get("reason")
                    or "source owner-response review decision remains not_proven"
                ),
            },
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "missing_material_summaries": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_summaries")
                or summary_fragment.get("missing_material_refs")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or handoff_doc.get("owner_next_step")
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or handoff_doc.get("reviewer_next_step")
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or handoff_doc.get("support_next_step")
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or handoff_doc.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or handoff_doc.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or handoff_doc.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "safe_to_control": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            },
            "not_proven": (
                _pr5_mandatory_sensor_material_owner_response_review_handoff_not_proven(
                    handoff_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        handoff_status in PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES,
        bool(source_review_decision_status),
        bool(summary["next_required_evidence"]),
        bool(summary["reviewer_next_step"] or summary["support_next_step"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] in {"unresolved", "is_resolved=false"},
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["evidence_boundary_status"] == "not_proven",
    )
    if not summary_fragment:
        summary["handoff_summary"]["status"] = "blocked_missing_review_decision_not_proven"
        summary["status"] = summary["handoff_summary"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        source_schema
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
    ):
        summary["handoff_summary"] = {
            "status": "blocked_missing_review_decision_not_proven",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
            "reason": (
                "PR #5 mandatory sensor material owner response review handoff "
                "schema or evidence boundary is unsupported"
            ),
        }
        summary["status"] = summary["handoff_summary"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if summary["source"] != "software_proof":
        summary["handoff_summary"]["status"] = "rejected_unsafe_material_not_proven"
        summary["handoff_summary"]["reason"] = (
            "PR #5 mandatory sensor material owner response review handoff must remain source=software_proof"
        )
        summary["status"] = summary["handoff_summary"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if not all(required_safe_metadata):
        summary["handoff_summary"]["status"] = "blocked_missing_review_decision_not_proven"
        summary["handoff_summary"]["reason"] = (
            "PR #5 mandatory sensor material owner response review handoff is missing required safe metadata"
        )
        summary["status"] = summary["handoff_summary"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        not _pr5_mandatory_sensor_material_owner_response_false_states_ok(
            handoff_doc,
            summary_fragment,
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            handoff_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            status_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields(
            source_review_doc
        )
        or _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe(safe_copy_text)
    ):
        blocked_copy = (
            "PR #5 mandatory sensor material owner response review handoff was "
            "blocked because summary fields could expose raw artifacts, local paths, "
            "checksums, tracebacks, robot command topics, ACK/cursor mutation, "
            "serial/UART details, WAVE ROVER parameters, credentials, remote review updates, "
            "external-proof, HIL pass, installed-sensor, PR-resolution, success, or "
            "control wording; source=software_proof; hardware_material_pending; "
            "not_proven; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": "rejected_unsafe_material_not_proven",
                "status": "rejected_unsafe_material_not_proven",
                "handoff_summary": {
                    "status": "rejected_unsafe_material_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": (
                        "unsafe raw artifact, local path, checksum, traceback, robot "
                        "command topic, ACK/cursor mutation, serial/UART detail, WAVE "
                        "ROVER detail, credential, remote review update, external-proof, HIL "
                        "pass, installed-sensor, PR-resolution, success, or control material"
                    ),
                },
                "safe_evidence_ref": "",
                "evidence_ref": "",
                "source_review_decision_status": "blocked",
                "source_review_decision_summary": {
                    "status": "blocked",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "unsafe owner response review handoff summary was redacted and blocked",
                },
                "handoff_reasons": [],
                "missing_material_summaries": [],
                "next_required_evidence": [],
                "owner_next_step": "",
                "reviewer_next_step": "",
                "support_next_step": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary


def summarize_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(source):
    """构建 PR #5 mandatory sensor material reviewer ACK intake 的 Robot-safe 摘要。"""
    # 只消费 Hardware gate 已消毒 summary；ACK/cursor/GitHub 写动作和机器人控制字段一律不透出。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary(
            source_path,
            read_error=(
                "PR #5 mandatory sensor material owner response reviewer ACK intake summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        intake_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "PR #5 mandatory sensor material owner response reviewer ACK intake summary artifact missing"
            )
            summary["reviewer_ack_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading PR #5 mandatory sensor material owner response "
                f"reviewer ACK intake summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reviewer_ack_status"]["reason"] = safe_error
            return summary

    if not isinstance(intake_doc, dict):
        summary["reviewer_ack_status"]["reason"] = (
            "PR #5 mandatory sensor material owner response reviewer ACK intake JSON must be an object"
        )
        return summary

    diagnostics = (
        intake_doc.get("diagnostics")
        if isinstance(intake_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(intake_doc.get("schema") or "")
    if raw_schema in {
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = intake_doc
    else:
        summary_fragment = {}
        for candidate in (
            intake_doc.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            intake_doc.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            intake_doc.get("diagnostics_summary"),
            intake_doc.get("robot_diagnostics_summary"),
            intake_doc.get("robot_compatible_summary"),
            intake_doc.get("summary"),
            diagnostics.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if not summary_fragment:
        summary["status"] = "blocked_missing_review_handoff_not_proven"
        summary["ack_intake_status"] = summary["status"]
        summary["reviewer_ack_status"]["status"] = summary["status"]
        return summary

    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema = str(
        summary_fragment.get("source_schema")
        or (
            PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
            if fragment_schema
            in {
                PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
                PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
            }
            else raw_schema
        )
    )
    source_boundary = str(
        summary_fragment.get("source_evidence_boundary")
        or summary_fragment.get("proof_boundary")
        or summary_fragment.get("evidence_boundary")
        or intake_doc.get("evidence_boundary")
        or ""
    )
    ack_doc = (
        summary_fragment.get("reviewer_ack_status")
        if isinstance(summary_fragment.get("reviewer_ack_status"), dict)
        else summary_fragment.get("ack_intake_status")
        if isinstance(summary_fragment.get("ack_intake_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        ack_doc.get("status")
        or summary_fragment.get("ack_intake_status")
        or summary_fragment.get("status")
        or "blocked_missing_review_handoff_not_proven"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; hardware_material_pending; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe copy 是 operator/relay 可见文案，必须自带 fail-closed 边界，避免 UI 误读。
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"

    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or intake_doc.get("source") or "software_proof"
            ),
            "status": status,
            "ack_intake_status": status,
            "reviewer_ack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": "software_proof",
                "reason": _redact_route_task_rehearsal_text(
                    ack_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "PR #5 reviewer ACK intake remains software_proof metadata only"
                ),
            },
            "overall_status": "not_proven",
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or intake_doc.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or intake_doc.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or intake_doc.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "hardware_material_pending": True,
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "false_states": {
                "hardware_material_pending": True,
                "not_proven": True,
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
                "ack_post_allowed": False,
                "cursor_updates_allowed": False,
                "review_thread_updates_allowed": False,
                "robot_command_side_effects_allowed": False,
                "source_payload_exposed": False,
            },
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_safe_metadata = (
        fragment_schema
        in {
            PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
            PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
        },
        source_schema == PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
        source_boundary == PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        summary["source"] == "software_proof",
        status in PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        bool(summary["next_required_evidence"]),
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
        _pr5_mandatory_sensor_material_owner_response_false_states_ok(
            intake_doc,
            summary_fragment,
        ),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
            intake_doc
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
            summary_fragment
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "PR #5 mandatory sensor material owner response reviewer ACK intake "
            "was blocked because the summary did not remain source=software_proof, "
            "not_proven, hardware_material_pending, safe_to_control=false, "
            "delivery_success=false, primary_actions_enabled=false, and free of "
            "raw artifacts, credentials, serial/UART, ROS control topics, GitHub "
            "write/resolve, ACK/cursor mutation, robot command side effects, "
            "HIL pass, installed-sensor, success, or control claims."
        )
        summary.update(
            {
                "status": "rejected_unsafe_ack_not_proven",
                "ack_intake_status": "rejected_unsafe_ack_not_proven",
                "reviewer_ack_status": {
                    "status": "rejected_unsafe_ack_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                    "reason": "unsafe PR #5 reviewer ACK intake summary was redacted and blocked",
                },
                "next_required_evidence": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
            }
        )
    return summary
