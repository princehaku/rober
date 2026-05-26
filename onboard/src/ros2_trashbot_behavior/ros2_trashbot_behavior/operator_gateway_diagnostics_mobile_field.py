import json
import os

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _route_task_field_run_readiness_copy_is_unsafe,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_task_field_retest import (
    _route_task_field_retest_execution_pack_has_success_wording,
)

MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SCHEMA = (
    "trashbot.mobile_route_elevator_field_device_precheck.v1"
)
MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY_SCHEMA = (
    "trashbot.mobile_route_elevator_field_device_precheck_summary.v1"
)
MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_GATE = (
    "software_proof_docker_mobile_route_elevator_field_device_precheck_gate"
)
MOBILE_FIELD_MATERIAL_INTAKE_SCHEMA = "trashbot.mobile_field_material_intake.v1"
MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA = "trashbot.mobile_field_material_intake_summary.v1"
MOBILE_FIELD_MATERIAL_INTAKE_GATE = "software_proof_docker_mobile_field_material_intake_gate"
MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA = "trashbot.mobile_field_material_review_decision.v1"
MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.mobile_field_material_review_decision_summary.v1"
)
MOBILE_FIELD_MATERIAL_REVIEW_DECISION_GATE = (
    "software_proof_docker_mobile_field_material_review_decision_gate"
)
MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SCHEMA = "trashbot.mobile_field_material_retest_request.v1"
MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY_SCHEMA = (
    "trashbot.mobile_field_material_retest_request_summary.v1"
)
MOBILE_FIELD_MATERIAL_RETEST_REQUEST_GATE = (
    "software_proof_docker_mobile_field_material_retest_request_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_review_handoff.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_review_handoff_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_pack.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_pack_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_pack_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_intake.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_intake_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_decision.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_intake.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_intake_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_decision.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_gate"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary.v1"
)
MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate"
)

def _mobile_route_elevator_field_device_precheck_not_proven(precheck=None, summary_fragment=None):
    # 手机/路线/电梯/现场设备预检只给下一步人工复核用；真实设备、控制面和交付结论必须继续外部证明。
    precheck = precheck if isinstance(precheck, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(precheck.get("not_proven"), list):
        source_values.extend(precheck.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_device_observed",
        "pwa_install_prompt_observed",
        "route_elevator_field_pass",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "real_route_execution",
        "real_elevator_operation",
        "real_nav2_fixed_route_run",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _mobile_field_material_intake_not_proven(intake=None, summary_fragment=None):
    # 手机现场材料 intake 只汇总人工回填材料；真实控制、ACK、Nav2、HIL 和交付结论必须继续外部证明。
    intake = intake if isinstance(intake, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(intake.get("not_proven"), list):
        source_values.extend(intake.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_phone_device_proof",
        "real_route_elevator_field_pass",
        "real_nav2_fixed_route_run",
        "task_record_real_world_completion",
        "completion_signal_real_world",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _mobile_field_material_review_decision_not_proven(review=None, summary_fragment=None):
    # review decision 只是把 intake 材料转成 owner handoff；真实手机、路线、电梯、Nav2 和终端完成仍必须另证。
    review = review if isinstance(review, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(review.get("not_proven"), list):
        source_values.extend(review.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_phone_device_proof",
        "real_route_elevator_field_pass",
        "real_nav2_fixed_route_run",
        "task_record_real_world_completion",
        "completion_signal_real_world",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _mobile_field_material_retest_request_not_proven(request=None, summary_fragment=None):
    # retest request 只把 review decision 转成下一轮补料请求；不能把补测请求升级成控制、ACK 或交付证据。
    request = request if isinstance(request, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    values = []
    source_values = []
    if isinstance(request.get("not_proven"), list):
        source_values.extend(request.get("not_proven"))
    if isinstance(summary_fragment.get("not_proven"), list):
        source_values.extend(summary_fragment.get("not_proven"))
    required = (
        "real_phone_device_proof",
        "real_route_elevator_field_pass",
        "real_nav2_fixed_route_run",
        "task_record_real_world_completion",
        "completion_signal_real_world",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "wave_rover_motion",
        "real_serial_or_uart_feedback",
        "real_hil_pass",
        "objective_5_external_proof",
    )
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _mobile_real_device_field_trial_acceptance_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    defaults = {
        "real_phone_device",
        "production_app",
        "real_pwa_prompt_or_user_choice",
        "real_cloud_or_4g",
        "oss_cdn_live_traffic",
        "nav2_fixed_route_run",
        "wave_rover_motion",
        "hil_pass",
        "route_elevator_field_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
    }
    values = set(defaults)
    for source in (handoff, summary_fragment):
        if isinstance(source, dict) and isinstance(source.get("not_proven"), list):
            values.update(str(item) for item in source["not_proven"] if str(item or "").strip())
    return sorted(values)


def _mobile_real_device_field_trial_acceptance_execution_pack_not_proven(
    pack=None,
    summary_fragment=None,
):
    # execution pack 只组织真实手机验收要采集的材料；控制、ACK、Nav2、HIL 和交付结果仍未证明。
    defaults = {
        "real_phone_device",
        "production_app",
        "real_pwa_prompt_or_user_choice",
        "real_cloud_or_4g",
        "oss_cdn_live_traffic",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "nav2_fixed_route_run",
        "wave_rover_motion",
        "hil_pass",
        "route_elevator_field_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
    }
    values = set(defaults)
    for source in (pack, summary_fragment):
        if isinstance(source, dict) and isinstance(source.get("not_proven"), list):
            values.update(str(item) for item in source["not_proven"] if str(item or "").strip())
    return sorted(values)


def _mobile_real_device_field_trial_acceptance_execution_callback_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # callback intake 只复核现场回填材料；不能把回填结果升级成真机通过、控制授权或交付成功。
    defaults = {
        "real_phone_device",
        "production_app",
        "real_pwa_prompt_or_user_choice",
        "real_cloud_or_4g",
        "oss_cdn_live_traffic",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "terminal_ack",
        "nav2_fixed_route_run",
        "wave_rover_motion",
        "hil_pass",
        "route_elevator_field_pass",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
    }
    values = set(defaults)
    for source in (intake, summary_fragment):
        if isinstance(source, dict) and isinstance(source.get("not_proven"), list):
            values.update(str(item) for item in source["not_proven"] if str(item or "").strip())
    return sorted(values)

def _default_mobile_route_elevator_field_device_precheck_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 预检 gate 的默认值必须全部 fail-closed，避免 metadata-only 摘要被误用成现场通过或控制授权。
    return {
        "schema": MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "precheck_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "mobile route elevator field device precheck is not configured",
        },
        "safe_evidence_ref": "",
        "device_precheck_summary": {},
        "route_elevator_precheck_summary": {},
        "operator_next_steps": [],
        "mobile_readonly_summary": {
            "safe_copy": "Mobile route/elevator field device precheck is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Mobile route/elevator field device precheck is metadata-only; delivery_success=false.",
        },
        "not_proven": _mobile_route_elevator_field_device_precheck_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "real_device_observed": False,
        "pwa_install_prompt_observed": False,
        "route_elevator_field_pass": False,
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


def _default_mobile_field_material_intake_summary(
    path,
    status="not_configured",
    read_error="",
):
    # intake 默认必须封死所有动作旗标，避免现场材料摘要被误读成 command/ACK 或真实完成。
    return {
        "schema": MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_FIELD_MATERIAL_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "mobile field material intake is not configured",
        },
        "safe_evidence_ref": "",
        "device_observation_summary": {},
        "route_elevator_materials_summary": {},
        "nav2_fixed_route_materials_summary": {},
        "task_record_materials_summary": {},
        "completion_signal_summary": {},
        "dropoff_cancel_materials_summary": {},
        "operator_next_steps": [],
        "mobile_readonly_summary": {
            "safe_copy": "Mobile field material intake is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Mobile field material intake is metadata-only; delivery_success=false.",
        },
        "not_proven": _mobile_field_material_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "same_evidence_ref_required": True,
        "real_device_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "task_record_completion": False,
        "completion_signal_received": False,
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


def _default_mobile_field_material_review_decision_summary(
    path,
    status="not_configured",
    read_error="",
):
    # review decision 默认也要 metadata-only；缺配置时不能暗示 command、ACK、Nav2、HIL 或交付完成。
    return {
        "schema": MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_FIELD_MATERIAL_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "mobile field material review decision is not configured",
        },
        "review_decision": "blocked_not_proven",
        "blocker_classification": "missing_mobile_field_material_review_decision",
        "next_required_evidence": [],
        "owner_handoff": "Product",
        "safe_evidence_ref": "",
        "same_evidence_ref_status": "not_proven",
        "operator_next_steps": [],
        "mobile_readonly_summary": {
            "safe_copy": "Mobile field material review decision is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Mobile field material review decision is metadata-only; delivery_success=false.",
        },
        "not_proven": _mobile_field_material_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "same_evidence_ref_required": True,
        "real_device_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "task_record_completion": False,
        "completion_signal_received": False,
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


def _default_mobile_field_material_retest_request_summary(
    path,
    status="not_configured",
    read_error="",
):
    # retest request 的默认输出保持 fail-closed，避免缺 artifact 时被前端或诊断误读成可复测/已通过。
    return {
        "schema": MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_FIELD_MATERIAL_RETEST_REQUEST_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "retest_request_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error or "mobile field material retest request is not configured",
        },
        "source_review_decision": "blocked_not_proven",
        "blockers": [],
        "next_required_evidence": [],
        "retest_request": {
            "status": "blocked_not_proven",
            "reason": "mobile field material retest request is not configured",
        },
        "route_elevator_material_checklist": [],
        "owner_handoff": "Product",
        "safe_evidence_ref": "",
        "same_evidence_ref_status": "not_proven",
        "operator_next_steps": [],
        "mobile_readonly_summary": {
            "safe_copy": "Mobile field material retest request is metadata-only; delivery_success=false.",
            "safe_phone_copy": "Mobile field material retest request is metadata-only; delivery_success=false.",
        },
        "not_proven": _mobile_field_material_retest_request_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "same_evidence_ref_required": True,
        "real_device_observed": False,
        "route_elevator_field_pass": False,
        "nav2_fixed_route_run": False,
        "task_record_completion": False,
        "completion_signal_received": False,
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


def _default_mobile_real_device_field_trial_acceptance_review_handoff_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认输出必须可被前端安全读取，但不能被误当成真实手机验收或机器人控制授权。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance review handoff is not configured",
        },
        "safe_evidence_ref": "",
        "owner_handoff": [],
        "next_required_evidence": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "rerun_commands_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance review handoff is metadata-only; "
                "safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance review handoff is metadata-only; "
                "safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance review handoff is metadata-only; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance review handoff is metadata-only; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "not_proven": _mobile_real_device_field_trial_acceptance_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_pack_summary(
    path,
    status="not_configured",
    read_error="",
):
    # execution pack 默认只能呈现“待人工执行”的安全摘要，不能变成手机或机器人动作入口。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "execution_pack_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution pack is not configured",
            "evidence_source": "software_proof",
        },
        "safe_evidence_ref": "",
        "source_review_handoff": {"status": "not_configured", "verdict": "not_proven"},
        "owner_handoff": [],
        "next_required_evidence": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "execution_steps_summary": [],
        "rerun_commands_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution pack is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution pack is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution pack is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution pack is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": _mobile_real_device_field_trial_acceptance_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary(
    path,
    status="not_configured",
    read_error="",
):
    # callback intake 默认也必须完整输出 false 栅栏，避免被手机端或 Robot 侧误用为控制入口。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "callback_intake_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution callback intake is not configured",
            "evidence_source": "software_proof",
        },
        "safe_evidence_ref": "",
        "source_execution_pack": {"status": "not_configured", "verdict": "not_proven"},
        "owner_handoff": [],
        "next_required_evidence": [],
        "accepted_callback_evidence": [],
        "missing_callback_evidence": [],
        "rejected_callback_evidence": [],
        "rerun_guidance": [],
        "rerun_commands_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution callback intake is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution callback intake is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution callback intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution callback intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": _mobile_real_device_field_trial_acceptance_execution_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_not_proven(
    source=None,
    summary_fragment=None,
):
    # review decision 仍只是复核入口，显式保留所有真实控制和真机验收缺口。
    values = []
    for item in (
        "real_iPhone_or_Android_device",
        "production_mobile_app",
        "real_PWA_prompt_or_user_choice",
        "real_phone_browser_acceptance",
        "Objective_5_external_cloud_proof",
        "route_elevator_field_pass",
        "Nav2_fixed_route_run",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
    ):
        values.append(item)
    for container in (source or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_not_proven(
    source=None,
    summary_fragment=None,
):
    # handoff 只把 review decision 转成 owner 待办；真实手机、O5、O1、HIL 和交付闭环仍未证明。
    values = []
    for item in (
        "real_iPhone_or_Android_device",
        "production_mobile_app",
        "real_phone_browser_acceptance",
        "Objective_5_external_cloud_proof",
        "Objective_1_hil_or_real_materials",
        "route_elevator_field_pass",
        "Nav2_fixed_route_run",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
    ):
        values.append(item)
    for container in (source or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _mobile_real_device_field_trial_acceptance_execution_handoff_intake_not_proven(
    source=None,
    summary_fragment=None,
):
    # handoff intake 只是 owner ack/readiness 摘要；真实手机、PWA、O5、HIL 和交付闭环仍未证明。
    values = []
    for item in (
        "real_iPhone_or_Android_device",
        "production_mobile_app",
        "real_PWA_prompt_or_user_choice",
        "real_phone_browser_acceptance",
        "Objective_5_external_cloud_proof",
        "Objective_1_hil_or_real_materials",
        "route_elevator_field_pass",
        "Nav2_fixed_route_run",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
    ):
        values.append(item)
    for container in (source or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_not_proven(
    source=None,
    summary_fragment=None,
):
    # review decision 只把 intake 状态归档成 accepted/missing/rejected/blocked；真实手机和机器人闭环仍未证明。
    values = []
    for item in (
        "real_iPhone_or_Android_device",
        "production_mobile_app",
        "real_PWA_prompt_or_user_choice",
        "real_phone_browser_acceptance",
        "Objective_5_external_cloud_proof",
        "Objective_1_hil_or_real_materials",
        "route_elevator_field_pass",
        "Nav2_fixed_route_run",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
    ):
        values.append(item)
    for container in (source or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_not_proven(
    source=None,
    summary_fragment=None,
):
    # handoff 只把复核结果交给现场 owner；真实手机、HIL、交付闭环和控制授权仍未证明。
    values = []
    for item in (
        "real_iPhone_or_Android_device",
        "production_mobile_app",
        "real_PWA_prompt_or_user_choice",
        "real_phone_browser_acceptance",
        "Objective_5_external_cloud_proof",
        "Objective_1_hil_or_real_materials",
        "route_elevator_field_pass",
        "Nav2_fixed_route_run",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
    ):
        values.append(item)
    for container in (source or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认摘要完整输出 false 栅栏，防止 diagnostics alias 被误解成真机验收或控制通道。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution callback review decision is not configured",
            "evidence_source": "software_proof",
        },
        "safe_evidence_ref": "",
        "source_callback_intake_status": {
            "status": "not_configured",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
        },
        "review_decision": "needs_callback_review",
        "decision_reasons": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "accepted_callback_evidence": [],
        "missing_callback_evidence": [],
        "rejected_callback_evidence": [],
        "rerun_guidance": [],
        "rerun_commands_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution callback review decision is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution callback review decision is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution callback review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution callback review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认摘要必须完整 fail closed，避免缺 handoff artifact 时被误解成真机验收或控制授权。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution callback review handoff is not configured",
            "evidence_source": "software_proof",
        },
        "safe_evidence_ref": "",
        "source_review_decision_status": {
            "status": "not_configured",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
        },
        "source_review_decision": "needs_callback_review",
        "owner_handoff": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "blocker_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution callback review handoff is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution callback review handoff is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution callback review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution callback review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": (
            _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 缺少 intake artifact 时仍返回完整 false 栅栏，避免 diagnostics alias 被当成现场验收。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution handoff intake is not configured",
            "evidence_source": "software_proof",
        },
        "safe_evidence_ref": "",
        "source_handoff_status": {
            "status": "not_configured",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
        },
        "owner_ack_status": {
            "status": "missing_owner_ack_not_proven",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
        },
        "missing_evidence": [],
        "next_owner": "",
        "owner_handoff": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "blocker_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution handoff intake is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution handoff intake is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution handoff intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution handoff intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": (
            _mobile_real_device_field_trial_acceptance_execution_handoff_intake_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 缺 review decision 时默认 blocked，保证 diagnostics alias 永远不会扩大成控制或真机验收结论。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution handoff review decision is not configured",
            "evidence_source": "software_proof",
        },
        "source_handoff_intake_status": {
            "status": "not_configured",
            "verdict": "not_proven",
            "evidence_source": "software_proof",
        },
        "review_decision": "blocked",
        "accepted_material_summary": [],
        "missing_material_summary": [],
        "rejected_material_summary": [],
        "blocked_reason": (
            read_error
            or "missing mobile real-device acceptance execution handoff intake summary"
        ),
        "next_owner": "",
        "rerun_guidance": [],
        "safe_evidence_ref": "",
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution handoff review decision is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution handoff review decision is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution handoff review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution handoff review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "not_proven": (
            _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }


def _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary(
    path,
    status="not_configured",
    read_error="",
):
    # 默认 handoff 摘要保持完整 false 栅栏，避免缺少来源时被误读成现场 owner 已完成验收。
    return {
        "schema": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "reason": read_error
            or "mobile real-device field-trial acceptance execution handoff review handoff is not configured",
            "evidence_source": "software_proof",
        },
        "current_decision": "blocked",
        "handoff_owner": "",
        "handoff_reason": read_error
        or "missing mobile real-device acceptance execution handoff review decision summary",
        "accepted_summary": [],
        "missing_summary": [],
        "rejected_summary": [],
        "blocked_summary": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "safe_evidence_ref": "",
        "same_evidence_ref_required": True,
        "robot_diagnostics_summary": {
            "safe_copy": (
                "Mobile real-device acceptance execution handoff review handoff is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
            "safe_phone_copy": (
                "Mobile real-device acceptance execution handoff review handoff is metadata-only; "
                "source=software_proof; safe_to_control=false; delivery_success=false; "
                "primary_actions_enabled=false; not_proven."
            ),
        },
        "safe_copy": (
            "Mobile real-device acceptance execution handoff review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "safe_phone_copy": (
            "Mobile real-device acceptance execution handoff review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        ),
        "source": "software_proof",
        "software_proof": True,
        "not_proven": (
            _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
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
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
    }

def _mobile_route_elevator_field_device_precheck_has_unsafe_fields(value, key_path=""):
    # 预检 source 可能来自手机/人工材料；控制、ACK、持久化或成功布尔为真时必须整体降级。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_artifact",
        "raw_payload",
        "raw_response",
        "raw_robot",
        "raw_command",
        "raw_ack",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
        "real_device_observed",
        "pwa_install_prompt_observed",
        "route_elevator_field_pass",
        "dropoff_completion",
        "cancel_completion",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "remote_ack_posted",
        "terminal_ack_posted",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "not_proven":
                continue
            if _mobile_route_elevator_field_device_precheck_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(_mobile_route_elevator_field_device_precheck_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        lowered = redacted.lower()
        guarded = lowered
        for phrase in (
            "not delivery success",
            "delivery_success=false",
            "not_proven",
            "not proven",
            "metadata-only",
            "must not",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            "/api/collect" in guarded
            or "ack posted" in guarded
            or "cursor advanced" in guarded
            or "nav2 started" in guarded
            or "dropoff complete" in guarded
            or "cancel complete" in guarded
            or "delivery success" in guarded
            or "real device observed" in guarded
            or "pwa install prompt observed" in guarded
            or "route elevator field pass" in guarded
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
    return False


def _mobile_field_material_intake_has_unsafe_fields(value, key_path=""):
    # intake 会承接手机和现场人工材料；只要出现 raw 控制/ACK/硬件字段或完成 claim，就必须 fail closed。
    unsafe_key_fragments = (
        "authorization",
        "token",
        "secret",
        "access_key",
        "password",
        "credential",
        "checksum",
        "traceback",
        "raw_artifact",
        "raw_json",
        "raw_payload",
        "raw_response",
        "raw_ros",
        "raw_robot",
        "raw_command",
        "raw_ack",
        "ros_topic",
        "hardware_path",
        "command_envelope",
        "status_envelope",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
    )
    unsafe_true_keys = {
        "delivery_success",
        "primary_actions_enabled",
        "real_device_observed",
        "route_elevator_field_pass",
        "nav2_fixed_route_run",
        "task_record_completion",
        "completion_signal_received",
        "dropoff_completion",
        "cancel_completion",
        "ack_post_allowed",
        "remote_ack_allowed",
        "cursor_updates_allowed",
        "persistence_updates_allowed",
        "terminal_ack_allowed",
        "nav2_triggered",
        "hil_pass",
        "production_ready",
        "collect_triggered",
        "dropoff_triggered",
        "cancel_triggered",
        "remote_ack_posted",
        "terminal_ack_posted",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            current_path = f"{key_path}.{key_text}" if key_path else key_text
            if key_text in unsafe_true_keys and bool(item):
                return True
            if key_text == "same_evidence_ref_required" and item is not True:
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "not_proven":
                continue
            if _mobile_field_material_intake_has_unsafe_fields(item, current_path):
                return True
        return False
    if isinstance(value, list):
        return any(_mobile_field_material_intake_has_unsafe_fields(item, key_path) for item in value)
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value)
        guarded = redacted.lower()
        for phrase in (
            "not delivery success",
            "delivery_success=false",
            "not_proven",
            "not proven",
            "metadata-only",
            "must not",
            "not real",
            "不证明",
        ):
            guarded = guarded.replace(phrase, "")
        return (
            "/api/collect" in guarded
            or "ack posted" in guarded
            or "remote ack" in guarded
            or "terminal ack" in guarded
            or "cursor advanced" in guarded
            or "persistence updated" in guarded
            or "nav2 started" in guarded
            or "hil pass" in guarded
            or "dropoff complete" in guarded
            or "cancel complete" in guarded
            or "delivery success" in guarded
            or "real route/elevator field pass" in guarded
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
    return False

def _mobile_route_elevator_field_device_precheck_source_contract(value):
    # 允许直接 artifact 或已生成 summary，但 summary wrapper 也必须回指同一个 precheck gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_field_material_intake_source_contract(value):
    # 支持直接 artifact 或已生成 summary；summary wrapper 仍必须回指 intake schema 和同一 evidence boundary。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_field_material_review_decision_source_contract(value):
    # 支持直接 artifact 或已生成 summary；summary wrapper 仍必须回指 review decision schema 和同一 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_field_material_retest_request_source_contract(value):
    # 支持直接 artifact 或已生成 summary；summary wrapper 不能把 review decision gate 混成 retest request gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_review_handoff_source_contract(value):
    # 支持 Full-stack/Product 产出的 artifact 或 summary；summary 必须回指同一个 handoff gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_pack_source_contract(value):
    # 支持 direct artifact、summary 和 Robot diagnostics alias；summary 必须回指 execution pack gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_callback_intake_source_contract(value):
    # 支持 direct artifact、summary 和 Robot diagnostics alias；summary 必须回指 callback intake gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_contract(
    value,
):
    # 支持 direct artifact、summary 和 Robot diagnostics alias；summary 必须回指 review decision gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_contract(
    value,
):
    # handoff 可从本轮 handoff summary 或上一轮 review decision summary 派生，但都必须保留原 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_contract(
    value,
):
    # intake 只接受本轮 intake summary 或上一轮 handoff summary；向前追溯时仍必须保留原 gate。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_contract(
    value,
):
    # review decision 只能从本轮决策 summary 或上一轮 handoff intake summary 派生，不能追读 raw artifact。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA
        and value.get("source_schema")
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_contract(
    value,
):
    # handoff 必须回指上一轮 review decision；直接 handoff wrapper 也只能携带已消毒 source_*。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY_SCHEMA
        or (
            source_schema
            == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA
            and value.get("source_schema")
        )
    ):
        source_schema = str(value.get("source_schema") or source_schema)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy(
    value,
):
    # 本 gate 面向现场 handoff，不允许出现成功、pass、HIL、control 或完整 artifact/checksum 暗示。
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in {"complete_artifact", "artifact_checksum", "checksum"}:
                return True
            if _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy(
                item
            )
            for item in value
        )
    if not isinstance(value, str):
        return False
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    guarded = text
    for phrase in (
        "not delivery success",
        "delivery_success=false",
        "safe_to_control=false",
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
        "delivery success" in guarded
        or "delivery-success" in guarded
        or " hil " in f" {guarded} "
        or "hil pass" in guarded
        or "field pass" in guarded
        or " pass " in f" {guarded} "
        or "control" in guarded
        or "safe to control" in guarded
        or "complete artifact" in guarded
        or "checksum" in guarded
    )

def summarize_mobile_route_elevator_field_device_precheck(path):
    """构建 mobile route/elevator field-device precheck 的 metadata-only diagnostics 摘要。"""
    precheck_path = os.path.expanduser(str(path or ""))
    summary = _default_mobile_route_elevator_field_device_precheck_summary(
        precheck_path,
        read_error="mobile route elevator field device precheck is not configured",
    )
    if not precheck_path:
        return summary
    if not os.path.exists(precheck_path):
        summary.update(
            {
                "precheck_status": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "mobile route elevator field device precheck artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile route/elevator field device precheck is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile route/elevator field device precheck is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(precheck_path, "r", encoding="utf-8") as f:
            precheck = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(
            f"failed reading mobile route elevator field device precheck: {exc}"
        )
        summary.update(
            {
                "precheck_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile route/elevator field device precheck could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile route/elevator field device precheck could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(precheck, dict):
        summary.update(
            {
                "precheck_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile route elevator field device precheck JSON must be an object",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile route/elevator field device precheck shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile route/elevator field device precheck shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只消费白名单 summary 字段；原始手机、路线、电梯和控制材料都留在 source artifact 外部。
    summary_fragment = {}
    for candidate in (
        precheck.get("mobile_readonly_summary"),
        precheck.get("phone_safe_summary"),
        precheck.get("device_precheck_summary"),
        precheck.get("route_elevator_precheck_summary"),
        precheck.get("mobile_route_elevator_field_device_precheck_summary"),
        precheck.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _mobile_route_elevator_field_device_precheck_source_contract(precheck)
    status_source = (
        precheck.get("precheck_status")
        if isinstance(precheck.get("precheck_status"), dict)
        else summary_fragment.get("precheck_status")
        if isinstance(summary_fragment.get("precheck_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or precheck.get("safe_copy")
        or precheck.get("safe_phone_copy")
        or "Mobile route/elevator field device precheck is metadata-only; delivery_success=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": precheck.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "precheck_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or precheck.get("status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or precheck.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or precheck.get("reason")
                    or "mobile route elevator field device precheck consumed without explicit reason"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or precheck.get("safe_evidence_ref")
                or precheck.get("evidence_ref", "")
            ),
            "device_precheck_summary": _safe_pc_route_debug_dict(
                precheck.get("device_precheck_summary")
                if isinstance(precheck.get("device_precheck_summary"), dict)
                else summary_fragment.get("device_precheck_summary")
            ),
            "route_elevator_precheck_summary": _safe_pc_route_debug_dict(
                precheck.get("route_elevator_precheck_summary")
                if isinstance(precheck.get("route_elevator_precheck_summary"), dict)
                else summary_fragment.get("route_elevator_precheck_summary")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                precheck.get("operator_next_steps")
                if isinstance(precheck.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "mobile_readonly_summary": mobile_summary,
            "not_proven": _mobile_route_elevator_field_device_precheck_not_proven(
                precheck,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "real_device_observed": False,
            "pwa_install_prompt_observed": False,
            "route_elevator_field_pass": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SCHEMA,
        MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary != MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_GATE
    ):
        summary.update(
            {
                "precheck_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile route elevator field device precheck schema or evidence boundary is unsupported",
                },
                "device_precheck_summary": {},
                "route_elevator_precheck_summary": {},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile route/elevator field device precheck is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Mobile route/elevator field device precheck is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        _mobile_route_elevator_field_device_precheck_has_unsafe_fields(precheck)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "precheck_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile route elevator field device precheck contains unsafe fields or success/control claims",
                },
                "device_precheck_summary": {},
                "route_elevator_precheck_summary": {},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile route/elevator field device precheck was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Mobile route/elevator field device precheck was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_mobile_field_material_intake(path):
    """构建 mobile field material intake 的 metadata-only diagnostics 摘要。"""
    intake_path = os.path.expanduser(str(path or ""))
    summary = _default_mobile_field_material_intake_summary(
        intake_path,
        read_error="mobile field material intake is not configured",
    )
    if not intake_path:
        return summary
    if not os.path.exists(intake_path):
        summary.update(
            {
                "intake_status": {
                    "status": "missing",
                    "verdict": "not_proven",
                    "reason": "mobile field material intake artifact missing",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material intake is missing; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile field material intake is missing; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    try:
        with open(intake_path, "r", encoding="utf-8") as f:
            intake = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        safe_error = _redact_route_task_rehearsal_text(f"failed reading mobile field material intake: {exc}")
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": safe_error,
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material intake could not be read; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile field material intake could not be read; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile field material intake JSON must be an object",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material intake shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile field material intake shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只消费 phone-safe summary 形态，避免 raw 手机材料、控制 envelope 或完整现场 artifact 进入 diagnostics。
    summary_fragment = {}
    for candidate in (
        intake.get("mobile_field_material_intake_summary"),
        intake.get("mobile_readonly_summary"),
        intake.get("phone_safe_summary"),
        intake.get("robot_diagnostics_summary"),
        intake.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _mobile_field_material_intake_source_contract(intake)
    status_source = (
        intake.get("intake_status")
        if isinstance(intake.get("intake_status"), dict)
        else summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or "Mobile field material intake is metadata-only; delivery_success=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": intake.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or intake.get("status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or intake.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or intake.get("reason")
                    or "mobile field material intake consumed without explicit reason"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or intake.get("safe_evidence_ref")
                or intake.get("evidence_ref", "")
            ),
            "device_observation_summary": _safe_pc_route_debug_dict(
                intake.get("device_observation_summary")
                if isinstance(intake.get("device_observation_summary"), dict)
                else summary_fragment.get("device_observation_summary")
            ),
            "route_elevator_materials_summary": _safe_pc_route_debug_dict(
                intake.get("route_elevator_materials_summary")
                if isinstance(intake.get("route_elevator_materials_summary"), dict)
                else summary_fragment.get("route_elevator_materials_summary")
            ),
            "nav2_fixed_route_materials_summary": _safe_pc_route_debug_dict(
                intake.get("nav2_fixed_route_materials_summary")
                if isinstance(intake.get("nav2_fixed_route_materials_summary"), dict)
                else summary_fragment.get("nav2_fixed_route_materials_summary")
            ),
            "task_record_materials_summary": _safe_pc_route_debug_dict(
                intake.get("task_record_materials_summary")
                if isinstance(intake.get("task_record_materials_summary"), dict)
                else summary_fragment.get("task_record_materials_summary")
            ),
            "completion_signal_summary": _safe_pc_route_debug_dict(
                intake.get("completion_signal_summary")
                if isinstance(intake.get("completion_signal_summary"), dict)
                else summary_fragment.get("completion_signal_summary")
            ),
            "dropoff_cancel_materials_summary": _safe_pc_route_debug_dict(
                intake.get("dropoff_cancel_materials_summary")
                if isinstance(intake.get("dropoff_cancel_materials_summary"), dict)
                else summary_fragment.get("dropoff_cancel_materials_summary")
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                intake.get("operator_next_steps")
                if isinstance(intake.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "mobile_readonly_summary": mobile_summary,
            "not_proven": _mobile_field_material_intake_not_proven(intake, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "same_evidence_ref_required": True,
            "real_device_observed": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "task_record_completion": False,
            "completion_signal_received": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_FIELD_MATERIAL_INTAKE_SCHEMA,
        MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != MOBILE_FIELD_MATERIAL_INTAKE_GATE:
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile field material intake schema or evidence boundary is unsupported",
                },
                "device_observation_summary": {},
                "route_elevator_materials_summary": {},
                "nav2_fixed_route_materials_summary": {},
                "task_record_materials_summary": {},
                "completion_signal_summary": {},
                "dropoff_cancel_materials_summary": {},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material intake is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Mobile field material intake is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(intake) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "intake_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile field material intake contains unsafe fields or success/control claims",
                },
                "device_observation_summary": {},
                "route_elevator_materials_summary": {},
                "nav2_fixed_route_materials_summary": {},
                "task_record_materials_summary": {},
                "completion_signal_summary": {},
                "dropoff_cancel_materials_summary": {},
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material intake was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Mobile field material intake was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_mobile_field_material_review_decision(source):
    """构建 mobile field material review decision 的 metadata-only diagnostics 摘要。"""
    # 允许 build_diagnostics_payload 直接传入 diagnostics source 字典；路径读取仍覆盖 explicit ref / env 场景。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_field_material_review_decision_summary(
        source_path,
        read_error="mobile field material review decision is not configured",
    )
    if isinstance(source, dict):
        review = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "mobile field material review decision artifact missing",
                    },
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material review decision is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile field material review decision is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                review = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile field material review decision: {exc}"
            )
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material review decision could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile field material review decision could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(review, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile field material review decision JSON must be an object",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material review decision shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile field material review decision shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只消费 phone-safe summary 片段；raw artifact 只能用于 schema/boundary 和保守状态字段归一。
    summary_fragment = {}
    for candidate in (
        review.get("mobile_field_material_review_decision_summary"),
        review.get("mobile_readonly_summary"),
        review.get("phone_safe_summary"),
        review.get("robot_diagnostics_summary"),
        review.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _mobile_field_material_review_decision_source_contract(review)
    status_source = (
        review.get("review_status")
        if isinstance(review.get("review_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or review.get("safe_copy")
        or review.get("safe_phone_copy")
        or "Mobile field material review decision is metadata-only; delivery_success=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": review.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or review.get("status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or review.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or review.get("reason")
                    or "mobile field material review decision consumed without explicit reason"
                ),
            },
            "review_decision": _redact_route_task_rehearsal_text(
                review.get("review_decision")
                or summary_fragment.get("review_decision")
                or "blocked_not_proven"
            ),
            "blocker_classification": _redact_route_task_rehearsal_text(
                review.get("blocker_classification")
                or summary_fragment.get("blocker_classification")
                or "blocked_missing_mobile_field_material_review_decision"
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                review.get("next_required_evidence")
                if isinstance(review.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _redact_route_task_rehearsal_text(
                review.get("owner_handoff")
                or summary_fragment.get("owner_handoff")
                or "Product"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or review.get("safe_evidence_ref")
                or review.get("evidence_ref", "")
            ),
            "same_evidence_ref_status": _redact_route_task_rehearsal_text(
                review.get("same_evidence_ref_status")
                or summary_fragment.get("same_evidence_ref_status")
                or "not_proven"
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                review.get("operator_next_steps")
                if isinstance(review.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "mobile_readonly_summary": mobile_summary,
            "not_proven": _mobile_field_material_review_decision_not_proven(review, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "same_evidence_ref_required": True,
            "real_device_observed": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "task_record_completion": False,
            "completion_signal_received": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA,
        MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != MOBILE_FIELD_MATERIAL_REVIEW_DECISION_GATE:
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile field material review decision schema or evidence boundary is unsupported",
                },
                "review_decision": "blocked_not_proven",
                "blocker_classification": "unsupported_mobile_field_material_review_decision_schema",
                "next_required_evidence": [],
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material review decision is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Mobile field material review decision is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(review) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile field material review decision contains unsafe fields or success/control claims",
                },
                "review_decision": "blocked_not_proven",
                "blocker_classification": "unsafe_mobile_field_material_review_decision",
                "next_required_evidence": [],
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material review decision was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Mobile field material review decision was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_mobile_field_material_retest_request(source):
    """构建 mobile field material retest request 的 metadata-only diagnostics 摘要。"""
    # 支持 explicit ref、env path 和 diagnostics source dict；三者都只进入白名单摘要，不转发 raw artifact。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_field_material_retest_request_summary(
        source_path,
        read_error="mobile field material retest request is not configured",
    )
    if isinstance(source, dict):
        request = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "retest_request_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "mobile field material retest request artifact missing",
                    },
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material retest request is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile field material retest request is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                request = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile field material retest request: {exc}"
            )
            summary.update(
                {
                    "retest_request_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "mobile_readonly_summary": {
                        "safe_copy": "Mobile field material retest request could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile field material retest request could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(request, dict):
        summary.update(
            {
                "retest_request_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile field material retest request JSON must be an object",
                },
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material retest request shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile field material retest request shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    # 只选取 summary/phone-safe 片段；raw artifact 中的路径、topic、ACK、command 字段不会进入输出。
    summary_fragment = {}
    for candidate in (
        request.get("mobile_field_material_retest_request_summary"),
        request.get("mobile_readonly_summary"),
        request.get("phone_safe_summary"),
        request.get("robot_diagnostics_summary"),
        request.get("summary"),
    ):
        if isinstance(candidate, dict):
            summary_fragment = candidate
            break
    source_schema, source_boundary = _mobile_field_material_retest_request_source_contract(request)
    status_source = (
        request.get("retest_request_status")
        if isinstance(request.get("retest_request_status"), dict)
        else summary_fragment.get("retest_request_status")
        if isinstance(summary_fragment.get("retest_request_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or request.get("safe_copy")
        or request.get("safe_phone_copy")
        or "Mobile field material retest request is metadata-only; delivery_success=false."
    )
    mobile_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            mobile_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    mobile_summary["safe_copy"] = safe_copy
    mobile_summary["safe_phone_copy"] = safe_copy
    blockers = (
        request.get("blockers")
        if isinstance(request.get("blockers"), list)
        else request.get("blocked_categories")
        if isinstance(request.get("blocked_categories"), list)
        else [request.get("blocker_classification")]
        if str(request.get("blocker_classification") or "").strip()
        else []
    )
    checklist = (
        request.get("route_elevator_material_checklist")
        if isinstance(request.get("route_elevator_material_checklist"), list)
        else request.get("material_checklist")
        if isinstance(request.get("material_checklist"), list)
        else summary_fragment.get("route_elevator_material_checklist")
        if isinstance(summary_fragment.get("route_elevator_material_checklist"), list)
        else []
    )
    retest_request = (
        request.get("retest_request")
        if isinstance(request.get("retest_request"), dict)
        else summary_fragment.get("retest_request")
        if isinstance(summary_fragment.get("retest_request"), dict)
        else {"status": request.get("status") or summary_fragment.get("status") or "blocked_not_proven"}
    )
    source_review_decision = (
        request.get("source_review_decision")
        if "source_review_decision" in request
        else summary_fragment.get("source_review_decision")
        if "source_review_decision" in summary_fragment
        else request.get("review_decision")
        or summary_fragment.get("review_decision")
        or "blocked_not_proven"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": request.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "retest_request_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or request.get("status")
                    or "blocked"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or request.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or request.get("reason")
                    or "mobile field material retest request consumed without explicit reason"
                ),
            },
            "source_review_decision": _safe_pc_route_debug_value(source_review_decision),
            "blockers": _safe_route_task_rehearsal_list(blockers),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                request.get("next_required_evidence")
                if isinstance(request.get("next_required_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "retest_request": _safe_pc_route_debug_value(retest_request),
            "route_elevator_material_checklist": _safe_pc_route_debug_value(checklist),
            "owner_handoff": _redact_route_task_rehearsal_text(
                request.get("owner_handoff")
                or summary_fragment.get("owner_handoff")
                or "Product"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or request.get("safe_evidence_ref")
                or request.get("evidence_ref", "")
            ),
            "same_evidence_ref_status": _redact_route_task_rehearsal_text(
                request.get("same_evidence_ref_status")
                or summary_fragment.get("same_evidence_ref_status")
                or "not_proven"
            ),
            "operator_next_steps": _safe_route_task_rehearsal_list(
                request.get("operator_next_steps")
                if isinstance(request.get("operator_next_steps"), list)
                else summary_fragment.get("operator_next_steps")
            ),
            "mobile_readonly_summary": mobile_summary,
            "not_proven": _mobile_field_material_retest_request_not_proven(request, summary_fragment),
            "read_error": "",
            "metadata_only": True,
            "same_evidence_ref_required": request.get("same_evidence_ref_required", True) is True,
            "real_device_observed": False,
            "route_elevator_field_pass": False,
            "nav2_fixed_route_run": False,
            "task_record_completion": False,
            "completion_signal_received": False,
            "dropoff_completion": False,
            "cancel_completion": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SCHEMA,
        MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != MOBILE_FIELD_MATERIAL_RETEST_REQUEST_GATE:
        summary.update(
            {
                "retest_request_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile field material retest request schema or evidence boundary is unsupported",
                },
                "source_review_decision": "blocked_not_proven",
                "blockers": [],
                "next_required_evidence": [],
                "retest_request": {"status": "blocked_not_proven"},
                "route_elevator_material_checklist": [],
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material retest request is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Mobile field material retest request is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if _mobile_field_material_intake_has_unsafe_fields(request) or _route_task_field_run_readiness_copy_is_unsafe(safe_copy):
        summary.update(
            {
                "retest_request_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile field material retest request contains unsafe fields or success/control claims",
                },
                "source_review_decision": "blocked_not_proven",
                "blockers": [],
                "next_required_evidence": [],
                "retest_request": {"status": "blocked_not_proven"},
                "route_elevator_material_checklist": [],
                "operator_next_steps": [],
                "mobile_readonly_summary": {
                    "safe_copy": "Mobile field material retest request was blocked because fields could expose control data or imply delivery success.",
                    "safe_phone_copy": "Mobile field material retest request was blocked because fields could expose control data or imply delivery success.",
                },
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_review_handoff(source):
    """构建 real-device acceptance review handoff 的 metadata-only diagnostics 摘要。"""
    # Robot 只读取 Full-stack/Product 产出的安全 summary；raw 手机材料、路径和控制 claim 必须停在边界外。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_real_device_field_trial_acceptance_review_handoff_summary(
        source_path,
        read_error="mobile real-device field-trial acceptance review handoff is not configured",
    )
    if isinstance(source, dict):
        handoff = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance review handoff is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance review handoff is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance review handoff: {exc}"
            )
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance review handoff could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance review handoff could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance review handoff JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance review handoff shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device acceptance review handoff shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 优先选择已消毒 summary/alias；直接 artifact 只用于兼容同 gate 且仍需通过安全字段检查。
    summary_fragment = {}
    for candidate in (
        handoff
        if handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {},
        handoff.get("mobile_real_device_field_trial_acceptance_review_handoff_summary"),
        handoff.get("robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary"),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("summary"),
        diagnostics.get("mobile_real_device_field_trial_acceptance_review_handoff_summary"),
        diagnostics.get("robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and handoff.get("schema")
                == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA
            )
        )
        and handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA
    ):
        summary_fragment = handoff
    if not summary_fragment:
        source_schema, source_boundary = _mobile_real_device_field_trial_acceptance_review_handoff_source_contract(
            handoff
        )
        if source_schema or source_boundary:
            summary.update(
                {
                    "source_schema": _redact_route_task_rehearsal_text(source_schema),
                    "source_schema_version": handoff.get("schema_version"),
                    "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                    "handoff_status": {
                        "status": "unsupported_schema",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance review handoff schema or evidence boundary is unsupported",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance review handoff is not a supported diagnostics source; no delivery result is proven.",
                        "safe_phone_copy": "Mobile real-device acceptance review handoff is not a supported diagnostics source; no delivery result is proven.",
                    },
                }
            )
            return summary
        summary.update(
            {
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance review handoff lacks a safe summary",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance review handoff is blocked because no safe summary was provided.",
                    "safe_phone_copy": "Mobile real-device acceptance review handoff is blocked because no safe summary was provided.",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = _mobile_real_device_field_trial_acceptance_review_handoff_source_contract(
        contract_source
    )
    status_source = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else handoff.get("handoff_status")
        if isinstance(handoff.get("handoff_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance review handoff is metadata-only; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or handoff.get("status")
                    or "blocked_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance review handoff consumed without explicit reason"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or handoff.get("safe_evidence_ref")
                or handoff.get("evidence_ref", "")
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                if isinstance(summary_fragment.get("accepted_materials_summary"), list)
                else summary_fragment.get("accepted_materials")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                if isinstance(summary_fragment.get("missing_materials_summary"), list)
                else summary_fragment.get("missing_materials")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                if isinstance(summary_fragment.get("rejected_materials_summary"), list)
                else summary_fragment.get("rejected_materials")
            ),
            "rerun_commands_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands_summary")
                if isinstance(summary_fragment.get("rerun_commands_summary"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "not_proven": _mobile_real_device_field_trial_acceptance_review_handoff_not_proven(
                handoff, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_GATE:
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance review handoff schema or evidence boundary is unsupported",
                },
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "rerun_commands_summary": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance review handoff is not a supported diagnostics source; no delivery result is proven.",
                    "safe_phone_copy": "Mobile real-device acceptance review handoff is not a supported diagnostics source; no delivery result is proven.",
                },
            }
        )
        return summary

    if (
        not summary["safe_evidence_ref"]
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance review handoff contains unsafe raw fields, success claims, or control claims",
                },
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "rerun_commands_summary": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance review handoff was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_pack(source):
    """构建 real-device acceptance execution pack 的只读 diagnostics 摘要。"""
    # Robot diagnostics 只复制白名单字段；执行包不能触发 collect/dropoff/cancel/ACK/cursor/Nav2/HIL。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_real_device_field_trial_acceptance_execution_pack_summary(
        source_path,
        read_error="mobile real-device field-trial acceptance execution pack is not configured",
    )
    if isinstance(source, dict):
        pack = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance execution pack summary missing",
                        "evidence_source": "software_proof",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution pack is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution pack is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance execution pack: {exc}"
            )
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution pack could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution pack could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution pack JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution pack shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device acceptance execution pack shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        pack
        if pack.get("schema") == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA
        else {},
        pack.get("mobile_real_device_field_trial_acceptance_execution_pack_summary"),
        pack.get("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary"),
        pack.get("robot_diagnostics_summary"),
        pack.get("mobile_readonly_summary"),
        pack.get("phone_safe_summary"),
        pack.get("summary"),
        diagnostics.get("mobile_real_device_field_trial_acceptance_execution_pack_summary"),
        diagnostics.get("robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary"),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and pack.get("schema") == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA
            )
        )
        and pack.get("schema") == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA
    ):
        summary_fragment = pack
    if not summary_fragment:
        source_schema, source_boundary = _mobile_real_device_field_trial_acceptance_execution_pack_source_contract(
            pack
        )
        if source_schema or source_boundary:
            summary.update(
                {
                    "source_schema": _redact_route_task_rehearsal_text(source_schema),
                    "source_schema_version": pack.get("schema_version"),
                    "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                    "execution_pack_status": {
                        "status": "unsupported_schema",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance execution pack schema or evidence boundary is unsupported",
                        "evidence_source": "software_proof",
                    },
                }
            )
            return summary
        summary.update(
            {
                "execution_pack_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution pack lacks a safe summary",
                    "evidence_source": "software_proof",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = _mobile_real_device_field_trial_acceptance_execution_pack_source_contract(
        contract_source
    )
    status_source = (
        summary_fragment.get("execution_pack_status")
        if isinstance(summary_fragment.get("execution_pack_status"), dict)
        else pack.get("execution_pack_status")
        if isinstance(pack.get("execution_pack_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution pack is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_pack_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or pack.get("status")
                    or "blocked_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance execution pack consumed without explicit reason"
                ),
                "evidence_source": "software_proof",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or pack.get("safe_evidence_ref")
                or pack.get("evidence_ref", "")
            ),
            "source_review_handoff": _safe_pc_route_debug_value(
                summary_fragment.get("source_review_handoff")
                or summary_fragment.get("source_review_handoff_summary")
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                if isinstance(summary_fragment.get("accepted_materials_summary"), list)
                else summary_fragment.get("accepted_materials")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                if isinstance(summary_fragment.get("missing_materials_summary"), list)
                else summary_fragment.get("missing_materials")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                if isinstance(summary_fragment.get("rejected_materials_summary"), list)
                else summary_fragment.get("rejected_materials")
            ),
            "execution_steps_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("execution_steps_summary")
                if isinstance(summary_fragment.get("execution_steps_summary"), list)
                else summary_fragment.get("execution_steps")
            ),
            "rerun_commands_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands_summary")
                if isinstance(summary_fragment.get("rerun_commands_summary"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": _mobile_real_device_field_trial_acceptance_execution_pack_not_proven(
                pack, summary_fragment
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or source_boundary != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_GATE:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution pack schema or evidence boundary is unsupported",
                    "evidence_source": "software_proof",
                },
                "source_review_handoff": {"status": "blocked_not_proven", "verdict": "not_proven"},
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "execution_steps_summary": [],
                "rerun_commands_summary": [],
            }
        )
        return summary

    unsafe_source = str(summary_fragment.get("source") or pack.get("source") or "software_proof")
    if (
        unsafe_source != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not summary["safe_evidence_ref"]
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "unsafe_fields",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution pack contains unsafe raw fields, success claims, or control claims",
                    "evidence_source": "software_proof",
                },
                "source_review_handoff": {"status": "blocked_not_proven", "verdict": "not_proven"},
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "execution_steps_summary": [],
                "rerun_commands_summary": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution pack was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance execution pack was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance execution pack was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance execution pack was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_callback_intake(source):
    """构建 real-device acceptance execution callback intake 的只读 diagnostics 摘要。"""
    # Robot diagnostics 只镜像回调复核摘要；这里绝不产生 ACK、cursor、Start/Confirm/Cancel 或机器人命令。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary(
        source_path,
        read_error=(
            "mobile real-device field-trial acceptance execution callback intake is not configured"
        ),
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "callback_intake_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance execution callback intake summary missing",
                        "evidence_source": "software_proof",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution callback intake is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution callback intake is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance execution callback intake: {exc}"
            )
            summary.update(
                {
                    "callback_intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution callback intake could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution callback intake could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback intake JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution callback intake shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device acceptance execution callback intake shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        intake
        if intake.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {},
        intake.get("mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"),
        intake.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"
        ),
        intake.get("robot_diagnostics_summary"),
        intake.get("mobile_readonly_summary"),
        intake.get("phone_safe_summary"),
        intake.get("summary"),
        diagnostics.get("mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and intake.get("schema")
                == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA
            )
        )
        and intake.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA
    ):
        summary_fragment = intake
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_callback_intake_source_contract(
                intake
            )
        )
        if source_schema or source_boundary:
            summary.update(
                {
                    "source_schema": _redact_route_task_rehearsal_text(source_schema),
                    "source_schema_version": intake.get("schema_version"),
                    "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                    "callback_intake_status": {
                        "status": "unsupported_schema",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance execution callback intake schema or evidence boundary is unsupported",
                        "evidence_source": "software_proof",
                    },
                }
            )
            return summary
        summary.update(
            {
                "callback_intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback intake lacks a safe summary",
                    "evidence_source": "software_proof",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_callback_intake_source_contract(
            contract_source
        )
    )
    status_source = (
        summary_fragment.get("callback_intake_status")
        if isinstance(summary_fragment.get("callback_intake_status"), dict)
        else intake.get("callback_intake_status")
        if isinstance(intake.get("callback_intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution callback intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "callback_intake_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or intake.get("status")
                    or "blocked_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance execution callback intake consumed without explicit reason"
                ),
                "evidence_source": "software_proof",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or intake.get("safe_evidence_ref")
                or intake.get("evidence_ref", "")
            ),
            "source_execution_pack": _safe_pc_route_debug_value(
                summary_fragment.get("source_execution_pack")
                or summary_fragment.get("source_execution_pack_summary")
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "accepted_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_callback_evidence")
                if isinstance(summary_fragment.get("accepted_callback_evidence"), list)
                else summary_fragment.get("accepted_materials_summary")
            ),
            "missing_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_callback_evidence")
                if isinstance(summary_fragment.get("missing_callback_evidence"), list)
                else summary_fragment.get("missing_materials_summary")
            ),
            "rejected_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_callback_evidence")
                if isinstance(summary_fragment.get("rejected_callback_evidence"), list)
                else summary_fragment.get("rejected_materials_summary")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "rerun_commands_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands_summary")
                if isinstance(summary_fragment.get("rerun_commands_summary"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": _mobile_real_device_field_trial_acceptance_execution_callback_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary
        != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "callback_intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback intake schema or evidence boundary is unsupported",
                    "evidence_source": "software_proof",
                },
                "source_execution_pack": {"status": "blocked_not_proven", "verdict": "not_proven"},
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_callback_evidence": [],
                "missing_callback_evidence": [],
                "rejected_callback_evidence": [],
                "rerun_guidance": [],
                "rerun_commands_summary": [],
            }
        )
        return summary

    unsafe_source = str(summary_fragment.get("source") or intake.get("source") or "software_proof")
    status_text = str(summary["callback_intake_status"].get("status") or "")
    callback_rejected = bool(summary["rejected_callback_evidence"]) or "rejected" in status_text
    missing_material = bool(summary["missing_callback_evidence"]) or "missing" in status_text
    if (
        unsafe_source != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not summary["safe_evidence_ref"]
        or callback_rejected
        or missing_material
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_reason = "mobile real-device acceptance execution callback intake contains unsafe raw fields, success claims, rejected callback, missing material, or control claims"
        summary.update(
            {
                "callback_intake_status": {
                    "status": "unsafe_fields" if not (callback_rejected or missing_material) else "blocked_not_proven",
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "source_execution_pack": {"status": "blocked_not_proven", "verdict": "not_proven"},
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_callback_evidence": [],
                "rerun_guidance": [],
                "rerun_commands_summary": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution callback intake was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance execution callback intake was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance execution callback intake was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance execution callback intake was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_decision(
    source,
):
    """构建 real-device acceptance execution callback review decision 的只读 diagnostics 摘要。"""
    # 该 alias 只镜像复核决策元数据；任何缺字段、原始材料或控制/成功语义都必须 fail closed。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary(
            source_path,
            read_error=(
                "mobile real-device field-trial acceptance execution callback review decision is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": (
                            "mobile real-device acceptance execution callback review decision summary missing"
                        ),
                        "evidence_source": "software_proof",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution callback review decision is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution callback review decision is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading mobile real-device acceptance execution callback "
                f"review decision: {exc}"
            )
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device acceptance execution callback review decision could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device acceptance execution callback review decision could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback review decision JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution callback review decision shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device acceptance execution callback review decision shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        decision
        if decision.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {},
        decision.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        decision.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        decision.get("robot_diagnostics_summary"),
        decision.get("mobile_readonly_summary"),
        decision.get("phone_safe_summary"),
        decision.get("summary"),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and decision.get("schema")
                == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
            )
        )
        and decision.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
    ):
        summary_fragment = decision
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_contract(
                decision
            )
        )
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary" if not (source_schema or source_boundary) else "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback review decision lacks a safe summary",
                    "evidence_source": "software_proof",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_contract(
            contract_source
        )
    )
    review_source = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else decision.get("review_status")
        if isinstance(decision.get("review_status"), dict)
        else {}
    )
    callback_status = (
        summary_fragment.get("source_callback_intake_status")
        if isinstance(summary_fragment.get("source_callback_intake_status"), dict)
        else summary_fragment.get("callback_intake_status")
        if isinstance(summary_fragment.get("callback_intake_status"), dict)
        else decision.get("source_callback_intake_status")
        if isinstance(decision.get("source_callback_intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or decision.get("safe_copy")
        or decision.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution callback review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": _redact_route_task_rehearsal_text(
                    review_source.get("status")
                    or summary_fragment.get("status")
                    or decision.get("status")
                    or "blocked_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    review_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    review_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance execution callback review decision consumed without explicit reason"
                ),
                "evidence_source": "software_proof",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or decision.get("safe_evidence_ref")
                or decision.get("evidence_ref", "")
            ),
            "source_callback_intake_status": _safe_pc_route_debug_value(callback_status)
            or {
                "status": "missing_source_callback_intake_status",
                "verdict": "not_proven",
                "evidence_source": "software_proof",
            },
            "review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_decision")
                or summary_fragment.get("decision")
                or decision.get("review_decision")
                or decision.get("decision")
                or "needs_callback_review"
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
                if isinstance(summary_fragment.get("decision_reasons"), list)
                else summary_fragment.get("review_reasons")
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "accepted_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_callback_evidence")
                if isinstance(summary_fragment.get("accepted_callback_evidence"), list)
                else summary_fragment.get("accepted_materials_summary")
            ),
            "missing_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_callback_evidence")
                if isinstance(summary_fragment.get("missing_callback_evidence"), list)
                else summary_fragment.get("missing_materials_summary")
            ),
            "rejected_callback_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_callback_evidence")
                if isinstance(summary_fragment.get("rejected_callback_evidence"), list)
                else summary_fragment.get("rejected_materials_summary")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "rerun_commands_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_commands_summary")
                if isinstance(summary_fragment.get("rerun_commands_summary"), list)
                else summary_fragment.get("rerun_commands")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary
        != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback review decision schema or evidence boundary is unsupported",
                    "evidence_source": "software_proof",
                },
                "source_callback_intake_status": {
                    "status": "blocked_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "review_decision": "needs_callback_review",
                "decision_reasons": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_callback_evidence": [],
                "missing_callback_evidence": [],
                "rejected_callback_evidence": [],
                "rerun_guidance": [],
                "rerun_commands_summary": [],
            }
        )
        return summary

    status_text = str(summary["review_status"].get("status") or "")
    callback_text = json.dumps(
        summary["source_callback_intake_status"], ensure_ascii=False, sort_keys=True
    )
    callback_rejected = (
        bool(summary["rejected_callback_evidence"])
        or "rejected" in status_text
        or "rejected" in callback_text
    )
    missing_material = (
        bool(summary["missing_callback_evidence"])
        or "missing" in status_text
        or "missing" in callback_text
    )
    required_fields_present = (
        bool(summary["source_callback_intake_status"]),
        bool(summary["review_decision"]),
        isinstance(summary["decision_reasons"], list),
        isinstance(summary["owner_handoff"], (dict, list, str)),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["accepted_callback_evidence"], list),
        isinstance(summary["missing_callback_evidence"], list),
        isinstance(summary["rejected_callback_evidence"], list),
        isinstance(summary["rerun_guidance"], list),
        bool(summary["safe_copy"]),
    )
    if (
        str(summary_fragment.get("source") or decision.get("source") or "software_proof")
        != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not summary["safe_evidence_ref"]
        or not all(required_fields_present)
        or callback_rejected
        or missing_material
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_reason = "mobile real-device acceptance execution callback review decision contains missing fields, unsafe raw fields, rejected callback material, missing callback material, success claims, or control claims"
        summary.update(
            {
                "review_status": {
                    "status": "unsafe_fields" if not (callback_rejected or missing_material) else "blocked_not_proven",
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "review_decision": (
                    "needs_callback_material_backfill"
                    if missing_material
                    else "needs_callback_review_rerun"
                ),
                "decision_reasons": [blocked_reason],
                "owner_handoff": [],
                "next_required_evidence": [],
                "accepted_callback_evidence": [],
                "rerun_guidance": [],
                "rerun_commands_summary": [],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution callback review decision was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance execution callback review decision was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance execution callback review decision was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance execution callback review decision was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff(
    source,
):
    """构建 real-device acceptance execution callback review handoff 的只读 diagnostics 摘要。"""
    # 该 alias 只能消费已消毒 handoff summary；raw artifact、ACK、cursor、checksum 或控制语义必须 fail closed。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary(
            source_path,
            read_error=(
                "mobile real-device field-trial acceptance execution callback review handoff is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        handoff = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": (
                            "mobile real-device acceptance execution callback review handoff summary missing"
                        ),
                        "evidence_source": "software_proof",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device callback review handoff is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device callback review handoff is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading mobile real-device acceptance execution callback "
                f"review handoff: {exc}"
            )
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device callback review handoff could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device callback review handoff could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device callback review handoff JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device callback review handoff shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device callback review handoff shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        handoff
        if handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {},
        handoff
        if handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {},
        handoff.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        handoff.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("summary"),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and handoff.get("schema")
                == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
            )
        )
        and handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
    ):
        summary_fragment = handoff
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_contract(
                handoff
            )
        )
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary" if not (source_schema or source_boundary) else "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback review handoff lacks a safe summary",
                    "evidence_source": "software_proof",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_contract(
            contract_source
        )
    )
    handoff_source = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else handoff.get("handoff_status")
        if isinstance(handoff.get("handoff_status"), dict)
        else {}
    )
    review_status = (
        summary_fragment.get("source_review_decision_status")
        if isinstance(summary_fragment.get("source_review_decision_status"), dict)
        else summary_fragment.get("source_review_status")
        if isinstance(summary_fragment.get("source_review_status"), dict)
        else handoff.get("source_review_decision_status")
        if isinstance(handoff.get("source_review_decision_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else handoff.get("review_status")
        if isinstance(handoff.get("review_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution callback review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": _redact_route_task_rehearsal_text(
                    handoff_source.get("status")
                    or summary_fragment.get("status")
                    or handoff.get("status")
                    or (
                        "callback_review_handoff_ready_not_proven"
                        if review_status
                        else "blocked_not_proven"
                    )
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    handoff_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    handoff_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance execution callback review handoff consumed without explicit reason"
                ),
                "evidence_source": "software_proof",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or handoff.get("safe_evidence_ref")
                or handoff.get("evidence_ref", "")
            ),
            "source_review_decision_status": _safe_pc_route_debug_value(review_status)
            or {
                "status": "missing_source_review_decision_status",
                "verdict": "not_proven",
                "evidence_source": "software_proof",
            },
            "source_review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision")
                or summary_fragment.get("review_decision")
                or handoff.get("source_review_decision")
                or handoff.get("review_decision")
                or "needs_callback_review"
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "blocker_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocker_summary")
                if isinstance(summary_fragment.get("blocker_summary"), list)
                else summary_fragment.get("blockers")
                if isinstance(summary_fragment.get("blockers"), list)
                else summary_fragment.get("decision_reasons")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": (
                _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    accepted_boundaries = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary not in accepted_boundaries
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution callback review handoff schema or evidence boundary is unsupported",
                    "evidence_source": "software_proof",
                },
                "source_review_decision_status": {
                    "status": "blocked_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "source_review_decision": "needs_callback_review",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
            }
        )
        return summary

    status_text = str(summary["handoff_status"].get("status") or "")
    review_text = json.dumps(
        summary["source_review_decision_status"], ensure_ascii=False, sort_keys=True
    )
    missing_or_blocked_source = (
        "missing" in status_text
        or "unsupported" in status_text
        or "missing" in review_text
        or "unsupported" in review_text
    )
    required_fields_present = (
        bool(summary["source_review_decision_status"]),
        bool(summary["source_review_decision"]),
        isinstance(summary["owner_handoff"], (dict, list, str))
        and bool(summary["owner_handoff"]),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_guidance"], list),
        isinstance(summary["blocker_summary"], list),
        bool(summary["safe_copy"]),
    )
    if (
        str(summary_fragment.get("source") or handoff.get("source") or "software_proof")
        != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not summary["safe_evidence_ref"]
        or not all(required_fields_present)
        or missing_or_blocked_source
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_reason = "mobile real-device acceptance execution callback review handoff contains missing source decision, missing fields, unsafe raw fields, success claims, or control claims"
        summary.update(
            {
                "handoff_status": {
                    "status": "unsafe_fields" if not missing_or_blocked_source else "blocked_not_proven",
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "source_review_decision": "needs_callback_review",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [blocked_reason],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution callback review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance execution callback review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance execution callback review handoff was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance execution callback review handoff was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_handoff_intake(source):
    """构建 real-device acceptance execution handoff intake 的只读 diagnostics 摘要。"""
    # 该 alias 只镜像 owner ack/intake 元数据；不读取 raw artifact、ACK/cursor、checksum 或控制入口。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary(
        source_path,
        read_error=(
            "mobile real-device field-trial acceptance execution handoff intake is not configured"
        ),
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": "mobile real-device acceptance execution handoff intake summary missing",
                        "evidence_source": "software_proof",
                    },
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff intake is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff intake is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance execution handoff intake: {exc}"
            )
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff intake could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff intake could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device handoff intake JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device handoff intake shape is invalid; metadata remains blocked/not_proven.",
                    "safe_phone_copy": "Mobile real-device handoff intake shape is invalid; metadata remains blocked/not_proven.",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        intake
        if intake.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA
        else {},
        intake
        if intake.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {},
        intake.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        intake.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        intake.get("robot_diagnostics_summary"),
        intake.get("mobile_readonly_summary"),
        intake.get("phone_safe_summary"),
        intake.get("summary"),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or (
                not summary_fragment.get("schema")
                and intake.get("schema")
                == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA
            )
        )
        and intake.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA
    ):
        summary_fragment = intake
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_contract(
                intake
            )
        )
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary" if not (source_schema or source_boundary) else "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution handoff intake lacks a safe summary",
                    "evidence_source": "software_proof",
                },
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_contract(
            contract_source
        )
    )
    intake_source = (
        summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else summary_fragment.get("handoff_intake_status")
        if isinstance(summary_fragment.get("handoff_intake_status"), dict)
        else intake.get("intake_status")
        if isinstance(intake.get("intake_status"), dict)
        else {}
    )
    handoff_status = (
        summary_fragment.get("source_handoff_status")
        if isinstance(summary_fragment.get("source_handoff_status"), dict)
        else summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else intake.get("handoff_status")
        if isinstance(intake.get("handoff_status"), dict)
        else {}
    )
    owner_ack_status = (
        summary_fragment.get("owner_ack_status")
        if isinstance(summary_fragment.get("owner_ack_status"), dict)
        else summary_fragment.get("owner_ack")
        if isinstance(summary_fragment.get("owner_ack"), dict)
        else summary_fragment.get("owner_acknowledgement")
        if isinstance(summary_fragment.get("owner_acknowledgement"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution handoff intake is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": _redact_route_task_rehearsal_text(
                    intake_source.get("status")
                    or summary_fragment.get("status")
                    or intake.get("status")
                    or (
                        "ack_received_not_proven"
                        if owner_ack_status
                        else "blocked_missing_owner_ack_not_proven"
                    )
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    intake_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": _redact_route_task_rehearsal_text(
                    intake_source.get("reason")
                    or summary_fragment.get("reason")
                    or "mobile real-device acceptance execution handoff intake consumed without explicit reason"
                ),
                "evidence_source": "software_proof",
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or intake.get("safe_evidence_ref")
                or intake.get("evidence_ref", "")
            ),
            "source_handoff_status": _safe_pc_route_debug_value(handoff_status)
            or {
                "status": "missing_source_handoff_status",
                "verdict": "not_proven",
                "evidence_source": "software_proof",
            },
            "owner_ack_status": _safe_pc_route_debug_value(owner_ack_status)
            or {
                "status": "missing_owner_ack_not_proven",
                "verdict": "not_proven",
                "evidence_source": "software_proof",
            },
            "missing_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_evidence")
                if isinstance(summary_fragment.get("missing_evidence"), list)
                else summary_fragment.get("next_required_evidence")
            ),
            "next_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("next_owner")
                or summary_fragment.get("owner")
                or "full-stack-software-engineer"
            ),
            "owner_handoff": _safe_pc_route_debug_value(summary_fragment.get("owner_handoff")),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "blocker_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocker_summary")
                if isinstance(summary_fragment.get("blocker_summary"), list)
                else summary_fragment.get("blockers")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": (
                _mobile_real_device_field_trial_acceptance_execution_handoff_intake_not_proven(
                    intake,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }
    accepted_boundaries = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
    }
    status_text = json.dumps(
        [summary["intake_status"], summary["source_handoff_status"], summary["owner_ack_status"]],
        ensure_ascii=False,
        sort_keys=True,
    )
    missing_or_blocked_source = (
        "missing" in status_text or "unsupported" in status_text or "blocked" in status_text
    )
    required_fields_present = (
        bool(summary["source_handoff_status"]),
        bool(summary["owner_ack_status"]),
        isinstance(summary["missing_evidence"], list),
        bool(summary["next_owner"]),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_guidance"], list),
        isinstance(summary["blocker_summary"], list),
        bool(summary["safe_copy"]),
    )
    if (
        source_schema not in accepted_schemas
        or source_boundary not in accepted_boundaries
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution handoff intake schema or evidence boundary is unsupported",
                    "evidence_source": "software_proof",
                },
                "source_handoff_status": {
                    "status": "blocked_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "owner_ack_status": {
                    "status": "missing_owner_ack_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "missing_evidence": [],
                "next_owner": "",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
            }
        )
        return summary
    if (
        str(summary_fragment.get("source") or intake.get("source") or "software_proof")
        != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not summary["safe_evidence_ref"]
        or not all(required_fields_present)
        or missing_or_blocked_source
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    ):
        blocked_reason = "mobile real-device acceptance execution handoff intake contains missing source handoff, missing owner ack, unsafe raw fields, success claims, or control claims"
        summary.update(
            {
                "intake_status": {
                    "status": "unsafe_fields" if not missing_or_blocked_source else "blocked_missing_owner_ack_not_proven",
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "owner_ack_status": {
                    "status": "missing_owner_ack_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "missing_evidence": [],
                "next_owner": "",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [blocked_reason],
                "robot_diagnostics_summary": {
                    "safe_copy": "Mobile real-device acceptance execution handoff intake was blocked because fields could expose raw/control data or imply delivery success.",
                    "safe_phone_copy": "Mobile real-device acceptance execution handoff intake was blocked because fields could expose raw/control data or imply delivery success.",
                },
                "safe_copy": "Mobile real-device acceptance execution handoff intake was blocked because fields could expose raw/control data or imply delivery success.",
                "safe_phone_copy": "Mobile real-device acceptance execution handoff intake was blocked because fields could expose raw/control data or imply delivery success.",
            }
        )
        return summary

    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision(
    source,
):
    """构建 real-device acceptance execution handoff review decision 的只读 diagnostics 摘要。"""
    # 该 alias 只消费上一轮已消毒 intake summary；raw artifact、ACK、cursor、checksum 和控制字段必须阻断。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary(
            source_path,
            read_error=(
                "mobile real-device field-trial acceptance execution handoff review decision is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing_summary",
                        "verdict": "not_proven",
                        "reason": (
                            "mobile real-device acceptance execution handoff review decision source summary missing"
                        ),
                        "evidence_source": "software_proof",
                    },
                    "blocked_reason": "missing source handoff intake summary",
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff review decision source is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff review decision source is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance execution handoff review decision: {exc}"
            )
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "blocked_reason": safe_error,
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff review decision source could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff review decision source could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device handoff review decision JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "blocked_reason": "invalid JSON shape",
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        decision
        if decision.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA
        else {},
        decision
        if decision.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA
        else {},
        decision.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        decision.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        decision.get("mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"),
        decision.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        decision.get("robot_diagnostics_summary"),
        decision.get("mobile_readonly_summary"),
        decision.get("phone_safe_summary"),
        decision.get("summary"),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        diagnostics.get("mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or not summary_fragment.get("schema")
        )
        and decision.get("schema")
        in {
            MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA,
            MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA,
        }
    ):
        summary_fragment = decision
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_contract(
                decision
            )
        )
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary" if not (source_schema or source_boundary) else "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution handoff review decision lacks a safe source summary",
                    "evidence_source": "software_proof",
                },
                "blocked_reason": "missing safe source summary",
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_contract(
            contract_source
        )
    )
    review_source = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else decision.get("review_status")
        if isinstance(decision.get("review_status"), dict)
        else {}
    )
    intake_status = (
        summary_fragment.get("source_handoff_intake_status")
        if isinstance(summary_fragment.get("source_handoff_intake_status"), dict)
        else summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else decision.get("intake_status")
        if isinstance(decision.get("intake_status"), dict)
        else {}
    )
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or decision.get("safe_copy")
        or decision.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution handoff review decision is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    accepted_material_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("accepted_material_summary")
        if isinstance(summary_fragment.get("accepted_material_summary"), list)
        else summary_fragment.get("accepted_materials_summary")
        if isinstance(summary_fragment.get("accepted_materials_summary"), list)
        else summary_fragment.get("owner_handoff")
    )
    missing_material_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_material_summary")
        if isinstance(summary_fragment.get("missing_material_summary"), list)
        else summary_fragment.get("missing_evidence")
        if isinstance(summary_fragment.get("missing_evidence"), list)
        else summary_fragment.get("next_required_evidence")
    )
    rejected_material_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("rejected_material_summary")
        if isinstance(summary_fragment.get("rejected_material_summary"), list)
        else summary_fragment.get("rejected_materials_summary")
    )
    status_text = json.dumps([review_source, intake_status], ensure_ascii=False, sort_keys=True)
    requested_decision = str(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision.get("review_decision")
        or ""
    ).strip()
    if requested_decision not in {"accepted", "missing", "rejected", "blocked"}:
        if rejected_material_summary or "rejected" in status_text:
            requested_decision = "rejected"
        elif missing_material_summary or "missing" in status_text:
            requested_decision = "missing"
        elif "blocked" in status_text or "unsupported" in status_text:
            requested_decision = "blocked"
        else:
            requested_decision = "accepted"
    blocked_reason = _redact_route_task_rehearsal_text(
        summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or review_source.get("reason")
        or (
            "source handoff intake has rejected material"
            if requested_decision == "rejected"
            else "source handoff intake has missing material"
            if requested_decision == "missing"
            else "source handoff intake remains blocked/not_proven"
            if requested_decision == "blocked"
            else ""
        )
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": _redact_route_task_rehearsal_text(
                    review_source.get("status")
                    or summary_fragment.get("status")
                    or decision.get("status")
                    or f"{requested_decision}_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    review_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": blocked_reason
                or "mobile real-device acceptance execution handoff intake accepted as metadata only",
                "evidence_source": "software_proof",
            },
            "source_handoff_intake_status": _safe_pc_route_debug_value(intake_status)
            or {
                "status": "missing_source_handoff_intake_status",
                "verdict": "not_proven",
                "evidence_source": "software_proof",
            },
            "review_decision": requested_decision,
            "accepted_material_summary": accepted_material_summary,
            "missing_material_summary": missing_material_summary,
            "rejected_material_summary": rejected_material_summary,
            "blocked_reason": blocked_reason,
            "next_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("next_owner")
                or summary_fragment.get("owner")
                or "product-okr-owner"
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or decision.get("safe_evidence_ref")
                or decision.get("evidence_ref", "")
            ),
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "not_proven": (
                _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA,
    }
    accepted_boundaries = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
    }
    required_fields_present = (
        bool(summary["source_handoff_intake_status"]),
        summary["review_decision"] in {"accepted", "missing", "rejected", "blocked"},
        isinstance(summary["accepted_material_summary"], list),
        isinstance(summary["missing_material_summary"], list),
        isinstance(summary["rejected_material_summary"], list),
        bool(summary["next_owner"]),
        isinstance(summary["rerun_guidance"], list),
        bool(summary["safe_copy"]),
        bool(summary["safe_evidence_ref"]),
    )
    unsafe_source = (
        source_schema not in accepted_schemas
        or source_boundary not in accepted_boundaries
        or str(summary_fragment.get("source") or decision.get("source") or "software_proof")
        != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or not all(required_fields_present)
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
    )
    if unsafe_source:
        blocked_reason = "source handoff intake summary is missing, schema-mismatched, unsafe, or contains control/success claims"
        summary.update(
            {
                "review_status": {
                    "status": (
                        "unsupported_schema"
                        if source_schema not in accepted_schemas
                        or source_boundary not in accepted_boundaries
                        else "unsafe_fields"
                    ),
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "source_handoff_intake_status": {
                    "status": "blocked_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": "software_proof",
                },
                "review_decision": "rejected" if _mobile_field_material_intake_has_unsafe_fields(summary_fragment) else "blocked",
                "accepted_material_summary": [],
                "missing_material_summary": [],
                "rejected_material_summary": [blocked_reason],
                "blocked_reason": blocked_reason,
                "next_owner": "full-stack-software-engineer",
                "rerun_guidance": ["rerun safe handoff intake with sanitized summary only"],
                "robot_diagnostics_summary": {
                    "safe_copy": (
                        "Mobile real-device acceptance execution handoff review decision was blocked; "
                        "source=software_proof; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false; not_proven."
                    ),
                    "safe_phone_copy": (
                        "Mobile real-device acceptance execution handoff review decision was blocked; "
                        "source=software_proof; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false; not_proven."
                    ),
                },
                "safe_copy": (
                    "Mobile real-device acceptance execution handoff review decision was blocked; "
                    "source=software_proof; safe_to_control=false; delivery_success=false; "
                    "primary_actions_enabled=false; not_proven."
                ),
                "safe_phone_copy": (
                    "Mobile real-device acceptance execution handoff review decision was blocked; "
                    "source=software_proof; safe_to_control=false; delivery_success=false; "
                    "primary_actions_enabled=false; not_proven."
                ),
            }
        )
    return summary


def summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff(
    source,
):
    """构建 real-device acceptance execution handoff review handoff 的只读 diagnostics 摘要。"""
    # 该 alias 只消费上一轮 review decision 的安全摘要；raw artifact、ACK、checksum、cursor 和控制字段必须阻断。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary(
            source_path,
            read_error=(
                "mobile real-device field-trial acceptance execution handoff review handoff is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        handoff = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing_source_decision",
                        "verdict": "not_proven",
                        "reason": (
                            "mobile real-device acceptance execution handoff review handoff source decision missing"
                        ),
                        "evidence_source": "software_proof",
                    },
                    "blocked_summary": ["missing source handoff review decision summary"],
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff review handoff source decision is missing; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff review handoff source decision is missing; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading mobile real-device acceptance execution handoff review handoff: {exc}"
            )
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": safe_error,
                        "evidence_source": "software_proof",
                    },
                    "handoff_reason": safe_error,
                    "blocked_summary": [safe_error],
                    "read_error": safe_error,
                    "robot_diagnostics_summary": {
                        "safe_copy": "Mobile real-device handoff review handoff source could not be read; metadata remains blocked/not_proven.",
                        "safe_phone_copy": "Mobile real-device handoff review handoff source could not be read; metadata remains blocked/not_proven.",
                    },
                }
            )
            return summary

    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "mobile real-device handoff review handoff JSON must be an object",
                    "evidence_source": "software_proof",
                },
                "handoff_reason": "invalid JSON shape",
                "blocked_summary": ["invalid JSON shape"],
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    summary_fragment = {}
    for candidate in (
        handoff
        if handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {},
        handoff
        if handoff.get("schema")
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA
        else {},
        handoff.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"
        ),
        handoff.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"
        ),
        handoff.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        handoff.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        handoff.get("robot_diagnostics_summary"),
        handoff.get("mobile_readonly_summary"),
        handoff.get("phone_safe_summary"),
        handoff.get("summary"),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary"
        ),
        diagnostics.get(
            "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        diagnostics.get(
            "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary"
        ),
        diagnostics.get("summary"),
        diagnostics.get("diagnostics_summary"),
    ):
        if isinstance(candidate, dict) and candidate:
            summary_fragment = candidate
            break
    if (
        (
            not summary_fragment
            or not summary_fragment.get("schema")
        )
        and handoff.get("schema")
        in {
            MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA,
            MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA,
        }
    ):
        summary_fragment = handoff
    if not summary_fragment:
        source_schema, source_boundary = (
            _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_contract(
                handoff
            )
        )
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_source_decision" if not (source_schema or source_boundary) else "unsupported_schema",
                    "verdict": "not_proven",
                    "reason": "mobile real-device acceptance execution handoff review handoff lacks a safe source decision summary",
                    "evidence_source": "software_proof",
                },
                "blocked_summary": ["missing safe source decision summary"],
            }
        )
        return summary

    contract_source = summary_fragment
    source_schema, source_boundary = (
        _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_contract(
            contract_source
        )
    )
    if (
        source_schema
        == MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA
        and summary_fragment.get("source_schema")
    ):
        source_schema = str(summary_fragment.get("source_schema") or "")
        source_boundary = str(summary_fragment.get("source_evidence_boundary") or source_boundary)
    status_source = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    current_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("current_decision")
        or summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or handoff.get("current_decision")
        or handoff.get("review_decision")
        or "blocked"
    )
    if current_decision not in {"accepted", "missing", "rejected", "blocked"}:
        current_decision = "blocked"
    safe_copy = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or (
            "Mobile real-device acceptance execution handoff review handoff is metadata-only; "
            "source=software_proof; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    )
    if "source=software_proof" not in safe_copy:
        safe_copy = f"{safe_copy}; source=software_proof."
    if "safe_to_control=false" not in safe_copy:
        safe_copy = (
            f"{safe_copy}; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; not_proven."
        )
    robot_summary = {}
    for key in ("summary", "safe_copy", "safe_phone_copy"):
        if str(summary_fragment.get(key) or "").strip():
            robot_summary[key] = _redact_route_task_rehearsal_text(summary_fragment.get(key))
    robot_summary["safe_copy"] = safe_copy
    robot_summary["safe_phone_copy"] = safe_copy
    accepted_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("accepted_summary")
        if isinstance(summary_fragment.get("accepted_summary"), list)
        else summary_fragment.get("accepted_material_summary")
    )
    missing_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_summary")
        if isinstance(summary_fragment.get("missing_summary"), list)
        else summary_fragment.get("missing_material_summary")
    )
    rejected_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("rejected_summary")
        if isinstance(summary_fragment.get("rejected_summary"), list)
        else summary_fragment.get("rejected_material_summary")
    )
    blocked_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("blocked_summary")
        if isinstance(summary_fragment.get("blocked_summary"), list)
        else [summary_fragment.get("blocked_reason")]
        if summary_fragment.get("blocked_reason")
        else []
    )
    handoff_owner = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_owner")
        or summary_fragment.get("next_owner")
        or summary_fragment.get("owner")
        or "product-okr-owner"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_reason")
        or summary_fragment.get("reason")
        or status_source.get("reason")
        or (
            "accepted decision requires field owner handoff package"
            if current_decision == "accepted"
            else "missing decision requires evidence owner follow-up"
            if current_decision == "missing"
            else "rejected decision requires owner correction before rerun"
            if current_decision == "rejected"
            else "blocked decision requires source evidence repair"
        )
    )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status")
                    or summary_fragment.get("status")
                    or f"{current_decision}_handoff_not_proven"
                ),
                "verdict": _redact_route_task_rehearsal_text(
                    status_source.get("verdict")
                    or summary_fragment.get("verdict")
                    or "not_proven"
                ),
                "reason": handoff_reason,
                "evidence_source": "software_proof",
            },
            "current_decision": current_decision,
            "handoff_owner": handoff_owner,
            "handoff_reason": handoff_reason,
            "accepted_summary": accepted_summary,
            "missing_summary": missing_summary,
            "rejected_summary": rejected_summary,
            "blocked_summary": blocked_summary,
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if isinstance(summary_fragment.get("rerun_guidance"), list)
                else summary_fragment.get("rerun_commands_summary")
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "robot_diagnostics_summary": robot_summary,
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "source": "software_proof",
            "software_proof": True,
            "not_proven": (
                _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "read_error": "",
            "metadata_only": True,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    accepted_schemas = {
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA,
        MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    required_fields_present = (
        summary["current_decision"] in {"accepted", "missing", "rejected", "blocked"},
        bool(summary["handoff_owner"]),
        bool(summary["handoff_reason"]),
        isinstance(summary["accepted_summary"], list),
        isinstance(summary["missing_summary"], list),
        isinstance(summary["rejected_summary"], list),
        isinstance(summary["blocked_summary"], list),
        isinstance(summary["next_required_evidence"], list),
        isinstance(summary["rerun_guidance"], list),
        bool(summary["safe_copy"]),
        bool(summary["safe_evidence_ref"]),
        summary["same_evidence_ref_required"] is True,
    )
    unsafe_source = (
        source_schema not in accepted_schemas
        or source_boundary
        != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE
        or str(summary_fragment.get("source") or handoff.get("source") or "software_proof")
        != "software_proof"
        or summary_fragment.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is True
        or summary_fragment.get("primary_actions_enabled") is True
        or source_ref and summary_ref and source_ref != summary_ref
        or not all(required_fields_present)
        or _mobile_field_material_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
        or _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy(
            summary_fragment
        )
        or _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy(
            safe_copy
        )
    )
    if unsafe_source:
        blocked_reason = "source handoff review decision summary is missing, schema-mismatched, unsafe, or contains control/success claims"
        summary.update(
            {
                "handoff_status": {
                    "status": (
                        "unsupported_schema"
                        if source_schema not in accepted_schemas
                        or source_boundary
                        != MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE
                        else "unsafe_fields"
                    ),
                    "verdict": "not_proven",
                    "reason": blocked_reason,
                    "evidence_source": "software_proof",
                },
                "current_decision": "blocked",
                "handoff_owner": "product-okr-owner",
                "handoff_reason": blocked_reason,
                "accepted_summary": [],
                "missing_summary": [],
                "rejected_summary": [],
                "blocked_summary": [blocked_reason],
                "next_required_evidence": ["rerun sanitized handoff review decision summary"],
                "rerun_guidance": ["rerun safe handoff review handoff with sanitized source decision only"],
                "robot_diagnostics_summary": {
                    "safe_copy": (
                        "Mobile real-device acceptance execution handoff review handoff was blocked; "
                        "source=software_proof; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false; not_proven."
                    ),
                    "safe_phone_copy": (
                        "Mobile real-device acceptance execution handoff review handoff was blocked; "
                        "source=software_proof; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false; not_proven."
                    ),
                },
                "safe_copy": (
                    "Mobile real-device acceptance execution handoff review handoff was blocked; "
                    "source=software_proof; safe_to_control=false; delivery_success=false; "
                    "primary_actions_enabled=false; not_proven."
                ),
                "safe_phone_copy": (
                    "Mobile real-device acceptance execution handoff review handoff was blocked; "
                    "source=software_proof; safe_to_control=false; delivery_success=false; "
                    "primary_actions_enabled=false; not_proven."
                ),
            }
        )
    return summary
