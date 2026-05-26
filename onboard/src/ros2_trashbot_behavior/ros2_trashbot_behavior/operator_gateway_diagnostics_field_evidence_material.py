"""Field evidence material diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 field evidence real-material、
material blocker 与 material resolution 只读摘要逻辑。这里的摘要只证明
software_proof 元数据可读，不能升级为真实现场通过、HIL、Nav2 runtime、
WAVE ROVER 运动证明或 delivery success。
"""

import json
import os

EVIDENCE_SOURCE_SOFTWARE = "software_proof"


def _diagnostics():
    # 延迟读取 facade helper，避免兼容层导入本模块时形成初始化环。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _facade_helper(name, *args, **kwargs):
    # 目标域先拆出自身逻辑，通用安全清洗 helper 暂由 facade 统一提供。
    return getattr(_diagnostics(), name)(*args, **kwargs)


def _real_material_evidence_ref_is_unsafe(value):
    # evidence_ref 安全规则必须沿用 facade 现有实现，避免拆分时扩大可接受字符集。
    return _facade_helper("_real_material_evidence_ref_is_unsafe", value)


def _redact_route_task_rehearsal_text(value):
    # 复用已有脱敏规则，保证 safe copy 与旧 facade 输出逐字兼容。
    return _facade_helper("_redact_route_task_rehearsal_text", value)


def _route_task_field_retest_execution_pack_has_success_wording(value):
    # 成功/通过措辞仍由共享守卫判定，避免 metadata-only 摘要误报真实闭环。
    return _facade_helper("_route_task_field_retest_execution_pack_has_success_wording", value)


def _route_task_field_run_readiness_has_unsafe_fields(value, key_path=""):
    # readiness unsafe 规则属于跨域控制守卫，拆分后继续委托同一实现。
    return _facade_helper("_route_task_field_run_readiness_has_unsafe_fields", value, key_path)


def _safe_pc_route_debug_dict(value):
    # PC debug 字段只能保留短安全摘要，不能泄露本地路径或原始材料。
    return _facade_helper("_safe_pc_route_debug_dict", value)


def _safe_pc_route_debug_value(value, depth=0):
    # 与旧实现保持递归深度限制，避免嵌套原始 payload 透传。
    return _facade_helper("_safe_pc_route_debug_value", value, depth)


def _safe_route_task_rehearsal_list(value, limit=8):
    # 列表裁剪规则保持不变，避免 diagnostics payload 体积和字段语义漂移。
    return _facade_helper("_safe_route_task_rehearsal_list", value, limit)


def _safe_route_task_rehearsal_ref(value):
    # 引用清洗保持兼容，旧调用方依赖空字符串 fail-closed 语义。
    return _facade_helper("_safe_route_task_rehearsal_ref", value)


def _task_terminal_field_material_intake_copy_is_unsafe(value):
    # field material safe copy 的危险措辞仍走共享判定，保证跨入口一致。
    return _facade_helper("_task_terminal_field_material_intake_copy_is_unsafe", value)

FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SCHEMA = (
    "trashbot.field_evidence_real_material_request_dispatch.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_request_dispatch_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE = (
    "software_proof_docker_field_evidence_real_material_request_dispatch_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS = (
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

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SCHEMA = (
    "trashbot.field_evidence_real_material_response_intake.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_response_intake_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE = (
    "software_proof_docker_field_evidence_real_material_response_intake_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_STATUSES = (
    "accepted",
    "missing",
    "rejected",
    "blocked",
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_real_material_response_review_decision.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_response_review_decision_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_real_material_response_review_decision_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_VALUES = (
    "accepted_for_later_review_not_proven",
    "needs_material_backfill_not_proven",
    "rejected_unsafe_or_mixed_response_not_proven",
    "blocked_real_environment_unavailable_not_proven",
    "blocked_missing_field_evidence_real_material_response_intake_not_proven",
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_real_material_response_review_handoff.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_response_review_handoff_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_real_material_response_review_handoff_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.field_evidence_real_material_followup_escalation_status.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_field_evidence_real_material_followup_escalation_status_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA = (
    "trashbot.field_evidence_real_material_owner_ack_intake.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_owner_ack_intake_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE = (
    "software_proof_docker_field_evidence_real_material_owner_ack_intake_gate"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_real_material_owner_ack_review_decision.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_real_material_owner_ack_review_decision_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary.v1"
)

FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate"
)

FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA = (
    "trashbot.field_evidence_material_blocker_escalation_pack.v1"
)

FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_blocker_escalation_pack_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE = (
    "software_proof_docker_field_evidence_material_blocker_escalation_pack_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SCHEMA = (
    "trashbot.field_evidence_material_resolution_intake.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE = (
    "software_proof_docker_field_evidence_material_resolution_intake_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_DECISIONS = (
    "accepted",
    "missing",
    "rejected",
    "blocked",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_material_resolution_review_decision.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_material_resolution_review_decision_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_DECISIONS = (
    "accepted_for_owner_review_not_proven",
    "needs_more_evidence_not_proven",
    "rejected_unsafe_resolution_not_proven",
    "blocked_missing_resolution_intake_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_material_resolution_review_handoff.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_material_resolution_review_handoff_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_STATUSES = (
    "ready_for_owner_handoff_not_proven",
    "needs_more_evidence_not_proven",
    "blocked_missing_review_decision_not_proven",
    "blocked_unsafe_handoff_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.field_evidence_material_resolution_followup_escalation_status.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUSES = (
    "pending_owner_response_not_proven",
    "overdue_owner_response_not_proven",
    "escalated_for_owner_action_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_intake.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE = (
    "software_proof_docker_field_evidence_material_resolution_owner_response_intake_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_REVIEWER_ACK_BRIDGE = (
    "field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_STATUSES = (
    "accepted",
    "missing",
    "rejected",
    "blocked",
    "accepted_not_proven",
    "missing_not_proven",
    "rejected_not_proven",
    "blocked_not_proven",
    "accepted_for_owner_response_intake_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_review_decision.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISIONS = (
    "accepted_for_material_review_not_proven",
    "needs_more_evidence_not_proven",
    "rejected_unsafe_material_response_not_proven",
    "blocked_missing_owner_response_intake_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_review_handoff.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_owner_response_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES = (
    "accepted_for_resolution_owner_handoff_not_proven",
    "needs_more_evidence_not_proven",
    "rejected_unsafe_owner_response_review_handoff_not_proven",
    "blocked_missing_owner_response_review_handoff_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE = (
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_STATUSES = (
    "accepted_not_proven",
    "missing_not_proven",
    "rejected_not_proven",
    "blocked_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_review_decision.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISIONS = (
    "accepted_for_material_review_not_proven",
    "needs_reassignment_not_proven",
    "needs_field_owner_supplement_not_proven",
    "rejected_unsafe_ack_not_proven",
    "blocked_missing_reviewer_ack_intake_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES = (
    "accepted_for_material_review_handoff_not_proven",
    "needs_reassignment_not_proven",
    "needs_field_owner_supplement_not_proven",
    "rejected_unsafe_ack_review_handoff_not_proven",
    "blocked_missing_reviewer_ack_review_decision_not_proven",
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate"
)

FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUSES = (
    "owner_response_pending_not_proven",
    "owner_response_overdue_escalate_not_proven",
    "blocked_missing_required_materials_not_proven",
    "blocked_unsafe_material_claims_not_proven",
    "accepted_for_owner_response_intake_not_proven",
    "blocked_missing_reviewer_ack_handoff_not_proven",
)

def _field_evidence_real_material_request_dispatch_not_proven(
    request=None,
    summary_fragment=None,
):
    # request dispatch 只派发真实材料清单；不能把派发状态当成现场复跑、手机或交付证据。
    source_values = []
    for item in (request, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_real_material_request_dispatch_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "hardware_transport_control",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _field_evidence_real_material_response_intake_not_proven(
    response=None,
    summary_fragment=None,
):
    # response intake 只分类现场 owner 回填状态，accepted 也不能升级成真实现场通过。
    source_values = []
    for item in (response, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_real_material_response_intake_only",
        "accepted_materials_ready_for_later_review_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "hardware_transport_control",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _field_evidence_real_material_response_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只说明材料是否可进入后续人工复核；accepted 仍不是现场通过或交付成功。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_real_material_response_review_decision_only",
        "accepted_for_later_review_not_delivery_success",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "hardware_transport_control",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _field_evidence_real_material_response_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只把复核后续责任交给现场 owner；Robot 不能把它解释为现场通过。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_real_material_response_review_handoff_only",
        "review_handoff_not_delivery_success",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "hil_pass_not_verified",
        "hardware_transport_not_verified",
        "o5_external_proof_not_verified",
        "pr5_review_thread_not_resolved",
        "safe_to_control_false",
        "primary_actions_enabled_false",
        "delivery_success_false",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _field_evidence_real_material_followup_escalation_status_not_proven(
    status=None,
    summary_fragment=None,
):
    # field-evidence follow-up 只汇总现场材料升级状态；不证明复跑、送达或硬件闭环。
    status = status if isinstance(status, dict) else {}
    summary_fragment = summary_fragment if isinstance(summary_fragment, dict) else {}
    source_values = []
    for item in (status, summary_fragment):
        if isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
        for group in item.get("material_groups", []):
            if not isinstance(group, dict):
                continue
            if str(group.get("blocked_reason") or "").strip():
                source_values.append(group.get("blocked_reason"))
            if isinstance(group.get("next_required_evidence"), list):
                source_values.extend(group.get("next_required_evidence"))
    required = (
        "field_evidence_real_material_followup_escalation_status_only",
        "field_owner_followup_not_review_resolution",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "pr5_review_thread_not_resolved",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "hardware_transport_control",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values

def _default_field_evidence_real_material_request_dispatch_summary(
    path,
    request_status="blocked_missing_field_evidence_real_material_request_dispatch",
    read_error="",
):
    # 缺源时也返回完整材料模板和 false flags，避免 diagnostics 缺项被误读成现场材料已到位。
    safe_copy = (
        "Field evidence real material request dispatch is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material request dispatch is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "request_status": {
            "status": request_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "request_verdict": "blocked",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "required_materials": list(
            FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS
        ),
        "owner_mapping": {},
        "next_required_evidence": [],
        "blocked_claims": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE,
        "not_proven": _field_evidence_real_material_request_dispatch_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_real_material_response_intake_summary(
    path,
    response_status="blocked_missing_field_evidence_real_material_response_intake",
    read_error="",
):
    # 缺省态必须带齐四类材料桶和 false flags，避免 diagnostics 把缺回执误读成通过。
    safe_copy = (
        "Field evidence real material response intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material response intake is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "response_status": {
            "status": response_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "response_verdict": "blocked",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "required_materials": list(
            FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS
        ),
        "accepted_materials": [],
        "missing_materials": list(
            FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS
        ),
        "rejected_materials": [],
        "blocked_materials": [],
        "material_statuses": {
            "accepted": [],
            "missing": list(
                FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS
            ),
            "rejected": [],
            "blocked": [],
        },
        "next_required_evidence": [],
        "blocked_claims": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE,
        "not_proven": _field_evidence_real_material_response_intake_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_real_material_response_review_decision_summary(
    path,
    review_status="blocked_missing_field_evidence_real_material_response_review_decision",
    read_error="",
):
    # 缺省态必须 fail closed；Robot diagnostics 不能把缺复核材料解释成可控或已送达。
    safe_copy = (
        "Field evidence real material response review decision is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material response review decision is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_response_intake_schema": "",
        "source_response_intake_status": "blocked",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "review_decision": (
            "blocked_missing_field_evidence_real_material_response_intake_not_proven"
        ),
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "accepted_materials": [],
        "missing_materials": list(
            FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS
        ),
        "rejected_materials": [],
        "blocked_materials": [],
        "decision_reasons": [reason],
        "owner_handoff": [],
        "next_required_evidence": [],
        "blocked_claims": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_real_material_response_review_decision_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_real_material_response_review_handoff_summary(
    path,
    handoff_status="blocked_missing_field_evidence_real_material_response_review_handoff",
    read_error="",
):
    # 缺省态保留 handoff gate 的软件证明边界，不把缺材料变成可控任务状态。
    safe_copy = (
        "Field evidence real material response review handoff is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material response review handoff is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_review_decision": "",
        "source_review_decision_status": "blocked",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "handoff_decision": "blocked_missing_real_material_response_review_handoff_not_proven",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "owner_handoff": [],
        "next_required_evidence": [],
        "blocker_summary": "",
        "rerun_guidance": [],
        "reconciliation_guidance": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE,
        "not_proven": _field_evidence_real_material_response_review_handoff_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_real_material_followup_escalation_status_summary(
    path,
    status="blocked_missing_field_evidence_real_material_followup_escalation_status",
    read_error="",
):
    # 缺省态必须完整返回 false flags，避免前端或 diagnostics 把缺 follow-up 材料解释成可控。
    safe_copy = (
        "Field evidence real material follow-up escalation status is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material follow-up escalation status is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "followup_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "material_group": "",
        "field_owner": "",
        "due_status": "",
        "blocked_reason": "",
        "next_required_evidence": [],
        "escalation_level": "",
        "rerun_status_summary": {},
        "source_review_handoff_status": "",
        "owner_handoff": [],
        "material_groups": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "not_proven": (
            _field_evidence_real_material_followup_escalation_status_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _field_evidence_real_material_owner_ack_intake_not_proven(
    ack=None,
    summary_fragment=None,
):
    # owner ack 只说明现场 owner 已读/待补材料；Robot 不能据此认定现场复跑或控制闭环。
    source_values = []
    for item in (ack, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_real_material_owner_ack_intake_only",
        "field_owner_ack_not_review_resolution",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_hardware_runtime_not_verified",
        "pr5_review_thread_not_resolved",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "hardware_transport_control",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        # HIL/pass/raw/checksum/path 等词不能进入 Robot diagnostics；它们只作为阻断原因处理。
        lowered = safe_item.lower()
        if any(marker in lowered for marker in ("hil", " pass", "checksum", "raw", "artifact", "[redacted")):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_real_material_owner_ack_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # owner ack review 只代表安全摘要被复核，不能升级成 PR 关闭、现场复跑或真实送达结论。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("decision_reasons"), list):
            source_values.extend(item.get("decision_reasons"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_real_material_owner_ack_review_decision_only",
        "field_owner_ack_not_pr5_resolution",
        "source_owner_ack_status_not_real_material",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        # Robot diagnostics 不展示 HIL/pass/raw/path/checksum 细节，只保留软件证明缺口。
        lowered = safe_item.lower()
        if any(marker in lowered for marker in ("hil", " pass", "raw", "path", "checksum", "[redacted")):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_blocker_escalation_pack_not_proven(
    pack=None,
    summary_fragment=None,
):
    # escalation pack 只把阻塞升级为人工决策材料，不代表现场材料、控制授权或送达成功。
    source_values = []
    for item in (pack, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_blocker_escalation_pack_only",
        "real_field_materials_not_supplied",
        "route_elevator_field_pass_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "pr5_review_thread_not_resolved",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw/path/checksum/HIL 等只作为阻断线索，不进入 Robot safe alias 的可见 not_proven 列表。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # resolution intake 只表示 owner 给出安全摘要，不能变成现场通过、云证明或控制许可。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_intake_only",
        "owner_resolution_not_delivery_success",
        "route_elevator_field_pass_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "pr5_review_thread_not_resolved",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw/path/checksum/HIL/pass/control 词只作为阻断条件，不能进入可见安全摘要。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只是 owner-review 队列入口，必须显式排除交付、控制、HIL 和真实外部证明。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_review_decision_only",
        "owner_review_not_delivery_success",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "pr5_review_thread_not_resolved",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw/path/checksum/HIL/pass/control 细节只用于阻断，不能进入 Robot-safe not_proven 列表。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只交接 owner 下一步，不把 handoff_status 提升为 readiness 或成功态。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_real_evidence"), list):
            source_values.extend(item.get("next_required_real_evidence"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_review_handoff_only",
        "handoff_status_not_readiness",
        "owner_handoff_not_delivery_success",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "pr5_review_thread_not_resolved",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # 控制、raw、路径、checksum 和 HIL 词只用于阻断，不能进入 Robot-safe 可见列表。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_followup_escalation_status_not_proven(
    followup=None,
    summary_fragment=None,
):
    # follow-up escalation 只说明 owner response 缺口状态，不能证明 reviewer resolved 或材料齐备。
    source_values = []
    for item in (followup, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_followup_escalation_status_only",
        "owner_response_material_missing_or_pending",
        "followup_status_not_readiness",
        "escalation_status_not_control_authorization",
        "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
        "comment_3269642220_not_reviewer_resolution",
        "hardware_material_pending",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw/path/checksum/HIL pass 线索只用于阻断，不能进入可见 not_proven 字段。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_owner_response_intake_not_proven(
    response=None,
    summary_fragment=None,
):
    # owner response intake 只证明“收到安全摘要”，不能证明材料验收、复核通过或机器人可控。
    source_values = []
    for item in (response, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_owner_response_intake_only",
        "owner_response_intake_not_review_acceptance",
        "owner_response_intake_not_readiness",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制词只用于阻断，不能暴露到 phone-safe not_proven。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_owner_response_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review-decision 只把 owner response 分桶成后续复核状态，不能提升成真实验收或控制许可。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_owner_response_review_decision_only",
        "owner_response_review_decision_not_readiness",
        "owner_response_review_decision_not_command_authorization",
        "owner_response_review_decision_not_owner_material_real_acceptance",
        "owner_response_review_decision_not_pr_reviewer_resolution",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制细节只用于阻断，不进入 Robot-safe 可见列表。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_owner_response_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # review-handoff 只是把已消毒的 review decision 交给后续 owner 处理，不能变成控制或交付成功。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_owner_response_review_handoff_only",
        "owner_response_review_handoff_not_readiness",
        "owner_response_review_handoff_not_command_authorization",
        "owner_response_review_handoff_not_owner_material_real_acceptance",
        "owner_response_review_handoff_not_pr_reviewer_resolution",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制细节只用于阻断，不进入 Robot-safe 可见列表。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_reviewer_ack_intake_not_proven(
    ack=None,
    summary_fragment=None,
):
    # reviewer ACK intake 只证明“安全 ACK 摘要已进入诊断面”，不能证明 reviewer resolved 或真实材料闭环。
    source_values = []
    for item in (ack, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_reviewer_ack_intake_only",
        "reviewer_ack_intake_not_reviewer_resolution",
        "reviewer_ack_intake_not_command_authorization",
        "reviewer_ack_intake_not_owner_material_real_acceptance",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制细节只用于阻断，不进入 Robot-safe 可见列表。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_reviewer_ack_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # reviewer ACK review-decision 只分类 ACK 后续处理，不能变成 reviewer resolved 或控制许可。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_reviewer_ack_review_decision_only",
        "reviewer_ack_review_decision_not_reviewer_resolution",
        "reviewer_ack_review_decision_not_command_authorization",
        "reviewer_ack_review_decision_not_owner_material_real_acceptance",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制细节只用于阻断，不进入 phone-safe 输出。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_reviewer_ack_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # reviewer ACK review-handoff 只是复核后的交接面，不能变成 reviewer resolved 或控制许可。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_reviewer_ack_review_handoff_only",
        "reviewer_ack_review_handoff_not_reviewer_resolution",
        "reviewer_ack_review_handoff_not_command_authorization",
        "reviewer_ack_review_handoff_not_owner_material_real_acceptance",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # raw、路径、checksum、HIL/pass 和控制细节只用于阻断，不进入 phone-safe 输出。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_not_proven(
    followup=None,
    summary_fragment=None,
):
    # followup escalation status 只是追办状态，不得被解释成 owner 已验收或 Robot 可控。
    source_values = []
    for item in (followup, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_only",
        "reviewer_ack_followup_status_not_reviewer_resolution",
        "reviewer_ack_followup_status_not_command_authorization",
        "reviewer_ack_followup_status_not_owner_material_real_acceptance",
        "source_handoff_status_not_delivery_success",
        "route_elevator_field_result_not_verified",
        "verified_terminal_delivery_result_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "true_phone_browser_evidence_not_verified",
        "real_cloud_external_proof_not_verified",
        "hardware_hil_not_verified",
        "delivery_success",
        "primary_actions_enabled",
        "safe_to_control",
    )
    values = []
    for item in list(source_values) + list(required):
        safe_item = _redact_route_task_rehearsal_text(item)
        lowered = safe_item.lower()
        # 禁止把 raw/path/checksum/HIL pass 这类阻断证据搬到手机安全摘要里。
        if any(
            marker in lowered
            for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
        ):
            continue
        if safe_item and safe_item not in values:
            values.append(safe_item)
    return values

def _default_field_evidence_real_material_owner_ack_intake_summary(
    path,
    status="blocked_missing_field_evidence_real_material_owner_ack_intake",
    read_error="",
):
    # 缺省摘要必须是完整 false 栅栏，避免 owner ack 缺失时 UI 或 Robot 侧误启主动作。
    safe_copy = (
        "Field evidence real material owner ack intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material owner ack intake summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "owner_ack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "material_group": "",
        "field_owner": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "blocked_reason": "",
        "next_required_evidence": [],
        "owner_next_steps": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE,
        "not_proven": _field_evidence_real_material_owner_ack_intake_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_real_material_owner_ack_review_decision_summary(
    path,
    status="blocked_missing_field_evidence_real_material_owner_ack_review_decision",
    read_error="",
):
    # 缺省 review-decision 也必须是完整 false 栅栏，避免 owner ack 被误读为控制许可。
    safe_copy = (
        "Field evidence real material owner ack review decision is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence real material owner ack review decision summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE,
        "capability": "field_evidence_real_material_owner_ack_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "review_decision": "blocked_missing_owner_ack_review_decision_not_proven",
        "source_owner_ack_schema": "",
        "source_owner_ack_status": "blocked",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "decision_reasons": [reason],
        "missing_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE,
        "proof_boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_real_material_owner_ack_review_decision_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_blocker_escalation_pack_summary(
    path,
    status="blocked_missing_field_evidence_material_blocker_escalation_pack",
    read_error="",
):
    # 缺省态固定四个 false flags，避免缺 pack 时被手机或 Robot 误读成控制许可。
    safe_copy = (
        "Field evidence material blocker escalation pack is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material blocker escalation pack summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE,
        "capability": "field_evidence_material_blocker_escalation_pack",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "pack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "blocked_reason": reason,
        "target_owner": "",
        "owner_escalation_level": "",
        "next_required_evidence": [],
        "owner_handoff": [],
        "field_safe_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE,
        "not_proven": _field_evidence_material_blocker_escalation_pack_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_intake_summary(
    path,
    decision="blocked",
    read_error="",
):
    # 缺省态必须携带 Robot-safe alias schema 和 false flags，避免缺 resolution 时误启控制链路。
    safe_copy = (
        "Field evidence material resolution intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution intake summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE,
        "capability": "field_evidence_material_resolution_intake",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "decision": decision,
        "status": "blocked_missing_field_evidence_material_resolution_intake",
        "overall_status": "not_proven",
        "resolution_status": {
            "status": "blocked_missing_field_evidence_material_resolution_intake",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "accepted_summary": [],
        "missing_summary": [],
        "rejected_summary": [],
        "blocked_summary": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE,
        "not_proven": _field_evidence_material_resolution_intake_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_review_decision_summary(
    path,
    decision="blocked_missing_resolution_intake_not_proven",
    read_error="",
):
    # 缺省态必须 blocked/not_proven；没有 sanitized review summary 时不能给手机或 Robot 控制许可。
    safe_copy = (
        "Field evidence material resolution review decision is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution review decision summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE,
        "capability": "field_evidence_material_resolution_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "decision": decision,
        "status": decision,
        "overall_status": "not_proven",
        "review_status": {
            "status": decision,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "reason": reason,
        "next_required_evidence": [],
        "owner_review_handoff": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": decision, "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_material_resolution_review_decision_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_review_handoff_summary(
    path,
    handoff_status="blocked_missing_review_decision_not_proven",
    read_error="",
):
    # 缺 handoff 时必须完整 fail closed，防止交接摘要被误读成发车准备完成。
    safe_copy = (
        "Field evidence material resolution review handoff is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution review handoff summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE,
        "capability": "field_evidence_material_resolution_review_handoff",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "overall_status": "not_proven",
        "handoff_review_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "previous_review_decision_ref": "",
        "previous_review_decision": "",
        "accepted_material_refs": [],
        "rejected_material_refs": [],
        "missing_required_materials": [],
        "owner_handoff_role": "",
        "owner_next_action": "",
        "next_required_real_evidence": [],
        "blocked_categories": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": handoff_status, "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE,
        "not_proven": _field_evidence_material_resolution_review_handoff_not_proven(),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_followup_escalation_status_summary(
    path,
    followup_status="pending_owner_response_not_proven",
    read_error="",
):
    # 缺 follow-up status 时也要返回完整 false 栅栏，避免 diagnostics 被误读成 owner ready。
    safe_copy = (
        "Field evidence material resolution follow-up escalation status is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; owner response material missing."
    )
    reason = read_error or (
        "field evidence material resolution follow-up escalation status is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "capability": "field_evidence_material_resolution_followup_escalation_status",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "followup_status": followup_status,
        "status": followup_status,
        "overall_status": "not_proven",
        "followup_review_status": {
            "status": followup_status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "previous_handoff_ref": "",
        "previous_review_decision_ref": "",
        "owner_response_material_status": "missing",
        "due_status": "",
        "blocked_reason": reason,
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": followup_status, "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE,
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_followup_escalation_status_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_owner_response_intake_summary(
    path,
    status="blocked_missing_field_evidence_material_resolution_owner_response_intake",
    read_error="",
):
    # 缺省态固定为 diagnostics-only，避免 owner response 被误读成 readiness 或 review acceptance。
    safe_copy = (
        "Field evidence material resolution owner response intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution owner response intake summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE,
        "capability": "field_evidence_material_resolution_owner_response_intake",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "owner_response_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_bridge": "",
        "source_reviewer_ack_followup_status": {},
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "next_required_evidence": [],
        "operator_support_handoff": [],
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE,
        "not_proven": (
            _field_evidence_material_resolution_owner_response_intake_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_owner_response_review_decision_summary(
    path,
    decision="blocked_missing_owner_response_intake_not_proven",
    read_error="",
):
    # 缺 review-decision safe summary 时必须 fail closed，防止 owner response 被当成验收通过。
    safe_copy = (
        "Field evidence material resolution owner response review decision is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution owner response review decision summary "
        "is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "capability": "field_evidence_material_resolution_owner_response_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision": decision,
        "status": decision,
        "overall_status": "not_proven",
        "review_status": {
            "status": decision,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_schema": "",
        "source_owner_response_status": "blocked",
        "previous_owner_response_intake_ref": "",
        "decision_reasons": [reason],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "review_handoff_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": decision, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_owner_response_review_decision_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_owner_response_review_handoff_summary(
    path,
    handoff_status="blocked_missing_owner_response_review_handoff_not_proven",
    read_error="",
):
    # 缺 review-handoff safe summary 时必须 fail closed，避免 Robot 把 handoff 当成真实验收或控制许可。
    safe_copy = (
        "Field evidence material resolution owner response review handoff is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution owner response review handoff summary "
        "is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "capability": "field_evidence_material_resolution_owner_response_review_handoff",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "overall_status": "not_proven",
        "review_handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_review_decision_schema": "",
        "source_owner_response_review_decision_status": "blocked",
        "previous_owner_response_review_decision_ref": "",
        "handoff_reasons": [reason],
        "handoff_targets": [],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": handoff_status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_owner_response_review_handoff_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "cursor_updates_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_reviewer_ack_intake_summary(
    path,
    status="blocked_missing_field_evidence_material_resolution_reviewer_ack_intake",
    read_error="",
):
    # 缺 reviewer ACK 时必须 fail closed，避免 ACK 摘要被误读成 reviewer resolved 或控制许可。
    safe_copy = (
        "Field evidence material resolution reviewer ack intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution reviewer ack intake summary is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE,
        "capability": "field_evidence_material_resolution_reviewer_ack_intake",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "reviewer_ack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_review_handoff_schema": "",
        "source_owner_response_review_handoff_status": "blocked",
        "previous_owner_response_review_handoff_ref": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "ack_reasons": [reason],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE,
        "proof_boundary": FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE,
        "not_proven": (
            _field_evidence_material_resolution_reviewer_ack_intake_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "ack_mutation_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_reviewer_ack_review_decision_summary(
    path,
    decision="blocked_missing_reviewer_ack_intake_not_proven",
    read_error="",
):
    # 缺 reviewer ACK review-decision 时必须 fail closed，避免 ACK 复核被误读成 resolved 或可控。
    safe_copy = (
        "Field evidence material resolution reviewer ack review decision is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution reviewer ack review decision summary "
        "is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "capability": "field_evidence_material_resolution_reviewer_ack_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision": decision,
        "status": decision,
        "overall_status": "not_proven",
        "review_status": {
            "status": decision,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_intake_schema": "",
        "source_reviewer_ack_intake_status": "blocked",
        "previous_reviewer_ack_intake_ref": "",
        "decision_reasons": [reason],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "review_handoff_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": decision, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_reviewer_ack_review_decision_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "ack_mutation_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_reviewer_ack_review_handoff_summary(
    path,
    status="blocked_missing_reviewer_ack_review_decision_not_proven",
    read_error="",
):
    # 缺 reviewer ACK review-handoff 时必须 fail closed，避免交接摘要被误读成 resolved 或可控。
    safe_copy = (
        "Field evidence material resolution reviewer ack review handoff is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution reviewer ack review handoff summary "
        "is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "capability": "field_evidence_material_resolution_reviewer_ack_review_handoff",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "handoff_status": status,
        "status": status,
        "overall_status": "not_proven",
        "review_handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_review_decision_schema": "",
        "source_reviewer_ack_review_decision_status": "blocked",
        "previous_reviewer_ack_review_decision_ref": "",
        "handoff_reasons": [reason],
        "handoff_targets": [],
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "unsafe_materials": [],
        "next_required_evidence": [],
        "owner_action": "",
        "ceo_escalation_recommendation": "",
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_comment_id": "3269642220",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_reviewer_ack_review_handoff_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "ack_mutation_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
    }

def _default_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary(
    path,
    status="blocked_missing_reviewer_ack_handoff_not_proven",
    read_error="",
):
    # 缺 followup escalation status 时必须仍返回完整 false 栅栏，手机端只能展示追办缺口。
    safe_copy = (
        "Field evidence material resolution reviewer ack followup escalation "
        "status is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence material resolution reviewer ack followup escalation "
        "status summary is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "capability": (
            "field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "followup_status": status,
        "due_status": "blocked",
        "status": status,
        "overall_status": "not_proven",
        "followup_status_summary": {
            "status": status,
            "due_status": "blocked",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_handoff_status": "blocked",
        "source_handoff_schema": "",
        "source_handoff_ref": "",
        "owner_handoff_hints": [],
        "missing_required_evidence": [reason],
        "next_required_evidence": [],
        "phone_safe_copy": safe_copy,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "not_proven": (
            _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_not_proven()
        ),
        "metadata_only": True,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "collect_triggered": False,
        "dropoff_triggered": False,
        "cancel_triggered": False,
        "ack_post_allowed": False,
        "ack_mutation_allowed": False,
        "cursor_updates_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "read_error": _redact_route_task_rehearsal_text(read_error),
    }

def _field_evidence_real_material_request_dispatch_source_contract(value):
    # Robot 只接受 Autonomy 的 canonical summary，或带 canonical summary 的 compatible wrapper。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_response_intake_source_contract(value):
    # response intake 兼容 canonical summary 和 wrapper，但必须回指本轮 response-intake gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_response_review_decision_source_contract(value):
    # review decision 只能消费本轮 canonical summary 或 wrapper，不能误接 response-intake gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_response_review_handoff_source_contract(value):
    # review handoff 只能消费本轮 handoff canonical summary 或 wrapper，不能误接 review-decision。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_followup_escalation_status_source_contract(value):
    # follow-up status 只接受 field-evidence gate 的 canonical summary 或 compatible wrapper。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_owner_ack_intake_source_contract(value):
    # owner-ack alias 只接受本轮 ack-intake canonical summary 或 Robot safe alias。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_real_material_owner_ack_review_decision_source_contract(value):
    # owner-ack review-decision 只接受本轮 review-decision summary 或 wrapper，不能误接 intake。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_blocker_escalation_pack_source_contract(value):
    # escalation pack 只接受 PC gate 的 canonical summary 或带 summary 的 wrapper。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_intake_source_contract(value):
    # resolution intake 只接受 PC gate 的 sanitized summary 或 Robot alias，禁止消费 raw artifact。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_review_decision_source_contract(value):
    # review-decision 只信任 sanitized summary；raw artifact wrapper 必须另带 summary 才能继续。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_review_handoff_source_contract(value):
    # handoff 只信任 sanitized summary；wrapper 只能提供定位，不能直接泄露 raw artifact。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_followup_escalation_status_source_contract(
    value,
):
    # follow-up escalation status 只信任 PC safe summary；artifact wrapper 必须嵌套 summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_owner_response_intake_source_contract(value):
    # owner response intake 只信任 PC safe summary 或 Robot alias；raw artifact wrapper 必须另带 summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_owner_response_review_decision_source_contract(
    value,
):
    # owner-response review-decision 只信任 PC safe summary 或 Robot alias，不能直接消费 raw GitHub/材料包。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_owner_response_review_handoff_source_contract(
    value,
):
    # owner-response review-handoff 只信任 PC safe summary 或 Robot alias，raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_reviewer_ack_intake_source_contract(value):
    # reviewer ACK intake 只信任 PC safe summary 或 Robot alias，raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_reviewer_ack_review_decision_source_contract(
    value,
):
    # reviewer ACK review-decision 只信任 safe summary；raw ACK/review artifact 必须另带 summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_reviewer_ack_review_handoff_source_contract(
    value,
):
    # reviewer ACK review-handoff 只信任 safe summary；raw handoff wrapper 必须另带 summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source_contract(
    value,
):
    # followup escalation status 只接受 PC safe summary 或其 artifact wrapper，不直接信任 raw artifact。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary

def _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(value):
    # Robot diagnostics 只展示白名单摘要；路径、凭证、checksum、topic、串口和控制字段一律阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack_cursor",
        "command",
    )
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(fragment in str(key).lower() for fragment in unsafe_key_fragments):
                return True
            if _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(item)
            for item in value
        )
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value).lower()
        return any(marker in redacted for marker in unsafe_text_fragments)
    return False

def _field_evidence_material_resolution_intake_has_unsafe_fields(value):
    # resolution alias 白名单比 PC artifact 更窄：只允许决策桶、handoff、next evidence 和 false flags。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack",
        "cursor",
        "command",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "decision",
        "status",
        "overall_status",
        "resolution_status",
        "status_summary",
        "verdict",
        "reason",
        "accepted_summary",
        "missing_summary",
        "rejected_summary",
        "blocked_summary",
        "accepted",
        "missing",
        "rejected",
        "blocked",
        "next_required_evidence",
        "owner_handoff",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_intake_summary",
        "robot_diagnostics_field_evidence_material_resolution_intake_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_intake_has_unsafe_fields(item)
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "ack payload",
        "cursor payload",
        "complete artifact",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_review_decision_has_unsafe_fields(value):
    # review-decision alias 是手机/Robot 可见面，只保留 owner-review 所需的最小字段。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack",
        "cursor",
        "command",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "decision",
        "status",
        "overall_status",
        "review_status",
        "status_summary",
        "verdict",
        "reason",
        "next_required_evidence",
        "owner_review_handoff",
        "owner_handoff",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_review_decision_summary",
        "robot_diagnostics_field_evidence_material_resolution_review_decision_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "ack payload",
        "cursor payload",
        "complete artifact",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "success=true",
        "success enabled",
        "operation succeeded",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_review_handoff_has_unsafe_fields(value):
    # handoff alias 只展示交接摘要；命令、ACK、raw 材料和成功语义全部阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack",
        "cursor",
        "command",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "handoff_status",
        "status",
        "overall_status",
        "handoff_review_status",
        "review_status",
        "status_summary",
        "verdict",
        "reason",
        "previous_review_decision_ref",
        "previous_review_decision",
        "accepted_material_refs",
        "rejected_material_refs",
        "missing_required_materials",
        "owner_handoff_role",
        "owner_next_action",
        "next_required_real_evidence",
        "next_required_evidence",
        "blocked_categories",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_review_handoff_summary",
        "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_review_handoff_has_unsafe_fields(item)
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "ack payload",
        "cursor payload",
        "complete artifact",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "success=true",
        "success enabled",
        "operation succeeded",
        "ready=true",
        "readiness=true",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
    value,
):
    # escalation status 是 read-only support metadata，任何 raw GitHub/ROS/硬件/控制字段都 fail closed。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "ack",
        "cursor",
        "command",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "github_raw",
        "reviewer_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "followup_status",
        "status",
        "overall_status",
        "followup_review_status",
        "status_summary",
        "verdict",
        "reason",
        "previous_handoff_ref",
        "previous_review_decision_ref",
        "owner_response_material_status",
        "due_status",
        "blocked_reason",
        "next_required_evidence",
        "owner_action",
        "owner_next_action",
        "ceo_escalation_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if (
                _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
                    item
                )
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "ack payload",
        "cursor payload",
        "complete artifact",
        "raw github",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "reviewer resolved",
        "thread resolved",
        "success=true",
        "operation succeeded",
        "field pass",
        "cloud proof",
        "phone proof",
        "hil pass",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
    value,
):
    # 该 alias 面向 Robot diagnostics 和 operator support，任何 raw/GitHub/控制/硬件细节都直接阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "traceback",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "owner_response_status",
        "source_bridge",
        "source_reviewer_ack_followup_status",
        "source_followup_status",
        "reviewer_ack_followup_status",
        "status_summary",
        "verdict",
        "reason",
        "accepted_materials_summary",
        "missing_materials_summary",
        "rejected_materials_summary",
        "unsafe_materials_summary",
        "accepted_summary",
        "missing_summary",
        "rejected_summary",
        "unsafe_summary",
        "accepted",
        "missing",
        "rejected",
        "unsafe",
        "next_required_evidence",
        "operator_support_handoff",
        "owner_handoff",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_owner_response_intake_summary",
        "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "review accepted",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
    value,
):
    # review-decision 可见字段比 intake 多，但 raw/GitHub/凭证/控制/硬件细节仍一律阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "review_status",
        "decision_status",
        "status_summary",
        "verdict",
        "reason",
        "review_decision",
        "decision",
        "source_owner_response_schema",
        "source_owner_response_status",
        "previous_owner_response_intake_ref",
        "decision_reasons",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "unsafe_materials",
        "next_required_evidence",
        "owner_action",
        "ceo_escalation_recommendation",
        "review_handoff_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_owner_response_review_decision_summary",
        "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
    value,
):
    # handoff alias 只允许 phone-safe 元数据；raw/GitHub/凭证/控制/硬件细节一律 fail closed。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "review_handoff_status",
        "handoff_status",
        "status_summary",
        "verdict",
        "reason",
        "source_owner_response_review_decision_schema",
        "source_owner_response_review_decision_status",
        "previous_owner_response_review_decision_ref",
        "handoff_reasons",
        "handoff_targets",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "unsafe_materials",
        "next_required_evidence",
        "owner_action",
        "ceo_escalation_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_owner_response_review_handoff_summary",
        "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "replay enabled",
        "resubmit enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(value):
    # reviewer ACK alias 只允许 phone-safe 元数据；ACK/cursor mutation、控制和硬件细节一律阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
        "mutation",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "reviewer_ack_status",
        "status_summary",
        "verdict",
        "reason",
        "source_owner_response_review_handoff_schema",
        "source_owner_response_review_handoff_status",
        "previous_owner_response_review_handoff_ref",
        "acknowledged_by",
        "acknowledged_at",
        "ack_reasons",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "unsafe_materials",
        "next_required_evidence",
        "owner_action",
        "ceo_escalation_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_reviewer_ack_intake_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "ack mutation",
        "cursor mutation",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "replay enabled",
        "resubmit enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
    value,
):
    # review-decision 可见字段更窄；raw ACK、resolved claim、控制和硬件细节一律 fail closed。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
        "mutation",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "review_status",
        "decision_status",
        "status_summary",
        "verdict",
        "reason",
        "review_decision",
        "decision",
        "source_reviewer_ack_intake_schema",
        "source_reviewer_ack_intake_status",
        "previous_reviewer_ack_intake_ref",
        "decision_reasons",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "unsafe_materials",
        "next_required_evidence",
        "owner_action",
        "ceo_escalation_recommendation",
        "review_handoff_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_reviewer_ack_review_decision_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "ack mutation",
        "cursor mutation",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "replay enabled",
        "resubmit enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
    value,
):
    # handoff 可见字段只服务诊断交接；raw ACK、resolved claim、控制和硬件细节一律 fail closed。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "command",
        "ack_cursor",
        "mutation",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "review_handoff_status",
        "handoff_status",
        "handoff_status_summary",
        "status_summary",
        "verdict",
        "reason",
        "source_reviewer_ack_review_decision_schema",
        "source_reviewer_ack_review_decision_status",
        "previous_reviewer_ack_review_decision_ref",
        "handoff_reasons",
        "handoff_targets",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "unsafe_materials",
        "next_required_evidence",
        "owner_action",
        "ceo_escalation_recommendation",
        "pr5_thread_id",
        "pr5_thread_state",
        "pr5_material_state",
        "pr5_reply_comment_id",
        "pr5_reply_resolution_claim",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "ack mutation",
        "cursor mutation",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "replay enabled",
        "resubmit enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
    value,
):
    # 追办状态只能给 Robot/手机展示白名单摘要；任何 raw、路径、控制或硬件细节都阻断。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "signed_url",
        "github",
        "db_url",
        "queue_url",
        "oss_ak",
        "oss_sk",
        "traceback",
        "internal_log",
        "ros_topic",
        "topic",
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "control_permission",
        "command",
        "ack_cursor",
        "mutation",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "followup_status",
        "due_status",
        "status",
        "overall_status",
        "followup_status_summary",
        "status_summary",
        "verdict",
        "reason",
        "source_handoff_status",
        "source_handoff_schema",
        "source_handoff_ref",
        "source_reviewer_ack_handoff_status",
        "source_reviewer_ack_handoff_schema",
        "source_reviewer_ack_handoff_ref",
        "owner_handoff_hints",
        "owner_action",
        "support_escalation_owner",
        "missing_required_evidence",
        "missing_materials",
        "next_required_evidence",
        "phone_safe_copy",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_fragments = (
        "/cmd_vel",
        "/dev/tty",
        "ttyusb",
        "wave rover",
        "wave_rover",
        "traceback",
        "checksum",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "signed url",
        "github raw",
        "raw github",
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "internal log",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "readiness=true",
        "owner material accepted",
        "reviewer resolved",
        "pr reviewer resolved",
        "pr resolved",
        "ack mutation",
        "cursor mutation",
        "start delivery",
        "confirm dropoff",
        "control enabled",
        "cancel enabled",
        "replay enabled",
        "resubmit enabled",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)

def _field_evidence_real_material_owner_ack_intake_has_unsafe_fields(
    value,
    key_path="",
):
    # ack-intake 面向 diagnostics，只允许安全摘要；raw 包、路径、凭证、topic、串口和完整 artifact 都阻断。
    unsafe_key_fragments = (
        "raw",
        "packet",
        "artifact_path",
        "artifact_ref",
        "complete_artifact",
        "full_artifact",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            nested_path = f"{key_path}.{key_text}" if key_path else key_text
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _field_evidence_real_material_owner_ack_intake_has_unsafe_fields(
                item,
                nested_path,
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_owner_ack_intake_has_unsafe_fields(
                item,
                key_path,
            )
            for item in value
        )
    if isinstance(value, str):
        redacted = _redact_route_task_rehearsal_text(value).lower()
        unsafe_markers = (
            "[redacted_auth_header]",
            "bearer [redacted]",
            "[redacted_url]",
            "/dev/[redacted_serial]",
            "[redacted_baud]",
            "[redacted_local_path]",
            "hil pass",
            "real hil",
            "delivery success",
            "control enabled",
            "start delivery enabled",
            "confirm dropoff enabled",
            "cancel enabled",
            "ack posted",
            "cursor advanced",
            "nav2 started",
        )
        return any(marker in redacted for marker in unsafe_markers)
    return False

def _field_evidence_real_material_request_dispatch_has_unsafe_fields(value):
    # request dispatch 要允许材料类别名，但禁止 raw artifact、raw diagnostics 和任何控制/硬件细节。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "raw_diagnostics",
        "diagnostics_raw",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "cmd_vel",
        "control",
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "complete_artifact",
        "complete_diagnostics",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "request_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "request_verdict",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "required_materials",
        "owner_mapping",
        "owner_handoff",
        "next_required_evidence",
        "blocked_claims",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "control_entrypoint_enabled",
        "field_evidence_real_material_request_dispatch_summary",
        "robot_diagnostics_field_evidence_real_material_request_dispatch_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_real_material_request_dispatch_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_request_dispatch_has_unsafe_fields(item)
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_markers = (
        "/cmd_vel",
        "ros_topic",
        "serial",
        "uart",
        "wave rover",
        "wave_rover",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "traceback",
        "checksum",
        "db_url",
        "queue_url",
        "oss_access_key",
        "oss_secret",
        "local_path",
        "/tmp/",
    )
    return any(marker in text for marker in unsafe_text_markers) or (
        _route_task_field_retest_execution_pack_has_success_wording(value)
    )

def _field_evidence_real_material_response_intake_has_unsafe_fields(value):
    # response intake 允许四类状态桶，但仍禁止 raw/source 材料和任何成功、控制、硬件细节。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "raw_diagnostics",
        "diagnostics_raw",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "cmd_vel",
        "control",
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "complete_artifact",
        "complete_diagnostics",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "response_status",
        "intake_status",
        "material_response_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "response_verdict",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "required_materials",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "blocked_materials",
        "material_statuses",
        "accepted",
        "missing",
        "rejected",
        "blocked",
        "next_required_evidence",
        "blocked_claims",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "control_entrypoint_enabled",
        "field_evidence_real_material_response_intake_summary",
        "robot_diagnostics_field_evidence_real_material_response_intake_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "blocked_claims":
                # blocked_claims 会列出被禁止的硬件/控制证明名；这些名称只能作为阻断声明展示。
                continue
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_real_material_response_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_response_intake_has_unsafe_fields(item)
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_markers = (
        "/cmd_vel",
        "ros_topic",
        "serial",
        "uart",
        "wave rover",
        "wave_rover",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "traceback",
        "checksum",
        "db_url",
        "queue_url",
        "oss_access_key",
        "oss_secret",
        "local_path",
        "/tmp/",
    )
    return any(marker in text for marker in unsafe_text_markers) or (
        _route_task_field_retest_execution_pack_has_success_wording(value)
    )

def _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
    value,
    key_path="",
):
    # review-decision 只展示复核结论和下一步材料；任何 raw/路径/硬件/控制/PR 解决语义都阻断。
    unsafe_key_fragments = (
        "raw",
        "packet",
        "artifact_path",
        "artifact_ref",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "cmd_vel",
        "control",
        "ack_post",
        "ack_cursor",
        "cursor",
        "traceback",
        "complete_log",
        "complete_artifact",
        "pr5_resolved",
        "review_thread_resolved",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "source_owner_ack_schema",
        "source_owner_ack_status",
        "source_owner_ack_summary_status",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "status",
        "overall_status",
        "review_status",
        "status_summary",
        "verdict",
        "reason",
        "review_decision",
        "decision",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "decision_reasons",
        "missing_materials",
        "next_required_evidence",
        "owner_handoff",
        "proof_boundary",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "field_evidence_real_material_owner_ack_review_decision_summary",
        "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
                item,
                f"{key_path}.{key_text}" if key_path else key_text,
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
                item,
                key_path,
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_markers = (
        "/cmd_vel",
        "ros_topic",
        "serial",
        "uart",
        "wave rover",
        "wave_rover",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "traceback",
        "checksum",
        "/tmp/",
        "local path",
        "complete log",
        "complete artifact",
        "hil pass",
        "hil_pass",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "pr #5 resolved",
        "pr5 resolved",
        "review thread resolved",
    )
    return any(marker in text for marker in unsafe_text_markers) or (
        _route_task_field_retest_execution_pack_has_success_wording(value)
    )

def _field_evidence_real_material_response_review_decision_has_unsafe_fields(value):
    # review decision 允许人工复核结论字段，但拒绝 raw artifact、本地路径、硬件细节和控制语义。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "raw_diagnostics",
        "diagnostics_raw",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "cmd_vel",
        "control",
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "complete_artifact",
        "complete_diagnostics",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "source_response_intake_schema",
        "source_response_intake_status",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "review_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "review_decision",
        "decision",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "blocked_materials",
        "decision_reasons",
        "owner_handoff",
        "next_required_evidence",
        "blocked_claims",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "control_entrypoint_enabled",
        "field_evidence_real_material_response_review_decision_summary",
        "robot_diagnostics_field_evidence_real_material_response_review_decision_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "blocked_claims":
                # blocked_claims 只能展示被拒绝的证明类型名，不代表 Robot 接受这些 raw 证明。
                continue
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_real_material_response_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_response_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_markers = (
        "/cmd_vel",
        "ros_topic",
        "serial",
        "uart",
        "wave rover",
        "wave_rover",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "traceback",
        "checksum",
        "db_url",
        "queue_url",
        "oss_access_key",
        "oss_secret",
        "local_path",
        "/tmp/",
    )
    return any(marker in text for marker in unsafe_text_markers) or (
        _route_task_field_retest_execution_pack_has_success_wording(value)
    )

def _field_evidence_real_material_response_review_handoff_has_unsafe_fields(value):
    # handoff 只允许 owner 交接摘要；raw 复核材料、路径、ACK/cursor 和控制路由必须被拦截。
    unsafe_key_fragments = (
        "raw",
        "artifact_path",
        "artifact_ref",
        "raw_diagnostics",
        "raw_review",
        "review_material",
        "diagnostics_raw",
        "local_path",
        "path",
        "checksum",
        "credential",
        "secret",
        "token",
        "authorization",
        "bearer",
        "ros_topic",
        "topic",
        "serial",
        "uart",
        "baud",
        "wave_rover",
        "cmd_vel",
        "control",
        "ack_cursor",
        "ack_post",
        "ack_state",
        "ack_route",
        "cursor",
        "cursor_route",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "complete_artifact",
        "complete_diagnostics",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "capability",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "source_review_decision",
        "source_review_decision_status",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "handoff_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "handoff_decision",
        "review_decision",
        "decision",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "owner_handoff",
        "next_required_evidence",
        "blocker_summary",
        "rerun_guidance",
        "reconciliation_guidance",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "control_entrypoint_enabled",
        "field_evidence_real_material_response_review_handoff_summary",
        "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary",
        "diagnostics",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_real_material_response_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_real_material_response_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    unsafe_text_markers = (
        "/cmd_vel",
        "ros_topic",
        "serial",
        "uart",
        "wave rover",
        "wave_rover",
        "bearer",
        "authorization",
        "credential",
        "secret",
        "token",
        "traceback",
        "checksum",
        "db_url",
        "queue_url",
        "oss_access_key",
        "oss_secret",
        "local_path",
        "/tmp/",
        "ack/",
        "cursor/",
    )
    return any(marker in text for marker in unsafe_text_markers) or (
        _route_task_field_retest_execution_pack_has_success_wording(value)
    )

def summarize_field_evidence_real_material_request_dispatch(source):
    """构建 field evidence real material request dispatch 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        request = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_real_material_request_dispatch_summary(
            source_path,
            read_error="field evidence real material request dispatch is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "request_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence real material request dispatch summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material request dispatch summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                request = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "request_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence real material request dispatch: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material request dispatch JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_real_material_request_dispatch_summary(
        source_path,
        read_error="field evidence real material request dispatch is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(request, dict):
        summary.update(
            {
                "request_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence real material request dispatch JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "real material request dispatch JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = request.get("diagnostics") if isinstance(request.get("diagnostics"), dict) else {}
    # compatible wrapper 可以出现多种字段名，但最终必须落到 canonical safe summary。
    summary_fragment = (
        request
        if str(request.get("schema") or "")
        == FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            request.get("field_evidence_real_material_request_dispatch_summary"),
            request.get(
                "robot_diagnostics_field_evidence_real_material_request_dispatch_summary"
            ),
            request.get("robot_compatible_summary"),
            request.get("summary"),
            request.get("diagnostics_summary"),
            diagnostics.get("field_evidence_real_material_request_dispatch_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_real_material_request_dispatch_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else request
    source_schema, source_boundary = (
        _field_evidence_real_material_request_dispatch_source_contract(contract_source)
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
        summary.update(
            {
                "request_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence real material request dispatch lacks a safe canonical summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe real material request dispatch summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("request_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    request_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("request_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence real material request dispatch consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence real material request dispatch is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # phone-safe copy 必须重复 false literal，方便下游只读面板直接显示边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        request.get("safe_evidence_ref") or request.get("evidence_ref") or ""
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
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    owner_mapping = (
        _safe_pc_route_debug_dict(summary_fragment.get("owner_mapping"))
        if isinstance(summary_fragment.get("owner_mapping"), dict)
        else _safe_route_task_rehearsal_list(summary_fragment.get("owner_mapping"))
    )
    required_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("required_materials"),
        limit=len(FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS),
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "request_status": {
                "status": request_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "request_verdict": _redact_route_task_rehearsal_text(
                summary_fragment.get("request_verdict")
                or summary_fragment.get("decision")
                or request_status
                or "blocked"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": request_status or "blocked",
                "verdict": "not_proven",
                "reason": "real material request dispatch lacks same evidence_ref status",
            },
            "required_materials": required_materials,
            "owner_mapping": owner_mapping or {},
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "blocked_claims": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_claims")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": request_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_real_material_request_dispatch_not_proven(
                request,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_material_set = {
        str(item or "").strip() for item in summary["required_materials"]
    }
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        summary["same_evidence_ref_required"] is True,
        bool(summary["same_evidence_ref_status"]),
        set(FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS)
        <= required_material_set,
        bool(summary["owner_mapping"]),
        bool(summary["next_required_evidence"]),
    )
    unsafe_material = any(
        _field_evidence_real_material_request_dispatch_has_unsafe_fields(item)
        for item in (
            status_source,
            same_ref_source,
            summary["required_materials"],
            summary["owner_mapping"],
            summary["next_required_evidence"],
            summary["blocked_claims"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SCHEMA
        or source_boundary != FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE
    ):
        summary.update(
            {
                "request_status": {
                    "status": "blocked_unsupported_field_evidence_real_material_request_dispatch",
                    "verdict": "not_proven",
                    "reason": "field evidence real material request dispatch schema or boundary is unsupported",
                },
                "request_verdict": "blocked",
                "owner_mapping": {},
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported real material request dispatch schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["request_status"] = {
            "status": "blocked_unsupported_field_evidence_real_material_request_dispatch",
            "verdict": "not_proven",
            "reason": "real material request dispatch must remain software_proof and not_proven",
        }
        summary["request_verdict"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "request_status": {
                    "status": "blocked_missing_field_evidence_real_material_request_dispatch_materials",
                    "verdict": "not_proven",
                    "reason": "real material request dispatch is missing required safe metadata",
                },
                "request_verdict": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required real material request dispatch fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["request_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_real_material_request_dispatch_blocked",
            "verdict": "not_proven",
            "reason": "real material request dispatch evidence_ref values do not match",
        }
        summary["request_verdict"] = "blocked"
        summary["same_evidence_ref_status"] = {
            "status": "mismatch",
            "verdict": "not_proven",
            "reason": "same evidence_ref mismatch",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_real_material_request_dispatch_has_unsafe_fields(request)
        or _field_evidence_real_material_request_dispatch_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_real_material_request_dispatch_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence real material request dispatch was blocked because "
            "summary fields could expose raw artifacts, diagnostics, control data, paths, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "request_status": {
                    "status": "blocked_unsafe_field_evidence_real_material_request_dispatch",
                    "verdict": "not_proven",
                    "reason": "unsafe raw artifact, diagnostics, control, path, credential, or success material",
                },
                "request_verdict": "blocked",
                "owner_mapping": {},
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

def summarize_field_evidence_real_material_response_intake(source):
    """构建 field evidence real material response intake 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        response = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_real_material_response_intake_summary(
            source_path,
            read_error="field evidence real material response intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "response_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence real material response intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response intake summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "response_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence real material response intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_real_material_response_intake_summary(
        source_path,
        read_error="field evidence real material response intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(response, dict):
        summary.update(
            {
                "response_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "real material response intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        response.get("diagnostics")
        if isinstance(response.get("diagnostics"), dict)
        else {}
    )
    # wrapper、latest_status 和 diagnostics 嵌套都必须最终落到 canonical sanitized summary。
    summary_fragment = (
        response
        if str(response.get("schema") or "")
        == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            response.get("field_evidence_real_material_response_intake_summary"),
            response.get(
                "robot_diagnostics_field_evidence_real_material_response_intake_summary"
            ),
            response.get("robot_compatible_summary"),
            response.get("summary"),
            response.get("diagnostics_summary"),
            diagnostics.get("field_evidence_real_material_response_intake_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_real_material_response_intake_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else response
    source_schema, source_boundary = (
        _field_evidence_real_material_response_intake_source_contract(contract_source)
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
        summary.update(
            {
                "response_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response intake lacks a safe canonical summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe real material response intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("response_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("material_response_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    response_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("response_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence real material response intake consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence real material response intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # copy 里保留 literal false，方便 mobile/diagnostics 面板直接展示安全边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        response.get("safe_evidence_ref") or response.get("evidence_ref") or ""
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
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    material_statuses_source = (
        summary_fragment.get("material_statuses")
        if isinstance(summary_fragment.get("material_statuses"), dict)
        else {}
    )
    accepted_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("accepted_materials")
        or material_statuses_source.get("accepted")
    )
    missing_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_materials")
        or material_statuses_source.get("missing")
    )
    rejected_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("rejected_materials")
        or material_statuses_source.get("rejected")
    )
    blocked_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("blocked_materials")
        or material_statuses_source.get("blocked")
    )
    required_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("required_materials"),
        limit=len(FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS),
    )
    material_statuses = {
        "accepted": accepted_materials,
        "missing": missing_materials,
        "rejected": rejected_materials,
        "blocked": blocked_materials,
    }
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "response_status": {
                "status": response_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "response_verdict": _redact_route_task_rehearsal_text(
                summary_fragment.get("response_verdict")
                or summary_fragment.get("decision")
                or response_status
                or "blocked"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": response_status or "blocked",
                "verdict": "not_proven",
                "reason": "real material response intake lacks same evidence_ref status",
            },
            "required_materials": required_materials,
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "blocked_materials": blocked_materials,
            "material_statuses": material_statuses,
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "blocked_claims": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_claims")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": response_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_real_material_response_intake_not_proven(
                response,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_material_set = {
        str(item or "").strip() for item in summary["required_materials"]
    }
    classified_materials = set()
    for bucket in material_statuses.values():
        classified_materials.update(str(item or "").strip() for item in bucket)
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        summary["same_evidence_ref_required"] is True,
        bool(summary["same_evidence_ref_status"]),
        set(FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS)
        <= required_material_set,
        set(FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_STATUSES)
        == set(material_statuses),
        required_material_set <= classified_materials,
        bool(summary["next_required_evidence"]),
        bool(summary["blocked_claims"]),
    )
    unsafe_material = any(
        _field_evidence_real_material_response_intake_has_unsafe_fields(item)
        for item in (
            status_source,
            same_ref_source,
            summary["required_materials"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["blocked_materials"],
            summary["material_statuses"],
            summary["next_required_evidence"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE
    ):
        summary.update(
            {
                "response_status": {
                    "status": "blocked_unsupported_field_evidence_real_material_response_intake",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response intake schema or boundary is unsupported",
                },
                "response_verdict": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported real material response intake schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["response_status"] = {
            "status": "blocked_unsupported_field_evidence_real_material_response_intake",
            "verdict": "not_proven",
            "reason": "real material response intake must remain software_proof and not_proven",
        }
        summary["response_verdict"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "response_status": {
                    "status": "blocked_missing_field_evidence_real_material_response_intake_materials",
                    "verdict": "not_proven",
                    "reason": "real material response intake is missing required safe metadata",
                },
                "response_verdict": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required real material response intake fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["response_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_real_material_response_intake_blocked",
            "verdict": "not_proven",
            "reason": "real material response intake evidence_ref values do not match",
        }
        summary["response_verdict"] = "blocked"
        summary["same_evidence_ref_status"] = {
            "status": "mismatch",
            "verdict": "not_proven",
            "reason": "same evidence_ref mismatch",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_real_material_response_intake_has_unsafe_fields(response)
        or _field_evidence_real_material_response_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_real_material_response_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence real material response intake was blocked because "
            "summary fields could expose raw artifacts, diagnostics, control data, paths, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "response_status": {
                    "status": "blocked_unsafe_field_evidence_real_material_response_intake",
                    "verdict": "not_proven",
                    "reason": "unsafe raw artifact, diagnostics, control, path, credential, or success material",
                },
                "response_verdict": "blocked",
                "accepted_materials": [],
                "material_statuses": {
                    "accepted": [],
                    "missing": summary["missing_materials"],
                    "rejected": summary["rejected_materials"],
                    "blocked": summary["blocked_materials"],
                },
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

def summarize_field_evidence_real_material_response_review_decision(source):
    """构建 field evidence real material response review decision 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_real_material_response_review_decision_summary(
            source_path,
            read_error=(
                "field evidence real material response review decision is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence real material response review decision summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response review decision summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "review_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence real material response "
                            f"review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response review decision JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_real_material_response_review_decision_summary(
        source_path,
        read_error="field evidence real material response review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "real material response review decision JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    # 只接受 review-decision 自己的 summary；response-intake summary 只能作为上游状态引用。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("field_evidence_real_material_response_review_decision_summary"),
            decision.get(
                "robot_diagnostics_field_evidence_real_material_response_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            diagnostics.get("field_evidence_real_material_response_review_decision_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_real_material_response_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _field_evidence_real_material_response_review_decision_source_contract(
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
        summary.update(
            {
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response review decision lacks a safe canonical summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe real material response review decision summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence real material response review decision consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence real material response review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # 面板文案也要带 false flags；避免手机端把 accepted 文案误读成可发车。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        decision.get("safe_evidence_ref") or decision.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked_missing_field_evidence_real_material_response_intake_not_proven"
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "source_response_intake_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_response_intake_schema")
                or FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA
            ),
            "source_response_intake_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_response_intake_status") or "blocked"
            ),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "review_decision": review_decision,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "real material response review decision lacks same evidence_ref status",
            },
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "blocked_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_materials")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "blocked_claims": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_claims")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_real_material_response_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        summary["same_evidence_ref_required"] is True,
        bool(summary["same_evidence_ref_status"]),
        summary["review_decision"]
        in FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_VALUES,
        bool(summary["decision_reasons"]),
        bool(summary["owner_handoff"]),
        bool(summary["next_required_evidence"]),
        bool(summary["blocked_claims"]),
    )
    unsafe_material = any(
        _field_evidence_real_material_response_review_decision_has_unsafe_fields(item)
        for item in (
            status_source,
            same_ref_source,
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["blocked_materials"],
            summary["decision_reasons"],
            summary["owner_handoff"],
            summary["next_required_evidence"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SCHEMA
        or source_boundary != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_unsupported_field_evidence_real_material_response_review_decision",
                    "verdict": "not_proven",
                    "reason": "field evidence real material response review decision schema or boundary is unsupported",
                },
                "review_decision": (
                    "blocked_missing_field_evidence_real_material_response_intake_not_proven"
                ),
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported real material response review decision schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["review_status"] = {
            "status": "blocked_unsupported_field_evidence_real_material_response_review_decision",
            "verdict": "not_proven",
            "reason": "real material response review decision must remain software_proof and not_proven",
        }
        summary["review_decision"] = (
            "blocked_missing_field_evidence_real_material_response_intake_not_proven"
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_missing_field_evidence_real_material_response_review_decision_materials",
                    "verdict": "not_proven",
                    "reason": "real material response review decision is missing required safe metadata",
                },
                "review_decision": (
                    "blocked_missing_field_evidence_real_material_response_intake_not_proven"
                ),
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required real material response review decision fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_real_material_response_review_decision_blocked",
            "verdict": "not_proven",
            "reason": "real material response review decision evidence_ref values do not match",
        }
        summary["review_decision"] = (
            "blocked_missing_field_evidence_real_material_response_intake_not_proven"
        )
        summary["same_evidence_ref_status"] = {
            "status": "mismatch",
            "verdict": "not_proven",
            "reason": "same evidence_ref mismatch",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_real_material_response_review_decision_has_unsafe_fields(
            decision
        )
        or _field_evidence_real_material_response_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_real_material_response_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence real material response review decision was blocked because "
            "summary fields could expose raw artifacts, diagnostics, control data, paths, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_status": {
                    "status": "blocked_unsafe_field_evidence_real_material_response_review_decision",
                    "verdict": "not_proven",
                    "reason": "unsafe raw artifact, diagnostics, control, path, credential, or success material",
                },
                "review_decision": "rejected_unsafe_or_mixed_response_not_proven",
                "accepted_materials": [],
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

def summarize_field_evidence_real_material_response_review_handoff(source):
    """构建 field evidence real material response review handoff 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_real_material_response_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence real material response review handoff is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence real material response review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response review handoff summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence real material response "
                            f"review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "real material response review handoff JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_real_material_response_review_handoff_summary(
        source_path,
        read_error="field evidence real material response review handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary["handoff_status"] = {
            "status": "read_error",
            "verdict": "not_proven",
            "reason": "field evidence real material response review handoff JSON must be an object",
        }
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "real material response review handoff JSON shape is invalid",
        }
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("field_evidence_real_material_response_review_handoff_summary"),
            handoff.get(
                "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary"
            ),
            handoff.get("robot_compatible_summary"),
            handoff.get("summary"),
            handoff.get("diagnostics_summary"),
            diagnostics.get("field_evidence_real_material_response_review_handoff_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _field_evidence_real_material_response_review_handoff_source_contract(
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
        summary["handoff_status"] = {
            "status": "missing_summary",
            "verdict": "not_proven",
            "reason": "field evidence real material response review handoff lacks a safe canonical summary",
        }
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "missing safe real material response review handoff summary",
        }
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence real material response review handoff consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence real material response review handoff is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # handoff 文案必须重复 false flags，避免 owner-handoff 被 UI 当成可执行授权。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    source_review_decision_status = summary_fragment.get("source_review_decision_status")
    if not isinstance(source_review_decision_status, (dict, str)):
        source_review_decision_status = "blocked"
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "source_review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision")
                or summary_fragment.get("review_decision")
                or "blocked_missing_field_evidence_real_material_response_review_decision_not_proven"
            ),
            "source_review_decision_status": _safe_pc_route_debug_value(
                source_review_decision_status
            ),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "handoff_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("handoff_decision")
                or summary_fragment.get("decision")
                or "needs_real_material_owner_handoff_not_proven"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": "real material response review handoff lacks same evidence_ref status",
            },
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "blocker_summary": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocker_summary") or ""
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
            ),
            "reconciliation_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("reconciliation_guidance")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_real_material_response_review_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        summary["same_evidence_ref_required"] is True,
        bool(summary["same_evidence_ref_status"]),
        bool(summary["source_review_decision"]),
        bool(summary["source_review_decision_status"]),
        bool(summary["handoff_decision"]),
        bool(summary["owner_handoff"]),
        bool(summary["next_required_evidence"]),
        bool(summary["blocker_summary"]),
    )
    unsafe_material = any(
        _field_evidence_real_material_response_review_handoff_has_unsafe_fields(item)
        for item in (
            status_source,
            source_review_decision_status,
            same_ref_source,
            summary["owner_handoff"],
            summary["next_required_evidence"],
            summary["blocker_summary"],
            summary["rerun_guidance"],
            summary["reconciliation_guidance"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SCHEMA
        or source_boundary != FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE
    ):
        summary["handoff_status"] = {
            "status": "blocked_unsupported_field_evidence_real_material_response_review_handoff",
            "verdict": "not_proven",
            "reason": "field evidence real material response review handoff schema or boundary is unsupported",
        }
        summary["handoff_decision"] = (
            "blocked_missing_real_material_response_review_handoff_not_proven"
        )
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "unsupported real material response review handoff schema or boundary",
        }
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["handoff_status"] = {
            "status": "blocked_unsupported_field_evidence_real_material_response_review_handoff",
            "verdict": "not_proven",
            "reason": "real material response review handoff must remain software_proof and not_proven",
        }
        summary["handoff_decision"] = (
            "blocked_missing_real_material_response_review_handoff_not_proven"
        )
        return summary
    if not all(required_summary_fields):
        summary["handoff_status"] = {
            "status": "blocked_missing_field_evidence_real_material_response_review_handoff_materials",
            "verdict": "not_proven",
            "reason": "real material response review handoff is missing required safe metadata",
        }
        summary["handoff_decision"] = (
            "blocked_missing_real_material_response_review_handoff_not_proven"
        )
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "missing required real material response review handoff fields",
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["handoff_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_real_material_response_review_handoff_blocked",
            "verdict": "not_proven",
            "reason": "real material response review handoff evidence_ref values do not match",
        }
        summary["handoff_decision"] = (
            "blocked_missing_real_material_response_review_handoff_not_proven"
        )
        summary["same_evidence_ref_status"] = {
            "status": "mismatch",
            "verdict": "not_proven",
            "reason": "same evidence_ref mismatch",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_real_material_response_review_handoff_has_unsafe_fields(
            handoff
        )
        or _field_evidence_real_material_response_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_real_material_response_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence real material response review handoff was blocked because "
            "summary fields could expose raw artifacts, review materials, control data, "
            "paths, credentials, ACK/cursor routes, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary["handoff_status"] = {
            "status": "blocked_unsafe_field_evidence_real_material_response_review_handoff",
            "verdict": "not_proven",
            "reason": "unsafe raw artifact, review material, control, path, credential, ACK/cursor, or success material",
        }
        summary["handoff_decision"] = (
            "blocked_unsafe_real_material_response_review_handoff_not_proven"
        )
        summary["owner_handoff"] = []
        summary["next_required_evidence"] = []
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "safe_copy": blocked_copy,
            "safe_phone_copy": blocked_copy,
        }
        summary["safe_copy"] = blocked_copy
        summary["safe_phone_copy"] = blocked_copy
    return summary

def summarize_field_evidence_real_material_followup_escalation_status(source):
    """构建 field-evidence 真实材料 follow-up escalation status 的安全 diagnostics 摘要。"""
    # Robot 只消费 Autonomy 生成的 canonical summary；wrapper 只是兼容载体，raw artifact 一律阻断。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_real_material_followup_escalation_status_summary(
        source_path,
        read_error=(
            "field_evidence_real_material_followup_escalation_status summary is not configured"
        ),
    )
    if isinstance(source, dict):
        followup = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_real_material_followup_escalation_status summary artifact missing"
            )
            summary["followup_status"]["reason"] = summary["read_error"]
            summary["followup_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_real_material_followup_escalation_status "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status"]["reason"] = safe_error
            return summary

    if not isinstance(followup, dict):
        summary["followup_status"]["reason"] = (
            "field_evidence_real_material_followup_escalation_status JSON must be an object"
        )
        return summary

    raw_schema = str(followup.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_real_material_followup_escalation_status_source_contract(followup)
    )
    if raw_schema == FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA:
        summary_fragment = followup
    else:
        summary_fragment = {}
        for candidate in (
            followup.get("field_evidence_real_material_followup_escalation_status_summary"),
            followup.get(
                "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary"
            ),
            followup.get("diagnostics_summary"),
            followup.get("robot_diagnostics_summary"),
            followup.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if isinstance(summary_fragment, dict) and summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_real_material_followup_escalation_status_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    }
    followup_status = (
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
        else summary_fragment.get("escalation_status")
        if isinstance(summary_fragment.get("escalation_status"), dict)
        else followup.get("followup_status")
        if isinstance(followup.get("followup_status"), dict)
        else followup.get("escalation_status")
        if isinstance(followup.get("escalation_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or followup.get("safe_copy")
        or followup.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        followup_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or followup.get("status")
        or followup.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or followup.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or followup.get("source")
        or followup_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup.get("safe_evidence_ref")
        or followup.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else followup.get("robot_diagnostics_summary")
        if isinstance(followup.get("robot_diagnostics_summary"), dict)
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
    material_groups_source = (
        summary_fragment.get("material_groups")
        if isinstance(summary_fragment.get("material_groups"), list)
        else []
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
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "capability": "field_evidence_real_material_owner_ack_review_decision",
            "exists": True,
            "followup_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    followup_status.get("reason")
                    or summary_fragment.get("reason")
                    or followup.get("reason")
                    or (
                        "field evidence real material follow-up escalation status "
                        "is software_proof only"
                    )
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "material_group": _redact_route_task_rehearsal_text(
                summary_fragment.get("material_group") or followup.get("material_group") or ""
            ),
            "field_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("field_owner") or followup.get("field_owner") or ""
            ),
            "due_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("due_status") or followup.get("due_status") or ""
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or followup.get("blocked_reason")
                or followup_status.get("reason")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "escalation_level": _redact_route_task_rehearsal_text(
                summary_fragment.get("escalation_level")
                or followup.get("escalation_level")
                or ""
            ),
            "rerun_status_summary": _safe_pc_route_debug_dict(
                summary_fragment.get("rerun_status_summary")
                if isinstance(summary_fragment.get("rerun_status_summary"), dict)
                else {}
            ),
            "source_review_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_handoff_status")
                or followup.get("source_review_handoff_status")
                or ""
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "material_groups": _safe_pc_route_debug_value(material_groups_source),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_phone_copy": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_phone_copy")
                or followup.get("safe_phone_copy")
                or safe_copy
            ),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": (
                _field_evidence_real_material_followup_escalation_status_not_proven(
                    followup,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    boundary_supported = (
        source_boundary == FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE
    )
    if source_schema not in accepted_schemas or not boundary_supported:
        summary.update(
            {
                "status": "unsupported_schema",
                "followup_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_real_material_followup_escalation_status"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_followup_escalation_status "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        raw_schema == FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "missing_summary",
                "followup_status": {
                    "status": (
                        "blocked_missing_field_evidence_real_material_followup_escalation_status_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_followup_escalation_status "
                        "artifact is missing sanitized summary"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
            }
        )
        return summary

    # 任一 raw/凭证/路径/硬件/control/success 线索都降级，避免把状态摘要变成控制入口。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or followup.get("delivery_success") is True
        or followup.get("primary_actions_enabled") is True
        or followup.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(followup)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Field evidence real material follow-up escalation status was blocked "
            "because the summary did not remain source=software_proof/not_proven "
            "with delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_real_material_followup_escalation_status"
                ),
                "followup_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_real_material_followup_escalation_status"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_followup_escalation_status "
                        "contains unsafe fields, success wording, weak evidence_ref, "
                        "or control claims"
                    ),
                },
                "safe_evidence_ref": "",
                "material_groups": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "rerun_status_summary": {},
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_real_material_owner_ack_intake(source):
    """构建 field-evidence real-material owner ack intake 的安全 diagnostics 摘要。"""
    # Robot 只读取 PC/Autonomy 已消毒 summary；完整 raw ack packet 永远不能透传到 diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_real_material_owner_ack_intake_summary(
        source_path,
        read_error=(
            "field_evidence_real_material_owner_ack_intake summary is not configured"
        ),
    )
    if isinstance(source, dict):
        ack = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_real_material_owner_ack_intake summary artifact missing"
            )
            summary["owner_ack_status"]["reason"] = summary["read_error"]
            summary["owner_ack_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                ack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_real_material_owner_ack_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["owner_ack_status"]["reason"] = safe_error
            return summary

    if not isinstance(ack, dict):
        summary["owner_ack_status"]["reason"] = (
            "field_evidence_real_material_owner_ack_intake JSON must be an object"
        )
        return summary

    raw_schema = str(ack.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_real_material_owner_ack_intake_source_contract(ack)
    )
    if raw_schema in {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = ack
    else:
        summary_fragment = {}
        for candidate in (
            ack.get("field_evidence_real_material_owner_ack_intake_summary"),
            ack.get(
                "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary"
            ),
            ack.get("diagnostics_summary"),
            ack.get("robot_diagnostics_summary"),
            ack.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_real_material_owner_ack_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    accepted_schemas = {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA,
    }
    owner_ack_status = (
        summary_fragment.get("owner_ack_status")
        if isinstance(summary_fragment.get("owner_ack_status"), dict)
        else summary_fragment.get("ack_status")
        if isinstance(summary_fragment.get("ack_status"), dict)
        else ack.get("owner_ack_status")
        if isinstance(ack.get("owner_ack_status"), dict)
        else ack.get("ack_status")
        if isinstance(ack.get("ack_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or ack.get("safe_copy")
        or ack.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        owner_ack_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or ack.get("status")
        or ack.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or ack.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or ack.get("source")
        or owner_ack_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ack.get("safe_evidence_ref")
        or ack.get("evidence_ref", "")
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else ack.get("robot_diagnostics_summary")
        if isinstance(ack.get("robot_diagnostics_summary"), dict)
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
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or ack.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "exists": True,
            "owner_ack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    owner_ack_status.get("reason")
                    or summary_fragment.get("reason")
                    or ack.get("reason")
                    or "field evidence real material owner ack is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "material_group": _redact_route_task_rehearsal_text(
                summary_fragment.get("material_group") or ack.get("material_group") or ""
            ),
            "field_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("field_owner") or ack.get("field_owner") or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by")
                or ack.get("acknowledged_by")
                or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at")
                or ack.get("acknowledged_at")
                or ""
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or ack.get("blocked_reason")
                or owner_ack_status.get("reason")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_steps": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_next_steps")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_phone_copy": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_phone_copy")
                or ack.get("safe_phone_copy")
                or safe_copy
            ),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _field_evidence_real_material_owner_ack_intake_not_proven(
                ack,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    boundary_supported = (
        source_boundary == FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE
    )
    if source_schema not in accepted_schemas or not boundary_supported:
        summary.update(
            {
                "status": "unsupported_schema",
                "owner_ack_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_real_material_owner_ack_intake"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_intake schema or "
                        "evidence boundary is unsupported"
                    ),
                },
                "safe_evidence_ref": "",
                "next_required_evidence": [],
                "owner_next_steps": [],
            }
        )
        return summary
    if raw_schema == FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA and not summary_fragment:
        summary.update(
            {
                "status": "missing_summary",
                "owner_ack_status": {
                    "status": (
                        "blocked_missing_field_evidence_real_material_owner_ack_intake_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_intake artifact is "
                        "missing sanitized summary"
                    ),
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    # 任一 raw/凭证/路径/控制/成功/HIL/pass 线索都降级，确保 diagnostics 只暴露安全回执摘要。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or ack.get("delivery_success") is True
        or ack.get("primary_actions_enabled") is True
        or ack.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _field_evidence_real_material_owner_ack_intake_has_unsafe_fields(ack)
        or _field_evidence_real_material_owner_ack_intake_has_unsafe_fields(
            summary_fragment
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Field evidence real material owner ack intake was blocked because "
            "the summary did not remain source=software_proof/not_proven with "
            "delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_real_material_owner_ack_intake"
                ),
                "owner_ack_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_real_material_owner_ack_intake"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_intake contains "
                        "unsafe fields, success wording, weak evidence_ref, or "
                        "control claims"
                    ),
                },
                "safe_evidence_ref": "",
                "next_required_evidence": [],
                "owner_next_steps": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_real_material_owner_ack_review_decision(source):
    """构建 field-evidence real-material owner ack review decision 的安全 diagnostics 摘要。"""
    # Robot 只镜像已经消毒的 review decision；不读取原始材料、不推进 ACK/控制，也不暗示 PR 关闭。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_real_material_owner_ack_review_decision_summary(
        source_path,
        read_error=(
            "field_evidence_real_material_owner_ack_review_decision summary is not configured"
        ),
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_real_material_owner_ack_review_decision summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            summary["review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_real_material_owner_ack_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision, dict):
        summary["review_status"]["reason"] = (
            "field_evidence_real_material_owner_ack_review_decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_real_material_owner_ack_review_decision_source_contract(
            decision
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision
    else:
        summary_fragment = {}
        for candidate in (
            decision.get("field_evidence_real_material_owner_ack_review_decision_summary"),
            decision.get(
                "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary"
            ),
            decision.get("diagnostics_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("summary"),
            diagnostics.get("field_evidence_real_material_owner_ack_review_decision_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_real_material_owner_ack_review_decision_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    review_status = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else decision.get("review_status")
        if isinstance(decision.get("review_status"), dict)
        else {}
    )
    same_ref_status = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or decision.get("safe_copy")
        or decision.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        review_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or decision.get("status")
        or "not_proven"
    )
    verdict = _redact_route_task_rehearsal_text(
        review_status.get("verdict")
        or summary_fragment.get("verdict")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or decision.get("overall_status")
        or verdict
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or decision.get("source")
        or review_status.get("evidence_source")
        or ""
    )
    source_ref = str(
        decision.get("safe_evidence_ref") or decision.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 固定 false flags 写入 copy，避免下游只读面板把 review accepted 当成主动作可用。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or decision.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "exists": True,
            "review_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    review_status.get("reason")
                    or summary_fragment.get("reason")
                    or decision.get("reason")
                    or "field evidence real material owner ack review decision is software_proof only"
                ),
            },
            "review_decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_decision")
                or summary_fragment.get("decision")
                or decision.get("review_decision")
                or "blocked_missing_owner_ack_review_decision_not_proven"
            ),
            "source_owner_ack_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_ack_schema")
                or FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA
            ),
            "source_owner_ack_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_ack_status")
                or summary_fragment.get("source_owner_ack_summary_status")
                or "blocked"
            ),
            "same_evidence_ref_required": (
                summary_fragment.get("same_evidence_ref_required") is True
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_status)
            or {
                "status": status or "blocked",
                "verdict": "not_proven",
                "reason": "owner ack review decision lacks same evidence_ref status",
            },
            "safe_evidence_ref": safe_evidence_ref,
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "proof_boundary": FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "not_proven": _field_evidence_real_material_owner_ack_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    accepted_schemas = {
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if source_schema not in accepted_schemas or (
        source_boundary != FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "review_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_real_material_owner_ack_review_decision"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_review_decision "
                        "schema or evidence boundary is unsupported"
                    ),
                },
                "safe_evidence_ref": "",
                "decision_reasons": [],
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        raw_schema == FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "missing_summary",
                "review_status": {
                    "status": (
                        "blocked_missing_field_evidence_real_material_owner_ack_review_decision_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_review_decision "
                        "artifact is missing sanitized summary"
                    ),
                },
                "safe_evidence_ref": "",
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": (
                        "evidence_ref_mismatch_field_evidence_real_material_owner_ack_review_decision_blocked"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "owner ack review decision evidence_ref values do not match",
                },
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary

    # 只要 source/verdict/flags/字段消毒不满足约束，就返回固定 blocked 摘要。
    unsafe_payload = (
        not summary_fragment
        or source_value != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or not summary["same_evidence_ref_required"]
        or not summary["decision_reasons"]
        or not summary["next_required_evidence"]
        or not summary["owner_handoff"]
        or decision.get("delivery_success") is True
        or decision.get("primary_actions_enabled") is True
        or decision.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
            decision
        )
        or _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Field evidence real material owner ack review decision was blocked "
            "because the summary did not remain source=software_proof/not_proven "
            "with delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_real_material_owner_ack_review_decision"
                ),
                "review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_real_material_owner_ack_review_decision"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_real_material_owner_ack_review_decision "
                        "contains unsafe fields, success wording, weak evidence_ref, "
                        "or control claims"
                    ),
                },
                "review_decision": "blocked_unsafe_owner_ack_review_decision_not_proven",
                "safe_evidence_ref": "",
                "decision_reasons": [],
                "missing_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_blocker_escalation_pack(source):
    """构建 field-evidence material blocker escalation pack 的安全 diagnostics 摘要。"""
    # Robot 只消费 PC gate 的 sanitized summary；artifact 本体、路径、checksum、控制字段都不能透传。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_material_blocker_escalation_pack_summary(
        source_path,
        read_error=(
            "field_evidence_material_blocker_escalation_pack summary is not configured"
        ),
    )
    if isinstance(source, dict):
        pack = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_blocker_escalation_pack summary artifact missing"
            )
            summary["pack_status"]["reason"] = summary["read_error"]
            summary["pack_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_blocker_escalation_pack "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["pack_status"]["reason"] = safe_error
            return summary

    if not isinstance(pack, dict):
        summary["pack_status"]["reason"] = (
            "field_evidence_material_blocker_escalation_pack JSON must be an object"
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    raw_schema = str(pack.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_blocker_escalation_pack_source_contract(pack)
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA,
    }:
        summary_fragment = pack
    else:
        summary_fragment = {}
        for candidate in (
            pack.get("field_evidence_material_blocker_escalation_pack_summary"),
            pack.get(
                "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary"
            ),
            pack.get("diagnostics_summary"),
            pack.get("robot_diagnostics_summary"),
            pack.get("robot_compatible_summary"),
            pack.get("summary"),
            diagnostics.get("field_evidence_material_blocker_escalation_pack_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_blocker_escalation_pack_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    pack_status = (
        summary_fragment.get("pack_status")
        if isinstance(summary_fragment.get("pack_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else pack.get("pack_status")
        if isinstance(pack.get("pack_status"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("field_safe_copy")
        or summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or pack.get("field_safe_copy")
        or pack.get("safe_copy")
        or pack.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    status = _redact_route_task_rehearsal_text(
        pack_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or pack.get("status")
        or "not_proven"
    )
    verdict = _redact_route_task_rehearsal_text(
        pack_status.get("verdict")
        or summary_fragment.get("verdict")
        or summary_fragment.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or pack.get("overall_status")
        or verdict
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or pack.get("source")
        or pack_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or pack.get("safe_evidence_ref")
        or pack.get("evidence_ref", "")
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游面板可能只展示 copy；这里补齐 false flags，避免升级包被误读为控制入口。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or pack.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "exists": True,
            "pack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    pack_status.get("reason")
                    or summary_fragment.get("reason")
                    or pack.get("reason")
                    or (
                        "field evidence material blocker escalation pack is "
                        "software_proof only"
                    )
                ),
            },
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or pack.get("blocked_reason")
                or pack_status.get("reason")
                or ""
            ),
            "target_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("target_owner") or pack.get("target_owner") or ""
            ),
            "owner_escalation_level": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_escalation_level")
                or summary_fragment.get("escalation_level")
                or pack.get("owner_escalation_level")
                or pack.get("escalation_level")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "field_safe_copy": safe_copy_text,
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "not_proven": _field_evidence_material_blocker_escalation_pack_not_proven(
                pack,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    accepted_schemas = {
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary != FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "pack_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_material_blocker_escalation_pack"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_material_blocker_escalation_pack schema "
                        "or evidence boundary is unsupported"
                    ),
                },
                "safe_evidence_ref": "",
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        raw_schema == FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "missing_summary",
                "pack_status": {
                    "status": (
                        "blocked_missing_field_evidence_material_blocker_escalation_pack_summary"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_material_blocker_escalation_pack artifact "
                        "is missing sanitized summary"
                    ),
                },
                "safe_evidence_ref": "",
            }
        )
        return summary
    unsafe_payload = (
        not summary_fragment
        or source_value != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or not summary["next_required_evidence"]
        or pack.get("delivery_success") is True
        or pack.get("primary_actions_enabled") is True
        or pack.get("safe_to_control") is True
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(pack)
        or _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_blocker_escalation_pack_has_unsafe_fields(
            robot_summary
        )
    )
    if unsafe_payload:
        blocked_copy = (
            "Field evidence material blocker escalation pack was blocked because "
            "the summary did not remain source=software_proof/not_proven with "
            "delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_field_evidence_material_blocker_escalation_pack",
                "pack_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_blocker_escalation_pack"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "field_evidence_material_blocker_escalation_pack contains "
                        "unsafe fields, success wording, weak evidence_ref, or "
                        "control claims"
                    ),
                },
                "safe_evidence_ref": "",
                "next_required_evidence": [],
                "owner_handoff": [],
                "field_safe_copy": blocked_copy,
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_intake(source):
    """构建 field evidence material resolution intake 的 Robot-safe 摘要。"""
    # Robot 只接 PC/Autonomy 产出的 sanitized summary；raw artifact 即使命中 schema 也必须降级为 blocked。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_material_resolution_intake_summary(
        source_path,
        read_error=(
            "field_evidence_material_resolution_intake summary is not configured"
        ),
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_intake summary artifact missing"
            )
            summary["resolution_status"]["reason"] = summary["read_error"]
            summary["resolution_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["resolution_status"]["reason"] = safe_error
            return summary

    if not isinstance(intake, dict):
        summary["resolution_status"]["reason"] = (
            "field_evidence_material_resolution_intake JSON must be an object"
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    raw_schema = str(intake.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_intake_source_contract(intake)
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = intake
    else:
        summary_fragment = {}
        for candidate in (
            intake.get("field_evidence_material_resolution_intake_summary"),
            intake.get(
                "robot_diagnostics_field_evidence_material_resolution_intake_summary"
            ),
            intake.get("diagnostics_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("summary"),
            diagnostics.get("field_evidence_material_resolution_intake_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_intake_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_source = (
        summary_fragment.get("resolution_status")
        if isinstance(summary_fragment.get("resolution_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游可能直接展示 copy；这里强制补齐 false-state 边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("decision")
        or status_source.get("decision")
        or status_source.get("status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or intake.get("safe_evidence_ref")
        or intake.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or intake.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "decision": decision,
            "status": _redact_route_task_rehearsal_text(
                status_source.get("status") or decision
            ),
            "overall_status": "not_proven",
            "resolution_status": {
                "status": _redact_route_task_rehearsal_text(
                    status_source.get("status") or decision
                ),
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_source.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence material resolution intake is "
                        "software_proof only"
                    )
                ),
            },
            "accepted_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_summary")
                or summary_fragment.get("accepted")
            ),
            "missing_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_summary") or summary_fragment.get("missing")
            ),
            "rejected_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_summary")
                or summary_fragment.get("rejected")
            ),
            "blocked_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_summary") or summary_fragment.get("blocked")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": decision,
            },
            "not_proven": _field_evidence_material_resolution_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        decision in FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_DECISIONS,
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_intake_has_unsafe_fields(item)
        for item in (
            status_source,
            summary["accepted_summary"],
            summary["missing_summary"],
            summary["rejected_summary"],
            summary["blocked_summary"],
            summary["next_required_evidence"],
            summary["owner_handoff"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["resolution_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_intake_summary"
        )
        summary["status"] = summary["resolution_status"]["status"]
        return summary
    if (
        source_schema != FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE
    ):
        summary["resolution_status"] = {
            "status": "blocked_unsupported_field_evidence_material_resolution_intake",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "field evidence material resolution intake schema or boundary is unsupported",
        }
        summary["status"] = summary["resolution_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["resolution_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_intake"
        )
        summary["resolution_status"]["reason"] = (
            "field evidence material resolution intake must remain software_proof"
        )
        summary["status"] = summary["resolution_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["resolution_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_intake_materials"
        )
        summary["resolution_status"]["reason"] = (
            "field evidence material resolution intake is missing required safe metadata"
        )
        summary["status"] = summary["resolution_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_intake_has_unsafe_fields(intake)
        or _field_evidence_material_resolution_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution intake was blocked because "
            "summary fields could expose raw artifacts, credentials, ACK/cursor data, "
            "checksums, control data, paths, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "decision": "blocked",
                "status": "blocked_unsafe_field_evidence_material_resolution_intake",
                "resolution_status": {
                    "status": "blocked_unsafe_field_evidence_material_resolution_intake",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "unsafe raw artifact, credential, ACK/cursor, checksum, control, path, or success material",
                },
                "accepted_summary": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_review_decision(source):
    """构建 field evidence material resolution review decision 的 Robot-safe 摘要。"""
    # Robot 只转发 PC/Autonomy 的 sanitized review-decision summary；raw artifact 只能作为 wrapper。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_material_resolution_review_decision_summary(
        source_path,
        read_error=(
            "field_evidence_material_resolution_review_decision summary is not configured"
        ),
    )
    if isinstance(source, dict):
        decision_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_review_decision summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            summary["review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_status"]["reason"] = (
            "field_evidence_material_resolution_review_decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_review_decision_source_contract(
            decision_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "field_evidence_material_resolution_review_decision_summary"
            ),
            decision_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_review_decision_summary"
            ),
            decision_doc.get("diagnostics_summary"),
            decision_doc.get("robot_diagnostics_summary"),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_review_decision_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_review_decision_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    review_status = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游可能直接展示 copy；这里强制补齐 false-state 边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("decision")
        or review_status.get("decision")
        or review_status.get("status")
        or "blocked_missing_resolution_intake_not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or decision_doc.get("safe_evidence_ref")
        or decision_doc.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        summary_fragment.get("reason")
        or review_status.get("reason")
        or "field evidence material resolution review decision is software_proof only"
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "decision": decision,
            "status": decision,
            "overall_status": "not_proven",
            "review_status": {
                "status": decision,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": reason,
            },
            "reason": reason,
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_review_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_review_handoff")
                or summary_fragment.get("owner_handoff")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": decision,
            },
            "not_proven": _field_evidence_material_resolution_review_decision_not_proven(
                decision_doc,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        decision in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_DECISIONS,
        bool(summary["next_required_evidence"]),
        bool(summary["owner_review_handoff"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_review_decision_has_unsafe_fields(item)
        for item in (
            review_status,
            summary["next_required_evidence"],
            summary["owner_review_handoff"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_review_decision_summary"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        source_schema != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SCHEMA
        or source_boundary != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE
    ):
        summary["review_status"] = {
            "status": "blocked_unsupported_field_evidence_material_resolution_review_decision",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "field evidence material resolution review decision schema or boundary is unsupported",
        }
        summary["status"] = summary["review_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["review_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_review_decision"
        )
        summary["review_status"]["reason"] = (
            "field evidence material resolution review decision must remain software_proof"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_review_decision_materials"
        )
        summary["review_status"]["reason"] = (
            "field evidence material resolution review decision is missing required safe metadata"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _field_evidence_material_resolution_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution review decision was blocked because "
            "summary fields could expose unsafe artifacts, credentials, ACK/cursor data, "
            "checksums, control data, paths, or truthy success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "decision": "rejected_unsafe_resolution_not_proven",
                "status": "blocked_unsafe_field_evidence_material_resolution_review_decision",
                "review_status": {
                    "status": "blocked_unsafe_field_evidence_material_resolution_review_decision",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "unsafe artifact, credential, ACK/cursor, checksum, control, path, or success material",
                },
                "safe_evidence_ref": "",
                "next_required_evidence": [],
                "owner_review_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "rejected_unsafe_resolution_not_proven",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_review_handoff(source):
    """构建 field evidence material resolution review handoff 的 Robot-safe 摘要。"""
    # Robot 侧只重新发布 handoff 安全摘要，不执行 owner action、ACK 或任何控制命令。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_field_evidence_material_resolution_review_handoff_summary(
        source_path,
        read_error=(
            "field_evidence_material_resolution_review_handoff summary is not configured"
        ),
    )
    if isinstance(source, dict):
        handoff_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_review_handoff summary artifact missing"
            )
            summary["handoff_review_status"]["reason"] = summary["read_error"]
            summary["handoff_review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_review_handoff "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["handoff_review_status"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["handoff_review_status"]["reason"] = (
            "field_evidence_material_resolution_review_handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_review_handoff_source_contract(handoff_doc)
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get("field_evidence_material_resolution_review_handoff_summary"),
            handoff_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary"
            ),
            handoff_doc.get("diagnostics_summary"),
            handoff_doc.get("robot_diagnostics_summary"),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_review_handoff_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    handoff_status_doc = (
        summary_fragment.get("handoff_review_status")
        if isinstance(summary_fragment.get("handoff_review_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # copy 可能直接被下游展示，因此这里强制写入 false-state 证明边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    handoff_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("handoff_status")
        or handoff_status_doc.get("handoff_status")
        or handoff_status_doc.get("status")
        or "blocked_missing_review_decision_not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or handoff_doc.get("safe_evidence_ref")
        or handoff_doc.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        summary_fragment.get("reason")
        or handoff_status_doc.get("reason")
        or "field evidence material resolution review handoff is software_proof only"
    )
    previous_review_decision_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("previous_review_decision_ref")
        or handoff_doc.get("previous_review_decision_ref")
    )
    previous_review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("previous_review_decision")
        or handoff_doc.get("previous_review_decision")
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "handoff_status": handoff_status,
            "status": handoff_status,
            "overall_status": "not_proven",
            "handoff_review_status": {
                "status": handoff_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": reason,
            },
            "previous_review_decision_ref": previous_review_decision_ref,
            "previous_review_decision": previous_review_decision,
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
            ),
            "rejected_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_material_refs")
            ),
            "missing_required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_materials")
            ),
            "owner_handoff_role": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_handoff_role")
            ),
            "owner_next_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_action")
            ),
            "next_required_real_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_real_evidence")
                or summary_fragment.get("next_required_evidence")
            ),
            "blocked_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_categories")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": handoff_status,
            },
            "not_proven": _field_evidence_material_resolution_review_handoff_not_proven(
                handoff_doc,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        handoff_status
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_STATUSES,
        bool(summary["previous_review_decision_ref"]),
        bool(summary["previous_review_decision"]),
        bool(summary["owner_handoff_role"]),
        bool(summary["owner_next_action"]),
        bool(summary["next_required_real_evidence"]),
        bool(summary["blocked_categories"]),
    )
    required_blocked_categories = {
        "external_cloud",
        "terminal_result",
        "phone_browser",
        "field_route_elevator",
        "hardware_hil",
        "pr5",
    }
    blocked_categories = {
        _redact_route_task_rehearsal_text(item).strip().lower()
        for item in summary["blocked_categories"]
    }
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_review_handoff_has_unsafe_fields(item)
        for item in (
            handoff_status_doc,
            summary["accepted_material_refs"],
            summary["rejected_material_refs"],
            summary["missing_required_materials"],
            summary["next_required_real_evidence"],
            summary["blocked_categories"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["handoff_review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_review_handoff_summary"
        )
        summary["status"] = summary["handoff_review_status"]["status"]
        return summary
    if (
        source_schema != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SCHEMA
        or source_boundary != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE
    ):
        summary["handoff_review_status"] = {
            "status": "blocked_unsupported_field_evidence_material_resolution_review_handoff",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "field evidence material resolution review handoff schema or boundary is unsupported",
        }
        summary["status"] = summary["handoff_review_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["handoff_review_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_review_handoff"
        )
        summary["handoff_review_status"]["reason"] = (
            "field evidence material resolution review handoff must remain software_proof"
        )
        summary["status"] = summary["handoff_review_status"]["status"]
        return summary
    if (
        not all(required_safe_metadata)
        or not required_blocked_categories.issubset(blocked_categories)
    ):
        summary["handoff_review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_review_handoff_materials"
        )
        summary["handoff_review_status"]["reason"] = (
            "field evidence material resolution review handoff is missing required safe metadata"
        )
        summary["status"] = summary["handoff_review_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_review_handoff_has_unsafe_fields(
            handoff_doc
        )
        or _field_evidence_material_resolution_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution review handoff was blocked because "
            "summary fields could expose unsafe artifacts, credentials, ACK/cursor data, "
            "checksums, control data, paths, readiness, or truthy success wording; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": "blocked_unsafe_handoff_not_proven",
                "status": "blocked_unsafe_field_evidence_material_resolution_review_handoff",
                "handoff_review_status": {
                    "status": "blocked_unsafe_field_evidence_material_resolution_review_handoff",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "unsafe artifact, credential, ACK/cursor, checksum, control, path, readiness, or success material",
                },
                "safe_evidence_ref": "",
                "previous_review_decision_ref": "",
                "previous_review_decision": "",
                "accepted_material_refs": [],
                "rejected_material_refs": [],
                "missing_required_materials": [],
                "owner_handoff_role": "",
                "owner_next_action": "",
                "next_required_real_evidence": [],
                "blocked_categories": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked_unsafe_handoff_not_proven",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_followup_escalation_status(source):
    """构建 field evidence material resolution follow-up escalation 的 Robot-safe 摘要。"""
    # Robot 只发布 owner response 缺口状态；不能把 escalate/pending 转成 readiness 或控制许可。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_followup_escalation_status_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_followup_escalation_status "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        followup_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_followup_escalation_status "
                "summary artifact missing"
            )
            summary["followup_review_status"]["reason"] = summary["read_error"]
            summary["followup_review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_followup_escalation_status "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_review_status"]["reason"] = safe_error
            return summary

    if not isinstance(followup_doc, dict):
        summary["followup_review_status"]["reason"] = (
            "field_evidence_material_resolution_followup_escalation_status JSON must be an object"
        )
        return summary

    diagnostics = (
        followup_doc.get("diagnostics")
        if isinstance(followup_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(followup_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_followup_escalation_status_source_contract(
            followup_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        summary_fragment = followup_doc
    else:
        summary_fragment = {}
        for candidate in (
            followup_doc.get(
                "field_evidence_material_resolution_followup_escalation_status_summary"
            ),
            followup_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary"
            ),
            followup_doc.get("diagnostics_summary"),
            followup_doc.get("robot_diagnostics_summary"),
            followup_doc.get("robot_compatible_summary"),
            followup_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_followup_escalation_status_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_followup_escalation_status_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("followup_review_status")
        if isinstance(summary_fragment.get("followup_review_status"), dict)
        else summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
        else summary_fragment.get("escalation_status")
        if isinstance(summary_fragment.get("escalation_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # copy 是下游 UI 直接展示字段，因此强制追加软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false; owner response material missing."
        )
    followup_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), str)
        else status_doc.get("status")
        or summary_fragment.get("status")
        or "pending_owner_response_not_proven"
    )
    owner_response_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("owner_response_material_status")
        or followup_doc.get("owner_response_material_status")
        or "missing"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup_doc.get("safe_evidence_ref")
        or followup_doc.get("evidence_ref", "")
    )
    reason = _redact_route_task_rehearsal_text(
        summary_fragment.get("reason")
        or status_doc.get("reason")
        or "owner response material is still missing or pending"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or followup_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "followup_status": followup_status,
            "status": followup_status,
            "overall_status": "not_proven",
            "followup_review_status": {
                "status": followup_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": reason,
            },
            "previous_handoff_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_handoff_ref")
                or followup_doc.get("previous_handoff_ref")
            ),
            "previous_review_decision_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_review_decision_ref")
                or followup_doc.get("previous_review_decision_ref")
            ),
            "owner_response_material_status": owner_response_status,
            "due_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("due_status") or followup_doc.get("due_status")
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or followup_doc.get("blocked_reason")
                or reason
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action")
                or summary_fragment.get("owner_next_action")
                or followup_doc.get("owner_action")
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation")
                or followup_doc.get("ceo_escalation_recommendation")
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id")
                or followup_doc.get("pr5_thread_id")
                or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state")
                or followup_doc.get("pr5_thread_state")
                or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or followup_doc.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id")
                or followup_doc.get("pr5_reply_comment_id")
                or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or followup_doc.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": followup_status,
            },
            "not_proven": (
                _field_evidence_material_resolution_followup_escalation_status_not_proven(
                    followup_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        followup_status
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUSES,
        owner_response_status in {"missing", "pending", "escalate"},
        bool(summary["previous_handoff_ref"]),
        bool(summary["previous_review_decision_ref"]),
        bool(summary["due_status"]),
        bool(summary["blocked_reason"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        bool(summary["ceo_escalation_recommendation"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["next_required_evidence"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["followup_review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_followup_escalation_status_summary"
        )
        summary["status"] = summary["followup_review_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary["followup_review_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_followup_escalation_status"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": (
                "field evidence material resolution follow-up escalation status "
                "schema or boundary is unsupported"
            ),
        }
        summary["status"] = summary["followup_review_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["followup_review_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_followup_escalation_status"
        )
        summary["followup_review_status"]["reason"] = (
            "field evidence material resolution follow-up escalation status must remain software_proof"
        )
        summary["status"] = summary["followup_review_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["followup_review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_followup_escalation_status_materials"
        )
        summary["followup_review_status"]["reason"] = (
            "field evidence material resolution follow-up escalation status is missing required safe metadata"
        )
        summary["status"] = summary["followup_review_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
            followup_doc
        )
        or _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution follow-up escalation status was "
            "blocked because summary fields could expose unsafe artifacts, raw "
            "GitHub data, credentials, ROS topics, serial/UART details, WAVE ROVER "
            "parameters, readiness, reviewer resolution, or truthy success/control "
            "wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "followup_status": "blocked_unsafe_followup_escalation_not_proven",
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_followup_escalation_status"
                ),
                "followup_review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_followup_escalation_status"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe artifact, raw GitHub, credential, ROS topic, "
                        "serial/UART, WAVE ROVER, readiness, reviewer-resolution, "
                        "control, path, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "previous_handoff_ref": "",
                "previous_review_decision_ref": "",
                "owner_response_material_status": "missing",
                "due_status": "",
                "blocked_reason": "",
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked_unsafe_followup_escalation_not_proven",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_owner_response_intake(source):
    """构建 field evidence material resolution owner response intake 的 Robot-safe 摘要。"""
    # Robot 只展示 PC safe summary；owner response 的状态绝不能转成 readiness、控制授权或 review acceptance。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_owner_response_intake_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_owner_response_intake "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        response_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_owner_response_intake "
                "summary artifact missing"
            )
            summary["owner_response_status"]["reason"] = summary["read_error"]
            summary["owner_response_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_owner_response_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["owner_response_status"]["reason"] = safe_error
            return summary

    if not isinstance(response_doc, dict):
        summary["owner_response_status"]["reason"] = (
            "field_evidence_material_resolution_owner_response_intake JSON must be an object"
        )
        return summary

    diagnostics = (
        response_doc.get("diagnostics")
        if isinstance(response_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(response_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_owner_response_intake_source_contract(
            response_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = response_doc
    else:
        summary_fragment = {}
        for candidate in (
            response_doc.get(
                "field_evidence_material_resolution_owner_response_intake_summary"
            ),
            response_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary"
            ),
            response_doc.get("diagnostics_summary"),
            response_doc.get("robot_diagnostics_summary"),
            response_doc.get("robot_compatible_summary"),
            response_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_owner_response_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_owner_response_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("owner_response_status")
        if isinstance(summary_fragment.get("owner_response_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    raw_source_bridge = str(
        summary_fragment.get("source_bridge")
        or summary_fragment.get("source_bridge_marker")
        or ""
    ).strip()
    # reviewer ACK bridge 只能暴露固定安全标记；不允许透传 raw source artifact/path。
    source_bridge = (
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_REVIEWER_ACK_BRIDGE
        if raw_source_bridge
        == FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_REVIEWER_ACK_BRIDGE
        else ""
    )
    source_reviewer_ack_followup_status = (
        summary_fragment.get("source_reviewer_ack_followup_status")
        if isinstance(summary_fragment.get("source_reviewer_ack_followup_status"), dict)
        else summary_fragment.get("source_followup_status")
        if isinstance(summary_fragment.get("source_followup_status"), dict)
        else summary_fragment.get("reviewer_ack_followup_status")
        if isinstance(summary_fragment.get("reviewer_ack_followup_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 是下游直接展示面，必须显式带上软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or response_doc.get("safe_evidence_ref")
        or response_doc.get("evidence_ref", "")
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "status": status,
            "overall_status": "not_proven",
            "owner_response_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence material resolution owner response "
                        "intake is software_proof only"
                    )
                ),
            },
            "source_bridge": source_bridge,
            "source_reviewer_ack_followup_status": _safe_pc_route_debug_dict(
                source_reviewer_ack_followup_status
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                or summary_fragment.get("accepted_summary")
                or summary_fragment.get("accepted")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                or summary_fragment.get("missing_summary")
                or summary_fragment.get("missing")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                or summary_fragment.get("rejected_summary")
                or summary_fragment.get("rejected")
            ),
            "unsafe_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials_summary")
                or summary_fragment.get("unsafe_summary")
                or summary_fragment.get("unsafe")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "operator_support_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("owner_handoff")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "not_proven": (
                _field_evidence_material_resolution_owner_response_intake_not_proven(
                    response_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        status in FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_STATUSES,
        bool(summary["next_required_evidence"]),
        bool(summary["operator_support_handoff"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    reviewer_ack_bridge_source = (
        bool(source_bridge)
        and source_schema
        == FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        and source_boundary
        == FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
    )
    owner_response_intake_source = (
        source_schema == FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SCHEMA
        and source_boundary == FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE
    )
    unsafe_material = any(
        _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            raw_source_bridge,
            source_reviewer_ack_followup_status,
            summary["accepted_materials_summary"],
            summary["missing_materials_summary"],
            summary["rejected_materials_summary"],
            summary["unsafe_materials_summary"],
            summary["next_required_evidence"],
            summary["operator_support_handoff"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["owner_response_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_intake_summary"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if raw_source_bridge and not source_bridge:
        summary["owner_response_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_owner_response_intake"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": (
                "field evidence material resolution owner response intake source bridge "
                "marker is unsupported"
            ),
        }
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if not (owner_response_intake_source or reviewer_ack_bridge_source):
        summary["owner_response_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_owner_response_intake"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": (
                "field evidence material resolution owner response intake schema "
                "or boundary is unsupported"
            ),
        }
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["owner_response_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_owner_response_intake"
        )
        summary["owner_response_status"]["reason"] = (
            "field evidence material resolution owner response intake must remain software_proof"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["owner_response_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_intake_materials"
        )
        summary["owner_response_status"]["reason"] = (
            "field evidence material resolution owner response intake is missing required safe metadata"
        )
        summary["status"] = summary["owner_response_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("review_acceptance_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
            response_doc
        )
        or _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution owner response intake was blocked "
            "because summary fields could expose raw artifacts, raw GitHub data, "
            "credentials, DB/queue or OSS secrets, ROS topics, /cmd_vel, serial/UART "
            "details, WAVE ROVER parameters, tracebacks, checksums, readiness, review "
            "acceptance, or truthy success/control wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_owner_response_intake"
                ),
                "owner_response_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_owner_response_intake"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw artifact, raw GitHub, credential, DB/queue, OSS, "
                        "ROS topic, serial/UART, WAVE ROVER, traceback, checksum, "
                        "readiness, review acceptance, control, path, or success material"
                    ),
                },
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "next_required_evidence": [],
                "operator_support_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_owner_response_review_decision(
    source,
):
    """构建 owner-response review-decision 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 PC safe summary；review decision 不能变成 readiness、控制授权或真实材料验收。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_owner_response_review_decision_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_owner_response_review_decision "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        decision_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_owner_response_review_decision "
                "summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            summary["review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_owner_response_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_status"]["reason"] = (
            "field_evidence_material_resolution_owner_response_review_decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_owner_response_review_decision_source_contract(
            decision_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "field_evidence_material_resolution_owner_response_review_decision_summary"
            ),
            decision_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary"
            ),
            decision_doc.get("diagnostics_summary"),
            decision_doc.get("robot_diagnostics_summary"),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_owner_response_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_owner_response_review_decision_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("decision_status")
        if isinstance(summary_fragment.get("decision_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游 UI 可能只显示 safe_copy，因此这里强制写入 software_proof 与三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision_doc.get("review_decision")
        or decision_doc.get("decision")
        or "blocked_missing_owner_response_intake_not_proven"
    )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status") or summary_fragment.get("status") or review_decision
    )
    source_ref = str(
        decision_doc.get("safe_evidence_ref") or decision_doc.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "review_decision": review_decision,
            "status": status,
            "overall_status": "not_proven",
            "review_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence material resolution owner response review "
                        "decision is software_proof only"
                    )
                ),
            },
            "source_owner_response_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or summary_fragment.get("source_owner_response_intake_status")
                or "blocked"
            ),
            "previous_owner_response_intake_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_owner_response_intake_ref")
                or summary_fragment.get("source_owner_response_ref")
                or ""
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action") or ""
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation") or ""
            ),
            "review_handoff_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_handoff_recommendation") or ""
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state") or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id") or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "not_proven": (
                _field_evidence_material_resolution_owner_response_review_decision_not_proven(
                    decision_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        review_decision
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISIONS,
        bool(summary["decision_reasons"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        bool(summary["ceo_escalation_recommendation"]),
        bool(summary["review_handoff_recommendation"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["decision_reasons"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["unsafe_materials"],
            summary["next_required_evidence"],
            summary["owner_action"],
            summary["ceo_escalation_recommendation"],
            summary["review_handoff_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_review_decision_summary"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE
    ):
        summary["review_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_owner_response_review_decision"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": (
                "field evidence material resolution owner response review decision "
                "schema or boundary is unsupported"
            ),
        }
        summary["status"] = summary["review_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["review_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_owner_response_review_decision"
        )
        summary["review_status"]["reason"] = (
            "field evidence material resolution owner response review decision must remain software_proof"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_review_decision_materials"
        )
        summary["review_status"]["reason"] = (
            "field evidence material resolution owner response review decision is missing required safe metadata"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution owner response review decision was "
            "blocked because the source included unsafe material, reviewer-resolution "
            "claims, owner-material acceptance claims, or truthy success/control "
            "wording; sensitive implementation details were redacted; "
            "safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_owner_response_review_decision"
                ),
                "review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_owner_response_review_decision"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe source material, readiness, reviewer resolution, "
                        "owner-material acceptance, control, path, or success material"
                    ),
                },
                "review_decision": (
                    "blocked_missing_owner_response_intake_not_proven"
                ),
                "safe_evidence_ref": "",
                "previous_owner_response_intake_ref": "",
                "decision_reasons": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "review_handoff_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_owner_response_review_handoff(
    source,
):
    """构建 owner-response review-handoff 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 PC safe summary；handoff 不能变成 readiness、ACK、回放、控制或真实材料验收。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_owner_response_review_handoff_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_owner_response_review_handoff "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        handoff_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_owner_response_review_handoff "
                "summary artifact missing"
            )
            summary["review_handoff_status"]["reason"] = summary["read_error"]
            summary["review_handoff_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_owner_response_review_handoff "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_handoff_status"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["review_handoff_status"]["reason"] = (
            "field_evidence_material_resolution_owner_response_review_handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_owner_response_review_handoff_source_contract(
            handoff_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get(
                "field_evidence_material_resolution_owner_response_review_handoff_summary"
            ),
            handoff_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary"
            ),
            handoff_doc.get("diagnostics_summary"),
            handoff_doc.get("robot_diagnostics_summary"),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_owner_response_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_owner_response_review_handoff_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("review_handoff_status")
        if isinstance(summary_fragment.get("review_handoff_status"), dict)
        else summary_fragment.get("handoff_status_summary")
        if isinstance(summary_fragment.get("handoff_status_summary"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 是手机/Robot 直显文本，必须显式携带软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    handoff_status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked_missing_owner_response_review_handoff_not_proven"
    )
    source_ref = str(
        handoff_doc.get("safe_evidence_ref") or handoff_doc.get("evidence_ref") or ""
    ).strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ""
    ).strip()
    safe_evidence_ref = _safe_route_task_rehearsal_ref(summary_ref or source_ref)
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "handoff_status": handoff_status,
            "status": handoff_status,
            "overall_status": "not_proven",
            "review_handoff_status": {
                "status": handoff_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence material resolution owner response review "
                        "handoff is software_proof only"
                    )
                ),
            },
            "source_owner_response_review_decision_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_review_decision_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA
            ),
            "source_owner_response_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_review_decision_status")
                or summary_fragment.get("source_review_decision_status")
                or "blocked"
            ),
            "previous_owner_response_review_decision_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_owner_response_review_decision_ref")
                or summary_fragment.get("source_owner_response_review_decision_ref")
                or ""
            ),
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "handoff_targets": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_targets")
                or summary_fragment.get("operator_support_handoff")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action") or ""
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation") or ""
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state") or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id") or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": handoff_status,
            },
            "not_proven": (
                _field_evidence_material_resolution_owner_response_review_handoff_not_proven(
                    handoff_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        handoff_status
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES,
        bool(summary["handoff_reasons"]),
        bool(summary["handoff_targets"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        bool(summary["ceo_escalation_recommendation"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["handoff_reasons"],
            summary["handoff_targets"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["unsafe_materials"],
            summary["next_required_evidence"],
            summary["owner_action"],
            summary["ceo_escalation_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_review_handoff_summary"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
    ):
        summary["review_handoff_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_owner_response_review_handoff"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": (
                "field evidence material resolution owner response review handoff "
                "schema or boundary is unsupported"
            ),
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["review_handoff_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_owner_response_review_handoff"
        )
        summary["review_handoff_status"]["reason"] = (
            "field evidence material resolution owner response review handoff must remain software_proof"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_owner_response_review_handoff_materials"
        )
        summary["review_handoff_status"]["reason"] = (
            "field evidence material resolution owner response review handoff is missing required safe metadata"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
            handoff_doc
        )
        or _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution owner response review handoff was "
            "blocked because the source included unsafe material, reviewer-resolution "
            "claims, owner-material acceptance claims, ACK/cursor/replay/resubmit "
            "claims, or truthy success/control wording; sensitive implementation "
            "details were redacted; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": (
                    "blocked_unsafe_owner_response_review_handoff_not_proven"
                ),
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_owner_response_review_handoff"
                ),
                "review_handoff_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_owner_response_review_handoff"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe artifact, raw GitHub, credential, ROS topic, serial/UART, "
                        "WAVE ROVER, reviewer-resolution, owner-material acceptance, "
                        "ACK/cursor/replay/resubmit, control, path, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "previous_owner_response_review_decision_ref": "",
                "handoff_reasons": [],
                "handoff_targets": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked_unsafe_owner_response_review_handoff_not_proven",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_reviewer_ack_intake(source):
    """构建 reviewer ACK intake 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 phone-safe ACK 摘要；这里不新增 ACK 写入、cursor 写入、回放、重提或控制入口。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_reviewer_ack_intake_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_reviewer_ack_intake "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        ack_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_reviewer_ack_intake "
                "summary artifact missing"
            )
            summary["reviewer_ack_status"]["reason"] = summary["read_error"]
            summary["reviewer_ack_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                ack_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_reviewer_ack_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reviewer_ack_status"]["reason"] = safe_error
            return summary

    if not isinstance(ack_doc, dict):
        summary["reviewer_ack_status"]["reason"] = (
            "field_evidence_material_resolution_reviewer_ack_intake JSON must be an object"
        )
        return summary

    diagnostics = (
        ack_doc.get("diagnostics")
        if isinstance(ack_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(ack_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_reviewer_ack_intake_source_contract(
            ack_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = ack_doc
    else:
        summary_fragment = {}
        for candidate in (
            ack_doc.get(
                "field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            ack_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            ack_doc.get("diagnostics_summary"),
            ack_doc.get("robot_diagnostics_summary"),
            ack_doc.get("robot_compatible_summary"),
            ack_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_reviewer_ack_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("reviewer_ack_status")
        if isinstance(summary_fragment.get("reviewer_ack_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 是下游直显文本，必须固定写入 software_proof 与三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("status")
        or "blocked_not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or ack_doc.get("safe_evidence_ref")
        or ack_doc.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or ack_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "status": status,
            "overall_status": "not_proven",
            "reviewer_ack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "reviewer ACK intake is software_proof only"
                ),
            },
            "source_owner_response_review_handoff_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_review_handoff_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA
            ),
            "source_owner_response_review_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_review_handoff_status")
                or "blocked"
            ),
            "previous_owner_response_review_handoff_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_owner_response_review_handoff_ref")
                or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by") or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at") or ""
            ),
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action") or ""
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation") or ""
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state") or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id") or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "not_proven": (
                _field_evidence_material_resolution_reviewer_ack_intake_not_proven(
                    ack_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        status in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_STATUSES,
        bool(summary["acknowledged_by"]),
        bool(summary["ack_reasons"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["ack_reasons"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["unsafe_materials"],
            summary["next_required_evidence"],
            summary["owner_action"],
            summary["ceo_escalation_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["reviewer_ack_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_intake_summary"
        )
        summary["status"] = summary["reviewer_ack_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE
    ):
        summary["reviewer_ack_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_intake"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK intake schema or boundary is unsupported",
        }
        summary["status"] = summary["reviewer_ack_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["reviewer_ack_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_intake"
        )
        summary["reviewer_ack_status"]["reason"] = (
            "reviewer ACK intake must remain software_proof"
        )
        summary["status"] = summary["reviewer_ack_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["reviewer_ack_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_intake_materials"
        )
        summary["reviewer_ack_status"]["reason"] = (
            "reviewer ACK intake is missing required safe metadata"
        )
        summary["status"] = summary["reviewer_ack_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
            ack_doc
        )
        or _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution reviewer ack intake was blocked "
            "because source material could imply reviewer resolution, owner-material "
            "acceptance, ACK/cursor mutation, replay/resubmit, robot control, raw "
            "diagnostics, hardware details, or success; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_intake"
                ),
                "reviewer_ack_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_intake"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe reviewer resolution, owner-material acceptance, "
                        "ACK/cursor mutation, replay/resubmit, control, path, "
                        "hardware, raw, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "previous_owner_response_review_handoff_ref": "",
                "acknowledged_by": "",
                "acknowledged_at": "",
                "ack_reasons": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_reviewer_ack_review_decision(source):
    """构建 reviewer ACK review-decision 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 Autonomy safe summary；这里不暴露 raw ACK、GitHub payload 或任何控制入口。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_reviewer_ack_review_decision_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_reviewer_ack_review_decision "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        decision_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_reviewer_ack_review_decision "
                "summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            summary["review_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_reviewer_ack_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_status"]["reason"] = (
            "field_evidence_material_resolution_reviewer_ack_review_decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_reviewer_ack_review_decision_source_contract(
            decision_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            decision_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            decision_doc.get("diagnostics_summary"),
            decision_doc.get("robot_diagnostics_summary"),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_reviewer_ack_review_decision_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("decision_status")
        if isinstance(summary_fragment.get("decision_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 可能直达手机面板，必须补齐 software_proof 与三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or decision_doc.get("review_decision")
        or decision_doc.get("decision")
        or "blocked_missing_reviewer_ack_intake_not_proven"
    )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status") or summary_fragment.get("status") or review_decision
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or decision_doc.get("safe_evidence_ref")
        or decision_doc.get("evidence_ref", "")
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "review_decision": review_decision,
            "status": status,
            "overall_status": "not_proven",
            "review_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "reviewer ACK review decision is software_proof only"
                ),
            },
            "source_reviewer_ack_intake_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_intake_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA
            ),
            "source_reviewer_ack_intake_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_intake_status")
                or summary_fragment.get("source_reviewer_ack_status")
                or "blocked"
            ),
            "previous_reviewer_ack_intake_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_reviewer_ack_intake_ref")
                or summary_fragment.get("source_reviewer_ack_intake_ref")
                or ""
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action") or ""
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation") or ""
            ),
            "review_handoff_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_handoff_recommendation") or ""
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state") or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id") or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "not_proven": (
                _field_evidence_material_resolution_reviewer_ack_review_decision_not_proven(
                    decision_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        review_decision
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISIONS,
        bool(summary["decision_reasons"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["decision_reasons"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["unsafe_materials"],
            summary["next_required_evidence"],
            summary["owner_action"],
            summary["ceo_escalation_recommendation"],
            summary["review_handoff_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_review_decision_summary"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE
    ):
        summary["review_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_review_decision"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK review decision schema or boundary is unsupported",
        }
        summary["status"] = summary["review_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["review_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_review_decision"
        )
        summary["review_status"]["reason"] = (
            "reviewer ACK review decision must remain software_proof"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_review_decision_materials"
        )
        summary["review_status"]["reason"] = (
            "reviewer ACK review decision is missing required safe metadata"
        )
        summary["status"] = summary["review_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution reviewer ack review decision was "
            "blocked because source material could imply reviewer resolution, "
            "owner-material acceptance, ACK/cursor mutation, replay/resubmit, "
            "robot control, raw diagnostics, hardware details, or success; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision": (
                    "blocked_missing_reviewer_ack_intake_not_proven"
                ),
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_review_decision"
                ),
                "review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_review_decision"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe reviewer resolution, owner-material acceptance, "
                        "ACK/cursor mutation, replay/resubmit, control, path, "
                        "hardware, raw, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "previous_reviewer_ack_intake_ref": "",
                "decision_reasons": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "review_handoff_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_reviewer_ack_review_handoff(source):
    """构建 reviewer ACK review-handoff 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 PC safe summary；handoff 不能变成 reviewer resolved、回放、重提或控制许可。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_reviewer_ack_review_handoff_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_reviewer_ack_review_handoff "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        handoff_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_reviewer_ack_review_handoff "
                "summary artifact missing"
            )
            summary["review_handoff_status"]["reason"] = summary["read_error"]
            summary["review_handoff_status"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_reviewer_ack_review_handoff "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_handoff_status"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["review_handoff_status"]["reason"] = (
            "field_evidence_material_resolution_reviewer_ack_review_handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_reviewer_ack_review_handoff_source_contract(
            handoff_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            handoff_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            handoff_doc.get("diagnostics_summary"),
            handoff_doc.get("robot_diagnostics_summary"),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_reviewer_ack_review_handoff_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("review_handoff_status")
        if isinstance(summary_fragment.get("review_handoff_status"), dict)
        else summary_fragment.get("handoff_status_summary")
        if isinstance(summary_fragment.get("handoff_status_summary"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 是手机/Robot 直显文本，必须显式携带 software_proof 与三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    handoff_status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked_missing_reviewer_ack_review_decision_not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or handoff_doc.get("safe_evidence_ref")
        or handoff_doc.get("evidence_ref", "")
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "handoff_status": handoff_status,
            "status": handoff_status,
            "overall_status": "not_proven",
            "review_handoff_status": {
                "status": handoff_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "reviewer ACK review handoff is software_proof only"
                ),
            },
            "source_reviewer_ack_review_decision_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_review_decision_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA
            ),
            "source_reviewer_ack_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_review_decision_status")
                or summary_fragment.get("source_review_decision_status")
                or "blocked"
            ),
            "previous_reviewer_ack_review_decision_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_reviewer_ack_review_decision_ref")
                or summary_fragment.get("source_reviewer_ack_review_decision_ref")
                or ""
            ),
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "handoff_targets": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_targets")
                or summary_fragment.get("operator_support_handoff")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_action": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_action") or ""
            ),
            "ceo_escalation_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("ceo_escalation_recommendation") or ""
            ),
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state") or "hardware_material_pending"
            ),
            "pr5_reply_comment_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_comment_id") or "3269642220"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": handoff_status,
            },
            "not_proven": (
                _field_evidence_material_resolution_reviewer_ack_review_handoff_not_proven(
                    handoff_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        handoff_status
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES,
        bool(summary["handoff_reasons"]),
        bool(summary["handoff_targets"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_action"]),
        bool(summary["ceo_escalation_recommendation"]),
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_comment_id"] == "3269642220",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["handoff_reasons"],
            summary["handoff_targets"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["rejected_materials"],
            summary["unsafe_materials"],
            summary["next_required_evidence"],
            summary["owner_action"],
            summary["ceo_escalation_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE
    ):
        summary["review_handoff_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_review_handoff"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK review handoff schema or boundary is unsupported",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["review_handoff_status"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_review_handoff"
        )
        summary["review_handoff_status"]["reason"] = (
            "reviewer ACK review handoff must remain software_proof"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_review_handoff_materials"
        )
        summary["review_handoff_status"]["reason"] = (
            "reviewer ACK review handoff is missing required safe metadata"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
            handoff_doc
        )
        or _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution reviewer ack review handoff was "
            "blocked because source material could imply reviewer resolution, "
            "owner-material acceptance, ACK/cursor mutation, replay/resubmit, "
            "robot control, raw diagnostics, hardware details, or success; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": (
                    "rejected_unsafe_ack_review_handoff_not_proven"
                ),
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_review_handoff"
                ),
                "review_handoff_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_review_handoff"
                    ),
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe reviewer resolution, owner-material acceptance, "
                        "ACK/cursor mutation, replay/resubmit, control, path, "
                        "hardware, raw, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "previous_reviewer_ack_review_decision_ref": "",
                "handoff_reasons": [],
                "handoff_targets": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_action": "",
                "ceo_escalation_recommendation": "",
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

def summarize_field_evidence_material_resolution_reviewer_ack_followup_escalation_status(
    source,
):
    """构建 reviewer ACK followup escalation status 的 Robot-safe diagnostics 摘要。"""
    # Robot 只展示 PC 产出的安全追办摘要；该 alias 永远不能升级为控制、成功或 reviewer resolved。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary(
            source_path,
            read_error=(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status "
                "summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        followup_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status "
                "summary artifact missing"
            )
            summary["followup_status_summary"]["reason"] = summary["read_error"]
            summary["followup_status_summary"]["status"] = "missing"
            summary["status"] = "missing"
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field_evidence_material_resolution_reviewer_ack_followup_escalation_status "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status_summary"]["reason"] = safe_error
            return summary

    if not isinstance(followup_doc, dict):
        summary["followup_status_summary"]["reason"] = (
            "field_evidence_material_resolution_reviewer_ack_followup_escalation_status JSON must be an object"
        )
        return summary

    diagnostics = (
        followup_doc.get("diagnostics")
        if isinstance(followup_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(followup_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source_contract(
            followup_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        summary_fragment = followup_doc
    else:
        summary_fragment = {}
        for candidate in (
            followup_doc.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            followup_doc.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            followup_doc.get("diagnostics_summary"),
            followup_doc.get("robot_diagnostics_summary"),
            followup_doc.get("robot_compatible_summary"),
            followup_doc.get("summary"),
            diagnostics.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics.get("diagnostics_summary"),
            diagnostics.get("summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("followup_status_summary")
        if isinstance(summary_fragment.get("followup_status_summary"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("phone_safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary_fragment.get("safe_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # phone-safe copy 是最终直显文案，必须重复 false flags，避免下游裁剪后丢边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    followup_status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("followup_status")
        or summary_fragment.get("status")
        or "blocked_missing_reviewer_ack_handoff_not_proven"
    )
    due_status = _redact_route_task_rehearsal_text(
        status_doc.get("due_status")
        or summary_fragment.get("due_status")
        or "blocked"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup_doc.get("safe_evidence_ref")
        or followup_doc.get("evidence_ref", "")
    )
    source_handoff_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_handoff_status")
        or summary_fragment.get("source_reviewer_ack_handoff_status")
        or "blocked"
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or followup_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "followup_status": followup_status,
            "due_status": due_status,
            "status": followup_status,
            "overall_status": "not_proven",
            "followup_status_summary": {
                "status": followup_status,
                "due_status": due_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "reviewer ACK followup escalation status is software_proof only"
                ),
            },
            "source_handoff_status": source_handoff_status,
            "source_handoff_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_schema")
                or summary_fragment.get("source_reviewer_ack_handoff_schema")
                or FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA
            ),
            "source_handoff_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("source_handoff_ref")
                or summary_fragment.get("source_reviewer_ack_handoff_ref")
                or ""
            ),
            "owner_handoff_hints": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff_hints")
                or summary_fragment.get("owner_action")
                or summary_fragment.get("support_escalation_owner")
            ),
            "missing_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_evidence")
                or summary_fragment.get("missing_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "phone_safe_copy": safe_copy_text,
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": followup_status,
            },
            "not_proven": (
                _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_not_proven(
                    followup_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        followup_status
        in FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUSES,
        bool(summary["due_status"]),
        bool(summary["source_handoff_status"]),
        bool(summary["source_handoff_schema"]),
        bool(summary["source_handoff_ref"]),
        bool(summary["owner_handoff_hints"]),
        bool(summary["missing_required_evidence"]),
        bool(summary["next_required_evidence"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["source_handoff_status"],
            summary["source_handoff_schema"],
            summary["source_handoff_ref"],
            summary["owner_handoff_hints"],
            summary["missing_required_evidence"],
            summary["next_required_evidence"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["followup_status_summary"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary["followup_status_summary"] = {
            "status": (
                "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
            ),
            "due_status": "blocked",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK followup escalation status schema or boundary is unsupported",
        }
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE:
        summary["followup_status_summary"]["status"] = (
            "blocked_unsupported_field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
        )
        summary["followup_status_summary"]["reason"] = (
            "reviewer ACK followup escalation status must remain software_proof"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["followup_status_summary"]["status"] = (
            "blocked_missing_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_materials"
        )
        summary["followup_status_summary"]["reason"] = (
            "reviewer ACK followup escalation status is missing required safe metadata"
        )
        summary["status"] = summary["followup_status_summary"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("owner_material_real_acceptance_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            followup_doc
        )
        or _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence material resolution reviewer ack followup escalation "
            "status was blocked because source material could imply reviewer "
            "resolution, owner-material acceptance, ACK/cursor mutation, "
            "replay/resubmit, robot control, raw diagnostics, hardware details, "
            "or success; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "followup_status": "blocked_unsafe_material_claims_not_proven",
                "due_status": "blocked",
                "status": (
                    "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
                ),
                "followup_status_summary": {
                    "status": (
                        "blocked_unsafe_field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
                    ),
                    "due_status": "blocked",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe reviewer resolution, owner-material acceptance, "
                        "ACK/cursor mutation, replay/resubmit, control, path, "
                        "hardware, raw, or success material"
                    ),
                },
                "safe_evidence_ref": "",
                "source_handoff_status": "blocked",
                "source_handoff_schema": "",
                "source_handoff_ref": "",
                "owner_handoff_hints": [],
                "missing_required_evidence": [],
                "next_required_evidence": [],
                "phone_safe_copy": blocked_copy,
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                },
            }
        )
    return summary

__all__ = [
    "FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_STATUSES",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_VALUES",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE",
    "FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_DECISIONS",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_DECISIONS",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_REVIEWER_ACK_BRIDGE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISIONS",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISIONS",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE",
    "FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUSES",
    "_field_evidence_real_material_request_dispatch_not_proven",
    "_field_evidence_real_material_response_intake_not_proven",
    "_field_evidence_real_material_response_review_decision_not_proven",
    "_field_evidence_real_material_response_review_handoff_not_proven",
    "_field_evidence_real_material_followup_escalation_status_not_proven",
    "_default_field_evidence_real_material_request_dispatch_summary",
    "_default_field_evidence_real_material_response_intake_summary",
    "_default_field_evidence_real_material_response_review_decision_summary",
    "_default_field_evidence_real_material_response_review_handoff_summary",
    "_default_field_evidence_real_material_followup_escalation_status_summary",
    "_field_evidence_real_material_owner_ack_intake_not_proven",
    "_field_evidence_real_material_owner_ack_review_decision_not_proven",
    "_field_evidence_material_blocker_escalation_pack_not_proven",
    "_field_evidence_material_resolution_intake_not_proven",
    "_field_evidence_material_resolution_review_decision_not_proven",
    "_field_evidence_material_resolution_review_handoff_not_proven",
    "_field_evidence_material_resolution_followup_escalation_status_not_proven",
    "_field_evidence_material_resolution_owner_response_intake_not_proven",
    "_field_evidence_material_resolution_owner_response_review_decision_not_proven",
    "_field_evidence_material_resolution_owner_response_review_handoff_not_proven",
    "_field_evidence_material_resolution_reviewer_ack_intake_not_proven",
    "_field_evidence_material_resolution_reviewer_ack_review_decision_not_proven",
    "_field_evidence_material_resolution_reviewer_ack_review_handoff_not_proven",
    "_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_not_proven",
    "_default_field_evidence_real_material_owner_ack_intake_summary",
    "_default_field_evidence_real_material_owner_ack_review_decision_summary",
    "_default_field_evidence_material_blocker_escalation_pack_summary",
    "_default_field_evidence_material_resolution_intake_summary",
    "_default_field_evidence_material_resolution_review_decision_summary",
    "_default_field_evidence_material_resolution_review_handoff_summary",
    "_default_field_evidence_material_resolution_followup_escalation_status_summary",
    "_default_field_evidence_material_resolution_owner_response_intake_summary",
    "_default_field_evidence_material_resolution_owner_response_review_decision_summary",
    "_default_field_evidence_material_resolution_owner_response_review_handoff_summary",
    "_default_field_evidence_material_resolution_reviewer_ack_intake_summary",
    "_default_field_evidence_material_resolution_reviewer_ack_review_decision_summary",
    "_default_field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
    "_default_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
    "_field_evidence_real_material_request_dispatch_source_contract",
    "_field_evidence_real_material_response_intake_source_contract",
    "_field_evidence_real_material_response_review_decision_source_contract",
    "_field_evidence_real_material_response_review_handoff_source_contract",
    "_field_evidence_real_material_followup_escalation_status_source_contract",
    "_field_evidence_real_material_owner_ack_intake_source_contract",
    "_field_evidence_real_material_owner_ack_review_decision_source_contract",
    "_field_evidence_material_blocker_escalation_pack_source_contract",
    "_field_evidence_material_resolution_intake_source_contract",
    "_field_evidence_material_resolution_review_decision_source_contract",
    "_field_evidence_material_resolution_review_handoff_source_contract",
    "_field_evidence_material_resolution_followup_escalation_status_source_contract",
    "_field_evidence_material_resolution_owner_response_intake_source_contract",
    "_field_evidence_material_resolution_owner_response_review_decision_source_contract",
    "_field_evidence_material_resolution_owner_response_review_handoff_source_contract",
    "_field_evidence_material_resolution_reviewer_ack_intake_source_contract",
    "_field_evidence_material_resolution_reviewer_ack_review_decision_source_contract",
    "_field_evidence_material_resolution_reviewer_ack_review_handoff_source_contract",
    "_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source_contract",
    "_field_evidence_material_blocker_escalation_pack_has_unsafe_fields",
    "_field_evidence_material_resolution_intake_has_unsafe_fields",
    "_field_evidence_material_resolution_review_decision_has_unsafe_fields",
    "_field_evidence_material_resolution_review_handoff_has_unsafe_fields",
    "_field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields",
    "_field_evidence_material_resolution_owner_response_intake_has_unsafe_fields",
    "_field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields",
    "_field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields",
    "_field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields",
    "_field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields",
    "_field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields",
    "_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields",
    "_field_evidence_real_material_owner_ack_intake_has_unsafe_fields",
    "_field_evidence_real_material_request_dispatch_has_unsafe_fields",
    "_field_evidence_real_material_response_intake_has_unsafe_fields",
    "_field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields",
    "_field_evidence_real_material_response_review_decision_has_unsafe_fields",
    "_field_evidence_real_material_response_review_handoff_has_unsafe_fields",
    "summarize_field_evidence_real_material_request_dispatch",
    "summarize_field_evidence_real_material_response_intake",
    "summarize_field_evidence_real_material_response_review_decision",
    "summarize_field_evidence_real_material_response_review_handoff",
    "summarize_field_evidence_real_material_followup_escalation_status",
    "summarize_field_evidence_real_material_owner_ack_intake",
    "summarize_field_evidence_real_material_owner_ack_review_decision",
    "summarize_field_evidence_material_blocker_escalation_pack",
    "summarize_field_evidence_material_resolution_intake",
    "summarize_field_evidence_material_resolution_review_decision",
    "summarize_field_evidence_material_resolution_review_handoff",
    "summarize_field_evidence_material_resolution_followup_escalation_status",
    "summarize_field_evidence_material_resolution_owner_response_intake",
    "summarize_field_evidence_material_resolution_owner_response_review_decision",
    "summarize_field_evidence_material_resolution_owner_response_review_handoff",
    "summarize_field_evidence_material_resolution_reviewer_ack_intake",
    "summarize_field_evidence_material_resolution_reviewer_ack_review_decision",
    "summarize_field_evidence_material_resolution_reviewer_ack_review_handoff",
    "summarize_field_evidence_material_resolution_reviewer_ack_followup_escalation_status",
]
