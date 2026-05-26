import json
import os
import re

from ros2_trashbot_behavior.operator_gateway_diagnostics_payload_sources import (
    first_dict_value,
    first_non_empty_dict_value,
    first_non_empty_dict_then_first_dict,
    first_status_dict,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_hardware_sensor import *
from ros2_trashbot_behavior.operator_gateway_diagnostics_wave_rover_hardware import (
    HARDWARE_BASELINE_REVIEW_GATE,
    HARDWARE_BASELINE_REVIEW_SCHEMA,
    HARDWARE_BASELINE_REVIEW_SUMMARY_SCHEMA,
    HARDWARE_BASELINE_SOURCE_ALIGNMENT_GATE,
    HARDWARE_BASELINE_SOURCE_ALIGNMENT_SCHEMA,
    HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY_SCHEMA,
    WAVE_ROVER_FEEDBACK_REPLAY_GATE,
    WAVE_ROVER_FEEDBACK_REPLAY_SCHEMA,
    WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY_SCHEMA,
    WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_GATE,
    WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SCHEMA,
    WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY_SCHEMA,
    WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_GATE,
    WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SCHEMA,
    WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY_SCHEMA,
    WAVE_ROVER_HIL_PACKET_INTAKE_GATE,
    WAVE_ROVER_HIL_PACKET_INTAKE_SCHEMA,
    WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY_SCHEMA,
    WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_GATE,
    WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SCHEMA,
    WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY_SCHEMA,
    _default_hardware_baseline_review_summary,
    _default_hardware_baseline_source_alignment_summary,
    _default_wave_rover_feedback_replay_summary,
    _default_wave_rover_hil_packet_collection_drill_summary,
    _default_wave_rover_hil_packet_execution_pack_summary,
    _default_wave_rover_hil_packet_intake_summary,
    _default_wave_rover_hil_packet_review_decision_summary,
    _hardware_baseline_review_not_proven,
    _hardware_baseline_review_source_contract,
    _hardware_baseline_source_alignment_field,
    _hardware_baseline_source_alignment_has_unsafe_fields,
    _hardware_baseline_source_alignment_not_proven,
    _hardware_baseline_source_alignment_source_contract,
    _hardware_baseline_source_alignment_status,
    _wave_rover_feedback_replay_has_disabled_actions,
    _wave_rover_feedback_replay_has_not_proven,
    _wave_rover_feedback_replay_has_unsafe_fields,
    _wave_rover_feedback_replay_not_proven,
    _wave_rover_feedback_replay_source_contract,
    _wave_rover_hil_packet_collection_drill_has_disabled_actions,
    _wave_rover_hil_packet_collection_drill_has_not_proven,
    _wave_rover_hil_packet_collection_drill_not_proven,
    _wave_rover_hil_packet_collection_drill_source_contract,
    _wave_rover_hil_packet_execution_pack_has_disabled_actions,
    _wave_rover_hil_packet_execution_pack_not_proven,
    _wave_rover_hil_packet_execution_pack_source_contract,
    _wave_rover_hil_packet_intake_has_disabled_actions,
    _wave_rover_hil_packet_intake_has_not_proven,
    _wave_rover_hil_packet_intake_has_unsafe_fields,
    _wave_rover_hil_packet_intake_not_proven,
    _wave_rover_hil_packet_intake_same_evidence_ref_ok,
    _wave_rover_hil_packet_intake_source_contract,
    _wave_rover_hil_packet_review_decision_has_disabled_actions,
    _wave_rover_hil_packet_review_decision_has_not_proven,
    _wave_rover_hil_packet_review_decision_has_unsafe_fields,
    _wave_rover_hil_packet_review_decision_not_proven,
    _wave_rover_hil_packet_review_decision_same_evidence_ref_ok,
    _wave_rover_hil_packet_review_decision_source_contract,
    summarize_hardware_baseline_review,
    summarize_hardware_baseline_source_alignment,
    summarize_wave_rover_feedback_replay,
    summarize_wave_rover_hil_packet_collection_drill,
    summarize_wave_rover_hil_packet_execution_pack,
    summarize_wave_rover_hil_packet_intake,
    summarize_wave_rover_hil_packet_review_decision,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_rehearsal import (
    PC_ROUTE_DEBUG_CONSOLE_GATE,
    PC_ROUTE_DEBUG_CONSOLE_SCHEMA,
    PC_ROUTE_DEBUG_CONSOLE_SUMMARY_SCHEMA,
    PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_GATE,
    PC_ROUTE_ELEVATOR_CONSOLE_INTEGRATION_SUMMARY_SCHEMA,
    ROUTE_TASK_REHEARSAL_ARTIFACT_GATE,
    ROUTE_TASK_REHEARSAL_DIAGNOSTICS_GATE,
    ROUTE_TASK_REHEARSAL_DIAGNOSTICS_SCHEMA,
    ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_GATE,
    ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SCHEMA,
    ROUTE_TASK_REHEARSAL_EXECUTION_BUNDLE_SUMMARY_SCHEMA,
    ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_GATE,
    ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SCHEMA,
    ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW_SUMMARY_SCHEMA,
    ROUTE_TASK_REHEARSAL_REQUIRED_NOT_PROVEN,
    ROUTE_TASK_REHEARSAL_SCHEMA,
    ROUTE_TASK_REHEARSAL_TEXT_REDACTIONS,
    _default_pc_route_debug_console_summary,
    _default_pc_route_elevator_reconciliation_summary,
    _default_route_task_rehearsal_execution_bundle_summary,
    _default_route_task_rehearsal_operator_review_summary,
    _default_route_task_rehearsal_summary,
    _first_route_task_rehearsal_value,
    _pc_route_debug_not_proven,
    _pc_route_debug_safe_copy_is_unsafe,
    _pc_route_elevator_reconciliation_has_unsafe_control_claims,
    _pc_route_elevator_reconciliation_not_proven,
    _pc_route_elevator_reconciliation_safe_copy_is_unsafe,
    _redact_route_task_rehearsal_text,
    _route_task_rehearsal_not_proven,
    _route_task_rehearsal_review_dict,
    _route_task_rehearsal_review_mismatch_summary,
    _route_task_rehearsal_review_safe_copy_is_unsafe,
    _safe_pc_route_debug_dict,
    _safe_pc_route_debug_value,
    _safe_route_task_rehearsal_list,
    _safe_route_task_rehearsal_ref,
    _summarize_pc_route_elevator_reconciliation,
    summarize_pc_route_debug_console,
    summarize_route_task_rehearsal_artifact,
    summarize_route_task_rehearsal_execution_bundle,
    summarize_route_task_rehearsal_operator_review,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_task_field_retest import *
from ros2_trashbot_behavior.operator_gateway_diagnostics_real_material import (
    HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_GATE,
    HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_REQUIRED_NOT_PROVEN,
    HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SCHEMA,
    HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SOURCE_SUMMARY_SCHEMA,
    HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SUMMARY_SCHEMA,
    REAL_MATERIAL_EVIDENCE_INTAKE_GATE,
    REAL_MATERIAL_EVIDENCE_INTAKE_REQUIRED_NOT_PROVEN,
    REAL_MATERIAL_EVIDENCE_INTAKE_SCHEMA,
    REAL_MATERIAL_EVIDENCE_INTAKE_SOURCE_SUMMARY_SCHEMA,
    REAL_MATERIAL_EVIDENCE_INTAKE_SUMMARY_SCHEMA,
    REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
    REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_REQUIRED_NOT_PROVEN,
    REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    REAL_MATERIAL_MANIFEST_TEMPLATE_ALLOWED_KEYS,
    REAL_MATERIAL_MANIFEST_TEMPLATE_EVIDENCE_REF_KEYS,
    REAL_MATERIAL_MANIFEST_TEMPLATE_FIELDS,
    REAL_MATERIAL_READINESS_BOARD_GATE,
    REAL_MATERIAL_READINESS_BOARD_REQUIRED_NOT_PROVEN,
    REAL_MATERIAL_READINESS_BOARD_SCHEMA,
    REAL_MATERIAL_READINESS_BOARD_SOURCE_SUMMARY_SCHEMA,
    REAL_MATERIAL_READINESS_BOARD_SUMMARY_SCHEMA,
    _default_hardware_real_material_escalation_request_summary,
    _default_real_material_evidence_intake_summary,
    _default_real_material_followup_escalation_status_summary,
    _default_real_material_readiness_board_summary,
    _hardware_real_material_escalation_request_not_proven,
    _hardware_real_material_escalation_request_source_contract,
    _real_material_evidence_intake_not_proven,
    _real_material_evidence_intake_source_contract,
    _real_material_evidence_ref_is_unsafe,
    _real_material_followup_escalation_status_has_unsafe_fields,
    _real_material_followup_escalation_status_not_proven,
    _real_material_followup_escalation_status_source_contract,
    _real_material_manifest_template_scalar_is_unsafe,
    _real_material_readiness_board_not_proven,
    _real_material_readiness_board_source_contract,
    _safe_real_material_manifest_template_alias,
    _safe_real_material_manifest_template_value,
    summarize_hardware_real_material_escalation_request,
    summarize_real_material_evidence_intake,
    summarize_real_material_followup_escalation_status,
    summarize_real_material_readiness_board,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_verified_terminal_material import *
from ros2_trashbot_behavior.operator_gateway_diagnostics_pr5_material import (
    PR5_REVIEW_THREAD_CLOSEOUT_SCHEMA,
    PR5_REVIEW_THREAD_CLOSEOUT_SOURCE_SUMMARY_SCHEMA,
    PR5_REVIEW_THREAD_CLOSEOUT_SUMMARY_SCHEMA,
    PR5_REVIEW_THREAD_CLOSEOUT_GATE,
    PR5_VENDOR_SOURCE_REVIEW_PACKET_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_PACKET_SOURCE_SUMMARY_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_PACKET_SUMMARY_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_PACKET_GATE,
    PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SOURCE_SUMMARY_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SUMMARY_SCHEMA,
    PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_GATE,
    PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SCHEMA,
    PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATES,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_DECISIONS,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISIONS,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES,
    PR5_REVIEW_THREAD_CLOSEOUT_REQUIRED_NOT_PROVEN,
    PR5_VENDOR_SOURCE_REVIEW_PACKET_REQUIRED_NOT_PROVEN,
    PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_REQUIRED_NOT_PROVEN,
    PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_REQUIRED_NOT_PROVEN,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REQUIRED_NOT_PROVEN,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_REQUIRED_NOT_PROVEN,
    PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_REQUIRED_NOT_PROVEN,
    _dedupe_ordered,
    _pr5_review_thread_closeout_not_proven,
    _pr5_vendor_source_review_packet_not_proven,
    _pr5_mandatory_sensor_source_alignment_not_proven,
    _pr5_mandatory_sensor_material_followup_escalation_status_not_proven,
    _pr5_mandatory_sensor_material_owner_response_intake_not_proven,
    _pr5_mandatory_sensor_material_owner_response_review_decision_not_proven,
    _pr5_mandatory_sensor_material_owner_response_review_handoff_not_proven,
    _default_pr5_review_thread_closeout_summary,
    _default_pr5_vendor_source_review_packet_summary,
    _default_pr5_vendor_source_review_reply_dispatch_summary,
    _default_pr5_mandatory_sensor_source_alignment_summary,
    _default_pr5_mandatory_sensor_material_followup_escalation_status_summary,
    _default_pr5_mandatory_sensor_material_owner_response_intake_summary,
    _default_pr5_mandatory_sensor_material_owner_response_review_decision_summary,
    _default_pr5_mandatory_sensor_material_owner_response_review_handoff_summary,
    _default_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary,
    _pr5_review_thread_closeout_source_contract,
    _pr5_vendor_source_review_packet_source_contract,
    _pr5_vendor_source_review_reply_dispatch_source_contract,
    _pr5_mandatory_sensor_source_alignment_source_contract,
    _pr5_mandatory_sensor_material_followup_escalation_status_source_contract,
    _pr5_mandatory_sensor_material_owner_response_intake_source_contract,
    _pr5_mandatory_sensor_material_owner_response_review_decision_source_contract,
    _pr5_mandatory_sensor_material_owner_response_review_handoff_source_contract,
    _pr5_review_thread_closeout_copy_is_unsafe,
    _pr5_review_thread_closeout_has_unsafe_fields,
    summarize_pr5_review_thread_closeout,
    summarize_pr5_vendor_source_review_packet,
    _pr5_vendor_source_review_reply_dispatch_has_unsafe_fields,
    summarize_pr5_vendor_source_review_reply_dispatch,
    _pr5_mandatory_sensor_source_alignment_copy_is_unsafe,
    _pr5_mandatory_sensor_source_alignment_has_unsafe_fields,
    _pr5_mandatory_sensor_source_alignment_false_states_ok,
    _pr5_mandatory_sensor_material_followup_copy_is_unsafe,
    _pr5_mandatory_sensor_material_followup_has_unsafe_fields,
    _pr5_mandatory_sensor_material_followup_false_states_ok,
    _pr5_mandatory_sensor_material_owner_response_copy_is_unsafe,
    _pr5_mandatory_sensor_material_owner_response_has_unsafe_fields,
    _pr5_mandatory_sensor_material_owner_response_false_states_ok,
    _pr5_mandatory_sensor_material_owner_response_review_decision_has_unsafe_fields,
    summarize_pr5_mandatory_sensor_source_alignment,
    summarize_pr5_mandatory_sensor_material_followup_escalation_status,
    summarize_pr5_mandatory_sensor_material_owner_response_intake,
    summarize_pr5_mandatory_sensor_material_owner_response_review_decision,
    summarize_pr5_mandatory_sensor_material_owner_response_review_handoff,
    summarize_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake,
)

from ros2_trashbot_behavior.operator_gateway_http import (
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_AUDIT_EXPORT_SCHEMA,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_DRILL_SCHEMA,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_EVIDENCE_BOUNDARY,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_FALSE_STATES,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_NOT_PROVEN,
    CLOUD_COMMAND_LIFECYCLE_REPLAY_ACCEPTANCE_PACKET_SCHEMA,
    normalize_elevator_assist,
    build_cloud_command_lifecycle_audit_export,
    status_payload,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_cloud_guards import (
    CLOUD_ACK_ACCEPTED_RESULT_PENDING_FALSE_STATES,
    CLOUD_ACK_ACCEPTED_RESULT_PENDING_GUARD_SCHEMA,
    CLOUD_ACK_ACCEPTED_RESULT_PENDING_REQUIRED_NOT_PROVEN,
    CLOUD_ACK_LOOKUP_PENDING_FALSE_STATES,
    CLOUD_ACK_LOOKUP_PENDING_REQUIRED_NOT_PROVEN,
    CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_BOUNDARY,
    CLOUD_ACK_LOOKUP_PENDING_STATUS_GUARD_SCHEMA,
    CLOUD_CANCEL_PENDING_COMMAND_SAFETY_GUARD_SCHEMA,
    CLOUD_CANCEL_PENDING_FALSE_STATES,
    CLOUD_CANCEL_PENDING_REQUIRED_NOT_PROVEN,
    CLOUD_POLL_BACKOFF_FALSE_STATES,
    CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_BOUNDARY,
    CLOUD_POLL_BACKOFF_RATE_LIMIT_GUARD_SCHEMA,
    CLOUD_POLL_BACKOFF_REQUIRED_NOT_PROVEN,
    CLOUD_SUPPORT_HANDOFF_SAFE_EXPORT_ROBOT_SCHEMA,
    CLOUD_TERMINAL_RESULT_VERIFICATION_FALSE_STATES,
    CLOUD_TERMINAL_RESULT_VERIFICATION_GUARD_SCHEMA,
    CLOUD_TERMINAL_RESULT_VERIFICATION_REQUIRED_NOT_PROVEN,
    CLOUD_UNREACHABLE_MALFORMED_RESPONSE_FALSE_STATES,
    CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_BOUNDARY,
    CLOUD_UNREACHABLE_MALFORMED_RESPONSE_GUARD_SCHEMA,
    CLOUD_UNREACHABLE_MALFORMED_RESPONSE_REQUIRED_NOT_PROVEN,
    CLOUD_UNREACHABLE_MALFORMED_RESPONSE_STATES,
    _remote_readiness_for_ack_accepted_result_pending_guard,
    _remote_readiness_for_ack_lookup_pending_guard,
    _remote_readiness_for_cancel_pending_guard,
    _remote_readiness_for_cloud_guard,
    _remote_readiness_for_poll_backoff_guard,
    _remote_readiness_for_terminal_result_verification_guard,
    summarize_cloud_ack_accepted_result_pending_guard,
    summarize_cloud_ack_lookup_pending_status_guard,
    summarize_cloud_cancel_pending_command_safety_guard,
    summarize_cloud_poll_backoff_rate_limit_guard,
    summarize_cloud_support_handoff_safe_export,
    summarize_cloud_terminal_result_verification_guard,
    summarize_cloud_unreachable_malformed_response_guard,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_cloud_lifecycle import (
    summarize_cloud_command_lifecycle_audit_export,
    summarize_cloud_command_lifecycle_replay_acceptance_packet,
    summarize_cloud_command_lifecycle_replay_drill,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_cloud_external_evidence import (
    CLOUD_EXTERNAL_EVIDENCE_INTAKE_GATE,
    CLOUD_EXTERNAL_EVIDENCE_INTAKE_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_GATE,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_NOT_PROVEN,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_STATUSES,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_GATE,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_NOT_PROVEN,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_STATUSES,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_GATE,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_NOT_PROVEN,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_STATUSES,
    CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    summarize_cloud_external_evidence_review_decision,
    summarize_cloud_external_evidence_review_handoff,
    summarize_cloud_external_evidence_review_handoff_followup_escalation_status,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_cloud_worker import (
    CLOUD_WORKER_CUTOVER_DRAIN_GATE,
    CLOUD_WORKER_CUTOVER_DRAIN_REQUIRED_NOT_PROVEN,
    CLOUD_WORKER_CUTOVER_DRAIN_SCHEMA,
    CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY_SCHEMA,
    CLOUD_WORKER_MIGRATION_REHEARSAL_GATE,
    CLOUD_WORKER_MIGRATION_REHEARSAL_REQUIRED_NOT_PROVEN,
    CLOUD_WORKER_MIGRATION_REHEARSAL_SCHEMA,
    CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY_SCHEMA,
    _cloud_worker_cutover_drain_not_proven,
    _cloud_worker_cutover_drain_status,
    _cloud_worker_migration_rehearsal_not_proven,
    _cloud_worker_migration_rehearsal_status,
    _default_cloud_worker_cutover_drain_summary,
    _default_cloud_worker_migration_rehearsal_summary,
    summarize_cloud_worker_cutover_drain,
    summarize_cloud_worker_migration_rehearsal,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_task_terminal import (
    TASK_TERMINAL_COMPLETION_MAINLINE_GATE,
    TASK_TERMINAL_COMPLETION_MAINLINE_SCHEMA,
    TASK_TERMINAL_COMPLETION_MAINLINE_SUMMARY_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_INTAKE_GATE,
    TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SOURCE_SUMMARY_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_GATE,
    TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    TASK_TERMINAL_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    _default_task_terminal_completion_mainline_summary,
    _default_task_terminal_field_material_intake_summary,
    _default_task_terminal_field_material_review_decision_summary,
    _task_terminal_completion_mainline_not_proven,
    _task_terminal_completion_mainline_source_from_payloads,
    _task_terminal_field_material_intake_not_proven,
    _task_terminal_field_material_intake_source_from_payloads,
    _task_terminal_field_material_review_decision_not_proven,
    _task_terminal_field_material_review_decision_source_from_payloads,
    summarize_task_terminal_completion_mainline,
    summarize_task_terminal_field_material_intake,
    summarize_task_terminal_field_material_review_decision,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_run import (
    ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_GATE,
    ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SCHEMA,
    ROUTE_TASK_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_INTAKE_GATE,
    ROUTE_TASK_FIELD_RUN_INTAKE_SCHEMA,
    ROUTE_TASK_FIELD_RUN_INTAKE_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_READINESS_GATE,
    ROUTE_TASK_FIELD_RUN_READINESS_SCHEMA,
    ROUTE_TASK_FIELD_RUN_READINESS_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_REVIEW_GATE,
    ROUTE_TASK_FIELD_RUN_REVIEW_SCHEMA,
    ROUTE_TASK_FIELD_RUN_REVIEW_SUMMARY_SCHEMA,
    _default_route_task_field_run_execution_pack_summary,
    _default_route_task_field_run_intake_summary,
    _default_route_task_field_run_readiness_summary,
    _default_route_task_field_run_review_summary,
    _route_task_field_run_execution_pack_not_proven,
    _route_task_field_run_intake_has_unsafe_control_claims,
    _route_task_field_run_intake_not_proven,
    _route_task_field_run_readiness_copy_is_unsafe,
    _route_task_field_run_readiness_has_unsafe_fields,
    _route_task_field_run_readiness_not_proven,
    _route_task_field_run_review_not_proven,
    summarize_route_task_field_run_execution_pack,
    summarize_route_task_field_run_intake,
    summarize_route_task_field_run_readiness,
    summarize_route_task_field_run_review,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_field_artifacts import (
    ROUTE_TASK_FIELD_RUN_CONSOLE_GATE,
    ROUTE_TASK_FIELD_RUN_CONSOLE_SCHEMA,
    ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_GATE,
    ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SCHEMA,
    ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_GATE,
    ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SCHEMA,
    ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_GATE,
    ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA,
    ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA,
    ROUTE_TASK_FIELD_RUN_RECONCILIATION_GATE,
    ROUTE_TASK_FIELD_RUN_RECONCILIATION_SCHEMA,
    ROUTE_TASK_FIELD_RUN_RECONCILIATION_SUMMARY_SCHEMA,
    _default_route_task_field_run_console_summary,
    _default_route_task_field_run_evidence_kit_summary,
    _default_route_task_field_run_material_bundle_summary,
    _default_route_task_field_run_material_validation_summary,
    _default_route_task_field_run_reconciliation_summary,
    _route_task_field_run_console_has_unsafe_fields,
    _route_task_field_run_console_not_proven,
    _route_task_field_run_evidence_kit_not_proven,
    _route_task_field_run_evidence_kit_source_contract,
    _route_task_field_run_material_bundle_not_proven,
    _route_task_field_run_material_bundle_source_contract,
    _route_task_field_run_material_validation_not_proven,
    _route_task_field_run_material_validation_source_contract,
    _route_task_field_run_reconciliation_not_proven,
    summarize_route_task_field_run_console,
    summarize_route_task_field_run_evidence_kit,
    summarize_route_task_field_run_material_bundle,
    summarize_route_task_field_run_material_validation,
    summarize_route_task_field_run_reconciliation,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_elevator_proof import *
from ros2_trashbot_behavior.operator_gateway_diagnostics_elevator_field_run import (
    ELEVATOR_FIELD_RUN_EXECUTION_PACK_GATE,
    ELEVATOR_FIELD_RUN_EXECUTION_PACK_SCHEMA,
    ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_GATE,
    ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SCHEMA,
    ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_RUN_REVIEW_GATE,
    ELEVATOR_FIELD_RUN_REVIEW_SCHEMA,
    ELEVATOR_FIELD_RUN_REVIEW_SUMMARY_SCHEMA,
    _default_elevator_field_run_execution_pack_summary,
    _default_elevator_field_run_material_validation_summary,
    _default_elevator_field_run_review_summary,
    _elevator_field_run_execution_pack_not_proven,
    _elevator_field_run_execution_pack_source_contract,
    _elevator_field_run_material_validation_not_proven,
    _elevator_field_run_material_validation_source_contract,
    _elevator_field_run_review_not_proven,
    _elevator_field_run_review_source_contract,
    summarize_elevator_field_run_execution_pack,
    summarize_elevator_field_run_material_validation,
    summarize_elevator_field_run_review,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_elevator_field_evidence_trace import (
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_GATE,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_ROBOT_SUMMARY_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SCHEMA,
    ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    _default_elevator_field_evidence_trace_callback_intake_summary,
    _default_elevator_field_evidence_trace_callback_review_decision_summary,
    _default_elevator_field_evidence_trace_callback_review_handoff_summary,
    _default_elevator_field_evidence_trace_material_backfill_intake_summary,
    _default_elevator_field_evidence_trace_material_backfill_review_decision_summary,
    _default_elevator_field_evidence_trace_material_backfill_review_handoff_summary,
    _elevator_field_evidence_trace_callback_intake_has_disabled_actions,
    _elevator_field_evidence_trace_callback_intake_has_unsafe_fields,
    _elevator_field_evidence_trace_callback_intake_not_proven,
    _elevator_field_evidence_trace_callback_intake_source_contract,
    _elevator_field_evidence_trace_callback_review_decision_has_unsafe_fields,
    _elevator_field_evidence_trace_callback_review_decision_not_proven,
    _elevator_field_evidence_trace_callback_review_decision_source_contract,
    _elevator_field_evidence_trace_callback_review_handoff_has_unsafe_fields,
    _elevator_field_evidence_trace_callback_review_handoff_not_proven,
    _elevator_field_evidence_trace_callback_review_handoff_source_contract,
    _elevator_field_evidence_trace_material_backfill_intake_has_unsafe_fields,
    _elevator_field_evidence_trace_material_backfill_intake_not_proven,
    _elevator_field_evidence_trace_material_backfill_intake_source_contract,
    _elevator_field_evidence_trace_material_backfill_review_decision_has_unsafe_fields,
    _elevator_field_evidence_trace_material_backfill_review_decision_not_proven,
    _elevator_field_evidence_trace_material_backfill_review_decision_source_contract,
    _elevator_field_evidence_trace_material_backfill_review_handoff_has_unsafe_fields,
    _elevator_field_evidence_trace_material_backfill_review_handoff_not_proven,
    _elevator_field_evidence_trace_material_backfill_review_handoff_source_contract,
    summarize_elevator_field_evidence_trace_callback_intake,
    summarize_elevator_field_evidence_trace_callback_review_decision,
    summarize_elevator_field_evidence_trace_callback_review_handoff,
    summarize_elevator_field_evidence_trace_material_backfill_intake,
    summarize_elevator_field_evidence_trace_material_backfill_review_decision,
    summarize_elevator_field_evidence_trace_material_backfill_review_handoff,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_elevator_field_session import (
    ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_GATE,
    ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SCHEMA,
    ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY_SCHEMA,
    _default_route_elevator_field_session_handoff_summary,
    _route_elevator_field_session_handoff_has_disabled_actions,
    _route_elevator_field_session_handoff_not_proven,
    _route_elevator_field_session_handoff_requires_same_evidence_ref,
    _route_elevator_field_session_handoff_source_contract,
    summarize_route_elevator_field_session_handoff,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_mobile_field import (
    MOBILE_FIELD_MATERIAL_INTAKE_GATE,
    MOBILE_FIELD_MATERIAL_INTAKE_SCHEMA,
    MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY_SCHEMA,
    MOBILE_FIELD_MATERIAL_RETEST_REQUEST_GATE,
    MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SCHEMA,
    MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY_SCHEMA,
    MOBILE_FIELD_MATERIAL_REVIEW_DECISION_GATE,
    MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SCHEMA,
    MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_GATE,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA,
    MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_GATE,
    MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SCHEMA,
    MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY_SCHEMA,
    _default_mobile_field_material_intake_summary,
    _default_mobile_field_material_retest_request_summary,
    _default_mobile_field_material_review_decision_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary,
    _default_mobile_real_device_field_trial_acceptance_execution_pack_summary,
    _default_mobile_real_device_field_trial_acceptance_review_handoff_summary,
    _default_mobile_route_elevator_field_device_precheck_summary,
    _mobile_field_material_intake_has_unsafe_fields,
    _mobile_field_material_intake_not_proven,
    _mobile_field_material_intake_source_contract,
    _mobile_field_material_retest_request_not_proven,
    _mobile_field_material_retest_request_source_contract,
    _mobile_field_material_review_decision_not_proven,
    _mobile_field_material_review_decision_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_callback_intake_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_callback_intake_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_handoff_intake_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_has_unsafe_copy,
    _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_contract,
    _mobile_real_device_field_trial_acceptance_execution_pack_not_proven,
    _mobile_real_device_field_trial_acceptance_execution_pack_source_contract,
    _mobile_real_device_field_trial_acceptance_review_handoff_not_proven,
    _mobile_real_device_field_trial_acceptance_review_handoff_source_contract,
    _mobile_route_elevator_field_device_precheck_has_unsafe_fields,
    _mobile_route_elevator_field_device_precheck_not_proven,
    _mobile_route_elevator_field_device_precheck_source_contract,
    summarize_mobile_field_material_intake,
    summarize_mobile_field_material_retest_request,
    summarize_mobile_field_material_review_decision,
    summarize_mobile_real_device_field_trial_acceptance_execution_callback_intake,
    summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_decision,
    summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff,
    summarize_mobile_real_device_field_trial_acceptance_execution_handoff_intake,
    summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision,
    summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff,
    summarize_mobile_real_device_field_trial_acceptance_execution_pack,
    summarize_mobile_real_device_field_trial_acceptance_review_handoff,
    summarize_mobile_route_elevator_field_device_precheck,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_field_evidence_rerun import (
    FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SCHEMA,
    FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_GATE,
    FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_QUEUE_SCHEMA,
    FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_QUEUE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_PACK_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_STATUSES,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_GATE,
    FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_OWNER_RESPONSE_INTAKE_BRIDGE_SOURCE,
    _field_evidence_rerun_material_dispatch_not_proven,
    _field_evidence_rerun_callback_intake_not_proven,
    _field_evidence_rerun_callback_review_decision_not_proven,
    _field_evidence_rerun_callback_review_handoff_not_proven,
    _field_evidence_rerun_handoff_intake_not_proven,
    _field_evidence_rerun_queue_not_proven,
    _field_evidence_rerun_execution_pack_not_proven,
    _field_evidence_rerun_execution_callback_intake_not_proven,
    _field_evidence_rerun_execution_callback_review_decision_not_proven,
    _field_evidence_rerun_execution_callback_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_intake_not_proven,
    _field_evidence_rerun_execution_result_review_decision_not_proven,
    _field_evidence_rerun_execution_result_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_acceptance_packet_not_proven,
    _field_evidence_rerun_execution_result_acceptance_backfill_not_proven,
    _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_not_proven,
    _field_evidence_rerun_execution_result_acceptance_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_not_proven,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_not_proven,
    _default_field_evidence_rerun_material_dispatch_summary,
    _default_field_evidence_rerun_callback_intake_summary,
    _default_field_evidence_rerun_callback_review_decision_summary,
    _default_field_evidence_rerun_callback_review_handoff_summary,
    _default_field_evidence_rerun_handoff_intake_summary,
    _default_field_evidence_rerun_queue_summary,
    _default_field_evidence_rerun_execution_pack_summary,
    _default_field_evidence_rerun_execution_callback_intake_summary,
    _default_field_evidence_rerun_execution_callback_review_decision_summary,
    _default_field_evidence_rerun_execution_callback_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_intake_summary,
    _default_field_evidence_rerun_execution_result_review_decision_summary,
    _default_field_evidence_rerun_execution_result_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_acceptance_packet_summary,
    _default_field_evidence_rerun_execution_result_acceptance_backfill_summary,
    _default_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary,
    _default_field_evidence_rerun_execution_result_acceptance_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary,
    _default_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary,
    _field_evidence_rerun_material_dispatch_source_contract,
    _field_evidence_rerun_callback_intake_source_contract,
    _field_evidence_rerun_callback_review_decision_source_contract,
    _field_evidence_rerun_callback_review_handoff_source_contract,
    _field_evidence_rerun_handoff_intake_source_contract,
    _field_evidence_rerun_queue_source_contract,
    _field_evidence_rerun_execution_pack_source_contract,
    _field_evidence_rerun_execution_callback_intake_source_contract,
    _field_evidence_rerun_execution_callback_review_decision_source_contract,
    _field_evidence_rerun_handoff_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_pack_has_unsafe_fields,
    _field_evidence_rerun_execution_callback_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_callback_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_intake_source_contract,
    _field_evidence_rerun_execution_result_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_result_review_decision_source_contract,
    _field_evidence_rerun_execution_result_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_review_handoff_source_contract,
    _field_evidence_rerun_execution_result_review_handoff_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_packet_source_contract,
    _field_evidence_rerun_execution_result_acceptance_backfill_source_contract,
    _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_source_contract,
    _field_evidence_rerun_execution_result_acceptance_review_handoff_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source_contract,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source_contract,
    _field_evidence_rerun_execution_result_acceptance_packet_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_backfill_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_backfill_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_review_handoff_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_has_unsafe_fields,
    _field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_has_unsafe_fields,
    summarize_field_evidence_rerun_material_dispatch,
    _field_evidence_rerun_callback_intake_material_counts,
    summarize_field_evidence_rerun_callback_intake,
    summarize_field_evidence_rerun_callback_review_decision,
    summarize_field_evidence_rerun_callback_review_handoff,
    summarize_field_evidence_rerun_handoff_intake,
    summarize_field_evidence_rerun_queue,
    summarize_field_evidence_rerun_execution_pack,
    summarize_field_evidence_rerun_execution_callback_intake,
    summarize_field_evidence_rerun_execution_callback_review_decision,
    summarize_field_evidence_rerun_execution_callback_review_handoff,
    summarize_field_evidence_rerun_execution_result_intake,
    summarize_field_evidence_rerun_execution_result_review_decision,
    summarize_field_evidence_rerun_execution_result_review_handoff,
    summarize_field_evidence_rerun_execution_result_acceptance_packet,
    summarize_field_evidence_rerun_execution_result_acceptance_backfill,
    summarize_field_evidence_rerun_execution_result_acceptance_backfill_review_decision,
    summarize_field_evidence_rerun_execution_result_acceptance_review_handoff,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff,
    summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status,
    _execution_callback_review_handoff_replace,
    _EXECUTION_CALLBACK_REVIEW_HANDOFF_TO_BASE_HANDOFF,
    _BASE_HANDOFF_TO_EXECUTION_CALLBACK_REVIEW_HANDOFF,
    _strip_execution_callback_review_handoff_forbidden_terms,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_field_evidence_material import (
    FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_REQUIRED_MATERIALS,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_STATUSES,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_VALUES,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_GATE,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_DECISIONS,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_DECISIONS,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_REVIEWER_ACK_BRIDGE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISIONS,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISIONS,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_STATUSES,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SOURCE_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY_SCHEMA,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_GATE,
    FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUSES,
    _field_evidence_real_material_request_dispatch_not_proven,
    _field_evidence_real_material_response_intake_not_proven,
    _field_evidence_real_material_response_review_decision_not_proven,
    _field_evidence_real_material_response_review_handoff_not_proven,
    _field_evidence_real_material_followup_escalation_status_not_proven,
    _default_field_evidence_real_material_request_dispatch_summary,
    _default_field_evidence_real_material_response_intake_summary,
    _default_field_evidence_real_material_response_review_decision_summary,
    _default_field_evidence_real_material_response_review_handoff_summary,
    _default_field_evidence_real_material_followup_escalation_status_summary,
    _field_evidence_real_material_owner_ack_intake_not_proven,
    _field_evidence_real_material_owner_ack_review_decision_not_proven,
    _field_evidence_material_blocker_escalation_pack_not_proven,
    _field_evidence_material_resolution_intake_not_proven,
    _field_evidence_material_resolution_review_decision_not_proven,
    _field_evidence_material_resolution_review_handoff_not_proven,
    _field_evidence_material_resolution_followup_escalation_status_not_proven,
    _field_evidence_material_resolution_owner_response_intake_not_proven,
    _field_evidence_material_resolution_owner_response_review_decision_not_proven,
    _field_evidence_material_resolution_owner_response_review_handoff_not_proven,
    _field_evidence_material_resolution_reviewer_ack_intake_not_proven,
    _field_evidence_material_resolution_reviewer_ack_review_decision_not_proven,
    _field_evidence_material_resolution_reviewer_ack_review_handoff_not_proven,
    _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_not_proven,
    _default_field_evidence_real_material_owner_ack_intake_summary,
    _default_field_evidence_real_material_owner_ack_review_decision_summary,
    _default_field_evidence_material_blocker_escalation_pack_summary,
    _default_field_evidence_material_resolution_intake_summary,
    _default_field_evidence_material_resolution_review_decision_summary,
    _default_field_evidence_material_resolution_review_handoff_summary,
    _default_field_evidence_material_resolution_followup_escalation_status_summary,
    _default_field_evidence_material_resolution_owner_response_intake_summary,
    _default_field_evidence_material_resolution_owner_response_review_decision_summary,
    _default_field_evidence_material_resolution_owner_response_review_handoff_summary,
    _default_field_evidence_material_resolution_reviewer_ack_intake_summary,
    _default_field_evidence_material_resolution_reviewer_ack_review_decision_summary,
    _default_field_evidence_material_resolution_reviewer_ack_review_handoff_summary,
    _default_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary,
    _field_evidence_real_material_request_dispatch_source_contract,
    _field_evidence_real_material_response_intake_source_contract,
    _field_evidence_real_material_response_review_decision_source_contract,
    _field_evidence_real_material_response_review_handoff_source_contract,
    _field_evidence_real_material_followup_escalation_status_source_contract,
    _field_evidence_real_material_owner_ack_intake_source_contract,
    _field_evidence_real_material_owner_ack_review_decision_source_contract,
    _field_evidence_material_blocker_escalation_pack_source_contract,
    _field_evidence_material_resolution_intake_source_contract,
    _field_evidence_material_resolution_review_decision_source_contract,
    _field_evidence_material_resolution_review_handoff_source_contract,
    _field_evidence_material_resolution_followup_escalation_status_source_contract,
    _field_evidence_material_resolution_owner_response_intake_source_contract,
    _field_evidence_material_resolution_owner_response_review_decision_source_contract,
    _field_evidence_material_resolution_owner_response_review_handoff_source_contract,
    _field_evidence_material_resolution_reviewer_ack_intake_source_contract,
    _field_evidence_material_resolution_reviewer_ack_review_decision_source_contract,
    _field_evidence_material_resolution_reviewer_ack_review_handoff_source_contract,
    _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source_contract,
    _field_evidence_material_blocker_escalation_pack_has_unsafe_fields,
    _field_evidence_material_resolution_intake_has_unsafe_fields,
    _field_evidence_material_resolution_review_decision_has_unsafe_fields,
    _field_evidence_material_resolution_review_handoff_has_unsafe_fields,
    _field_evidence_material_resolution_followup_escalation_status_has_unsafe_fields,
    _field_evidence_material_resolution_owner_response_intake_has_unsafe_fields,
    _field_evidence_material_resolution_owner_response_review_decision_has_unsafe_fields,
    _field_evidence_material_resolution_owner_response_review_handoff_has_unsafe_fields,
    _field_evidence_material_resolution_reviewer_ack_intake_has_unsafe_fields,
    _field_evidence_material_resolution_reviewer_ack_review_decision_has_unsafe_fields,
    _field_evidence_material_resolution_reviewer_ack_review_handoff_has_unsafe_fields,
    _field_evidence_material_resolution_reviewer_ack_followup_escalation_status_has_unsafe_fields,
    _field_evidence_real_material_owner_ack_intake_has_unsafe_fields,
    _field_evidence_real_material_request_dispatch_has_unsafe_fields,
    _field_evidence_real_material_response_intake_has_unsafe_fields,
    _field_evidence_real_material_owner_ack_review_decision_has_unsafe_fields,
    _field_evidence_real_material_response_review_decision_has_unsafe_fields,
    _field_evidence_real_material_response_review_handoff_has_unsafe_fields,
    summarize_field_evidence_real_material_request_dispatch,
    summarize_field_evidence_real_material_response_intake,
    summarize_field_evidence_real_material_response_review_decision,
    summarize_field_evidence_real_material_response_review_handoff,
    summarize_field_evidence_real_material_followup_escalation_status,
    summarize_field_evidence_real_material_owner_ack_intake,
    summarize_field_evidence_real_material_owner_ack_review_decision,
    summarize_field_evidence_material_blocker_escalation_pack,
    summarize_field_evidence_material_resolution_intake,
    summarize_field_evidence_material_resolution_review_decision,
    summarize_field_evidence_material_resolution_review_handoff,
    summarize_field_evidence_material_resolution_followup_escalation_status,
    summarize_field_evidence_material_resolution_owner_response_intake,
    summarize_field_evidence_material_resolution_owner_response_review_decision,
    summarize_field_evidence_material_resolution_owner_response_review_handoff,
    summarize_field_evidence_material_resolution_reviewer_ack_intake,
    summarize_field_evidence_material_resolution_reviewer_ack_review_decision,
    summarize_field_evidence_material_resolution_reviewer_ack_review_handoff,
    summarize_field_evidence_material_resolution_reviewer_ack_followup_escalation_status,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_route_terminal import (
    ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_GATE,
    ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SCHEMA,
    ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY_SCHEMA,
    ROUTE_TASK_TERMINAL_REVIEW_DECISION_GATE,
    ROUTE_TASK_TERMINAL_REVIEW_DECISION_SCHEMA,
    ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY_SCHEMA,
    _default_route_task_terminal_completion_rehearsal_summary,
    _default_route_task_terminal_review_decision_summary,
    _route_task_terminal_completion_evidence_refs_match,
    _route_task_terminal_completion_rehearsal_not_proven,
    _route_task_terminal_review_decision_evidence_refs_match,
    _route_task_terminal_review_decision_not_proven,
    _route_task_terminal_review_decision_source_contract,
    summarize_route_task_terminal_completion_rehearsal,
    summarize_route_task_terminal_review_decision,
)
from ros2_trashbot_behavior.remote_cloud_relay import (
    build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_payload,
    build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_payload,
    build_phone_credential_rotation_summary,
    build_phone_network_recovery_summary,
    build_phone_oss_cdn_manifest_summary,
    build_phone_production_store_queue_summary,
    build_phone_production_recovery_summary,
    build_phone_provisioning_audit_summary,
    build_phone_queue_ordering_drill_summary,
    build_phone_transaction_isolation_summary,
)

from ros2_trashbot_behavior.operator_gateway_diagnostics_vision_review import (
    LOW_CONFIDENCE_REVIEW_THRESHOLD,
    REVIEW_DECISION_ORDER,
    REVIEW_DECISION_VALUES,
    REVIEW_QUEUE_LIMIT,
    _review_decision_distribution,
    build_vision_review_queue,
    default_integrity_fields,
    integrity_status,
    sample_event_type,
    sample_review_reason,
    summarize_review_progress,
    summarize_vision_manifest,
    vision_manifest_integrity_fields,
    vision_sample_review_item,
)
from ros2_trashbot_behavior.operator_gateway_diagnostics_common import (
    HARDWARE_PROOF_STATUSES,
    _default_hardware_proof_summary,
    _hardware_proof_risk_text,
    _has_hil_risk,
    _task_terminal_field_material_intake_copy_is_unsafe,
    default_review_decision_log,
    load_review_decision_log,
    normalize_log_refs,
    review_decision_entry,
    safe_int,
    summarize_hardware_proof,
)



# 默认 summary helper 与安全 copy 判定已迁入 canonical 领域模块；payload 模块直接使用 common 定义。


def _drop_safe_alias_inputs(latest_status, *keys, diagnostics_source=None):
    # diagnostics builder 会重新生成 canonical safe alias；旧状态文件里的同名对象可能是 raw/source wrapper。
    # 集中清理能让后续新增手机面板时复用同一条 fail-closed 规则，避免误把 not-proven 写成 proven。
    if isinstance(latest_status, dict):
        for key in keys:
            latest_status.pop(key, None)
    if isinstance(diagnostics_source, dict):
        for key in keys:
            diagnostics_source.pop(key, None)


def build_diagnostics_payload(
    latest_status,
    *,
    software_version,
    map_version,
    route_version,
    log_refs,
    vision_sample_manifest_ref,
    review_decision_log_ref,
    operator_status_file,
    hardware_proof_ref="",
    oss_cdn_manifest_artifact_ref="",
    network_recovery_artifact_ref="",
    credential_rotation_artifact_ref="",
    provisioning_audit_artifact_ref="",
    production_store_queue_artifact_ref="",
    queue_ordering_drill_artifact_ref="",
    transaction_isolation_artifact_ref="",
    production_recovery_artifact_ref="",
    cloud_worker_migration_rehearsal_artifact_ref="",
    cloud_worker_cutover_drain_artifact_ref="",
    route_task_rehearsal_artifact_ref="",
    route_task_rehearsal_bundle_ref="",
    route_task_rehearsal_operator_review_ref="",
    pc_route_debug_console_ref="",
    route_task_field_run_readiness_ref="",
    route_task_field_run_intake_ref="",
    route_task_field_run_review_ref="",
    route_task_field_run_execution_pack_ref="",
    route_task_field_retest_execution_pack_ref="",
    route_task_field_retest_session_handoff_ref="",
    route_task_field_retest_result_intake_ref="",
    route_task_field_retest_result_reconciliation_ref="",
    route_task_field_retest_material_pack_ref="",
    route_task_field_retest_material_callback_packet_ref="",
    route_task_field_retest_material_callback_review_decision_ref="",
    route_task_field_retest_operator_drill_ref="",
    route_task_field_retest_drill_console_ref="",
    route_task_field_retest_acceptance_brief_ref="",
    route_task_field_retest_acceptance_review_decision_ref="",
    route_task_field_retest_acceptance_execution_pack_ref="",
    route_task_field_retest_acceptance_execution_callback_intake_ref="",
    route_task_field_retest_acceptance_execution_callback_review_decision_ref="",
    route_task_field_retest_acceptance_execution_callback_review_handoff_ref="",
    route_task_field_retest_acceptance_execution_handoff_intake_ref="",
    route_task_field_retest_acceptance_execution_rerun_queue_ref="",
    route_task_field_retest_acceptance_execution_rerun_result_intake_ref="",
    route_task_field_retest_acceptance_execution_rerun_result_review_decision_ref="",
    route_task_field_retest_acceptance_execution_rerun_result_review_handoff_ref="",
    field_evidence_rerun_material_dispatch_ref="",
    field_evidence_rerun_callback_intake_ref="",
    field_evidence_rerun_callback_review_decision_ref="",
    field_evidence_rerun_callback_review_handoff_ref="",
    field_evidence_rerun_handoff_intake_ref="",
    field_evidence_rerun_queue_ref="",
    field_evidence_rerun_execution_pack_ref="",
    field_evidence_rerun_execution_callback_intake_ref="",
    field_evidence_rerun_execution_callback_review_decision_ref="",
    field_evidence_rerun_execution_callback_review_handoff_ref="",
    field_evidence_rerun_execution_result_intake_ref="",
    field_evidence_rerun_execution_result_review_decision_ref="",
    field_evidence_rerun_execution_result_review_handoff_ref="",
    field_evidence_rerun_execution_result_acceptance_packet_ref="",
    field_evidence_rerun_execution_result_acceptance_backfill_ref="",
    field_evidence_rerun_execution_result_acceptance_backfill_review_decision_ref="",
    field_evidence_rerun_execution_result_acceptance_review_handoff_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_ref="",
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_ref="",
    field_evidence_real_material_request_dispatch_ref="",
    field_evidence_real_material_response_intake_ref="",
    field_evidence_real_material_response_review_decision_ref="",
    field_evidence_real_material_response_review_handoff_ref="",
    route_task_field_retest_evidence_dispatch_ref="",
    route_task_field_retest_callback_intake_ref="",
    route_task_field_retest_callback_review_decision_ref="",
    route_task_field_retest_review_result_handoff_ref="",
    route_task_field_retest_result_acceptance_packet_ref="",
    route_task_field_retest_result_acceptance_backfill_ref="",
    route_task_field_retest_result_backfill_review_decision_ref="",
    route_task_field_retest_result_review_dispatch_ref="",
    route_task_field_retest_result_review_intake_ref="",
    route_task_field_retest_result_review_decision_ref="",
    route_task_field_retest_result_review_handoff_ref="",
    route_task_field_retest_result_callback_intake_ref="",
    route_task_field_retest_result_callback_review_decision_ref="",
    route_task_field_retest_result_callback_review_handoff_ref="",
    route_task_field_run_reconciliation_ref="",
    route_task_completion_signal_ref="",
    route_task_terminal_completion_rehearsal_ref="",
    route_task_terminal_review_decision_ref="",
    route_task_field_run_console_ref="",
    route_task_field_run_evidence_kit_ref="",
    route_task_field_run_material_bundle_ref="",
    route_task_field_run_material_validation_ref="",
    elevator_field_run_material_validation_ref="",
    elevator_field_run_review_ref="",
    elevator_field_run_execution_pack_ref="",
    elevator_route_evidence_reconciliation_ref="",
    route_elevator_field_session_handoff_ref="",
    mobile_route_elevator_field_device_precheck_ref="",
    mobile_field_material_intake_ref="",
    mobile_field_material_review_decision_ref="",
    mobile_field_material_retest_request_ref="",
    mobile_real_device_field_trial_acceptance_review_handoff_ref="",
    mobile_real_device_field_trial_acceptance_execution_pack_ref="",
    mobile_real_device_field_trial_acceptance_execution_callback_intake_ref="",
    mobile_real_device_field_trial_acceptance_execution_callback_review_decision_ref="",
    mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_ref="",
    mobile_real_device_field_trial_acceptance_execution_handoff_intake_ref="",
    mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_ref="",
    mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_ref="",
    wave_rover_feedback_replay_ref="",
    wave_rover_hil_packet_intake_ref="",
    wave_rover_hil_packet_review_decision_ref="",
    wave_rover_hil_packet_execution_pack_ref="",
    wave_rover_hil_packet_collection_drill_ref="",
    hardware_baseline_review_ref="",
    hardware_baseline_source_alignment_ref="",
    hardware_sensor_procurement_intake_ref="",
    hardware_sensor_procurement_review_decision_ref="",
    hardware_sensor_procurement_execution_pack_ref="",
    hardware_sensor_procurement_receipt_intake_ref="",
    hardware_sensor_hil_entry_config_precheck_ref="",
    hardware_sensor_hil_entry_readiness_review_ref="",
    hardware_sensor_hil_entry_execution_pack_ref="",
    hardware_sensor_hil_entry_callback_intake_ref="",
    hardware_sensor_hil_entry_callback_review_decision_ref="",
    hardware_sensor_hil_entry_callback_review_handoff_ref="",
    pr5_review_thread_closeout_ref="",
    pr5_vendor_source_review_packet_ref="",
    pr5_vendor_source_review_reply_dispatch_ref="",
    pr5_mandatory_sensor_source_alignment_ref="",
    pr5_mandatory_sensor_material_followup_escalation_status_ref="",
    pr5_mandatory_sensor_material_owner_response_intake_ref="",
    pr5_mandatory_sensor_material_owner_response_review_decision_ref="",
    pr5_mandatory_sensor_material_owner_response_review_handoff_ref="",
    pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_ref="",
    hardware_real_material_escalation_request_ref="",
    real_material_readiness_board_ref="",
    real_material_evidence_intake_ref="",
    verified_terminal_result_material_intake_ref="",
    verified_terminal_result_material_review_decision_ref="",
    verified_terminal_result_material_review_handoff_ref="",
    verified_terminal_result_material_followup_escalation_status_ref="",
    verified_terminal_result_material_owner_response_intake_ref="",
    verified_terminal_result_material_owner_response_review_decision_ref="",
    verified_terminal_result_material_owner_response_review_handoff_ref="",
    verified_terminal_result_material_owner_response_reviewer_ack_intake_ref="",
    verified_terminal_result_material_owner_response_reviewer_ack_review_decision_ref="",
    verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_ref="",
    verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_ref="",
    real_material_followup_escalation_status_ref="",
    field_evidence_real_material_followup_escalation_status_ref="",
    field_evidence_real_material_owner_ack_intake_ref="",
    field_evidence_real_material_owner_ack_review_decision_ref="",
    field_evidence_material_blocker_escalation_pack_ref="",
    field_evidence_material_resolution_intake_ref="",
    field_evidence_material_resolution_review_decision_ref="",
    field_evidence_material_resolution_review_handoff_ref="",
    field_evidence_material_resolution_followup_escalation_status_ref="",
    field_evidence_material_resolution_owner_response_intake_ref="",
    field_evidence_material_resolution_owner_response_review_decision_ref="",
    field_evidence_material_resolution_owner_response_review_handoff_ref="",
    field_evidence_material_resolution_reviewer_ack_intake_ref="",
    field_evidence_material_resolution_reviewer_ack_review_decision_ref="",
    field_evidence_material_resolution_reviewer_ack_review_handoff_ref="",
    field_evidence_material_resolution_reviewer_ack_followup_escalation_status_ref="",
    elevator_field_evidence_trace_callback_intake_ref="",
    elevator_field_evidence_trace_callback_review_decision_ref="",
    elevator_field_evidence_trace_callback_review_handoff_ref="",
    elevator_field_evidence_trace_material_backfill_intake_ref="",
    elevator_field_evidence_trace_material_backfill_review_decision_ref="",
    elevator_field_evidence_trace_material_backfill_review_handoff_ref="",
):
    latest_status = dict(latest_status or {})
    diagnostics_source = latest_status.get("diagnostics") if isinstance(latest_status.get("diagnostics"), dict) else {}
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff"
            ),
            dict,
        )
        else {}
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake"
            ),
            dict,
        )
        else {}
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision"
            ),
            dict,
        )
        else {}
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff"
            ),
            dict,
        )
        else {}
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status"
            ),
            dict,
        )
        else {}
    )
    field_evidence_real_material_response_intake_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_real_material_response_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_real_material_response_intake_summary"
            ),
            dict,
        )
        else latest_status.get("field_evidence_real_material_response_intake_summary")
        if isinstance(
            latest_status.get("field_evidence_real_material_response_intake_summary"),
            dict,
        )
        else latest_status.get("field_evidence_real_material_response_intake")
        if isinstance(latest_status.get("field_evidence_real_material_response_intake"), dict)
        else {}
    )
    field_evidence_real_material_response_review_decision_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_real_material_response_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_real_material_response_review_decision_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_real_material_response_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_real_material_response_review_decision_summary"
            ),
            dict,
        )
        else latest_status.get("field_evidence_real_material_response_review_decision")
        if isinstance(
            latest_status.get("field_evidence_real_material_response_review_decision"),
            dict,
        )
        else {}
    )
    field_evidence_real_material_response_review_handoff_preserved_source = (
        latest_status.get(
            "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "field_evidence_real_material_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "field_evidence_real_material_response_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get("field_evidence_real_material_response_review_handoff")
        if isinstance(
            latest_status.get("field_evidence_real_material_response_review_handoff"),
            dict,
        )
        else {}
    )
    field_evidence_real_material_owner_ack_intake_preserved_keys = (
        "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary",
        "field_evidence_real_material_owner_ack_intake_summary",
        "field_evidence_real_material_owner_ack_intake",
    )
    field_evidence_real_material_owner_ack_review_decision_preserved_keys = (
        "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary",
        "field_evidence_real_material_owner_ack_review_decision_summary",
        "field_evidence_real_material_owner_ack_review_decision",
    )
    # Owner ACK preserved source 保留旧 alias 顺序，避免 raw artifact 抢占 robot summary。
    field_evidence_real_material_owner_ack_intake_preserved_source = first_status_dict(
        latest_status,
        diagnostics_source,
        field_evidence_real_material_owner_ack_intake_preserved_keys,
        default={},
    )
    # review decision 与 intake 使用同一字段级边界，不加入整包 diagnostics 兜底。
    field_evidence_real_material_owner_ack_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            field_evidence_real_material_owner_ack_review_decision_preserved_keys,
            default={},
        )
    )
    field_evidence_material_blocker_escalation_pack_preserved_keys = (
        "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary",
        "field_evidence_material_blocker_escalation_pack_summary",
        "field_evidence_material_blocker_escalation_pack",
    )
    # Blocker escalation pack 只收字段级来源，避免整包 diagnostics 被误当作物料证据。
    field_evidence_material_blocker_escalation_pack_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            field_evidence_material_blocker_escalation_pack_preserved_keys,
            default={},
        )
    )
    field_evidence_material_resolution_intake_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_intake_summary",
                "field_evidence_material_resolution_intake_summary",
                "field_evidence_material_resolution_intake",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_review_decision_summary",
                "field_evidence_material_resolution_review_decision_summary",
                "field_evidence_material_resolution_review_decision",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_review_handoff_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary",
                "field_evidence_material_resolution_review_handoff_summary",
                "field_evidence_material_resolution_review_handoff",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_followup_escalation_status_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary",
                "field_evidence_material_resolution_followup_escalation_status_summary",
                "field_evidence_material_resolution_followup_escalation_status",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_owner_response_intake_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary",
                "field_evidence_material_resolution_owner_response_intake_summary",
                "field_evidence_material_resolution_owner_response_intake",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_owner_response_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary",
                "field_evidence_material_resolution_owner_response_review_decision_summary",
                "field_evidence_material_resolution_owner_response_review_decision",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_owner_response_review_handoff_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            (
                "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary",
                "field_evidence_material_resolution_owner_response_review_handoff_summary",
                "field_evidence_material_resolution_owner_response_review_handoff",
            ),
            default={},
        )
    )
    field_evidence_material_resolution_reviewer_ack_intake_preserved_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_intake_summary"
            ),
            latest_status.get("field_evidence_material_resolution_reviewer_ack_intake"),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_intake"
            ),
            default={},
        )
    )
    field_evidence_material_resolution_reviewer_ack_review_decision_preserved_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_review_decision"
            ),
            default={},
        )
    )
    field_evidence_material_resolution_reviewer_ack_review_handoff_preserved_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_review_handoff"
            ),
            default={},
        )
    )
    field_evidence_material_resolution_reviewer_ack_followup_escalation_status_preserved_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary"
            ),
            latest_status.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
            ),
            diagnostics_source.get(
                "field_evidence_material_resolution_reviewer_ack_followup_escalation_status"
            ),
            default={},
        )
    )
    verified_terminal_result_material_intake_keys = (
        "robot_diagnostics_verified_terminal_result_material_intake_summary",
        "verified_terminal_result_material_intake_summary",
        "verified_terminal_result_material_intake",
    )
    # 旧 intake 链路允许把整个 diagnostics_source 当 preserved-source 兜底；
    # 保留这个兜底是为了兼容历史调用方只传诊断对象、不传细分 alias 的场景。
    verified_terminal_result_material_intake_preserved_source = first_status_dict(
        latest_status,
        diagnostics_source,
        verified_terminal_result_material_intake_keys,
        fallback_to_diagnostics_source=True,
        default={},
    )
    verified_terminal_result_material_review_decision_keys = (
        "robot_diagnostics_verified_terminal_result_material_review_decision_summary",
        "verified_terminal_result_material_review_decision_summary",
        "verified_terminal_result_material_review_decision",
    )
    # review_decision 与 intake 使用同一历史兜底语义，避免旧诊断快照丢失来源。
    verified_terminal_result_material_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_review_decision_keys,
            fallback_to_diagnostics_source=True,
            default={},
        )
    )
    verified_terminal_result_material_review_handoff_keys = (
        "robot_diagnostics_verified_terminal_result_material_review_handoff_summary",
        "verified_terminal_result_material_review_handoff_summary",
        "verified_terminal_result_material_review_handoff",
    )
    # review_handoff 也保留 diagnostics_source 整体兜底，避免改变旧 safe-copy 输入面。
    verified_terminal_result_material_review_handoff_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_review_handoff_keys,
            fallback_to_diagnostics_source=True,
            default={},
        )
    )
    verified_terminal_result_material_followup_escalation_status_keys = (
        "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary",
        "verified_terminal_result_material_followup_escalation_status_summary",
        "verified_terminal_result_material_followup_escalation_status",
    )
    # followup 旧逻辑只允许字段级 diagnostics_source alias，不允许整对象兜底。
    verified_terminal_result_material_followup_escalation_status_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_followup_escalation_status_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_intake_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary",
        "verified_terminal_result_material_owner_response_intake_summary",
        "verified_terminal_result_material_owner_response_intake",
    )
    # owner_response 只接受字段级 alias，避免把整个 diagnostics_source 误当作 owner response 证据。
    verified_terminal_result_material_owner_response_intake_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_intake_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_review_decision_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary",
        "verified_terminal_result_material_owner_response_review_decision_summary",
        "verified_terminal_result_material_owner_response_review_decision",
    )
    # review_decision 延续旧字段级兜底；整对象 fallback 会扩大证据来源边界。
    verified_terminal_result_material_owner_response_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_review_decision_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_review_handoff_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary",
        "verified_terminal_result_material_owner_response_review_handoff_summary",
        "verified_terminal_result_material_owner_response_review_handoff",
    )
    # review_handoff 同样只走显式字段 alias，保持旧默认 {} 的 fail-closed 行为。
    verified_terminal_result_material_owner_response_review_handoff_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_review_handoff_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_reviewer_ack_intake_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_intake",
    )
    # reviewer_ack 只接受字段级 alias，避免扩大 owner response ACK 的证据边界。
    verified_terminal_result_material_owner_response_reviewer_ack_intake_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_reviewer_ack_intake_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_reviewer_ack_review_decision_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision",
    )
    # review_decision 延续字段级 alias 顺序；缺失时保持旧默认 {}。
    verified_terminal_result_material_owner_response_reviewer_ack_review_decision_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_reviewer_ack_review_decision_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff",
    )
    # review_handoff 不启用整对象兜底，防止把泛诊断状态提升为 ACK 来源。
    verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_keys,
            default={},
        )
    )
    verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_keys = (
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status",
    )
    # followup 仅复用字段级 resolver，保持 not_proven 证据收口不变。
    verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_preserved_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_keys,
            default={},
        )
    )
    # cloud guard 只保留旧的 latest guard fallback，不扩大 diagnostics guard 来源。
    cloud_guard_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_unreachable_malformed_response_guard"),
        latest_status.get("robot_diagnostics_cloud_unreachable_malformed_response_guard_summary"),
        default={},
    )
    cloud_guard_summary = summarize_cloud_unreachable_malformed_response_guard(cloud_guard_source)
    safe_cloud_remote_readiness = _remote_readiness_for_cloud_guard(cloud_guard_summary)
    if safe_cloud_remote_readiness:
        latest_status["remote_readiness"] = safe_cloud_remote_readiness
    # rate-limit guard 同样不读取 diagnostics raw/summary guard，避免扩大云保护证据面。
    poll_backoff_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_poll_backoff_rate_limit_guard"),
        latest_status.get("robot_diagnostics_cloud_poll_backoff_rate_limit_guard_summary"),
        default={},
    )
    poll_backoff_summary = summarize_cloud_poll_backoff_rate_limit_guard(poll_backoff_source)
    safe_poll_backoff_remote_readiness = _remote_readiness_for_poll_backoff_guard(poll_backoff_summary)
    if safe_poll_backoff_remote_readiness:
        latest_status["remote_readiness"] = safe_poll_backoff_remote_readiness
    # ACK lookup 保留旧的 latest -> diagnostics 字段级顺序，缺失时仍 fail-closed 到 {}。
    ack_lookup_pending_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_ack_lookup_pending_status_guard"),
        latest_status.get("robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary"),
        diagnostics_source.get("cloud_ack_lookup_pending_status_guard"),
        diagnostics_source.get("robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary"),
        default={},
    )
    ack_lookup_pending_summary = summarize_cloud_ack_lookup_pending_status_guard(
        ack_lookup_pending_source
    )
    safe_ack_lookup_pending_remote_readiness = _remote_readiness_for_ack_lookup_pending_guard(
        ack_lookup_pending_summary
    )
    if safe_ack_lookup_pending_remote_readiness:
        latest_status["remote_readiness"] = safe_ack_lookup_pending_remote_readiness
    # accepted-result pending 继续接受 diagnostics 字段 alias，但不接受聚合 summary 兜底。
    ack_accepted_result_pending_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_ack_accepted_result_pending_guard"),
        latest_status.get("robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary"),
        diagnostics_source.get("cloud_ack_accepted_result_pending_guard"),
        diagnostics_source.get("robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary"),
        default={},
    )
    ack_accepted_result_pending_summary = summarize_cloud_ack_accepted_result_pending_guard(
        ack_accepted_result_pending_source
    )
    safe_ack_accepted_result_pending_remote_readiness = (
        _remote_readiness_for_ack_accepted_result_pending_guard(
            ack_accepted_result_pending_summary
        )
    )
    if safe_ack_accepted_result_pending_remote_readiness:
        latest_status["remote_readiness"] = safe_ack_accepted_result_pending_remote_readiness
    # terminal verification 的候选仍按旧序列出，便于审查终态确认来源。
    terminal_result_verification_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_terminal_result_verification_guard"),
        latest_status.get("robot_diagnostics_cloud_terminal_result_verification_guard_summary"),
        diagnostics_source.get("cloud_terminal_result_verification_guard"),
        diagnostics_source.get("robot_diagnostics_cloud_terminal_result_verification_guard_summary"),
        default={},
    )
    terminal_result_verification_summary = summarize_cloud_terminal_result_verification_guard(
        terminal_result_verification_source
    )
    safe_terminal_result_verification_remote_readiness = (
        _remote_readiness_for_terminal_result_verification_guard(
            terminal_result_verification_summary
        )
    )
    if safe_terminal_result_verification_remote_readiness:
        latest_status["remote_readiness"] = safe_terminal_result_verification_remote_readiness
    # cancel pending 维持字段级 fallback，避免把 diagnostics 聚合对象误当取消保护证据。
    cancel_pending_source = first_dict_value(
        latest_status.get("remote_readiness"),
        diagnostics_source.get("remote_readiness"),
        latest_status.get("cloud_cancel_pending_command_safety_guard"),
        latest_status.get("robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary"),
        diagnostics_source.get("cloud_cancel_pending_command_safety_guard"),
        diagnostics_source.get("robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary"),
        default={},
    )
    cancel_pending_summary = summarize_cloud_cancel_pending_command_safety_guard(cancel_pending_source)
    safe_cancel_pending_remote_readiness = _remote_readiness_for_cancel_pending_guard(cancel_pending_summary)
    if safe_cancel_pending_remote_readiness:
        latest_status["remote_readiness"] = safe_cancel_pending_remote_readiness
    cloud_support_handoff_safe_export_keys = (
        "cloud_support_handoff_safe_export",
        "cloud_support_handoff_safe_export_summary",
        "robot_diagnostics_cloud_support_handoff_safe_export_summary",
    )
    # 这里的 raw -> plain summary -> robot summary 顺序是移动端兼容契约，不能被别名排序重排。
    cloud_support_handoff_safe_export_source = first_status_dict(
        latest_status,
        diagnostics_source,
        cloud_support_handoff_safe_export_keys,
        default={},
    )
    cloud_support_handoff_safe_export_summary = summarize_cloud_support_handoff_safe_export(
        cloud_support_handoff_safe_export_source
    )
    cloud_command_lifecycle_status_source = dict(latest_status)
    # 上面的 guard 会把 latest_status.remote_readiness 覆盖成 canonical safe state；
    # lifecycle audit 仍需要同一 safe command_id，因此优先读覆盖前的 guard source。
    for lifecycle_remote_source in (
        terminal_result_verification_source,
        ack_accepted_result_pending_source,
        cancel_pending_source,
        ack_lookup_pending_source,
        latest_status.get("remote_readiness")
        if isinstance(latest_status.get("remote_readiness"), dict)
        else {},
        diagnostics_source.get("remote_readiness")
        if isinstance(diagnostics_source.get("remote_readiness"), dict)
        else {},
    ):
        if not isinstance(lifecycle_remote_source, dict):
            continue
        lifecycle_state = str(
            lifecycle_remote_source.get("degradation_state")
            or lifecycle_remote_source.get("state")
            or ""
        ).strip()
        if lifecycle_state:
            cloud_command_lifecycle_status_source["remote_readiness"] = lifecycle_remote_source
            break
    cloud_command_lifecycle_audit_export_keys = (
        "cloud_command_lifecycle_audit_export",
        "cloud_command_lifecycle_audit_export_summary",
        "robot_diagnostics_cloud_command_lifecycle_audit_export_summary",
    )
    cloud_command_lifecycle_audit_export_source = first_status_dict(
        latest_status,
        diagnostics_source,
        cloud_command_lifecycle_audit_export_keys,
    )
    if cloud_command_lifecycle_audit_export_source is None:
        # builder 只能在没有任何 dict source 时执行，避免提前构造改变旧链路副作用边界。
        cloud_command_lifecycle_audit_export_source = build_cloud_command_lifecycle_audit_export(
            cloud_command_lifecycle_status_source,
            {"remote_readiness": cloud_command_lifecycle_status_source.get("remote_readiness", {})},
            diagnostics_source,
        )
    cloud_command_lifecycle_audit_export_summary = summarize_cloud_command_lifecycle_audit_export(
        cloud_command_lifecycle_audit_export_source
    )
    cloud_command_lifecycle_replay_drill_summary = summarize_cloud_command_lifecycle_replay_drill(
        cloud_command_lifecycle_audit_export_summary
    )
    cloud_command_lifecycle_replay_acceptance_packet_summary = (
        summarize_cloud_command_lifecycle_replay_acceptance_packet(
            cloud_command_lifecycle_replay_drill_summary
        )
    )
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_keys = (
        "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff",
        "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary",
        "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary",
    )
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_keys,
            default={},
        )
    )
    # operator diagnostics 只消费上一阶 safe summary；缺失时由 relay builder 给出 fail-closed 默认摘要。
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_summary = (
        build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_payload(
            source_review_handoff=(
                cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_source
                or None
            )
        )
    )
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_keys = (
        "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status",
        "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary",
        "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary",
    )
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_keys,
            default=cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_summary,
        )
    )
    # bridge 只从上一阶 safe follow-up summary 派生，避免 diagnostics 端误读原始 reviewer material。
    cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_summary = (
        build_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_payload(
            source_followup_summary=(
                cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_source
            )
        )
    )
    cloud_external_evidence_review_decision_keys = (
        "robot_diagnostics_cloud_external_evidence_review_decision_summary",
        "cloud_external_evidence_review_decision_summary",
        "cloud_external_evidence_review_decision",
    )
    # env fallback 是操作员临时注入入口，status-source 是状态快照入口；两层兼容不能合并。
    cloud_external_evidence_review_decision_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        cloud_external_evidence_review_decision_keys,
        default={},
    )
    cloud_external_evidence_review_decision_source = (
        os.environ.get("TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_SUMMARY", "")
        or os.environ.get("TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION", "")
        or cloud_external_evidence_review_decision_status_source
    )
    cloud_external_evidence_review_decision_summary = (
        summarize_cloud_external_evidence_review_decision(
            cloud_external_evidence_review_decision_source
        )
    )
    cloud_external_evidence_review_handoff_keys = (
        "robot_diagnostics_cloud_external_evidence_review_handoff_summary",
        "cloud_external_evidence_review_handoff_summary",
        "cloud_external_evidence_review_handoff",
    )
    # env fallback 继续优先于 status-source，保留旧调试入口和字段级 alias 顺序。
    cloud_external_evidence_review_handoff_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        cloud_external_evidence_review_handoff_keys,
        default={},
    )
    cloud_external_evidence_review_handoff_source = (
        os.environ.get("TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_SUMMARY", "")
        or os.environ.get("TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF", "")
        or cloud_external_evidence_review_handoff_status_source
    )
    cloud_external_evidence_review_handoff_summary = (
        summarize_cloud_external_evidence_review_handoff(
            cloud_external_evidence_review_handoff_source
        )
    )
    cloud_external_evidence_review_handoff_followup_keys = (
        "robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary",
        "cloud_external_evidence_review_handoff_followup_escalation_status_summary",
        "cloud_external_evidence_review_handoff_followup_escalation_status",
    )
    # follow-up 也保留 env fallback 作为第二层入口，避免 resolver 吞掉既有覆盖顺序。
    cloud_external_evidence_review_handoff_followup_source = first_status_dict(
        latest_status,
        diagnostics_source,
        cloud_external_evidence_review_handoff_followup_keys,
        default={},
    )
    cloud_external_evidence_review_handoff_followup_source = (
        os.environ.get(
            "TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or os.environ.get(
            "TRASHBOT_CLOUD_EXTERNAL_EVIDENCE_REVIEW_HANDOFF_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or cloud_external_evidence_review_handoff_followup_source
    )
    cloud_external_evidence_review_handoff_followup_summary = (
        summarize_cloud_external_evidence_review_handoff_followup_escalation_status(
            cloud_external_evidence_review_handoff_followup_source
        )
    )
    task_terminal_field_material_intake_source = (
        _task_terminal_field_material_intake_source_from_payloads(
            latest_status,
            diagnostics_source,
        )
    )
    task_terminal_field_material_review_decision_source = (
        _task_terminal_field_material_review_decision_source_from_payloads(
            latest_status,
            diagnostics_source,
        )
    )
    real_material_readiness_board_keys = (
        "real_material_readiness_board",
        "real_material_readiness_board_summary",
        "robot_diagnostics_real_material_readiness_board_summary",
    )
    # real material 只接受字段级 alias，避免把整包 diagnostics 误当成真实材料证据。
    real_material_readiness_board_source = first_status_dict(
        latest_status,
        diagnostics_source,
        real_material_readiness_board_keys,
        default={},
    )
    real_material_evidence_intake_keys = (
        "real_material_evidence_intake",
        "real_material_evidence_intake_summary",
        "robot_diagnostics_real_material_evidence_intake_summary",
    )
    # intake 与 readiness 共享同一字段级边界，保持旧 alias 顺序和默认 {}。
    real_material_evidence_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        real_material_evidence_intake_keys,
        default={},
    )
    real_material_followup_escalation_status_keys = (
        "real_material_followup_escalation_status",
        "real_material_followup_escalation_status_summary",
        "robot_diagnostics_real_material_followup_escalation_status_summary",
    )
    # followup status 也不启用整包兜底，避免把待补材料状态误提升为已收材料。
    real_material_followup_escalation_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        real_material_followup_escalation_status_keys,
        default={},
    )
    field_evidence_real_material_followup_escalation_status_keys = (
        "field_evidence_real_material_followup_escalation_status",
        "field_evidence_real_material_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary",
    )
    # followup escalation status 的旧契约是 raw -> plain -> robot，不能改成 robot-first。
    field_evidence_real_material_followup_escalation_status_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            field_evidence_real_material_followup_escalation_status_keys,
            default={},
        )
    )
    elevator_field_evidence_trace_callback_intake_source_keys = (
        "elevator_field_evidence_trace_callback_intake",
        "elevator_field_evidence_trace_callback_intake_summary",
        "robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary",
    )
    elevator_field_evidence_trace_callback_review_decision_source_keys = (
        "elevator_field_evidence_trace_callback_review_decision",
        "elevator_field_evidence_trace_callback_review_decision_summary",
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary",
    )
    elevator_field_evidence_trace_callback_review_handoff_source_keys = (
        "elevator_field_evidence_trace_callback_review_handoff",
        "elevator_field_evidence_trace_callback_review_handoff_summary",
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary",
    )
    elevator_field_evidence_trace_material_backfill_intake_source_keys = (
        "elevator_field_evidence_trace_material_backfill_intake",
        "elevator_field_evidence_trace_material_backfill_intake_summary",
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary",
    )
    elevator_field_evidence_trace_material_backfill_review_decision_source_keys = (
        "elevator_field_evidence_trace_material_backfill_review_decision",
        "elevator_field_evidence_trace_material_backfill_review_decision_summary",
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary",
    )
    elevator_field_evidence_trace_material_backfill_review_handoff_source_keys = (
        "elevator_field_evidence_trace_material_backfill_review_handoff",
        "elevator_field_evidence_trace_material_backfill_review_handoff_summary",
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary",
    )
    # 电梯 field evidence trace 只接受字段级 alias，避免把整包 diagnostics 误当作证据 trace。
    elevator_field_evidence_trace_callback_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_callback_intake_source_keys,
        default={},
    )
    elevator_field_evidence_trace_callback_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_callback_review_decision_source_keys,
        default={},
    )
    elevator_field_evidence_trace_callback_review_handoff_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_callback_review_handoff_source_keys,
        default={},
    )
    elevator_field_evidence_trace_material_backfill_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_material_backfill_intake_source_keys,
        default={},
    )
    elevator_field_evidence_trace_material_backfill_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_material_backfill_review_decision_source_keys,
        default={},
    )
    elevator_field_evidence_trace_material_backfill_review_handoff_source = first_status_dict(
        latest_status,
        diagnostics_source,
        elevator_field_evidence_trace_material_backfill_review_handoff_source_keys,
        default={},
    )
    hardware_baseline_review_source = (
        latest_status.get("hardware_baseline_review")
        if isinstance(latest_status.get("hardware_baseline_review"), dict)
        else latest_status.get("hardware_baseline_review_summary")
        if isinstance(latest_status.get("hardware_baseline_review_summary"), dict)
        else diagnostics_source.get("hardware_baseline_review")
        if isinstance(diagnostics_source.get("hardware_baseline_review"), dict)
        else diagnostics_source.get("hardware_baseline_review_summary")
        if isinstance(diagnostics_source.get("hardware_baseline_review_summary"), dict)
        else {}
    )
    hardware_baseline_source_alignment_source = (
        latest_status.get("hardware_baseline_source_alignment")
        if isinstance(latest_status.get("hardware_baseline_source_alignment"), dict)
        else latest_status.get("hardware_baseline_source_alignment_summary")
        if isinstance(latest_status.get("hardware_baseline_source_alignment_summary"), dict)
        else diagnostics_source.get("hardware_baseline_source_alignment")
        if isinstance(diagnostics_source.get("hardware_baseline_source_alignment"), dict)
        else diagnostics_source.get("hardware_baseline_source_alignment_summary")
        if isinstance(diagnostics_source.get("hardware_baseline_source_alignment_summary"), dict)
        else {}
    )
    hardware_sensor_procurement_intake_source = (
        latest_status.get("hardware_sensor_procurement_intake")
        if isinstance(latest_status.get("hardware_sensor_procurement_intake"), dict)
        else latest_status.get("hardware_sensor_procurement_intake_summary")
        if isinstance(latest_status.get("hardware_sensor_procurement_intake_summary"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_intake")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_intake"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_intake_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_intake_summary"), dict)
        else {}
    )
    hardware_sensor_procurement_review_decision_source = (
        latest_status.get("hardware_sensor_procurement_review_decision")
        if isinstance(latest_status.get("hardware_sensor_procurement_review_decision"), dict)
        else latest_status.get("hardware_sensor_procurement_review_decision_summary")
        if isinstance(latest_status.get("hardware_sensor_procurement_review_decision_summary"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_review_decision")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_review_decision"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_review_decision_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_review_decision_summary"), dict)
        else {}
    )
    hardware_sensor_procurement_execution_pack_source = (
        latest_status.get("hardware_sensor_procurement_execution_pack")
        if isinstance(latest_status.get("hardware_sensor_procurement_execution_pack"), dict)
        else latest_status.get("hardware_sensor_procurement_execution_pack_summary")
        if isinstance(latest_status.get("hardware_sensor_procurement_execution_pack_summary"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_execution_pack")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_execution_pack"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_execution_pack_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_execution_pack_summary"), dict)
        else {}
    )
    hardware_sensor_procurement_receipt_intake_source = (
        latest_status.get("hardware_sensor_procurement_receipt_intake")
        if isinstance(latest_status.get("hardware_sensor_procurement_receipt_intake"), dict)
        else latest_status.get("hardware_sensor_procurement_receipt_intake_summary")
        if isinstance(latest_status.get("hardware_sensor_procurement_receipt_intake_summary"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_receipt_intake")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_receipt_intake"), dict)
        else diagnostics_source.get("hardware_sensor_procurement_receipt_intake_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_procurement_receipt_intake_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_config_precheck_source = (
        latest_status.get("hardware_sensor_hil_entry_config_precheck")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_config_precheck"), dict)
        else latest_status.get("hardware_sensor_hil_entry_config_precheck_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_config_precheck_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_config_precheck")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_config_precheck"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_config_precheck_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_config_precheck_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_readiness_review_source = (
        latest_status.get("hardware_sensor_hil_entry_readiness_review")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_readiness_review"), dict)
        else latest_status.get("hardware_sensor_hil_entry_readiness_review_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_readiness_review_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_readiness_review")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_readiness_review"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_readiness_review_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_readiness_review_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_execution_pack_source = (
        latest_status.get("hardware_sensor_hil_entry_execution_pack")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_execution_pack"), dict)
        else latest_status.get("hardware_sensor_hil_entry_execution_pack_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_execution_pack_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_execution_pack")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_execution_pack"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_execution_pack_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_execution_pack_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_callback_intake_source = (
        latest_status.get("hardware_sensor_hil_entry_callback_intake")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_intake"), dict)
        else latest_status.get("hardware_sensor_hil_entry_callback_intake_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_intake_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_intake")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_intake"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_intake_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_intake_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_callback_review_decision_source = (
        latest_status.get("hardware_sensor_hil_entry_callback_review_decision")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_review_decision"), dict)
        else latest_status.get("hardware_sensor_hil_entry_callback_review_decision_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_review_decision_summary"), dict)
        else latest_status.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary")
        if isinstance(latest_status.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_review_decision")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_review_decision"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_review_decision_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_review_decision_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary"), dict)
        else {}
    )
    hardware_sensor_hil_entry_callback_review_handoff_source = (
        latest_status.get("hardware_sensor_hil_entry_callback_review_handoff")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_review_handoff"), dict)
        else latest_status.get("hardware_sensor_hil_entry_callback_review_handoff_summary")
        if isinstance(latest_status.get("hardware_sensor_hil_entry_callback_review_handoff_summary"), dict)
        else latest_status.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary")
        if isinstance(latest_status.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_review_handoff")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_review_handoff"), dict)
        else diagnostics_source.get("hardware_sensor_hil_entry_callback_review_handoff_summary")
        if isinstance(diagnostics_source.get("hardware_sensor_hil_entry_callback_review_handoff_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary"), dict)
        else {}
    )
    pr5_review_thread_closeout_source = (
        latest_status.get("pr5_review_thread_closeout")
        if isinstance(latest_status.get("pr5_review_thread_closeout"), dict)
        else latest_status.get("pr5_review_thread_closeout_summary")
        if isinstance(latest_status.get("pr5_review_thread_closeout_summary"), dict)
        else latest_status.get("robot_diagnostics_pr5_review_thread_closeout_summary")
        if isinstance(latest_status.get("robot_diagnostics_pr5_review_thread_closeout_summary"), dict)
        else diagnostics_source.get("pr5_review_thread_closeout")
        if isinstance(diagnostics_source.get("pr5_review_thread_closeout"), dict)
        else diagnostics_source.get("pr5_review_thread_closeout_summary")
        if isinstance(diagnostics_source.get("pr5_review_thread_closeout_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_pr5_review_thread_closeout_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_pr5_review_thread_closeout_summary"), dict)
        else {}
    )
    pr5_vendor_source_review_packet_source = (
        latest_status.get("pr5_vendor_source_review_packet")
        if isinstance(latest_status.get("pr5_vendor_source_review_packet"), dict)
        else latest_status.get("pr5_vendor_source_review_packet_summary")
        if isinstance(latest_status.get("pr5_vendor_source_review_packet_summary"), dict)
        else latest_status.get("robot_diagnostics_pr5_vendor_source_review_packet_summary")
        if isinstance(
            latest_status.get("robot_diagnostics_pr5_vendor_source_review_packet_summary"),
            dict,
        )
        else diagnostics_source.get("pr5_vendor_source_review_packet")
        if isinstance(diagnostics_source.get("pr5_vendor_source_review_packet"), dict)
        else diagnostics_source.get("pr5_vendor_source_review_packet_summary")
        if isinstance(diagnostics_source.get("pr5_vendor_source_review_packet_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_pr5_vendor_source_review_packet_summary")
        if isinstance(
            diagnostics_source.get("robot_diagnostics_pr5_vendor_source_review_packet_summary"),
            dict,
        )
        else {}
    )
    pr5_vendor_source_review_reply_dispatch_source = (
        latest_status.get("pr5_vendor_source_review_reply_dispatch")
        if isinstance(latest_status.get("pr5_vendor_source_review_reply_dispatch"), dict)
        else latest_status.get("pr5_vendor_source_review_reply_dispatch_summary")
        if isinstance(latest_status.get("pr5_vendor_source_review_reply_dispatch_summary"), dict)
        else latest_status.get("robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary")
        if isinstance(
            latest_status.get("robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary"),
            dict,
        )
        else diagnostics_source.get("pr5_vendor_source_review_reply_dispatch")
        if isinstance(diagnostics_source.get("pr5_vendor_source_review_reply_dispatch"), dict)
        else diagnostics_source.get("pr5_vendor_source_review_reply_dispatch_summary")
        if isinstance(
            diagnostics_source.get("pr5_vendor_source_review_reply_dispatch_summary"),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_source_alignment_source = (
        latest_status.get("pr5_mandatory_sensor_source_alignment")
        if isinstance(latest_status.get("pr5_mandatory_sensor_source_alignment"), dict)
        else latest_status.get("pr5_mandatory_sensor_source_alignment_summary")
        if isinstance(latest_status.get("pr5_mandatory_sensor_source_alignment_summary"), dict)
        else latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary"
            ),
            dict,
        )
        else diagnostics_source.get("pr5_mandatory_sensor_source_alignment")
        if isinstance(diagnostics_source.get("pr5_mandatory_sensor_source_alignment"), dict)
        else diagnostics_source.get("pr5_mandatory_sensor_source_alignment_summary")
        if isinstance(
            diagnostics_source.get("pr5_mandatory_sensor_source_alignment_summary"),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_material_followup_escalation_status_source = (
        latest_status.get("pr5_mandatory_sensor_material_followup_escalation_status")
        if isinstance(
            latest_status.get("pr5_mandatory_sensor_material_followup_escalation_status"),
            dict,
        )
        else latest_status.get(
            "pr5_mandatory_sensor_material_followup_escalation_status_summary"
        )
        if isinstance(
            latest_status.get(
                "pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            dict,
        )
        else latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_followup_escalation_status"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_followup_escalation_status"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_followup_escalation_status_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_material_owner_response_intake_source = (
        latest_status.get("pr5_mandatory_sensor_material_owner_response_intake")
        if isinstance(latest_status.get("pr5_mandatory_sensor_material_owner_response_intake"), dict)
        else latest_status.get("pr5_mandatory_sensor_material_owner_response_intake_summary")
        if isinstance(
            latest_status.get("pr5_mandatory_sensor_material_owner_response_intake_summary"),
            dict,
        )
        else latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
            ),
            dict,
        )
        else diagnostics_source.get("pr5_mandatory_sensor_material_owner_response_intake")
        if isinstance(
            diagnostics_source.get("pr5_mandatory_sensor_material_owner_response_intake"),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_intake_summary"
        )
        if isinstance(
            diagnostics_source.get("pr5_mandatory_sensor_material_owner_response_intake_summary"),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_material_owner_response_review_decision_source = (
        latest_status.get("pr5_mandatory_sensor_material_owner_response_review_decision")
        if isinstance(
            latest_status.get("pr5_mandatory_sensor_material_owner_response_review_decision"),
            dict,
        )
        else latest_status.get(
            "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            dict,
        )
        else latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_review_decision"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_review_decision"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_material_owner_response_review_handoff_source = (
        latest_status.get("pr5_mandatory_sensor_material_owner_response_review_handoff")
        if isinstance(
            latest_status.get("pr5_mandatory_sensor_material_owner_response_review_handoff"),
            dict,
        )
        else latest_status.get(
            "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_review_handoff"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_review_handoff"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary"
            ),
            dict,
        )
        else {}
    )
    pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_source = (
        latest_status.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else latest_status.get(
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            latest_status.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else latest_status.get(
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake"
        )
        if isinstance(
            latest_status.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake"
            ),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
            ),
            dict,
        )
        else diagnostics_source.get(
            "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake"
        )
        if isinstance(
            diagnostics_source.get(
                "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake"
            ),
            dict,
        )
        else {}
    )
    hardware_real_material_escalation_request_source = (
        latest_status.get("hardware_real_material_escalation_request")
        if isinstance(latest_status.get("hardware_real_material_escalation_request"), dict)
        else latest_status.get("hardware_real_material_escalation_request_summary")
        if isinstance(latest_status.get("hardware_real_material_escalation_request_summary"), dict)
        else latest_status.get(
            "robot_diagnostics_hardware_real_material_escalation_request_summary"
        )
        if isinstance(
            latest_status.get(
                "robot_diagnostics_hardware_real_material_escalation_request_summary"
            ),
            dict,
        )
        else diagnostics_source.get("hardware_real_material_escalation_request")
        if isinstance(diagnostics_source.get("hardware_real_material_escalation_request"), dict)
        else diagnostics_source.get("hardware_real_material_escalation_request_summary")
        if isinstance(
            diagnostics_source.get("hardware_real_material_escalation_request_summary"),
            dict,
        )
        else diagnostics_source.get(
            "robot_diagnostics_hardware_real_material_escalation_request_summary"
        )
        if isinstance(
            diagnostics_source.get(
                "robot_diagnostics_hardware_real_material_escalation_request_summary"
            ),
            dict,
        )
        else {}
    )
    # 手机端 field material 只接受旧链路已有的 raw 与 plain summary，避免新增 robot alias 改变来源边界。
    mobile_field_material_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        (
            "mobile_field_material_review_decision",
            "mobile_field_material_review_decision_summary",
        ),
        default={},
    )
    # retest request 同样保留 latest 优先、diagnostics 次之，后续 ref/env 覆盖仍在原位置处理。
    mobile_field_material_retest_request_source = first_status_dict(
        latest_status,
        diagnostics_source,
        (
            "mobile_field_material_retest_request",
            "mobile_field_material_retest_request_summary",
        ),
        default={},
    )
    mobile_real_device_field_trial_acceptance_review_handoff_source_keys = (
        "mobile_real_device_field_trial_acceptance_review_handoff",
        "mobile_real_device_field_trial_acceptance_review_handoff_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary",
    )
    # 手机实机 field-trial 验收状态只接受字段级 alias，避免把整包 diagnostics 当作真实手机验收证据。
    # review_handoff 保留 raw -> summary -> robot summary 顺序，维持手机验收交接来源兼容。
    mobile_real_device_field_trial_acceptance_review_handoff_source = first_status_dict(
        latest_status,
        diagnostics_source,
        mobile_real_device_field_trial_acceptance_review_handoff_source_keys,
        default={},
    )
    # execution_pack 仍优先 runtime status，避免 diagnostics 快照覆盖最新执行包证据。
    mobile_real_device_field_trial_acceptance_execution_pack_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_pack",
        "mobile_real_device_field_trial_acceptance_execution_pack_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary",
    )
    # 这里不启用整包 fallback，因为执行包必须来自明确字段而不是聚合诊断对象。
    mobile_real_device_field_trial_acceptance_execution_pack_source = first_status_dict(
        latest_status,
        diagnostics_source,
        mobile_real_device_field_trial_acceptance_execution_pack_source_keys,
        default={},
    )
    # callback_intake 的三类 alias 顺序是对外兼容契约，不能按名称重新排序。
    mobile_real_device_field_trial_acceptance_execution_callback_intake_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_callback_intake",
        "mobile_real_device_field_trial_acceptance_execution_callback_intake_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary",
    )
    # 字段级 resolver 让手机端只消费 intake 摘要，不误读其他 diagnostics sibling。
    mobile_real_device_field_trial_acceptance_execution_callback_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        mobile_real_device_field_trial_acceptance_execution_callback_intake_source_keys,
        default={},
    )
    # callback_review_decision 保留旧 raw-first 行为，避免改变评审决策来源优先级。
    mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_callback_review_decision",
        "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary",
    )
    # default={} 继续 fail-closed，缺少字段时不制造手机实机验收结论。
    mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source_keys,
            default={},
        )
    )
    # callback_review_handoff 与 review_decision 分开列 keys，便于后续逐字段审查差异。
    mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff",
        "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary",
    )
    # resolver 只消除重复三元链，不改变 handoff 摘要的 safe-copy 与 not_proven 语义。
    mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source_keys,
            default={},
        )
    )
    # execution_handoff_intake 的字段 alias 独立于 callback intake，避免跨阶段串证据。
    mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_handoff_intake",
        "mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary",
    )
    # diagnostics_source 仍只是第二来源，保持 latest_status 覆盖历史快照的旧语义。
    mobile_real_device_field_trial_acceptance_execution_handoff_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        mobile_real_device_field_trial_acceptance_execution_handoff_intake_source_keys,
        default={},
    )
    # execution_handoff_review_decision 只迁移 review_decision，不触碰后续 review_handoff 链。
    mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision",
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary",
    )
    # 该 resolver 调用保持字段级边界，避免本轮范围外的 review_handoff 行为漂移。
    mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source_keys,
            default={},
        )
    )
    # 这是上一组 mobile field-trial source 的尾部 handoff，继续保持字段级 alias 边界。
    mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_keys = (
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff",
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary",
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary",
    )
    # 不启用整包 diagnostics fallback，避免把聚合诊断误当作真实手机验收交接证据。
    mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source_keys,
            default={},
        )
    )
    wave_rover_feedback_replay_source = (
        latest_status.get("wave_rover_feedback_replay")
        if isinstance(latest_status.get("wave_rover_feedback_replay"), dict)
        else latest_status.get("wave_rover_feedback_replay_summary")
        if isinstance(latest_status.get("wave_rover_feedback_replay_summary"), dict)
        else diagnostics_source.get("wave_rover_feedback_replay")
        if isinstance(diagnostics_source.get("wave_rover_feedback_replay"), dict)
        else diagnostics_source.get("wave_rover_feedback_replay_summary")
        if isinstance(diagnostics_source.get("wave_rover_feedback_replay_summary"), dict)
        else diagnostics_source.get("summary")
        if isinstance(diagnostics_source.get("summary"), dict)
        else diagnostics_source.get("diagnostics_summary")
        if isinstance(diagnostics_source.get("diagnostics_summary"), dict)
        else {}
    )
    wave_rover_hil_packet_intake_source = (
        latest_status.get("wave_rover_hil_packet_intake")
        if isinstance(latest_status.get("wave_rover_hil_packet_intake"), dict)
        else latest_status.get("wave_rover_hil_packet_intake_summary")
        if isinstance(latest_status.get("wave_rover_hil_packet_intake_summary"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_intake")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_intake"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_intake_summary")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_intake_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_intake_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_intake_summary"), dict)
        else diagnostics_source.get("summary")
        if isinstance(diagnostics_source.get("summary"), dict)
        else diagnostics_source.get("diagnostics_summary")
        if isinstance(diagnostics_source.get("diagnostics_summary"), dict)
        else {}
    )
    wave_rover_hil_packet_review_decision_source = (
        latest_status.get("wave_rover_hil_packet_review_decision")
        if isinstance(latest_status.get("wave_rover_hil_packet_review_decision"), dict)
        else latest_status.get("wave_rover_hil_packet_review_decision_summary")
        if isinstance(latest_status.get("wave_rover_hil_packet_review_decision_summary"), dict)
        else latest_status.get("robot_diagnostics_wave_rover_hil_packet_review_decision_summary")
        if isinstance(latest_status.get("robot_diagnostics_wave_rover_hil_packet_review_decision_summary"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_review_decision")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_review_decision"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_review_decision_summary")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_review_decision_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_review_decision_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_review_decision_summary"), dict)
        else diagnostics_source.get("summary")
        if isinstance(diagnostics_source.get("summary"), dict)
        else diagnostics_source.get("diagnostics_summary")
        if isinstance(diagnostics_source.get("diagnostics_summary"), dict)
        else {}
    )
    wave_rover_hil_packet_execution_pack_source = (
        latest_status.get("wave_rover_hil_packet_execution_pack")
        if isinstance(latest_status.get("wave_rover_hil_packet_execution_pack"), dict)
        else latest_status.get("wave_rover_hil_packet_execution_pack_summary")
        if isinstance(latest_status.get("wave_rover_hil_packet_execution_pack_summary"), dict)
        else latest_status.get("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary")
        if isinstance(latest_status.get("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_execution_pack")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_execution_pack"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_execution_pack_summary")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_execution_pack_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary"), dict)
        else diagnostics_source.get("summary")
        if isinstance(diagnostics_source.get("summary"), dict)
        else diagnostics_source.get("diagnostics_summary")
        if isinstance(diagnostics_source.get("diagnostics_summary"), dict)
        else {}
    )
    wave_rover_hil_packet_collection_drill_source = (
        latest_status.get("wave_rover_hil_packet_collection_drill")
        if isinstance(latest_status.get("wave_rover_hil_packet_collection_drill"), dict)
        else latest_status.get("wave_rover_hil_packet_collection_drill_summary")
        if isinstance(latest_status.get("wave_rover_hil_packet_collection_drill_summary"), dict)
        else latest_status.get("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary")
        if isinstance(latest_status.get("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_collection_drill")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_collection_drill"), dict)
        else diagnostics_source.get("wave_rover_hil_packet_collection_drill_summary")
        if isinstance(diagnostics_source.get("wave_rover_hil_packet_collection_drill_summary"), dict)
        else diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary")
        if isinstance(diagnostics_source.get("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary"), dict)
        else diagnostics_source.get("summary")
        if isinstance(diagnostics_source.get("summary"), dict)
        else diagnostics_source.get("diagnostics_summary")
        if isinstance(diagnostics_source.get("diagnostics_summary"), dict)
        else {}
    )
    # 这里刻意只列历史字段别名，避免把聚合 diagnostics summary 误当成终端任务证据。
    route_task_terminal_completion_rehearsal_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "route_task_terminal_completion_rehearsal",
            "route_task_terminal_completion_rehearsal_summary",
        ],
        default={},
    )
    task_terminal_completion_mainline_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "task_terminal_completion_mainline",
            "task_terminal_completion_mainline_summary",
            "robot_diagnostics_task_terminal_completion_mainline_summary",
        ],
        default={},
    )
    route_task_terminal_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "route_task_terminal_review_decision",
            "route_task_terminal_review_decision_summary",
        ],
        default={},
    )
    # 这三条 route field retest source 兼容旧诊断快照的通用 summary 兜底；
    # 使用 first_dict_value 是为了让空 dict 仍按旧 isinstance(dict) 链路命中。
    route_task_field_retest_execution_pack_source = first_dict_value(
        latest_status.get("route_task_field_retest_execution_pack"),
        latest_status.get("route_task_field_retest_execution_pack_summary"),
        latest_status.get("phone_readiness"),
        diagnostics_source.get("route_task_field_retest_execution_pack"),
        diagnostics_source.get("route_task_field_retest_execution_pack_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_session_handoff_source = first_dict_value(
        latest_status.get("route_task_field_retest_session_handoff"),
        latest_status.get("route_task_field_retest_session_handoff_summary"),
        diagnostics_source.get("route_task_field_retest_session_handoff"),
        diagnostics_source.get("route_task_field_retest_session_handoff_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_result_intake_source = first_dict_value(
        latest_status.get("route_task_field_retest_result_intake"),
        latest_status.get("route_task_field_retest_result_intake_summary"),
        diagnostics_source.get("route_task_field_retest_result_intake"),
        diagnostics_source.get("route_task_field_retest_result_intake_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_result_reconciliation_source = first_dict_value(
        latest_status.get("route_task_field_retest_result_reconciliation"),
        latest_status.get("route_task_field_retest_result_reconciliation_summary"),
        diagnostics_source.get("route_task_field_retest_result_reconciliation"),
        diagnostics_source.get("route_task_field_retest_result_reconciliation_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # material pack/callback packet 需要保留 robot_diagnostics_* 别名；
    # 它们是旧诊断快照的中间兜底，不能挪到通用 summary 之后。
    route_task_field_retest_material_pack_source = first_dict_value(
        latest_status.get("route_task_field_retest_material_pack"),
        latest_status.get("route_task_field_retest_material_pack_summary"),
        latest_status.get("robot_diagnostics_route_task_field_retest_material_pack_summary"),
        diagnostics_source.get("route_task_field_retest_material_pack"),
        diagnostics_source.get("route_task_field_retest_material_pack_summary"),
        diagnostics_source.get("robot_diagnostics_route_task_field_retest_material_pack_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_material_callback_packet_source = first_dict_value(
        latest_status.get("route_task_field_retest_material_callback_packet"),
        latest_status.get("route_task_field_retest_material_callback_packet_summary"),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_material_callback_packet_summary"
        ),
        diagnostics_source.get("route_task_field_retest_material_callback_packet"),
        diagnostics_source.get("route_task_field_retest_material_callback_packet_summary"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_material_callback_packet_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 这三条 drill/review source 的旧链包含 robot_diagnostics_* 中间别名；
    # 显式列出候选可以避免后续清理时误把通用 summary 提前。
    route_task_field_retest_material_callback_review_decision_source = first_dict_value(
        latest_status.get("route_task_field_retest_material_callback_review_decision"),
        latest_status.get("route_task_field_retest_material_callback_review_decision_summary"),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary"
        ),
        diagnostics_source.get("route_task_field_retest_material_callback_review_decision"),
        diagnostics_source.get(
            "route_task_field_retest_material_callback_review_decision_summary"
        ),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_operator_drill_source = first_dict_value(
        latest_status.get("route_task_field_retest_operator_drill"),
        latest_status.get("route_task_field_retest_operator_drill_summary"),
        latest_status.get("robot_diagnostics_route_task_field_retest_operator_drill_summary"),
        diagnostics_source.get("route_task_field_retest_operator_drill"),
        diagnostics_source.get("route_task_field_retest_operator_drill_summary"),
        diagnostics_source.get("robot_diagnostics_route_task_field_retest_operator_drill_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_drill_console_source = first_dict_value(
        latest_status.get("route_task_field_retest_drill_console"),
        latest_status.get("route_task_field_retest_drill_console_summary"),
        latest_status.get("robot_diagnostics_route_task_field_retest_drill_console_summary"),
        diagnostics_source.get("route_task_field_retest_drill_console"),
        diagnostics_source.get("route_task_field_retest_drill_console_summary"),
        diagnostics_source.get("robot_diagnostics_route_task_field_retest_drill_console_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # acceptance 三条链也保留 robot_diagnostics_* 中间别名和通用 summary 尾部兜底；
    # first_dict_value 会接受空 dict，等价于旧 isinstance(dict) 三元链的命中规则。
    route_task_field_retest_acceptance_brief_source = first_dict_value(
        latest_status.get("route_task_field_retest_acceptance_brief"),
        latest_status.get("route_task_field_retest_acceptance_brief_summary"),
        latest_status.get("robot_diagnostics_route_task_field_retest_acceptance_brief_summary"),
        diagnostics_source.get("route_task_field_retest_acceptance_brief"),
        diagnostics_source.get("route_task_field_retest_acceptance_brief_summary"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_brief_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_review_decision_source = first_dict_value(
        latest_status.get("route_task_field_retest_acceptance_review_decision"),
        latest_status.get("route_task_field_retest_acceptance_review_decision_summary"),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary"
        ),
        diagnostics_source.get("route_task_field_retest_acceptance_review_decision"),
        diagnostics_source.get("route_task_field_retest_acceptance_review_decision_summary"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_execution_pack_source = first_dict_value(
        latest_status.get("route_task_field_retest_acceptance_execution_pack"),
        latest_status.get("route_task_field_retest_acceptance_execution_pack_summary"),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary"
        ),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_pack"),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_pack_summary"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 这里显式列出候选，是为了保留旧三元链“空 dict 也算命中”的来源边界。
    route_task_field_retest_acceptance_execution_callback_intake_source = first_dict_value(
        latest_status.get("route_task_field_retest_acceptance_execution_callback_intake"),
        latest_status.get(
            "route_task_field_retest_acceptance_execution_callback_intake_summary"
        ),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"
        ),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_callback_intake"),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_callback_intake_summary"
        ),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_execution_callback_review_decision_source = first_dict_value(
        latest_status.get(
            "route_task_field_retest_acceptance_execution_callback_review_decision"
        ),
        latest_status.get(
            "route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        ),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_callback_review_decision"
        ),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_execution_callback_review_handoff_source = first_dict_value(
        latest_status.get(
            "route_task_field_retest_acceptance_execution_callback_review_handoff"
        ),
        latest_status.get(
            "route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        ),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_callback_review_handoff"
        ),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 两条 acceptance execution 链的历史顺序不同，必须分别显式列候选避免误合并。
    route_task_field_retest_acceptance_execution_handoff_intake_source = first_dict_value(
        latest_status.get("route_task_field_retest_acceptance_execution_handoff_intake"),
        latest_status.get("route_task_field_retest_acceptance_execution_handoff_intake_summary"),
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"
        ),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_handoff_intake"),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_handoff_intake_summary"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_execution_rerun_queue_source = first_dict_value(
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"
        ),
        latest_status.get("route_task_field_retest_acceptance_execution_rerun_queue_summary"),
        latest_status.get("route_task_field_retest_acceptance_execution_rerun_queue"),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary"
        ),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_rerun_queue_summary"),
        diagnostics_source.get("route_task_field_retest_acceptance_execution_rerun_queue"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 这一组三段 acceptance execution rerun result source 需要保留旧快照 summary 兜底；
    # 历史 rerun result artifact 可能只保存 aggregate summary，不能折叠成字段级 resolver。
    route_task_field_retest_acceptance_execution_rerun_result_intake_source = first_dict_value(
        latest_status.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        ),
        latest_status.get(
            "route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        ),
        diagnostics_source.get(
            "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        ),
        diagnostics_source.get(
            "route_task_field_retest_acceptance_execution_rerun_result_intake_summary"
        ),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_decision_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            latest_status.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            diagnostics_source.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary"
            ),
            diagnostics_source.get("summary"),
            diagnostics_source.get("diagnostics_summary"),
            default={},
        )
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source = (
        first_dict_value(
            latest_status.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            latest_status.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            diagnostics_source.get(
                "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            diagnostics_source.get(
                "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary"
            ),
            diagnostics_source.get("summary"),
            diagnostics_source.get("diagnostics_summary"),
            default={},
        )
    )
    # 这一组 field evidence rerun source 需要保留旧快照 summary 兜底；
    # 普通字段级 resolver 不含该兜底，会破坏历史诊断 payload 的回放兼容性。
    field_evidence_rerun_material_dispatch_source = first_dict_value(
        latest_status.get("robot_diagnostics_field_evidence_rerun_material_dispatch_summary"),
        latest_status.get("field_evidence_rerun_material_dispatch_summary"),
        latest_status.get("field_evidence_rerun_material_dispatch"),
        diagnostics_source.get("robot_diagnostics_field_evidence_rerun_material_dispatch_summary"),
        diagnostics_source.get("field_evidence_rerun_material_dispatch_summary"),
        diagnostics_source.get("field_evidence_rerun_material_dispatch"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    field_evidence_rerun_callback_intake_source = first_dict_value(
        latest_status.get("robot_diagnostics_field_evidence_rerun_callback_intake_summary"),
        latest_status.get("field_evidence_rerun_callback_intake_summary"),
        latest_status.get("field_evidence_rerun_callback_intake"),
        diagnostics_source.get("robot_diagnostics_field_evidence_rerun_callback_intake_summary"),
        diagnostics_source.get("field_evidence_rerun_callback_intake_summary"),
        diagnostics_source.get("field_evidence_rerun_callback_intake"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    field_evidence_rerun_callback_review_decision_source = first_dict_value(
        latest_status.get("robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"),
        latest_status.get("field_evidence_rerun_callback_review_decision_summary"),
        latest_status.get("field_evidence_rerun_callback_review_decision"),
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_callback_review_decision_summary"
        ),
        diagnostics_source.get("field_evidence_rerun_callback_review_decision_summary"),
        diagnostics_source.get("field_evidence_rerun_callback_review_decision"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    field_evidence_rerun_callback_review_handoff_source = first_dict_value(
        latest_status.get("robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"),
        latest_status.get("field_evidence_rerun_callback_review_handoff_summary"),
        latest_status.get("field_evidence_rerun_callback_review_handoff"),
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary"
        ),
        diagnostics_source.get("field_evidence_rerun_callback_review_handoff_summary"),
        diagnostics_source.get("field_evidence_rerun_callback_review_handoff"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    field_evidence_rerun_handoff_intake_source = first_dict_value(
        latest_status.get("robot_diagnostics_field_evidence_rerun_handoff_intake_summary"),
        latest_status.get("field_evidence_rerun_handoff_intake_summary"),
        latest_status.get("field_evidence_rerun_handoff_intake"),
        diagnostics_source.get("robot_diagnostics_field_evidence_rerun_handoff_intake_summary"),
        diagnostics_source.get("field_evidence_rerun_handoff_intake_summary"),
        diagnostics_source.get("field_evidence_rerun_handoff_intake"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 这四个前置复测 source 兼容旧诊断快照的通用 summary 兜底；
    # 因此不能混用普通字段级 resolver，否则会丢掉历史 summary/diagnostics_summary。
    route_task_field_retest_evidence_dispatch_source = first_dict_value(
        latest_status.get("route_task_field_retest_evidence_dispatch"),
        latest_status.get("route_task_field_retest_evidence_dispatch_summary"),
        diagnostics_source.get("route_task_field_retest_evidence_dispatch"),
        diagnostics_source.get("route_task_field_retest_evidence_dispatch_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_callback_intake_source = first_dict_value(
        latest_status.get("route_task_field_retest_callback_intake"),
        latest_status.get("route_task_field_retest_callback_intake_summary"),
        diagnostics_source.get("route_task_field_retest_callback_intake"),
        diagnostics_source.get("route_task_field_retest_callback_intake_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_callback_review_decision_source = first_dict_value(
        latest_status.get("route_task_field_retest_callback_review_decision"),
        latest_status.get("route_task_field_retest_callback_review_decision_summary"),
        diagnostics_source.get("route_task_field_retest_callback_review_decision"),
        diagnostics_source.get("route_task_field_retest_callback_review_decision_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_review_result_handoff_source = first_dict_value(
        latest_status.get("route_task_field_retest_review_result_handoff"),
        latest_status.get("route_task_field_retest_review_result_handoff_summary"),
        diagnostics_source.get("route_task_field_retest_review_result_handoff"),
        diagnostics_source.get("route_task_field_retest_review_result_handoff_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    # 这三个 acceptance/backfill source 兼容旧路由复测整包 summary artifact；
    # 因此不能改用普通字段级 resolver，否则会丢掉 summary/diagnostics_summary 兜底。
    route_task_field_retest_result_acceptance_packet_source = first_dict_value(
        latest_status.get("route_task_field_retest_result_acceptance_packet"),
        latest_status.get("route_task_field_retest_result_acceptance_packet_summary"),
        diagnostics_source.get("route_task_field_retest_result_acceptance_packet"),
        diagnostics_source.get("route_task_field_retest_result_acceptance_packet_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_result_acceptance_backfill_source = first_dict_value(
        latest_status.get("route_task_field_retest_result_acceptance_backfill"),
        latest_status.get("route_task_field_retest_result_acceptance_backfill_summary"),
        diagnostics_source.get("route_task_field_retest_result_acceptance_backfill"),
        diagnostics_source.get("route_task_field_retest_result_acceptance_backfill_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_result_backfill_review_decision_source = first_dict_value(
        latest_status.get("route_task_field_retest_result_backfill_review_decision"),
        latest_status.get("route_task_field_retest_result_backfill_review_decision_summary"),
        diagnostics_source.get("route_task_field_retest_result_backfill_review_decision"),
        diagnostics_source.get("route_task_field_retest_result_backfill_review_decision_summary"),
        diagnostics_source.get("summary"),
        diagnostics_source.get("diagnostics_summary"),
        default={},
    )
    route_task_field_retest_result_review_dispatch_keys = (
        "route_task_field_retest_result_review_dispatch",
        "route_task_field_retest_result_review_dispatch_summary",
    )
    # dispatch 历史上没有 robot_diagnostics_* alias，不能在清理三元链时补造来源。
    route_task_field_retest_result_review_dispatch_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_review_dispatch_keys,
        default={},
    )
    route_task_field_retest_result_review_intake_keys = (
        "route_task_field_retest_result_review_intake",
        "route_task_field_retest_result_review_intake_summary",
        "robot_diagnostics_route_task_field_retest_result_review_intake_summary",
    )
    route_task_field_retest_result_review_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_review_intake_keys,
        default={},
    )
    route_task_field_retest_result_review_decision_keys = (
        "route_task_field_retest_result_review_decision",
        "route_task_field_retest_result_review_decision_summary",
        "robot_diagnostics_route_task_field_retest_result_review_decision_summary",
    )
    route_task_field_retest_result_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_review_decision_keys,
        default={},
    )
    route_task_field_retest_result_review_handoff_keys = (
        "route_task_field_retest_result_review_handoff",
        "route_task_field_retest_result_review_handoff_summary",
        "robot_diagnostics_route_task_field_retest_result_review_handoff_summary",
    )
    route_task_field_retest_result_review_handoff_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_review_handoff_keys,
        default={},
    )
    route_task_field_retest_result_callback_intake_keys = (
        "route_task_field_retest_result_callback_intake",
        "route_task_field_retest_result_callback_intake_summary",
        "robot_diagnostics_route_task_field_retest_result_callback_intake_summary",
    )
    route_task_field_retest_result_callback_intake_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_callback_intake_keys,
        default={},
    )
    route_task_field_retest_result_callback_review_decision_keys = (
        "route_task_field_retest_result_callback_review_decision",
        "route_task_field_retest_result_callback_review_decision_summary",
        "robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary",
    )
    route_task_field_retest_result_callback_review_decision_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_callback_review_decision_keys,
        default={},
    )
    route_task_field_retest_result_callback_review_handoff_keys = (
        "route_task_field_retest_result_callback_review_handoff",
        "route_task_field_retest_result_callback_review_handoff_summary",
        "robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary",
    )
    route_task_field_retest_result_callback_review_handoff_source = first_status_dict(
        latest_status,
        diagnostics_source,
        route_task_field_retest_result_callback_review_handoff_keys,
        default={},
    )
    # phone-safe metadata 必须由 HTTP wrapper 重新生成；诊断 core 不转发状态文件里的旧对象。
    _drop_safe_alias_inputs(
        latest_status,
        "phone_support_bundle",
        "cloud_support_handoff_safe_export",
        "cloud_support_handoff_safe_export_summary",
        "robot_diagnostics_cloud_support_handoff_safe_export_summary",
        "cloud_command_lifecycle_audit_export",
        "cloud_command_lifecycle_audit_export_summary",
        "robot_diagnostics_cloud_command_lifecycle_audit_export_summary",
        "cloud_command_lifecycle_replay_drill",
        "cloud_command_lifecycle_replay_drill_summary",
        "robot_diagnostics_cloud_command_lifecycle_replay_drill_summary",
        "cloud_command_lifecycle_replay_acceptance_packet",
        "cloud_command_lifecycle_replay_acceptance_packet_summary",
        "robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary",
        "cloud_cancel_pending_command_safety_guard",
        "cloud_cancel_pending_command_safety_guard_summary",
        "robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary",
        "cloud_ack_lookup_pending_status_guard",
        "cloud_ack_lookup_pending_status_guard_summary",
        "robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary",
        "cloud_ack_accepted_result_pending_guard",
        "cloud_ack_accepted_result_pending_guard_summary",
        "robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary",
        "cloud_terminal_result_verification_guard",
        "cloud_terminal_result_verification_guard_summary",
        "robot_diagnostics_cloud_terminal_result_verification_guard_summary",
        "voice_prompt_readiness",
        "phone_offline_resume_readiness",
        "cloud_unreachable_malformed_response_guard",
        "cloud_unreachable_malformed_response_guard_summary",
        "robot_diagnostics_cloud_unreachable_malformed_response_guard_summary",
    )
    latest_status.pop("mobile_route_elevator_field_device_precheck", None)
    latest_status.pop("mobile_route_elevator_field_device_precheck_summary", None)
    latest_status.pop("mobile_route_elevator_field_device_precheck_copy", None)
    latest_status.pop("mobile_field_material_intake", None)
    latest_status.pop("mobile_field_material_intake_summary", None)
    latest_status.pop("mobile_field_material_intake_copy", None)
    latest_status.pop("mobile_field_material_review_decision", None)
    latest_status.pop("mobile_field_material_review_decision_summary", None)
    latest_status.pop("mobile_field_material_review_decision_copy", None)
    latest_status.pop("mobile_field_material_retest_request", None)
    latest_status.pop("mobile_field_material_retest_request_summary", None)
    latest_status.pop("mobile_field_material_retest_request_copy", None)
    latest_status.pop("mobile_real_device_field_trial_acceptance_execution_pack", None)
    latest_status.pop("mobile_real_device_field_trial_acceptance_execution_pack_summary", None)
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary",
        None,
    )
    latest_status.pop("mobile_real_device_field_trial_acceptance_execution_pack_copy", None)
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_intake",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_intake_copy",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_decision",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_decision_copy",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_copy",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_intake",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_intake_copy",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_copy",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_copy",
        None,
    )
    latest_status.pop("wave_rover_feedback_replay", None)
    latest_status.pop("wave_rover_feedback_replay_summary", None)
    latest_status.pop("wave_rover_feedback_replay_copy", None)
    latest_status.pop("wave_rover_hil_packet_intake", None)
    latest_status.pop("wave_rover_hil_packet_intake_summary", None)
    latest_status.pop("wave_rover_hil_packet_intake_copy", None)
    latest_status.pop("wave_rover_hil_packet_review_decision", None)
    latest_status.pop("wave_rover_hil_packet_review_decision_summary", None)
    latest_status.pop("wave_rover_hil_packet_review_decision_copy", None)
    latest_status.pop("robot_diagnostics_wave_rover_hil_packet_review_decision_summary", None)
    latest_status.pop("wave_rover_hil_packet_execution_pack", None)
    latest_status.pop("wave_rover_hil_packet_execution_pack_summary", None)
    latest_status.pop("wave_rover_hil_packet_execution_pack_copy", None)
    latest_status.pop("robot_diagnostics_wave_rover_hil_packet_execution_pack_summary", None)
    latest_status.pop("wave_rover_hil_packet_collection_drill", None)
    latest_status.pop("wave_rover_hil_packet_collection_drill_summary", None)
    latest_status.pop("wave_rover_hil_packet_collection_drill_copy", None)
    latest_status.pop("robot_diagnostics_wave_rover_hil_packet_collection_drill_summary", None)
    latest_status.pop("route_task_terminal_completion_rehearsal", None)
    latest_status.pop("route_task_terminal_completion_rehearsal_summary", None)
    latest_status.pop("route_task_terminal_completion_rehearsal_copy", None)
    latest_status.pop("task_terminal_completion_mainline", None)
    latest_status.pop("task_terminal_completion_mainline_summary", None)
    latest_status.pop("robot_diagnostics_task_terminal_completion_mainline_summary", None)
    latest_status.pop("task_terminal_field_material_intake", None)
    latest_status.pop("task_terminal_field_material_intake_summary", None)
    latest_status.pop("robot_diagnostics_task_terminal_field_material_intake_summary", None)
    latest_status.pop("task_terminal_field_material_review_decision", None)
    latest_status.pop("task_terminal_field_material_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_task_terminal_field_material_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_terminal_review_decision", None)
    latest_status.pop("route_task_terminal_review_decision_summary", None)
    latest_status.pop("route_task_terminal_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_execution_pack", None)
    latest_status.pop("route_task_field_retest_execution_pack_summary", None)
    latest_status.pop("route_task_field_retest_execution_pack_copy", None)
    latest_status.pop("route_task_field_retest_session_handoff", None)
    latest_status.pop("route_task_field_retest_session_handoff_summary", None)
    latest_status.pop("route_task_field_retest_session_handoff_copy", None)
    latest_status.pop("route_task_field_retest_result_intake", None)
    latest_status.pop("route_task_field_retest_result_intake_summary", None)
    latest_status.pop("route_task_field_retest_result_intake_copy", None)
    latest_status.pop("route_task_field_retest_result_reconciliation", None)
    latest_status.pop("route_task_field_retest_result_reconciliation_summary", None)
    latest_status.pop("route_task_field_retest_result_reconciliation_copy", None)
    latest_status.pop("route_task_field_retest_material_pack", None)
    latest_status.pop("route_task_field_retest_material_pack_summary", None)
    latest_status.pop("route_task_field_retest_material_pack_copy", None)
    latest_status.pop("route_task_field_retest_material_callback_review_decision", None)
    latest_status.pop("route_task_field_retest_material_callback_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_material_callback_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_operator_drill", None)
    latest_status.pop("route_task_field_retest_operator_drill_summary", None)
    latest_status.pop("route_task_field_retest_operator_drill_copy", None)
    latest_status.pop("route_task_field_retest_drill_console", None)
    latest_status.pop("route_task_field_retest_drill_console_summary", None)
    latest_status.pop("robot_diagnostics_route_task_field_retest_drill_console_summary", None)
    latest_status.pop("route_task_field_retest_drill_console_copy", None)
    latest_status.pop("route_task_field_retest_acceptance_brief", None)
    latest_status.pop("route_task_field_retest_acceptance_brief_summary", None)
    latest_status.pop("robot_diagnostics_route_task_field_retest_acceptance_brief_summary", None)
    latest_status.pop("route_task_field_retest_acceptance_brief_copy", None)
    latest_status.pop("route_task_field_retest_acceptance_review_decision", None)
    latest_status.pop("route_task_field_retest_acceptance_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_pack", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_pack_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_pack_copy", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_callback_intake", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_callback_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_callback_intake_copy", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_callback_review_decision", None)
    latest_status.pop(
        "route_task_field_retest_acceptance_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_callback_review_handoff", None)
    latest_status.pop(
        "route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_handoff_intake", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_handoff_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_rerun_queue", None)
    latest_status.pop("route_task_field_retest_acceptance_execution_rerun_queue_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_rerun_result_intake", None)
    latest_status.pop(
        "route_task_field_retest_acceptance_execution_rerun_result_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_acceptance_execution_rerun_result_review_handoff", None)
    latest_status.pop(
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "route_task_field_retest_acceptance_execution_rerun_result_review_handoff_copy",
        None,
    )
    latest_status.pop("route_task_field_retest_evidence_dispatch", None)
    latest_status.pop("route_task_field_retest_evidence_dispatch_summary", None)
    latest_status.pop("route_task_field_retest_evidence_dispatch_copy", None)
    latest_status.pop("route_task_field_retest_callback_intake", None)
    latest_status.pop("route_task_field_retest_callback_intake_summary", None)
    latest_status.pop("route_task_field_retest_callback_intake_copy", None)
    latest_status.pop("route_task_field_retest_callback_review_decision", None)
    latest_status.pop("route_task_field_retest_callback_review_decision_summary", None)
    latest_status.pop("route_task_field_retest_callback_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_review_result_handoff", None)
    latest_status.pop("route_task_field_retest_review_result_handoff_summary", None)
    latest_status.pop("route_task_field_retest_review_result_handoff_copy", None)
    latest_status.pop("route_task_field_retest_result_acceptance_packet", None)
    latest_status.pop("route_task_field_retest_result_acceptance_packet_summary", None)
    latest_status.pop("route_task_field_retest_result_acceptance_packet_copy", None)
    latest_status.pop("route_task_field_retest_result_acceptance_backfill", None)
    latest_status.pop("route_task_field_retest_result_acceptance_backfill_summary", None)
    latest_status.pop("route_task_field_retest_result_acceptance_backfill_copy", None)
    latest_status.pop("route_task_field_retest_result_backfill_review_decision", None)
    latest_status.pop("route_task_field_retest_result_backfill_review_decision_summary", None)
    latest_status.pop("route_task_field_retest_result_backfill_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_result_review_dispatch", None)
    latest_status.pop("route_task_field_retest_result_review_dispatch_summary", None)
    latest_status.pop("route_task_field_retest_result_review_dispatch_copy", None)
    latest_status.pop("route_task_field_retest_result_review_intake", None)
    latest_status.pop("route_task_field_retest_result_review_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_result_review_intake_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_result_review_intake_copy", None)
    latest_status.pop("route_task_field_retest_result_review_decision", None)
    latest_status.pop("route_task_field_retest_result_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_result_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_result_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_result_review_handoff", None)
    latest_status.pop("route_task_field_retest_result_review_handoff_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_result_review_handoff_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_result_review_handoff_copy", None)
    latest_status.pop("route_task_field_retest_result_callback_intake", None)
    latest_status.pop("route_task_field_retest_result_callback_intake_summary", None)
    latest_status.pop("robot_diagnostics_route_task_field_retest_result_callback_intake_summary", None)
    latest_status.pop("route_task_field_retest_result_callback_intake_copy", None)
    latest_status.pop("route_task_field_retest_result_callback_review_decision", None)
    latest_status.pop("route_task_field_retest_result_callback_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_result_callback_review_decision_copy", None)
    latest_status.pop("route_task_field_retest_result_callback_review_handoff", None)
    latest_status.pop("route_task_field_retest_result_callback_review_handoff_summary", None)
    latest_status.pop(
        "robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary",
        None,
    )
    latest_status.pop("route_task_field_retest_result_callback_review_handoff_copy", None)
    latest_status.pop("field_evidence_rerun_callback_review_decision", None)
    latest_status.pop("field_evidence_rerun_callback_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_callback_review_decision_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_callback_review_decision_copy", None)
    latest_status.pop("field_evidence_rerun_callback_review_handoff", None)
    latest_status.pop("field_evidence_rerun_callback_review_handoff_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_callback_review_handoff_copy", None)
    latest_status.pop("field_evidence_rerun_handoff_intake", None)
    latest_status.pop("field_evidence_rerun_handoff_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_handoff_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_handoff_intake_copy", None)
    latest_status.pop("field_evidence_rerun_queue", None)
    latest_status.pop("field_evidence_rerun_queue_summary", None)
    latest_status.pop("robot_diagnostics_field_evidence_rerun_queue_summary", None)
    latest_status.pop("field_evidence_rerun_queue_copy", None)
    latest_status.pop("field_evidence_rerun_execution_pack", None)
    latest_status.pop("field_evidence_rerun_execution_pack_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_pack_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_pack_copy", None)
    latest_status.pop("field_evidence_rerun_execution_callback_intake", None)
    latest_status.pop("field_evidence_rerun_execution_callback_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_callback_intake_copy", None)
    latest_status.pop("field_evidence_rerun_execution_callback_review_decision", None)
    latest_status.pop(
        "field_evidence_rerun_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_callback_review_decision_copy", None)
    latest_status.pop("field_evidence_rerun_execution_callback_review_handoff", None)
    latest_status.pop(
        "field_evidence_rerun_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_callback_review_handoff_copy", None)
    latest_status.pop("field_evidence_rerun_execution_result_intake", None)
    latest_status.pop("field_evidence_rerun_execution_result_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_result_intake_copy", None)
    latest_status.pop("field_evidence_rerun_execution_result_review_decision", None)
    latest_status.pop(
        "field_evidence_rerun_execution_result_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_result_review_decision_copy", None)
    latest_status.pop("field_evidence_rerun_execution_result_review_handoff", None)
    latest_status.pop(
        "field_evidence_rerun_execution_result_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_result_review_handoff_copy", None)
    latest_status.pop("field_evidence_rerun_execution_result_acceptance_packet", None)
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_packet_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_packet_copy",
        None,
    )
    latest_status.pop("field_evidence_rerun_execution_result_acceptance_backfill", None)
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_backfill_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_backfill_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_review_handoff",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_review_handoff_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_copy",
        None,
    )
    latest_status.pop("field_evidence_real_material_request_dispatch", None)
    latest_status.pop("field_evidence_real_material_request_dispatch_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_request_dispatch_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_request_dispatch_copy", None)
    latest_status.pop("field_evidence_real_material_response_intake", None)
    latest_status.pop("field_evidence_real_material_response_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_response_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_response_intake_copy", None)
    latest_status.pop("field_evidence_real_material_response_review_decision", None)
    latest_status.pop(
        "field_evidence_real_material_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_real_material_response_review_decision_copy",
        None,
    )
    latest_status.pop("field_evidence_real_material_response_review_handoff", None)
    latest_status.pop(
        "field_evidence_real_material_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_real_material_response_review_handoff_copy",
        None,
    )
    latest_status.pop("hardware_baseline_review", None)
    latest_status.pop("hardware_baseline_review_summary", None)
    latest_status.pop("hardware_baseline_review_copy", None)
    latest_status.pop("hardware_baseline_source_alignment", None)
    latest_status.pop("hardware_baseline_source_alignment_summary", None)
    latest_status.pop("hardware_baseline_source_alignment_copy", None)
    latest_status.pop("hardware_sensor_procurement_intake", None)
    latest_status.pop("hardware_sensor_procurement_intake_summary", None)
    latest_status.pop("hardware_sensor_procurement_intake_copy", None)
    latest_status.pop("hardware_sensor_procurement_review_decision", None)
    latest_status.pop("hardware_sensor_procurement_review_decision_summary", None)
    latest_status.pop("hardware_sensor_procurement_review_decision_copy", None)
    latest_status.pop("hardware_sensor_procurement_execution_pack", None)
    latest_status.pop("hardware_sensor_procurement_execution_pack_summary", None)
    latest_status.pop("hardware_sensor_procurement_execution_pack_copy", None)
    latest_status.pop("hardware_sensor_procurement_receipt_intake", None)
    latest_status.pop("hardware_sensor_procurement_receipt_intake_summary", None)
    latest_status.pop("hardware_sensor_procurement_receipt_intake_copy", None)
    latest_status.pop("hardware_sensor_hil_entry_config_precheck", None)
    latest_status.pop("hardware_sensor_hil_entry_config_precheck_summary", None)
    latest_status.pop("hardware_sensor_hil_entry_config_precheck_copy", None)
    latest_status.pop("hardware_sensor_hil_entry_readiness_review", None)
    latest_status.pop("hardware_sensor_hil_entry_readiness_review_summary", None)
    latest_status.pop("hardware_sensor_hil_entry_readiness_review_copy", None)
    latest_status.pop("hardware_sensor_hil_entry_execution_pack", None)
    latest_status.pop("hardware_sensor_hil_entry_execution_pack_summary", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_intake", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_intake_summary", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_review_decision", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_review_decision_summary", None)
    latest_status.pop("robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_review_handoff", None)
    latest_status.pop("hardware_sensor_hil_entry_callback_review_handoff_summary", None)
    latest_status.pop("robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary", None)
    latest_status.pop("pr5_review_thread_closeout", None)
    latest_status.pop("pr5_review_thread_closeout_summary", None)
    latest_status.pop("robot_diagnostics_pr5_review_thread_closeout_summary", None)
    latest_status.pop("pr5_vendor_source_review_packet", None)
    latest_status.pop("pr5_vendor_source_review_packet_summary", None)
    latest_status.pop("robot_diagnostics_pr5_vendor_source_review_packet_summary", None)
    latest_status.pop("pr5_vendor_source_review_reply_dispatch", None)
    latest_status.pop("pr5_vendor_source_review_reply_dispatch_summary", None)
    latest_status.pop(
        "robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary",
        None,
    )
    latest_status.pop("pr5_mandatory_sensor_source_alignment", None)
    latest_status.pop("pr5_mandatory_sensor_source_alignment_summary", None)
    latest_status.pop(
        "robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary",
        None,
    )
    latest_status.pop("hardware_real_material_escalation_request", None)
    latest_status.pop("hardware_real_material_escalation_request_summary", None)
    latest_status.pop("robot_diagnostics_hardware_real_material_escalation_request_summary", None)
    latest_status.pop("real_material_readiness_board", None)
    latest_status.pop("real_material_readiness_board_summary", None)
    latest_status.pop("robot_diagnostics_real_material_readiness_board_summary", None)
    latest_status.pop("real_material_evidence_intake", None)
    latest_status.pop("real_material_evidence_intake_summary", None)
    latest_status.pop("robot_diagnostics_real_material_evidence_intake_summary", None)
    latest_status.pop("real_material_followup_escalation_status", None)
    latest_status.pop("real_material_followup_escalation_status_summary", None)
    latest_status.pop(
        "robot_diagnostics_real_material_followup_escalation_status_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_followup_escalation_status", None)
    latest_status.pop(
        "field_evidence_real_material_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_owner_ack_intake", None)
    latest_status.pop("field_evidence_real_material_owner_ack_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_owner_ack_intake_copy", None)
    latest_status.pop("field_evidence_real_material_owner_ack_review_decision", None)
    latest_status.pop(
        "field_evidence_real_material_owner_ack_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary",
        None,
    )
    latest_status.pop("field_evidence_real_material_owner_ack_review_decision_copy", None)
    latest_status.pop("field_evidence_material_blocker_escalation_pack", None)
    latest_status.pop(
        "field_evidence_material_blocker_escalation_pack_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary",
        None,
    )
    latest_status.pop("field_evidence_material_blocker_escalation_pack_copy", None)
    latest_status.pop("field_evidence_material_resolution_intake", None)
    latest_status.pop("field_evidence_material_resolution_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_intake_summary",
        None,
    )
    latest_status.pop("field_evidence_material_resolution_intake_copy", None)
    latest_status.pop("field_evidence_material_resolution_review_decision", None)
    latest_status.pop(
        "field_evidence_material_resolution_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_review_decision_summary",
        None,
    )
    latest_status.pop("field_evidence_material_resolution_review_decision_copy", None)
    latest_status.pop("field_evidence_material_resolution_review_handoff", None)
    latest_status.pop(
        "field_evidence_material_resolution_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_review_handoff_summary",
        None,
    )
    latest_status.pop("field_evidence_material_resolution_review_handoff_copy", None)
    latest_status.pop(
        "field_evidence_material_resolution_followup_escalation_status",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_followup_escalation_status_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_intake",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_intake_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_intake_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_decision",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_decision_copy",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_handoff",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "field_evidence_material_resolution_owner_response_review_handoff_copy",
        None,
    )
    latest_status.pop("elevator_action_feedback_trace", None)
    latest_status.pop("robot_diagnostics_elevator_action_feedback_trace_summary", None)
    latest_status.pop("elevator_field_evidence_trace_callback_intake", None)
    latest_status.pop("elevator_field_evidence_trace_callback_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary",
        None,
    )
    latest_status.pop("elevator_field_evidence_trace_callback_review_decision", None)
    latest_status.pop("elevator_field_evidence_trace_callback_review_decision_summary", None)
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary",
        None,
    )
    latest_status.pop("elevator_field_evidence_trace_callback_review_handoff", None)
    latest_status.pop("elevator_field_evidence_trace_callback_review_handoff_summary", None)
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary",
        None,
    )
    latest_status.pop("elevator_field_evidence_trace_material_backfill_intake", None)
    latest_status.pop("elevator_field_evidence_trace_material_backfill_intake_summary", None)
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary",
        None,
    )
    latest_status.pop("elevator_field_evidence_trace_material_backfill_review_decision", None)
    latest_status.pop(
        "elevator_field_evidence_trace_material_backfill_review_decision_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary",
        None,
    )
    latest_status.pop("elevator_field_evidence_trace_material_backfill_review_handoff", None)
    latest_status.pop(
        "elevator_field_evidence_trace_material_backfill_review_handoff_summary",
        None,
    )
    latest_status.pop(
        "robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary",
        None,
    )
    last_task = dict(latest_status.get("last_task") or {})
    task_record_path = str(
        latest_status.get("task_record_path")
        or last_task.get("task_record_path")
        or ""
    )
    task_record = _read_task_record(task_record_path)
    task_terminal_completion_mainline_source = (
        task_terminal_completion_mainline_source
        or _task_terminal_completion_mainline_source_from_payloads(
            task_record,
            latest_status,
            last_task,
        )
    )
    task_terminal_field_material_intake_source = (
        task_terminal_field_material_intake_source
        or _task_terminal_field_material_intake_source_from_payloads(
            task_record,
            latest_status,
            last_task,
        )
    )
    task_terminal_field_material_review_decision_source = (
        task_terminal_field_material_review_decision_source
        or _task_terminal_field_material_review_decision_source_from_payloads(
            task_record,
            latest_status,
            last_task,
        )
    )
    elevator_action_feedback_trace, elevator_action_feedback_trace_source = (
        _elevator_action_feedback_trace_from_payloads(task_record, latest_status, last_task)
    )
    elevator_action_feedback_trace_summary = summarize_elevator_action_feedback_trace(
        elevator_action_feedback_trace,
        source=elevator_action_feedback_trace_source,
    )
    elevator_field_evidence_trace_callback_intake_source = (
        elevator_field_evidence_trace_callback_intake_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_INTAKE_SUMMARY", "")
        or elevator_field_evidence_trace_callback_intake_source
    )
    elevator_field_evidence_trace_callback_intake_summary = (
        summarize_elevator_field_evidence_trace_callback_intake(
            elevator_field_evidence_trace_callback_intake_source
        )
    )
    elevator_field_evidence_trace_callback_review_decision_source = (
        elevator_field_evidence_trace_callback_review_decision_ref
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or elevator_field_evidence_trace_callback_review_decision_source
    )
    elevator_field_evidence_trace_callback_review_decision_summary = (
        summarize_elevator_field_evidence_trace_callback_review_decision(
            elevator_field_evidence_trace_callback_review_decision_source
        )
    )
    elevator_field_evidence_trace_callback_review_handoff_source = (
        elevator_field_evidence_trace_callback_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or elevator_field_evidence_trace_callback_review_handoff_source
    )
    elevator_field_evidence_trace_callback_review_handoff_summary = (
        summarize_elevator_field_evidence_trace_callback_review_handoff(
            elevator_field_evidence_trace_callback_review_handoff_source
        )
    )
    elevator_field_evidence_trace_material_backfill_intake_source = (
        elevator_field_evidence_trace_material_backfill_intake_ref
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_INTAKE_SUMMARY",
            "",
        )
        or elevator_field_evidence_trace_material_backfill_intake_source
    )
    elevator_field_evidence_trace_material_backfill_intake_summary = (
        summarize_elevator_field_evidence_trace_material_backfill_intake(
            elevator_field_evidence_trace_material_backfill_intake_source
        )
    )
    elevator_field_evidence_trace_material_backfill_review_decision_source = (
        elevator_field_evidence_trace_material_backfill_review_decision_ref
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_DECISION_SUMMARY",
            "",
        )
        or elevator_field_evidence_trace_material_backfill_review_decision_source
    )
    elevator_field_evidence_trace_material_backfill_review_decision_summary = (
        summarize_elevator_field_evidence_trace_material_backfill_review_decision(
            elevator_field_evidence_trace_material_backfill_review_decision_source
        )
    )
    elevator_field_evidence_trace_material_backfill_review_handoff_source = (
        elevator_field_evidence_trace_material_backfill_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ELEVATOR_FIELD_EVIDENCE_TRACE_MATERIAL_BACKFILL_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or elevator_field_evidence_trace_material_backfill_review_handoff_source
    )
    elevator_field_evidence_trace_material_backfill_review_handoff_summary = (
        summarize_elevator_field_evidence_trace_material_backfill_review_handoff(
            elevator_field_evidence_trace_material_backfill_review_handoff_source
        )
    )
    route_proof_summary, route_proof_source = _extract_route_proof_summary(latest_status, last_task)
    route_proof_status = classify_route_proof(route_proof_summary, source=route_proof_source)
    elevator_assist, elevator_assist_source = extract_elevator_assist(latest_status, last_task)
    elevator_assist_status = classify_elevator_assist(elevator_assist, source=elevator_assist_source)
    traceability = coalesce_traceability_fields(
        latest_status,
        task_record=task_record,
        last_task=last_task,
    )
    source = normalize_evidence_source(traceability["source"])
    result_path = traceability["result_path"]
    evidence_ref = traceability["evidence_ref"]
    failure_code = traceability["failure_code"]
    human_intervention_required = traceability["human_intervention_required"]
    state_transition_history = traceability["state_transition_history"]
    route_progress = traceability["route_progress"]
    last_task["source"] = source
    last_task["result_path"] = result_path
    if "evidence_ref" in last_task:
        last_task["evidence_ref"] = evidence_ref
    else:
        last_task["evidence_ref"] = (
            str(task_record.get("result_path", "")).strip() or evidence_ref
        )
    last_task["failure_code"] = failure_code
    last_task["state_transition_history"] = state_transition_history
    last_task["human_intervention_required"] = human_intervention_required
    last_task["route_progress"] = route_progress
    failure = {
        "state": latest_status.get("state", ""),
        "message": latest_status.get("message", ""),
        "error_code": latest_status.get("error_code") or last_task.get("error_code", ""),
        "final_state": latest_status.get("final_state") or last_task.get("final_state", ""),
        "task_record_path": latest_status.get("task_record_path") or last_task.get("task_record_path", ""),
        "result_path": result_path,
        "source": source,
        "evidence_ref": evidence_ref,
        "failure_code": failure_code,
        "human_intervention_required": human_intervention_required,
        "state_transition_history": state_transition_history,
        "route_progress": route_progress,
    }
    review_decision_log, decision_index = load_review_decision_log(review_decision_log_ref)
    route_task_field_run_readiness_summary = summarize_route_task_field_run_readiness(
        route_task_field_run_readiness_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS", "")
    )
    route_task_field_run_intake_summary = summarize_route_task_field_run_intake(
        route_task_field_run_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE", "")
    )
    route_task_field_run_review_summary = summarize_route_task_field_run_review(
        route_task_field_run_review_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW", "")
    )
    route_task_field_run_execution_pack_summary = summarize_route_task_field_run_execution_pack(
        route_task_field_run_execution_pack_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK", "")
    )
    route_task_field_retest_execution_pack_source = (
        route_task_field_retest_execution_pack_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY", "")
        or route_task_field_retest_execution_pack_source
    )
    route_task_field_retest_execution_pack_summary = summarize_route_task_field_retest_execution_pack(
        route_task_field_retest_execution_pack_source
    )
    route_task_field_retest_session_handoff_source = (
        route_task_field_retest_session_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY", "")
        or route_task_field_retest_session_handoff_source
    )
    route_task_field_retest_session_handoff_summary = summarize_route_task_field_retest_session_handoff(
        route_task_field_retest_session_handoff_source
    )
    route_task_field_retest_result_intake_source = (
        route_task_field_retest_result_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY", "")
        or route_task_field_retest_result_intake_source
    )
    route_task_field_retest_result_intake_summary = summarize_route_task_field_retest_result_intake(
        route_task_field_retest_result_intake_source
    )
    route_task_field_retest_result_reconciliation_source = (
        route_task_field_retest_result_reconciliation_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY", "")
        or route_task_field_retest_result_reconciliation_source
    )
    route_task_field_retest_result_reconciliation_summary = (
        summarize_route_task_field_retest_result_reconciliation(
            route_task_field_retest_result_reconciliation_source
        )
    )
    route_task_field_retest_material_pack_source = (
        route_task_field_retest_material_pack_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY", "")
        or route_task_field_retest_material_pack_source
    )
    route_task_field_retest_material_pack_summary = summarize_route_task_field_retest_material_pack(
        route_task_field_retest_material_pack_source
    )
    route_task_field_retest_material_callback_packet_source = (
        route_task_field_retest_material_callback_packet_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY", "")
        or route_task_field_retest_material_callback_packet_source
    )
    route_task_field_retest_material_callback_packet_summary = (
        summarize_route_task_field_retest_material_callback_packet(
            route_task_field_retest_material_callback_packet_source
        )
    )
    route_task_field_retest_material_callback_review_decision_source = (
        route_task_field_retest_material_callback_review_decision_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_material_callback_review_decision_source
    )
    route_task_field_retest_material_callback_review_decision_summary = (
        summarize_route_task_field_retest_material_callback_review_decision(
            route_task_field_retest_material_callback_review_decision_source
        )
    )
    route_task_field_retest_operator_drill_source = (
        route_task_field_retest_operator_drill_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY", "")
        or route_task_field_retest_operator_drill_source
    )
    route_task_field_retest_operator_drill_summary = summarize_route_task_field_retest_operator_drill(
        route_task_field_retest_operator_drill_source
    )
    route_task_field_retest_drill_console_source = (
        route_task_field_retest_drill_console_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY", "")
        or route_task_field_retest_drill_console_source
    )
    route_task_field_retest_drill_console_summary = summarize_route_task_field_retest_drill_console(
        route_task_field_retest_drill_console_source
    )
    route_task_field_retest_acceptance_brief_source = (
        route_task_field_retest_acceptance_brief_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY", "")
        or route_task_field_retest_acceptance_brief_source
    )
    route_task_field_retest_acceptance_brief_summary = (
        summarize_route_task_field_retest_acceptance_brief(
            route_task_field_retest_acceptance_brief_source
        )
    )
    route_task_field_retest_acceptance_review_decision_source = (
        route_task_field_retest_acceptance_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_review_decision_source
    )
    route_task_field_retest_acceptance_review_decision_summary = (
        summarize_route_task_field_retest_acceptance_review_decision(
            route_task_field_retest_acceptance_review_decision_source
        )
    )
    route_task_field_retest_acceptance_execution_pack_source = (
        route_task_field_retest_acceptance_execution_pack_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_pack_source
    )
    route_task_field_retest_acceptance_execution_pack_summary = (
        summarize_route_task_field_retest_acceptance_execution_pack(
            route_task_field_retest_acceptance_execution_pack_source
        )
    )
    route_task_field_retest_acceptance_execution_callback_intake_source = (
        route_task_field_retest_acceptance_execution_callback_intake_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_callback_intake_source
    )
    route_task_field_retest_acceptance_execution_callback_intake_summary = (
        summarize_route_task_field_retest_acceptance_execution_callback_intake(
            route_task_field_retest_acceptance_execution_callback_intake_source
        )
    )
    route_task_field_retest_acceptance_execution_callback_review_decision_source = (
        route_task_field_retest_acceptance_execution_callback_review_decision_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_callback_review_decision_source
    )
    route_task_field_retest_acceptance_execution_callback_review_decision_summary = (
        summarize_route_task_field_retest_acceptance_execution_callback_review_decision(
            route_task_field_retest_acceptance_execution_callback_review_decision_source
        )
    )
    route_task_field_retest_acceptance_execution_callback_review_handoff_source = (
        route_task_field_retest_acceptance_execution_callback_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_callback_review_handoff_source
    )
    route_task_field_retest_acceptance_execution_callback_review_handoff_summary = (
        summarize_route_task_field_retest_acceptance_execution_callback_review_handoff(
            route_task_field_retest_acceptance_execution_callback_review_handoff_source
        )
    )
    route_task_field_retest_acceptance_execution_handoff_intake_source = (
        route_task_field_retest_acceptance_execution_handoff_intake_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_handoff_intake_source
    )
    route_task_field_retest_acceptance_execution_handoff_intake_summary = (
        summarize_route_task_field_retest_acceptance_execution_handoff_intake(
            route_task_field_retest_acceptance_execution_handoff_intake_source
        )
    )
    route_task_field_retest_acceptance_execution_rerun_queue_source = (
        route_task_field_retest_acceptance_execution_rerun_queue_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_rerun_queue_source
    )
    route_task_field_retest_acceptance_execution_rerun_queue_summary = (
        summarize_route_task_field_retest_acceptance_execution_rerun_queue(
            route_task_field_retest_acceptance_execution_rerun_queue_source
        )
    )
    route_task_field_retest_acceptance_execution_rerun_result_intake_source = (
        route_task_field_retest_acceptance_execution_rerun_result_intake_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_rerun_result_intake_source
    )
    route_task_field_retest_acceptance_execution_rerun_result_intake_summary = (
        summarize_route_task_field_retest_acceptance_execution_rerun_result_intake(
            route_task_field_retest_acceptance_execution_rerun_result_intake_source
        )
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_decision_source = (
        route_task_field_retest_acceptance_execution_rerun_result_review_decision_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_rerun_result_review_decision_source
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary = (
        summarize_route_task_field_retest_acceptance_execution_rerun_result_review_decision(
            route_task_field_retest_acceptance_execution_rerun_result_review_decision_source
        )
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source = (
        route_task_field_retest_acceptance_execution_rerun_result_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source
    )
    route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary = (
        summarize_route_task_field_retest_acceptance_execution_rerun_result_review_handoff(
            route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source
        )
    )
    field_evidence_rerun_material_dispatch_source = (
        field_evidence_rerun_material_dispatch_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH", "")
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_MATERIAL_DISPATCH_SUMMARY", "")
        or field_evidence_rerun_material_dispatch_source
    )
    field_evidence_rerun_material_dispatch_summary = (
        summarize_field_evidence_rerun_material_dispatch(
            field_evidence_rerun_material_dispatch_source
        )
    )
    field_evidence_rerun_callback_intake_source = (
        field_evidence_rerun_callback_intake_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE", "")
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_INTAKE_SUMMARY", "")
        or field_evidence_rerun_callback_intake_source
    )
    field_evidence_rerun_callback_intake_summary = (
        summarize_field_evidence_rerun_callback_intake(
            field_evidence_rerun_callback_intake_source
        )
    )
    field_evidence_rerun_callback_review_decision_source = (
        field_evidence_rerun_callback_review_decision_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION", "")
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_callback_review_decision_source
    )
    field_evidence_rerun_callback_review_decision_summary = (
        summarize_field_evidence_rerun_callback_review_decision(
            field_evidence_rerun_callback_review_decision_source
        )
    )
    field_evidence_rerun_callback_review_handoff_source = (
        field_evidence_rerun_callback_review_handoff_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF", "")
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_callback_review_handoff_source
    )
    field_evidence_rerun_callback_review_handoff_summary = (
        summarize_field_evidence_rerun_callback_review_handoff(
            field_evidence_rerun_callback_review_handoff_source
        )
    )
    field_evidence_rerun_handoff_intake_source = (
        field_evidence_rerun_handoff_intake_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE", "")
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_HANDOFF_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_handoff_intake_source
    )
    field_evidence_rerun_handoff_intake_summary = (
        summarize_field_evidence_rerun_handoff_intake(
            field_evidence_rerun_handoff_intake_source
        )
    )
    # 这组 rerun status source 只信任字段级别证据，不能扩到 aggregate summary。
    field_evidence_rerun_queue_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_queue_summary",
            "field_evidence_rerun_queue_summary",
            "field_evidence_rerun_queue",
        ],
        default={},
    )
    field_evidence_rerun_queue_source = (
        field_evidence_rerun_queue_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_QUEUE", "")
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_QUEUE_SUMMARY", "")
        or field_evidence_rerun_queue_status_source
    )
    field_evidence_rerun_queue_summary = summarize_field_evidence_rerun_queue(
        field_evidence_rerun_queue_source
    )
    # execution_pack 历史上只读 diagnostics_source，不能新增 latest_status 候选。
    field_evidence_rerun_execution_pack_status_source = first_dict_value(
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_pack_summary"
        ),
        diagnostics_source.get("field_evidence_rerun_execution_pack_summary"),
        diagnostics_source.get("field_evidence_rerun_execution_pack"),
        default={},
    )
    field_evidence_rerun_execution_pack_source = (
        field_evidence_rerun_execution_pack_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_PACK_SUMMARY", "")
        or field_evidence_rerun_execution_pack_status_source
    )
    field_evidence_rerun_execution_pack_summary = (
        summarize_field_evidence_rerun_execution_pack(
            field_evidence_rerun_execution_pack_source
        )
    )
    # callback_intake 也保持 diagnostics_source-only，避免运行时状态改变来源边界。
    field_evidence_rerun_execution_callback_intake_status_source = first_dict_value(
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary"
        ),
        diagnostics_source.get("field_evidence_rerun_execution_callback_intake_summary"),
        diagnostics_source.get("field_evidence_rerun_execution_callback_intake"),
        default={},
    )
    field_evidence_rerun_execution_callback_intake_source = (
        field_evidence_rerun_execution_callback_intake_ref
        or os.environ.get("TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE", "")
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_callback_intake_status_source
    )
    field_evidence_rerun_execution_callback_intake_summary = (
        summarize_field_evidence_rerun_execution_callback_intake(
            field_evidence_rerun_execution_callback_intake_source
        )
    )
    # review_decision 保留 latest_status 优先，再查 diagnostics_source 的字段级顺序。
    field_evidence_rerun_execution_callback_review_decision_status_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            [
                "robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary",
                "field_evidence_rerun_execution_callback_review_decision_summary",
                "field_evidence_rerun_execution_callback_review_decision",
            ],
            default={},
        )
    )
    field_evidence_rerun_execution_callback_review_decision_source = (
        field_evidence_rerun_execution_callback_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_callback_review_decision_status_source
    )
    field_evidence_rerun_execution_callback_review_decision_summary = (
        summarize_field_evidence_rerun_execution_callback_review_decision(
            field_evidence_rerun_execution_callback_review_decision_source
        )
    )
    # review_handoff 同样不接 summary/diagnostics_summary，避免扩大证据来源。
    field_evidence_rerun_execution_callback_review_handoff_status_source = (
        first_status_dict(
            latest_status,
            diagnostics_source,
            [
                "robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary",
                "field_evidence_rerun_execution_callback_review_handoff_summary",
                "field_evidence_rerun_execution_callback_review_handoff",
            ],
            default={},
        )
    )
    field_evidence_rerun_execution_callback_review_handoff_source = (
        field_evidence_rerun_execution_callback_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_callback_review_handoff_status_source
    )
    field_evidence_rerun_execution_callback_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_callback_review_handoff(
            field_evidence_rerun_execution_callback_review_handoff_source
        )
    )
    # result 三条链只取字段级证据，避免 aggregate summary 混入验收边界。
    field_evidence_rerun_execution_result_intake_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_intake_summary",
            "field_evidence_rerun_execution_result_intake_summary",
            "field_evidence_rerun_execution_result_intake",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_intake_source = (
        field_evidence_rerun_execution_result_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_intake_status_source
    )
    field_evidence_rerun_execution_result_intake_summary = (
        summarize_field_evidence_rerun_execution_result_intake(
            field_evidence_rerun_execution_result_intake_source
        )
    )
    # 保持 latest -> diagnostics 的字段级顺序，不新增 summary/diagnostics_summary。
    field_evidence_rerun_execution_result_review_decision_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary",
            "field_evidence_rerun_execution_result_review_decision_summary",
            "field_evidence_rerun_execution_result_review_decision",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_review_decision_source = (
        field_evidence_rerun_execution_result_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_review_decision_status_source
    )
    field_evidence_rerun_execution_result_review_decision_summary = (
        summarize_field_evidence_rerun_execution_result_review_decision(
            field_evidence_rerun_execution_result_review_decision_source
        )
    )
    # handoff 与 intake/review 共用窄边界，后续 ref/env 字符串覆盖保持不变。
    field_evidence_rerun_execution_result_review_handoff_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary",
            "field_evidence_rerun_execution_result_review_handoff_summary",
            "field_evidence_rerun_execution_result_review_handoff",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_review_handoff_source = (
        field_evidence_rerun_execution_result_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_review_handoff_status_source
    )
    field_evidence_rerun_execution_result_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_result_review_handoff(
            field_evidence_rerun_execution_result_review_handoff_source
        )
    )
    # acceptance 结果仍只读取字段级证据，避免 aggregate summary 被误认成验收材料。
    field_evidence_rerun_execution_result_acceptance_packet_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary",
            "field_evidence_rerun_execution_result_acceptance_packet_summary",
            "field_evidence_rerun_execution_result_acceptance_packet",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_packet_source = (
        field_evidence_rerun_execution_result_acceptance_packet_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_PACKET_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_packet_status_source
    )
    field_evidence_rerun_execution_result_acceptance_packet_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_packet(
            field_evidence_rerun_execution_result_acceptance_packet_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_backfill_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary",
            "field_evidence_rerun_execution_result_acceptance_backfill_summary",
            "field_evidence_rerun_execution_result_acceptance_backfill",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_backfill_source = (
        field_evidence_rerun_execution_result_acceptance_backfill_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_backfill_status_source
    )
    field_evidence_rerun_execution_result_acceptance_backfill_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_backfill(
            field_evidence_rerun_execution_result_acceptance_backfill_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_backfill_review_decision_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_backfill_review_decision",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_backfill_review_decision_source = (
        field_evidence_rerun_execution_result_acceptance_backfill_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_BACKFILL_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_backfill_review_decision_status_source
    )
    field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_backfill_review_decision(
            field_evidence_rerun_execution_result_acceptance_backfill_review_decision_source
        )
    )
    # 这组 handoff 状态来源仍只接受字段级证据别名，避免把 aggregate summary
    # 误当作 rerun acceptance handoff 证据；后面的 ref/env 覆盖顺序保持原样。
    field_evidence_rerun_execution_result_acceptance_review_handoff_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
            "field_evidence_rerun_execution_result_acceptance_review_handoff_summary",
            "field_evidence_rerun_execution_result_acceptance_review_handoff",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_review_handoff_source = (
        field_evidence_rerun_execution_result_acceptance_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_review_handoff_status_source
    )
    field_evidence_rerun_execution_result_acceptance_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_review_handoff(
            field_evidence_rerun_execution_result_acceptance_review_handoff_source
        )
    )
    # handoff intake 也保持字段级证据边界，不新增 summary/diagnostics_summary 兜底。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_source
        )
    )
    # review decision 只收敛重复选择代码，候选顺序和证据边界保持旧行为。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_source
        )
    )
    # handoff-intake 后续三段仍只读取字段级证据别名，避免 aggregate summary
    # 混入复跑验收交接链；ref/env 字符串覆盖逻辑在后面保持原有兼容路径。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_source
        )
    )
    # 该字段只收敛 dict status source 的选择方式，env/ref 覆盖仍在后面保持原顺序。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary",
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision",
        ],
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_source
        )
    )
    # preserved_source 优先级属于字段级证据边界；空 dict 也要按旧的 isinstance 命中保留。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_status_source = first_dict_value(
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_preserved_source,
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff"
        ),
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_source
        )
    )
    # preserved_source 先于 diagnostics fallback，避免把字段级 ACK 证据扩展成整包诊断语义。
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_status_source = first_dict_value(
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_preserved_source,
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake"
        ),
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_status_source = first_non_empty_dict_value(
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_preserved_source,
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision"
        ),
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_status_source = first_non_empty_dict_value(
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_preserved_source,
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff"
        ),
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_source
        )
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_status_source = first_non_empty_dict_value(
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_preserved_source,
        diagnostics_source.get(
            "robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary"
        ),
        diagnostics_source.get(
            "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status"
        ),
        default={},
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source = (
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_RERUN_EXECUTION_RESULT_ACCEPTANCE_HANDOFF_INTAKE_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_status_source
    )
    field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary = (
        summarize_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_source
        )
    )
    field_evidence_real_material_request_dispatch_status_source = first_status_dict(
        latest_status,
        diagnostics_source,
        [
            "robot_diagnostics_field_evidence_real_material_request_dispatch_summary",
            "field_evidence_real_material_request_dispatch_summary",
            "field_evidence_real_material_request_dispatch",
        ],
        default={},
    )
    field_evidence_real_material_request_dispatch_source = (
        field_evidence_real_material_request_dispatch_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_REQUEST_DISPATCH_SUMMARY",
            "",
        )
        or field_evidence_real_material_request_dispatch_status_source
    )
    field_evidence_real_material_request_dispatch_summary = (
        summarize_field_evidence_real_material_request_dispatch(
            field_evidence_real_material_request_dispatch_source
        )
    )
    field_evidence_real_material_response_intake_status_source = (
        first_non_empty_dict_then_first_dict(
            field_evidence_real_material_response_intake_preserved_source,
            latest_status.get(
                "robot_diagnostics_field_evidence_real_material_response_intake_summary"
            ),
            latest_status.get("field_evidence_real_material_response_intake_summary"),
            latest_status.get("field_evidence_real_material_response_intake"),
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_real_material_response_intake_summary"
            ),
            diagnostics_source.get("field_evidence_real_material_response_intake_summary"),
            diagnostics_source.get("field_evidence_real_material_response_intake"),
            default={},
        )
    )
    field_evidence_real_material_response_intake_source = (
        field_evidence_real_material_response_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_real_material_response_intake_status_source
    )
    field_evidence_real_material_response_intake_summary = (
        summarize_field_evidence_real_material_response_intake(
            field_evidence_real_material_response_intake_source
        )
    )
    field_evidence_real_material_response_review_decision_status_source = (
        first_non_empty_dict_then_first_dict(
            field_evidence_real_material_response_review_decision_preserved_source,
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_real_material_response_review_decision_summary"
            ),
            diagnostics_source.get(
                "field_evidence_real_material_response_review_decision_summary"
            ),
            diagnostics_source.get("field_evidence_real_material_response_review_decision"),
            default={},
        )
    )
    field_evidence_real_material_response_review_decision_source = (
        field_evidence_real_material_response_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_real_material_response_review_decision_status_source
    )
    field_evidence_real_material_response_review_decision_summary = (
        summarize_field_evidence_real_material_response_review_decision(
            field_evidence_real_material_response_review_decision_source
        )
    )
    field_evidence_real_material_response_review_handoff_status_source = (
        first_non_empty_dict_then_first_dict(
            field_evidence_real_material_response_review_handoff_preserved_source,
            diagnostics_source.get(
                "robot_diagnostics_field_evidence_real_material_response_review_handoff_summary"
            ),
            diagnostics_source.get(
                "field_evidence_real_material_response_review_handoff_summary"
            ),
            diagnostics_source.get("field_evidence_real_material_response_review_handoff"),
            default={},
        )
    )
    field_evidence_real_material_response_review_handoff_source = (
        field_evidence_real_material_response_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_RESPONSE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_real_material_response_review_handoff_status_source
    )
    field_evidence_real_material_response_review_handoff_summary = (
        summarize_field_evidence_real_material_response_review_handoff(
            field_evidence_real_material_response_review_handoff_source
        )
    )
    route_task_field_retest_evidence_dispatch_source = (
        route_task_field_retest_evidence_dispatch_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY", "")
        or route_task_field_retest_evidence_dispatch_source
    )
    route_task_field_retest_evidence_dispatch_summary = (
        summarize_route_task_field_retest_evidence_dispatch(
            route_task_field_retest_evidence_dispatch_source
        )
    )
    route_task_field_retest_callback_intake_source = (
        route_task_field_retest_callback_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY", "")
        or route_task_field_retest_callback_intake_source
    )
    route_task_field_retest_callback_intake_summary = (
        summarize_route_task_field_retest_callback_intake(
            route_task_field_retest_callback_intake_source
        )
    )
    route_task_field_retest_callback_review_decision_source = (
        route_task_field_retest_callback_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY", "")
        or route_task_field_retest_callback_review_decision_source
    )
    route_task_field_retest_callback_review_decision_summary = (
        summarize_route_task_field_retest_callback_review_decision(
            route_task_field_retest_callback_review_decision_source
        )
    )
    route_task_field_retest_review_result_handoff_source = (
        route_task_field_retest_review_result_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY", "")
        or route_task_field_retest_review_result_handoff_source
    )
    route_task_field_retest_review_result_handoff_summary = (
        summarize_route_task_field_retest_review_result_handoff(
            route_task_field_retest_review_result_handoff_source
        )
    )
    route_task_field_retest_result_acceptance_packet_source = (
        route_task_field_retest_result_acceptance_packet_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY", "")
        or route_task_field_retest_result_acceptance_packet_source
    )
    route_task_field_retest_result_acceptance_packet_summary = (
        summarize_route_task_field_retest_result_acceptance_packet(
            route_task_field_retest_result_acceptance_packet_source
        )
    )
    route_task_field_retest_result_acceptance_backfill_source = (
        route_task_field_retest_result_acceptance_backfill_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY", "")
        or route_task_field_retest_result_acceptance_backfill_source
    )
    route_task_field_retest_result_acceptance_backfill_summary = (
        summarize_route_task_field_retest_result_acceptance_backfill(
            route_task_field_retest_result_acceptance_backfill_source
        )
    )
    route_task_field_retest_result_backfill_review_decision_source = (
        route_task_field_retest_result_backfill_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY", "")
        or route_task_field_retest_result_backfill_review_decision_source
    )
    route_task_field_retest_result_backfill_review_decision_summary = (
        summarize_route_task_field_retest_result_backfill_review_decision(
            route_task_field_retest_result_backfill_review_decision_source
        )
    )
    route_task_field_retest_result_review_dispatch_source = (
        route_task_field_retest_result_review_dispatch_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY", "")
        or route_task_field_retest_result_review_dispatch_source
    )
    route_task_field_retest_result_review_dispatch_summary = (
        summarize_route_task_field_retest_result_review_dispatch(
            route_task_field_retest_result_review_dispatch_source
        )
    )
    route_task_field_retest_result_review_intake_source = (
        route_task_field_retest_result_review_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY",
            "",
        )
        or route_task_field_retest_result_review_intake_source
    )
    route_task_field_retest_result_review_intake_summary = (
        summarize_route_task_field_retest_result_review_intake(
            route_task_field_retest_result_review_intake_source
        )
    )
    route_task_field_retest_result_review_decision_source = (
        route_task_field_retest_result_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_result_review_decision_source
    )
    route_task_field_retest_result_review_decision_summary = (
        summarize_route_task_field_retest_result_review_decision(
            route_task_field_retest_result_review_decision_source
        )
    )
    route_task_field_retest_result_review_handoff_source = (
        route_task_field_retest_result_review_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or route_task_field_retest_result_review_handoff_source
    )
    route_task_field_retest_result_review_handoff_summary = (
        summarize_route_task_field_retest_result_review_handoff(
            route_task_field_retest_result_review_handoff_source
        )
    )
    route_task_field_retest_result_callback_intake_source = (
        route_task_field_retest_result_callback_intake_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY", "")
        or route_task_field_retest_result_callback_intake_source
    )
    route_task_field_retest_result_callback_intake_summary = (
        summarize_route_task_field_retest_result_callback_intake(
            route_task_field_retest_result_callback_intake_source
        )
    )
    route_task_field_retest_result_callback_review_decision_source = (
        route_task_field_retest_result_callback_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or route_task_field_retest_result_callback_review_decision_source
    )
    route_task_field_retest_result_callback_review_decision_summary = (
        summarize_route_task_field_retest_result_callback_review_decision(
            route_task_field_retest_result_callback_review_decision_source
        )
    )
    route_task_field_retest_result_callback_review_handoff_source = (
        route_task_field_retest_result_callback_review_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF", "")
        or os.environ.get(
            "TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or route_task_field_retest_result_callback_review_handoff_source
    )
    route_task_field_retest_result_callback_review_handoff_summary = (
        summarize_route_task_field_retest_result_callback_review_handoff(
            route_task_field_retest_result_callback_review_handoff_source
        )
    )
    route_task_field_run_reconciliation_summary = summarize_route_task_field_run_reconciliation(
        route_task_field_run_reconciliation_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION", "")
    )
    route_task_completion_signal_summary = summarize_route_task_completion_signal(
        route_task_completion_signal_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL", "")
    )
    route_task_terminal_completion_rehearsal_summary = (
        summarize_route_task_terminal_completion_rehearsal(
            route_task_terminal_completion_rehearsal_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL", "")
            or os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY", "")
            or route_task_terminal_completion_rehearsal_source
        )
    )
    task_terminal_completion_mainline_summary = summarize_task_terminal_completion_mainline(
        task_terminal_completion_mainline_source
    )
    task_terminal_field_material_intake_summary = (
        summarize_task_terminal_field_material_intake(
            task_terminal_field_material_intake_source
        )
    )
    task_terminal_field_material_review_decision_summary = (
        summarize_task_terminal_field_material_review_decision(
            task_terminal_field_material_review_decision_source
        )
    )
    route_task_terminal_review_decision_source = (
        route_task_terminal_review_decision_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY", "")
        or route_task_terminal_review_decision_source
    )
    route_task_terminal_review_decision_summary = summarize_route_task_terminal_review_decision(
        route_task_terminal_review_decision_source
    )
    route_task_field_run_console_summary = summarize_route_task_field_run_console(
        route_task_field_run_console_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY", "")
    )
    route_task_field_run_evidence_kit_summary = summarize_route_task_field_run_evidence_kit(
        route_task_field_run_evidence_kit_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY", "")
    )
    route_task_field_run_material_bundle_summary = summarize_route_task_field_run_material_bundle(
        route_task_field_run_material_bundle_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY", "")
    )
    route_task_field_run_material_validation_summary = summarize_route_task_field_run_material_validation(
        route_task_field_run_material_validation_ref
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION", "")
        or os.environ.get("TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", "")
    )
    elevator_field_run_material_validation_summary = summarize_elevator_field_run_material_validation(
        elevator_field_run_material_validation_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY", "")
    )
    elevator_field_run_review_summary = summarize_elevator_field_run_review(
        elevator_field_run_review_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY", "")
    )
    elevator_field_run_execution_pack_summary = summarize_elevator_field_run_execution_pack(
        elevator_field_run_execution_pack_ref
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY", "")
    )
    elevator_route_evidence_reconciliation_summary = summarize_elevator_route_evidence_reconciliation(
        elevator_route_evidence_reconciliation_ref
        or os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION", "")
        or os.environ.get("TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY", "")
    )
    route_elevator_field_session_handoff_summary = summarize_route_elevator_field_session_handoff(
        route_elevator_field_session_handoff_ref
        or os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF", "")
        or os.environ.get("TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY", "")
    )
    mobile_route_elevator_field_device_precheck_summary = (
        summarize_mobile_route_elevator_field_device_precheck(
            mobile_route_elevator_field_device_precheck_ref
            or os.environ.get("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK", "")
            or os.environ.get("TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY", "")
        )
    )
    mobile_field_material_intake_summary = summarize_mobile_field_material_intake(
        mobile_field_material_intake_ref
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE", "")
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY", "")
    )
    mobile_field_material_review_decision_source = (
        mobile_field_material_review_decision_ref
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY", "")
        or mobile_field_material_review_decision_source
    )
    mobile_field_material_review_decision_summary = summarize_mobile_field_material_review_decision(
        mobile_field_material_review_decision_source
    )
    mobile_field_material_retest_request_source = (
        mobile_field_material_retest_request_ref
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST", "")
        or os.environ.get("TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY", "")
        or mobile_field_material_retest_request_source
    )
    mobile_field_material_retest_request_summary = summarize_mobile_field_material_retest_request(
        mobile_field_material_retest_request_source
    )
    mobile_real_device_field_trial_acceptance_review_handoff_source = (
        mobile_real_device_field_trial_acceptance_review_handoff_ref
        or os.environ.get("TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF", "")
        or os.environ.get("TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_REVIEW_HANDOFF_SUMMARY", "")
        or mobile_real_device_field_trial_acceptance_review_handoff_source
    )
    mobile_real_device_field_trial_acceptance_review_handoff_summary = (
        summarize_mobile_real_device_field_trial_acceptance_review_handoff(
            mobile_real_device_field_trial_acceptance_review_handoff_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_pack_source = (
        mobile_real_device_field_trial_acceptance_execution_pack_ref
        or os.environ.get("TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_PACK_SUMMARY", "")
        or mobile_real_device_field_trial_acceptance_execution_pack_source
    )
    mobile_real_device_field_trial_acceptance_execution_pack_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_pack(
            mobile_real_device_field_trial_acceptance_execution_pack_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_callback_intake_source = (
        mobile_real_device_field_trial_acceptance_execution_callback_intake_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_callback_intake_source
    )
    mobile_real_device_field_trial_acceptance_execution_callback_intake_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_callback_intake(
            mobile_real_device_field_trial_acceptance_execution_callback_intake_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source = (
        mobile_real_device_field_trial_acceptance_execution_callback_review_decision_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source
    )
    mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_decision(
            mobile_real_device_field_trial_acceptance_execution_callback_review_decision_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source = (
        mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source
    )
    mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff(
            mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_intake_source = (
        mobile_real_device_field_trial_acceptance_execution_handoff_intake_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_handoff_intake_source
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_handoff_intake(
            mobile_real_device_field_trial_acceptance_execution_handoff_intake_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source = (
        mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_DECISION_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_source
        )
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source = (
        mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_MOBILE_REAL_DEVICE_FIELD_TRIAL_ACCEPTANCE_EXECUTION_HANDOFF_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source
    )
    mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary = (
        summarize_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_source
        )
    )
    wave_rover_feedback_replay_source = (
        wave_rover_feedback_replay_ref
        or os.environ.get("TRASHBOT_WAVE_ROVER_FEEDBACK_REPLAY", "")
        or os.environ.get("TRASHBOT_WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY", "")
        or wave_rover_feedback_replay_source
    )
    wave_rover_feedback_replay_summary = summarize_wave_rover_feedback_replay(
        wave_rover_feedback_replay_source
    )
    wave_rover_hil_packet_intake_source = (
        wave_rover_hil_packet_intake_ref
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_INTAKE", "")
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY", "")
        or wave_rover_hil_packet_intake_source
    )
    wave_rover_hil_packet_intake_summary = summarize_wave_rover_hil_packet_intake(
        wave_rover_hil_packet_intake_source
    )
    wave_rover_hil_packet_review_decision_source = (
        wave_rover_hil_packet_review_decision_ref
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY", "")
        or wave_rover_hil_packet_review_decision_source
    )
    wave_rover_hil_packet_review_decision_summary = (
        summarize_wave_rover_hil_packet_review_decision(
            wave_rover_hil_packet_review_decision_source
        )
    )
    wave_rover_hil_packet_execution_pack_source = (
        wave_rover_hil_packet_execution_pack_ref
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY", "")
        or wave_rover_hil_packet_execution_pack_source
    )
    wave_rover_hil_packet_execution_pack_summary = (
        summarize_wave_rover_hil_packet_execution_pack(
            wave_rover_hil_packet_execution_pack_source
        )
    )
    wave_rover_hil_packet_collection_drill_source = (
        wave_rover_hil_packet_collection_drill_ref
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL", "")
        or os.environ.get("TRASHBOT_WAVE_ROVER_HIL_PACKET_COLLECTION_DRILL_SUMMARY", "")
        or wave_rover_hil_packet_collection_drill_source
    )
    wave_rover_hil_packet_collection_drill_summary = (
        summarize_wave_rover_hil_packet_collection_drill(
            wave_rover_hil_packet_collection_drill_source
        )
    )
    hardware_baseline_review_source = (
        hardware_baseline_review_ref
        or os.environ.get("TRASHBOT_HARDWARE_BASELINE_REVIEW", "")
        or os.environ.get("TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY", "")
        or hardware_baseline_review_source
    )
    hardware_baseline_review_summary = summarize_hardware_baseline_review(
        hardware_baseline_review_source
    )
    hardware_baseline_source_alignment_source = (
        hardware_baseline_source_alignment_ref
        or os.environ.get("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT", "")
        or os.environ.get("TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY", "")
        or hardware_baseline_source_alignment_source
    )
    hardware_baseline_source_alignment_summary = (
        summarize_hardware_baseline_source_alignment(
            hardware_baseline_source_alignment_source
        )
    )
    hardware_sensor_procurement_intake_source = (
        hardware_sensor_procurement_intake_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY", "")
        or hardware_sensor_procurement_intake_source
    )
    hardware_sensor_procurement_intake_summary = summarize_hardware_sensor_procurement_intake(
        hardware_sensor_procurement_intake_source
    )
    hardware_sensor_procurement_review_decision_source = (
        hardware_sensor_procurement_review_decision_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY", "")
        or hardware_sensor_procurement_review_decision_source
    )
    hardware_sensor_procurement_review_decision_summary = (
        summarize_hardware_sensor_procurement_review_decision(
            hardware_sensor_procurement_review_decision_source
        )
    )
    hardware_sensor_procurement_execution_pack_source = (
        hardware_sensor_procurement_execution_pack_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY", "")
        or hardware_sensor_procurement_execution_pack_source
    )
    hardware_sensor_procurement_execution_pack_summary = (
        summarize_hardware_sensor_procurement_execution_pack(
            hardware_sensor_procurement_execution_pack_source
        )
    )
    hardware_sensor_procurement_receipt_intake_source = (
        hardware_sensor_procurement_receipt_intake_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY", "")
        or hardware_sensor_procurement_receipt_intake_source
    )
    hardware_sensor_procurement_receipt_intake_summary = (
        summarize_hardware_sensor_procurement_receipt_intake(
            hardware_sensor_procurement_receipt_intake_source
        )
    )
    hardware_sensor_hil_entry_config_precheck_source = (
        hardware_sensor_hil_entry_config_precheck_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CONFIG_PRECHECK_SUMMARY", "")
        or hardware_sensor_hil_entry_config_precheck_source
    )
    hardware_sensor_hil_entry_config_precheck_summary = (
        summarize_hardware_sensor_hil_entry_config_precheck(
            hardware_sensor_hil_entry_config_precheck_source
        )
    )
    hardware_sensor_hil_entry_readiness_review_source = (
        hardware_sensor_hil_entry_readiness_review_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_READINESS_REVIEW_SUMMARY", "")
        or hardware_sensor_hil_entry_readiness_review_source
    )
    hardware_sensor_hil_entry_readiness_review_summary = (
        summarize_hardware_sensor_hil_entry_readiness_review(
            hardware_sensor_hil_entry_readiness_review_source
        )
    )
    hardware_sensor_hil_entry_execution_pack_source = (
        hardware_sensor_hil_entry_execution_pack_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_EXECUTION_PACK_SUMMARY", "")
        or hardware_sensor_hil_entry_execution_pack_source
    )
    hardware_sensor_hil_entry_execution_pack_summary = (
        summarize_hardware_sensor_hil_entry_execution_pack(
            hardware_sensor_hil_entry_execution_pack_source
        )
    )
    hardware_sensor_hil_entry_callback_intake_source = (
        hardware_sensor_hil_entry_callback_intake_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_INTAKE_SUMMARY", "")
        or hardware_sensor_hil_entry_callback_intake_source
    )
    hardware_sensor_hil_entry_callback_intake_summary = (
        summarize_hardware_sensor_hil_entry_callback_intake(
            hardware_sensor_hil_entry_callback_intake_source
        )
    )
    hardware_sensor_hil_entry_callback_review_decision_source = (
        hardware_sensor_hil_entry_callback_review_decision_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_DECISION_SUMMARY", "")
        or hardware_sensor_hil_entry_callback_review_decision_source
    )
    hardware_sensor_hil_entry_callback_review_decision_summary = (
        summarize_hardware_sensor_hil_entry_callback_review_decision(
            hardware_sensor_hil_entry_callback_review_decision_source
        )
    )
    hardware_sensor_hil_entry_callback_review_handoff_source = (
        hardware_sensor_hil_entry_callback_review_handoff_ref
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF", "")
        or os.environ.get("TRASHBOT_HARDWARE_SENSOR_HIL_ENTRY_CALLBACK_REVIEW_HANDOFF_SUMMARY", "")
        or hardware_sensor_hil_entry_callback_review_handoff_source
    )
    hardware_sensor_hil_entry_callback_review_handoff_summary = (
        summarize_hardware_sensor_hil_entry_callback_review_handoff(
            hardware_sensor_hil_entry_callback_review_handoff_source
        )
    )
    pr5_review_thread_closeout_source = (
        pr5_review_thread_closeout_ref
        or os.environ.get("TRASHBOT_PR5_REVIEW_THREAD_CLOSEOUT", "")
        or os.environ.get("TRASHBOT_PR5_REVIEW_THREAD_CLOSEOUT_SUMMARY", "")
        or pr5_review_thread_closeout_source
    )
    pr5_review_thread_closeout_summary = summarize_pr5_review_thread_closeout(
        pr5_review_thread_closeout_source
    )
    pr5_vendor_source_review_packet_source = (
        pr5_vendor_source_review_packet_ref
        or os.environ.get("TRASHBOT_PR5_VENDOR_SOURCE_REVIEW_PACKET", "")
        or os.environ.get("TRASHBOT_PR5_VENDOR_SOURCE_REVIEW_PACKET_SUMMARY", "")
        or pr5_vendor_source_review_packet_source
    )
    pr5_vendor_source_review_packet_summary = summarize_pr5_vendor_source_review_packet(
        pr5_vendor_source_review_packet_source
    )
    pr5_vendor_source_review_reply_dispatch_source = (
        pr5_vendor_source_review_reply_dispatch_ref
        or os.environ.get("TRASHBOT_PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH", "")
        or os.environ.get("TRASHBOT_PR5_VENDOR_SOURCE_REVIEW_REPLY_DISPATCH_SUMMARY", "")
        or pr5_vendor_source_review_reply_dispatch_source
    )
    pr5_vendor_source_review_reply_dispatch_summary = (
        summarize_pr5_vendor_source_review_reply_dispatch(
            pr5_vendor_source_review_reply_dispatch_source
        )
    )
    pr5_mandatory_sensor_source_alignment_source = (
        pr5_mandatory_sensor_source_alignment_ref
        or os.environ.get("TRASHBOT_PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT", "")
        or os.environ.get("TRASHBOT_PR5_MANDATORY_SENSOR_SOURCE_ALIGNMENT_SUMMARY", "")
        or pr5_mandatory_sensor_source_alignment_source
    )
    pr5_mandatory_sensor_source_alignment_summary = (
        summarize_pr5_mandatory_sensor_source_alignment(
            pr5_mandatory_sensor_source_alignment_source
        )
    )
    pr5_mandatory_sensor_material_followup_escalation_status_source = (
        pr5_mandatory_sensor_material_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or pr5_mandatory_sensor_material_followup_escalation_status_source
    )
    pr5_mandatory_sensor_material_followup_escalation_status_summary = (
        summarize_pr5_mandatory_sensor_material_followup_escalation_status(
            pr5_mandatory_sensor_material_followup_escalation_status_source
        )
    )
    # follow-up 输入可能来自 wrapper/raw latest_status；输出前只保留统一 Robot-safe alias。
    for unsafe_latest_key in (
        "pr5_mandatory_sensor_material_followup_escalation_status",
        "pr5_mandatory_sensor_material_followup_escalation_status_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    pr5_mandatory_sensor_material_owner_response_intake_source = (
        pr5_mandatory_sensor_material_owner_response_intake_ref
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY",
            "",
        )
        or pr5_mandatory_sensor_material_owner_response_intake_source
    )
    pr5_mandatory_sensor_material_owner_response_intake_summary = (
        summarize_pr5_mandatory_sensor_material_owner_response_intake(
            pr5_mandatory_sensor_material_owner_response_intake_source
        )
    )
    # owner response raw body 可能含敏感材料；latest_status 只留下 Robot-safe alias。
    for unsafe_latest_key in (
        "pr5_mandatory_sensor_material_owner_response_intake",
        "pr5_mandatory_sensor_material_owner_response_intake_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    pr5_mandatory_sensor_material_owner_response_review_decision_source = (
        pr5_mandatory_sensor_material_owner_response_review_decision_ref
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or pr5_mandatory_sensor_material_owner_response_review_decision_source
    )
    pr5_mandatory_sensor_material_owner_response_review_decision_summary = (
        summarize_pr5_mandatory_sensor_material_owner_response_review_decision(
            pr5_mandatory_sensor_material_owner_response_review_decision_source
        )
    )
    # review-decision 只允许 safe summary 进入 payload，raw owner/material 字段必须在这里剥离。
    for unsafe_latest_key in (
        "pr5_mandatory_sensor_material_owner_response_review_decision",
        "pr5_mandatory_sensor_material_owner_response_review_decision_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    pr5_mandatory_sensor_material_owner_response_review_handoff_source = (
        pr5_mandatory_sensor_material_owner_response_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or pr5_mandatory_sensor_material_owner_response_review_handoff_source
    )
    pr5_mandatory_sensor_material_owner_response_review_handoff_summary = (
        summarize_pr5_mandatory_sensor_material_owner_response_review_handoff(
            pr5_mandatory_sensor_material_owner_response_review_handoff_source
        )
    )
    # review-handoff 是 phone/status 只读面；raw artifact、ACK/cursor/远端评审更新字段不能留在 latest_status。
    for unsafe_latest_key in (
        "pr5_mandatory_sensor_material_owner_response_review_handoff",
        "pr5_mandatory_sensor_material_owner_response_review_handoff_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_source = (
        pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_ref
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_PR5_MANDATORY_SENSOR_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY",
            "",
        )
        or pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_source
    )
    pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary = (
        summarize_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
            pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_source
        )
    )
    # reviewer ACK intake 仅作为 Robot diagnostics safe alias，不能保留 raw ACK 或 GitHub mutation sibling。
    for unsafe_latest_key in (
        "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake",
        "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary",
        "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
        if isinstance(diagnostics_source, dict):
            diagnostics_source.pop(unsafe_latest_key, None)
    hardware_real_material_escalation_request_source = (
        hardware_real_material_escalation_request_ref
        or os.environ.get("TRASHBOT_HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST", "")
        or os.environ.get("TRASHBOT_HARDWARE_REAL_MATERIAL_ESCALATION_REQUEST_SUMMARY", "")
        or hardware_real_material_escalation_request_source
    )
    hardware_real_material_escalation_request_summary = (
        summarize_hardware_real_material_escalation_request(
            hardware_real_material_escalation_request_source
        )
    )
    real_material_readiness_board_source = (
        real_material_readiness_board_ref
        or os.environ.get("TRASHBOT_REAL_MATERIAL_READINESS_BOARD", "")
        or os.environ.get("TRASHBOT_REAL_MATERIAL_READINESS_BOARD_SUMMARY", "")
        or real_material_readiness_board_source
    )
    real_material_readiness_board_summary = summarize_real_material_readiness_board(
        real_material_readiness_board_source
    )
    real_material_evidence_intake_source = (
        real_material_evidence_intake_ref
        or os.environ.get("TRASHBOT_REAL_MATERIAL_EVIDENCE_INTAKE", "")
        or os.environ.get("TRASHBOT_REAL_MATERIAL_EVIDENCE_INTAKE_SUMMARY", "")
        or real_material_evidence_intake_source
    )
    real_material_evidence_intake_summary = summarize_real_material_evidence_intake(
        real_material_evidence_intake_source
    )
    verified_terminal_result_material_intake_source = (
        verified_terminal_result_material_intake_ref
        or os.environ.get("TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE", "")
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_INTAKE_SUMMARY",
            "",
        )
        or verified_terminal_result_material_intake_preserved_source
    )
    verified_terminal_result_material_intake_summary = (
        summarize_verified_terminal_result_material_intake(
            verified_terminal_result_material_intake_source
        )
    )
    # 显式 ref 或 diagnostics source 已生成安全 alias 后，返回体不能继续携带 raw/source key。
    for unsafe_latest_key in (
        "verified_terminal_result_material_intake",
        "verified_terminal_result_material_intake_summary",
        "robot_diagnostics_verified_terminal_result_material_intake_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_review_decision_source = (
        verified_terminal_result_material_review_decision_ref
        or os.environ.get("TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION", "")
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_DECISION_SUMMARY",
            "",
        )
        or verified_terminal_result_material_review_decision_preserved_source
    )
    verified_terminal_result_material_review_decision_summary = (
        summarize_verified_terminal_result_material_review_decision(
            verified_terminal_result_material_review_decision_source
        )
    )
    # review-decision 输入可能包含 artifact wrapper；输出前只保留 canonical safe alias。
    for unsafe_latest_key in (
        "verified_terminal_result_material_review_decision",
        "verified_terminal_result_material_review_decision_summary",
        "robot_diagnostics_verified_terminal_result_material_review_decision_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_review_handoff_source = (
        verified_terminal_result_material_review_handoff_ref
        or os.environ.get("TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF", "")
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or verified_terminal_result_material_review_handoff_preserved_source
    )
    verified_terminal_result_material_review_handoff_summary = (
        summarize_verified_terminal_result_material_review_handoff(
            verified_terminal_result_material_review_handoff_source
        )
    )
    # handoff 输入可带 wrapper/raw sibling；输出前仅保留统一 Robot-safe alias。
    for unsafe_latest_key in (
        "verified_terminal_result_material_review_handoff",
        "verified_terminal_result_material_review_handoff_summary",
        "robot_diagnostics_verified_terminal_result_material_review_handoff_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_followup_escalation_status_source = (
        verified_terminal_result_material_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or verified_terminal_result_material_followup_escalation_status_preserved_source
    )
    verified_terminal_result_material_followup_escalation_status_summary = (
        summarize_verified_terminal_result_material_followup_escalation_status(
            verified_terminal_result_material_followup_escalation_status_source
        )
    )
    # follow-up 输入可能夹带 raw/source sibling；返回前只保留 Robot-safe alias。
    for unsafe_latest_key in (
        "verified_terminal_result_material_followup_escalation_status",
        "verified_terminal_result_material_followup_escalation_status_summary",
        "robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_intake_source = (
        verified_terminal_result_material_owner_response_intake_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_INTAKE_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_intake_preserved_source
    )
    verified_terminal_result_material_owner_response_intake_summary = (
        summarize_verified_terminal_result_material_owner_response_intake(
            verified_terminal_result_material_owner_response_intake_source
        )
    )
    # owner response accepted 也只能进入 later review queue；latest_status 不保留 raw/source sibling。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_intake",
        "verified_terminal_result_material_owner_response_intake_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_review_decision_source = (
        verified_terminal_result_material_owner_response_review_decision_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_review_decision_preserved_source
    )
    verified_terminal_result_material_owner_response_review_decision_summary = (
        summarize_verified_terminal_result_material_owner_response_review_decision(
            verified_terminal_result_material_owner_response_review_decision_source
        )
    )
    # review decision accepted 只表示可进入 next handoff；输出前仍只保留 Robot-safe alias。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_review_decision",
        "verified_terminal_result_material_owner_response_review_decision_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_review_handoff_source = (
        verified_terminal_result_material_owner_response_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_review_handoff_preserved_source
        or verified_terminal_result_material_owner_response_review_decision_summary
    )
    verified_terminal_result_material_owner_response_review_handoff_summary = (
        summarize_verified_terminal_result_material_owner_response_review_handoff(
            verified_terminal_result_material_owner_response_review_handoff_source
        )
    )
    # handoff 由安全 summary 派生，返回前继续移除 source/wrapper sibling。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_review_handoff",
        "verified_terminal_result_material_owner_response_review_handoff_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_reviewer_ack_intake_source = (
        verified_terminal_result_material_owner_response_reviewer_ack_intake_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_INTAKE_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_reviewer_ack_intake_preserved_source
        or verified_terminal_result_material_owner_response_review_handoff_summary
    )
    verified_terminal_result_material_owner_response_reviewer_ack_intake_summary = (
        summarize_verified_terminal_result_material_owner_response_reviewer_ack_intake(
            verified_terminal_result_material_owner_response_reviewer_ack_intake_source
        )
    )
    # reviewer ACK intake 也只暴露 canonical safe alias，避免 raw ACK 或 resolved 语义旁路。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_reviewer_ack_intake",
        "verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_reviewer_ack_review_decision_source = (
        verified_terminal_result_material_owner_response_reviewer_ack_review_decision_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_reviewer_ack_review_decision_preserved_source
        or verified_terminal_result_material_owner_response_reviewer_ack_intake_summary
    )
    verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary = (
        summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_decision(
            verified_terminal_result_material_owner_response_reviewer_ack_review_decision_source
        )
    )
    # reviewer ACK review decision 仍是只读 metadata，不保留 raw decision 或可变 review sibling。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_source = (
        verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_preserved_source
        or verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary
    )
    verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary = (
        summarize_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff(
            verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_source
        )
    )
    # review handoff 只发布 safe alias，避免 raw handoff、ACK/cursor 或控制语义留在 latest_status。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff",
        "verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_source = (
        verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_VERIFIED_TERMINAL_RESULT_MATERIAL_OWNER_RESPONSE_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_preserved_source
        or verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary
    )
    verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary = (
        summarize_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
            verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_source
        )
    )
    # follow-up escalation 只保留 Robot-safe alias；raw ACK/cursor/fetch/command hints 必须被清掉。
    for unsafe_latest_key in (
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status",
        "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
        "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    real_material_followup_escalation_status_source = (
        real_material_followup_escalation_status_ref
        or os.environ.get("TRASHBOT_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS", "")
        or os.environ.get("TRASHBOT_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY", "")
        or real_material_followup_escalation_status_source
    )
    real_material_followup_escalation_status_summary = (
        summarize_real_material_followup_escalation_status(
            real_material_followup_escalation_status_source
        )
    )
    field_evidence_real_material_followup_escalation_status_source = (
        field_evidence_real_material_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or field_evidence_real_material_followup_escalation_status_source
    )
    field_evidence_real_material_followup_escalation_status_summary = (
        summarize_field_evidence_real_material_followup_escalation_status(
            field_evidence_real_material_followup_escalation_status_source
        )
    )
    field_evidence_real_material_owner_ack_intake_source = (
        field_evidence_real_material_owner_ack_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_real_material_owner_ack_intake_preserved_source
    )
    field_evidence_real_material_owner_ack_intake_summary = (
        summarize_field_evidence_real_material_owner_ack_intake(
            field_evidence_real_material_owner_ack_intake_source
        )
    )
    field_evidence_real_material_owner_ack_review_decision_source = (
        field_evidence_real_material_owner_ack_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_REAL_MATERIAL_OWNER_ACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_real_material_owner_ack_review_decision_preserved_source
    )
    field_evidence_real_material_owner_ack_review_decision_summary = (
        summarize_field_evidence_real_material_owner_ack_review_decision(
            field_evidence_real_material_owner_ack_review_decision_source
        )
    )
    field_evidence_material_blocker_escalation_pack_source = (
        field_evidence_material_blocker_escalation_pack_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_BLOCKER_ESCALATION_PACK_SUMMARY",
            "",
        )
        or field_evidence_material_blocker_escalation_pack_preserved_source
    )
    field_evidence_material_blocker_escalation_pack_summary = (
        summarize_field_evidence_material_blocker_escalation_pack(
            field_evidence_material_blocker_escalation_pack_source
        )
    )
    field_evidence_material_resolution_intake_source = (
        field_evidence_material_resolution_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_intake_preserved_source
    )
    field_evidence_material_resolution_intake_summary = (
        summarize_field_evidence_material_resolution_intake(
            field_evidence_material_resolution_intake_source
        )
    )
    field_evidence_material_resolution_review_decision_source = (
        field_evidence_material_resolution_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_review_decision_preserved_source
    )
    field_evidence_material_resolution_review_decision_summary = (
        summarize_field_evidence_material_resolution_review_decision(
            field_evidence_material_resolution_review_decision_source
        )
    )
    field_evidence_material_resolution_review_handoff_source = (
        field_evidence_material_resolution_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_review_handoff_preserved_source
    )
    field_evidence_material_resolution_review_handoff_summary = (
        summarize_field_evidence_material_resolution_review_handoff(
            field_evidence_material_resolution_review_handoff_source
        )
    )
    field_evidence_material_resolution_followup_escalation_status_source = (
        field_evidence_material_resolution_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_followup_escalation_status_preserved_source
    )
    field_evidence_material_resolution_followup_escalation_status_summary = (
        summarize_field_evidence_material_resolution_followup_escalation_status(
            field_evidence_material_resolution_followup_escalation_status_source
        )
    )
    field_evidence_material_resolution_owner_response_intake_source = (
        field_evidence_material_resolution_owner_response_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_owner_response_intake_preserved_source
    )
    field_evidence_material_resolution_owner_response_intake_summary = (
        summarize_field_evidence_material_resolution_owner_response_intake(
            field_evidence_material_resolution_owner_response_intake_source
        )
    )
    field_evidence_material_resolution_owner_response_review_decision_source = (
        field_evidence_material_resolution_owner_response_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_owner_response_review_decision_preserved_source
    )
    field_evidence_material_resolution_owner_response_review_decision_summary = (
        summarize_field_evidence_material_resolution_owner_response_review_decision(
            field_evidence_material_resolution_owner_response_review_decision_source
        )
    )
    field_evidence_material_resolution_owner_response_review_handoff_source = (
        field_evidence_material_resolution_owner_response_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_OWNER_RESPONSE_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_owner_response_review_handoff_preserved_source
    )
    field_evidence_material_resolution_owner_response_review_handoff_summary = (
        summarize_field_evidence_material_resolution_owner_response_review_handoff(
            field_evidence_material_resolution_owner_response_review_handoff_source
        )
    )
    field_evidence_material_resolution_reviewer_ack_intake_source = (
        field_evidence_material_resolution_reviewer_ack_intake_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_INTAKE_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_reviewer_ack_intake_preserved_source
    )
    field_evidence_material_resolution_reviewer_ack_intake_summary = (
        summarize_field_evidence_material_resolution_reviewer_ack_intake(
            field_evidence_material_resolution_reviewer_ack_intake_source
        )
    )
    field_evidence_material_resolution_reviewer_ack_review_decision_source = (
        field_evidence_material_resolution_reviewer_ack_review_decision_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_DECISION_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_reviewer_ack_review_decision_preserved_source
    )
    field_evidence_material_resolution_reviewer_ack_review_decision_summary = (
        summarize_field_evidence_material_resolution_reviewer_ack_review_decision(
            field_evidence_material_resolution_reviewer_ack_review_decision_source
        )
    )
    field_evidence_material_resolution_reviewer_ack_review_handoff_source = (
        field_evidence_material_resolution_reviewer_ack_review_handoff_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_REVIEW_HANDOFF_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_reviewer_ack_review_handoff_preserved_source
    )
    field_evidence_material_resolution_reviewer_ack_review_handoff_summary = (
        summarize_field_evidence_material_resolution_reviewer_ack_review_handoff(
            field_evidence_material_resolution_reviewer_ack_review_handoff_source
        )
    )
    field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source = (
        field_evidence_material_resolution_reviewer_ack_followup_escalation_status_ref
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS",
            "",
        )
        or os.environ.get(
            "TRASHBOT_FIELD_EVIDENCE_MATERIAL_RESOLUTION_REVIEWER_ACK_FOLLOWUP_ESCALATION_STATUS_SUMMARY",
            "",
        )
        or field_evidence_material_resolution_reviewer_ack_followup_escalation_status_preserved_source
    )
    field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary = (
        summarize_field_evidence_material_resolution_reviewer_ack_followup_escalation_status(
            field_evidence_material_resolution_reviewer_ack_followup_escalation_status_source
        )
    )
    # reviewer ACK 系列可能来自 raw latest_status；输出前只保留统一 Robot-safe alias。
    for unsafe_latest_key in (
        "field_evidence_material_resolution_reviewer_ack_intake",
        "field_evidence_material_resolution_reviewer_ack_intake_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary",
        "field_evidence_material_resolution_reviewer_ack_review_decision",
        "field_evidence_material_resolution_reviewer_ack_review_decision_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary",
        "field_evidence_material_resolution_reviewer_ack_review_handoff",
        "field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary",
        "field_evidence_material_resolution_reviewer_ack_followup_escalation_status",
        "field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
        "robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary",
        "cloud_external_evidence_review_decision",
        "cloud_external_evidence_review_decision_summary",
        "robot_diagnostics_cloud_external_evidence_review_decision_summary",
        "cloud_external_evidence_review_handoff",
        "cloud_external_evidence_review_handoff_summary",
        "robot_diagnostics_cloud_external_evidence_review_handoff_summary",
        "cloud_external_evidence_review_handoff_followup_escalation_status",
        "cloud_external_evidence_review_handoff_followup_escalation_status_summary",
        "robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary",
    ):
        latest_status.pop(unsafe_latest_key, None)
    return status_payload(
        "diagnostics_ready",
        "diagnostics package ready",
        software_version=str(software_version or ""),
        map_version=str(map_version or ""),
        route_version=str(route_version or ""),
        latest_status=latest_status,
        last_task=last_task,
        source=source,
        result_path=result_path,
        evidence_ref=evidence_ref,
        failure_code=failure_code,
        human_intervention_required=human_intervention_required,
        state_transition_history=state_transition_history,
        route_progress=route_progress,
        failure=failure,
        log_refs=normalize_log_refs(log_refs),
        vision_sample_manifest_ref=str(vision_sample_manifest_ref or ""),
        review_decision_log_ref=str(review_decision_log_ref or ""),
        review_decision_log=review_decision_log,
        vision_samples=summarize_vision_manifest(
            vision_sample_manifest_ref,
            decision_index=decision_index,
        ),
        route_proof_summary=route_proof_summary,
        route_proof_status=route_proof_status,
        cloud_unreachable_malformed_response_guard=cloud_guard_summary,
        cloud_unreachable_malformed_response_guard_summary=cloud_guard_summary,
        robot_diagnostics_cloud_unreachable_malformed_response_guard_summary=cloud_guard_summary,
        cloud_poll_backoff_rate_limit_guard=poll_backoff_summary,
        cloud_poll_backoff_rate_limit_guard_summary=poll_backoff_summary,
        robot_diagnostics_cloud_poll_backoff_rate_limit_guard_summary=poll_backoff_summary,
        cloud_ack_lookup_pending_status_guard=ack_lookup_pending_summary,
        cloud_ack_lookup_pending_status_guard_summary=ack_lookup_pending_summary,
        robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary=(
            ack_lookup_pending_summary
        ),
        cloud_ack_accepted_result_pending_guard=ack_accepted_result_pending_summary,
        cloud_ack_accepted_result_pending_guard_summary=ack_accepted_result_pending_summary,
        robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary=(
            ack_accepted_result_pending_summary
        ),
        cloud_terminal_result_verification_guard=terminal_result_verification_summary,
        cloud_terminal_result_verification_guard_summary=terminal_result_verification_summary,
        robot_diagnostics_cloud_terminal_result_verification_guard_summary=(
            terminal_result_verification_summary
        ),
        cloud_cancel_pending_command_safety_guard=cancel_pending_summary,
        cloud_cancel_pending_command_safety_guard_summary=cancel_pending_summary,
        robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary=cancel_pending_summary,
        cloud_support_handoff_safe_export=cloud_support_handoff_safe_export_summary,
        cloud_support_handoff_safe_export_summary=cloud_support_handoff_safe_export_summary,
        robot_diagnostics_cloud_support_handoff_safe_export_summary=(
            cloud_support_handoff_safe_export_summary
        ),
        cloud_command_lifecycle_audit_export=cloud_command_lifecycle_audit_export_summary,
        cloud_command_lifecycle_audit_export_summary=(
            cloud_command_lifecycle_audit_export_summary
        ),
        robot_diagnostics_cloud_command_lifecycle_audit_export_summary=(
            cloud_command_lifecycle_audit_export_summary
        ),
        cloud_command_lifecycle_replay_drill=cloud_command_lifecycle_replay_drill_summary,
        cloud_command_lifecycle_replay_drill_summary=(
            cloud_command_lifecycle_replay_drill_summary
        ),
        robot_diagnostics_cloud_command_lifecycle_replay_drill_summary=(
            cloud_command_lifecycle_replay_drill_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet=(
            cloud_command_lifecycle_replay_acceptance_packet_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_summary
        ),
        robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_summary
        ),
        robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_followup_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_summary
        ),
        cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_summary
        ),
        robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary=(
            cloud_command_lifecycle_replay_acceptance_packet_reviewer_ack_owner_response_intake_bridge_summary
        ),
        cloud_external_evidence_review_decision=(
            cloud_external_evidence_review_decision_summary
        ),
        cloud_external_evidence_review_decision_summary=(
            cloud_external_evidence_review_decision_summary
        ),
        robot_diagnostics_cloud_external_evidence_review_decision_summary=(
            cloud_external_evidence_review_decision_summary
        ),
        cloud_external_evidence_review_handoff=(
            cloud_external_evidence_review_handoff_summary
        ),
        cloud_external_evidence_review_handoff_summary=(
            cloud_external_evidence_review_handoff_summary
        ),
        robot_diagnostics_cloud_external_evidence_review_handoff_summary=(
            cloud_external_evidence_review_handoff_summary
        ),
        cloud_external_evidence_review_handoff_followup_escalation_status=(
            cloud_external_evidence_review_handoff_followup_summary
        ),
        cloud_external_evidence_review_handoff_followup_escalation_status_summary=(
            cloud_external_evidence_review_handoff_followup_summary
        ),
        robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary=(
            cloud_external_evidence_review_handoff_followup_summary
        ),
        route_task_rehearsal=summarize_route_task_rehearsal_artifact(
            route_task_rehearsal_artifact_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_ARTIFACT", "")
        ),
        route_task_rehearsal_execution_bundle=summarize_route_task_rehearsal_execution_bundle(
            route_task_rehearsal_bundle_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE", "")
        ),
        route_task_rehearsal_operator_review=summarize_route_task_rehearsal_operator_review(
            route_task_rehearsal_operator_review_ref
            or os.environ.get("TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW", "")
        ),
        pc_route_debug_console=summarize_pc_route_debug_console(
            pc_route_debug_console_ref
            or os.environ.get("TRASHBOT_PC_ROUTE_DEBUG_CONSOLE", "")
        ),
        route_task_field_run_readiness=route_task_field_run_readiness_summary,
        route_task_field_run_readiness_summary=route_task_field_run_readiness_summary,
        route_task_field_run_intake=route_task_field_run_intake_summary,
        route_task_field_run_intake_summary=route_task_field_run_intake_summary,
        route_task_field_run_review=route_task_field_run_review_summary,
        route_task_field_run_review_summary=route_task_field_run_review_summary,
        route_task_field_run_execution_pack=route_task_field_run_execution_pack_summary,
        route_task_field_run_execution_pack_summary=route_task_field_run_execution_pack_summary,
        route_task_field_retest_execution_pack=route_task_field_retest_execution_pack_summary,
        route_task_field_retest_execution_pack_summary=route_task_field_retest_execution_pack_summary,
        route_task_field_retest_session_handoff=route_task_field_retest_session_handoff_summary,
        route_task_field_retest_session_handoff_summary=route_task_field_retest_session_handoff_summary,
        route_task_field_retest_result_intake=route_task_field_retest_result_intake_summary,
        route_task_field_retest_result_intake_summary=route_task_field_retest_result_intake_summary,
        route_task_field_retest_result_reconciliation=route_task_field_retest_result_reconciliation_summary,
        route_task_field_retest_result_reconciliation_summary=route_task_field_retest_result_reconciliation_summary,
        route_task_field_retest_material_pack=route_task_field_retest_material_pack_summary,
        route_task_field_retest_material_pack_summary=route_task_field_retest_material_pack_summary,
        robot_diagnostics_route_task_field_retest_material_pack_summary=route_task_field_retest_material_pack_summary,
        route_task_field_retest_material_callback_packet=(
            route_task_field_retest_material_callback_packet_summary
        ),
        route_task_field_retest_material_callback_packet_summary=(
            route_task_field_retest_material_callback_packet_summary
        ),
        robot_diagnostics_route_task_field_retest_material_callback_packet_summary=(
            route_task_field_retest_material_callback_packet_summary
        ),
        route_task_field_retest_material_callback_review_decision=(
            route_task_field_retest_material_callback_review_decision_summary
        ),
        route_task_field_retest_material_callback_review_decision_summary=(
            route_task_field_retest_material_callback_review_decision_summary
        ),
        robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary=(
            route_task_field_retest_material_callback_review_decision_summary
        ),
        route_task_field_retest_operator_drill=route_task_field_retest_operator_drill_summary,
        route_task_field_retest_operator_drill_summary=route_task_field_retest_operator_drill_summary,
        robot_diagnostics_route_task_field_retest_operator_drill_summary=(
            route_task_field_retest_operator_drill_summary
        ),
        route_task_field_retest_drill_console=route_task_field_retest_drill_console_summary,
        route_task_field_retest_drill_console_summary=route_task_field_retest_drill_console_summary,
        robot_diagnostics_route_task_field_retest_drill_console_summary=(
            route_task_field_retest_drill_console_summary
        ),
        route_task_field_retest_acceptance_brief=route_task_field_retest_acceptance_brief_summary,
        route_task_field_retest_acceptance_brief_summary=route_task_field_retest_acceptance_brief_summary,
        robot_diagnostics_route_task_field_retest_acceptance_brief_summary=(
            route_task_field_retest_acceptance_brief_summary
        ),
        route_task_field_retest_acceptance_review_decision=(
            route_task_field_retest_acceptance_review_decision_summary
        ),
        route_task_field_retest_acceptance_review_decision_summary=(
            route_task_field_retest_acceptance_review_decision_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary=(
            route_task_field_retest_acceptance_review_decision_summary
        ),
        route_task_field_retest_acceptance_execution_pack=(
            route_task_field_retest_acceptance_execution_pack_summary
        ),
        route_task_field_retest_acceptance_execution_pack_summary=(
            route_task_field_retest_acceptance_execution_pack_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary=(
            route_task_field_retest_acceptance_execution_pack_summary
        ),
        route_task_field_retest_acceptance_execution_callback_intake=(
            route_task_field_retest_acceptance_execution_callback_intake_summary
        ),
        route_task_field_retest_acceptance_execution_callback_intake_summary=(
            route_task_field_retest_acceptance_execution_callback_intake_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary=(
            route_task_field_retest_acceptance_execution_callback_intake_summary
        ),
        route_task_field_retest_acceptance_execution_callback_review_decision=(
            route_task_field_retest_acceptance_execution_callback_review_decision_summary
        ),
        route_task_field_retest_acceptance_execution_callback_review_decision_summary=(
            route_task_field_retest_acceptance_execution_callback_review_decision_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary=(
            route_task_field_retest_acceptance_execution_callback_review_decision_summary
        ),
        route_task_field_retest_acceptance_execution_callback_review_handoff=(
            route_task_field_retest_acceptance_execution_callback_review_handoff_summary
        ),
        route_task_field_retest_acceptance_execution_callback_review_handoff_summary=(
            route_task_field_retest_acceptance_execution_callback_review_handoff_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary=(
            route_task_field_retest_acceptance_execution_callback_review_handoff_summary
        ),
        route_task_field_retest_acceptance_execution_handoff_intake=(
            route_task_field_retest_acceptance_execution_handoff_intake_summary
        ),
        route_task_field_retest_acceptance_execution_handoff_intake_summary=(
            route_task_field_retest_acceptance_execution_handoff_intake_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary=(
            route_task_field_retest_acceptance_execution_handoff_intake_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_queue=(
            route_task_field_retest_acceptance_execution_rerun_queue_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_queue_summary=(
            route_task_field_retest_acceptance_execution_rerun_queue_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary=(
            route_task_field_retest_acceptance_execution_rerun_queue_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_intake=(
            route_task_field_retest_acceptance_execution_rerun_result_intake_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_intake_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_intake_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_intake_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_review_decision=(
            route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_review_handoff=(
            route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary
        ),
        route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary
        ),
        robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary=(
            route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary
        ),
        field_evidence_rerun_material_dispatch=field_evidence_rerun_material_dispatch_summary,
        field_evidence_rerun_material_dispatch_summary=field_evidence_rerun_material_dispatch_summary,
        robot_diagnostics_field_evidence_rerun_material_dispatch_summary=(
            field_evidence_rerun_material_dispatch_summary
        ),
        field_evidence_rerun_callback_intake=field_evidence_rerun_callback_intake_summary,
        field_evidence_rerun_callback_intake_summary=field_evidence_rerun_callback_intake_summary,
        robot_diagnostics_field_evidence_rerun_callback_intake_summary=(
            field_evidence_rerun_callback_intake_summary
        ),
        field_evidence_rerun_callback_review_decision=(
            field_evidence_rerun_callback_review_decision_summary
        ),
        field_evidence_rerun_callback_review_decision_summary=(
            field_evidence_rerun_callback_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_callback_review_decision_summary=(
            field_evidence_rerun_callback_review_decision_summary
        ),
        field_evidence_rerun_callback_review_handoff=(
            field_evidence_rerun_callback_review_handoff_summary
        ),
        field_evidence_rerun_callback_review_handoff_summary=(
            field_evidence_rerun_callback_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary=(
            field_evidence_rerun_callback_review_handoff_summary
        ),
        field_evidence_rerun_handoff_intake=(
            field_evidence_rerun_handoff_intake_summary
        ),
        field_evidence_rerun_handoff_intake_summary=(
            field_evidence_rerun_handoff_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_handoff_intake_summary=(
            field_evidence_rerun_handoff_intake_summary
        ),
        field_evidence_rerun_queue=field_evidence_rerun_queue_summary,
        field_evidence_rerun_queue_summary=field_evidence_rerun_queue_summary,
        robot_diagnostics_field_evidence_rerun_queue_summary=(
            field_evidence_rerun_queue_summary
        ),
        field_evidence_rerun_execution_pack=(
            field_evidence_rerun_execution_pack_summary
        ),
        field_evidence_rerun_execution_pack_summary=(
            field_evidence_rerun_execution_pack_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_pack_summary=(
            field_evidence_rerun_execution_pack_summary
        ),
        field_evidence_rerun_execution_callback_intake=(
            field_evidence_rerun_execution_callback_intake_summary
        ),
        field_evidence_rerun_execution_callback_intake_summary=(
            field_evidence_rerun_execution_callback_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary=(
            field_evidence_rerun_execution_callback_intake_summary
        ),
        field_evidence_rerun_execution_callback_review_decision=(
            field_evidence_rerun_execution_callback_review_decision_summary
        ),
        field_evidence_rerun_execution_callback_review_decision_summary=(
            field_evidence_rerun_execution_callback_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary=(
            field_evidence_rerun_execution_callback_review_decision_summary
        ),
        field_evidence_rerun_execution_callback_review_handoff=(
            field_evidence_rerun_execution_callback_review_handoff_summary
        ),
        field_evidence_rerun_execution_callback_review_handoff_summary=(
            field_evidence_rerun_execution_callback_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary=(
            field_evidence_rerun_execution_callback_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_intake=(
            field_evidence_rerun_execution_result_intake_summary
        ),
        field_evidence_rerun_execution_result_intake_summary=(
            field_evidence_rerun_execution_result_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_intake_summary=(
            field_evidence_rerun_execution_result_intake_summary
        ),
        field_evidence_rerun_execution_result_review_decision=(
            field_evidence_rerun_execution_result_review_decision_summary
        ),
        field_evidence_rerun_execution_result_review_decision_summary=(
            field_evidence_rerun_execution_result_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary=(
            field_evidence_rerun_execution_result_review_decision_summary
        ),
        field_evidence_rerun_execution_result_review_handoff=(
            field_evidence_rerun_execution_result_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_review_handoff_summary=(
            field_evidence_rerun_execution_result_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary=(
            field_evidence_rerun_execution_result_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_packet=(
            field_evidence_rerun_execution_result_acceptance_packet_summary
        ),
        field_evidence_rerun_execution_result_acceptance_packet_summary=(
            field_evidence_rerun_execution_result_acceptance_packet_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary=(
            field_evidence_rerun_execution_result_acceptance_packet_summary
        ),
        field_evidence_rerun_execution_result_acceptance_backfill=(
            field_evidence_rerun_execution_result_acceptance_backfill_summary
        ),
        field_evidence_rerun_execution_result_acceptance_backfill_summary=(
            field_evidence_rerun_execution_result_acceptance_backfill_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary=(
            field_evidence_rerun_execution_result_acceptance_backfill_summary
        ),
        field_evidence_rerun_execution_result_acceptance_backfill_review_decision=(
            field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_review_handoff=(
            field_evidence_rerun_execution_result_acceptance_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary=(
            field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        field_evidence_real_material_request_dispatch=(
            field_evidence_real_material_request_dispatch_summary
        ),
        field_evidence_real_material_request_dispatch_summary=(
            field_evidence_real_material_request_dispatch_summary
        ),
        robot_diagnostics_field_evidence_real_material_request_dispatch_summary=(
            field_evidence_real_material_request_dispatch_summary
        ),
        field_evidence_real_material_response_intake=(
            field_evidence_real_material_response_intake_summary
        ),
        field_evidence_real_material_response_intake_summary=(
            field_evidence_real_material_response_intake_summary
        ),
        robot_diagnostics_field_evidence_real_material_response_intake_summary=(
            field_evidence_real_material_response_intake_summary
        ),
        field_evidence_real_material_response_review_decision=(
            field_evidence_real_material_response_review_decision_summary
        ),
        field_evidence_real_material_response_review_decision_summary=(
            field_evidence_real_material_response_review_decision_summary
        ),
        robot_diagnostics_field_evidence_real_material_response_review_decision_summary=(
            field_evidence_real_material_response_review_decision_summary
        ),
        field_evidence_real_material_response_review_handoff=(
            field_evidence_real_material_response_review_handoff_summary
        ),
        field_evidence_real_material_response_review_handoff_summary=(
            field_evidence_real_material_response_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_real_material_response_review_handoff_summary=(
            field_evidence_real_material_response_review_handoff_summary
        ),
        route_task_field_retest_evidence_dispatch=route_task_field_retest_evidence_dispatch_summary,
        route_task_field_retest_evidence_dispatch_summary=route_task_field_retest_evidence_dispatch_summary,
        route_task_field_retest_callback_intake=route_task_field_retest_callback_intake_summary,
        route_task_field_retest_callback_intake_summary=route_task_field_retest_callback_intake_summary,
        route_task_field_retest_callback_review_decision=route_task_field_retest_callback_review_decision_summary,
        route_task_field_retest_callback_review_decision_summary=route_task_field_retest_callback_review_decision_summary,
        route_task_field_retest_review_result_handoff=route_task_field_retest_review_result_handoff_summary,
        route_task_field_retest_review_result_handoff_summary=route_task_field_retest_review_result_handoff_summary,
        route_task_field_retest_result_acceptance_packet=route_task_field_retest_result_acceptance_packet_summary,
        route_task_field_retest_result_acceptance_packet_summary=route_task_field_retest_result_acceptance_packet_summary,
        route_task_field_retest_result_acceptance_backfill=route_task_field_retest_result_acceptance_backfill_summary,
        route_task_field_retest_result_acceptance_backfill_summary=route_task_field_retest_result_acceptance_backfill_summary,
        route_task_field_retest_result_backfill_review_decision=route_task_field_retest_result_backfill_review_decision_summary,
        route_task_field_retest_result_backfill_review_decision_summary=route_task_field_retest_result_backfill_review_decision_summary,
        route_task_field_retest_result_review_dispatch=route_task_field_retest_result_review_dispatch_summary,
        route_task_field_retest_result_review_dispatch_summary=route_task_field_retest_result_review_dispatch_summary,
        route_task_field_retest_result_review_intake=route_task_field_retest_result_review_intake_summary,
        route_task_field_retest_result_review_intake_summary=route_task_field_retest_result_review_intake_summary,
        robot_diagnostics_route_task_field_retest_result_review_intake_summary=route_task_field_retest_result_review_intake_summary,
        route_task_field_retest_result_review_decision=route_task_field_retest_result_review_decision_summary,
        route_task_field_retest_result_review_decision_summary=route_task_field_retest_result_review_decision_summary,
        robot_diagnostics_route_task_field_retest_result_review_decision_summary=route_task_field_retest_result_review_decision_summary,
        route_task_field_retest_result_review_handoff=route_task_field_retest_result_review_handoff_summary,
        route_task_field_retest_result_review_handoff_summary=route_task_field_retest_result_review_handoff_summary,
        robot_diagnostics_route_task_field_retest_result_review_handoff_summary=route_task_field_retest_result_review_handoff_summary,
        route_task_field_retest_result_callback_intake=route_task_field_retest_result_callback_intake_summary,
        route_task_field_retest_result_callback_intake_summary=route_task_field_retest_result_callback_intake_summary,
        robot_diagnostics_route_task_field_retest_result_callback_intake_summary=route_task_field_retest_result_callback_intake_summary,
        route_task_field_retest_result_callback_review_decision=route_task_field_retest_result_callback_review_decision_summary,
        route_task_field_retest_result_callback_review_decision_summary=route_task_field_retest_result_callback_review_decision_summary,
        robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary=route_task_field_retest_result_callback_review_decision_summary,
        route_task_field_retest_result_callback_review_handoff=route_task_field_retest_result_callback_review_handoff_summary,
        route_task_field_retest_result_callback_review_handoff_summary=route_task_field_retest_result_callback_review_handoff_summary,
        robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary=route_task_field_retest_result_callback_review_handoff_summary,
        route_task_field_run_reconciliation=route_task_field_run_reconciliation_summary,
        route_task_field_run_reconciliation_summary=route_task_field_run_reconciliation_summary,
        route_task_completion_signal=route_task_completion_signal_summary,
        route_task_completion_signal_summary=route_task_completion_signal_summary,
        route_task_terminal_completion_rehearsal=route_task_terminal_completion_rehearsal_summary,
        route_task_terminal_completion_rehearsal_summary=route_task_terminal_completion_rehearsal_summary,
        task_terminal_completion_mainline=task_terminal_completion_mainline_summary,
        task_terminal_completion_mainline_summary=task_terminal_completion_mainline_summary,
        robot_diagnostics_task_terminal_completion_mainline_summary=(
            task_terminal_completion_mainline_summary
        ),
        task_terminal_field_material_intake=task_terminal_field_material_intake_summary,
        task_terminal_field_material_intake_summary=(
            task_terminal_field_material_intake_summary
        ),
        robot_diagnostics_task_terminal_field_material_intake_summary=(
            task_terminal_field_material_intake_summary
        ),
        task_terminal_field_material_review_decision=(
            task_terminal_field_material_review_decision_summary
        ),
        task_terminal_field_material_review_decision_summary=(
            task_terminal_field_material_review_decision_summary
        ),
        robot_diagnostics_task_terminal_field_material_review_decision_summary=(
            task_terminal_field_material_review_decision_summary
        ),
        route_task_terminal_review_decision=route_task_terminal_review_decision_summary,
        route_task_terminal_review_decision_summary=route_task_terminal_review_decision_summary,
        route_task_field_run_console=route_task_field_run_console_summary,
        route_task_field_run_console_summary=route_task_field_run_console_summary,
        route_task_field_run_evidence_kit=route_task_field_run_evidence_kit_summary,
        route_task_field_run_evidence_kit_summary=route_task_field_run_evidence_kit_summary,
        route_task_field_run_material_bundle=route_task_field_run_material_bundle_summary,
        route_task_field_run_material_bundle_summary=route_task_field_run_material_bundle_summary,
        route_task_field_run_material_validation=route_task_field_run_material_validation_summary,
        route_task_field_run_material_validation_summary=route_task_field_run_material_validation_summary,
        elevator_field_run_material_validation=elevator_field_run_material_validation_summary,
        elevator_field_run_material_validation_summary=elevator_field_run_material_validation_summary,
        elevator_field_run_review=elevator_field_run_review_summary,
        elevator_field_run_review_summary=elevator_field_run_review_summary,
        elevator_field_run_execution_pack=elevator_field_run_execution_pack_summary,
        elevator_field_run_execution_pack_summary=elevator_field_run_execution_pack_summary,
        elevator_route_evidence_reconciliation=elevator_route_evidence_reconciliation_summary,
        elevator_route_evidence_reconciliation_summary=elevator_route_evidence_reconciliation_summary,
        route_elevator_field_session_handoff=route_elevator_field_session_handoff_summary,
        route_elevator_field_session_handoff_summary=route_elevator_field_session_handoff_summary,
        mobile_route_elevator_field_device_precheck=mobile_route_elevator_field_device_precheck_summary,
        mobile_route_elevator_field_device_precheck_summary=mobile_route_elevator_field_device_precheck_summary,
        mobile_field_material_intake=mobile_field_material_intake_summary,
        mobile_field_material_intake_summary=mobile_field_material_intake_summary,
        mobile_field_material_review_decision=mobile_field_material_review_decision_summary,
        mobile_field_material_review_decision_summary=mobile_field_material_review_decision_summary,
        mobile_field_material_retest_request=mobile_field_material_retest_request_summary,
        mobile_field_material_retest_request_summary=mobile_field_material_retest_request_summary,
        mobile_real_device_field_trial_acceptance_review_handoff=(
            mobile_real_device_field_trial_acceptance_review_handoff_summary
        ),
        mobile_real_device_field_trial_acceptance_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_review_handoff_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_review_handoff_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_pack=(
            mobile_real_device_field_trial_acceptance_execution_pack_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_pack_summary=(
            mobile_real_device_field_trial_acceptance_execution_pack_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary=(
            mobile_real_device_field_trial_acceptance_execution_pack_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_intake=(
            mobile_real_device_field_trial_acceptance_execution_callback_intake_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_intake_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_intake_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_intake_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_review_decision=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_review_handoff=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_intake=(
            mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_intake_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_review_decision=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_decision_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary
        ),
        mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary
        ),
        robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary=(
            mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary
        ),
        wave_rover_feedback_replay=wave_rover_feedback_replay_summary,
        wave_rover_feedback_replay_summary=wave_rover_feedback_replay_summary,
        wave_rover_hil_packet_intake=wave_rover_hil_packet_intake_summary,
        wave_rover_hil_packet_intake_summary=wave_rover_hil_packet_intake_summary,
        robot_diagnostics_wave_rover_hil_packet_intake_summary=wave_rover_hil_packet_intake_summary,
        wave_rover_hil_packet_review_decision=wave_rover_hil_packet_review_decision_summary,
        wave_rover_hil_packet_review_decision_summary=wave_rover_hil_packet_review_decision_summary,
        robot_diagnostics_wave_rover_hil_packet_review_decision_summary=(
            wave_rover_hil_packet_review_decision_summary
        ),
        wave_rover_hil_packet_execution_pack=wave_rover_hil_packet_execution_pack_summary,
        wave_rover_hil_packet_execution_pack_summary=wave_rover_hil_packet_execution_pack_summary,
        robot_diagnostics_wave_rover_hil_packet_execution_pack_summary=(
            wave_rover_hil_packet_execution_pack_summary
        ),
        wave_rover_hil_packet_collection_drill=wave_rover_hil_packet_collection_drill_summary,
        wave_rover_hil_packet_collection_drill_summary=(
            wave_rover_hil_packet_collection_drill_summary
        ),
        robot_diagnostics_wave_rover_hil_packet_collection_drill_summary=(
            wave_rover_hil_packet_collection_drill_summary
        ),
        hardware_baseline_review=hardware_baseline_review_summary,
        hardware_baseline_review_summary=hardware_baseline_review_summary,
        hardware_baseline_source_alignment=hardware_baseline_source_alignment_summary,
        hardware_baseline_source_alignment_summary=hardware_baseline_source_alignment_summary,
        hardware_sensor_procurement_intake=hardware_sensor_procurement_intake_summary,
        hardware_sensor_procurement_intake_summary=hardware_sensor_procurement_intake_summary,
        hardware_sensor_procurement_review_decision=hardware_sensor_procurement_review_decision_summary,
        hardware_sensor_procurement_review_decision_summary=hardware_sensor_procurement_review_decision_summary,
        hardware_sensor_procurement_execution_pack=hardware_sensor_procurement_execution_pack_summary,
        hardware_sensor_procurement_execution_pack_summary=hardware_sensor_procurement_execution_pack_summary,
        hardware_sensor_procurement_receipt_intake=hardware_sensor_procurement_receipt_intake_summary,
        hardware_sensor_procurement_receipt_intake_summary=hardware_sensor_procurement_receipt_intake_summary,
        hardware_sensor_hil_entry_config_precheck=hardware_sensor_hil_entry_config_precheck_summary,
        hardware_sensor_hil_entry_config_precheck_summary=hardware_sensor_hil_entry_config_precheck_summary,
        hardware_sensor_hil_entry_readiness_review=hardware_sensor_hil_entry_readiness_review_summary,
        hardware_sensor_hil_entry_readiness_review_summary=hardware_sensor_hil_entry_readiness_review_summary,
        hardware_sensor_hil_entry_execution_pack=hardware_sensor_hil_entry_execution_pack_summary,
        hardware_sensor_hil_entry_execution_pack_summary=hardware_sensor_hil_entry_execution_pack_summary,
        hardware_sensor_hil_entry_callback_intake=hardware_sensor_hil_entry_callback_intake_summary,
        hardware_sensor_hil_entry_callback_intake_summary=hardware_sensor_hil_entry_callback_intake_summary,
        hardware_sensor_hil_entry_callback_review_decision=(
            hardware_sensor_hil_entry_callback_review_decision_summary
        ),
        hardware_sensor_hil_entry_callback_review_decision_summary=(
            hardware_sensor_hil_entry_callback_review_decision_summary
        ),
        robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary=(
            hardware_sensor_hil_entry_callback_review_decision_summary
        ),
        hardware_sensor_hil_entry_callback_review_handoff=(
            hardware_sensor_hil_entry_callback_review_handoff_summary
        ),
        hardware_sensor_hil_entry_callback_review_handoff_summary=(
            hardware_sensor_hil_entry_callback_review_handoff_summary
        ),
        robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary=(
            hardware_sensor_hil_entry_callback_review_handoff_summary
        ),
        pr5_review_thread_closeout=pr5_review_thread_closeout_summary,
        pr5_review_thread_closeout_summary=pr5_review_thread_closeout_summary,
        robot_diagnostics_pr5_review_thread_closeout_summary=(
            pr5_review_thread_closeout_summary
        ),
        pr5_vendor_source_review_packet=pr5_vendor_source_review_packet_summary,
        pr5_vendor_source_review_packet_summary=pr5_vendor_source_review_packet_summary,
        robot_diagnostics_pr5_vendor_source_review_packet_summary=(
            pr5_vendor_source_review_packet_summary
        ),
        pr5_vendor_source_review_reply_dispatch=(
            pr5_vendor_source_review_reply_dispatch_summary
        ),
        pr5_vendor_source_review_reply_dispatch_summary=(
            pr5_vendor_source_review_reply_dispatch_summary
        ),
        robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary=(
            pr5_vendor_source_review_reply_dispatch_summary
        ),
        pr5_mandatory_sensor_source_alignment=(
            pr5_mandatory_sensor_source_alignment_summary
        ),
        pr5_mandatory_sensor_source_alignment_summary=(
            pr5_mandatory_sensor_source_alignment_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary=(
            pr5_mandatory_sensor_source_alignment_summary
        ),
        pr5_mandatory_sensor_material_followup_escalation_status=(
            pr5_mandatory_sensor_material_followup_escalation_status_summary
        ),
        pr5_mandatory_sensor_material_followup_escalation_status_summary=(
            pr5_mandatory_sensor_material_followup_escalation_status_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary=(
            pr5_mandatory_sensor_material_followup_escalation_status_summary
        ),
        pr5_mandatory_sensor_material_owner_response_intake=(
            pr5_mandatory_sensor_material_owner_response_intake_summary
        ),
        pr5_mandatory_sensor_material_owner_response_intake_summary=(
            pr5_mandatory_sensor_material_owner_response_intake_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary=(
            pr5_mandatory_sensor_material_owner_response_intake_summary
        ),
        pr5_mandatory_sensor_material_owner_response_review_decision=(
            pr5_mandatory_sensor_material_owner_response_review_decision_summary
        ),
        pr5_mandatory_sensor_material_owner_response_review_decision_summary=(
            pr5_mandatory_sensor_material_owner_response_review_decision_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary=(
            pr5_mandatory_sensor_material_owner_response_review_decision_summary
        ),
        pr5_mandatory_sensor_material_owner_response_review_handoff=(
            pr5_mandatory_sensor_material_owner_response_review_handoff_summary
        ),
        pr5_mandatory_sensor_material_owner_response_review_handoff_summary=(
            pr5_mandatory_sensor_material_owner_response_review_handoff_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary=(
            pr5_mandatory_sensor_material_owner_response_review_handoff_summary
        ),
        pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake=(
            pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary
        ),
        pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary=(
            pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary
        ),
        robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary=(
            pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary
        ),
        hardware_real_material_escalation_request=(
            hardware_real_material_escalation_request_summary
        ),
        hardware_real_material_escalation_request_summary=(
            hardware_real_material_escalation_request_summary
        ),
        robot_diagnostics_hardware_real_material_escalation_request_summary=(
            hardware_real_material_escalation_request_summary
        ),
        real_material_readiness_board=real_material_readiness_board_summary,
        real_material_readiness_board_summary=real_material_readiness_board_summary,
        robot_diagnostics_real_material_readiness_board_summary=(
            real_material_readiness_board_summary
        ),
        real_material_evidence_intake=real_material_evidence_intake_summary,
        real_material_evidence_intake_summary=real_material_evidence_intake_summary,
        robot_diagnostics_real_material_evidence_intake_summary=(
            real_material_evidence_intake_summary
        ),
        verified_terminal_result_material_intake=(
            verified_terminal_result_material_intake_summary
        ),
        verified_terminal_result_material_intake_summary=(
            verified_terminal_result_material_intake_summary
        ),
        robot_diagnostics_verified_terminal_result_material_intake_summary=(
            verified_terminal_result_material_intake_summary
        ),
        verified_terminal_result_material_review_decision=(
            verified_terminal_result_material_review_decision_summary
        ),
        verified_terminal_result_material_review_decision_summary=(
            verified_terminal_result_material_review_decision_summary
        ),
        robot_diagnostics_verified_terminal_result_material_review_decision_summary=(
            verified_terminal_result_material_review_decision_summary
        ),
        verified_terminal_result_material_review_handoff=(
            verified_terminal_result_material_review_handoff_summary
        ),
        verified_terminal_result_material_review_handoff_summary=(
            verified_terminal_result_material_review_handoff_summary
        ),
        robot_diagnostics_verified_terminal_result_material_review_handoff_summary=(
            verified_terminal_result_material_review_handoff_summary
        ),
        verified_terminal_result_material_followup_escalation_status=(
            verified_terminal_result_material_followup_escalation_status_summary
        ),
        verified_terminal_result_material_followup_escalation_status_summary=(
            verified_terminal_result_material_followup_escalation_status_summary
        ),
        robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary=(
            verified_terminal_result_material_followup_escalation_status_summary
        ),
        verified_terminal_result_material_owner_response_intake=(
            verified_terminal_result_material_owner_response_intake_summary
        ),
        verified_terminal_result_material_owner_response_intake_summary=(
            verified_terminal_result_material_owner_response_intake_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary=(
            verified_terminal_result_material_owner_response_intake_summary
        ),
        verified_terminal_result_material_owner_response_review_decision=(
            verified_terminal_result_material_owner_response_review_decision_summary
        ),
        verified_terminal_result_material_owner_response_review_decision_summary=(
            verified_terminal_result_material_owner_response_review_decision_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary=(
            verified_terminal_result_material_owner_response_review_decision_summary
        ),
        verified_terminal_result_material_owner_response_review_handoff=(
            verified_terminal_result_material_owner_response_review_handoff_summary
        ),
        verified_terminal_result_material_owner_response_review_handoff_summary=(
            verified_terminal_result_material_owner_response_review_handoff_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary=(
            verified_terminal_result_material_owner_response_review_handoff_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_intake=(
            verified_terminal_result_material_owner_response_reviewer_ack_intake_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_intake_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_intake_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_intake_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_review_decision=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_review_handoff=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status=(
            verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary=(
            verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary
        ),
        real_material_followup_escalation_status=(
            real_material_followup_escalation_status_summary
        ),
        real_material_followup_escalation_status_summary=(
            real_material_followup_escalation_status_summary
        ),
        robot_diagnostics_real_material_followup_escalation_status_summary=(
            real_material_followup_escalation_status_summary
        ),
        field_evidence_real_material_followup_escalation_status=(
            field_evidence_real_material_followup_escalation_status_summary
        ),
        field_evidence_real_material_followup_escalation_status_summary=(
            field_evidence_real_material_followup_escalation_status_summary
        ),
        robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary=(
            field_evidence_real_material_followup_escalation_status_summary
        ),
        field_evidence_real_material_owner_ack_intake=(
            field_evidence_real_material_owner_ack_intake_summary
        ),
        field_evidence_real_material_owner_ack_intake_summary=(
            field_evidence_real_material_owner_ack_intake_summary
        ),
        robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary=(
            field_evidence_real_material_owner_ack_intake_summary
        ),
        field_evidence_real_material_owner_ack_review_decision=(
            field_evidence_real_material_owner_ack_review_decision_summary
        ),
        field_evidence_real_material_owner_ack_review_decision_summary=(
            field_evidence_real_material_owner_ack_review_decision_summary
        ),
        robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary=(
            field_evidence_real_material_owner_ack_review_decision_summary
        ),
        field_evidence_material_blocker_escalation_pack=(
            field_evidence_material_blocker_escalation_pack_summary
        ),
        field_evidence_material_blocker_escalation_pack_summary=(
            field_evidence_material_blocker_escalation_pack_summary
        ),
        robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary=(
            field_evidence_material_blocker_escalation_pack_summary
        ),
        field_evidence_material_resolution_intake=(
            field_evidence_material_resolution_intake_summary
        ),
        field_evidence_material_resolution_intake_summary=(
            field_evidence_material_resolution_intake_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_intake_summary=(
            field_evidence_material_resolution_intake_summary
        ),
        field_evidence_material_resolution_review_decision=(
            field_evidence_material_resolution_review_decision_summary
        ),
        field_evidence_material_resolution_review_decision_summary=(
            field_evidence_material_resolution_review_decision_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_review_decision_summary=(
            field_evidence_material_resolution_review_decision_summary
        ),
        field_evidence_material_resolution_review_handoff=(
            field_evidence_material_resolution_review_handoff_summary
        ),
        field_evidence_material_resolution_review_handoff_summary=(
            field_evidence_material_resolution_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_review_handoff_summary=(
            field_evidence_material_resolution_review_handoff_summary
        ),
        field_evidence_material_resolution_followup_escalation_status=(
            field_evidence_material_resolution_followup_escalation_status_summary
        ),
        field_evidence_material_resolution_followup_escalation_status_summary=(
            field_evidence_material_resolution_followup_escalation_status_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary=(
            field_evidence_material_resolution_followup_escalation_status_summary
        ),
        field_evidence_material_resolution_owner_response_intake=(
            field_evidence_material_resolution_owner_response_intake_summary
        ),
        field_evidence_material_resolution_owner_response_intake_summary=(
            field_evidence_material_resolution_owner_response_intake_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary=(
            field_evidence_material_resolution_owner_response_intake_summary
        ),
        field_evidence_material_resolution_owner_response_review_decision=(
            field_evidence_material_resolution_owner_response_review_decision_summary
        ),
        field_evidence_material_resolution_owner_response_review_decision_summary=(
            field_evidence_material_resolution_owner_response_review_decision_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary=(
            field_evidence_material_resolution_owner_response_review_decision_summary
        ),
        field_evidence_material_resolution_owner_response_review_handoff=(
            field_evidence_material_resolution_owner_response_review_handoff_summary
        ),
        field_evidence_material_resolution_owner_response_review_handoff_summary=(
            field_evidence_material_resolution_owner_response_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary=(
            field_evidence_material_resolution_owner_response_review_handoff_summary
        ),
        field_evidence_material_resolution_reviewer_ack_intake=(
            field_evidence_material_resolution_reviewer_ack_intake_summary
        ),
        field_evidence_material_resolution_reviewer_ack_intake_summary=(
            field_evidence_material_resolution_reviewer_ack_intake_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary=(
            field_evidence_material_resolution_reviewer_ack_intake_summary
        ),
        field_evidence_material_resolution_reviewer_ack_review_decision=(
            field_evidence_material_resolution_reviewer_ack_review_decision_summary
        ),
        field_evidence_material_resolution_reviewer_ack_review_decision_summary=(
            field_evidence_material_resolution_reviewer_ack_review_decision_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary=(
            field_evidence_material_resolution_reviewer_ack_review_decision_summary
        ),
        field_evidence_material_resolution_reviewer_ack_review_handoff=(
            field_evidence_material_resolution_reviewer_ack_review_handoff_summary
        ),
        field_evidence_material_resolution_reviewer_ack_review_handoff_summary=(
            field_evidence_material_resolution_reviewer_ack_review_handoff_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary=(
            field_evidence_material_resolution_reviewer_ack_review_handoff_summary
        ),
        field_evidence_material_resolution_reviewer_ack_followup_escalation_status=(
            field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary
        ),
        field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary=(
            field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary
        ),
        robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary=(
            field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary
        ),
        elevator_action_feedback_trace=elevator_action_feedback_trace_summary,
        robot_diagnostics_elevator_action_feedback_trace_summary=(
            elevator_action_feedback_trace_summary
        ),
        elevator_field_evidence_trace_callback_intake=(
            elevator_field_evidence_trace_callback_intake_summary
        ),
        elevator_field_evidence_trace_callback_intake_summary=(
            elevator_field_evidence_trace_callback_intake_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary=(
            elevator_field_evidence_trace_callback_intake_summary
        ),
        elevator_field_evidence_trace_callback_review_decision=(
            elevator_field_evidence_trace_callback_review_decision_summary
        ),
        elevator_field_evidence_trace_callback_review_decision_summary=(
            elevator_field_evidence_trace_callback_review_decision_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary=(
            elevator_field_evidence_trace_callback_review_decision_summary
        ),
        elevator_field_evidence_trace_callback_review_handoff=(
            elevator_field_evidence_trace_callback_review_handoff_summary
        ),
        elevator_field_evidence_trace_callback_review_handoff_summary=(
            elevator_field_evidence_trace_callback_review_handoff_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary=(
            elevator_field_evidence_trace_callback_review_handoff_summary
        ),
        elevator_field_evidence_trace_material_backfill_intake=(
            elevator_field_evidence_trace_material_backfill_intake_summary
        ),
        elevator_field_evidence_trace_material_backfill_intake_summary=(
            elevator_field_evidence_trace_material_backfill_intake_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary=(
            elevator_field_evidence_trace_material_backfill_intake_summary
        ),
        elevator_field_evidence_trace_material_backfill_review_decision=(
            elevator_field_evidence_trace_material_backfill_review_decision_summary
        ),
        elevator_field_evidence_trace_material_backfill_review_decision_summary=(
            elevator_field_evidence_trace_material_backfill_review_decision_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary=(
            elevator_field_evidence_trace_material_backfill_review_decision_summary
        ),
        elevator_field_evidence_trace_material_backfill_review_handoff=(
            elevator_field_evidence_trace_material_backfill_review_handoff_summary
        ),
        elevator_field_evidence_trace_material_backfill_review_handoff_summary=(
            elevator_field_evidence_trace_material_backfill_review_handoff_summary
        ),
        robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary=(
            elevator_field_evidence_trace_material_backfill_review_handoff_summary
        ),
        elevator_assist=elevator_assist,
        elevator_assist_status=elevator_assist_status,
        hardware_proof=summarize_hardware_proof(hardware_proof_ref),
        oss_cdn_manifest=build_phone_oss_cdn_manifest_summary(oss_cdn_manifest_artifact_ref),
        network_recovery_drill=build_phone_network_recovery_summary(
            network_recovery_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT", "")
        ),
        credential_rotation=build_phone_credential_rotation_summary(
            credential_rotation_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_CREDENTIAL_ROTATION_ARTIFACT", "")
        ),
        provisioning_audit=build_phone_provisioning_audit_summary(
            provisioning_audit_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT", "")
        ),
        production_store_queue=build_phone_production_store_queue_summary(
            production_store_queue_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT", "")
        ),
        queue_ordering_drill=build_phone_queue_ordering_drill_summary(
            queue_ordering_drill_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT", "")
        ),
        transaction_isolation=build_phone_transaction_isolation_summary(
            transaction_isolation_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT", "")
        ),
        production_recovery=build_phone_production_recovery_summary(
            production_recovery_artifact_ref
            or os.environ.get("TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT", "")
        ),
        cloud_worker_migration_rehearsal=summarize_cloud_worker_migration_rehearsal(
            cloud_worker_migration_rehearsal_artifact_ref
            or os.environ.get("TRASHBOT_CLOUD_WORKER_MIGRATION_REHEARSAL", "")
            or os.environ.get("TRASHBOT_CLOUD_WORKER_MIGRATION_REHEARSAL_SUMMARY", "")
        ),
        cloud_worker_cutover_drain=summarize_cloud_worker_cutover_drain(
            cloud_worker_cutover_drain_artifact_ref
            or os.environ.get("TRASHBOT_CLOUD_WORKER_CUTOVER_DRAIN", "")
            or os.environ.get("TRASHBOT_CLOUD_WORKER_CUTOVER_DRAIN_SUMMARY", "")
        ),
        operator_status_file=str(operator_status_file or ""),
    )


def diagnostics_payload(latest_status=None, **kwargs):
    """兼容脚本型验收入口，默认生成最小 diagnostics payload。"""
    # 轻量 wrapper 让一次性 handoff 验收不用重复传入与 schema 无关的版本/路径字段。
    defaults = {
        "software_version": "",
        "map_version": "",
        "route_version": "",
        "log_refs": [],
        "vision_sample_manifest_ref": "",
        "review_decision_log_ref": "",
        "operator_status_file": "",
    }
    defaults.update(kwargs)
    return build_diagnostics_payload(latest_status or {}, **defaults)
