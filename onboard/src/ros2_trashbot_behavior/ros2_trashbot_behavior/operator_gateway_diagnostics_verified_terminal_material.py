import json
import os
import re

from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    _route_task_field_run_readiness_has_unsafe_fields,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    _redact_route_task_rehearsal_text,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_task_field_retest import (
    _route_task_field_retest_execution_pack_has_success_wording,
)


EVIDENCE_SOURCE_SOFTWARE = "software_proof"


def _task_terminal_field_material_intake_copy_is_unsafe(value):
    # 材料入口 copy 面向手机/diagnostics，任何现场通过、HIL、O5 或控制授权暗示都必须整体阻断。
    text = _redact_route_task_rehearsal_text(value).strip().lower()
    if not text:
        return True
    guarded_phrases = (
        "not delivery success",
        "not a delivery success",
        "delivery_success=false",
        "primary_actions_enabled=false",
        "safe_to_control=false",
        "not field pass",
        "not real field pass",
        "not route/elevator field pass",
        "not hil",
        "not proven",
        "not_proven",
        "metadata-only",
        "software_proof",
        "must not",
    )
    unsafe_phrases = (
        "delivery success",
        "field pass",
        "field-pass",
        "route/elevator field pass",
        "route elevator field pass",
        "hil pass",
        "real hil",
        "o5 external proof",
        "external proof passed",
        "control grant",
        "safe to control",
        "start delivery enabled",
        "confirm dropoff enabled",
        "cancel enabled",
        "ack posted",
        "terminal ack",
        "cursor advanced",
        "nav2 started",
        "dropoff complete",
        "cancel complete",
    )
    guarded_text = text
    for guard in guarded_phrases:
        guarded_text = guarded_text.replace(guard, "")
    for phrase in unsafe_phrases:
        if phrase in guarded_text:
            return True
    return False


def _real_material_evidence_ref_is_unsafe(value):
    # evidence_ref 只允许短的逻辑引用；本地路径、脱敏标记、空白或 shell 字符都不能进 diagnostics。
    text = str(value or "").strip()
    if (
        not text
        or text.startswith("local_path_redacted:")
        or "[REDACTED" in text
        or not re.fullmatch(r"(?:evidence://)?[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", text)
    ):
        return True
    return False


VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SCHEMA = (
    "trashbot.verified_terminal_result_material_intake.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_intake_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_GATE = (
    "software_proof_docker_verified_terminal_result_material_intake_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SCHEMA = (
    "trashbot.verified_terminal_result_material_review_decision.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_review_decision_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_GATE = (
    "software_proof_docker_verified_terminal_result_material_review_decision_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.verified_terminal_result_material_review_handoff.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_verified_terminal_result_material_review_handoff_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_STATUSES = (
    "ready_for_owner_handoff",
    "needs_material_backfill",
    "rejected",
    "blocked",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.verified_terminal_result_material_followup_escalation_status.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_STATUSES = (
    "escalated_for_terminal_result_material_followup_not_proven",
    "waiting_for_terminal_result_material_backfill_not_proven",
    "needs_support_owner_reassignment_not_proven",
    "rejected_unsafe_terminal_result_followup_not_proven",
    "blocked_missing_terminal_result_review_handoff_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_intake.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_intake_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_intake_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_STATUSES = (
    "accepted_not_proven",
    "missing_not_proven",
    "rejected_not_proven",
    "blocked_not_proven",
    "accepted_for_later_review_not_proven",
    "blocked_missing_terminal_result_followup_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_review_decision.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_STATUSES = (
    "accepted_for_next_handoff_not_proven",
    "missing_not_proven",
    "rejected_not_proven",
    "blocked_not_proven",
    "blocked_missing_terminal_result_owner_response_intake_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_review_handoff.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES = (
    "acknowledged_not_proven",
    "needs_reassignment_not_proven",
    "blocked_missing_handoff_not_proven",
    "rejected_unsafe_ack_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES = (
    "accepted_for_review_not_proven",
    "missing_material_not_proven",
    "reassignment_required_not_proven",
    "rejected_unsafe_not_proven",
    "blocked_missing_source_intake_not_proven",
    "evidence_ref_mismatch_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES = (
    "accepted_for_reviewer_ack_handoff_not_proven",
    "ready_for_field_owner_reviewer_ack_followup_not_proven",
    "needs_reviewer_handoff_reassignment_not_proven",
    "needs_field_owner_ack_material_supplement_not_proven",
    "rejected_unsafe_reviewer_ack_handoff_not_proven",
    "blocked_missing_reviewer_ack_review_decision_not_proven",
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA = (
    "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA = (
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE = (
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate"
)
VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES = (
    "pending",
    "due",
    "overdue",
    "escalated",
    "blocked_missing_real_materials",
    "pending_not_proven",
    "due_not_proven",
    "overdue_not_proven",
    "escalated_not_proven",
    "blocked_missing_real_materials_not_proven",
)
__all__ = (
    "VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE",
    "VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES",
    "_verified_terminal_result_material_intake_not_proven",
    "_default_verified_terminal_result_material_intake_summary",
    "_verified_terminal_result_material_intake_source_contract",
    "_verified_terminal_result_material_intake_summary_fragment",
    "_verified_terminal_result_material_intake_has_unsafe_controls",
    "_verified_terminal_result_material_intake_safe_list",
    "summarize_verified_terminal_result_material_intake",
    "_verified_terminal_result_material_review_decision_not_proven",
    "_default_verified_terminal_result_material_review_decision_summary",
    "_verified_terminal_result_material_review_decision_summary_fragment",
    "_verified_terminal_result_material_review_decision_has_unsafe_controls",
    "_verified_terminal_result_material_review_decision_safe_list",
    "summarize_verified_terminal_result_material_review_decision",
    "_verified_terminal_result_material_review_handoff_not_proven",
    "_default_verified_terminal_result_material_review_handoff_summary",
    "_verified_terminal_result_material_review_handoff_source_contract",
    "_verified_terminal_result_material_review_handoff_summary_fragment",
    "_verified_terminal_result_material_review_handoff_has_unsafe_controls",
    "_verified_terminal_result_material_review_handoff_safe_list",
    "summarize_verified_terminal_result_material_review_handoff",
    "_verified_terminal_result_material_followup_escalation_status_not_proven",
    "_default_verified_terminal_result_material_followup_escalation_status_summary",
    "_verified_terminal_result_material_followup_escalation_status_source_contract",
    "_verified_terminal_result_material_followup_escalation_status_summary_fragment",
    "_verified_terminal_result_material_followup_escalation_status_has_unsafe_controls",
    "_verified_terminal_result_material_followup_escalation_status_safe_list",
    "summarize_verified_terminal_result_material_followup_escalation_status",
    "_verified_terminal_result_material_owner_response_intake_not_proven",
    "_default_verified_terminal_result_material_owner_response_intake_summary",
    "_verified_terminal_result_material_owner_response_intake_source_contract",
    "_verified_terminal_result_material_owner_response_intake_summary_fragment",
    "_verified_terminal_result_material_owner_response_intake_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_intake",
    "_verified_terminal_result_material_owner_response_review_decision_not_proven",
    "_default_verified_terminal_result_material_owner_response_review_decision_summary",
    "_verified_terminal_result_material_owner_response_review_decision_source_contract",
    "_verified_terminal_result_material_owner_response_review_decision_summary_fragment",
    "_verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_review_decision",
    "_verified_terminal_result_material_owner_response_review_handoff_not_proven",
    "_default_verified_terminal_result_material_owner_response_review_handoff_summary",
    "_verified_terminal_result_material_owner_response_review_handoff_summary_fragment",
    "_verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_review_handoff",
    "_verified_terminal_result_material_owner_response_reviewer_ack_intake_not_proven",
    "_default_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
    "_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary_fragment",
    "_verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_reviewer_ack_intake",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_not_proven",
    "_default_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary_fragment",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_decision",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_not_proven",
    "_default_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary_fragment",
    "_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff",
    "_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_not_proven",
    "_default_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
    "_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary_fragment",
    "_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls",
    "summarize_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status",
)


def _verified_terminal_result_material_intake_not_proven(intake=None, summary_fragment=None):
    # 终态材料入口只能说明“材料已被归档到安全摘要”，真实送达和控制授权仍要外部证明。
    values = [
        "verified_terminal_result_material_intake_only",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "replay_or_resubmit",
        "real_hil_pass",
    ]
    for container in (intake or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_intake_summary(
    path,
    status="blocked_missing_verified_terminal_result_material_intake_summary",
    read_error="",
):
    # 缺少 verified terminal result 材料摘要时必须完整 fail-closed，不能把空摘要当成送达成功。
    safe_copy = (
        "Verified terminal result material intake is metadata-only; "
        "source=software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false; safe_to_control=false."
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "intake_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": read_error
            or "verified_terminal_result_material_intake summary is not configured",
        },
        "safe_evidence_ref": "",
        "accepted_materials": [],
        "missing_materials": [],
        "rejected_materials": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _verified_terminal_result_material_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _verified_terminal_result_material_intake_source_contract(value):
    if not isinstance(value, dict):
        return "", ""
    schema = str(value.get("source_schema") or value.get("schema") or "")
    boundary = str(value.get("source_evidence_boundary") or value.get("evidence_boundary") or "")
    return schema, boundary


def _verified_terminal_result_material_intake_summary_fragment(value):
    # Robot 只选取 canonical summary 或兼容 diagnostics/status summary；raw artifact 不能直接成为输出。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") == VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY_SCHEMA:
        return value
    for candidate in (
        value.get("verified_terminal_result_material_intake_summary"),
        value.get("robot_diagnostics_verified_terminal_result_material_intake_summary"),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = _verified_terminal_result_material_intake_summary_fragment(container)
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_intake_has_unsafe_controls(value):
    # verified terminal result 材料入口不允许隐藏任何控制、ACK、cursor、replay 或 resubmit 能力。
    unsafe_true_keys = {
        "ack_mutation_allowed",
        "cursor_mutation_allowed",
        "replay_allowed",
        "resubmit_allowed",
        "robot_control_allowed",
        "robot_command_allowed",
        "start_delivery_enabled",
        "confirm_dropoff_enabled",
        "cancel_enabled",
        "commands_enabled",
    }
    unsafe_key_fragments = (
        "raw",
        "ack_cursor",
        "ack_mutation",
        "cursor_mutation",
        "replay_command",
        "resubmit_command",
        "robot_control",
        "command_envelope",
        "control_envelope",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _verified_terminal_result_material_intake_has_unsafe_controls(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_intake_has_unsafe_controls(item)
            for item in value
        )
    return False


def _verified_terminal_result_material_intake_safe_list(value):
    # 列表只保留材料类别和下一步说明；raw/cursor/replay 词面不能出现在 Robot 输出里。
    safe_items = []
    for item in _safe_route_task_rehearsal_list(value):
        lowered = str(item or "").lower()
        if any(
            marker in lowered
            for marker in (
                "raw",
                "ack_cursor",
                "cursor_mutation",
                "ack_mutation",
                "replay",
                "resubmit",
            )
        ):
            continue
        safe_items.append(item)
    return safe_items


def summarize_verified_terminal_result_material_intake(source):
    """构建 verified terminal result 材料入口的只读 Robot diagnostics 摘要。"""
    # summary 是材料入口可见性，不是 delivery success；因此所有动作、ACK、cursor 和重放能力都固定关闭。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_intake_summary(
        source_path,
        read_error="verified_terminal_result_material_intake summary is not configured",
    )
    if isinstance(source, dict):
        intake = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = "verified_terminal_result_material_intake summary artifact missing"
            summary["intake_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                intake = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading verified_terminal_result_material_intake summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["intake_status"]["reason"] = safe_error
            return summary

    if not isinstance(intake, dict):
        summary["intake_status"]["reason"] = (
            "verified_terminal_result_material_intake JSON must be an object"
        )
        return summary

    raw_schema = str(intake.get("schema") or "")
    summary_fragment = _verified_terminal_result_material_intake_summary_fragment(intake)
    source_schema, source_boundary = _verified_terminal_result_material_intake_source_contract(
        summary_fragment or intake
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(intake.get("evidence_boundary") or "")
    intake_status = (
        summary_fragment.get("intake_status")
        if isinstance(summary_fragment.get("intake_status"), dict)
        else intake.get("intake_status")
        if isinstance(intake.get("intake_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or intake.get("safe_copy")
        or intake.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else intake.get("robot_diagnostics_summary")
        if isinstance(intake.get("robot_diagnostics_summary"), dict)
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
    status = _redact_route_task_rehearsal_text(
        intake_status.get("status")
        or summary_fragment.get("status")
        or summary_fragment.get("overall_status")
        or intake.get("status")
        or intake.get("overall_status")
        or "not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status") or intake.get("overall_status") or status
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or intake.get("source")
        or intake_status.get("evidence_source")
        or ""
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
            "source_evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "intake_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    intake_status.get("reason")
                    or summary_fragment.get("reason")
                    or intake.get("reason")
                    or "verified terminal result material intake is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "accepted_materials": _safe_pc_route_debug_value(
                summary_fragment.get("accepted_materials")
                if isinstance(summary_fragment.get("accepted_materials"), list)
                else []
            ),
            "missing_materials": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials")
            ),
            "rejected_materials": _verified_terminal_result_material_intake_safe_list(
                summary_fragment.get("rejected_materials")
            ),
            "next_required_evidence": _verified_terminal_result_material_intake_safe_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _verified_terminal_result_material_intake_safe_list(
                summary_fragment.get("owner_handoff")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_phone_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _verified_terminal_result_material_intake_not_proven(
                intake,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    accepted_schemas = {
        VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary != VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "intake_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_intake schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SCHEMA and not summary_fragment:
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_intake_summary",
                "intake_status": {
                    "status": "blocked_missing_verified_terminal_result_material_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_intake artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    # 任一 raw/control/success 线索都降级，避免 diagnostics alias 被手机端误当成送达或远控入口。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or status != "not_proven"
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or (
            raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SCHEMA
            and (
                intake.get("delivery_success") is not False
                or intake.get("primary_actions_enabled") is not False
                or intake.get("safe_to_control") is not False
            )
        )
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(intake)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _verified_terminal_result_material_intake_has_unsafe_controls(intake)
        or _verified_terminal_result_material_intake_has_unsafe_controls(
            summary_fragment
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Verified terminal result material intake was blocked because the summary "
            "did not remain software_proof/not_proven with delivery_success=false, "
            "primary_actions_enabled=false, and safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_intake_summary",
                "intake_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_intake contains unsafe fields, success wording, raw details, ACK/cursor/replay claims, or control claims",
                },
                "safe_evidence_ref": "",
                "accepted_materials": [],
                "missing_materials": [],
                "rejected_materials": [],
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


def _verified_terminal_result_material_review_decision_not_proven(
    decision=None, summary_fragment=None
):
    # review decision 只能说明“材料进入复核队列”，不能被解释成送达、ACK 或控制授权。
    values = [
        "verified_terminal_result_material_review_decision_only",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "replay_or_resubmit",
        "real_hil_pass",
    ]
    for container in (decision or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_review_decision_summary(
    path,
    status="blocked_missing_verified_terminal_result_material_review_decision_summary",
    read_error="",
):
    # 缺省摘要必须带完整 false 状态，避免空输入被手机或支持面误读成可执行状态。
    safe_copy = (
        "Verified terminal result material review decision is metadata-only; "
        "source=software_proof; not_proven; delivery_success=false; "
        "primary_actions_enabled=false; safe_to_control=false."
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_review_decision",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "review_decision": "blocked",
        "review_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": read_error
            or "verified_terminal_result_material_review_decision summary is not configured",
        },
        "source_intake_status": {},
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "decision_reasons": [],
        "material_status_summary": {},
        "blocked_reason": read_error,
        "rejected_reason": "",
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _verified_terminal_result_material_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _verified_terminal_result_material_review_decision_summary_fragment(value):
    # Robot 只消费 summary-only 字段；artifact wrapper 中的 raw body 不允许直接透传。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") == VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA:
        return value
    for candidate in (
        value.get("verified_terminal_result_material_review_decision_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_review_decision_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = _verified_terminal_result_material_review_decision_summary_fragment(
                container
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_review_decision_has_unsafe_controls(value):
    # review decision alias 是诊断安全面；发现 raw、ACK/cursor、replay、resubmit 或控制字段就整体降级。
    unsafe_true_keys = {
        "ack_mutation_allowed",
        "cursor_mutation_allowed",
        "replay_allowed",
        "resubmit_allowed",
        "robot_control_allowed",
        "robot_command_allowed",
        "start_delivery_enabled",
        "confirm_dropoff_enabled",
        "cancel_enabled",
        "commands_enabled",
    }
    unsafe_key_fragments = (
        "raw",
        "ack_cursor",
        "ack_mutation",
        "cursor_mutation",
        "replay",
        "resubmit",
        "robot_control",
        "command_envelope",
        "control_envelope",
        "authorization",
        "credential",
        "secret",
        "token",
        "checksum",
        "traceback",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _verified_terminal_result_material_review_decision_has_unsafe_controls(item):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_review_decision_has_unsafe_controls(item)
            for item in value
        )
    return False


def _verified_terminal_result_material_review_decision_safe_list(value):
    # 列表面向 operator/mobile 展示，只保留短文本并过滤 mutation/replay/control 词面。
    safe_items = []
    for item in _safe_route_task_rehearsal_list(value):
        lowered = str(item or "").lower()
        if any(
            marker in lowered
            for marker in (
                "raw",
                "ack_cursor",
                "cursor_mutation",
                "ack_mutation",
                "replay",
                "resubmit",
                "robot_control",
                "/cmd_vel",
            )
        ):
            continue
        safe_items.append(item)
    return safe_items


def summarize_verified_terminal_result_material_review_decision(source):
    """构建 verified terminal result material review decision 的只读 Robot diagnostics 摘要。"""
    # 本 alias 只提供支持排障摘要；所有机器人动作面在输出阶段强制保持关闭。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_review_decision_summary(
        source_path,
        read_error=(
            "verified_terminal_result_material_review_decision summary is not configured"
        ),
    )
    if isinstance(source, dict):
        decision = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_review_decision summary artifact missing"
            )
            summary["review_status"]["reason"] = summary["read_error"]
            summary["blocked_reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                decision = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading verified_terminal_result_material_review_decision summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_status"]["reason"] = safe_error
            summary["blocked_reason"] = safe_error
            return summary

    if not isinstance(decision, dict):
        summary["review_status"]["reason"] = (
            "verified_terminal_result_material_review_decision JSON must be an object"
        )
        return summary

    raw_schema = str(decision.get("schema") or "")
    summary_fragment = _verified_terminal_result_material_review_decision_summary_fragment(
        decision
    )
    source_schema, source_boundary = (
        _verified_terminal_result_material_intake_source_contract(
            summary_fragment or decision
        )
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(decision.get("evidence_boundary") or "")
    review_status = (
        summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else summary_fragment.get("decision_status")
        if isinstance(summary_fragment.get("decision_status"), dict)
        else decision.get("review_status")
        if isinstance(decision.get("review_status"), dict)
        else decision.get("decision_status")
        if isinstance(decision.get("decision_status"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or decision.get("safe_copy")
        or decision.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else decision.get("robot_diagnostics_summary")
        if isinstance(decision.get("robot_diagnostics_summary"), dict)
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
    review_decision = _redact_route_task_rehearsal_text(
        summary_fragment.get("review_decision")
        or decision.get("review_decision")
        or review_status.get("status")
        or "blocked"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or decision.get("overall_status")
        or "not_proven"
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or decision.get("source")
        or review_status.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or decision.get("safe_evidence_ref")
        or decision.get("evidence_ref", "")
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
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "status": review_decision,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "review_decision": review_decision,
            "review_status": {
                "status": review_decision,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    review_status.get("reason")
                    or summary_fragment.get("reason")
                    or decision.get("reason")
                    or "verified terminal result material review decision is software_proof only"
                ),
            },
            "source_intake_status": _safe_pc_route_debug_value(
                summary_fragment.get("source_intake_status")
                if isinstance(summary_fragment.get("source_intake_status"), dict)
                else {}
            ),
            "safe_evidence_ref": safe_evidence_ref,
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or decision.get("safe_command_id")
                or decision.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or decision.get("terminal_result_type")
                or ""
            ),
            "decision_reasons": (
                _verified_terminal_result_material_review_decision_safe_list(
                    summary_fragment.get("decision_reasons")
                )
            ),
            "material_status_summary": _safe_pc_route_debug_value(
                summary_fragment.get("material_status_summary")
                if isinstance(summary_fragment.get("material_status_summary"), dict)
                else {}
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason") or decision.get("blocked_reason") or ""
            ),
            "rejected_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("rejected_reason") or decision.get("rejected_reason") or ""
            ),
            "next_required_evidence": (
                _verified_terminal_result_material_review_decision_safe_list(
                    summary_fragment.get("next_required_evidence")
                )
            ),
            "owner_handoff": _verified_terminal_result_material_review_decision_safe_list(
                summary_fragment.get("owner_handoff")
            ),
            "safe_copy": _redact_route_task_rehearsal_text(safe_copy),
            "safe_phone_copy": _redact_route_task_rehearsal_text(safe_copy),
            "robot_diagnostics_summary": safe_robot_summary,
            "not_proven": _verified_terminal_result_material_review_decision_not_proven(
                decision,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    accepted_schemas = {
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    }
    if (
        source_schema not in accepted_schemas
        or source_boundary != VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "review_decision": "blocked",
                "review_status": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_decision schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "decision_reasons": [],
                "material_status_summary": {},
                "next_required_evidence": [],
                "owner_handoff": [],
            }
        )
        return summary
    if (
        raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_review_decision_summary",
                "review_decision": "blocked",
                "review_status": {
                    "status": "blocked_missing_verified_terminal_result_material_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_decision artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    # 所有可见输出都必须来自软件证明摘要；任何成功语义或 raw 控制字段都阻断 alias。
    if (
        source_value != EVIDENCE_SOURCE_SOFTWARE
        or overall_status != "not_proven"
        or _real_material_evidence_ref_is_unsafe(safe_evidence_ref)
        or (
            raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SCHEMA
            and (
                (
                    "delivery_success" in decision
                    and decision.get("delivery_success") is not False
                )
                or (
                    "primary_actions_enabled" in decision
                    and decision.get("primary_actions_enabled") is not False
                )
                or (
                    "safe_to_control" in decision
                    and decision.get("safe_to_control") is not False
                )
            )
        )
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(decision)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _verified_terminal_result_material_review_decision_has_unsafe_controls(
            decision
        )
        or _verified_terminal_result_material_review_decision_has_unsafe_controls(
            summary_fragment
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy)
        or _task_terminal_field_material_intake_copy_is_unsafe(
            safe_robot_summary.get("safe_copy", "")
        )
    ):
        blocked_copy = (
            "Verified terminal result material review decision was blocked because "
            "the summary did not remain software_proof/not_proven with "
            "delivery_success=false, primary_actions_enabled=false, and "
            "safe_to_control=false."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_review_decision_summary",
                "review_decision": "blocked",
                "review_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_decision contains unsafe fields, success wording, raw details, ACK/cursor/replay claims, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "decision_reasons": [],
                "material_status_summary": {},
                "blocked_reason": blocked_copy,
                "rejected_reason": "",
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


def _verified_terminal_result_material_review_handoff_not_proven(
    handoff=None, summary_fragment=None
):
    # handoff 只表示 owner 交接材料状态，不能被解释成终态送达、投放、取消或控制授权。
    values = [
        "verified_terminal_result_material_review_handoff_only",
        "handoff_status_not_delivery_success",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "replay_or_resubmit",
        "real_hil_pass",
    ]
    for container in (handoff or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_review_handoff_summary(
    path,
    handoff_status="blocked",
    read_error="",
):
    # 缺 handoff 时仍返回完整 false flags，避免空 diagnostics 被误当成送达完成或控制入口。
    safe_copy = (
        "Verified terminal result material review handoff is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "verified_terminal_result_material_review_handoff summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_review_handoff",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": handoff_status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "source_review_decision": {},
        "handoff_status": handoff_status,
        "handoff_status_detail": {
            "status": handoff_status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "material_status_summary": {},
        "accepted_material_refs": [],
        "missing_required_materials": [],
        "rejected_material_refs": [],
        "owner_handoff": [],
        "next_required_evidence": [],
        "blocked_reason": read_error,
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": _verified_terminal_result_material_review_handoff_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
    }


def _verified_terminal_result_material_review_handoff_source_contract(value):
    # source summary 和 Robot alias 都必须回指 handoff artifact 与本轮 handoff gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _verified_terminal_result_material_review_handoff_summary_fragment(value):
    # 兼容 latest_status / diagnostics / status 多层包装，但只取已经消毒的 summary。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get("verified_terminal_result_material_review_handoff_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_review_handoff_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = _verified_terminal_result_material_review_handoff_summary_fragment(
                container
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_review_handoff_has_unsafe_controls(value):
    # 任意控制、ACK/cursor mutation、重放、resubmit 或 raw diagnostics fetch 线索都要整体降级。
    unsafe_true_keys = {
        "ack_mutation_allowed",
        "cursor_mutation_allowed",
        "replay_allowed",
        "resubmit_allowed",
        "robot_control_allowed",
        "robot_command_allowed",
        "raw_diagnostics_fetch_allowed",
        "start_delivery_enabled",
        "confirm_dropoff_enabled",
        "cancel_enabled",
        "commands_enabled",
    }
    unsafe_key_fragments = (
        "raw",
        "ack_cursor",
        "ack_mutation",
        "cursor_mutation",
        "replay",
        "resubmit",
        "robot_control",
        "command_envelope",
        "control_envelope",
        "raw_diagnostics",
        "diagnostics_fetch",
        "authorization",
        "credential",
        "secret",
        "token",
        "checksum",
        "traceback",
        "local_path",
        "artifact_path",
        "file_path",
        "serial",
        "uart",
        "baud",
        "cmd_vel",
        "wave_rover",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
            ) and item is False:
                continue
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if key_text == "delivery_success" and item is not False:
                return True
            if key_text == "primary_actions_enabled" and item is not False:
                return True
            if key_text == "safe_to_control" and item is not False:
                return True
            if _verified_terminal_result_material_review_handoff_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_review_handoff_has_unsafe_controls(item)
            for item in value
        )
    if isinstance(value, str):
        if not value.strip():
            return False
        return (
            _task_terminal_field_material_intake_copy_is_unsafe(value)
            or _route_task_field_retest_execution_pack_has_success_wording(value)
        )
    return False


def _verified_terminal_result_material_review_handoff_safe_list(value):
    # 列表字段只保留可展示的短文本，过滤所有 mutation/replay/control/raw diagnostics 词面。
    safe_items = []
    for item in _safe_route_task_rehearsal_list(value):
        lowered = str(item or "").lower()
        if any(
            marker in lowered
            for marker in (
                "raw",
                "ack_cursor",
                "cursor_mutation",
                "ack_mutation",
                "replay",
                "resubmit",
                "robot_control",
                "diagnostics_fetch",
                "/cmd_vel",
            )
        ):
            continue
        safe_items.append(item)
    return safe_items


def summarize_verified_terminal_result_material_review_handoff(source):
    """构建 verified terminal result material review handoff 的只读 Robot diagnostics 摘要。"""
    # Robot 只消费 Task A 的 sanitized handoff；handoff 状态不能开启发车、投放确认、取消或 ACK/cursor 修改。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_review_handoff_summary(
        source_path,
        read_error=(
            "verified_terminal_result_material_review_handoff summary is not configured"
        ),
    )
    if isinstance(source, dict):
        handoff = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_review_handoff summary artifact missing"
            )
            summary["handoff_status_detail"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                handoff = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading verified_terminal_result_material_review_handoff summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["handoff_status_detail"]["reason"] = safe_error
            return summary

    if not isinstance(handoff, dict):
        summary["handoff_status_detail"]["reason"] = (
            "verified_terminal_result_material_review_handoff JSON must be an object"
        )
        return summary

    raw_schema = str(handoff.get("schema") or "")
    summary_fragment = _verified_terminal_result_material_review_handoff_summary_fragment(
        handoff
    )
    contract_source = summary_fragment if summary_fragment else handoff
    source_schema, source_boundary = (
        _verified_terminal_result_material_review_handoff_source_contract(
            contract_source
        )
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(handoff.get("evidence_boundary") or "")
    handoff_status_doc = (
        summary_fragment.get("handoff_status_detail")
        if isinstance(summary_fragment.get("handoff_status_detail"), dict)
        else summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else summary_fragment.get("status_summary")
        if isinstance(summary_fragment.get("status_summary"), dict)
        else {}
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or handoff.get("safe_copy")
        or handoff.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        # 下游可直接展示 safe_copy，所以固定补齐 false-state 边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    status_value = _redact_route_task_rehearsal_text(
        handoff_status_doc.get("status")
        or summary_fragment.get("handoff_status")
        or summary_fragment.get("status")
        or handoff.get("handoff_status")
        or handoff.get("status")
        or "blocked"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or handoff.get("overall_status")
        or "not_proven"
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or handoff.get("source")
        or handoff_status_doc.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or handoff.get("safe_evidence_ref")
        or handoff.get("evidence_ref", "")
    )
    safe_command_id = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_command_id")
        or summary_fragment.get("command_id")
        or handoff.get("safe_command_id")
        or handoff.get("command_id")
        or ""
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or handoff.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status_value,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_review_decision": _safe_pc_route_debug_value(
                summary_fragment.get("source_review_decision")
                if isinstance(summary_fragment.get("source_review_decision"), dict)
                else {}
            ),
            "handoff_status": status_value,
            "handoff_status_detail": {
                "status": status_value,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    handoff_status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or handoff.get("reason")
                    or "verified terminal result material review handoff is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "safe_command_id": safe_command_id,
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or handoff.get("terminal_result_type")
                or ""
            ),
            "material_status_summary": _safe_pc_route_debug_value(
                summary_fragment.get("material_status_summary")
                if isinstance(summary_fragment.get("material_status_summary"), dict)
                else {}
            ),
            "accepted_material_refs": (
                _verified_terminal_result_material_review_handoff_safe_list(
                    summary_fragment.get("accepted_material_refs")
                )
            ),
            "missing_required_materials": (
                _verified_terminal_result_material_review_handoff_safe_list(
                    summary_fragment.get("missing_required_materials")
                )
            ),
            "rejected_material_refs": (
                _verified_terminal_result_material_review_handoff_safe_list(
                    summary_fragment.get("rejected_material_refs")
                )
            ),
            "owner_handoff": _verified_terminal_result_material_review_handoff_safe_list(
                summary_fragment.get("owner_handoff")
            ),
            "next_required_evidence": (
                _verified_terminal_result_material_review_handoff_safe_list(
                    summary_fragment.get("next_required_evidence")
                )
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason") or handoff.get("blocked_reason") or ""
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status_value,
            },
            "not_proven": _verified_terminal_result_material_review_handoff_not_proven(
                handoff,
                summary_fragment,
            ),
            "read_error": "",
        }
    )
    if (
        source_schema != VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SCHEMA
        or source_boundary != VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "handoff_status": "blocked",
                "handoff_status_detail": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_handoff schema or evidence boundary is unsupported",
                },
                "source_review_decision": {},
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "material_status_summary": {},
                "accepted_material_refs": [],
                "missing_required_materials": [],
                "rejected_material_refs": [],
                "owner_handoff": [],
                "next_required_evidence": [],
            }
        )
        return summary
    if (
        raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_review_handoff_summary",
                "handoff_status": "blocked",
                "handoff_status_detail": {
                    "status": "blocked_missing_verified_terminal_result_material_review_handoff_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_handoff artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    # 合法 handoff 也只能是 read-only proof；任何成功/控制/raw 线索都固定转为 blocked。
    required_safe_metadata = (
        bool(summary_fragment),
        source_value == EVIDENCE_SOURCE_SOFTWARE,
        overall_status == "not_proven",
        status_value in VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_STATUSES,
        bool(summary["safe_evidence_ref"]),
        bool(summary["safe_command_id"]),
        bool(summary["terminal_result_type"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(handoff)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _verified_terminal_result_material_review_handoff_has_unsafe_controls(
            handoff
        )
        or _verified_terminal_result_material_review_handoff_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_review_handoff_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material review handoff was blocked because "
            "the summary did not remain source=software_proof/not_proven with "
            "delivery_success=false, primary_actions_enabled=false, "
            "safe_to_control=false, and no control, ACK/cursor, replay, resubmit, "
            "raw diagnostics, or robot-control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_review_handoff_summary",
                "handoff_status": "blocked",
                "handoff_status_detail": {
                    "status": "blocked_unsafe_verified_terminal_result_material_review_handoff_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_review_handoff contains unsafe fields, missing safe metadata, success wording, raw diagnostics, ACK/cursor/replay claims, or control claims",
                },
                "source_review_decision": {},
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "material_status_summary": {},
                "accepted_material_refs": [],
                "missing_required_materials": [],
                "rejected_material_refs": [],
                "owner_handoff": [],
                "next_required_evidence": [],
                "blocked_reason": blocked_copy,
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_followup_escalation_status_not_proven(
    followup=None, summary_fragment=None
):
    # follow-up escalation 只说明材料追办状态，不能被解释为 reviewer 已解决、送达成功或 HIL 通过。
    values = [
        "verified_terminal_result_material_followup_escalation_status_only",
        "followup_status_not_delivery_success",
        "reviewer_resolution_not_proven",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "replay_or_resubmit",
        "real_hil_pass",
    ]
    for container in (followup or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_followup_escalation_status_summary(
    path,
    followup_status="blocked_missing_terminal_result_review_handoff_not_proven",
    read_error="",
):
    # 缺 follow-up 输入时也返回完整 false flags，避免空状态被移动端或支持端误读成可控制。
    safe_copy = (
        "Verified terminal result material follow-up escalation status is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "verified_terminal_result_material_followup_escalation_status summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_followup_escalation_status",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "source_contract": {"schema": "", "evidence_boundary": "", "metadata_only": True},
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": followup_status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "source_handoff_status": "",
        "followup_status": followup_status,
        "followup_status_detail": {
            "status": followup_status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "assigned_owner": "",
        "support_owner": "",
        "reviewer_route": "",
        "required_material_backfill": [],
        "escalation_reason": "",
        "blocked_reason": read_error,
        "next_required_evidence": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
        },
        "not_proven": (
            _verified_terminal_result_material_followup_escalation_status_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
    }


def _verified_terminal_result_material_followup_escalation_status_source_contract(
    value,
):
    # source summary 和 Robot alias 都必须回指 follow-up artifact 与本轮 follow-up gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _verified_terminal_result_material_followup_escalation_status_summary_fragment(
    value,
):
    # 兼容 latest_status / diagnostics / status 嵌套，但只接受已经消毒的 summary 或 Robot alias。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get("verified_terminal_result_material_followup_escalation_status_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_followup_escalation_status_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
    value,
):
    # follow-up alias 必须比 handoff 更保守，reviewer resolution、raw artifact 和控制线索都整体拒绝。
    if _verified_terminal_result_material_review_handoff_has_unsafe_controls(value):
        return True
    unsafe_true_keys = {
        "reviewer_resolution",
        "reviewer_resolved",
        "resolved",
        "complete",
        "completed",
        "hil_pass",
        "field_pass",
        "delivery_complete",
    }
    unsafe_key_fragments = (
        "complete_json",
        "raw_artifact",
        "raw_source",
        "reviewer_resolution",
        "resolution_claim",
        "hardware",
        "device_path",
        "wave_rover",
        "uart",
        "serial",
        "credential",
        "secret",
        "token",
        "ack_cursor",
        "replay",
        "resubmit",
        "cmd_vel",
        "ros",
        "control",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
            ) and item is False:
                continue
            if key_text in unsafe_true_keys and bool(item):
                return True
            if any(fragment in key_text for fragment in unsafe_key_fragments):
                return True
            if _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        if any(
            marker in lowered
            for marker in (
                "reviewer resolved",
                "complete json",
                "raw artifact",
                "raw source",
                "hil pass",
                "delivery success",
            )
        ):
            return True
    return False


def _verified_terminal_result_material_followup_escalation_status_safe_list(value):
    # 列表字段只保留可读的追办/补证文本，过滤 raw、resolution、ACK/cursor 和控制语义。
    safe_items = []
    for item in _verified_terminal_result_material_review_handoff_safe_list(value):
        lowered = str(item or "").lower()
        if any(
            marker in lowered
            for marker in (
                "reviewer resolved",
                "resolution",
                "complete json",
                "raw artifact",
                "raw source",
                "ack",
                "cursor",
                "replay",
                "resubmit",
                "hardware",
                "uart",
                "wave rover",
                "control",
            )
        ):
            continue
        safe_items.append(item)
    return safe_items


def summarize_verified_terminal_result_material_followup_escalation_status(source):
    """构建 verified terminal result material follow-up escalation 的只读 Robot diagnostics 摘要。"""
    # Robot 只转发 Task A 已消毒的追办 summary；任何 raw/source sibling 都不能穿透到 diagnostics。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_verified_terminal_result_material_followup_escalation_status_summary(
            source_path,
            read_error=(
                "verified_terminal_result_material_followup_escalation_status summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        followup = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_followup_escalation_status summary artifact missing"
            )
            summary["followup_status_detail"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                followup = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                f"failed reading verified_terminal_result_material_followup_escalation_status summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status_detail"]["reason"] = safe_error
            return summary

    if not isinstance(followup, dict):
        summary["followup_status_detail"]["reason"] = (
            "verified_terminal_result_material_followup_escalation_status JSON must be an object"
        )
        return summary

    raw_schema = str(followup.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_followup_escalation_status_summary_fragment(
            followup
        )
    )
    contract_source = summary_fragment if summary_fragment else followup
    source_schema, source_boundary = (
        _verified_terminal_result_material_followup_escalation_status_source_contract(
            contract_source
        )
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(followup.get("evidence_boundary") or "")

    followup_status_doc = (
        summary_fragment.get("followup_status_detail")
        if isinstance(summary_fragment.get("followup_status_detail"), dict)
        else summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
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
        # safe_copy 是 UI 可展示文本，固定带上 false-state，避免后续复制时丢失证据边界。
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    status_value = _redact_route_task_rehearsal_text(
        followup_status_doc.get("status")
        or summary_fragment.get("followup_status")
        or summary_fragment.get("status")
        or followup.get("followup_status")
        or followup.get("status")
        or "blocked_missing_terminal_result_review_handoff_not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or followup.get("overall_status")
        or "not_proven"
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or followup.get("source")
        or followup_status_doc.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or followup.get("safe_evidence_ref")
        or followup.get("evidence_ref", "")
    )
    safe_command_id = _redact_route_task_rehearsal_text(
        summary_fragment.get("safe_command_id")
        or summary_fragment.get("command_id")
        or followup.get("safe_command_id")
        or followup.get("command_id")
        or ""
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
            "source_contract": {
                "schema": _redact_route_task_rehearsal_text(source_schema),
                "evidence_boundary": _redact_route_task_rehearsal_text(source_boundary),
                "metadata_only": True,
            },
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status_value,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_status")
                or followup.get("source_handoff_status")
                or ""
            ),
            "followup_status": status_value,
            "followup_status_detail": {
                "status": status_value,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    followup_status_doc.get("reason")
                    or summary_fragment.get("escalation_reason")
                    or followup.get("escalation_reason")
                    or "verified terminal result material follow-up escalation is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "safe_command_id": safe_command_id,
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or followup.get("terminal_result_type")
                or ""
            ),
            "assigned_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("assigned_owner")
                or followup.get("assigned_owner")
                or ""
            ),
            "support_owner": _redact_route_task_rehearsal_text(
                summary_fragment.get("support_owner")
                or followup.get("support_owner")
                or ""
            ),
            "reviewer_route": _redact_route_task_rehearsal_text(
                summary_fragment.get("reviewer_route")
                or followup.get("reviewer_route")
                or ""
            ),
            "required_material_backfill": (
                _verified_terminal_result_material_followup_escalation_status_safe_list(
                    summary_fragment.get("required_material_backfill")
                )
            ),
            "escalation_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("escalation_reason")
                or followup.get("escalation_reason")
                or ""
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason") or followup.get("blocked_reason") or ""
            ),
            "next_required_evidence": (
                _verified_terminal_result_material_followup_escalation_status_safe_list(
                    summary_fragment.get("next_required_evidence")
                )
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {
                "safe_copy": safe_copy_text,
                "safe_phone_copy": safe_copy_text,
                "status": status_value,
            },
            "not_proven": (
                _verified_terminal_result_material_followup_escalation_status_not_proven(
                    followup,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    if (
        source_schema != VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        or source_boundary
        != VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE
    ):
        summary.update(
            {
                "status": "unsupported_schema",
                "followup_status": "blocked_missing_terminal_result_review_handoff_not_proven",
                "followup_status_detail": {
                    "status": "unsupported_schema",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_followup_escalation_status schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "required_material_backfill": [],
                "next_required_evidence": [],
            }
        )
        return summary
    if (
        raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_followup_escalation_status_summary",
                "followup_status": "blocked_missing_terminal_result_review_handoff_not_proven",
                "followup_status_detail": {
                    "status": "blocked_missing_verified_terminal_result_material_followup_escalation_status_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_followup_escalation_status artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    # 合法 follow-up 也只能是追办软件证明；任何完成、resolution 或控制语义都必须 fail closed。
    required_safe_metadata = (
        bool(summary_fragment),
        source_value == EVIDENCE_SOURCE_SOFTWARE,
        overall_status == "not_proven",
        status_value
        in VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_STATUSES,
        bool(summary["safe_evidence_ref"]),
        bool(summary["safe_command_id"]),
        bool(summary["terminal_result_type"]),
        bool(summary["source_handoff_status"]),
        bool(summary["assigned_owner"]),
        bool(summary["support_owner"]),
        bool(summary["reviewer_route"]),
        bool(summary["required_material_backfill"]),
        bool(summary["next_required_evidence"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _route_task_field_run_readiness_has_unsafe_fields(followup)
        or _route_task_field_run_readiness_has_unsafe_fields(summary_fragment)
        or _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
            followup
        )
        or _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_followup_escalation_status_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material follow-up escalation status was blocked "
            "because the summary did not remain source=software_proof/not_proven "
            "with delivery_success=false, primary_actions_enabled=false, "
            "safe_to_control=false, and no raw source, raw artifact, complete JSON, "
            "reviewer-resolution, ACK/cursor, replay, resubmit, hardware, ROS, "
            "or robot-control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_followup_escalation_status_summary",
                "followup_status": "rejected_unsafe_terminal_result_followup_not_proven",
                "followup_status_detail": {
                    "status": "blocked_unsafe_verified_terminal_result_material_followup_escalation_status_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_followup_escalation_status contains unsafe fields, missing safe metadata, success wording, reviewer-resolution, raw artifacts, ACK/cursor/replay claims, hardware details, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "required_material_backfill": [],
                "next_required_evidence": [],
                "blocked_reason": blocked_copy,
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "rejected_unsafe_terminal_result_followup_not_proven",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_intake_not_proven(
    response=None,
    summary_fragment=None,
):
    # owner response intake 只证明安全材料进入后续复核队列，不代表 PR #5 关闭或终态送达成立。
    values = [
        "verified_terminal_result_material_owner_response_intake_only",
        "owner_response_material_not_reviewer_resolution",
        "owner_response_material_not_delivery_success",
        "accepted_materials_for_later_review_only",
        "pr5_PRRT_kwDOSWB9286CJ3tX_unresolved",
        "hardware_material_pending",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "collect_dropoff_cancel_control",
        "real_hil_pass",
    ]
    for container in (response or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for item in container.get("not_proven", []):
            safe_item = _redact_route_task_rehearsal_text(item)
            lowered = safe_item.lower()
            # raw/path/checksum/HIL pass 线索只用于阻断，不暴露到 Robot-safe not_proven 列表。
            if any(
                marker in lowered
                for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
            ):
                continue
            if safe_item and safe_item not in values:
                values.append(safe_item)
        for item in container.get("next_required_evidence", []):
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_intake_summary(
    path,
    status="blocked_missing_terminal_result_followup_not_proven",
    read_error="",
):
    # 默认值也显式保持三类 false flag，防止缺材料时被 UI 解释成可继续控制。
    safe_copy = (
        "Verified terminal result material owner response intake is metadata-only; "
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_intake summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_intake",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "owner_response_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "source_followup_status": "",
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "next_required_evidence": [],
        "operator_support_handoff": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "status": status,
        },
        "not_proven": _verified_terminal_result_material_owner_response_intake_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "pr5_review_thread_resolved": False,
        "okr_percentage_lift": False,
    }


def _verified_terminal_result_material_owner_response_intake_source_contract(value):
    # source summary 和 Robot alias 都必须回指 owner-response intake artifact 与本轮 intake gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _verified_terminal_result_material_owner_response_intake_summary_fragment(value):
    # 只接受 Task A 已消毒 summary 或 Robot alias；raw owner-response artifact 不能直接展示。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get("verified_terminal_result_material_owner_response_intake_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_intake_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
    value,
):
    # 新 alias 允许 safe_command_id 等安全字段，但 raw/control/PR resolved 线索仍必须阻断。
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
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
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
        "safe_evidence_ref",
        "evidence_ref",
        "safe_command_id",
        "command_id",
        "terminal_result_type",
        "status",
        "overall_status",
        "owner_response_status",
        "source_followup_status",
        "status_summary",
        "verdict",
        "reason",
        "evidence_source",
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
        "verified_terminal_result_material_owner_response_intake_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary",
        "diagnostics",
        "status",
        "latest_status",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
            ) and item is False:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "pr5_review_thread_resolved",
                "owner_material_real_acceptance",
                "collect_triggered",
                "dropoff_triggered",
                "cancel_triggered",
                "ack_post_allowed",
                "cursor_updates_allowed",
                "robot_control_allowed",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "reviewer resolved",
                "thread resolved",
                "pr resolved",
                "delivery success",
                "control enabled",
                "start delivery",
                "confirm dropoff",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_intake(source):
    """构建 verified terminal result material owner-response intake 的只读 Robot diagnostics 摘要。"""
    # accepted 也只表示进入 later review queue，不能启用 collect/dropoff/cancel、ACK/cursor 或 OKR 提升。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_owner_response_intake_summary(
        source_path,
        read_error=(
            "verified_terminal_result_material_owner_response_intake summary is not configured"
        ),
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_intake summary artifact missing"
            )
            summary["owner_response_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["owner_response_status"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["owner_response_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_intake JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_intake_summary_fragment(
            response
        )
    )
    contract_source = summary_fragment if summary_fragment else response
    source_schema, source_boundary = (
        _verified_terminal_result_material_owner_response_intake_source_contract(
            contract_source
        )
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

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
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or response.get("safe_copy")
        or response.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("owner_response_status")
        or summary_fragment.get("status")
        or response.get("status")
        or "blocked_missing_terminal_result_followup_not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or response.get("overall_status")
        or "not_proven"
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or response.get("source")
        or status_doc.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or response.get("safe_evidence_ref")
        or response.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or response.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "owner_response_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response intake is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "source_followup_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_followup_status")
                or summary_fragment.get("source_followup_status_summary")
                or response.get("source_followup_status")
                or ""
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
                _verified_terminal_result_material_owner_response_intake_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    if (
        source_schema != VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA
        or source_boundary
        != VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_GATE
    ):
        summary.update(
            {
                "status": "blocked_unsupported_verified_terminal_result_material_owner_response_intake",
                "owner_response_status": {
                    "status": "blocked_unsupported_verified_terminal_result_material_owner_response_intake",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_intake schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
            }
        )
        return summary
    if (
        raw_schema == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_owner_response_intake_summary",
                "owner_response_status": {
                    "status": "blocked_missing_verified_terminal_result_material_owner_response_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_intake artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    required_safe_metadata = (
        bool(summary_fragment),
        source_value == EVIDENCE_SOURCE_SOFTWARE,
        overall_status == "not_proven",
        status in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_STATUSES,
        bool(summary["safe_evidence_ref"]),
        bool(summary["safe_command_id"]),
        bool(summary["terminal_result_type"]),
        bool(summary["next_required_evidence"]),
        bool(summary["operator_support_handoff"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_intake_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response intake was blocked "
            "because the summary did not remain source=software_proof/not_proven "
            "with safe_to_control=false, delivery_success=false, "
            "primary_actions_enabled=false, PR #5 PRRT_kwDOSWB9286CJ3tX unresolved, "
            "and no raw artifact, reviewer-resolution, ACK/cursor, collect/dropoff/"
            "cancel, hardware, ROS, or robot-control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_intake_summary",
                "owner_response_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_intake contains unsafe fields, missing safe metadata, success wording, reviewer-resolution, ACK/cursor, collect/dropoff/cancel, hardware details, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "next_required_evidence": [],
                "operator_support_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_review_decision_not_proven(
    response=None,
    summary_fragment=None,
):
    # review decision 只证明 owner response 可被下一步交接消费，不代表送达或控制闭环成立。
    values = [
        "verified_terminal_result_material_owner_response_review_decision_only",
        "owner_response_review_decision_not_delivery_success",
        "accepted_for_next_handoff_not_robot_control",
        "accepted_materials_for_handoff_only",
        "real_delivery_result",
        "dropoff_completion",
        "cancel_completion",
        "delivery_success",
        "robot_control_authorization",
        "ACK_mutation",
        "cursor_mutation",
        "collect_dropoff_cancel_control",
        "real_hil_pass",
    ]
    for container in (response or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for key in ("not_proven", "next_required_evidence"):
            for item in container.get(key, []):
                safe_item = _redact_route_task_rehearsal_text(item)
                lowered = safe_item.lower()
                # 诊断 alias 不回显 raw/path/checksum/HIL pass 字样，避免被下游当成真实材料。
                if any(
                    marker in lowered
                    for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
                ):
                    continue
                if safe_item and safe_item not in values:
                    values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_review_decision_summary(
    path,
    status="blocked_missing_terminal_result_owner_response_intake_not_proven",
    read_error="",
):
    # 默认缺省状态也显式写入三个 false flag，防止 UI 把缺材料误当作可控制。
    safe_copy = (
        "Verified terminal result material owner response review decision is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_review_decision summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_review_decision",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE,
        "source_schema": "",
        "source_schema_version": None,
        "source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "review_decision": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "source_owner_response_status": "",
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {
            "safe_copy": safe_copy,
            "safe_phone_copy": safe_copy,
            "status": status,
        },
        "not_proven": _verified_terminal_result_material_owner_response_review_decision_not_proven(),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "owner_response_material_accepted": False,
        "handoff_authorized": False,
    }


def _verified_terminal_result_material_owner_response_review_decision_source_contract(
    value,
):
    # source summary 和 Robot alias 必须回指本轮 review-decision artifact 与 gate。
    value = value if isinstance(value, dict) else {}
    source_schema = str(value.get("schema") or "")
    source_boundary = str(value.get("evidence_boundary") or "")
    if source_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            value.get("source_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(value.get("source_evidence_boundary") or source_boundary)
    return source_schema, source_boundary


def _verified_terminal_result_material_owner_response_review_decision_summary_fragment(
    value,
):
    # raw artifact 只有包含已消毒 summary 时才可进入 Robot diagnostics。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get("verified_terminal_result_material_owner_response_review_decision_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_review_decision_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
    value,
):
    # 允许 safe_command_id / owner_handoff 等字段；真实控制、raw、ACK/cursor 和硬件线索一律阻断。
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
        "cmd_vel",
        "serial",
        "uart",
        "baud",
        "wave_rover",
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
        "safe_evidence_ref",
        "evidence_ref",
        "safe_command_id",
        "command_id",
        "terminal_result_type",
        "status",
        "overall_status",
        "review_decision",
        "owner_response_review_decision",
        "review_status",
        "source_owner_response_status",
        "status_summary",
        "verdict",
        "reason",
        "evidence_source",
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
        "owner_handoff",
        "operator_support_handoff",
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
        "verified_terminal_result_material_owner_response_review_decision_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary",
        "diagnostics",
        "status",
        "latest_status",
        "summary",
        "diagnostics_summary",
    }
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text not in safe_keys and any(
                fragment in key_text for fragment in unsafe_key_fragments
            ):
                return True
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
            ) and item is False:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "owner_response_material_accepted",
                "handoff_authorized",
                "collect_triggered",
                "dropoff_triggered",
                "cancel_triggered",
                "ack_post_allowed",
                "cursor_updates_allowed",
                "robot_control_allowed",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        if "delivery_success=false" in lowered and "safe_to_control=false" in lowered:
            return False
        return any(
            marker in lowered
            for marker in (
                "reviewer resolved",
                "thread resolved",
                "delivery success",
                "control enabled",
                "start delivery",
                "confirm dropoff",
                "handoff authorized",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_review_decision(source):
    """构建 owner-response review-decision 的只读 Robot diagnostics 摘要。"""
    # accepted_for_next_handoff 只是交接材料状态，不允许下游启用主动作或控制链路。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_owner_response_review_decision_summary(
        source_path,
        read_error=(
            "verified_terminal_result_material_owner_response_review_decision summary is not configured"
        ),
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_review_decision summary artifact missing"
            )
            summary["review_decision"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_decision"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["review_decision"]["reason"] = (
            "verified_terminal_result_material_owner_response_review_decision JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_review_decision_summary_fragment(
            response
        )
    )
    contract_source = summary_fragment if summary_fragment else response
    source_schema, source_boundary = (
        _verified_terminal_result_material_owner_response_review_decision_source_contract(
            contract_source
        )
    )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    status_doc = (
        summary_fragment.get("review_decision")
        if isinstance(summary_fragment.get("review_decision"), dict)
        else summary_fragment.get("owner_response_review_decision")
        if isinstance(summary_fragment.get("owner_response_review_decision"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
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
        or response.get("safe_copy")
        or response.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = (
            f"{safe_copy_text}; source=software_proof; not_proven; "
            "safe_to_control=false; delivery_success=false; "
            "primary_actions_enabled=false."
        )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("status")
        or response.get("status")
        or "blocked_missing_terminal_result_owner_response_intake_not_proven"
    )
    overall_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("overall_status")
        or response.get("overall_status")
        or "not_proven"
    )
    source_value = _redact_route_task_rehearsal_text(
        summary_fragment.get("source")
        or response.get("source")
        or status_doc.get("evidence_source")
        or ""
    )
    safe_evidence_ref = _safe_route_task_rehearsal_ref(
        summary_fragment.get("safe_evidence_ref")
        or summary_fragment.get("evidence_ref")
        or response.get("safe_evidence_ref")
        or response.get("evidence_ref", "")
    )
    summary.update(
        {
            "source_schema": _redact_route_task_rehearsal_text(source_schema),
            "source_schema_version": (
                summary_fragment.get("source_schema_version")
                or summary_fragment.get("schema_version")
                or response.get("schema_version")
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "review_decision": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response review decision is software_proof only"
                ),
            },
            "safe_evidence_ref": safe_evidence_ref,
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
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
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
                or summary_fragment.get("operator_support_handoff")
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
                _verified_terminal_result_material_owner_response_review_decision_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )
    if (
        source_schema
        != VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        or source_boundary
        != VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE
    ):
        summary.update(
            {
                "status": "blocked_unsupported_verified_terminal_result_material_owner_response_review_decision",
                "review_decision": {
                    "status": "blocked_unsupported_verified_terminal_result_material_owner_response_review_decision",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_review_decision schema or evidence boundary is unsupported",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
            }
        )
        return summary
    if (
        raw_schema
        == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        and not summary_fragment
    ):
        summary.update(
            {
                "status": "blocked_missing_verified_terminal_result_material_owner_response_review_decision_summary",
                "review_decision": {
                    "status": "blocked_missing_verified_terminal_result_material_owner_response_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_review_decision artifact is missing sanitized summary",
                },
                "safe_evidence_ref": "",
            }
        )
        return summary

    required_safe_metadata = (
        bool(summary_fragment),
        source_value == EVIDENCE_SOURCE_SOFTWARE,
        overall_status == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_STATUSES,
        bool(summary["safe_evidence_ref"]),
        bool(summary["safe_command_id"]),
        bool(summary["terminal_result_type"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or summary_fragment.get("delivery_success") is not False
        or summary_fragment.get("primary_actions_enabled") is not False
        or summary_fragment.get("safe_to_control") is not False
        or _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response review decision was "
            "blocked because the summary did not remain source=software_proof/"
            "not_proven with safe_to_control=false, delivery_success=false, "
            "primary_actions_enabled=false, and no raw artifact, ACK/cursor, "
            "collect/dropoff/cancel, handoff-authorization, hardware, ROS, or "
            "robot-control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_review_decision_summary",
                "review_decision": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_review_decision contains unsafe fields, missing safe metadata, success wording, ACK/cursor, collect/dropoff/cancel, handoff authorization, hardware details, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_review_handoff_not_proven(
    handoff=None, summary_fragment=None
):
    # handoff 只是给 owner/support/reviewer 的安全交接包，不代表 PR #5 或真实送达已解决。
    values = [
        "verified_terminal_result_material_owner_response_review_handoff_only",
        "source_decision_not_delivery_success",
        "PRRT_kwDOSWB9286CJ3tX_unresolved",
        "hardware_material_pending",
        "real_terminal_result",
        "delivery_success",
        "robot_control_authorization",
        "route_or_elevator_field_pass",
        "real_hil_pass",
        "wave_rover_or_uart_proof",
        "public_ingress_or_tls_proof",
        "production_db_queue_proof",
    ]
    for container in (handoff or {}, summary_fragment or {}):
        for item in container.get("not_proven", []) if isinstance(container, dict) else []:
            safe_item = _redact_route_task_rehearsal_text(item)
            if safe_item and safe_item not in values:
                values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_review_handoff_summary(
    path,
    status="blocked_missing_verified_terminal_result_material_owner_response_review_decision_not_proven",
    read_error="",
):
    # 缺输入时也返回完整 false flags，避免移动端把空对象误读成可交付或可控制。
    safe_copy = (
        "Verified terminal result material owner response review handoff is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; PR #5 PRRT_kwDOSWB9286CJ3tX remains "
        "unresolved and hardware_material_pending."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_review_handoff summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_review_handoff",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
        "source_schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA,
        "source_schema_version": None,
        "source_evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
        "upstream_source_schema": "",
        "upstream_source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "review_decision": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "source_review_decision_status": "",
        "source_owner_response_status": "",
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "operator_support_handoff": [],
        "reviewer_route": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "not_proven": (
            _verified_terminal_result_material_owner_response_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "owner_response_material_accepted": False,
        "handoff_authorized": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _verified_terminal_result_material_owner_response_review_handoff_summary_fragment(
    value,
):
    # 优先接受 handoff summary；没有 handoff 时允许从上游 review-decision safe summary 派生。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get("verified_terminal_result_material_owner_response_review_handoff_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary"
        ),
        value.get("verified_terminal_result_material_owner_response_review_decision_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_review_handoff_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
    value,
):
    # 复用上游 review-decision 的 raw/控制拦截，再额外拒绝 resolved/success/production 语义。
    if _verified_terminal_result_material_owner_response_review_decision_has_unsafe_controls(
        value
    ):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
                "pr5_resolved",
            ) and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "pr5_resolved",
                "delivery_complete",
                "production_ready",
                "hil_pass",
                "field_pass",
                "handoff_authorized",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "pr #5 resolved",
                "prrt_kwdoswb9286cj3tx resolved",
                "reviewer resolved",
                "delivery success",
                "production ready",
                "public https",
                "tls proof",
                "4g/sim proof",
                "oss/cdn live",
                "hil pass",
                "wave rover proof",
                "uart proof",
                "route field pass",
                "elevator field pass",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_review_handoff(source):
    """从 owner-response review-decision 安全摘要派生只读 handoff Robot alias。"""
    # 派生逻辑只读取 safe summary；raw artifact、真实控制和硬件字段会被阻断。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = _default_verified_terminal_result_material_owner_response_review_handoff_summary(
        source_path,
        read_error=(
            "verified_terminal_result_material_owner_response_review_handoff summary is not configured"
        ),
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_review_handoff summary artifact missing"
            )
            summary["review_decision"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_review_handoff "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["review_decision"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["review_decision"]["reason"] = (
            "verified_terminal_result_material_owner_response_review_handoff JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_review_handoff_summary_fragment(
            response
        )
    )
    if not summary_fragment:
        summary["status"] = (
            "blocked_missing_verified_terminal_result_material_owner_response_review_handoff_summary"
        )
        summary["review_decision"]["status"] = summary["status"]
        summary["review_decision"]["reason"] = (
            "verified_terminal_result_material_owner_response_review_handoff input is missing sanitized summary"
        )
        return summary

    # raw handoff wrapper 可携带 decision safe summary；真正 raw-only 输入仍会因没有 summary fail closed。
    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema, source_boundary = (
        _verified_terminal_result_material_owner_response_review_decision_source_contract(
            summary_fragment
        )
    )
    if fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        source_schema = str(
            summary_fragment.get("upstream_source_schema")
            or summary_fragment.get("decision_source_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA
        )
        source_boundary = str(
            summary_fragment.get("upstream_source_evidence_boundary")
            or summary_fragment.get("decision_source_evidence_boundary")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE
        )
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    status_doc = (
        summary_fragment.get("review_decision")
        if isinstance(summary_fragment.get("review_decision"), dict)
        else summary_fragment.get("owner_response_review_decision")
        if isinstance(summary_fragment.get("owner_response_review_decision"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    status = _redact_route_task_rehearsal_text(
        status_doc.get("status")
        or summary_fragment.get("source_review_decision_status")
        or summary_fragment.get("status")
        or "blocked_missing_terminal_result_owner_response_intake_not_proven"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "PR #5 PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending."
    )
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    if "PRRT_kwDOSWB9286CJ3tX" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "upstream_source_schema": _redact_route_task_rehearsal_text(source_schema),
            "upstream_source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "review_decision": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    status_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response review handoff is software_proof only"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref", "")
            ),
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "source_review_decision_status": status,
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
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
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "operator_support_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_routing")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy_text, "status": status},
            "not_proven": (
                _verified_terminal_result_material_owner_response_review_handoff_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        source_schema
        == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA,
        source_boundary
        == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE,
        summary_fragment.get("source") == EVIDENCE_SOURCE_SOFTWARE,
        summary_fragment.get("overall_status") == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_STATUSES,
        bool(summary["safe_evidence_ref"]),
        bool(summary["safe_command_id"]),
        bool(summary["terminal_result_type"]),
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
    )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response review handoff was "
            "blocked because the summary did not remain source=software_proof/"
            "not_proven with safe_to_control=false, delivery_success=false, "
            "primary_actions_enabled=false, PR #5 PRRT_kwDOSWB9286CJ3tX unresolved, "
            "hardware_material_pending, and no raw artifact, credentials, paths, "
            "ROS command topics, ACK/cursor, collect/dropoff/cancel, handoff "
            "authorization, hardware, WAVE ROVER/UART, success, or control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_review_handoff_summary",
                "review_decision": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_review_handoff_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_review_handoff contains unsafe fields, missing safe metadata, success wording, hardware details, PR-resolution claims, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "operator_support_handoff": [],
                "reviewer_route": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_reviewer_ack_intake_not_proven(
    ack=None,
    summary_fragment=None,
):
    # reviewer ACK intake 只证明 ACK 材料进入安全诊断面，不代表 PR #5、真实送达或控制闭环完成。
    values = [
        "verified_terminal_result_material_owner_response_reviewer_ack_intake_only",
        "source_handoff_not_delivery_success",
        "reviewer_ack_intake_not_pr5_resolution",
        "reviewer_ack_intake_not_robot_control_authorization",
        "PRRT_kwDOSWB9286CJ3tX_unresolved",
        "hardware_material_pending",
        "real_terminal_result",
        "delivery_success",
        "robot_control_authorization",
        "route_or_elevator_field_pass",
        "real_hil_pass",
        "wave_rover_or_uart_proof",
        "public_ingress_or_tls_proof",
        "production_db_queue_proof",
    ]
    for container in (ack or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for key in ("not_proven", "next_required_evidence"):
            for item in container.get(key, []):
                safe_item = _redact_route_task_rehearsal_text(item)
                lowered = safe_item.lower()
                # raw/path/checksum/HIL pass 字样只用于阻断，不进入 Robot-safe 输出。
                if any(
                    marker in lowered
                    for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
                ):
                    continue
                if safe_item and safe_item not in values:
                    values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary(
    path,
    status="blocked_missing_verified_terminal_result_material_owner_response_review_handoff_not_proven",
    read_error="",
):
    # 缺 ACK 材料时仍返回完整 false flags，避免手机或 Robot 面把空摘要误读为可控。
    safe_copy = (
        "Verified terminal result material owner response reviewer ACK intake is "
        "metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; PR #5 PRRT_kwDOSWB9286CJ3tX remains "
        "unresolved and hardware_material_pending."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_reviewer_ack_intake summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_reviewer_ack_intake",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        "source_schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
        "source_schema_version": None,
        "source_evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        "upstream_source_schema": "",
        "upstream_source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "reviewer_ack_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "source_handoff_status": "",
        "source_review_decision_status": "",
        "source_owner_response_status": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "ack_reasons": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "next_required_evidence": [],
        "owner_handoff": [],
        "operator_support_handoff": [],
        "reviewer_route": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "not_proven": (
            _verified_terminal_result_material_owner_response_reviewer_ack_intake_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "owner_response_material_accepted": False,
        "handoff_authorized": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _verified_terminal_result_material_owner_response_reviewer_ack_intake_summary_fragment(
    value,
):
    # 先消费同名 summary / Robot alias；只在没有 ACK summary 时允许从上游 handoff safe summary 派生 blocked 状态。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
        ),
        value.get("verified_terminal_result_material_owner_response_review_handoff_summary"),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_reviewer_ack_intake_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
    value,
):
    # ACK intake 继承 handoff 的原始材料/硬件/成功语义阻断，并额外拒绝 reviewer resolved 文案。
    if _verified_terminal_result_material_owner_response_review_handoff_has_unsafe_controls(
        value
    ):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
                "pr5_resolved",
            ) and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "pr5_resolved",
                "delivery_complete",
                "production_ready",
                "hil_pass",
                "field_pass",
                "handoff_authorized",
                "ack_mutation_enabled",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "pr #5 resolved",
                "prrt_kwdoswb9286cj3tx resolved",
                "reviewer resolved",
                "thread resolved",
                "delivery success",
                "production ready",
                "public https",
                "tls proof",
                "4g/sim proof",
                "oss/cdn live",
                "hil pass",
                "wave rover proof",
                "uart proof",
                "route field pass",
                "elevator field pass",
                "control enabled",
                "start delivery",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_reviewer_ack_intake(source):
    """构建 owner-response reviewer ACK intake 的只读 Robot diagnostics 摘要。"""
    # 该 alias 只读取 safe summary；raw ACK、真实控制和硬件细节会 fail closed。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary(
            source_path,
            read_error=(
                "verified_terminal_result_material_owner_response_reviewer_ack_intake summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_reviewer_ack_intake summary artifact missing"
            )
            summary["reviewer_ack_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_reviewer_ack_intake "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reviewer_ack_status"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["reviewer_ack_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_intake JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_reviewer_ack_intake_summary_fragment(
            response
        )
    )
    if not summary_fragment:
        summary["status"] = (
            "blocked_missing_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
        )
        summary["reviewer_ack_status"]["status"] = summary["status"]
        summary["reviewer_ack_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_intake input is missing sanitized summary"
        )
        return summary

    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema = str(summary_fragment.get("source_schema") or "")
    source_boundary = str(summary_fragment.get("source_evidence_boundary") or "")
    if fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    ):
        source_schema = source_schema or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
        source_boundary = source_boundary or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
    else:
        source_schema = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA
        source_boundary = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    ack_doc = (
        summary_fragment.get("reviewer_ack_status")
        if isinstance(summary_fragment.get("reviewer_ack_status"), dict)
        else summary_fragment.get("ack_status")
        if isinstance(summary_fragment.get("ack_status"), dict)
        else summary_fragment.get("review_status")
        if isinstance(summary_fragment.get("review_status"), dict)
        else {}
    )
    handoff_input = (
        fragment_schema
        in (
            VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
            VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        )
    )
    ack_status_value = (
        summary_fragment.get("reviewer_ack_status")
        if isinstance(summary_fragment.get("reviewer_ack_status"), str)
        else ""
    )
    status = _redact_route_task_rehearsal_text(
        "blocked_missing_handoff_not_proven"
        if handoff_input
        else ack_doc.get("status")
        or ack_status_value
        or summary_fragment.get("status")
        or "blocked_missing_verified_terminal_result_material_owner_response_review_handoff_not_proven"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "PR #5 PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending."
    )
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    if "PRRT_kwDOSWB9286CJ3tX" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
            ),
            "upstream_source_schema": _redact_route_task_rehearsal_text(source_schema),
            "upstream_source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "reviewer_ack_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    ack_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response reviewer ACK intake is software_proof only"
                ),
            },
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref", "")
            ),
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "source_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_status")
                or summary_fragment.get("source_review_handoff_status")
                or summary_fragment.get("status")
                or ""
            ),
            "source_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision_status")
                or response.get("source_review_decision_status")
                or ""
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by")
                or summary_fragment.get("reviewer")
                or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at") or ""
            ),
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                or summary_fragment.get("accepted_materials")
                or summary_fragment.get("accepted")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                or summary_fragment.get("missing_materials")
                or summary_fragment.get("missing")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                or summary_fragment.get("rejected_materials")
                or summary_fragment.get("rejected")
            ),
            "unsafe_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials_summary")
                or summary_fragment.get("unsafe_materials")
                or summary_fragment.get("unsafe")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "operator_support_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_routing")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy_text, "status": status},
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "not_proven": (
                _verified_terminal_result_material_owner_response_reviewer_ack_intake_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )

    source_is_ack_summary = fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    )
    required_safe_metadata = (
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["overall_status"] == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
        bool(summary["operator_support_handoff"]),
        bool(summary["reviewer_route"]),
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
    )
    if source_is_ack_summary:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
            bool(summary["safe_evidence_ref"]),
            bool(summary["safe_command_id"]),
            bool(summary["source_handoff_status"]),
        )
    else:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
        )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response reviewer ACK intake "
            "was blocked because the summary did not remain source=software_proof/"
            "not_proven with safe_to_control=false, delivery_success=false, "
            "primary_actions_enabled=false, PR #5 PRRT_kwDOSWB9286CJ3tX unresolved, "
            "hardware_material_pending, and no raw artifact, credentials, paths, "
            "ROS command topics, ACK/cursor mutation, collect/dropoff/cancel, "
            "handoff authorization, hardware, WAVE ROVER/UART, success, resolved, "
            "or control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
                "reviewer_ack_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_reviewer_ack_intake contains unsafe fields, missing safe metadata, success wording, hardware details, PR-resolution claims, or control claims",
                },
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "acknowledged_by": "",
                "acknowledged_at": "",
                "ack_reasons": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "next_required_evidence": [],
                "owner_handoff": [],
                "operator_support_handoff": [],
                "reviewer_route": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_not_proven(
    decision=None,
    summary_fragment=None,
):
    # review decision 只证明 reviewer ACK 被安全复核，不代表 PR #5、HIL 或真实送达闭环完成。
    values = [
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision_only",
        "source_reviewer_ack_intake_not_delivery_success",
        "review_decision_not_pr5_resolution",
        "review_decision_not_robot_control_authorization",
        "PRRT_kwDOSWB9286CJ3tX_unresolved",
        "hardware_material_pending",
        "real_terminal_result",
        "delivery_success",
        "robot_control_authorization",
        "route_or_elevator_field_pass",
        "real_hil_pass",
        "wave_rover_or_uart_proof",
        "public_ingress_or_tls_proof",
        "production_db_queue_proof",
    ]
    for container in (decision or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for key in ("not_proven", "next_required_evidence"):
            for item in container.get(key, []):
                safe_item = _redact_route_task_rehearsal_text(item)
                lowered = safe_item.lower()
                # raw/path/checksum/HIL pass 字样只用于阻断，不能进入 Robot-safe 输出。
                if any(
                    marker in lowered
                    for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
                ):
                    continue
                if safe_item and safe_item not in values:
                    values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary(
    path,
    status="blocked_missing_source_intake_not_proven",
    read_error="",
):
    # 缺 review decision 时仍返回完整 false flags，避免下游把空状态当作可控复核结果。
    safe_copy = (
        "Verified terminal result material owner response reviewer ACK review "
        "decision is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; PR #5 PRRT_kwDOSWB9286CJ3tX remains "
        "unresolved and hardware_material_pending."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_reviewer_ack_review_decision",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
        "source_schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
        "source_schema_version": None,
        "source_evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
        "upstream_source_schema": "",
        "upstream_source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "reviewer_ack_review_decision": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_intake_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "source_handoff_status": "",
        "source_review_decision_status": "",
        "source_owner_response_status": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "decision_reasons": [],
        "ack_reasons": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "reassignment_reason": "",
        "next_required_evidence": [],
        "owner_handoff": [],
        "operator_support_handoff": [],
        "reviewer_route": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "not_proven": (
            _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "owner_response_material_accepted": False,
        "handoff_authorized": False,
        "review_decision_authorized": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
    }


def _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary_fragment(
    value,
):
    # 优先消费本 rung 的 sanitized summary；没有时只允许从 reviewer ACK intake safe summary 派生 blocked 状态。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary"
        ),
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
    value,
):
    # 继承 reviewer ACK intake 的阻断条件，再额外拒绝 review/PR/HIL 成功或授权语义。
    if _verified_terminal_result_material_owner_response_reviewer_ack_intake_has_unsafe_controls(
        value
    ):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
                "pr5_resolved",
                "review_decision_authorized",
            ) and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "review_decision_authorized",
                "pr5_resolved",
                "delivery_complete",
                "production_ready",
                "hil_pass",
                "field_pass",
                "handoff_authorized",
                "ack_mutation_enabled",
                "control_authorized",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "pr #5 resolved",
                "prrt_kwdoswb9286cj3tx resolved",
                "reviewer resolved",
                "thread resolved",
                "review authorized",
                "delivery success",
                "production ready",
                "public https",
                "tls proof",
                "4g/sim proof",
                "oss/cdn live",
                "hil pass",
                "hil_pass",
                "wave rover proof",
                "uart proof",
                "route field pass",
                "elevator field pass",
                "control enabled",
                "start delivery",
                "complete artifact",
                "complete_json",
                "checksum",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_decision(
    source,
):
    """构建 owner-response reviewer ACK review decision 的只读 Robot diagnostics 摘要。"""
    # 该 alias 只读 safe summary；review decision 不能变成 ACK/cursor、GitHub 或机器人控制语义。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary(
            source_path,
            read_error=(
                "verified_terminal_result_material_owner_response_reviewer_ack_review_decision summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_reviewer_ack_review_decision summary artifact missing"
            )
            summary["reviewer_ack_review_decision"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_reviewer_ack_review_decision "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["reviewer_ack_review_decision"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["reviewer_ack_review_decision"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_review_decision JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary_fragment(
            response
        )
    )
    if not summary_fragment:
        summary["status"] = (
            "blocked_missing_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary"
        )
        summary["reviewer_ack_review_decision"]["status"] = summary["status"]
        summary["reviewer_ack_review_decision"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_review_decision input is missing sanitized summary"
        )
        return summary

    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema = str(summary_fragment.get("source_schema") or "")
    source_boundary = str(summary_fragment.get("source_evidence_boundary") or "")
    if fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        source_schema = (
            source_schema
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        )
        source_boundary = (
            source_boundary
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        )
    else:
        source_schema = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA
        source_boundary = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    decision_doc = (
        summary_fragment.get("reviewer_ack_review_decision")
        if isinstance(summary_fragment.get("reviewer_ack_review_decision"), dict)
        else summary_fragment.get("review_decision")
        if isinstance(summary_fragment.get("review_decision"), dict)
        else summary_fragment.get("decision")
        if isinstance(summary_fragment.get("decision"), dict)
        else {}
    )
    intake_input = fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    )
    decision_status_value = (
        summary_fragment.get("reviewer_ack_review_decision")
        if isinstance(summary_fragment.get("reviewer_ack_review_decision"), str)
        else summary_fragment.get("review_decision_status")
        if isinstance(summary_fragment.get("review_decision_status"), str)
        else ""
    )
    status = _redact_route_task_rehearsal_text(
        "blocked_missing_source_intake_not_proven"
        if intake_input
        else decision_doc.get("status")
        or decision_status_value
        or summary_fragment.get("status")
        or "blocked_missing_source_intake_not_proven"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "PR #5 PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending."
    )
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    if "PRRT_kwDOSWB9286CJ3tX" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    reviewer_ack_status_doc = (
        summary_fragment.get("reviewer_ack_status")
        if isinstance(summary_fragment.get("reviewer_ack_status"), dict)
        else {}
    )
    # 显式拆开 ACK 来源状态，避免 Python 条件表达式把当前 review decision 状态误当上游 ACK 状态。
    source_ack_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_reviewer_ack_intake_status")
        or summary_fragment.get("source_ack_intake_status")
        or reviewer_ack_status_doc.get("status")
        or ("blocked_missing_source_intake_not_proven" if intake_input else "")
    )
    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
            ),
            "upstream_source_schema": _redact_route_task_rehearsal_text(source_schema),
            "upstream_source_evidence_boundary": _redact_route_task_rehearsal_text(
                source_boundary
            ),
            "reviewer_ack_review_decision": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    decision_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response reviewer ACK review decision is software_proof only"
                ),
            },
            "source_reviewer_ack_intake_status": source_ack_status,
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref", "")
            ),
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "source_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_status")
                or response.get("source_handoff_status")
                or ""
            ),
            "source_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision_status")
                or response.get("source_review_decision_status")
                or ""
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by")
                or summary_fragment.get("reviewer")
                or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at") or ""
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
                or summary_fragment.get("review_decision_reasons")
                or decision_doc.get("reasons")
            ),
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                or summary_fragment.get("accepted_materials")
                or summary_fragment.get("accepted")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                or summary_fragment.get("missing_materials")
                or summary_fragment.get("missing")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                or summary_fragment.get("rejected_materials")
                or summary_fragment.get("rejected")
            ),
            "unsafe_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials_summary")
                or summary_fragment.get("unsafe_materials")
                or summary_fragment.get("unsafe")
            ),
            "reassignment_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("reassignment_reason")
                or decision_doc.get("reassignment_reason")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "operator_support_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_routing")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy_text, "status": status},
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "not_proven": (
                _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )

    source_is_review_decision_summary = fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    )
    required_safe_metadata = (
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["overall_status"] == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
        bool(summary["operator_support_handoff"]),
        bool(summary["reviewer_route"]),
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
    )
    if source_is_review_decision_summary:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
            bool(summary["safe_evidence_ref"]),
            bool(summary["safe_command_id"]),
            bool(summary["source_reviewer_ack_intake_status"]),
        )
    else:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
        )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response reviewer ACK review "
            "decision was blocked because the summary did not remain "
            "source=software_proof/not_proven with safe_to_control=false, "
            "delivery_success=false, primary_actions_enabled=false, PR #5 "
            "PRRT_kwDOSWB9286CJ3tX unresolved, hardware_material_pending, and no "
            "raw artifact, credentials, paths, ROS command topics, ACK/cursor "
            "mutation, collect/dropoff/cancel, review authorization, hardware, "
            "WAVE ROVER/UART, HIL, success, resolved, or control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
                "reviewer_ack_review_decision": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_reviewer_ack_review_decision contains unsafe fields, missing safe metadata, success wording, hardware details, PR-resolution claims, HIL claims, or control claims",
                },
                "source_reviewer_ack_intake_status": "",
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "acknowledged_by": "",
                "acknowledged_at": "",
                "decision_reasons": [],
                "ack_reasons": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "reassignment_reason": "",
                "next_required_evidence": [],
                "owner_handoff": [],
                "operator_support_handoff": [],
                "reviewer_route": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_not_proven(
    handoff=None,
    summary_fragment=None,
):
    # handoff 只把 reviewer ACK review-decision 转成 owner/support/reviewer 路由元数据。
    values = [
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_only",
        "source_reviewer_ack_review_decision_not_delivery_success",
        "handoff_not_pr5_resolution",
        "handoff_not_robot_control_authorization",
        "PRRT_kwDOSWB9286CJ3tX_unresolved",
        "hardware_material_pending",
        "real_terminal_result",
        "delivery_success",
        "robot_control_authorization",
        "route_or_elevator_field_pass",
        "real_hil_pass",
        "wave_rover_or_uart_proof",
        "true_phone_or_browser_proof",
        "public_ingress_or_tls_proof",
        "production_db_queue_proof",
    ]
    for container in (handoff or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for key in ("not_proven", "next_required_evidence"):
            for item in container.get(key, []):
                safe_item = _redact_route_task_rehearsal_text(item)
                lowered = safe_item.lower()
                # raw/path/checksum/HIL pass 字样是阻断证据，不应出现在 Robot/API/mobile safe alias。
                if any(
                    marker in lowered
                    for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
                ):
                    continue
                if safe_item and safe_item not in values:
                    values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary(
    path,
    status="blocked_missing_reviewer_ack_review_decision_not_proven",
    read_error="",
):
    # 缺 handoff 输入时仍输出完整 false flags，防止前端把空对象误读成可控制。
    safe_copy = (
        "Verified terminal result material owner response reviewer ACK review "
        "handoff is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; PR #5 PRRT_kwDOSWB9286CJ3tX remains "
        "unresolved and hardware_material_pending."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
        "source_schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
        "source_schema_version": None,
        "source_evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
        "upstream_source_schema": "",
        "upstream_source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "handoff_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_review_decision_status": "",
        "source_reviewer_ack_intake_status": "",
        "source_handoff_status": "",
        "source_review_decision_status": "",
        "source_owner_response_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "handoff_reasons": [],
        "decision_reasons": [],
        "ack_reasons": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "reassignment_reason": "",
        "next_required_evidence": [],
        "owner_handoff": [],
        "operator_support_handoff": [],
        "reviewer_route": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "not_proven": (
            _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "owner_response_material_accepted": False,
        "handoff_authorized": False,
        "review_decision_authorized": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
        "true_phone_browser_proof": False,
    }


def _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary_fragment(
    value,
):
    # 只接受本 rung 的 sanitized handoff summary；没有时允许从上游 review-decision 派生 blocked handoff。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
        ),
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
    value,
):
    # 复用 review-decision 的阻断规则，并额外拒绝 handoff/phone proof 成功语义。
    if _verified_terminal_result_material_owner_response_reviewer_ack_review_decision_has_unsafe_controls(
        value
    ):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
                "pr5_resolved",
                "true_phone_browser_proof",
            ) and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "review_decision_authorized",
                "pr5_resolved",
                "delivery_complete",
                "production_ready",
                "hil_pass",
                "field_pass",
                "handoff_authorized",
                "ack_mutation_enabled",
                "control_authorized",
                "true_phone_browser_proof",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "pr #5 resolved",
                "prrt_kwdoswb9286cj3tx resolved",
                "reviewer resolved",
                "thread resolved",
                "review authorized",
                "handoff authorized",
                "delivery success",
                "production ready",
                "public https",
                "tls proof",
                "4g/sim proof",
                "oss/cdn live",
                "hil pass",
                "hil_pass",
                "wave rover proof",
                "uart proof",
                "route field pass",
                "elevator field pass",
                "true phone",
                "true browser",
                "control enabled",
                "start delivery",
                "complete artifact",
                "complete_json",
                "checksum",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
    source,
):
    """构建 owner-response reviewer ACK review handoff 的只读 Robot diagnostics 摘要。"""
    # handoff alias 只转发安全交接元数据，绝不注册控制、ACK/cursor 或硬件动作语义。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary(
            source_path,
            read_error=(
                "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff summary artifact missing"
            )
            summary["handoff_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_reviewer_ack_review_handoff "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["handoff_status"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["handoff_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary_fragment(
            response
        )
    )
    if not summary_fragment:
        summary["status"] = (
            "blocked_missing_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
        )
        summary["handoff_status"]["status"] = summary["status"]
        summary["handoff_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff input is missing sanitized summary"
        )
        return summary

    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema = str(summary_fragment.get("source_schema") or "")
    source_boundary = str(summary_fragment.get("source_evidence_boundary") or "")
    source_is_handoff_summary = fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    )
    if source_is_handoff_summary:
        source_schema = (
            source_schema
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        )
        source_boundary = (
            source_boundary
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        )
        upstream_source_schema = str(
            summary_fragment.get("upstream_source_schema")
            or summary_fragment.get("source_reviewer_ack_review_decision_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        )
        upstream_source_boundary = str(
            summary_fragment.get("upstream_source_evidence_boundary")
            or summary_fragment.get(
                "source_reviewer_ack_review_decision_evidence_boundary"
            )
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        )
    else:
        source_schema = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA
        source_boundary = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE
        upstream_source_schema = source_schema
        upstream_source_boundary = source_boundary
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    handoff_doc = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else summary_fragment.get("reviewer_ack_review_handoff")
        if isinstance(summary_fragment.get("reviewer_ack_review_handoff"), dict)
        else summary_fragment.get("review_handoff")
        if isinstance(summary_fragment.get("review_handoff"), dict)
        else {}
    )
    source_decision_input = not source_is_handoff_summary
    status = _redact_route_task_rehearsal_text(
        "blocked_missing_reviewer_ack_review_decision_not_proven"
        if source_decision_input
        else handoff_doc.get("status")
        or summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), str)
        else summary_fragment.get("status")
        or "blocked_missing_reviewer_ack_review_decision_not_proven"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "PR #5 PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending."
    )
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    if "PRRT_kwDOSWB9286CJ3tX" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    decision_doc = (
        summary_fragment.get("reviewer_ack_review_decision")
        if isinstance(summary_fragment.get("reviewer_ack_review_decision"), dict)
        else summary_fragment.get("review_decision")
        if isinstance(summary_fragment.get("review_decision"), dict)
        else {}
    )
    source_review_decision_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_reviewer_ack_review_decision_status")
        or summary_fragment.get("source_review_decision_status")
        or decision_doc.get("status")
        or summary_fragment.get("status")
        or ("blocked_missing_reviewer_ack_review_decision_not_proven" if source_decision_input else "")
    )
    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
            ),
            "upstream_source_schema": _redact_route_task_rehearsal_text(
                upstream_source_schema
            ),
            "upstream_source_evidence_boundary": _redact_route_task_rehearsal_text(
                upstream_source_boundary
            ),
            "handoff_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    handoff_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response reviewer ACK review handoff is software_proof only"
                ),
            },
            "source_reviewer_ack_review_decision_status": source_review_decision_status,
            "source_reviewer_ack_intake_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_intake_status")
                or response.get("source_reviewer_ack_intake_status")
                or ""
            ),
            "source_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_status")
                or response.get("source_handoff_status")
                or ""
            ),
            "source_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision_status")
                or response.get("source_review_decision_status")
                or ""
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref", "")
            ),
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by")
                or summary_fragment.get("reviewer")
                or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at") or ""
            ),
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or handoff_doc.get("reasons")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
                or summary_fragment.get("review_decision_reasons")
                or decision_doc.get("reasons")
            ),
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                or summary_fragment.get("accepted_materials")
                or summary_fragment.get("accepted")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                or summary_fragment.get("missing_materials")
                or summary_fragment.get("missing")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                or summary_fragment.get("rejected_materials")
                or summary_fragment.get("rejected")
            ),
            "unsafe_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials_summary")
                or summary_fragment.get("unsafe_materials")
                or summary_fragment.get("unsafe")
            ),
            "reassignment_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("reassignment_reason")
                or handoff_doc.get("reassignment_reason")
                or decision_doc.get("reassignment_reason")
                or ""
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "owner_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_handoff")
            ),
            "operator_support_handoff": _safe_route_task_rehearsal_list(
                summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_routing")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy_text, "status": status},
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "not_proven": (
                _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["overall_status"] == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
        bool(summary["next_required_evidence"]),
        bool(summary["owner_handoff"]),
        bool(summary["operator_support_handoff"]),
        bool(summary["reviewer_route"]),
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
    )
    if source_is_handoff_summary:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
            upstream_source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
            upstream_source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
            bool(summary["safe_evidence_ref"]),
            bool(summary["safe_command_id"]),
            bool(summary["source_reviewer_ack_review_decision_status"]),
        )
    else:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
        )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response reviewer ACK review "
            "handoff was blocked because the summary did not remain "
            "source=software_proof/not_proven with safe_to_control=false, "
            "delivery_success=false, primary_actions_enabled=false, PR #5 "
            "PRRT_kwDOSWB9286CJ3tX unresolved, hardware_material_pending, and no "
            "raw artifact, credentials, paths, ROS command topics, ACK/cursor "
            "mutation, collect/dropoff/cancel, handoff authorization, review "
            "authorization, phone/browser proof, hardware, WAVE ROVER/UART, HIL, "
            "success, resolved, or control claims."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
                "handoff_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff contains unsafe fields, missing safe metadata, success wording, hardware details, PR-resolution claims, HIL claims, true phone/browser proof, or control claims",
                },
                "source_reviewer_ack_review_decision_status": "",
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "acknowledged_by": "",
                "acknowledged_at": "",
                "handoff_reasons": [],
                "decision_reasons": [],
                "ack_reasons": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "reassignment_reason": "",
                "next_required_evidence": [],
                "owner_handoff": [],
                "operator_support_handoff": [],
                "reviewer_route": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary


def _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_not_proven(
    followup=None,
    summary_fragment=None,
):
    # follow-up escalation 只能说明后续材料追踪状态，不能被误读为 PR #5 已解决或可控车。
    values = [
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_only",
        "source_reviewer_ack_review_handoff_not_delivery_success",
        "followup_escalation_not_pr5_resolution",
        "hardware_material_pending",
        "PRRT_kwDOSWB9286CJ3tX_unresolved",
        "real_terminal_result",
        "delivery_success",
        "robot_control_authorization",
        "route_or_elevator_field_pass",
        "real_hil_pass",
        "wave_rover_or_uart_proof",
        "true_phone_or_browser_proof",
        "public_ingress_or_tls_proof",
        "production_db_queue_proof",
    ]
    for container in (followup or {}, summary_fragment or {}):
        if not isinstance(container, dict):
            continue
        for key in ("not_proven", "next_required_evidence"):
            for item in container.get(key, []):
                safe_item = _redact_route_task_rehearsal_text(item)
                lowered = safe_item.lower()
                # raw/path/checksum/HIL pass 只能作为拒绝原因，不能进入 not_proven 白名单。
                if any(
                    marker in lowered
                    for marker in ("raw", "path", "checksum", "hil pass", "[redacted")
                ):
                    continue
                if safe_item and safe_item not in values:
                    values.append(safe_item)
    return values


def _default_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary(
    path,
    status="blocked_missing_real_materials",
    read_error="",
):
    # 缺少 sanitized PC summary 时必须 fail closed，避免空 diagnostics 被 mobile 当成可操作态。
    safe_copy = (
        "Verified terminal result material owner response reviewer ACK follow-up "
        "escalation status is metadata-only; source=software_proof; not_proven; "
        "safe_to_control=false; delivery_success=false; "
        "primary_actions_enabled=false; PR #5 PRRT_kwDOSWB9286CJ3tX remains "
        "unresolved and hardware_material_pending."
    )
    reason = read_error or (
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status summary is not configured"
    )
    return {
        "schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        "schema_version": 1,
        "capability": "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status",
        "evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE,
        "source_schema": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
        "source_schema_version": None,
        "source_evidence_boundary": VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE,
        "upstream_source_schema": "",
        "upstream_source_evidence_boundary": "",
        "configured": bool(str(path or "").strip()),
        "exists": False,
        "status": status,
        "overall_status": "not_proven",
        "source": EVIDENCE_SOURCE_SOFTWARE,
        "followup_status": {
            "status": status,
            "verdict": "not_proven",
            "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
            "reason": reason,
        },
        "source_reviewer_ack_review_handoff_status": "",
        "source_reviewer_ack_review_decision_status": "",
        "source_reviewer_ack_intake_status": "",
        "source_handoff_status": "",
        "source_review_decision_status": "",
        "source_owner_response_status": "",
        "safe_evidence_ref": "",
        "safe_command_id": "",
        "terminal_result_type": "",
        "acknowledged_by": "",
        "acknowledged_at": "",
        "due_at": "",
        "overdue": False,
        "escalated": False,
        "escalation_reason": "",
        "blocked_reason": "",
        "owner_route": [],
        "support_route": [],
        "reviewer_route": [],
        "next_required_evidence": [],
        "handoff_reasons": [],
        "decision_reasons": [],
        "ack_reasons": [],
        "accepted_materials_summary": [],
        "missing_materials_summary": [],
        "rejected_materials_summary": [],
        "unsafe_materials_summary": [],
        "safe_copy": safe_copy,
        "safe_phone_copy": safe_copy,
        "robot_diagnostics_summary": {"safe_copy": safe_copy, "status": status},
        "pr5_thread_id": "PRRT_kwDOSWB9286CJ3tX",
        "pr5_thread_state": "unresolved",
        "pr5_material_state": "hardware_material_pending",
        "pr5_reply_resolution_claim": "not_reviewer_resolution",
        "not_proven": (
            _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_not_proven()
        ),
        "read_error": _redact_route_task_rehearsal_text(read_error),
        "metadata_only": True,
        "summary_required": True,
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
        "ack_mutation_allowed": False,
        "cursor_mutation_allowed": False,
        "replay_allowed": False,
        "resubmit_allowed": False,
        "diagnostics_fetch_mutation_allowed": False,
        "robot_command_hint_allowed": False,
        "robot_control_allowed": False,
        "nav2_triggered": False,
        "hil_pass": False,
        "field_pass": False,
        "production_ready": False,
        "dropoff_completion": False,
        "cancel_completion": False,
        "reviewer_resolution": False,
        "pr5_resolved": False,
        "hardware_material_pending": True,
        "true_phone_browser_proof": False,
        "okr_percentage_lift": False,
    }


def _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary_fragment(
    value,
):
    # 只接受 PC gate/Robot 已消毒 summary；上一 rung handoff 只能导出 blocked follow-up。
    if not isinstance(value, dict):
        return {}
    if str(value.get("schema") or "") in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ):
        return value
    for candidate in (
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary"
        ),
        value.get(
            "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
        ),
        value.get(
            "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary"
        ),
        value.get("diagnostics_summary"),
        value.get("robot_diagnostics_summary"),
        value.get("robot_compatible_summary"),
        value.get("summary"),
    ):
        if isinstance(candidate, dict):
            return candidate
    for container_name in ("diagnostics", "status", "latest_status"):
        container = value.get(container_name)
        if isinstance(container, dict):
            nested = (
                _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary_fragment(
                    container
                )
            )
            if nested:
                return nested
    return {}


def _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
    value,
):
    # 复用 handoff 的阻断规则，并额外拒绝 follow-up 变成 fetch/mutation/command 指引。
    if _verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_has_unsafe_controls(
        value
    ):
        return True
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "").strip().lower()
            if key_text == "not_proven":
                continue
            if key_text in (
                "delivery_success",
                "primary_actions_enabled",
                "safe_to_control",
                "overdue",
                "escalated",
                "pr5_resolved",
                "true_phone_browser_proof",
                "diagnostics_fetch_mutation_allowed",
                "robot_command_hint_allowed",
            ) and item is False:
                continue
            if key_text == "hardware_material_pending" and item is True:
                continue
            if key_text in (
                "raw_artifact",
                "raw_artifacts",
                "raw_robot_response",
                "raw_response",
                "raw_ack",
                "raw_ack_payload",
                "ack_payload",
                "ack_cursor",
                "cursor_value",
                "cursor",
                "raw_diagnostics_fetch",
                "diagnostics_fetch_mutation",
                "robot_command_hint",
                "cmd_vel",
            ):
                return True
            if key_text in (
                "reviewer_resolution",
                "reviewer_resolved",
                "pr5_resolved",
                "delivery_complete",
                "production_ready",
                "hil_pass",
                "field_pass",
                "ack_mutation_enabled",
                "control_authorized",
                "diagnostics_fetch_mutation_allowed",
                "robot_command_hint_allowed",
            ) and bool(item):
                return True
            if _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
                item
            ):
                return True
        return False
    if isinstance(value, list):
        return any(
            _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
                item
            )
            for item in value
        )
    if isinstance(value, str):
        lowered = value.lower()
        return any(
            marker in lowered
            for marker in (
                "pr #5 resolved",
                "reviewer resolved",
                "thread resolved",
                "delivery success",
                "production ready",
                "hil pass",
                "hil_pass",
                "field pass",
                "wave rover proof",
                "uart proof",
                "control enabled",
                "start delivery",
                "ack payload",
                "ack cursor",
                "cursor value",
                "raw robot response",
                "diagnostics fetch mutation",
                "robot command",
                "ros topic",
                "/cmd_vel",
                "/dev/tty",
                "serial",
                "uart",
                "complete_json",
                "checksum",
            )
        )
    return False


def summarize_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
    source,
):
    """构建 owner-response reviewer ACK follow-up escalation status 的只读 Robot diagnostics 摘要。"""
    # Robot 只能消费 PC gate 的 sanitized summary；任何 raw artifact 都会阻断，防止控制面被旁路打开。
    source_path = "" if isinstance(source, dict) else os.path.expanduser(str(source or ""))
    summary = (
        _default_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary(
            source_path,
            read_error=(
                "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status summary is not configured"
            ),
        )
    )
    if isinstance(source, dict):
        response = dict(source)
    else:
        if not source_path:
            return summary
        if not os.path.exists(source_path):
            summary["read_error"] = (
                "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status summary artifact missing"
            )
            summary["followup_status"]["reason"] = summary["read_error"]
            return summary
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            safe_error = _redact_route_task_rehearsal_text(
                "failed reading verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status "
                f"summary: {exc}"
            )
            summary["read_error"] = safe_error
            summary["followup_status"]["reason"] = safe_error
            return summary

    if not isinstance(response, dict):
        summary["followup_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status JSON must be an object"
        )
        return summary

    raw_schema = str(response.get("schema") or "")
    summary_fragment = (
        _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary_fragment(
            response
        )
    )
    if not summary_fragment:
        summary["status"] = (
            "blocked_missing_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary"
        )
        summary["followup_status"]["status"] = summary["status"]
        summary["followup_status"]["reason"] = (
            "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status input is missing sanitized summary"
        )
        return summary

    fragment_schema = str(summary_fragment.get("schema") or "")
    source_schema = str(summary_fragment.get("source_schema") or "")
    source_boundary = str(summary_fragment.get("source_evidence_boundary") or "")
    source_is_followup_summary = fragment_schema in (
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
        VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    )
    if source_is_followup_summary:
        source_schema = (
            source_schema
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
        )
        source_boundary = (
            source_boundary
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
        )
        upstream_source_schema = str(
            summary_fragment.get("upstream_source_schema")
            or summary_fragment.get("source_reviewer_ack_review_handoff_schema")
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        )
        upstream_source_boundary = str(
            summary_fragment.get("upstream_source_evidence_boundary")
            or summary_fragment.get(
                "source_reviewer_ack_review_handoff_evidence_boundary"
            )
            or VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        )
    else:
        source_schema = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA
        source_boundary = VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE
        upstream_source_schema = source_schema
        upstream_source_boundary = source_boundary
    if not source_schema and raw_schema:
        source_schema = raw_schema
    if not source_boundary:
        source_boundary = str(response.get("evidence_boundary") or "")

    followup_doc = (
        summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), dict)
        else summary_fragment.get("followup")
        if isinstance(summary_fragment.get("followup"), dict)
        else {}
    )
    source_handoff_input = not source_is_followup_summary
    status = _redact_route_task_rehearsal_text(
        "blocked_missing_real_materials"
        if source_handoff_input
        else followup_doc.get("status")
        or summary_fragment.get("followup_status")
        if isinstance(summary_fragment.get("followup_status"), str)
        else summary_fragment.get("status")
        or "blocked_missing_real_materials"
    )
    safe_copy = (
        summary_fragment.get("safe_copy")
        or summary_fragment.get("safe_phone_copy")
        or summary["safe_copy"]
    )
    safe_copy_text = _redact_route_task_rehearsal_text(safe_copy)
    required_suffix = (
        "source=software_proof; not_proven; safe_to_control=false; "
        "delivery_success=false; primary_actions_enabled=false; "
        "PR #5 PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending; "
        "no OKR percentage lift."
    )
    if "delivery_success=false" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    if "PRRT_kwDOSWB9286CJ3tX" not in safe_copy_text:
        safe_copy_text = f"{safe_copy_text}; {required_suffix}"
    robot_summary = (
        summary_fragment.get("robot_diagnostics_summary")
        if isinstance(summary_fragment.get("robot_diagnostics_summary"), dict)
        else summary_fragment.get("robot_compatible_summary")
        if isinstance(summary_fragment.get("robot_compatible_summary"), dict)
        else {}
    )
    handoff_doc = (
        summary_fragment.get("handoff_status")
        if isinstance(summary_fragment.get("handoff_status"), dict)
        else summary_fragment.get("reviewer_ack_review_handoff")
        if isinstance(summary_fragment.get("reviewer_ack_review_handoff"), dict)
        else {}
    )
    source_handoff_status = _redact_route_task_rehearsal_text(
        summary_fragment.get("source_reviewer_ack_review_handoff_status")
        or summary_fragment.get("source_handoff_status")
        or handoff_doc.get("status")
        or ("blocked_missing_real_materials" if source_handoff_input else "")
    )
    summary.update(
        {
            "configured": bool(str(source_path or "").strip()) or isinstance(source, dict),
            "exists": True,
            "status": status,
            "overall_status": "not_proven",
            "source": EVIDENCE_SOURCE_SOFTWARE,
            "source_schema_version": summary_fragment.get("source_schema_version")
            or summary_fragment.get("schema_version"),
            "source_schema": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA
            ),
            "source_evidence_boundary": _redact_route_task_rehearsal_text(
                VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE
            ),
            "upstream_source_schema": _redact_route_task_rehearsal_text(
                upstream_source_schema
            ),
            "upstream_source_evidence_boundary": _redact_route_task_rehearsal_text(
                upstream_source_boundary
            ),
            "followup_status": {
                "status": status,
                "verdict": "not_proven",
                "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                "reason": _redact_route_task_rehearsal_text(
                    followup_doc.get("reason")
                    or summary_fragment.get("reason")
                    or "verified terminal result material owner response reviewer ACK follow-up escalation status is software_proof only"
                ),
            },
            "source_reviewer_ack_review_handoff_status": source_handoff_status,
            "source_reviewer_ack_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_review_decision_status")
                or response.get("source_reviewer_ack_review_decision_status")
                or ""
            ),
            "source_reviewer_ack_intake_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_reviewer_ack_intake_status")
                or response.get("source_reviewer_ack_intake_status")
                or ""
            ),
            "source_handoff_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_handoff_status")
                or response.get("source_handoff_status")
                or ""
            ),
            "source_review_decision_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_review_decision_status")
                or response.get("source_review_decision_status")
                or ""
            ),
            "source_owner_response_status": _redact_route_task_rehearsal_text(
                summary_fragment.get("source_owner_response_status")
                or response.get("source_owner_response_status")
                or ""
            ),
            "safe_evidence_ref": _safe_route_task_rehearsal_ref(
                summary_fragment.get("safe_evidence_ref")
                or summary_fragment.get("evidence_ref")
                or response.get("safe_evidence_ref")
                or response.get("evidence_ref", "")
            ),
            "safe_command_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("safe_command_id")
                or summary_fragment.get("command_id")
                or response.get("safe_command_id")
                or response.get("command_id")
                or ""
            ),
            "terminal_result_type": _redact_route_task_rehearsal_text(
                summary_fragment.get("terminal_result_type")
                or response.get("terminal_result_type")
                or ""
            ),
            "acknowledged_by": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_by")
                or summary_fragment.get("reviewer")
                or ""
            ),
            "acknowledged_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("acknowledged_at") or ""
            ),
            "due_at": _redact_route_task_rehearsal_text(
                summary_fragment.get("due_at") or followup_doc.get("due_at") or ""
            ),
            "overdue": bool(summary_fragment.get("overdue") or status == "overdue"),
            "escalated": bool(summary_fragment.get("escalated") or status == "escalated"),
            "escalation_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("escalation_reason")
                or followup_doc.get("escalation_reason")
                or ""
            ),
            "blocked_reason": _redact_route_task_rehearsal_text(
                summary_fragment.get("blocked_reason")
                or followup_doc.get("blocked_reason")
                or ""
            ),
            "owner_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("owner_route")
                or summary_fragment.get("owner_handoff")
            ),
            "support_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("support_route")
                or summary_fragment.get("operator_support_handoff")
                or summary_fragment.get("support_handoff")
            ),
            "reviewer_route": _safe_route_task_rehearsal_list(
                summary_fragment.get("reviewer_route")
                or summary_fragment.get("reviewer_routing")
            ),
            "next_required_evidence": _safe_route_task_rehearsal_list(
                summary_fragment.get("next_required_evidence")
            ),
            "handoff_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("handoff_reasons")
                or handoff_doc.get("reasons")
            ),
            "decision_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("decision_reasons")
            ),
            "ack_reasons": _safe_route_task_rehearsal_list(
                summary_fragment.get("ack_reasons")
            ),
            "accepted_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("accepted_materials_summary")
                or summary_fragment.get("accepted_materials")
            ),
            "missing_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("missing_materials_summary")
                or summary_fragment.get("missing_materials")
            ),
            "rejected_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("rejected_materials_summary")
                or summary_fragment.get("rejected_materials")
            ),
            "unsafe_materials_summary": _safe_route_task_rehearsal_list(
                summary_fragment.get("unsafe_materials_summary")
                or summary_fragment.get("unsafe_materials")
            ),
            "safe_copy": safe_copy_text,
            "safe_phone_copy": safe_copy_text,
            "robot_diagnostics_summary": _safe_pc_route_debug_dict(robot_summary)
            or {"safe_copy": safe_copy_text, "status": status},
            "pr5_thread_id": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_id") or "PRRT_kwDOSWB9286CJ3tX"
            ),
            "pr5_thread_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_thread_state") or "unresolved"
            ),
            "pr5_material_state": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_material_state")
                or "hardware_material_pending"
            ),
            "pr5_reply_resolution_claim": _redact_route_task_rehearsal_text(
                summary_fragment.get("pr5_reply_resolution_claim")
                or "not_reviewer_resolution"
            ),
            "not_proven": (
                _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_not_proven(
                    response,
                    summary_fragment,
                )
            ),
            "read_error": "",
        }
    )

    required_safe_metadata = (
        summary["source"] == EVIDENCE_SOURCE_SOFTWARE,
        summary["overall_status"] == "not_proven",
        status
        in VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES,
        summary["pr5_thread_id"] == "PRRT_kwDOSWB9286CJ3tX",
        summary["pr5_thread_state"] == "unresolved",
        summary["pr5_material_state"] == "hardware_material_pending",
        summary["pr5_reply_resolution_claim"] == "not_reviewer_resolution",
        summary_fragment.get("delivery_success") is False,
        summary_fragment.get("primary_actions_enabled") is False,
        summary_fragment.get("safe_to_control") is False,
    )
    if source_is_followup_summary:
        required_safe_metadata = required_safe_metadata + (
            bool(summary["next_required_evidence"]),
            bool(summary["owner_route"]),
            bool(summary["support_route"]),
            bool(summary["reviewer_route"]),
            bool(summary["blocked_reason"] or summary["escalation_reason"]),
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE,
            upstream_source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
            upstream_source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
            bool(summary["safe_evidence_ref"]),
            bool(summary["safe_command_id"]),
            bool(summary["source_reviewer_ack_review_handoff_status"]),
        )
    else:
        required_safe_metadata = required_safe_metadata + (
            source_schema
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
            source_boundary
            == VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
        )
    unsafe_payload = (
        not all(required_safe_metadata)
        or _real_material_evidence_ref_is_unsafe(summary["safe_evidence_ref"])
        or _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
            response
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
            summary_fragment
        )
        or _verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_controls(
            robot_summary
        )
        or _task_terminal_field_material_intake_copy_is_unsafe(safe_copy_text)
    )
    if unsafe_payload:
        blocked_copy = (
            "Verified terminal result material owner response reviewer ACK "
            "follow-up escalation status was blocked because the summary did "
            "not remain source=software_proof/not_proven with "
            "safe_to_control=false, delivery_success=false, "
            "primary_actions_enabled=false, PR #5 PRRT_kwDOSWB9286CJ3tX "
            "unresolved, hardware_material_pending, owner/support/reviewer "
            "route, next required evidence, due/overdue/escalated state, and "
            "no unsafe source details, secret material, local filesystem "
            "references, robot transport details, ACK or cursor mutation "
            "material, diagnostics mutation hints, command hints, PR #5 "
            "resolved wording, HIL/field pass, delivery success, or true "
            "control flags."
        )
        summary.update(
            {
                "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
                "followup_status": {
                    "status": "blocked_unsafe_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
                    "verdict": "not_proven",
                    "evidence_source": EVIDENCE_SOURCE_SOFTWARE,
                    "reason": "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status contains unsafe fields, missing safe metadata, success wording, hardware details, PR-resolution claims, HIL claims, raw ACK/cursor or command hints, or control claims",
                },
                "source_reviewer_ack_review_handoff_status": "",
                "safe_evidence_ref": "",
                "safe_command_id": "",
                "acknowledged_by": "",
                "acknowledged_at": "",
                "due_at": "",
                "overdue": False,
                "escalated": False,
                "escalation_reason": "",
                "blocked_reason": "",
                "owner_route": [],
                "support_route": [],
                "reviewer_route": [],
                "next_required_evidence": [],
                "handoff_reasons": [],
                "decision_reasons": [],
                "ack_reasons": [],
                "accepted_materials_summary": [],
                "missing_materials_summary": [],
                "rejected_materials_summary": [],
                "unsafe_materials_summary": [],
                "safe_copy": blocked_copy,
                "safe_phone_copy": blocked_copy,
                "robot_diagnostics_summary": {
                    "safe_copy": blocked_copy,
                    "safe_phone_copy": blocked_copy,
                    "status": "blocked",
                },
            }
        )
    return summary

