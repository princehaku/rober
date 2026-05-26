"""Field evidence rerun diagnostics summary helpers.

本模块承接 operator_gateway_diagnostics 的 field evidence rerun 只读摘要逻辑。
这里的摘要只证明 software_proof 元数据可读，不能升级为真实现场通过、
HIL、Nav2 runtime、WAVE ROVER 运动证明或 delivery success。
"""

import json
import os

EVIDENCE_SOURCE_SOFTWARE = "software_proof"


def _diagnostics():
    # 延迟读取 facade helper，避免兼容层导入本模块时形成初始化环。
    from ros2_trashbot_behavior import operator_gateway_diagnostics

    return operator_gateway_diagnostics


def _facade_helper(name, *args, **kwargs):
    # field-evidence-rerun 已独立成域，通用安全清洗 helper 暂由 facade 统一提供。
    return getattr(_diagnostics(), name)(*args, **kwargs)


def _redact_route_task_rehearsal_text(value):
    # 脱敏规则仍复用共享实现，避免拆分时改变 safe copy 输出。
    return _facade_helper("_redact_route_task_rehearsal_text", value)


def _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(value):
    # 复跑结果材料沿用 retest unsafe 判定，避免 metadata-only 摘要误接收原始材料。
    return _facade_helper(
        "_route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material",
        value,
    )


def _route_task_field_retest_execution_pack_has_success_wording(value):
    # 成功/通过措辞仍由共享守卫判定，避免复跑摘要误报真实闭环。
    return _facade_helper("_route_task_field_retest_execution_pack_has_success_wording", value)


def _route_task_field_run_intake_has_unsafe_control_claims(value):
    # 控制授权敏感词保持跨域一致，Robot diagnostics 不新增任何可控动作入口。
    return _facade_helper("_route_task_field_run_intake_has_unsafe_control_claims", value)


def _route_task_field_run_readiness_copy_is_unsafe(value):
    # safe copy 危险措辞仍走共享判定，保证拆分前后 fail-closed 条件一致。
    return _facade_helper("_route_task_field_run_readiness_copy_is_unsafe", value)


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

FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SCHEMA = (
    "trashbot.field_evidence_rerun_material_dispatch.v1"
)


FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_material_dispatch_summary.v1"
)


FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE = (
    "software_proof_docker_field_evidence_rerun_material_dispatch_gate"
)


FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_intake.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_callback_intake_gate"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_callback_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_callback_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_callback_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_handoff_intake.v1"
)


FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_handoff_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_handoff_intake_gate"
)


FIELD_EVIDENCE_RERUN_QUEUE_SCHEMA = "trashbot.field_evidence_rerun_queue.v1"


FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_queue_summary.v1"
)


FIELD_EVIDENCE_RERUN_QUEUE_GATE = (
    "software_proof_docker_field_evidence_rerun_queue_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_pack.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_pack_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_pack_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_intake.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_callback_intake_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_intake.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_intake_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_STATUSES = (
    "ready_for_field_owner_support_reviewer_handoff_not_proven",
    "handoff_needs_more_material",
    "handoff_evidence_ref_mismatch",
    "handoff_unsafe_rejected",
    "blocked_missing_review_decision",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_STATUSES = (
    "ready_for_acceptance_handoff_owner_intake_not_proven",
    "intake_needs_more_material",
    "intake_evidence_ref_mismatch",
    "intake_unsafe_rejected",
    "blocked_missing_review_handoff",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_STATUSES = (
    "ready_for_acceptance_handoff_review_handoff_not_proven",
    "review_needs_owner_rework",
    "review_evidence_ref_mismatch",
    "review_unsafe_rejected",
    "blocked_missing_handoff_intake",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_STATUSES = (
    "ready_for_acceptance_review_handoff_not_proven",
    "handoff_needs_owner_rework",
    "handoff_evidence_ref_mismatch",
    "handoff_unsafe_rejected",
    "blocked_missing_review_decision",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATES = (
    "pending",
    "overdue",
    "escalated",
    "blocked",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_STATUSES = (
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


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_STATUSES = (
    "ready_for_owner_response_review_handoff_not_proven",
    "review_needs_owner_rework",
    "review_evidence_ref_mismatch",
    "review_unsafe_rejected",
    "blocked_missing_owner_response_intake",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES = (
    "ready_for_owner_response_review_handoff_not_proven",
    "handoff_needs_owner_rework",
    "handoff_evidence_ref_mismatch",
    "handoff_unsafe_rejected",
    "blocked_missing_owner_response_review_decision",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES = (
    "reviewer_acknowledged_not_proven",
    "reviewer_ack_needs_reassignment",
    "blocked_missing_owner_response_review_handoff",
    "reviewer_ack_evidence_ref_mismatch",
    "reviewer_ack_rejected_unsafe",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES = (
    "accepted_for_reviewer_ack_review_not_proven",
    "needs_reviewer_reassignment_not_proven",
    "needs_field_owner_supplement_not_proven",
    "rejected_unsafe_reviewer_ack_not_proven",
    "blocked_missing_reviewer_ack_intake_not_proven",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES = (
    "ready_for_field_owner_reviewer_ack_followup_not_proven",
    "needs_reviewer_handoff_reassignment_not_proven",
    "needs_field_owner_ack_material_supplement_not_proven",
    "rejected_unsafe_reviewer_ack_handoff_not_proven",
    "blocked_missing_reviewer_ack_review_decision_not_proven",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES = (
    "pending_reviewer_ack_followup_not_proven",
    "overdue_reviewer_ack_followup_not_proven",
    "escalated_missing_real_material_not_proven",
    "blocked_missing_reviewer_ack_review_handoff_not_proven",
    "ready_for_real_material_reviewer_followup_not_proven",
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_GATE = (
    "software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate"
)


FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_SOURCE = (
    "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status"
)


def _execution_callback_review_handoff_replace(value, replacements):
    # 复用旧 handoff 安全逻辑时只做名称和边界映射，不放宽任何字段白名单。
    if isinstance(value, dict):
        converted = {}
        for key, item in value.items():
            new_key = str(key)
            for old, new in replacements.items():
                new_key = new_key.replace(old, new)
            converted[new_key] = _execution_callback_review_handoff_replace(
                item,
                replacements,
            )
        return converted
    if isinstance(value, list):
        return [
            _execution_callback_review_handoff_replace(item, replacements)
            for item in value
        ]
    if isinstance(value, str):
        text = value
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    return value


_EXECUTION_CALLBACK_REVIEW_HANDOFF_TO_BASE_HANDOFF = {
    "field_evidence_rerun_execution_callback_review_handoff": (
        "field_evidence_rerun_callback_review_handoff"
    ),
    "FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF": (
        "FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF"
    ),
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA: (
        FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ),
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA: (
        FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA
    ),
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE: (
        FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE
    ),
}
_BASE_HANDOFF_TO_EXECUTION_CALLBACK_REVIEW_HANDOFF = {
    value: key for key, value in _EXECUTION_CALLBACK_REVIEW_HANDOFF_TO_BASE_HANDOFF.items()
}


def _strip_execution_callback_review_handoff_forbidden_terms(summary):
    # 新 alias 只保留任务交接元数据；串口、UART、WAVE ROVER 字段名本身也不能外露。
    if not isinstance(summary, dict):
        return summary
    summary.pop("serial_uart_triggered", None)
    summary.pop("wave_rover_triggered", None)
    if isinstance(summary.get("not_proven"), list):
        summary["not_proven"] = [
            item
            for item in summary["not_proven"]
            if "serial" not in str(item).lower()
            and "uart" not in str(item).lower()
            and "wave_rover" not in str(item).lower()
        ]
    return summary










































































































def _field_evidence_rerun_material_dispatch_not_proven(dispatch=None, summary_fragment=None):
    # 现场材料派发只说明还缺哪些真实材料；Robot diagnostics 不能把派发包解释成执行结果。
    source_values = []
    for item in (dispatch, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_material_dispatch_only",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "hil_pass_not_verified",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_callback_intake_not_proven(intake=None, summary_fragment=None):
    # 回执入口只消费现场 owner 的安全摘要；accepted 计数也不能升级成路线、电梯或交付通过。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_callback_intake_only",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "hil_pass_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # 复核决策只把 Autonomy 的白名单结论转给 Robot diagnostics；不能把 accepted 写成实地通过。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_callback_review_decision_only",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "hil_pass_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_callback_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只交接复核后的待办，不能把 owner handoff 误解释成现场完成。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_callback_review_handoff_only",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "hil_pass_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "serial_uart_or_wave_rover_control",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_handoff_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # handoff intake 只是 owner 回执入口，不能被解释成现场复跑、交付或控制已完成。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_handoff_intake_only",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "hil_pass_not_verified",
        "collect_dropoff_cancel_control",
        "remote_ack",
        "cursor_advance_or_persistence",
        "serial_uart_or_wave_rover_control",
        "delivery_success",
    )
    values = []
    for item in list(source_values) + list(required):
        text = str(item or "").strip()
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_queue_not_proven(queue=None, summary_fragment=None):
    # rerun queue 只是现场复跑的排队元数据；Robot 不能把“已排队”解释成现场执行或验收通过。
    source_values = []
    for item in (queue, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_queue_only",
        "field_rerun_not_executed",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_pack_not_proven(pack=None, summary_fragment=None):
    # execution pack 只是给现场 owner 的复跑操作包；Robot 不能把“包已生成”解释成现场已执行。
    source_values = []
    for item in (pack, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_pack_only",
        "field_rerun_not_executed",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_callback_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # callback-intake 只说明现场 owner 回填了安全摘要；accepted 材料不能升级成现场复跑通过。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_callback_intake_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_callback_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review-decision 只审核上一轮 execution callback intake；不能把 ready/missing 结论升级成现场跑通。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_callback_review_decision_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_callback_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # execution handoff 只交接复跑回执复核后的待办，不能被解读成现场复跑或投递成功。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_callback_review_handoff_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # result-intake 只接收现场结果回填摘要；accepted 只代表进入复核，不代表机器人真实执行。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_intake_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # result-review-decision 只复核现场结果回填摘要；accepted_for_review 仍不是现场执行成功。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_review_decision_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # review-handoff 只是把复核结论交给现场 owner；不能当成机器人已复跑或交付成功。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_review_handoff_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_packet_not_proven(
    packet=None,
    summary_fragment=None,
):
    # acceptance packet 只是验收准备摘要；即使 ready 也不能代表真实复跑或投递成功。
    source_values = []
    for item in (packet, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_packet_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_backfill_not_proven(
    backfill=None,
    summary_fragment=None,
):
    # backfill 只代表材料补录状态；Robot 不能把补录完成误当成真实复跑闭环。
    source_values = []
    for item in (backfill, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_backfill_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只说明补录材料是否可交接，不能被 Robot 解释成真实复跑或投递成功。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只说明支持/owner/reviewer 的安全交接，不能被解释为现场复跑或投递已成功。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_review_handoff_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_not_proven(
    intake=None,
    summary_fragment=None,
):
    # intake 只接收 owner/support 交接回执，不能被解释成现场复跑、验收或投递已成功。
    source_values = []
    for item in (intake, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只判断 intake 材料是否可交接/返工，不能被解释成真实现场验收通过。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # review handoff 只把复核决策交给 owner/support/reviewer，不能被解释成真实现场验收通过。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_only",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_not_proven(
    status=None,
    summary_fragment=None,
):
    # follow-up escalation 只说明后续追踪状态，不能被 Robot 解释成现场复跑、验收或控制证据。
    source_values = []
    for item in (status, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_only",
        "source_review_handoff_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_not_proven(
    response=None,
    summary_fragment=None,
):
    # owner response intake 只接收 owner/support/reviewer 的安全材料分类，不能被解释成现场验收或控制许可。
    source_values = []
    for item in (response, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_only",
        "source_followup_escalation_status_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # owner response review decision 只复核 owner 回执材料，不能被解释成真实送达或控制许可。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_only",
        "source_owner_response_intake_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
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


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # owner response review handoff 只交接安全复核摘要，不能升级成现场通过、控制许可或 PR resolved。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_only",
        "source_owner_response_review_decision_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "real_hardware_runtime_not_verified",
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
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL 等敏感词只作为阻断线索，不进入 Robot 可见 not_proven 列表。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_not_proven(
    ack=None,
    summary_fragment=None,
):
    # reviewer ACK intake 只是复核确认的安全元数据，不能被解释成现场成功或控制许可。
    source_values = []
    for item in (ack, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_only",
        "source_owner_response_review_handoff_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "real_hardware_runtime_not_verified",
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
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # 不把 raw/path/checksum/HIL 词带入 Robot 可见 not_proven，避免摘要反向泄漏敏感线索。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review-decision 只是 ACK 后的安全复核分类，不能被解释成现场、HIL 或交付成功。
    source_values = []
    for item in (decision, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_only",
        "source_reviewer_ack_intake_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "real_hardware_runtime_not_verified",
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
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL 这类词只用于阻断，不能出现在 Robot 可见 not_proven 细节里。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # review-handoff 只把 ACK 复核交接结果投到 diagnostics，不能变成现场通过或控制授权。
    source_values = []
    for item in (handoff, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_only",
        "source_reviewer_ack_review_decision_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "real_hardware_runtime_not_verified",
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
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL 这类敏感词只用于阻断，不进入 Robot 可见 not_proven 细节。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_not_proven(
    status_doc=None,
    summary_fragment=None,
):
    # follow-up escalation status 只暴露缺材料升级状态，不能被解释成 reviewer 已闭环或现场交付成功。
    source_values = []
    for item in (status_doc, summary_fragment):
        if isinstance(item, dict) and isinstance(item.get("not_proven"), list):
            source_values.extend(item.get("not_proven"))
        if isinstance(item, dict) and isinstance(item.get("missing_evidence_summary"), list):
            source_values.extend(item.get("missing_evidence_summary"))
        if isinstance(item, dict) and isinstance(item.get("next_required_evidence"), list):
            source_values.extend(item.get("next_required_evidence"))
    required = (
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_only",
        "source_reviewer_ack_review_handoff_not_field_proof",
        "field_rerun_not_executed_by_robot",
        "real_route_completion_not_verified",
        "real_field_task_record_not_verified",
        "real_nav2_fixed_route_runtime_not_verified",
        "real_elevator_operation_not_verified",
        "real_dropoff_cancel_completion_not_verified",
        "real_delivery_result_not_verified",
        "real_phone_browser_not_verified",
        "real_hardware_runtime_not_verified",
        "PRRT_kwDOSWB9286CJ3tX",
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
        text = _redact_route_task_rehearsal_text(item)
        lowered = text.lower()
        # raw/path/checksum/HIL 这类词只用于阻断，Robot 摘要里保留安全的 not_proven 标签即可。
        if any(marker in lowered for marker in ("raw", "path", "checksum", "hil", " pass", "[redacted")):
            continue
        if text and text not in values:
            values.append(text)
    return values


def _default_field_evidence_rerun_material_dispatch_summary(
    path,
    dispatch_status="blocked_missing_field_evidence_rerun_material_dispatch",
    read_error="",
):
    # 默认摘要必须 fail closed；缺材料派发包时不得启用控制、ACK、Nav2 或 HIL 语义。
    reason = read_error or "field evidence rerun material dispatch is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "dispatch_status": {
            "status": dispatch_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "owner_work_orders": [],
        "required_material_groups": [],
        "rerun_commands": [],
        "callback_packet_requirements": [],
        "same_evidence_ref_required": True,
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE,
        "not_proven": _field_evidence_rerun_material_dispatch_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Field evidence rerun material dispatch is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun material dispatch is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_callback_intake_summary(
    path,
    intake_status="blocked_missing_field_evidence_rerun_callback_intake",
    read_error="",
):
    # 缺省值固定 blocked，避免 Robot 在缺回执或坏输入时误认为现场材料已经可执行。
    reason = read_error or "field evidence rerun callback intake is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "material_counts": {"accepted": 0, "missing": 0, "rejected": 0, "blocked": 0},
        "accepted_material_count": 0,
        "missing_material_count": 0,
        "rejected_material_count": 0,
        "blocked_material_count": 0,
        "next_required_evidence": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE,
        "not_proven": _field_evidence_rerun_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Field evidence rerun callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_callback_review_decision_summary(
    path,
    review_status="blocked_missing_field_evidence_rerun_callback_review_decision",
    read_error="",
):
    # 缺省 blocked 保证 Robot diagnostics 在没有复核决策时不会猜测现场复跑可交付。
    reason = read_error or "field evidence rerun callback review decision is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision": "blocked",
        "owner_handoff": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "blocker_summary": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "raw_artifact_consumed": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_rerun_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Field evidence rerun callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_callback_review_handoff_summary(
    path,
    handoff_status="blocked_missing_field_evidence_rerun_callback_review_handoff",
    read_error="",
):
    # 缺省 blocked 摘要让 diagnostics 在没有 handoff 材料时仍保持 fail-closed。
    reason = read_error or "field evidence rerun callback review handoff is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision": "blocked",
        "owner_handoff": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "blocker_summary": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "raw_artifact_consumed": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE,
        "not_proven": _field_evidence_rerun_callback_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Field evidence rerun callback review handoff is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun callback review handoff is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "serial_uart_triggered": False,
        "wave_rover_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_handoff_intake_summary(
    path,
    intake_status="blocked_missing_field_evidence_rerun_handoff_intake",
    read_error="",
):
    # 缺省 blocked 摘要让 Robot 在没有 owner-safe intake 时保持只读、不可控。
    reason = read_error or "field evidence rerun handoff intake is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "owner_ack_status": "blocked",
        "next_owner": "",
        "owner_handoff": [],
        "next_required_evidence": [],
        "rerun_guidance": [],
        "blocker_summary": [],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE,
        "not_proven": _field_evidence_rerun_handoff_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "safe_copy": (
            "Field evidence rerun handoff intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun handoff intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "serial_uart_triggered": False,
        "wave_rover_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_queue_summary(
    path,
    queue_status="blocked_missing_field_evidence_rerun_queue",
    read_error="",
):
    # 缺省态必须 fail-closed；Robot diagnostics 不能从缺 Autonomy queue 推断现场可复跑。
    reason = read_error or "field evidence rerun queue is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_QUEUE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "queue_status": {
            "status": queue_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_handoff_intake_schema": "",
        "source_handoff_intake_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "blocker_summary": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_rerun_hint": [],
        "safe_copy": (
            "Field evidence rerun queue is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun queue is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_QUEUE_GATE,
        "not_proven": _field_evidence_rerun_queue_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "hardware_transport_triggered": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_execution_pack_summary(
    path,
    execution_status="blocked_missing_field_evidence_rerun_execution_pack",
    read_error="",
):
    # 缺省态必须 fail-closed；Robot diagnostics 只能展示复跑执行包元数据，不能触发控制链路。
    reason = read_error or "field evidence rerun execution pack is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "execution_pack_status": {
            "status": execution_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_queue_schema": "",
        "source_queue_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "execution_steps": [],
        "material_templates": [],
        "owner_handoff": [],
        "fail_thresholds": [],
        "pass_thresholds": [],
        "backfill_instructions": [],
        "safe_copy": (
            "Field evidence rerun execution pack is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun execution pack is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE,
        "not_proven": _field_evidence_rerun_execution_pack_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "hardware_transport_triggered": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_execution_callback_intake_summary(
    path,
    intake_status="blocked_missing_field_evidence_rerun_execution_callback_intake",
    read_error="",
):
    # 缺省摘要必须 blocked；Robot 只能展示回执入口元数据，不能推断复跑执行或交付完成。
    reason = read_error or "field evidence rerun execution callback intake is not configured"
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_execution_pack_schema": "",
        "source_execution_pack_status": {},
        "callback_packet_schema": "",
        "callback_packet_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "blocked_materials": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "safe_copy": (
            "Field evidence rerun execution callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun execution callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE,
        "not_proven": _field_evidence_rerun_execution_callback_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "hardware_transport_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_execution_callback_review_decision_summary(
    path,
    review_status="blocked_missing_field_evidence_rerun_execution_callback_review_decision",
    read_error="",
):
    # 缺省态必须 blocked；Robot 只展示复核结论元数据，不能推断现场复跑或交付完成。
    reason = read_error or (
        "field evidence rerun execution callback review decision is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "source_callback_intake_schema": "",
        "source_callback_intake_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "review_decision": "blocked",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "blocked_materials": [],
        "decision_reasons": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "safe_copy": (
            "Field evidence rerun execution callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "safe_phone_copy": (
            "Field evidence rerun execution callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        ),
        "boundary_flags": {
            "metadata_only": True,
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "control_entrypoint_enabled": False,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_rerun_execution_callback_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "source": EVIDENCE_SOURCE_SOFTWARE,
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
        "hardware_transport_triggered": False,
        "hil_pass": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _default_field_evidence_rerun_execution_callback_review_handoff_summary(
    path,
    handoff_status="blocked_missing_field_evidence_rerun_execution_callback_review_handoff",
    read_error="",
):
    # 新 alias 的缺省态沿用 handoff 的 fail-closed 结构，但 gate/schema 必须是 execution rung。
    summary = _default_field_evidence_rerun_callback_review_handoff_summary(
        path,
        handoff_status=handoff_status.replace(
            "field_evidence_rerun_execution_callback_review_handoff",
            "field_evidence_rerun_callback_review_handoff",
        ),
        read_error=read_error.replace(
            "field evidence rerun execution callback review handoff",
            "field evidence rerun callback review handoff",
        ),
    )
    summary = _execution_callback_review_handoff_replace(
        summary,
        _BASE_HANDOFF_TO_EXECUTION_CALLBACK_REVIEW_HANDOFF,
    )
    if isinstance(summary.get("boundary_flags"), dict):
        # 默认摘要也不能出现 raw-artifact 字样，避免 diagnostics alias 泄露 raw 材料语义。
        summary["boundary_flags"].pop("raw_artifact_consumed", None)
    summary["not_proven"] = (
        _field_evidence_rerun_execution_callback_review_handoff_not_proven()
    )
    return _strip_execution_callback_review_handoff_forbidden_terms(summary)


def _default_field_evidence_rerun_execution_result_intake_summary(
    path,
    intake_status="blocked_missing_field_evidence_rerun_execution_result_intake",
    read_error="",
):
    # 缺省摘要必须 fail-closed，避免 mobile/diagnostics 把缺材料误读成可控制状态。
    safe_copy = (
        "Field evidence rerun execution result intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "result_intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": read_error
            or "field evidence rerun execution result intake is not configured",
        },
        "owner_handoff": [],
        "missing_reasons": [],
        "rejected_reasons": [],
        "blocked_reasons": [],
        "next_required_evidence": [],
        "robot_diagnostics_summary": {
            "status": "blocked",
            "reason": "field evidence rerun execution result intake is not configured",
        },
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_GATE,
        "not_proven": _field_evidence_rerun_execution_result_intake_not_proven(),
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


def _default_field_evidence_rerun_execution_result_review_decision_summary(
    path,
    review_status="blocked_missing_field_evidence_rerun_execution_result_review_decision",
    read_error="",
):
    # 缺省态保持 blocked，避免 diagnostics 在缺少 canonical summary 时泄露 raw review/result 材料。
    safe_copy = (
        "Field evidence rerun execution result review decision is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result review decision is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_status": {
            "status": review_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "review_decision": "blocked",
        "intake_reference": "",
        "source_result_intake_schema": "",
        "source_result_intake_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "blocker_reason": "",
        "rejection_reason": "",
        "backfill_reason": "",
        "next_required_evidence": [],
        "owner_handoff": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_GATE,
        "not_proven": _field_evidence_rerun_execution_result_review_decision_not_proven(),
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


def _default_field_evidence_rerun_execution_result_review_handoff_summary(
    path,
    handoff_status="blocked_missing_field_evidence_rerun_execution_result_review_handoff",
    read_error="",
):
    # 缺源时也返回完整 false flags，让 diagnostics/mobile 不能把空交接误读成控制许可。
    safe_copy = (
        "Field evidence rerun execution result review handoff is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result review handoff is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "source_review_decision": "blocked",
        "owner_handoff": [],
        "blocker_summary": "",
        "next_required_real_materials": [],
        "reconciliation_guidance": [],
        "rerun_guidance": [],
        "source_review_decision_status": {},
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_GATE,
        "not_proven": _field_evidence_rerun_execution_result_review_handoff_not_proven(),
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


def _default_field_evidence_rerun_execution_result_acceptance_packet_summary(
    path,
    acceptance_status="blocked_missing_field_evidence_rerun_execution_result_acceptance_packet",
    read_error="",
):
    # 缺省态必须显式 fail-closed，避免现场验收包缺失时被前端或 diagnostics 误读成可控。
    safe_copy = (
        "Field evidence rerun execution result acceptance packet is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance packet is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "acceptance_status": {
            "status": acceptance_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "acceptance_verdict": "blocked",
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "required_materials": [],
        "accepted_materials": [],
        "missing_materials": [],
        "blocked_materials": [],
        "owner_next_steps": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_GATE,
        "not_proven": _field_evidence_rerun_execution_result_acceptance_packet_not_proven(),
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


def _default_field_evidence_rerun_execution_result_acceptance_backfill_summary(
    path,
    backfill_status="blocked_missing_field_evidence_rerun_execution_result_acceptance_backfill",
    read_error="",
):
    # 缺省态保持 not_proven，确保 diagnostics 缺少补录摘要时不会开启任何主动作。
    safe_copy = (
        "Field evidence rerun execution result acceptance backfill is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance backfill is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "backfill_status": {
            "status": backfill_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "backfill_verdict": "blocked",
        "same_evidence_ref_status": {
            "status": "blocked",
            "verdict": "not_proven",
            "reason": reason,
        },
        "required_materials": [],
        "accepted_materials": [],
        "missing_materials": [],
        "blocked_materials": [],
        "owner_next_steps": [],
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_GATE,
        "not_proven": _field_evidence_rerun_execution_result_acceptance_backfill_not_proven(),
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


def _default_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary(
    path,
    decision_status="blocked_missing_backfill",
    read_error="",
):
    # 缺省态使用最小字段闭锁，避免 review-decision 缺失时被误判为补录已验收。
    safe_copy = (
        "Field evidence rerun execution result acceptance backfill review decision "
        "is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance backfill review decision is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "decision": "blocked",
        "decision_status": {
            "status": decision_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "missing_categories": [],
        "rejected_categories": [],
        "owner_next_step": "Attach same-ref sanitized backfill review materials.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_GATE
        ),
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_review_handoff_summary(
    path,
    handoff_status="blocked_missing_review_decision",
    read_error="",
):
    # 缺省态只返回交接元数据，避免 diagnostics 把缺失 handoff 当成现场验收完成。
    safe_copy = (
        "Field evidence rerun execution result acceptance review handoff "
        "is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance review handoff is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "handoff_status": {
            "status": handoff_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "required_materials": [],
        "blocked_categories": [],
        "rejected_categories": [],
        "owner_next_step": "Attach same-ref sanitized acceptance review handoff.",
        "support_next_step": "Wait for sanitized same-ref support handoff metadata.",
        "reviewer_next_step": "Review only software-proof safe handoff metadata.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_GATE,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_review_handoff_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary(
    path,
    intake_status="blocked_missing_review_handoff",
    read_error="",
):
    # 缺省态必须闭锁控制权限，避免 owner intake 缺失时被 UI 推断为验收完成。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake "
        "is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake is not configured"
    )
    return {
        "schema": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "intake_status": {
            "status": intake_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "accepted_material_refs": [],
        "required_checklist": [],
        "blocked_categories": [],
        "rejected_categories": [],
        "owner_next_step": "Attach same-ref sanitized owner intake metadata.",
        "support_next_step": "Wait for sanitized same-ref support intake metadata.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_GATE,
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary(
    path,
    review_decision_status="blocked_missing_handoff_intake",
    read_error="",
):
    # 缺省态必须闭锁控制权限，避免 review decision 缺失时被下游误读成可交接验收。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake review decision "
        "is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake review decision is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_decision_status": {
            "status": review_decision_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "source_intake_status": "unknown",
        "accepted_material_refs": [],
        "missing_or_rework_reasons": [],
        "rejected_categories": [],
        "owner_next_step": "Attach same-ref sanitized intake review decision metadata.",
        "support_next_step": "Wait for sanitized same-ref review decision metadata.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary(
    path,
    review_handoff_status="blocked_missing_review_decision",
    read_error="",
):
    # 缺省态必须闭锁控制权限，避免 review handoff 缺失时被下游误读成验收完成。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake review handoff "
        "is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake review handoff is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "review_handoff_status": {
            "status": review_handoff_status,
            "verdict": "not_proven",
            "reason": reason,
        },
        "source_review_decision_status": "unknown",
        "accepted_material_refs": [],
        "missing_or_rework_reasons": [],
        "rejected_categories": [],
        "owner_next_step": "Attach same-ref sanitized review handoff metadata.",
        "support_next_step": "Wait for sanitized same-ref support review handoff metadata.",
        "reviewer_next_step": "Review only software-proof safe handoff metadata.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary(
    path,
    followup_state="blocked",
    read_error="",
):
    # 缺 follow-up status 时也返回完整 false 栅栏，避免 diagnostics 缺项被误读成可控。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake follow-up "
        "escalation status is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake follow-up escalation status is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "followup_state": followup_state,
        "followup_status": {
            "state": followup_state,
            "verdict": "not_proven",
            "reason": reason,
        },
        "source_review_handoff_status": "unknown",
        "missing_required_material_refs": [],
        "pending_reason": "",
        "overdue_reason": "",
        "escalated_reason": "",
        "blocked_reason": reason,
        "owner_next_step": "Attach same-ref sanitized follow-up status metadata.",
        "support_next_step": "Wait for sanitized software-proof follow-up metadata.",
        "reviewer_next_step": "Keep follow-up not_proven until real field evidence exists.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {"status": "blocked", "reason": reason},
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary(
    path,
    status="blocked",
    read_error="",
):
    # 缺 owner response intake 时也返回完整 false 栅栏，避免 diagnostics 缺项被误读成可控。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response intake is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner response intake is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
        "source_bridge": "",
        "source_followup_status": {},
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "owner_response_intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_followup_escalation_status": {},
        "accepted_material_refs": [],
        "missing_material_refs": [],
        "rejected_material_refs": [],
        "blocked_material_refs": [],
        "owner_route": [],
        "reviewer_route": [],
        "support_route": [],
        "next_required_field_owner_materials": [],
        "false_state_flags": {
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "overall_status": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
            "ack_post_allowed": False,
            "cursor_updates_allowed": False,
            "nav2_triggered": False,
            "hil_pass": False,
        },
        "owner_next_step": "Attach same-ref sanitized owner response intake metadata.",
        "support_next_step": "Wait for sanitized software-proof owner response intake metadata.",
        "reviewer_next_step": "Keep owner response intake not_proven until real field evidence exists.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary(
    path,
    status="blocked_missing_owner_response_intake",
    read_error="",
):
    # 缺 owner response review decision 时必须显式回到 false 栅栏，避免下游把缺项当作可交接。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response review decision is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner response review decision is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "review_decision_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_intake_status": "unknown",
        "accepted_material_refs": [],
        "missing_material_refs": [],
        "rejected_material_refs": [],
        "blocked_material_refs": [],
        "decision_reasons": [],
        "owner_next_step": "Attach same-ref sanitized owner response review decision metadata.",
        "support_next_step": "Wait for sanitized software-proof owner response review decision metadata.",
        "reviewer_next_step": "Keep owner response review decision not_proven until real field evidence exists.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": "blocked", "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary(
    path,
    status="blocked_missing_owner_response_review_decision",
    read_error="",
):
    # 缺 owner response review handoff 时必须闭锁控制权限，避免 diagnostics 被误读成现场交付完成。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response review handoff is metadata-only; source=software_proof; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner response review handoff is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "handoff_status": status,
        "overall_status": "not_proven",
        "review_handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_review_decision_status": "unknown",
        "handoff_reasons": [reason],
        "next_required_evidence": [],
        "owner_next_step": "Attach same-ref sanitized owner response review handoff metadata.",
        "support_next_step": "Wait for sanitized software-proof owner response review handoff metadata.",
        "reviewer_next_step": "Keep owner response review handoff not_proven until real field evidence exists.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary(
    path,
    status="blocked_missing_owner_response_review_handoff",
    read_error="",
):
    # 缺 reviewer ACK intake 时必须明确阻断，不能让 ACK 入口变成控制或成功信号。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK intake is metadata-only; source=software_proof; "
        "not_proven; safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner response reviewer ACK intake is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "ack_intake_status": status,
        "overall_status": "not_proven",
        "reviewer_ack_intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_owner_response_review_handoff_status": "unknown",
        "ack_reasons": [reason],
        "next_required_evidence": [],
        "owner_next_step": "Attach same-ref sanitized reviewer ACK intake metadata.",
        "support_next_step": "Wait for sanitized software-proof reviewer ACK intake metadata.",
        "reviewer_next_step": "Keep reviewer ACK intake not_proven until real field evidence exists.",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary(
    path,
    decision="blocked_missing_reviewer_ack_intake_not_proven",
    read_error="",
):
    # 缺 review-decision safe summary 时必须 fail closed，避免 ACK 复核被误读成现场验收或控制许可。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK review decision is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK review decision summary is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision",
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
        "owner_next_step": "",
        "support_next_step": "",
        "reviewer_next_step": "",
        "review_handoff_recommendation": "",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": decision, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary(
    path,
    handoff_status="blocked_missing_reviewer_ack_review_decision_not_proven",
    read_error="",
):
    # 缺 review-handoff safe summary 时默认阻断，防止 reviewer ACK 交接被误读成现场成功或控制许可。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK review handoff is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK review handoff summary is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff",
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
        "owner_next_step": "",
        "support_next_step": "",
        "reviewer_next_step": "",
        "review_handoff_recommendation": "",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": handoff_status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_not_proven()
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


def _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary(
    path,
    status="blocked_missing_reviewer_ack_review_handoff_not_proven",
    read_error="",
):
    # 缺 follow-up escalation safe summary 时必须显式阻断，避免 diagnostics 缺项被当成 reviewer ACK 已完成。
    safe_copy = (
        "Field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK followup escalation status is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "field evidence rerun execution result acceptance handoff intake owner "
        "response reviewer ACK followup escalation status summary is not configured"
    )
    return {
        "schema": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
        ),
        "schema_version": 1,
        "evidence_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "capability": "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status",
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "safe_evidence_ref": "",
        "status": status,
        "overall_status": "not_proven",
        "followup_escalation_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_review_handoff_schema": "",
        "source_reviewer_ack_review_handoff_status": "blocked",
        "previous_reviewer_ack_review_handoff_ref": "",
        "missing_evidence_summary": [],
        "next_required_evidence": [],
        "owner_next_step": "",
        "reviewer_next_step": "",
        "support_next_step": "",
        "evidence_boundary_status": "not_proven",
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "robot_compatible_summary": {"status": status, "reason": reason},
        "boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "proof_boundary": (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        ),
        "software_proof": True,
        "not_proven": (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_not_proven()
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


def _field_evidence_rerun_material_dispatch_source_contract(value):
    # summary wrapper 必须保留原始 Autonomy schema/boundary，防止 Robot 接受其他 gate 的近似字段。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_callback_intake_source_contract(value):
    # summary wrapper 必须回指 callback intake gate；Robot alias 不能接收 dispatch 或 review 的相似摘要。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_callback_review_decision_source_contract(value):
    # summary wrapper 必须回指 review decision gate；Robot 不能把 callback intake 当复核决策展示。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_callback_review_handoff_source_contract(value):
    # summary wrapper 必须回指 handoff gate；Robot 不能把 review decision 当 handoff 展示。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_handoff_intake_source_contract(value):
    # summary wrapper 必须回指 handoff-intake gate；Robot 不把上一轮 handoff 直接当 intake。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_queue_source_contract(value):
    # summary wrapper 必须回指 queue gate；Robot 不把 handoff intake 或 callback 回执当复跑队列。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY_SCHEMA:
        source_schema = str(value.get("source_schema") or FIELD_EVIDENCE_RERUN_QUEUE_SCHEMA)
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_pack_source_contract(value):
    # summary wrapper 必须回指 execution-pack gate；Robot 不把 queue 或 raw artifact 当执行包展示。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema") or FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_callback_intake_source_contract(value):
    # summary wrapper 必须回指 execution-callback-intake gate，防止 Robot 接收执行包或旧 callback intake。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_callback_review_decision_source_contract(value):
    # summary wrapper 必须回指 execution-callback-review-decision gate，防止 Robot 接收 callback-intake。
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_handoff_intake_has_unsafe_fields(value):
    # intake alias 严格只接收 safe summary；raw/path/checksum/topic/设备/凭证字段一律降级。
    unsafe_key_fragments = (
        "raw",
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
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in {
                "not_proven",
                "safe_to_control",
                "delivery_success",
                "primary_actions_enabled",
                "boundary_flags",
                "control_entrypoint_enabled",
                "owner_ack_status",
            }:
                continue
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _field_evidence_rerun_handoff_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(_field_evidence_rerun_handoff_intake_has_unsafe_fields(item) for item in value)
    return _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
        value
    )


def _field_evidence_rerun_execution_pack_has_unsafe_fields(value):
    # execution-pack 的合法字段名包含 pack/backfill，不能沿用 ack 子串的 key 级拦截。
    unsafe_key_fragments = (
        "raw",
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
        "cursor",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "source_queue_schema",
        "source_queue_status",
        "same_evidence_ref_status",
        "execution_pack_status",
        "execution_status",
        "pack_status",
        "execution_steps",
        "material_templates",
        "owner_handoff",
        "fail_thresholds",
        "pass_thresholds",
        "backfill_instructions",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "boundary_flags",
        "control_entrypoint_enabled",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_rerun_execution_pack_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(_field_evidence_rerun_execution_pack_has_unsafe_fields(item) for item in value)
    return _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
        value
    )


def _field_evidence_rerun_execution_callback_intake_has_unsafe_fields(value):
    # execution-callback-intake 允许材料分类字段，但不允许 raw artifact、控制、ACK、路径或硬件细节。
    unsafe_key_fragments = (
        "raw",
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
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
        "traceback",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "source_execution_pack_schema",
        "source_execution_pack_status",
        "callback_packet_schema",
        "callback_packet_status",
        "same_evidence_ref_status",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "blocked_materials",
        "owner_handoff",
        "next_required_evidence",
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
        "field_evidence_rerun_execution_result_acceptance_packet_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary",
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
            if _field_evidence_rerun_execution_callback_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_callback_intake_has_unsafe_fields(item)
            for item in value
        )
    return _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
        value
    )


def _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields(value):
    # review-decision 允许材料分类和 decision 字段，但不允许 raw artifact、控制、ACK、路径或硬件细节。
    unsafe_key_fragments = (
        "raw",
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
        "ack_cursor",
        "ack_post",
        "ack_state",
        "cursor",
        "traceback",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "source_callback_intake_schema",
        "source_callback_intake_status",
        "review_status",
        "decision_status",
        "same_evidence_ref_status",
        "review_decision",
        "decision",
        "accepted_materials",
        "missing_materials",
        "rejected_materials",
        "blocked_materials",
        "decision_reasons",
        "owner_handoff",
        "next_required_evidence",
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
        "field_evidence_rerun_execution_result_acceptance_packet_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary",
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
            if _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields(item)
            for item in value
        )
    return _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
        value
    )


def _field_evidence_rerun_execution_result_intake_source_contract(value):
    # canonical summary 必须回指 result-intake artifact 和本 gate，防止误消费 callback/handoff 摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_intake_has_unsafe_fields(value):
    # result-intake alias 只接收白名单摘要；raw result packet、路径、topic、ACK 或硬件细节一律降级。
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
        "ack",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "control",
        "success",
        "pass",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "result_intake_status",
        "intake_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "owner_handoff",
        "missing_reasons",
        "rejected_reasons",
        "blocked_reasons",
        "next_required_evidence",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_rerun_execution_result_intake_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_intake_has_unsafe_fields(item)
            for item in value
        )
    return (
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            value
        )
        or _route_task_field_retest_execution_pack_has_success_wording(value)
    )


def _field_evidence_rerun_execution_result_review_decision_source_contract(value):
    # canonical summary 必须回指 result-review-decision gate，防止误消费 raw result/review packet。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(value):
    # review-decision alias 只接收白名单摘要；raw result/review、路径、topic、ACK 或硬件细节一律降级。
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
        "ack",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "review_status",
        "decision_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "review_decision",
        "decision",
        "intake_reference",
        "source_result_intake_schema",
        "source_result_intake_status",
        "same_evidence_ref_status",
        "blocker_reason",
        "rejection_reason",
        "backfill_reason",
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
        "control_entrypoint_enabled",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(item)
            for item in value
        )
    return (
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            value
        )
        or _route_task_field_retest_execution_pack_has_success_wording(value)
    )


def _field_evidence_rerun_execution_result_review_handoff_source_contract(value):
    # canonical summary 必须回指 review-handoff gate，避免 Robot 误消费上一层 review-decision raw 材料。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(value):
    # handoff safe alias 只暴露 owner 交接元数据；raw packet、topic、凭证、路径和控制语义全部阻断。
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
        "ack",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "handoff_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "source_review_decision",
        "source_review_decision_status",
        "review_status",
        "review_decision",
        "same_evidence_ref_status",
        "owner_handoff",
        "field_owner_handoff",
        "blocker_summary",
        "blocker_reason",
        "blockers",
        "next_required_real_materials",
        "next_required_evidence",
        "reconciliation_guidance",
        "rerun_guidance",
        "safe_rerun_guidance",
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
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    return (
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            value
        )
        or _route_task_field_retest_execution_pack_has_success_wording(value)
    )


def _field_evidence_rerun_execution_result_acceptance_packet_source_contract(value):
    # Robot 只消费 Autonomy 给出的 safe summary，并用 source_schema 回指验收包 gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_backfill_source_contract(value):
    # Robot 只消费 canonical safe summary；source_schema 必须回指补录 artifact 自身。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_source_contract(
    value,
):
    # review-decision 只能消费 canonical safe summary，不能直接信任 raw backfill 或完整 artifact。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_review_handoff_source_contract(
    value,
):
    # handoff alias 只接受 PC gate 的 canonical summary，raw handoff wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_source_contract(
    value,
):
    # intake alias 只接受 canonical safe summary，完整 intake wrapper 必须另带安全摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_source_contract(
    value,
):
    # review decision alias 只接受 canonical safe summary，完整 decision wrapper 必须另带安全摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_source_contract(
    value,
):
    # review handoff alias 只接受 canonical safe summary，完整 handoff wrapper 必须另带安全摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_source_contract(
    value,
):
    # follow-up status 只接受 canonical safe summary，完整 wrapper 必须另带安全摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if (
        source_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
    ):
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_source_contract(
    value,
):
    # owner response intake 只信任 PC safe summary、桥接 safe summary 或 Robot alias；raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        source_bridge = str(value.get("source_bridge") or "")
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
        if source_bridge == (
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_SOURCE
        ):
            # 桥接摘要仍复用 owner-response intake schema，但 proof boundary 必须指向本轮 bridge gate。
            source_boundary = str(
                value.get("source_evidence_boundary")
                or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_GATE
            )
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_source_contract(
    value,
):
    # owner response review decision 只信任 PC safe summary 或 Robot alias；raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source_contract(
    value,
):
    # owner response review handoff 只信任 PC safe summary 或 Robot alias；raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source_contract(
    value,
):
    # reviewer ACK intake 只接收 PC safe summary 或 Robot alias；raw wrapper 必须内嵌安全摘要。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source_contract(
    value,
):
    # reviewer ACK review-decision 只信任 sanitized summary 或 Robot alias；raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source_contract(
    value,
):
    # reviewer ACK review-handoff 只信任 sanitized summary 或 Robot alias；raw wrapper 必须另带 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source_contract(
    value,
):
    # follow-up escalation 只信任 Autonomy safe summary 或 Robot alias；raw wrapper 必须内嵌 safe summary。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        source_schema = str(
            value.get("source_schema")
            or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(value):
    # acceptance packet alias 不能透出 raw task/log/route/elevator/packet、路径、凭证或控制语义。
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
        "ack",
        "cursor",
        "traceback",
        "db_url",
        "queue_url",
        "oss",
        "task_record",
        "runtime_log",
        "route_artifact",
        "elevator_artifact",
        "complete_acceptance",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "acceptance_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "acceptance_verdict",
        "decision",
        "same_evidence_ref_required",
        "same_evidence_ref_status",
        "required_materials",
        "accepted_materials",
        "missing_materials",
        "blocked_materials",
        "owner_next_steps",
        "owner_handoff",
        "next_required_evidence",
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
        "field_evidence_rerun_execution_result_acceptance_packet_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
                item
            )
            for item in value
        )
    return (
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            value
        )
        or _route_task_field_retest_execution_pack_has_success_wording(value)
    )


def _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(value):
    # backfill alias 的允许面和 acceptance packet 一致，但要允许自己的 summary key。
    if isinstance(value, dict):
        safe_backfill_keys = {
            "field_evidence_rerun_execution_result_acceptance_backfill_summary",
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary",
            "backfill_status",
            "backfill_verdict",
        }
        safe_value = {
            key: item
            for key, item in value.items()
            if str(key or "") not in safe_backfill_keys
        }
        for key in safe_backfill_keys:
            item = value.get(key)
            if isinstance(item, (dict, list)):
                if _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(
                    item
                ):
                    return True
            elif item is not None and (
                _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
                    item
                )
                or _route_task_field_retest_execution_pack_has_success_wording(item)
            ):
                return True
        return _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
            safe_value
        )
    return _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
        value
    )


def _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
    value,
):
    # review-decision 只允许决策桶和 owner 下一步；raw manifest、路径、凭证和控制词全部阻断。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "decision",
        "decision_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "missing_categories",
        "rejected_categories",
        "owner_next_step",
        "owner_next_steps",
        "evidence_boundary_status",
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
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # not_proven 列表会包含“不是 delivery success”的否定原因；先归一化，避免把安全否定误判成成功宣称。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "hil pass",
        "real hil",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
    value,
):
    # handoff 对 Robot 只暴露白名单交接字段；raw、控制、外部证明和 PR 解决宣称全部闭锁。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "handoff_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "required_materials",
        "blocked_categories",
        "rejected_categories",
        "missing_categories",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
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
        "field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # not_proven 中允许安全否定句，先归一化以避免被 success/pass 关键字误伤。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
    value,
):
    # owner intake 只能暴露安全回执字段；raw artifact、控制、外部证明、HIL 和 PR 解决宣称一律拒绝。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "intake_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "accepted_material_refs",
        "required_checklist",
        "required_materials",
        "blocked_categories",
        "rejected_categories",
        "missing_categories",
        "owner_next_step",
        "support_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 安全否定句会包含 delivery success / HIL pass 字样，先归一化再做危险词扫描。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
    value,
):
    # review decision 只暴露安全判定摘要；raw、控制、外部证明、HIL 和 PR 解决宣称全部闭锁。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "review_decision_status",
        "source_intake_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "accepted_material_refs",
        "accepted_safe_material_refs",
        "missing_or_rework_reasons",
        "missing_reasons",
        "rework_reasons",
        "blocked_categories",
        "rejected_categories",
        "missing_categories",
        "owner_next_step",
        "support_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 安全否定句会包含 delivery success / HIL pass 字样，先归一化再做危险词扫描。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
    value,
):
    # review handoff 只暴露安全交接摘要；raw、控制、外部证明、HIL 和 PR 解决宣称全部闭锁。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "review_handoff_status",
        "source_review_decision_status",
        "status",
        "status_summary",
        "verdict",
        "reason",
        "accepted_material_refs",
        "accepted_safe_material_refs",
        "missing_or_rework_reasons",
        "missing_reasons",
        "rework_reasons",
        "blocked_categories",
        "rejected_categories",
        "missing_categories",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 安全否定句会包含 delivery success / HIL pass 字样，先归一化再做危险词扫描。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
    value,
):
    # follow-up escalation 只能镜像 safe status；任何 raw、控制、硬件或外部证明字段都闭锁。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "capability",
        "followup_state",
        "followup_status",
        "status",
        "status_summary",
        "followup_review_status",
        "source_review_handoff_status",
        "source_review_handoff_summary_status",
        "verdict",
        "reason",
        "pending_reason",
        "overdue_reason",
        "escalated_reason",
        "blocked_reason",
        "missing_required_material_refs",
        "missing_material_refs",
        "required_material_refs",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 允许 not_proven / false 字样；禁止把 follow-up 状态写成真实成功或控制可用。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "success/control",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
    value,
):
    # owner response intake 只能暴露安全分类和下一步，任何 raw/控制/硬件/外部证明字段都闭锁。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "capability",
        "source_bridge",
        "status",
        "overall_status",
        "owner_response_intake_status",
        "owner_response_status",
        "status_summary",
        "verdict",
        "reason",
        "source_followup_escalation_status",
        "source_followup_status",
        "accepted_material_refs",
        "missing_material_refs",
        "rejected_material_refs",
        "blocked_material_refs",
        "owner_route",
        "field_owner_route",
        "reviewer_route",
        "reviewer_support_route",
        "support_route",
        "operator_support_route",
        "next_required_field_owner_materials",
        "next_required_evidence",
        "false_state_flags",
        "ack_post_allowed",
        "cursor_updates_allowed",
        "nav2_triggered",
        "hil_pass",
        "accepted",
        "missing",
        "rejected",
        "blocked",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 允许 not_proven / false 字样；禁止把 owner response 分类写成真实通过或控制可用。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "raw artifact",
        "raw robot response",
        "ack payload",
        "cursor payload",
        "diagnostics fetch mutation",
        "github mutation",
        "robot command",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "field pass",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
    value,
):
    # review decision 只能暴露安全复核结论；raw、控制、外部证明、HIL、PR 解决宣称全部拒绝。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "capability",
        "status",
        "overall_status",
        "review_decision_status",
        "owner_response_review_decision_status",
        "status_summary",
        "verdict",
        "reason",
        "source_owner_response_intake_status",
        "source_owner_response_status",
        "accepted_material_refs",
        "missing_material_refs",
        "rejected_material_refs",
        "blocked_material_refs",
        "accepted",
        "missing",
        "rejected",
        "blocked",
        "decision_reasons",
        "missing_or_rework_reasons",
        "rework_reasons",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 允许否定式 proof 边界文案；禁止真实成功、控制、外部证明、HIL 和 PR resolved 语义。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "field pass",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "passed",
        " pass",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
    value,
):
    # handoff alias 只允许安全交接元数据；raw、控制、外部证明、HIL、PR resolved 语义全部拒绝。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "ack",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "capability",
        "status",
        "handoff_status",
        "overall_status",
        "review_handoff_status",
        "status_summary",
        "verdict",
        "reason",
        "source_owner_response_review_decision_status",
        "source_review_decision_status",
        "handoff_reasons",
        "decision_reasons",
        "next_required_evidence",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    # 允许否定式 proof 边界文案；禁止真实成功、控制、外部证明、HIL 和 PR resolved 语义。
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "field pass",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "delivery passed",
        "passed",
        " pass",
        "replay enabled",
        "resubmit enabled",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
    value,
):
    # reviewer ACK 允许 ACK reason 字段名，但仍拒绝 raw、控制、外部证明、HIL 和 PR resolved 语义。
    unsafe_key_fragments = (
        "raw",
        "manifest",
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
        "db_url",
        "queue_url",
        "oss",
        "control",
        "cursor",
        "command",
        "external",
        "hil",
        "pr_resolution",
        "reviewer_resolution",
        "replay",
        "resubmit",
    )
    safe_keys = {
        "schema",
        "schema_version",
        "source",
        "source_schema",
        "source_schema_version",
        "source_evidence_boundary",
        "evidence_boundary",
        "boundary",
        "proof_boundary",
        "safe_evidence_ref",
        "evidence_ref",
        "capability",
        "status",
        "ack_intake_status",
        "overall_status",
        "reviewer_ack_intake_status",
        "status_summary",
        "verdict",
        "reason",
        "source_owner_response_review_handoff_status",
        "source_review_handoff_status",
        "ack_reasons",
        "next_required_evidence",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
        "evidence_boundary_status",
        "robot_diagnostics_summary",
        "robot_compatible_summary",
        "safe_copy",
        "safe_phone_copy",
        "software_proof",
        "not_proven",
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "metadata_only",
        "boundary_flags",
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary",
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary",
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
            if _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
                item
            )
            for item in value
        )
    text = str(value or "").strip().lower()
    text = text.replace("not delivery success", "not_delivery_success")
    text = text.replace("not proven delivery success", "not_proven_delivery_success")
    text = text.replace("not hil pass", "not_hil_pass")
    text = text.replace("not proven hil pass", "not_proven_hil_pass")
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
        "db://",
        "queue://",
        "oss ak",
        "oss sk",
        "delivery success",
        "delivery_success=true",
        "primary_actions_enabled=true",
        "safe_to_control=true",
        "control enabled",
        "start delivery",
        "confirm dropoff",
        "cancel enabled",
        "external proof",
        "real external",
        "hil pass",
        "real hil",
        "field pass",
        "pr resolved",
        "pr reviewer resolved",
        "reviewer resolved",
        "delivery passed",
        "passed",
        " pass",
        "replay enabled",
        "resubmit enabled",
    )
    return any(marker in text for marker in unsafe_text_fragments)


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields(
    value,
):
    # 本 rung 沿用 reviewer ACK intake 的敏感词栅栏；review-decision 不能扩大 raw/control 暴露面。
    return _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
        value
    )


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields(
    value,
):
    # review-handoff 沿用 reviewer ACK intake 的敏感词栅栏，保证交接面不泄漏 raw artifact 或控制细节。
    return _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
        value
    )


def _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields(
    value,
):
    # follow-up escalation status 和前一 reviewer ACK rung 共用敏感词栅栏，避免新增 raw/control 暴露面。
    return _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
        value
    )


def summarize_field_evidence_rerun_material_dispatch(source):
    """构建 field evidence rerun material dispatch 的 Robot-safe metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        dispatch = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_material_dispatch_summary(
            source_path,
            read_error="field evidence rerun material dispatch is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "dispatch_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun material dispatch summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun material dispatch summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun material dispatch is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun material dispatch is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                dispatch = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "dispatch_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun material dispatch: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun material dispatch JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_material_dispatch_summary(
        source_path,
        read_error="field evidence rerun material dispatch is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(dispatch, dict):
        summary.update(
            {
                "dispatch_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun material dispatch JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun material dispatch JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = dispatch.get("diagnostics") if isinstance(dispatch.get("diagnostics"), dict) else {}
    # 只白名单读取 Autonomy 产出的 summary/robot alias；完整 artifact 只能作为包裹层。
    summary_fragment = (
        dispatch
        if str(dispatch.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            dispatch.get("robot_diagnostics_field_evidence_rerun_material_dispatch_summary"),
            dispatch.get("field_evidence_rerun_material_dispatch_summary"),
            dispatch.get("summary"),
            dispatch.get("diagnostics_summary"),
            dispatch.get("robot_diagnostics_summary"),
            dispatch.get("robot_compatible_summary"),
            dispatch.get("mobile_readonly_summary"),
            dispatch.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_material_dispatch_summary"),
            diagnostics.get("field_evidence_rerun_material_dispatch_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else dispatch
    source_schema, source_boundary = _field_evidence_rerun_material_dispatch_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": dispatch.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "dispatch_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun material dispatch lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun material dispatch summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("dispatch_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    dispatch_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("dispatch_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    dispatch_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or "field evidence rerun material dispatch consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun material dispatch is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # phone/Robot 两侧都用 literal false 做围栏，避免派发包被误读为控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(dispatch.get("safe_evidence_ref") or dispatch.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_work_orders = _safe_pc_route_debug_value(summary_fragment.get("owner_work_orders"))
    required_material_groups = _safe_pc_route_debug_value(
        summary_fragment.get("required_material_groups")
    )
    rerun_commands = _safe_pc_route_debug_value(summary_fragment.get("rerun_commands"))
    callback_packet_requirements = _safe_pc_route_debug_value(
        summary_fragment.get("callback_packet_requirements")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "dispatch_status": {
                "status": dispatch_status or "blocked",
                "verdict": "not_proven",
                "reason": dispatch_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "owner_work_orders": owner_work_orders,
            "required_material_groups": required_material_groups,
            "rerun_commands": rerun_commands,
            "callback_packet_requirements": callback_packet_requirements,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": dispatch_status or "blocked",
                "reason": "dispatch consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE,
            "not_proven": _field_evidence_rerun_material_dispatch_not_proven(
                dispatch,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        isinstance(owner_work_orders, list),
        isinstance(required_material_groups, list),
        isinstance(rerun_commands, list),
        isinstance(callback_packet_requirements, list),
        summary["same_evidence_ref_required"],
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            owner_work_orders,
            required_material_groups,
            rerun_commands,
            callback_packet_requirements,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_material_dispatch",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun material dispatch schema or boundary is unsupported",
                },
                "owner_work_orders": [],
                "required_material_groups": [],
                "rerun_commands": [],
                "callback_packet_requirements": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "dispatch_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun material dispatch evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "dispatch_status": {
                    "status": "blocked_missing_field_evidence_rerun_material_dispatch_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun material dispatch is missing required safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe dispatch fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(summary["boundary_flags"].get("raw_artifact_consumed"))
        or bool(summary["boundary_flags"].get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "dispatch_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_material_dispatch",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun material dispatch contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "owner_work_orders": [],
                "required_material_groups": [],
                "rerun_commands": [],
                "callback_packet_requirements": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun material dispatch fields",
                },
                "safe_copy": (
                    "Field evidence rerun material dispatch was blocked because summary "
                    "fields could imply control, ACK, Nav2/HIL, raw artifact access, "
                    "or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun material dispatch was blocked because summary "
                    "fields could imply control, ACK, Nav2/HIL, raw artifact access, "
                    "or delivery success."
                ),
            }
        )
    return summary


def _field_evidence_rerun_callback_intake_material_counts(summary_fragment):
    # Autonomy/Full-stack 可能用列表或 counts 字段表达材料状态；Robot 只保留四类数量。
    counts = {"accepted": 0, "missing": 0, "rejected": 0, "blocked": 0}
    for key in ("material_counts", "material_status_counts", "counts"):
        source_counts = summary_fragment.get(key)
        if isinstance(source_counts, dict):
            for status in counts:
                try:
                    counts[status] = max(counts[status], int(source_counts.get(status) or 0))
                except (TypeError, ValueError):
                    counts[status] = 0
    list_keys = (
        ("accepted", ("accepted_materials", "accepted_material_groups")),
        ("missing", ("missing_materials", "missing_material_groups")),
        ("rejected", ("rejected_materials", "rejected_material_groups")),
        ("blocked", ("blocked_materials", "blocked_material_groups")),
    )
    for status, keys in list_keys:
        for key in keys:
            value = summary_fragment.get(key)
            if isinstance(value, list):
                counts[status] = max(counts[status], len(value))
    materials = summary_fragment.get("materials") or summary_fragment.get("material_results")
    if isinstance(materials, list):
        # 列表型结果只读取 status/classification 字段，避免把 raw artifact 明细转发给 Robot。
        derived = {"accepted": 0, "missing": 0, "rejected": 0, "blocked": 0}
        for item in materials:
            if isinstance(item, dict):
                status = str(item.get("status") or item.get("classification") or "").strip()
                if status in derived:
                    derived[status] += 1
        for status in counts:
            counts[status] = max(counts[status], derived[status])
    return counts


def summarize_field_evidence_rerun_callback_intake(source):
    """构建 field evidence rerun callback intake 的 Robot-safe metadata-only 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_callback_intake_summary(
            source_path,
            read_error="field evidence rerun callback intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun callback intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback intake summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun callback intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun callback intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun callback intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_callback_intake_summary(
        source_path,
        read_error="field evidence rerun callback intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun callback intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # 只读取已消毒 summary；完整 artifact 只能作为包裹层提供 schema/boundary/ref。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "") == FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("robot_diagnostics_field_evidence_rerun_callback_intake_summary"),
            intake.get("field_evidence_rerun_callback_intake_summary"),
            intake.get("summary"),
            intake.get("diagnostics_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_callback_intake_summary"),
            diagnostics.get("field_evidence_rerun_callback_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = _field_evidence_rerun_callback_intake_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback intake lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun callback intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocked_reason")
        or summary_fragment.get("reason")
        or "field evidence rerun callback intake consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # Robot diagnostics 与 mobile 文案都依赖 literal false 字样作为安全围栏。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else summary_fragment.get("same_evidence_ref_result")
        if isinstance(summary_fragment.get("same_evidence_ref_result"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    source_raw_artifact_consumed = bool(boundary_flags.get("raw_artifact_consumed"))
    source_control_entrypoint_enabled = bool(boundary_flags.get("control_entrypoint_enabled"))
    material_counts = _field_evidence_rerun_callback_intake_material_counts(summary_fragment)
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else summary_fragment.get("next_required_materials")
        if isinstance(summary_fragment.get("next_required_materials"), list)
        else []
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "material_counts": material_counts,
            "accepted_material_count": material_counts["accepted"],
            "missing_material_count": material_counts["missing"],
            "rejected_material_count": material_counts["rejected"],
            "blocked_material_count": material_counts["blocked"],
            "next_required_evidence": next_required_evidence,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback intake lacks same evidence_ref status",
            },
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "callback intake consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "callback intake consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE,
            "not_proven": _field_evidence_rerun_callback_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        isinstance(next_required_evidence, list),
        summary["same_evidence_ref_required"],
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            next_required_evidence,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_callback_intake",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback intake schema or boundary is unsupported",
                },
                "material_counts": {"accepted": 0, "missing": 0, "rejected": 0, "blocked": 0},
                "accepted_material_count": 0,
                "missing_material_count": 0,
                "rejected_material_count": 0,
                "blocked_material_count": 0,
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback intake evidence_ref mismatch",
                },
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_missing_field_evidence_rerun_callback_intake_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback intake is missing required safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe callback intake fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or source_raw_artifact_consumed
        or source_control_entrypoint_enabled
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_callback_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun callback intake contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "material_counts": {"accepted": 0, "missing": 0, "rejected": 0, "blocked": 0},
                "accepted_material_count": 0,
                "missing_material_count": 0,
                "rejected_material_count": 0,
                "blocked_material_count": 0,
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun callback intake fields",
                },
                "safe_copy": (
                    "Field evidence rerun callback intake was blocked because summary "
                    "fields could imply control, ACK, Nav2/HIL, raw artifact access, "
                    "or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun callback intake was blocked because summary "
                    "fields could imply control, ACK, Nav2/HIL, raw artifact access, "
                    "or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_callback_review_decision(source):
    """构建 field evidence rerun callback review decision 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_callback_review_decision_summary(
            source_path,
            read_error="field evidence rerun callback review decision is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun callback review decision summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback review decision summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun callback review decision is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun callback review decision is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
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
                            f"failed reading field evidence rerun callback review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback review decision JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_callback_review_decision_summary(
        source_path,
        read_error="field evidence rerun callback review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review decision JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun callback review decision JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # 完整 artifact 只能作为包裹层；Robot 真正消费的字段必须来自 sanitized summary。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"),
            decision.get("field_evidence_rerun_callback_review_decision_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"),
            diagnostics.get("field_evidence_rerun_callback_review_decision_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = _field_evidence_rerun_callback_review_decision_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review decision lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun callback review decision summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun callback review decision consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # 下游 mobile panel 用 literal false 边界做文案和按钮安全判断。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else summary_fragment.get("same_evidence_ref_result")
        if isinstance(summary_fragment.get("same_evidence_ref_result"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    rerun_guidance = _safe_route_task_rehearsal_list(
        summary_fragment.get("rerun_guidance")
        if isinstance(summary_fragment.get("rerun_guidance"), list)
        else summary_fragment.get("rerun_commands")
        if isinstance(summary_fragment.get("rerun_commands"), list)
        else []
    )
    blocker_source = summary_fragment.get("blocker_summary")
    blocker_summary = _safe_route_task_rehearsal_list(
        blocker_source
        if isinstance(blocker_source, list)
        else [blocker_source]
        if blocker_source
        else []
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if review_decision not in ("accepted", "missing", "rejected", "blocked"):
        review_decision = "blocked"
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "review_decision": review_decision,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "rerun_guidance": rerun_guidance,
            "blocker_summary": blocker_summary,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback review decision lacks same evidence_ref status",
            },
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": "callback review decision consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": "callback review decision consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": _field_evidence_rerun_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        isinstance(owner_handoff, list),
        isinstance(next_required_evidence, list),
        isinstance(rerun_guidance, list),
        summary["same_evidence_ref_required"],
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            owner_handoff,
            next_required_evidence,
            rerun_guidance,
            blocker_summary,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_callback_review_decision",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review decision schema or boundary is unsupported",
                },
                "review_decision": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_callback_review_decision_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review decision evidence_ref mismatch",
                },
                "review_decision": "blocked",
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_missing_field_evidence_rerun_callback_review_decision_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review decision is missing required safe metadata",
                },
                "review_decision": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe callback review decision fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("raw_artifact_consumed"))
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "review_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_callback_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun callback review decision contains unsafe "
                        "fields, enabled actions, raw details, or success wording"
                    ),
                },
                "review_decision": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun callback review decision fields",
                },
                "safe_copy": (
                    "Field evidence rerun callback review decision was blocked because "
                    "summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun callback review decision was blocked because "
                    "summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_callback_review_handoff(source):
    """构建 field evidence rerun callback review handoff 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_callback_review_handoff_summary(
            source_path,
            read_error="field evidence rerun callback review handoff is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun callback review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback review handoff summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun callback review handoff is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun callback review handoff is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
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
                            f"failed reading field evidence rerun callback review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun callback review handoff JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_callback_review_handoff_summary(
        source_path,
        read_error="field evidence rerun callback review handoff is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review handoff JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun callback review handoff JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # 完整 artifact 只能作为包裹层；Robot 只读取 sanitized summary，避免接触 raw callback 材料。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"),
            handoff.get("field_evidence_rerun_callback_review_handoff_summary"),
            handoff.get("summary"),
            handoff.get("diagnostics_summary"),
            handoff.get("robot_diagnostics_summary"),
            handoff.get("robot_compatible_summary"),
            handoff.get("mobile_readonly_summary"),
            handoff.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"),
            diagnostics.get("field_evidence_rerun_callback_review_handoff_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = _field_evidence_rerun_callback_review_handoff_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": handoff.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review handoff lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun callback review handoff summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = {}
    handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    handoff_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun callback review handoff consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun callback review handoff is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # 下游只用 literal false 文案判定能否露出控制按钮，因此缺失时主动补齐。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(handoff.get("safe_evidence_ref") or handoff.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else summary_fragment.get("same_evidence_ref_result")
        if isinstance(summary_fragment.get("same_evidence_ref_result"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    rerun_guidance = _safe_route_task_rehearsal_list(
        summary_fragment.get("rerun_guidance")
        if isinstance(summary_fragment.get("rerun_guidance"), list)
        else summary_fragment.get("rerun_commands")
        if isinstance(summary_fragment.get("rerun_commands"), list)
        else []
    )
    blocker_source = summary_fragment.get("blocker_summary")
    blocker_summary = _safe_route_task_rehearsal_list(
        blocker_source
        if isinstance(blocker_source, list)
        else [blocker_source]
        if blocker_source
        else []
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if review_decision not in ("accepted", "missing", "rejected", "blocked"):
        review_decision = "blocked"
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": handoff_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "review_decision": review_decision,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "rerun_guidance": rerun_guidance,
            "blocker_summary": blocker_summary,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": "callback review handoff lacks same evidence_ref status",
            },
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                raw_artifact_consumed=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "callback review handoff consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "reason": "callback review handoff consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE,
            "not_proven": _field_evidence_rerun_callback_review_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        isinstance(owner_handoff, list) and bool(owner_handoff),
        isinstance(next_required_evidence, list),
        isinstance(rerun_guidance, list),
        isinstance(blocker_summary, list),
        summary["same_evidence_ref_required"],
    )
    unsafe_material = any(
        _route_task_field_retest_acceptance_execution_rerun_result_intake_has_unsafe_material(
            item
        )
        for item in (
            status_source,
            owner_handoff,
            next_required_evidence,
            rerun_guidance,
            blocker_summary,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_callback_review_handoff",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review handoff schema or boundary is unsupported",
                },
                "review_decision": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "handoff_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_callback_review_handoff_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review handoff evidence_ref mismatch",
                },
                "review_decision": "blocked",
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_missing_field_evidence_rerun_callback_review_handoff_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun callback review handoff is missing required safe metadata",
                },
                "review_decision": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe callback review handoff fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("raw_artifact_consumed"))
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _route_task_field_run_intake_has_unsafe_control_claims(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_callback_review_handoff",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun callback review handoff contains unsafe "
                        "fields, enabled actions, raw details, or success wording"
                    ),
                },
                "review_decision": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun callback review handoff fields",
                },
                "safe_copy": (
                    "Field evidence rerun callback review handoff was blocked because "
                    "summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, serial/UART/WAVE ROVER access, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun callback review handoff was blocked because "
                    "summary fields could imply control, ACK, Nav2/HIL, raw artifact "
                    "access, serial/UART/WAVE ROVER access, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_handoff_intake(source):
    """构建 field evidence rerun handoff intake 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_handoff_intake_summary(
            source_path,
            read_error="field evidence rerun handoff intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun handoff intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun handoff intake summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun handoff intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun handoff intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun handoff intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun handoff intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_handoff_intake_summary(
        source_path,
        read_error="field evidence rerun handoff intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun handoff intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun handoff intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # Robot 只能取 Autonomy/PC 裁剪后的 summary；完整 artifact 只是外层信封，不能透传 raw 字段。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "") == FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("robot_diagnostics_field_evidence_rerun_handoff_intake_summary"),
            intake.get("field_evidence_rerun_handoff_intake_summary"),
            intake.get("summary"),
            intake.get("diagnostics_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_handoff_intake_summary"),
            diagnostics.get("field_evidence_rerun_handoff_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = _field_evidence_rerun_handoff_intake_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun handoff intake lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun handoff intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun handoff intake consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun handoff intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # mobile/HTTP consumers use this literal as a visible fence, so Robot fills it in when absent.
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else summary_fragment.get("same_evidence_ref_result")
        if isinstance(summary_fragment.get("same_evidence_ref_result"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    rerun_guidance = _safe_route_task_rehearsal_list(
        summary_fragment.get("rerun_guidance")
        if isinstance(summary_fragment.get("rerun_guidance"), list)
        else summary_fragment.get("rerun_commands")
        if isinstance(summary_fragment.get("rerun_commands"), list)
        else []
    )
    blocker_source = summary_fragment.get("blocker_summary")
    blocker_summary = _safe_route_task_rehearsal_list(
        blocker_source
        if isinstance(blocker_source, list)
        else [blocker_source]
        if blocker_source
        else []
    )
    owner_ack_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("owner_ack_status")
        or summary_fragment.get("ack_status")
        or "blocked"
    )
    next_owner = _redact_route_task_rehearsal_text(summary_fragment.get("next_owner") or "")
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "owner_ack_status": owner_ack_status or "blocked",
            "next_owner": next_owner,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "rerun_guidance": rerun_guidance,
            "blocker_summary": blocker_summary,
            "same_evidence_ref_required": summary_fragment.get("same_evidence_ref_required") is True,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": "handoff intake lacks same evidence_ref status",
            },
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "handoff intake consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": "handoff intake consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE,
            "not_proven": _field_evidence_rerun_handoff_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["owner_ack_status"]),
        isinstance(owner_handoff, list) and bool(owner_handoff),
        isinstance(next_required_evidence, list),
        isinstance(rerun_guidance, list),
        isinstance(blocker_summary, list),
        summary["same_evidence_ref_required"],
    )
    unsafe_material = any(
        _field_evidence_rerun_handoff_intake_has_unsafe_fields(item)
        for item in (
            status_source,
            owner_ack_status,
            next_owner,
            owner_handoff,
            next_required_evidence,
            rerun_guidance,
            blocker_summary,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_handoff_intake",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun handoff intake schema or boundary is unsupported",
                },
                "owner_ack_status": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun handoff intake evidence_ref mismatch",
                },
                "owner_ack_status": "blocked",
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_missing_field_evidence_rerun_handoff_intake_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun handoff intake is missing required safe metadata",
                },
                "owner_ack_status": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe handoff intake fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("raw_artifact_consumed"))
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_handoff_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_handoff_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun handoff intake contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "owner_ack_status": "blocked",
                "owner_handoff": [],
                "next_required_evidence": [],
                "rerun_guidance": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun handoff intake fields",
                },
                "safe_copy": (
                    "Field evidence rerun handoff intake was blocked because summary "
                    "fields could expose unsanitized data, ROS topic, serial/UART/WAVE ROVER, "
                    "credential, checksum, local path, control, ACK, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun handoff intake was blocked because summary "
                    "fields could expose unsanitized data, ROS topic, serial/UART/WAVE ROVER, "
                    "credential, checksum, local path, control, ACK, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_queue(source):
    """构建 field evidence rerun queue 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        queue = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_queue_summary(
            source_path,
            read_error="field evidence rerun queue is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "queue_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun queue summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun queue summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun queue is missing; metadata remains "
                        "blocked/not_proven; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun queue is missing; metadata remains "
                        "blocked/not_proven; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                queue = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "queue_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun queue: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun queue JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_queue_summary(
        source_path,
        read_error="field evidence rerun queue is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(queue, dict):
        summary.update(
            {
                "queue_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun queue JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun queue JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = queue.get("diagnostics") if isinstance(queue.get("diagnostics"), dict) else {}
    # Robot 只消费 Autonomy/PC 已裁剪的 summary；artifact 外壳只用于找到 nested safe summary。
    summary_fragment = (
        queue if str(queue.get("schema") or "") == FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY_SCHEMA else {}
    )
    if not summary_fragment:
        for candidate in (
            queue.get("robot_diagnostics_field_evidence_rerun_queue_summary"),
            queue.get("field_evidence_rerun_queue_summary"),
            queue.get("summary"),
            queue.get("diagnostics_summary"),
            queue.get("robot_diagnostics_summary"),
            queue.get("robot_compatible_summary"),
            queue.get("mobile_readonly_summary"),
            queue.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_queue_summary"),
            diagnostics.get("field_evidence_rerun_queue_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else queue
    source_schema, source_boundary = _field_evidence_rerun_queue_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": queue.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "queue_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun queue lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun queue summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("queue_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("rerun_queue_status")
    if not isinstance(status_source, dict):
        status_source = {}
    queue_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("queue_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    queue_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun queue consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun queue is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # safe_phone_copy 是下游 grep/人工验收的护栏，缺 literal false 时由 Robot 补齐。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(queue.get("safe_evidence_ref") or queue.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    blocker_summary = _safe_route_task_rehearsal_list(
        summary_fragment.get("blocker_summary")
        if isinstance(summary_fragment.get("blocker_summary"), list)
        else [summary_fragment.get("blocker_summary")]
        if summary_fragment.get("blocker_summary")
        else []
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "queue_status": {
                "status": queue_status or "blocked",
                "verdict": "not_proven",
                "reason": queue_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_handoff_intake_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_intake_schema") or ""
            ),
            "source_handoff_intake_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_handoff_intake_status")
                if "source_handoff_intake_status" in summary_fragment
                else summary_fragment.get("handoff_intake_status")
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": queue_status or "blocked",
                "verdict": "not_proven",
                "reason": "field evidence rerun queue lacks same evidence_ref status",
            },
            "blocker_summary": blocker_summary,
            "next_required_evidence": next_required_evidence,
            "owner_handoff": owner_handoff,
            "safe_rerun_hint": _safe_pc_route_debug_value(
                summary_fragment.get("safe_rerun_hint")
                or summary_fragment.get("safe_rerun_command_summary")
                or summary_fragment.get("rerun_guidance")
            ),
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": queue_status or "blocked",
                "reason": "field evidence rerun queue consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": queue_status or "blocked",
                "reason": "field evidence rerun queue consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_QUEUE_GATE,
            "not_proven": _field_evidence_rerun_queue_not_proven(queue, summary_fragment),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["source_handoff_intake_schema"]),
        bool(summary["source_handoff_intake_status"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(blocker_summary, list) and bool(blocker_summary),
        isinstance(next_required_evidence, list) and bool(next_required_evidence),
        isinstance(owner_handoff, list) and bool(owner_handoff),
    )
    unsafe_material = any(
        _field_evidence_rerun_handoff_intake_has_unsafe_fields(item)
        for item in (
            status_source,
            owner_handoff,
            next_required_evidence,
            blocker_summary,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_QUEUE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_QUEUE_GATE
    ):
        summary.update(
            {
                "queue_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_queue",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun queue schema or boundary is unsupported",
                },
                "owner_handoff": [],
                "next_required_evidence": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "queue_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_queue_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun queue evidence_ref mismatch",
                },
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "queue_status": {
                    "status": "blocked_missing_field_evidence_rerun_queue_materials",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun queue is missing required safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe queue fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_handoff_intake_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "queue_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_queue",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun queue contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "owner_handoff": [],
                "next_required_evidence": [],
                "blocker_summary": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun queue fields",
                },
                "safe_copy": (
                    "Field evidence rerun queue was blocked because summary fields could "
                    "expose unsanitized data, hardware transport details, credential, "
                    "checksum, local path, control, ACK, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun queue was blocked because summary fields could "
                    "expose unsanitized data, hardware transport details, credential, "
                    "checksum, local path, control, ACK, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_execution_pack(source):
    """构建 field evidence rerun execution pack 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        pack = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_pack_summary(
            source_path,
            read_error="field evidence rerun execution pack is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun execution pack summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun execution pack summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun execution pack is missing; metadata remains "
                        "blocked/not_proven; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun execution pack is missing; metadata remains "
                        "blocked/not_proven; safe_to_control=false; delivery_success=false; "
                        "primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                pack = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "execution_pack_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun execution pack: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun execution pack JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_pack_summary(
        source_path,
        read_error="field evidence rerun execution pack is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(pack, dict):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun execution pack JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun execution pack JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = pack.get("diagnostics") if isinstance(pack.get("diagnostics"), dict) else {}
    # Robot 只消费 canonical execution-pack summary；完整 artifact 外壳只用于定位 nested safe summary。
    summary_fragment = (
        pack
        if str(pack.get("schema") or "") == FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            pack.get("robot_diagnostics_field_evidence_rerun_execution_pack_summary"),
            pack.get("field_evidence_rerun_execution_pack_summary"),
            pack.get("summary"),
            pack.get("diagnostics_summary"),
            pack.get("robot_diagnostics_summary"),
            pack.get("robot_compatible_summary"),
            pack.get("mobile_readonly_summary"),
            pack.get("phone_safe_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_execution_pack_summary"),
            diagnostics.get("field_evidence_rerun_execution_pack_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else pack
    source_schema, source_boundary = _field_evidence_rerun_execution_pack_source_contract(
        contract_source
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": pack.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "execution_pack_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun execution pack lacks a sanitized summary",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun execution pack summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("execution_pack_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("execution_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("pack_status")
    if not isinstance(status_source, dict):
        status_source = {}
    execution_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("execution_pack_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    execution_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun execution pack consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution pack is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # mobile/HTTP consumers use literal false fences during manual review, so Robot fills them in.
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(pack.get("safe_evidence_ref") or pack.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    execution_steps = _safe_route_task_rehearsal_list(
        summary_fragment.get("execution_steps")
        if isinstance(summary_fragment.get("execution_steps"), list)
        else []
    )
    material_templates = _safe_route_task_rehearsal_list(
        summary_fragment.get("material_templates")
        if isinstance(summary_fragment.get("material_templates"), list)
        else []
    )
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    fail_thresholds = _safe_route_task_rehearsal_list(
        summary_fragment.get("fail_thresholds")
        if isinstance(summary_fragment.get("fail_thresholds"), list)
        else []
    )
    pass_thresholds = _safe_route_task_rehearsal_list(
        summary_fragment.get("pass_thresholds")
        if isinstance(summary_fragment.get("pass_thresholds"), list)
        else []
    )
    backfill_instructions = _safe_route_task_rehearsal_list(
        summary_fragment.get("backfill_instructions")
        if isinstance(summary_fragment.get("backfill_instructions"), list)
        else []
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "execution_pack_status": {
                "status": execution_status or "blocked",
                "verdict": "not_proven",
                "reason": execution_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_queue_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_queue_schema") or ""
            ),
            "source_queue_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_queue_status")
                if "source_queue_status" in summary_fragment
                else summary_fragment.get("queue_status")
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": execution_status or "blocked",
                "verdict": "not_proven",
                "reason": "field evidence rerun execution pack lacks same evidence_ref status",
            },
            "execution_steps": execution_steps,
            "material_templates": material_templates,
            "owner_handoff": owner_handoff,
            "fail_thresholds": fail_thresholds,
            "pass_thresholds": pass_thresholds,
            "backfill_instructions": backfill_instructions,
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": execution_status or "blocked",
                "reason": "field evidence rerun execution pack consumed without robot diagnostics summary",
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": execution_status or "blocked",
                "reason": "field evidence rerun execution pack consumed without robot diagnostics summary",
            },
            "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE,
            "not_proven": _field_evidence_rerun_execution_pack_not_proven(
                pack,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["source_queue_schema"]),
        bool(summary["source_queue_status"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(execution_steps, list) and bool(execution_steps),
        isinstance(material_templates, list) and bool(material_templates),
        isinstance(owner_handoff, list) and bool(owner_handoff),
        isinstance(fail_thresholds, list) and bool(fail_thresholds),
        isinstance(pass_thresholds, list) and bool(pass_thresholds),
        isinstance(backfill_instructions, list) and bool(backfill_instructions),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_pack_has_unsafe_fields(item)
        for item in (
            status_source,
            execution_steps,
            material_templates,
            owner_handoff,
            fail_thresholds,
            pass_thresholds,
            backfill_instructions,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_execution_pack",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution pack schema or boundary is unsupported"
                    ),
                },
                "execution_steps": [],
                "material_templates": [],
                "owner_handoff": [],
                "fail_thresholds": [],
                "pass_thresholds": [],
                "backfill_instructions": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "execution_pack_status": {
                    "status": "evidence_ref_mismatch_field_evidence_rerun_execution_pack_blocked",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun execution pack evidence_ref mismatch",
                },
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "blocked_missing_field_evidence_rerun_execution_pack_materials",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution pack is missing required safe metadata"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe execution pack fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_pack_has_unsafe_fields(summary_fragment)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "execution_pack_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_execution_pack",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution pack contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "execution_steps": [],
                "material_templates": [],
                "owner_handoff": [],
                "fail_thresholds": [],
                "pass_thresholds": [],
                "backfill_instructions": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun execution pack fields",
                },
                "safe_copy": (
                    "Field evidence rerun execution pack was blocked because summary "
                    "fields could expose unsanitized data, ROS topic, serial/UART/WAVE ROVER, "
                    "credential, traceback, checksum, local path, HIL/pass wording, "
                    "control, ACK, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun execution pack was blocked because summary "
                    "fields could expose unsanitized data, ROS topic, serial/UART/WAVE ROVER, "
                    "credential, traceback, checksum, local path, HIL/pass wording, "
                    "control, ACK, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_execution_callback_intake(source):
    """构建 field evidence rerun execution callback intake 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_callback_intake_summary(
            source_path,
            read_error="field evidence rerun execution callback intake is not configured",
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": "field evidence rerun execution callback intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun execution callback intake summary missing",
                    },
                    "safe_copy": (
                        "Field evidence rerun execution callback intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun execution callback intake is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            f"failed reading field evidence rerun execution callback intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "field evidence rerun execution callback intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_callback_intake_summary(
        source_path,
        read_error="field evidence rerun execution callback intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": "field evidence rerun execution callback intake JSON must be an object",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "field evidence rerun execution callback intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # Robot 优先消费 canonical callback-intake summary；artifact 外壳只用于定位已消毒摘要。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get(
                "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary"
            ),
            intake.get("field_evidence_rerun_execution_callback_intake_summary"),
            intake.get("summary"),
            intake.get("diagnostics_summary"),
            intake.get("robot_diagnostics_summary"),
            intake.get("robot_compatible_summary"),
            intake.get("mobile_readonly_summary"),
            intake.get("phone_safe_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary"
            ),
            diagnostics.get("field_evidence_rerun_execution_callback_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_callback_intake_source_contract(contract_source)
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": intake.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback intake lacks a sanitized summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing sanitized field evidence rerun execution callback intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("callback_intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    intake_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun execution callback intake consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution callback intake is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # safe_phone_copy 保留 literal false，避免 mobile/HTTP 把回执入口误读成控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(intake.get("safe_evidence_ref") or intake.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    accepted_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("accepted_materials")
        if isinstance(summary_fragment.get("accepted_materials"), list)
        else []
    )
    missing_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_materials")
        if isinstance(summary_fragment.get("missing_materials"), list)
        else []
    )
    rejected_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("rejected_materials")
        if isinstance(summary_fragment.get("rejected_materials"), list)
        else []
    )
    blocked_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("blocked_materials")
        if isinstance(summary_fragment.get("blocked_materials"), list)
        else []
    )
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "intake_status": {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": intake_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_execution_pack_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_execution_pack_schema") or ""
            ),
            "source_execution_pack_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_execution_pack_status")
                if "source_execution_pack_status" in summary_fragment
                else summary_fragment.get("execution_pack_status")
            ),
            "callback_packet_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("callback_packet_schema") or ""
            ),
            "callback_packet_status": _safe_pc_route_debug_value(
                summary_fragment.get("callback_packet_status")
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": intake_status or "blocked",
                "verdict": "not_proven",
                "reason": "field evidence rerun execution callback intake lacks same evidence_ref status",
            },
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "blocked_materials": blocked_materials,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": (
                    "field evidence rerun execution callback intake consumed without "
                    "robot diagnostics summary"
                ),
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "reason": (
                    "field evidence rerun execution callback intake consumed without "
                    "robot diagnostics summary"
                ),
            },
            "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE,
            "not_proven": _field_evidence_rerun_execution_callback_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["source_execution_pack_schema"]),
        bool(summary["source_execution_pack_status"]),
        bool(summary["callback_packet_schema"]),
        bool(summary["callback_packet_status"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(accepted_materials, list),
        isinstance(missing_materials, list),
        isinstance(rejected_materials, list),
        isinstance(blocked_materials, list),
        isinstance(owner_handoff, list) and bool(owner_handoff),
        isinstance(next_required_evidence, list) and bool(next_required_evidence),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_callback_intake_has_unsafe_fields(item)
        for item in (
            status_source,
            accepted_materials,
            missing_materials,
            rejected_materials,
            blocked_materials,
            owner_handoff,
            next_required_evidence,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsupported_field_evidence_rerun_execution_callback_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback intake schema or boundary is unsupported"
                    ),
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "blocked_materials": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "intake_status": {
                    "status": (
                        "evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked"
                    ),
                    "verdict": "not_proven",
                    "reason": "field evidence rerun execution callback intake evidence_ref mismatch",
                },
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_missing_field_evidence_rerun_execution_callback_intake_materials",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback intake is missing required safe metadata"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe execution callback intake fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_callback_intake_has_unsafe_fields(
            summary_fragment
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_execution_callback_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback intake contains unsafe fields, "
                        "enabled actions, raw details, or success wording"
                    ),
                },
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "blocked_materials": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsafe field evidence rerun execution callback intake fields",
                },
                "safe_copy": (
                    "Field evidence rerun execution callback intake was blocked because "
                    "summary fields could expose raw artifacts, ROS topic, /cmd_vel, "
                    "serial/UART/WAVE ROVER, credentials, local paths, checksums, "
                    "tracebacks, HIL/pass wording, ACK/cursor/control, or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun execution callback intake was blocked because "
                    "summary fields could expose raw artifacts, ROS topic, /cmd_vel, "
                    "serial/UART/WAVE ROVER, credentials, local paths, checksums, "
                    "tracebacks, HIL/pass wording, ACK/cursor/control, or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_execution_callback_review_decision(source):
    """构建 field evidence rerun execution callback review decision 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_callback_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution callback review decision is not configured"
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
                        "reason": (
                            "field evidence rerun execution callback review decision summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": (
                            "field evidence rerun execution callback review decision summary missing"
                        ),
                    },
                    "safe_copy": (
                        "Field evidence rerun execution callback review decision is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
                    "safe_phone_copy": (
                        "Field evidence rerun execution callback review decision is missing; "
                        "metadata remains blocked/not_proven; safe_to_control=false; "
                        "delivery_success=false; primary_actions_enabled=false."
                    ),
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
                            "failed reading field evidence rerun execution callback "
                            f"review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": (
                            "field evidence rerun execution callback review decision JSON read error"
                        ),
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_callback_review_decision_summary(
        source_path,
        read_error="field evidence rerun execution callback review decision is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": (
                        "field evidence rerun execution callback review decision JSON shape is invalid"
                    ),
                },
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot 只消费 canonical review-decision summary；artifact 外壳只用于定位已消毒摘要。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get(
                "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary"
            ),
            decision.get("field_evidence_rerun_execution_callback_review_decision_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            decision.get("robot_diagnostics_summary"),
            decision.get("robot_compatible_summary"),
            decision.get("mobile_readonly_summary"),
            decision.get("phone_safe_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary"
            ),
            diagnostics.get("field_evidence_rerun_execution_callback_review_decision_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_callback_review_decision_source_contract(
            contract_source
        )
    )
    if not summary_fragment:
        summary.update(
            {
                "source_schema": _redact_route_task_rehearsal_text(source_schema),
                "source_schema_version": decision.get("schema_version"),
                "source_evidence_boundary": _redact_route_task_rehearsal_text(
                    source_boundary
                ),
                "review_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision lacks a sanitized summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": (
                        "missing sanitized field evidence rerun execution callback review decision summary"
                    ),
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or status_source.get("verdict")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    review_reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or status_source.get("summary")
        or summary_fragment.get("blocker_summary")
        or summary_fragment.get("blocked_reason")
        or "field evidence rerun execution callback review decision consumed without explicit reason"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution callback review decision is metadata-only; "
            "source=software_proof; not_proven; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "safe_to_control=false" not in safe_copy_text:
        # mobile/HTTP 只认 literal false 边界；缺失时主动补齐，避免复核 ready 被误读为可控。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    source_ref = str(decision.get("safe_evidence_ref") or decision.get("evidence_ref") or "").strip()
    summary_ref = str(
        summary_fragment.get("safe_evidence_ref") or summary_fragment.get("evidence_ref") or ""
    ).strip()
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else diagnostics.get("robot_diagnostics_summary")
        if isinstance(diagnostics.get("robot_diagnostics_summary"), dict)
        else {}
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else summary_fragment.get("same_evidence_ref_match")
        if isinstance(summary_fragment.get("same_evidence_ref_match"), dict)
        else {}
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    accepted_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("accepted_materials")
        if isinstance(summary_fragment.get("accepted_materials"), list)
        else []
    )
    missing_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("missing_materials")
        if isinstance(summary_fragment.get("missing_materials"), list)
        else []
    )
    rejected_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("rejected_materials")
        if isinstance(summary_fragment.get("rejected_materials"), list)
        else []
    )
    blocked_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("blocked_materials")
        if isinstance(summary_fragment.get("blocked_materials"), list)
        else []
    )
    decision_reasons = _safe_route_task_rehearsal_list(
        summary_fragment.get("decision_reasons")
        if isinstance(summary_fragment.get("decision_reasons"), list)
        else [summary_fragment.get("decision_reason")]
        if summary_fragment.get("decision_reason")
        else []
    )
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if isinstance(summary_fragment.get("owner_handoff"), list)
        else [summary_fragment.get("owner_handoff")]
        if summary_fragment.get("owner_handoff")
        else []
    )
    next_required_evidence = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_evidence")
        if isinstance(summary_fragment.get("next_required_evidence"), list)
        else []
    )
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if review_decision not in (
        "ready",
        "missing",
        "rejected",
        "blocked",
        "unsupported",
        "unsafe",
        "mismatch",
        "source_not_ready",
    ):
        review_decision = "blocked"
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": contract_source.get("schema_version"),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "review_status": {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": review_reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(summary_ref or source_ref),
            "source_callback_intake_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_callback_intake_schema") or ""
            ),
            "source_callback_intake_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_callback_intake_status")
                if "source_callback_intake_status" in summary_fragment
                else summary_fragment.get("intake_status")
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": (
                    "field evidence rerun execution callback review decision lacks "
                    "same evidence_ref status"
                ),
            },
            "review_decision": review_decision,
            "accepted_materials": accepted_materials,
            "missing_materials": missing_materials,
            "rejected_materials": rejected_materials,
            "blocked_materials": blocked_materials,
            "decision_reasons": decision_reasons,
            "owner_handoff": owner_handoff,
            "next_required_evidence": next_required_evidence,
            "boundary_flags": dict(
                boundary_flags,
                metadata_only=True,
                source=EVIDENCE_SOURCE_SOFTWARE,
                safe_to_control=False,
                delivery_success=False,
                primary_actions_enabled=False,
                control_entrypoint_enabled=False,
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": (
                    "field evidence rerun execution callback review decision consumed "
                    "without robot diagnostics summary"
                ),
            },
            "robot_compatible_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "reason": (
                    "field evidence rerun execution callback review decision consumed "
                    "without robot diagnostics summary"
                ),
            },
            "boundary": FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
            "not_proven": _field_evidence_rerun_execution_callback_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    disabled_flags = (
        summary_fragment.get("safe_to_control") is False
        and summary_fragment.get("delivery_success") is False
        and summary_fragment.get("primary_actions_enabled") is False
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["source_callback_intake_schema"]),
        bool(summary["source_callback_intake_status"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(accepted_materials, list),
        isinstance(missing_materials, list),
        isinstance(rejected_materials, list),
        isinstance(blocked_materials, list),
        isinstance(decision_reasons, list) and bool(decision_reasons),
        isinstance(owner_handoff, list) and bool(owner_handoff),
        isinstance(next_required_evidence, list) and bool(next_required_evidence),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields(item)
        for item in (
            status_source,
            accepted_materials,
            missing_materials,
            rejected_materials,
            blocked_materials,
            decision_reasons,
            owner_handoff,
            next_required_evidence,
            same_ref_source,
            safe_copy,
            safe_copy_text,
            robot_summary,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_callback_review_decision"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision schema "
                        "or boundary is unsupported"
                    ),
                },
                "review_decision": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "blocked_materials": [],
                "decision_reasons": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported schema or evidence boundary",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary.update(
            {
                "review_status": {
                    "status": (
                        "evidence_ref_mismatch_field_evidence_rerun_execution_callback_review_decision_blocked"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision evidence_ref mismatch"
                    ),
                },
                "review_decision": "blocked",
                "same_evidence_ref_status": {
                    "status": "mismatch",
                    "verdict": "not_proven",
                    "reason": "same evidence_ref mismatch",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "same evidence_ref mismatch",
                },
            }
        )
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_missing_field_evidence_rerun_execution_callback_review_decision_materials"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision is missing required safe metadata"
                    ),
                },
                "review_decision": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required safe execution callback review decision fields",
                },
            }
        )
        return summary
    if (
        not disabled_flags
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy)
        or _route_task_field_run_readiness_copy_is_unsafe(safe_copy_text)
        or _route_task_field_retest_execution_pack_has_success_wording(summary_fragment)
    ):
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_rerun_execution_callback_review_decision"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review decision contains "
                        "unsafe fields, enabled actions, raw details, or success wording"
                    ),
                },
                "review_decision": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "blocked_materials": [],
                "decision_reasons": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": (
                        "unsafe field evidence rerun execution callback review decision fields"
                    ),
                },
                "safe_copy": (
                    "Field evidence rerun execution callback review decision was blocked "
                    "because summary fields could expose raw artifacts, ROS topic, "
                    "/cmd_vel, serial/UART/WAVE ROVER, credentials, local paths, "
                    "checksums, tracebacks, HIL/pass wording, ACK/cursor/control, "
                    "or delivery success."
                ),
                "safe_phone_copy": (
                    "Field evidence rerun execution callback review decision was blocked "
                    "because summary fields could expose raw artifacts, ROS topic, "
                    "/cmd_vel, serial/UART/WAVE ROVER, credentials, local paths, "
                    "checksums, tracebacks, HIL/pass wording, ACK/cursor/control, "
                    "or delivery success."
                ),
            }
        )
    return summary


def summarize_field_evidence_rerun_execution_callback_review_handoff(source):
    """构建 field evidence rerun execution callback review handoff 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_callback_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution callback review handoff is not configured"
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
                        "reason": (
                            "field evidence rerun execution callback review handoff summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": (
                            "field evidence rerun execution callback review handoff summary missing"
                        ),
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
                            "failed reading field evidence rerun execution callback "
                            f"review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": (
                            "field evidence rerun execution callback review handoff JSON read error"
                        ),
                    },
                }
            )
            return summary

    if not isinstance(handoff, dict):
        summary = _default_field_evidence_rerun_execution_callback_review_handoff_summary(
            source_path,
            read_error="field evidence rerun execution callback review handoff is invalid",
        )
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution callback review handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": (
                        "field evidence rerun execution callback review handoff JSON shape is invalid"
                    ),
                },
            }
        )
        return summary

    # 旧 handoff 路径已有严格白名单和 raw-material 拒绝逻辑；这里仅映射新 rung 名称后复用。
    base_handoff = _execution_callback_review_handoff_replace(
        handoff,
        _EXECUTION_CALLBACK_REVIEW_HANDOFF_TO_BASE_HANDOFF,
    )
    base_summary = summarize_field_evidence_rerun_callback_review_handoff(base_handoff)
    summary = _execution_callback_review_handoff_replace(
        base_summary,
        _BASE_HANDOFF_TO_EXECUTION_CALLBACK_REVIEW_HANDOFF,
    )
    summary["schema"] = FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA
    summary["evidence_boundary"] = FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE
    summary["boundary"] = FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE
    if summary.get("source_schema") == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA:
        summary["source_schema"] = FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA
    if summary.get("source_evidence_boundary") == FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE:
        summary["source_evidence_boundary"] = (
            FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE
        )
    if isinstance(summary.get("boundary_flags"), dict):
        # 新 execution alias 不向 diagnostics 暴露任何 raw-artifact 词面，哪怕值为 false。
        summary["boundary_flags"].pop("raw_artifact_consumed", None)
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    summary["not_proven"] = (
        _field_evidence_rerun_execution_callback_review_handoff_not_proven(
            handoff,
            summary,
        )
    )
    return _strip_execution_callback_review_handoff_forbidden_terms(summary)


def summarize_field_evidence_rerun_execution_result_intake(source):
    """构建 field evidence rerun execution result intake 的 Robot-safe 只读摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_intake_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result intake is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "result_intake_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "field evidence rerun execution result intake summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result intake summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "result_intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result "
                            f"intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_intake_summary(
        source_path,
        read_error="field evidence rerun execution result intake is not configured",
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "result_intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result intake JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = intake.get("diagnostics") if isinstance(intake.get("diagnostics"), dict) else {}
    # Robot 只优先消费 canonical summary 或 Robot alias；raw result packet 本体不会被直接当成安全摘要。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get("field_evidence_rerun_execution_result_intake_summary"),
            intake.get("robot_diagnostics_field_evidence_rerun_execution_result_intake_summary"),
            intake.get("robot_compatible_summary"),
            diagnostics.get("field_evidence_rerun_execution_result_intake_summary"),
            diagnostics.get("robot_diagnostics_field_evidence_rerun_execution_result_intake_summary"),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_intake_source_contract(contract_source)
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
                "result_intake_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result intake lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("result_intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("result_intake_status")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result intake consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result intake is metadata-only; "
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
        # 手机和 diagnostics grep 都依赖 literal false，避免把结果回填误当控制授权。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "result_intake_status": {
                "status": intake_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "missing_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_reasons")
                or summary_fragment.get("missing_materials")
            ),
            "rejected_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_reasons")
                or summary_fragment.get("rejected_materials")
            ),
            "blocked_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_reasons")
                or summary_fragment.get("blocked_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_rerun_execution_result_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_GATE
    ):
        summary["result_intake_status"] = {
            "status": "unsupported_schema",
            "verdict": "not_proven",
            "reason": (
                "field evidence rerun execution result intake schema or evidence boundary is unsupported"
            ),
        }
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "unsupported execution result intake schema or boundary",
        }
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["result_intake_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_intake",
            "verdict": "not_proven",
            "reason": "execution result intake must remain software_proof and not_proven",
        }
        return summary
    if not summary["safe_evidence_ref"] or summary["safe_evidence_ref"].startswith(
        "local_path_redacted:"
    ):
        summary["result_intake_status"] = {
            "status": "missing_evidence_ref",
            "verdict": "not_proven",
            "reason": "execution result intake is missing a safe evidence_ref",
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["result_intake_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_rerun_execution_result_intake_blocked",
            "verdict": "not_proven",
            "reason": "execution result intake evidence_ref values do not match",
        }
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or _field_evidence_rerun_execution_result_intake_has_unsafe_fields(intake)
        or _field_evidence_rerun_execution_result_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result intake was blocked because "
            "summary fields could expose raw result packet material, control data, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "result_intake_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_execution_result_intake",
                    "verdict": "not_proven",
                    "reason": "unsafe raw packet, control, path, credential, or success material",
                },
                "owner_handoff": [],
                "missing_reasons": [],
                "rejected_reasons": [],
                "blocked_reasons": [],
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


def summarize_field_evidence_rerun_execution_result_review_decision(source):
    """构建 field evidence rerun execution result review decision 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result review decision is not configured"
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
                        "reason": (
                            "field evidence rerun execution result review decision summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result review decision summary missing",
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
                            "failed reading field evidence rerun execution result "
                            f"review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result review decision JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_review_decision_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result review decision is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result review decision JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = decision.get("diagnostics") if isinstance(decision.get("diagnostics"), dict) else {}
    # Robot 只消费 canonical/safe summary；raw review/result packet 本体只能用于找嵌套摘要。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get("field_evidence_rerun_execution_result_review_decision_summary"),
            decision.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            diagnostics.get("field_evidence_rerun_execution_result_review_decision_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_review_decision_source_contract(
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
                    "reason": (
                        "field evidence rerun execution result review decision lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result review decision summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("review_status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result review decision consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result review decision is metadata-only; "
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
        # safe copy 是跨 diagnostics/mobile 的硬边界，缺 literal false 时主动补齐。
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
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or summary_fragment.get("decision")
        or "blocked"
    )
    if review_decision not in (
        "accepted_for_review",
        "needs_material_backfill",
        "rejected",
        "blocked",
    ):
        review_decision = "blocked"
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
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
            "intake_reference": _redact_route_task_rehearsal_text(
                summary_fragment.get("intake_reference") or ""
            ),
            "source_result_intake_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_result_intake_schema") or ""
            ),
            "source_result_intake_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_result_intake_status")
                if "source_result_intake_status" in summary_fragment
                else summary_fragment.get("result_intake_status")
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": review_status or "blocked",
                "verdict": "not_proven",
                "reason": "execution result review decision lacks same evidence_ref status",
            },
            "blocker_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocker_reason") or ""
            ),
            "rejection_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("rejection_reason") or ""
            ),
            "backfill_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("backfill_reason") or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_rerun_execution_result_review_decision_not_proven(
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
        bool(summary["review_decision"]),
        bool(summary["intake_reference"]),
        bool(summary["source_result_intake_schema"]),
        bool(summary["source_result_intake_status"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(summary["next_required_evidence"], list)
        and bool(summary["next_required_evidence"]),
        isinstance(summary["owner_handoff"], list) and bool(summary["owner_handoff"]),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(item)
        for item in (
            status_source,
            same_ref_source,
            summary["source_result_intake_status"],
            summary["blocker_reason"],
            summary["rejection_reason"],
            summary["backfill_reason"],
            summary["next_required_evidence"],
            summary["owner_handoff"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_result_review_decision"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result review decision schema "
                        "or boundary is unsupported"
                    ),
                },
                "review_decision": "blocked",
                "next_required_evidence": [],
                "owner_handoff": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result review decision schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["review_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_review_decision",
            "verdict": "not_proven",
            "reason": "execution result review decision must remain software_proof and not_proven",
        }
        summary["review_decision"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_missing_field_evidence_rerun_execution_result_review_decision_materials"
                    ),
                    "verdict": "not_proven",
                    "reason": "execution result review decision is missing required safe metadata",
                },
                "review_decision": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result review decision fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_status"] = {
            "status": (
                "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_decision_blocked"
            ),
            "verdict": "not_proven",
            "reason": "execution result review decision evidence_ref values do not match",
        }
        summary["review_decision"] = "blocked"
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
        or _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(
            decision
        )
        or _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result review decision was blocked because "
            "summary fields could expose raw result/review material, control data, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_rerun_execution_result_review_decision"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw review/result, control, path, credential, or success material"
                    ),
                },
                "review_decision": "blocked",
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


def summarize_field_evidence_rerun_execution_result_review_handoff(source):
    """构建 field evidence rerun execution result review handoff 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result review handoff is not configured"
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
                        "reason": (
                            "field evidence rerun execution result review handoff summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result review handoff summary missing",
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
                            "failed reading field evidence rerun execution result "
                            f"review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result review handoff JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_review_handoff_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result review handoff is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result review handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result review handoff JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = handoff.get("diagnostics") if isinstance(handoff.get("diagnostics"), dict) else {}
    # Robot 只信任 Autonomy 裁剪后的 handoff summary；raw review-decision/result packet 不进入输出。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get("field_evidence_rerun_execution_result_review_handoff_summary"),
            handoff.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary"
            ),
            handoff.get("robot_compatible_summary"),
            handoff.get("summary"),
            handoff.get("diagnostics_summary"),
            diagnostics.get("field_evidence_rerun_execution_result_review_handoff_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_review_handoff_source_contract(
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
                "handoff_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result review handoff lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result review handoff summary",
                },
            }
        )
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
        or "field evidence rerun execution result review handoff consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result review handoff is metadata-only; "
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
        # safe copy 会直接流向 operator/mobile；缺 false literal 时主动补齐，避免误读为实机通过。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
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
    source_review_decision_status = _safe_pc_route_debug_value(
        summary_fragment.get("source_review_decision_status")
        if "source_review_decision_status" in summary_fragment
        else summary_fragment.get("review_status")
    )
    same_ref_source = (
        summary_fragment.get("same_evidence_ref_status")
        if isinstance(summary_fragment.get("same_evidence_ref_status"), dict)
        else {}
    )
    source_review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_review_decision")
        or summary_fragment.get("review_decision")
        or "blocked"
    )
    owner_handoff = _safe_route_task_rehearsal_list(
        summary_fragment.get("owner_handoff")
        if "owner_handoff" in summary_fragment
        else summary_fragment.get("field_owner_handoff")
    )
    next_required_real_materials = _safe_route_task_rehearsal_list(
        summary_fragment.get("next_required_real_materials")
        if "next_required_real_materials" in summary_fragment
        else summary_fragment.get("next_required_evidence")
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "handoff_status": {
                "status": handoff_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "source_review_decision": source_review_decision or "blocked",
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "source_review_decision_status": source_review_decision_status,
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": handoff_status or "blocked",
                "verdict": "not_proven",
                "reason": "execution result review handoff lacks same evidence_ref status",
            },
            "owner_handoff": owner_handoff,
            "blocker_summary": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocker_summary")
                or summary_fragment.get("blocker_reason")
                or ""
            ),
            "next_required_real_materials": next_required_real_materials,
            "reconciliation_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("reconciliation_guidance")
            ),
            "rerun_guidance": _safe_route_task_rehearsal_list(
                summary_fragment.get("rerun_guidance")
                if "rerun_guidance" in summary_fragment
                else summary_fragment.get("safe_rerun_guidance")
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_rerun_execution_result_review_handoff_not_proven(
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
        bool(summary["source_review_decision"]),
        bool(summary["source_review_decision_status"]),
        isinstance(summary["owner_handoff"], list) and bool(summary["owner_handoff"]),
        bool(summary["blocker_summary"]),
        isinstance(summary["next_required_real_materials"], list)
        and bool(summary["next_required_real_materials"]),
        isinstance(summary["reconciliation_guidance"], list)
        and bool(summary["reconciliation_guidance"]),
        isinstance(summary["rerun_guidance"], list) and bool(summary["rerun_guidance"]),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(item)
        for item in (
            status_source,
            source_review_decision_status,
            same_ref_source,
            summary["owner_handoff"],
            summary["blocker_summary"],
            summary["next_required_real_materials"],
            summary["reconciliation_guidance"],
            summary["rerun_guidance"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_result_review_handoff"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result review handoff schema "
                        "or boundary is unsupported"
                    ),
                },
                "source_review_decision": "blocked",
                "owner_handoff": [],
                "next_required_real_materials": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result review handoff schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["handoff_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_review_handoff",
            "verdict": "not_proven",
            "reason": "execution result review handoff must remain software_proof and not_proven",
        }
        summary["source_review_decision"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "handoff_status": {
                    "status": (
                        "blocked_missing_field_evidence_rerun_execution_result_review_handoff_materials"
                    ),
                    "verdict": "not_proven",
                    "reason": "execution result review handoff is missing required safe metadata",
                },
                "source_review_decision": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result review handoff fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["handoff_status"] = {
            "status": (
                "evidence_ref_mismatch_field_evidence_rerun_execution_result_review_handoff_blocked"
            ),
            "verdict": "not_proven",
            "reason": "execution result review handoff evidence_ref values do not match",
        }
        summary["source_review_decision"] = "blocked"
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
        or _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(
            handoff
        )
        or _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result review handoff was blocked because "
            "summary fields could expose raw review-decision/result material, control "
            "data, or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_rerun_execution_result_review_handoff"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw review/result, control, path, credential, or success material"
                    ),
                },
                "source_review_decision": "blocked",
                "owner_handoff": [],
                "next_required_real_materials": [],
                "reconciliation_guidance": [],
                "rerun_guidance": [],
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


def summarize_field_evidence_rerun_execution_result_acceptance_packet(source):
    """构建 field evidence rerun execution result acceptance packet 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        packet = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_packet_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance packet is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "acceptance_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "field evidence rerun execution result acceptance packet summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance packet summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                packet = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "acceptance_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result "
                            f"acceptance packet: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance packet JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_packet_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance packet is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(packet, dict):
        summary.update(
            {
                "acceptance_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance packet JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance packet JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = packet.get("diagnostics") if isinstance(packet.get("diagnostics"), dict) else {}
    # 只信任 canonical safe summary；complete packet / raw task records / route logs 不进入 Robot 输出。
    summary_fragment = (
        packet
        if str(packet.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            packet.get("field_evidence_rerun_execution_result_acceptance_packet_summary"),
            packet.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary"
            ),
            packet.get("robot_compatible_summary"),
            packet.get("summary"),
            packet.get("diagnostics_summary"),
            diagnostics.get("field_evidence_rerun_execution_result_acceptance_packet_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else packet
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_packet_source_contract(
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
                "acceptance_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance packet lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance packet summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("acceptance_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    acceptance_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("acceptance_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance packet consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance packet is metadata-only; "
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
        # safe_copy 是用户可见边界，强制补齐 false literal 以防误读为验收通过。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        packet.get("safe_evidence_ref") or packet.get("evidence_ref") or ""
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
    owner_steps_source = (
        summary_fragment.get("owner_next_steps")
        if "owner_next_steps" in summary_fragment
        else summary_fragment.get("owner_handoff")
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "acceptance_status": {
                "status": acceptance_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "acceptance_verdict": _redact_route_task_rehearsal_text(
                summary_fragment.get("acceptance_verdict")
                or summary_fragment.get("decision")
                or acceptance_status
                or "blocked"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": acceptance_status or "blocked",
                "verdict": "not_proven",
                "reason": "execution result acceptance packet lacks same evidence_ref status",
            },
            "required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_materials")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "blocked_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_materials")
            ),
            "owner_next_steps": _safe_route_task_rehearsal_list(owner_steps_source),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": acceptance_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_rerun_execution_result_acceptance_packet_not_proven(
                packet,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["acceptance_verdict"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(summary["required_materials"], list)
        and bool(summary["required_materials"]),
        isinstance(summary["owner_next_steps"], list)
        and bool(summary["owner_next_steps"]),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(item)
        for item in (
            status_source,
            same_ref_source,
            summary["required_materials"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["blocked_materials"],
            summary["owner_next_steps"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_GATE
    ):
        summary.update(
            {
                "acceptance_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_packet"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance packet schema "
                        "or boundary is unsupported"
                    ),
                },
                "acceptance_verdict": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "blocked_materials": [],
                "owner_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance packet schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["acceptance_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_packet",
            "verdict": "not_proven",
            "reason": "execution result acceptance packet must remain software_proof and not_proven",
        }
        summary["acceptance_verdict"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "acceptance_status": {
                    "status": (
                        "blocked_missing_field_evidence_rerun_execution_result_acceptance_packet_materials"
                    ),
                    "verdict": "not_proven",
                    "reason": "execution result acceptance packet is missing required safe metadata",
                },
                "acceptance_verdict": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance packet fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["acceptance_status"] = {
            "status": (
                "evidence_ref_mismatch_field_evidence_rerun_execution_result_acceptance_packet_blocked"
            ),
            "verdict": "not_proven",
            "reason": "execution result acceptance packet evidence_ref values do not match",
        }
        summary["acceptance_verdict"] = "blocked"
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
        or _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
            packet
        )
        or _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance packet was blocked because "
            "summary fields could expose raw records/logs/artifacts, control data, or "
            "success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "acceptance_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_rerun_execution_result_acceptance_packet"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw record/log/artifact, control, path, credential, or success material"
                    ),
                },
                "acceptance_verdict": "blocked",
                "accepted_materials": [],
                "blocked_materials": [],
                "owner_next_steps": [],
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


def summarize_field_evidence_rerun_execution_result_acceptance_backfill(source):
    """构建 field evidence rerun execution result acceptance backfill 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        backfill = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_backfill_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance backfill is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "backfill_status": {
                        "status": "missing",
                        "verdict": "not_proven",
                        "reason": (
                            "field evidence rerun execution result acceptance backfill summary missing"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance backfill summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                backfill = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "backfill_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result "
                            f"acceptance backfill: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance backfill JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_backfill_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance backfill is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(backfill, dict):
        summary.update(
            {
                "backfill_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance backfill JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        backfill.get("diagnostics")
        if isinstance(backfill.get("diagnostics"), dict)
        else {}
    )
    # 完整 backfill artifact 只能包裹 canonical summary；Robot 输出不读取 raw manifest。
    summary_fragment = (
        backfill
        if str(backfill.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            backfill.get("field_evidence_rerun_execution_result_acceptance_backfill_summary"),
            backfill.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary"
            ),
            backfill.get("robot_compatible_summary"),
            backfill.get("summary"),
            backfill.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_backfill_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else backfill
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_backfill_source_contract(
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
                "backfill_status": {
                    "status": "missing_summary",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance backfill summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("backfill_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("acceptance_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    backfill_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("backfill_status")
        or summary_fragment.get("status")
        or "blocked"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance backfill consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance backfill is metadata-only; "
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
        # 手机和 diagnostics 都依赖 copy 中的 false literal；缺失时强制补齐边界文本。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        backfill.get("safe_evidence_ref") or backfill.get("evidence_ref") or ""
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
    owner_steps_source = (
        summary_fragment.get("owner_next_steps")
        if "owner_next_steps" in summary_fragment
        else summary_fragment.get("owner_handoff")
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "backfill_status": {
                "status": backfill_status or "blocked",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "backfill_verdict": _redact_route_task_rehearsal_text(
                summary_fragment.get("backfill_verdict")
                or summary_fragment.get("acceptance_verdict")
                or summary_fragment.get("decision")
                or backfill_status
                or "blocked"
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "same_evidence_ref_status": _safe_pc_route_debug_dict(same_ref_source)
            or {
                "status": backfill_status or "blocked",
                "verdict": "not_proven",
                "reason": "execution result acceptance backfill lacks same evidence_ref status",
            },
            "required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_materials")
            ),
            "accepted_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials")
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "blocked_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_materials")
            ),
            "owner_next_steps": _safe_route_task_rehearsal_list(owner_steps_source),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": backfill_status or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": _field_evidence_rerun_execution_result_acceptance_backfill_not_proven(
                backfill,
                summary_fragment,
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    required_summary_fields = (
        bool(summary["safe_evidence_ref"]),
        bool(summary["backfill_verdict"]),
        bool(summary["same_evidence_ref_status"]),
        isinstance(summary["required_materials"], list)
        and bool(summary["required_materials"]),
        isinstance(summary["owner_next_steps"], list)
        and bool(summary["owner_next_steps"]),
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            same_ref_source,
            summary["required_materials"],
            summary["accepted_materials"],
            summary["missing_materials"],
            summary["blocked_materials"],
            summary["owner_next_steps"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SCHEMA
        or source_boundary != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_GATE
    ):
        summary.update(
            {
                "backfill_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_backfill"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill schema "
                        "or boundary is unsupported"
                    ),
                },
                "backfill_verdict": "blocked",
                "accepted_materials": [],
                "missing_materials": [],
                "blocked_materials": [],
                "owner_next_steps": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance backfill schema or boundary",
                },
            }
        )
        return summary
    if summary["source"] != EVIDENCE_SOURCE_SOFTWARE or verdict != "not_proven":
        summary["backfill_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_backfill",
            "verdict": "not_proven",
            "reason": "execution result acceptance backfill must remain software_proof and not_proven",
        }
        summary["backfill_verdict"] = "blocked"
        return summary
    if not all(required_summary_fields):
        summary.update(
            {
                "backfill_status": {
                    "status": (
                        "blocked_missing_field_evidence_rerun_execution_result_acceptance_backfill_materials"
                    ),
                    "verdict": "not_proven",
                    "reason": "execution result acceptance backfill is missing required safe metadata",
                },
                "backfill_verdict": "blocked",
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance backfill fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["backfill_status"] = {
            "status": (
                "evidence_ref_mismatch_field_evidence_rerun_execution_result_acceptance_backfill_blocked"
            ),
            "verdict": "not_proven",
            "reason": "execution result acceptance backfill evidence_ref values do not match",
        }
        summary["backfill_verdict"] = "blocked"
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
        or _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(
            backfill
        )
        or _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance backfill was blocked because "
            "summary fields could expose raw manifest contents, control data, paths, or "
            "success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "backfill_status": {
                    "status": (
                        "blocked_unsafe_field_evidence_rerun_execution_result_acceptance_backfill"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, or success material"
                    ),
                },
                "backfill_verdict": "blocked",
                "accepted_materials": [],
                "blocked_materials": [],
                "owner_next_steps": [],
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


def summarize_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
    source,
):
    """构建 acceptance backfill review decision 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = (
            _default_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary(
                source_path,
                read_error=(
                    "field evidence rerun execution result acceptance backfill review decision is not configured"
                ),
            )
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "decision_status": {
                        "status": "blocked_missing_backfill",
                        "verdict": "not_proven",
                        "reason": "execution result acceptance backfill review decision summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance backfill review decision summary missing",
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
                    "decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result "
                            f"acceptance backfill review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance backfill review decision JSON read error",
                    },
                }
            )
            return summary

    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance backfill review decision is not configured"
            ),
        )
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance backfill review decision JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    # Robot 只消费 canonical summary；完整 review artifact 仅可作为 summary 容器。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get(
                "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary"
            ),
            decision.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_source_contract(
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
                "decision_status": {
                    "status": "blocked_missing_backfill",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill review decision lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance backfill review decision summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    decision_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("decision_status")
        or summary_fragment.get("status")
        or "blocked_missing_backfill"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance backfill review decision consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance backfill review decision "
            "is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 必须携带 false literal，便于 diagnostics 和手机端保持同一安全边界。
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
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    owner_next_step = _redact_route_task_rehearsal_text(
        summary_fragment.get("owner_next_step")
        or (
            summary_fragment.get("owner_next_steps")[0]
            if isinstance(summary_fragment.get("owner_next_steps"), list)
            and summary_fragment.get("owner_next_steps")
            else ""
        )
        or "Prepare ready_for_field_rerun_result_acceptance_review_handoff when safe materials match."
    )
    summary.update(
        {
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "decision": _redact_route_task_rehearsal_text(
                summary_fragment.get("decision") or decision_status or "blocked"
            ),
            "decision_status": {
                "status": decision_status or "blocked_missing_backfill",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "missing_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_categories")
                or summary_fragment.get("missing_materials")
            ),
            "rejected_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_categories")
                or summary_fragment.get("rejected_materials")
                or summary_fragment.get("blocked_materials")
            ),
            "owner_next_step": owner_next_step,
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": decision_status or "blocked_missing_backfill",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["missing_categories"],
            summary["rejected_categories"],
            summary["owner_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "decision": "blocked",
                "decision_status": {
                    "status": (
                        "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_backfill_review_decision"
                    ),
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance backfill review decision schema "
                        "or boundary is unsupported"
                    ),
                },
                "missing_categories": [],
                "rejected_categories": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance backfill review decision schema or boundary",
                },
            }
        )
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or summary["evidence_boundary_status"] != "not_proven"
    ):
        summary["decision"] = "blocked"
        summary["decision_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_backfill_review_decision",
            "verdict": "not_proven",
            "reason": "execution result acceptance backfill review decision must remain software_proof and not_proven",
        }
        return summary
    if not summary["safe_evidence_ref"] or not summary["owner_next_step"]:
        summary.update(
            {
                "decision": "blocked",
                "decision_status": {
                    "status": "blocked_missing_backfill",
                    "verdict": "not_proven",
                    "reason": "execution result acceptance backfill review decision is missing safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance backfill review decision fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["decision"] = "blocked"
        summary["decision_status"] = {
            "status": "evidence_ref_mismatch_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_blocked",
            "verdict": "not_proven",
            "reason": "execution result acceptance backfill review decision evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
            decision
        )
        or _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance backfill review decision "
            "was blocked because summary fields could expose raw manifest contents, "
            "control data, paths, credentials, external proof, or success wording; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "decision": "blocked",
                "decision_status": {
                    "status": "unsafe_rejected",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, external proof, or success material"
                    ),
                },
                "missing_categories": [],
                "rejected_categories": ["unsafe_rejected"],
                "owner_next_step": "Remove unsafe material and provide a sanitized same-ref review decision.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_review_handoff(source):
    """构建 acceptance review handoff 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance review handoff is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "handoff_status": {
                        "status": "blocked_missing_review_decision",
                        "verdict": "not_proven",
                        "reason": "execution result acceptance review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance review handoff summary missing",
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
                            "failed reading field evidence rerun execution result "
                            f"acceptance review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance review handoff JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_review_handoff_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance review handoff is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance review handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance review handoff JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        handoff.get("diagnostics")
        if isinstance(handoff.get("diagnostics"), dict)
        else {}
    )
    # 完整 handoff artifact 只能作为 safe summary 容器，Robot 不直接消费 raw handoff body。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get(
                "field_evidence_rerun_execution_result_acceptance_review_handoff_summary"
            ),
            handoff.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary"
            ),
            handoff.get("robot_compatible_summary"),
            handoff.get("summary"),
            handoff.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_review_handoff_source_contract(
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
                "handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance review handoff lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance review handoff summary",
                },
            }
        )
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
        or "blocked_missing_review_decision"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance review handoff consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance review handoff "
            "is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 必须保留 false literal，避免下游 UI 重新推断控制权限。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "handoff_status": {
                "status": handoff_status or "blocked_missing_review_decision",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "required_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_materials")
                or summary_fragment.get("required_material_checklist")
            ),
            "blocked_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_categories")
                or summary_fragment.get("missing_categories")
            ),
            "rejected_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_categories")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner attaches same-ref sanitized support handoff material."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support validates only metadata-only handoff fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps acceptance not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status or "blocked_missing_review_decision",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["required_materials"],
            summary["blocked_categories"],
            summary["rejected_categories"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance review handoff schema or boundary is unsupported"
                    ),
                },
                "required_materials": [],
                "blocked_categories": [],
                "rejected_categories": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance review handoff schema or boundary",
                },
            }
        )
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or summary["evidence_boundary_status"] != "not_proven"
        or handoff_status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_STATUSES
    ):
        summary["handoff_status"] = {
            "status": "handoff_unsafe_rejected",
            "verdict": "not_proven",
            "reason": "execution result acceptance review handoff must remain software_proof and not_proven",
        }
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary.update(
            {
                "handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": "execution result acceptance review handoff is missing safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance review handoff fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["handoff_status"] = {
            "status": "handoff_evidence_ref_mismatch",
            "verdict": "not_proven",
            "reason": "execution result acceptance review handoff evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
            handoff
        )
        or _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance review handoff "
            "was blocked because summary fields could expose raw manifest contents, "
            "control data, paths, credentials, external proof, HIL/pass, PR resolution, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": {
                    "status": "handoff_unsafe_rejected",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, external proof, HIL/pass, PR-resolution, or success material"
                    ),
                },
                "required_materials": [],
                "blocked_categories": ["handoff_unsafe_rejected"],
                "rejected_categories": ["handoff_unsafe_rejected"],
                "owner_next_step": "Remove unsafe material and provide a sanitized same-ref handoff.",
                "support_next_step": "Reject unsafe handoff metadata until only safe fields remain.",
                "reviewer_next_step": "Keep handoff not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake(source):
    """构建 acceptance handoff intake 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        intake = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "intake_status": {
                        "status": "blocked_missing_review_handoff",
                        "verdict": "not_proven",
                        "reason": "execution result acceptance handoff intake summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake summary missing",
                    },
                }
            )
            return summary
        summary["exists"] = True
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            summary.update(
                {
                    "intake_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result "
                            f"acceptance handoff intake: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance handoff intake is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(intake, dict):
        summary.update(
            {
                "intake_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance handoff intake JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        intake.get("diagnostics")
        if isinstance(intake.get("diagnostics"), dict)
        else {}
    )
    # 完整 intake artifact 只能作为 safe summary 容器，Robot 不消费 raw intake body。
    summary_fragment = (
        intake
        if str(intake.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            intake.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary"
            ),
            intake.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary"
            ),
            intake.get("robot_compatible_summary"),
            intake.get("summary"),
            intake.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else intake
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_source_contract(
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
                "intake_status": {
                    "status": "blocked_missing_review_handoff",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance handoff intake summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("intake_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    intake_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("intake_status")
        or summary_fragment.get("status")
        or "blocked_missing_review_handoff"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance handoff intake consumed as software_proof"
    )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance handoff intake "
            "is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 要保留 false literal，方便 mobile/web 只渲染后端已确认的闭锁状态。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "intake_status": {
                "status": intake_status or "blocked_missing_review_handoff",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted_safe_material_refs")
            ),
            "required_checklist": _safe_route_task_rehearsal_list(
                summary_fragment.get("required_checklist")
                or summary_fragment.get("required_materials")
            ),
            "blocked_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_categories")
                or summary_fragment.get("missing_categories")
            ),
            "rejected_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_categories")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner attaches same-ref sanitized intake acknowledgement."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support validates only metadata-only intake fields."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": intake_status or "blocked_missing_review_handoff",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_not_proven(
                    intake,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["accepted_material_refs"],
            summary["required_checklist"],
            summary["blocked_categories"],
            summary["rejected_categories"],
            summary["owner_next_step"],
            summary["support_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_GATE
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_missing_review_handoff",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake schema or boundary is unsupported"
                    ),
                },
                "accepted_material_refs": [],
                "required_checklist": [],
                "blocked_categories": [],
                "rejected_categories": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance handoff intake schema or boundary",
                },
            }
        )
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or summary["evidence_boundary_status"] != "not_proven"
        or intake_status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_STATUSES
        or not summary["software_proof"]
    ):
        summary["intake_status"] = {
            "status": "intake_unsafe_rejected",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake must remain software_proof and not_proven",
        }
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
    ):
        summary.update(
            {
                "intake_status": {
                    "status": "blocked_missing_review_handoff",
                    "verdict": "not_proven",
                    "reason": "execution result acceptance handoff intake is missing safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance handoff intake fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["intake_status"] = {
            "status": "intake_evidence_ref_mismatch",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
            intake
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake "
            "was blocked because summary fields could expose raw manifest contents, "
            "control data, paths, credentials, external proof, HIL/pass, PR resolution, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "intake_status": {
                    "status": "intake_unsafe_rejected",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, external proof, HIL/pass, PR-resolution, or success material"
                    ),
                },
                "accepted_material_refs": [],
                "required_checklist": [],
                "blocked_categories": ["intake_unsafe_rejected"],
                "rejected_categories": ["intake_unsafe_rejected"],
                "owner_next_step": "Remove unsafe material and provide a sanitized same-ref intake.",
                "support_next_step": "Reject unsafe intake metadata until only safe fields remain.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision(
    source,
):
    """构建 acceptance handoff intake review decision 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        decision = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake review decision is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_decision_status": {
                        "status": "blocked_missing_handoff_intake",
                        "verdict": "not_proven",
                        "reason": "execution result acceptance handoff intake review decision summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake review decision summary missing",
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
                    "review_decision_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result acceptance "
                            f"handoff intake review decision: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake review decision JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance handoff intake review decision is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(decision, dict):
        summary.update(
            {
                "review_decision_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review decision JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance handoff intake review decision JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        decision.get("diagnostics")
        if isinstance(decision.get("diagnostics"), dict)
        else {}
    )
    # 完整 decision artifact 只能作为 safe summary 容器，Robot 不消费 raw decision body。
    summary_fragment = (
        decision
        if str(decision.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            decision.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary"
            ),
            decision.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary"
            ),
            decision.get("robot_compatible_summary"),
            decision.get("summary"),
            decision.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_source_contract(
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
                "review_decision_status": {
                    "status": "blocked_missing_handoff_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review decision lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance handoff intake review decision summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_decision_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_decision_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("review_decision_status")
        or summary_fragment.get("status")
        or "blocked_missing_handoff_intake"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance handoff intake review decision consumed as software_proof"
    )
    source_intake_status = summary_fragment.get("source_intake_status")
    if isinstance(source_intake_status, dict):
        source_intake_status = _safe_pc_route_debug_dict(source_intake_status)
    else:
        source_intake_status = _redact_route_task_rehearsal_text(
            source_intake_status or "unknown"
        )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance handoff intake review decision "
            "is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 要保留 false literal，方便 mobile/web 只渲染后端已确认的闭锁状态。
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "review_decision_status": {
                "status": review_decision_status or "blocked_missing_handoff_intake",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "source_intake_status": source_intake_status,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted_safe_material_refs")
            ),
            "missing_or_rework_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_or_rework_reasons")
                or summary_fragment.get("rework_reasons")
                or summary_fragment.get("missing_reasons")
                or summary_fragment.get("blocked_categories")
            ),
            "rejected_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_categories")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner resolves review rework with same-ref sanitized material."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support validates only metadata-only review decision fields."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_decision_status or "blocked_missing_handoff_intake",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_not_proven(
                    decision,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["source_intake_status"],
            summary["accepted_material_refs"],
            summary["missing_or_rework_reasons"],
            summary["rejected_categories"],
            summary["owner_next_step"],
            summary["support_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "review_decision_status": {
                    "status": "blocked_missing_handoff_intake",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review decision schema or boundary is unsupported"
                    ),
                },
                "accepted_material_refs": [],
                "missing_or_rework_reasons": [],
                "rejected_categories": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance handoff intake review decision schema or boundary",
                },
            }
        )
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or summary["evidence_boundary_status"] != "not_proven"
        or review_decision_status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_decision_status"] = {
            "status": "review_unsafe_rejected",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake review decision must remain software_proof and not_proven",
        }
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
    ):
        summary.update(
            {
                "review_decision_status": {
                    "status": "blocked_missing_handoff_intake",
                    "verdict": "not_proven",
                    "reason": "execution result acceptance handoff intake review decision is missing safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance handoff intake review decision fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_decision_status"] = {
            "status": "review_evidence_ref_mismatch",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake review decision evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
            decision
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake review decision "
            "was blocked because summary fields could expose raw manifest contents, "
            "control data, paths, credentials, external proof, HIL/pass, PR resolution, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision_status": {
                    "status": "review_unsafe_rejected",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, external proof, HIL/pass, PR-resolution, or success material"
                    ),
                },
                "accepted_material_refs": [],
                "missing_or_rework_reasons": ["review_unsafe_rejected"],
                "rejected_categories": ["review_unsafe_rejected"],
                "owner_next_step": "Remove unsafe material and provide a sanitized same-ref review decision.",
                "support_next_step": "Reject unsafe review decision metadata until only safe fields remain.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
    source,
):
    """构建 acceptance handoff intake review handoff 的 Robot-safe 摘要。"""
    source_path = ""
    if isinstance(source, dict):
        handoff = source
    else:
        source_path = os.path.expanduser(str(source or ""))
        summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake review handoff is not configured"
            ),
        )
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary.update(
                {
                    "review_handoff_status": {
                        "status": "blocked_missing_review_decision",
                        "verdict": "not_proven",
                        "reason": "execution result acceptance handoff intake review handoff summary missing",
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake review handoff summary missing",
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
                    "review_handoff_status": {
                        "status": "read_error",
                        "verdict": "not_proven",
                        "reason": _redact_route_task_rehearsal_text(
                            "failed reading field evidence rerun execution result acceptance "
                            f"handoff intake review handoff: {exc}"
                        ),
                    },
                    "robot_diagnostics_summary": {
                        "status": "blocked",
                        "reason": "execution result acceptance handoff intake review handoff JSON read error",
                    },
                }
            )
            return summary

    summary = _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary(
        source_path,
        read_error=(
            "field evidence rerun execution result acceptance handoff intake review handoff is not configured"
        ),
    )
    summary["exists"] = bool(source_path) or isinstance(source, dict)
    if not isinstance(handoff, dict):
        summary.update(
            {
                "review_handoff_status": {
                    "status": "read_error",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review handoff JSON must be an object"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "execution result acceptance handoff intake review handoff JSON shape is invalid",
                },
            }
        )
        return summary

    diagnostics = (
        handoff.get("diagnostics")
        if isinstance(handoff.get("diagnostics"), dict)
        else {}
    )
    # 完整 review handoff artifact 只能作为 safe summary 容器，Robot 不消费 raw handoff body。
    summary_fragment = (
        handoff
        if str(handoff.get("schema") or "")
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY_SCHEMA
        else {}
    )
    if not summary_fragment:
        for candidate in (
            handoff.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary"
            ),
            handoff.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary"
            ),
            handoff.get("robot_compatible_summary"),
            handoff.get("summary"),
            handoff.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_source_contract(
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
                "review_handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review handoff lacks a safe canonical summary"
                    ),
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing safe execution result acceptance handoff intake review handoff summary",
                },
            }
        )
        return summary

    status_source = summary_fragment.get("review_handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("handoff_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    review_handoff_status = _redact_route_task_rehearsal_text(
        status_source.get("status")
        or summary_fragment.get("review_handoff_status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked_missing_review_decision"
    )
    verdict = _redact_route_task_rehearsal_text(
        status_source.get("verdict") or summary_fragment.get("verdict") or "not_proven"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "field evidence rerun execution result acceptance handoff intake review handoff consumed as software_proof"
    )
    source_review_decision_status = summary_fragment.get("source_review_decision_status")
    if isinstance(source_review_decision_status, dict):
        source_review_decision_status = _safe_pc_route_debug_dict(
            source_review_decision_status
        )
    else:
        source_review_decision_status = _redact_route_task_rehearsal_text(
            source_review_decision_status or "unknown"
        )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance handoff intake review handoff "
            "is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # safe_copy 要保留 false literal，方便 mobile/web 只渲染后端已确认的闭锁状态。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "review_handoff_status": {
                "status": review_handoff_status
                or "blocked_missing_review_decision",
                "verdict": verdict or "not_proven",
                "reason": reason,
            },
            "source_review_decision_status": source_review_decision_status,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted_safe_material_refs")
            ),
            "missing_or_rework_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_or_rework_reasons")
                or summary_fragment.get("rework_reasons")
                or summary_fragment.get("missing_reasons")
                or summary_fragment.get("blocked_categories")
            ),
            "rejected_categories": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_categories")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner resolves review handoff rework with same-ref sanitized material."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support validates only metadata-only review handoff fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps handoff not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": review_handoff_status
                or "blocked_missing_review_decision",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_not_proven(
                    handoff,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["source_review_decision_status"],
            summary["accepted_material_refs"],
            summary["missing_or_rework_reasons"],
            summary["rejected_categories"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "review_handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": (
                        "field evidence rerun execution result acceptance handoff intake review handoff schema or boundary is unsupported"
                    ),
                },
                "accepted_material_refs": [],
                "missing_or_rework_reasons": [],
                "rejected_categories": [],
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "unsupported execution result acceptance handoff intake review handoff schema or boundary",
                },
            }
        )
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or verdict != "not_proven"
        or summary["evidence_boundary_status"] != "not_proven"
        or review_handoff_status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_handoff_status"] = {
            "status": "handoff_unsafe_rejected",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake review handoff must remain software_proof and not_proven",
        }
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary.update(
            {
                "review_handoff_status": {
                    "status": "blocked_missing_review_decision",
                    "verdict": "not_proven",
                    "reason": "execution result acceptance handoff intake review handoff is missing safe metadata",
                },
                "robot_diagnostics_summary": {
                    "status": "blocked",
                    "reason": "missing required execution result acceptance handoff intake review handoff fields",
                },
            }
        )
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["review_handoff_status"] = {
            "status": "handoff_evidence_ref_mismatch",
            "verdict": "not_proven",
            "reason": "execution result acceptance handoff intake review handoff evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
            handoff
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake review handoff "
            "was blocked because summary fields could expose raw manifest contents, "
            "control data, paths, credentials, external proof, HIL/pass, PR resolution, "
            "or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_handoff_status": {
                    "status": "handoff_unsafe_rejected",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw manifest, control, path, credential, external proof, HIL/pass, PR-resolution, or success material"
                    ),
                },
                "accepted_material_refs": [],
                "missing_or_rework_reasons": ["handoff_unsafe_rejected"],
                "rejected_categories": ["handoff_unsafe_rejected"],
                "owner_next_step": "Remove unsafe material and provide a sanitized same-ref review handoff.",
                "support_next_step": "Reject unsafe review handoff metadata until only safe fields remain.",
                "reviewer_next_step": "Keep handoff not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
    source,
):
    """构建 acceptance handoff intake follow-up escalation status 的 Robot-safe 摘要。"""
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "follow-up escalation status is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        status_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field evidence rerun execution result acceptance handoff intake "
                "follow-up escalation status summary missing"
            )
            summary["followup_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                status_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake follow-up escalation status: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status"]["reason"] = safe_error
            return summary

    if not isinstance(status_doc, dict):
        summary["followup_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake follow-up escalation status JSON must be an object"
        )
        return summary

    diagnostics = (
        status_doc.get("diagnostics")
        if isinstance(status_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(status_doc.get("schema") or "")
    if (
        raw_schema
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA
    ):
        summary_fragment = status_doc
    else:
        summary_fragment = {}
        for candidate in (
            status_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"
            ),
            status_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"
            ),
            status_doc.get("robot_compatible_summary"),
            status_doc.get("summary"),
            status_doc.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else status_doc
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_source_contract(
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
        summary["followup_status"] = {
            "state": "blocked",
            "verdict": "not_proven",
            "reason": (
                "field evidence rerun execution result acceptance handoff intake follow-up escalation status lacks a safe canonical summary"
            ),
        }
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "missing safe follow-up escalation status summary",
        }
        return summary

    status_source = summary_fragment.get("followup_status")
    if not isinstance(status_source, dict):
        status_source = summary_fragment.get("status_summary")
    if not isinstance(status_source, dict):
        status_source = {}
    followup_state = _redact_route_task_rehearsal_text(
        summary_fragment.get("followup_state")
        or status_source.get("state")
        or status_source.get("status")
        or summary_fragment.get("status")
        or "blocked"
    )
    reason = _redact_route_task_rehearsal_text(
        status_source.get("reason")
        or summary_fragment.get("reason")
        or "follow-up escalation status consumed as software_proof"
    )
    source_review_handoff_status = summary_fragment.get("source_review_handoff_status")
    if isinstance(source_review_handoff_status, dict):
        source_review_handoff_status = _safe_pc_route_debug_dict(
            source_review_handoff_status
        )
    else:
        source_review_handoff_status = _redact_route_task_rehearsal_text(
            source_review_handoff_status or "unknown"
        )
    safe_copy = _safe_pc_route_debug_value(
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or (
            "Field evidence rerun execution result acceptance handoff intake follow-up "
            "escalation status is metadata-only; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    )
    safe_copy_text = (
        json.dumps(safe_copy, ensure_ascii=False, sort_keys=True)
        if isinstance(safe_copy, (dict, list))
        else str(safe_copy or "")
    )
    if "delivery_success=false" not in safe_copy_text:
        # 下游 UI 依赖 false literal 渲染禁用态，Robot 在这里统一补齐。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    source_ref = str(
        status_doc.get("safe_evidence_ref") or status_doc.get("evidence_ref") or ""
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
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "followup_state": followup_state or "blocked",
            "followup_status": {
                "state": followup_state or "blocked",
                "verdict": "not_proven",
                "reason": reason,
            },
            "source_review_handoff_status": source_review_handoff_status,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_ref or source_ref
            ),
            "missing_required_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_required_material_refs")
                or summary_fragment.get("missing_material_refs")
                or summary_fragment.get("required_material_refs")
            ),
            "pending_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("pending_reason")
            ),
            "overdue_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("overdue_reason")
            ),
            "escalated_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("escalated_reason")
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner keeps follow-up status safe and same-ref."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support checks only metadata-only follow-up fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps follow-up not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": followup_state or "blocked",
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_not_proven(
                    status_doc,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
            item
        )
        for item in (
            status_source,
            summary["source_review_handoff_status"],
            summary["missing_required_material_refs"],
            summary["pending_reason"],
            summary["overdue_reason"],
            summary["escalated_reason"],
            summary["blocked_reason"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary["followup_state"] = "blocked"
        summary["followup_status"] = {
            "state": "blocked",
            "verdict": "not_proven",
            "reason": "follow-up escalation status schema or boundary is unsupported",
        }
        summary["missing_required_material_refs"] = []
        summary["robot_diagnostics_summary"] = {
            "status": "blocked",
            "reason": "unsupported follow-up escalation status schema or boundary",
        }
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or summary["followup_state"]
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATES
        or not summary["software_proof"]
    ):
        summary["followup_state"] = "blocked"
        summary["followup_status"] = {
            "state": "blocked",
            "verdict": "not_proven",
            "reason": "follow-up escalation status must remain software_proof and not_proven",
        }
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["followup_state"] = "blocked"
        summary["followup_status"] = {
            "state": "blocked",
            "verdict": "not_proven",
            "reason": "follow-up escalation status is missing safe metadata",
        }
        return summary
    if source_ref and summary_ref and source_ref != summary_ref:
        summary["followup_state"] = "blocked"
        summary["followup_status"] = {
            "state": "blocked",
            "verdict": "not_proven",
            "reason": "follow-up escalation status evidence_ref values do not match",
        }
        return summary
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
            status_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake follow-up "
            "escalation status was blocked because summary fields could expose raw "
            "artifacts, control data, paths, credentials, external proof, HIL/pass, "
            "PR resolution, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "followup_state": "blocked",
                "followup_status": {
                    "state": "blocked",
                    "verdict": "not_proven",
                    "reason": (
                        "unsafe raw artifact, control, path, credential, external proof, HIL/pass, PR-resolution, or success material"
                    ),
                },
                "missing_required_material_refs": [],
                "pending_reason": "",
                "overdue_reason": "",
                "escalated_reason": "",
                "blocked_reason": "unsafe follow-up escalation status material",
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref follow-up status.",
                "support_next_step": "Reject unsafe follow-up metadata until only safe fields remain.",
                "reviewer_next_step": "Keep follow-up not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
    source,
):
    """构建 acceptance handoff intake owner response intake 的 Robot-safe 摘要。"""
    # Robot 只展示 owner response 的安全分类；不能由此推导现场验收、ACK 或控制许可。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response intake is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response intake summary missing"
            )
            summary["owner_response_intake_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response intake: {exc}"
            )
            summary["read_error"] = safe_error
            summary["owner_response_intake_status"]["reason"] = safe_error
            return summary

    if not isinstance(response_doc, dict):
        summary["owner_response_intake_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response intake JSON must be an object"
        )
        return summary

    diagnostics = (
        response_doc.get("diagnostics")
        if isinstance(response_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(response_doc.get("schema") or "")
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = response_doc
    else:
        summary_fragment = {}
        for candidate in (
            response_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
            ),
            response_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
            ),
            response_doc.get("robot_compatible_summary"),
            response_doc.get("summary"),
            response_doc.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else response_doc
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_source_contract(
            contract_source
        )
    )
    status_doc = (
        summary_fragment.get("owner_response_intake_status")
        if isinstance(summary_fragment.get("owner_response_intake_status"), dict)
        else summary_fragment.get("owner_response_status")
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
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # copy 是下游直接展示面，必须显式带上软件证明和三 false flags。
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
    source_followup_escalation_status = (
        summary_fragment.get("source_followup_escalation_status")
        if isinstance(summary_fragment.get("source_followup_escalation_status"), dict)
        else summary_fragment.get("source_followup_status")
        if isinstance(summary_fragment.get("source_followup_status"), dict)
        else {}
    )
    source_bridge = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_bridge") or ""
    )
    is_bridge_summary = (
        source_bridge
        == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_SOURCE
    )
    bridge_boundary = (
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_GATE
    )
    active_boundary = bridge_boundary if is_bridge_summary else source_boundary
    source_followup_status = (
        summary_fragment.get("source_followup_status")
        if isinstance(summary_fragment.get("source_followup_status"), dict)
        else source_followup_escalation_status
    )
    summary.update(
        {
            "capability": (
                FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE
                if is_bridge_summary
                else summary.get("capability")
            ),
            "source_bridge": source_bridge,
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or response_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(active_boundary),
            "evidence_boundary": _redact_route_task_rehearsal_text(active_boundary),
            "boundary": _redact_route_task_rehearsal_text(active_boundary),
            "proof_boundary": _redact_route_task_rehearsal_text(active_boundary),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "status": status,
            "overall_status": "not_proven",
            "owner_response_intake_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence rerun execution result acceptance handoff "
                        "intake owner response intake is software_proof only"
                    )
                ),
            },
            "source_followup_escalation_status": _safe_pc_route_debug_dict(
                source_followup_escalation_status
            ),
            "source_followup_status": _safe_pc_route_debug_dict(source_followup_status),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted")
            ),
            "missing_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_refs")
                or summary_fragment.get("missing")
            ),
            "rejected_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_material_refs")
                or summary_fragment.get("rejected")
            ),
            "blocked_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_material_refs")
                or summary_fragment.get("blocked")
            ),
            "owner_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_route")
                or summary_fragment.get("field_owner_route")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_support_route")
            ),
            "support_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("support_route")
                or summary_fragment.get("operator_support_route")
            ),
            "next_required_field_owner_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_field_owner_materials")
                or summary_fragment.get("next_required_evidence")
                or summary_fragment.get("missing_material_refs")
            ),
            "false_state_flags": _safe_pc_route_debug_dict(
                summary_fragment.get("false_state_flags")
            )
            or {
                "source": EVIDENCE_SOURCE_SOFTWARE,
                "overall_status": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
                "safe_to_control": False,
                "ack_post_allowed": False,
                "cursor_updates_allowed": False,
                "nav2_triggered": False,
                "hil_pass": False,
            },
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner supplies same-ref sanitized response materials."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support checks only metadata-only owner response fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps owner response intake not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": status,
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_not_proven(
                    response_doc,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["source_followup_escalation_status"],
            summary["accepted_material_refs"],
            summary["missing_material_refs"],
            summary["rejected_material_refs"],
            summary["blocked_material_refs"],
            summary["source_followup_status"],
            summary["owner_route"],
            summary["reviewer_route"],
            summary["support_route"],
            summary["next_required_field_owner_materials"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["owner_response_intake_status"] = {
            "status": (
                "blocked_missing_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "missing safe owner response intake summary",
        }
        summary["status"] = summary["owner_response_intake_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SCHEMA
        or active_boundary
        not in {
            FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE,
            bridge_boundary,
        }
        or bool(source_bridge)
        != bool(
            active_boundary == bridge_boundary
            and source_bridge
            == FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_SOURCE
        )
    ):
        summary["owner_response_intake_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response intake schema or boundary is unsupported",
        }
        summary["status"] = summary["owner_response_intake_status"]["status"]
        return summary
    if is_bridge_summary and (
        summary["capability"]
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE
        or not summary["source_followup_status"]
        or not summary["owner_route"]
        or not summary["reviewer_route"]
        or not summary["support_route"]
        or not summary["next_required_field_owner_materials"]
        or summary["false_state_flags"].get("delivery_success") is not False
        or summary["false_state_flags"].get("primary_actions_enabled") is not False
        or summary["false_state_flags"].get("safe_to_control") is not False
        or summary["false_state_flags"].get("source") != EVIDENCE_SOURCE_SOFTWARE
        or summary["false_state_flags"].get("overall_status") != "not_proven"
    ):
        summary["owner_response_intake_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK owner-response bridge is missing safe bridge metadata",
        }
        summary["status"] = summary["owner_response_intake_status"]["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or summary["status"]
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_STATUSES
        or not summary["software_proof"]
    ):
        summary["owner_response_intake_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response intake must remain software_proof and not_proven",
        }
        summary["status"] = summary["owner_response_intake_status"]["status"]
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["owner_response_intake_status"] = {
            "status": "blocked_missing_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_materials",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response intake is missing safe metadata",
        }
        summary["status"] = summary["owner_response_intake_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("diagnostics_fetch_mutation_enabled"))
        or bool(boundary_flags.get("github_mutation_enabled"))
        or bool(boundary_flags.get("robot_command_hint_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
            response_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response intake was blocked because summary fields could expose raw "
            "artifacts, control data, paths, credentials, DB/queue URLs, checksums, "
            "tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, external "
            "proof, or success wording; safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
                "owner_response_intake_status": {
                    "status": "blocked_unsafe_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw artifact, control, path, credential, DB/queue, "
                        "checksum, traceback, ROS topic, serial/UART, WAVE ROVER, "
                        "HIL/pass, external proof, or success material"
                    ),
                },
                "accepted_material_refs": [],
                "missing_material_refs": [],
                "rejected_material_refs": [],
                "blocked_material_refs": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref owner response intake.",
                "support_next_step": "Reject unsafe owner response metadata until only safe fields remain.",
                "reviewer_next_step": "Keep owner response intake not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
    source,
):
    """构建 acceptance handoff intake owner response review decision 的 Robot-safe 摘要。"""
    # Robot 只展示 owner response review 的安全判定；不能由此推导现场验收、ACK 或控制许可。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response review decision is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response review decision summary missing"
            )
            summary["review_decision_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response review decision: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_decision_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_decision_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response review decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
            ),
            decision_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
            ),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            decision_doc.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break

    contract_source = summary_fragment if summary_fragment else decision_doc
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_source_contract(
            contract_source
        )
    )
    status_doc = (
        summary_fragment.get("review_decision_status")
        if isinstance(summary_fragment.get("review_decision_status"), dict)
        else summary_fragment.get("owner_response_review_decision_status")
        if isinstance(summary_fragment.get("owner_response_review_decision_status"), dict)
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
        # copy 是下游直接展示面，必须显式带上软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("status")
        or "blocked_missing_owner_response_intake"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or decision_doc.get("safe_evidence_ref")
        or decision_doc.get("evidence_ref", "")
    )
    source_owner_response_intake_status = (
        summary_fragment.get("source_owner_response_intake_status")
        if isinstance(summary_fragment.get("source_owner_response_intake_status"), dict)
        else summary_fragment.get("source_owner_response_status")
        if isinstance(summary_fragment.get("source_owner_response_status"), dict)
        else summary_fragment.get("source_owner_response_intake_status")
        or summary_fragment.get("source_owner_response_status")
        or "unknown"
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
            "status": status,
            "overall_status": "not_proven",
            "review_decision_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence rerun execution result acceptance handoff "
                        "intake owner response review decision is software_proof only"
                    )
                ),
            },
            "source_owner_response_intake_status": (
                _safe_pc_route_debug_dict(source_owner_response_intake_status)
                if isinstance(source_owner_response_intake_status, dict)
                else _redact_route_task_rehearsal_text(
                    source_owner_response_intake_status
                )
            ),
            "accepted_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_material_refs")
                or summary_fragment.get("accepted")
            ),
            "missing_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_material_refs")
                or summary_fragment.get("missing")
            ),
            "rejected_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_material_refs")
                or summary_fragment.get("rejected")
            ),
            "blocked_material_refs": _safe_route_task_rehearsal_list(
                summary_fragment.get("blocked_material_refs")
                or summary_fragment.get("blocked")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
                or summary_fragment.get("missing_or_rework_reasons")
                or summary_fragment.get("rework_reasons")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner supplies same-ref sanitized response review materials."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support checks only metadata-only owner response review fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps owner response review decision not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": status,
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_not_proven(
                    decision_doc,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["source_owner_response_intake_status"],
            summary["accepted_material_refs"],
            summary["missing_material_refs"],
            summary["rejected_material_refs"],
            summary["blocked_material_refs"],
            summary["decision_reasons"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_decision_status"] = {
            "status": (
                "blocked_missing_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "missing safe owner response review decision summary",
        }
        summary["status"] = summary["review_decision_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE
    ):
        summary["review_decision_status"] = {
            "status": (
                "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision"
            ),
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review decision schema or boundary is unsupported",
        }
        summary["status"] = summary["review_decision_status"]["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or summary["status"]
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_decision_status"] = {
            "status": "blocked_unsupported_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review decision must remain software_proof and not_proven",
        }
        summary["status"] = summary["review_decision_status"]["status"]
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["review_decision_status"] = {
            "status": "blocked_missing_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_materials",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review decision is missing safe metadata",
        }
        summary["status"] = summary["review_decision_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response review decision was blocked because summary fields could expose raw "
            "artifacts, control data, paths, credentials, DB/queue URLs, checksums, "
            "tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, external "
            "proof, PR-resolution, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "review_unsafe_rejected",
                "review_decision_status": {
                    "status": "review_unsafe_rejected",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw artifact, control, path, credential, DB/queue, "
                        "checksum, traceback, ROS topic, serial/UART, WAVE ROVER, "
                        "HIL/pass, external proof, PR-resolution, or success material"
                    ),
                },
                "accepted_material_refs": [],
                "missing_material_refs": [],
                "rejected_material_refs": [],
                "blocked_material_refs": [],
                "decision_reasons": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref owner response review decision.",
                "support_next_step": "Reject unsafe owner response review metadata until only safe fields remain.",
                "reviewer_next_step": "Keep owner response review decision not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff(
    source,
):
    """构建 acceptance handoff intake owner response review handoff 的 Robot-safe 摘要。"""
    # Robot 只展示 handoff 安全元数据；这里不能启用 Start/Confirm/Cancel、ACK、Nav2 或硬件动作。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response review handoff is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response review handoff summary missing"
            )
            summary["review_handoff_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response review handoff: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_handoff_status"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["review_handoff_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response review handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source_contract(
            handoff_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            handoff_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            handoff_doc.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source_contract(
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
    if (
        "source=software_proof" not in safe_copy_text
        or "not_proven" not in safe_copy_text
        or "safe_to_control=false" not in safe_copy_text
        or "delivery_success=false" not in safe_copy_text
        or "primary_actions_enabled=false" not in safe_copy_text
    ):
        # safe_copy 是 diagnostics/mobile 直显文本，必须显式携带软件证明和三 false flags。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    handoff_status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or "blocked_missing_owner_response_review_decision"
    )
    source_review_status = summary_fragment.get(
        "source_owner_response_review_decision_status"
    ) or summary_fragment.get("source_review_decision_status")
    if isinstance(source_review_status, dict):
        source_review_status = source_review_status.get("status") or source_review_status.get(
            "decision"
        )
    source_review_status = _redact_route_task_rehearsal_text(
        source_review_status or "unknown"
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
            "status": handoff_status,
            "handoff_status": handoff_status,
            "overall_status": "not_proven",
            "review_handoff_status": {
                "status": handoff_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence rerun execution result acceptance handoff "
                        "intake owner response review handoff is software_proof only"
                    )
                ),
            },
            "source_owner_response_review_decision_status": source_review_status,
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or summary_fragment.get("decision_reasons")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Field owner supplies same-ref sanitized owner response review handoff metadata."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support checks only metadata-only owner response review handoff fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer keeps owner response review handoff not_proven until real field evidence exists."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": handoff_status,
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_not_proven(
                    handoff_doc,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["source_owner_response_review_decision_status"],
            summary["handoff_reasons"],
            summary["next_required_evidence"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_handoff_status"] = {
            "status": "blocked_missing_owner_response_review_decision",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "missing safe owner response review handoff summary",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
    ):
        summary["review_handoff_status"] = {
            "status": "handoff_unsafe_rejected",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review handoff schema or boundary is unsupported",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or summary["handoff_status"]
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_handoff_status"] = {
            "status": "handoff_unsafe_rejected",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review handoff must remain software_proof and not_proven",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["source_owner_response_review_decision_status"]
        or not summary["handoff_reasons"]
        or not summary["next_required_evidence"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["review_handoff_status"] = {
            "status": "blocked_missing_owner_response_review_decision",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "owner response review handoff is missing safe metadata",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("external_proof_enabled"))
        or bool(boundary_flags.get("hil_pass_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
            handoff_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response review handoff was blocked because summary fields could expose "
            "raw manifests, artifacts, control data, paths, credentials, DB/queue URLs, "
            "checksums, tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, "
            "external proof, PR-resolution, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "handoff_unsafe_rejected",
                "handoff_status": "handoff_unsafe_rejected",
                "review_handoff_status": {
                    "status": "handoff_unsafe_rejected",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw manifest, artifact, control, path, credential, "
                        "DB/queue, checksum, traceback, ROS topic, serial/UART, "
                        "WAVE ROVER, HIL/pass, external proof, PR-resolution, or success material"
                    ),
                },
                "handoff_reasons": [],
                "next_required_evidence": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref owner response review handoff.",
                "support_next_step": "Reject unsafe owner response review handoff metadata until only safe fields remain.",
                "reviewer_next_step": "Keep owner response review handoff not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
    source,
):
    """构建 acceptance handoff intake owner response reviewer ACK intake 的 Robot-safe 摘要。"""
    # ACK intake 是只读治理状态，Robot diagnostics 不能从这里派生控制、ACK 写入或 HIL 结论。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK intake is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK intake summary missing"
            )
            summary["reviewer_ack_intake_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                ack_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response reviewer ACK intake: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reviewer_ack_intake_status"]["reason"] = safe_error
            return summary

    if not isinstance(ack_doc, dict):
        summary["reviewer_ack_intake_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response reviewer ACK intake JSON must be an object"
        )
        return summary

    diagnostics = ack_doc.get("diagnostics") if isinstance(ack_doc.get("diagnostics"), dict) else {}
    raw_schema = str(ack_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source_contract(
            ack_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    }:
        summary_fragment = ack_doc
    else:
        summary_fragment = {}
        for candidate in (
            ack_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            ack_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            ack_doc.get("robot_compatible_summary"),
            ack_doc.get("summary"),
            ack_doc.get("diagnostics_summary"),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_doc = (
        summary_fragment.get("reviewer_ack_intake_status")
        if isinstance(summary_fragment.get("reviewer_ack_intake_status"), dict)
        else summary_fragment.get("ack_status_summary")
        if isinstance(summary_fragment.get("ack_status_summary"), dict)
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
    safe_copy = summary_fragment.get("safe_copy") or summary_fragment.get("safe_phone_copy") or summary["safe_copy"]
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if (
        "source=software_proof" not in safe_copy_text
        or "not_proven" not in safe_copy_text
        or "safe_to_control=false" not in safe_copy_text
        or "delivery_success=false" not in safe_copy_text
        or "primary_actions_enabled=false" not in safe_copy_text
    ):
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    ack_status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("ack_intake_status")
        or summary_fragment.get("status")
        or "blocked_missing_owner_response_review_handoff"
    )
    source_handoff_status = summary_fragment.get(
        "source_owner_response_review_handoff_status"
    ) or summary_fragment.get("source_review_handoff_status")
    if isinstance(source_handoff_status, dict):
        source_handoff_status = source_handoff_status.get("status") or source_handoff_status.get("handoff_status")
    source_handoff_status = _redact_route_task_rehearsal_text(source_handoff_status or "unknown")
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
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "status": ack_status,
            "ack_intake_status": ack_status,
            "overall_status": "not_proven",
            "reviewer_ack_intake_status": {
                "status": ack_status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or (
                        "field evidence rerun execution result acceptance handoff "
                        "intake owner response reviewer ACK intake is software_proof only"
                    )
                ),
            },
            "source_owner_response_review_handoff_status": source_handoff_status,
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons") or summary_fragment.get("reviewer_ack_reasons")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or "Owner keeps same-ref reviewer ACK intake metadata separate from field proof."
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step")
                or "Support checks only metadata-only reviewer ACK intake fields."
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step")
                or "Reviewer records ACK intake without PR resolution, HIL, or delivery success."
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "status": ack_status,
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_not_proven(
                    ack_doc,
                    summary_fragment,
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "read_error": "",
        }
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
            item
        )
        for item in (
            status_doc,
            summary["source_owner_response_review_handoff_status"],
            summary["ack_reasons"],
            summary["next_required_evidence"],
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["reviewer_ack_intake_status"] = {
            "status": "blocked_missing_owner_response_review_handoff",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "missing safe reviewer ACK intake summary",
        }
        summary["status"] = summary["reviewer_ack_intake_status"]["status"]
        summary["ack_intake_status"] = summary["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
    ):
        summary["reviewer_ack_intake_status"] = {
            "status": "reviewer_ack_rejected_unsafe",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK intake schema or boundary is unsupported",
        }
        summary["status"] = summary["reviewer_ack_intake_status"]["status"]
        summary["ack_intake_status"] = summary["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or summary["ack_intake_status"]
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES
        or not summary["software_proof"]
    ):
        summary["reviewer_ack_intake_status"] = {
            "status": "reviewer_ack_rejected_unsafe",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK intake must remain software_proof and not_proven",
        }
        summary["status"] = summary["reviewer_ack_intake_status"]["status"]
        summary["ack_intake_status"] = summary["status"]
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["source_owner_response_review_handoff_status"]
        or not summary["ack_reasons"]
        or not summary["next_required_evidence"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["reviewer_ack_intake_status"] = {
            "status": "blocked_missing_owner_response_review_handoff",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK intake is missing safe metadata",
        }
        summary["status"] = summary["reviewer_ack_intake_status"]["status"]
        summary["ack_intake_status"] = summary["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("external_proof_enabled"))
        or bool(boundary_flags.get("hil_pass_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
            ack_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response reviewer ACK intake was blocked because summary fields could expose "
            "raw manifests, artifacts, control data, paths, credentials, DB/queue URLs, "
            "checksums, tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, "
            "external proof, PR-resolution, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "reviewer_ack_rejected_unsafe",
                "ack_intake_status": "reviewer_ack_rejected_unsafe",
                "reviewer_ack_intake_status": {
                    "status": "reviewer_ack_rejected_unsafe",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw manifest, artifact, control, path, credential, "
                        "DB/queue, checksum, traceback, ROS topic, serial/UART, "
                        "WAVE ROVER, HIL/pass, external proof, PR-resolution, or success material"
                    ),
                },
                "ack_reasons": [],
                "next_required_evidence": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref reviewer ACK intake.",
                "support_next_step": "Reject unsafe reviewer ACK intake metadata until only safe fields remain.",
                "reviewer_next_step": "Keep reviewer ACK intake not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision(
    source,
):
    """构建 acceptance reviewer ACK review-decision 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 sanitized summary；review-decision 不能派生 ACK 写入、回放、Nav2 或交付成功。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK review decision is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK review decision summary missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response reviewer ACK review decision: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            return summary

    if not isinstance(decision_doc, dict):
        summary["review_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response reviewer ACK review decision JSON must be an object"
        )
        return summary

    diagnostics = (
        decision_doc.get("diagnostics")
        if isinstance(decision_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(decision_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source_contract(
            decision_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    }:
        summary_fragment = decision_doc
    else:
        summary_fragment = {}
        for candidate in (
            decision_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            decision_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            decision_doc.get("robot_compatible_summary"),
            decision_doc.get("summary"),
            decision_doc.get("diagnostics_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source_contract(
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
    if (
        "source=software_proof" not in safe_copy_text
        or "not_proven" not in safe_copy_text
        or "safe_to_control=false" not in safe_copy_text
        or "delivery_success=false" not in safe_copy_text
        or "primary_actions_enabled=false" not in safe_copy_text
    ):
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
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
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
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
                or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA
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
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step") or ""
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step") or ""
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step") or ""
            ),
            "review_handoff_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_handoff_recommendation") or ""
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_not_proven(
                    decision_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields(
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
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            summary["review_handoff_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_status"]["status"] = (
            "blocked_missing_reviewer_ack_intake_not_proven"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
    ):
        summary["review_status"] = {
            "status": "rejected_unsafe_reviewer_ack_not_proven",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK review decision schema or boundary is unsupported",
        }
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or review_decision
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_status"]["status"] = "rejected_unsafe_reviewer_ack_not_proven"
        summary["review_status"]["reason"] = (
            "reviewer ACK review decision must remain software_proof and not_proven"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        not summary["safe_evidence_ref"]
        or not summary["source_reviewer_ack_intake_status"]
        or not summary["decision_reasons"]
        or not summary["next_required_evidence"]
        or not summary["owner_next_step"]
        or not summary["support_next_step"]
        or not summary["reviewer_next_step"]
    ):
        summary["review_status"]["status"] = (
            "blocked_missing_reviewer_ack_intake_not_proven"
        )
        summary["review_status"]["reason"] = (
            "reviewer ACK review decision is missing safe metadata"
        )
        summary["status"] = summary["review_status"]["status"]
        summary["review_decision"] = summary["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("external_proof_enabled"))
        or bool(boundary_flags.get("hil_pass_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields(
            decision_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response reviewer ACK review decision was blocked because summary fields "
            "could expose raw artifacts, control data, paths, credentials, DB/queue URLs, "
            "checksums, tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, "
            "route/elevator field-pass, PR-resolution, or success wording; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "review_decision": "rejected_unsafe_reviewer_ack_not_proven",
                "status": "rejected_unsafe_reviewer_ack_not_proven",
                "review_status": {
                    "status": "rejected_unsafe_reviewer_ack_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe raw artifact, control, path, credential, DB/queue, "
                        "checksum, traceback, ROS topic, serial/UART, WAVE ROVER, "
                        "HIL/pass, route/elevator field-pass, PR-resolution, or success material"
                    ),
                },
                "decision_reasons": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref reviewer ACK review decision.",
                "support_next_step": "Reject unsafe reviewer ACK review decision metadata until only safe fields remain.",
                "reviewer_next_step": "Keep reviewer ACK review decision not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff(
    source,
):
    """构建 acceptance reviewer ACK review-handoff 的 Robot-safe diagnostics 摘要。"""
    # Robot 只消费 sanitized summary；review-handoff 不能派生 ACK 写入、回放、Nav2 或交付成功。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK review handoff is not configured"
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
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK review handoff summary missing"
            )
            summary["review_handoff_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response reviewer ACK review handoff: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_handoff_status"]["reason"] = safe_error
            return summary

    if not isinstance(handoff_doc, dict):
        summary["review_handoff_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response reviewer ACK review handoff JSON must be an object"
        )
        return summary

    diagnostics = (
        handoff_doc.get("diagnostics")
        if isinstance(handoff_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(handoff_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source_contract(
            handoff_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    }:
        summary_fragment = handoff_doc
    else:
        summary_fragment = {}
        for candidate in (
            handoff_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            handoff_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            handoff_doc.get("robot_compatible_summary"),
            handoff_doc.get("summary"),
            handoff_doc.get("diagnostics_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source_contract(
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
    if (
        "source=software_proof" not in safe_copy_text
        or "not_proven" not in safe_copy_text
        or "safe_to_control=false" not in safe_copy_text
        or "delivery_success=false" not in safe_copy_text
        or "primary_actions_enabled=false" not in safe_copy_text
    ):
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
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
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
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
                or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA
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
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or ""
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step") or ""
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step") or ""
            ),
            "review_handoff_recommendation": _redact_route_task_rehearsal_text(
                summary_fragment.get("review_handoff_recommendation") or ""
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": handoff_status,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_not_proven(
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
        in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES,
        bool(summary["source_reviewer_ack_review_decision_status"]),
        bool(summary["previous_reviewer_ack_review_decision_ref"]),
        bool(summary["handoff_reasons"]),
        bool(summary["handoff_targets"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_next_step"]),
        bool(summary["support_next_step"]),
        bool(summary["reviewer_next_step"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields(
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
            summary["owner_next_step"],
            summary["support_next_step"],
            summary["reviewer_next_step"],
            summary["review_handoff_recommendation"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_reviewer_ack_review_decision_not_proven"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
    ):
        summary["review_handoff_status"] = {
            "status": "rejected_unsafe_reviewer_ack_handoff_not_proven",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK review handoff schema or boundary is unsupported",
        }
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or handoff_status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES
        or not summary["software_proof"]
    ):
        summary["review_handoff_status"]["status"] = (
            "rejected_unsafe_reviewer_ack_handoff_not_proven"
        )
        summary["review_handoff_status"]["reason"] = (
            "reviewer ACK review handoff must remain software_proof and not_proven"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if not all(required_safe_metadata):
        summary["review_handoff_status"]["status"] = (
            "blocked_missing_reviewer_ack_review_decision_not_proven"
        )
        summary["review_handoff_status"]["reason"] = (
            "reviewer ACK review handoff is missing safe metadata"
        )
        summary["status"] = summary["review_handoff_status"]["status"]
        summary["handoff_status"] = summary["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("external_proof_enabled"))
        or bool(boundary_flags.get("hil_pass_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields(
            handoff_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response reviewer ACK review handoff was blocked because summary fields "
            "could expose artifact details, control data, paths, credentials, DB/queue URLs, "
            "checksums, tracebacks, ROS topics, serial/UART, WAVE ROVER, HIL/pass, "
            "route/elevator field-pass, PR-resolution, or success wording; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "handoff_status": "rejected_unsafe_reviewer_ack_handoff_not_proven",
                "status": "rejected_unsafe_reviewer_ack_handoff_not_proven",
                "review_handoff_status": {
                    "status": "rejected_unsafe_reviewer_ack_handoff_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe artifact, control, path, credential, DB/queue, "
                        "checksum, traceback, ROS topic, serial/UART, WAVE ROVER, "
                        "HIL/pass, route/elevator field-pass, PR-resolution, or success material"
                    ),
                },
                "handoff_reasons": [],
                "handoff_targets": [],
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "unsafe_materials": [],
                "next_required_evidence": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref reviewer ACK review handoff.",
                "support_next_step": "Reject unsafe reviewer ACK review handoff metadata until only safe fields remain.",
                "reviewer_next_step": "Keep reviewer ACK review handoff not_proven and request sanitized software-proof metadata.",
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


def summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status(
    source,
):
    """构建 acceptance reviewer ACK follow-up escalation status 的 Robot-safe diagnostics 摘要。"""
    # Robot 只展示 Autonomy PC gate 的 safe summary；升级状态不能触发 ACK、回放、Nav2 或机器人控制。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary(
            source_path,
            read_error=(
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK followup escalation status is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        status_doc = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "field evidence rerun execution result acceptance handoff intake "
                "owner response reviewer ACK followup escalation status summary missing"
            )
            summary["followup_escalation_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                status_doc = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading field evidence rerun execution result acceptance "
                f"handoff intake owner response reviewer ACK followup escalation status: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_escalation_status"]["reason"] = safe_error
            return summary

    if not isinstance(status_doc, dict):
        summary["followup_escalation_status"]["reason"] = (
            "field evidence rerun execution result acceptance handoff intake owner response reviewer ACK followup escalation status JSON must be an object"
        )
        return summary

    diagnostics = (
        status_doc.get("diagnostics")
        if isinstance(status_doc.get("diagnostics"), dict)
        else {}
    )
    raw_schema = str(status_doc.get("schema") or "")
    source_schema, source_boundary = (
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source_contract(
            status_doc
        )
    )
    if raw_schema in {
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    }:
        summary_fragment = status_doc
    else:
        summary_fragment = {}
        for candidate in (
            status_doc.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            status_doc.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            status_doc.get("robot_compatible_summary"),
            status_doc.get("summary"),
            status_doc.get("diagnostics_summary"),
            diagnostics.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics.get("summary"),
            diagnostics.get("diagnostics_summary"),
        ):
            if isinstance(candidate, dict):
                summary_fragment = candidate
                break
    if summary_fragment:
        nested_schema, nested_boundary = (
            _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source_contract(
                summary_fragment
            )
        )
        if nested_schema:
            source_schema, source_boundary = nested_schema, nested_boundary

    status_block = (
        summary_fragment.get("followup_escalation_status")
        if isinstance(summary_fragment.get("followup_escalation_status"), dict)
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
    if (
        "source=software_proof" not in safe_copy_text
        or "not_proven" not in safe_copy_text
        or "safe_to_control=false" not in safe_copy_text
        or "delivery_success=false" not in safe_copy_text
        or "primary_actions_enabled=false" not in safe_copy_text
    ):
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_block.get("status")
        or summary_fragment.get("status")
        or "blocked_missing_reviewer_ack_review_handoff_not_proven"
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or status_doc.get("safe_evidence_ref")
        or status_doc.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or status_doc.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source": _redact_route_task_rehearsal_text(
                summary_fragment.get("source") or EVIDENCE_SOURCE_SOFTWARE
            ),
            "exists": True,
            "safe_evidence_ref": safe_evidence_ref,
            "status": status,
            "overall_status": "not_proven",
            "followup_escalation_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_block.get("reason")
                    or summary_fragment.get("reason")
                    or "reviewer ACK followup escalation status is software_proof only"
                ),
            },
            "source_reviewer_ack_review_handoff_schema": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_review_handoff_schema")
                or FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA
            ),
            "source_reviewer_ack_review_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_review_handoff_status")
                or "blocked"
            ),
            "previous_reviewer_ack_review_handoff_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("previous_reviewer_ack_review_handoff_ref")
                or summary_fragment.get("source_reviewer_ack_review_handoff_ref")
                or ""
            ),
            "missing_evidence_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_evidence_summary")
                or summary_fragment.get("missing_materials")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("owner_next_step")
                or summary_fragment.get("owner_action")
                or ""
            ),
            "reviewer_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_next_step") or ""
            ),
            "support_next_step": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_next_step") or ""
            ),
            "evidence_boundary_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("evidence_boundary_status") or "not_proven"
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status,
            },
            "software_proof": summary_fragment.get("software_proof") is not False,
            "not_proven": (
                _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_not_proven(
                    status_doc,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    required_safe_metadata = (
        bool(summary_fragment),
        bool(summary["safe_evidence_ref"]),
        status
        in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES,
        bool(summary["source_reviewer_ack_review_handoff_status"]),
        bool(summary["previous_reviewer_ack_review_handoff_ref"]),
        bool(summary["missing_evidence_summary"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_next_step"]),
        bool(summary["reviewer_next_step"]),
        bool(summary["support_next_step"]),
    )
    boundary_flags = _safe_pc_route_debug_dict(summary_fragment.get("boundary_flags")) or {}
    unsafe_material = any(
        _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            item
        )
        for item in (
            status_block,
            summary["missing_evidence_summary"],
            summary["next_required_evidence"],
            summary["owner_next_step"],
            summary["reviewer_next_step"],
            summary["support_next_step"],
            robot_summary,
            safe_copy,
            safe_copy_text,
        )
    )
    if not summary_fragment:
        summary["followup_escalation_status"]["status"] = (
            "blocked_missing_reviewer_ack_review_handoff_not_proven"
        )
        summary["status"] = summary["followup_escalation_status"]["status"]
        return summary
    if (
        source_schema
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary["followup_escalation_status"] = {
            "status": "blocked_missing_reviewer_ack_review_handoff_not_proven",
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": "reviewer ACK followup escalation status schema or boundary is unsupported",
        }
        summary["status"] = summary["followup_escalation_status"]["status"]
        return summary
    if (
        summary["source"] != EVIDENCE_SOURCE_SOFTWARE
        or summary["evidence_boundary_status"] != "not_proven"
        or status
        not in FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES
        or not summary["software_proof"]
    ):
        summary["followup_escalation_status"]["status"] = (
            "escalated_missing_real_material_not_proven"
        )
        summary["followup_escalation_status"]["reason"] = (
            "reviewer ACK followup escalation status must remain software_proof and not_proven"
        )
        summary["status"] = summary["followup_escalation_status"]["status"]
        return summary
    if not all(required_safe_metadata):
        summary["followup_escalation_status"]["status"] = (
            "blocked_missing_reviewer_ack_review_handoff_not_proven"
        )
        summary["followup_escalation_status"]["reason"] = (
            "reviewer ACK followup escalation status is missing safe metadata"
        )
        summary["status"] = summary["followup_escalation_status"]["status"]
        return summary
    if (
        summary_fragment.get("safe_to_control") is not False
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or bool(boundary_flags.get("control_entrypoint_enabled"))
        or bool(boundary_flags.get("readiness_enabled"))
        or bool(boundary_flags.get("reviewer_resolution_enabled"))
        or bool(boundary_flags.get("external_proof_enabled"))
        or bool(boundary_flags.get("hil_pass_enabled"))
        or bool(boundary_flags.get("ack_mutation_enabled"))
        or bool(boundary_flags.get("cursor_mutation_enabled"))
        or bool(boundary_flags.get("replay_enabled"))
        or bool(boundary_flags.get("resubmit_enabled"))
        or unsafe_material
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            status_doc
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            summary_fragment
        )
        or _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields(
            robot_summary
        )
    ):
        blocked_copy = (
            "Field evidence rerun execution result acceptance handoff intake owner "
            "response reviewer ACK followup escalation status was blocked because "
            "summary fields could expose artifact details, control data, paths, "
            "credentials, DB/queue URLs, checksums, tracebacks, ROS topics, "
            "serial/UART, WAVE ROVER, HIL/pass, route/elevator field-pass, "
            "PR-resolution, or success wording; safe_to_control=false; "
            "delivery_success=false; primary_actions_enabled=false."
        )
        summary.update(
            {
                "status": "escalated_missing_real_material_not_proven",
                "followup_escalation_status": {
                    "status": "escalated_missing_real_material_not_proven",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": (
                        "unsafe artifact, control, path, credential, DB/queue, "
                        "checksum, traceback, ROS topic, serial/UART, WAVE ROVER, "
                        "HIL/pass, route/elevator field-pass, PR-resolution, or success material"
                    ),
                },
                "missing_evidence_summary": [],
                "next_required_evidence": [],
                "owner_next_step": "Remove unsafe material and provide sanitized same-ref reviewer ACK followup status.",
                "reviewer_next_step": "Keep reviewer ACK followup not_proven and request sanitized software-proof metadata.",
                "support_next_step": "Reject unsafe reviewer ACK followup status until only safe fields remain.",
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
