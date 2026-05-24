# ROS Runtime Contracts

## cloud_hosted_mobile_web_degradation_passthrough

`cloud_hosted_mobile_web_degradation_passthrough` is the Robot/API contract for the cloud-hosted same-origin mobile `GET /api/status` adapter. It consumes only sanitized relay latest status metadata and, when present, preserves an allow-listed safe `remote_readiness.degradation_state` instead of flattening degraded status to only `state=status_present`.

The contract is read-only and fail-closed:

- `source=software_proof`
- `proof_boundary=software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`
- `not_proven`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

Allowed degradation states are `auth_failed`, `cloud_poll_backoff`, `manual_takeover_required`, `command_pending`, `command_expired`, `command_duplicate_deduped`, `command_id_conflict`, `command_sequence_regression`, `cloud_unreachable`, and `malformed_response`. The hosted adapter may expose `remote_readiness.degradation_state`, `retry_hint`, `safe_phone_copy`, `source=software_proof`, and the explicit false control fields above. Missing latest status still returns `state=status_missing`; stale status still returns `state=status_stale`.

The adapter must not expose bearer tokens, Authorization headers, credentials, raw cloud payloads, DB/queue URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, local paths, tracebacks, checksums, complete artifacts, HIL/pass wording, delivery result, or delivery success. Any unsupported degradation state, unsafe copied field, `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, or `remote_ready=true` is overwritten or blocked so Start Delivery, Confirm Dropoff, Cancel, ACK/cursor fetch, retry/replay/resubmit, queue advancement, dropoff/cancel completion, delivery result, and primary robot actions remain disabled.

This boundary is Docker/local software proof only. It is not real external cloud proof, true phone/browser proof, HIL, WAVE ROVER/UART proof, route/elevator field pass, delivery result, or delivery success.

## robot_diagnostics_cloud_unreachable_malformed_response_guard_summary

`robot_diagnostics_cloud_unreachable_malformed_response_guard_summary` is the Robot diagnostics safe alias for the `cloud_unreachable_malformed_response_guard` gate. It consumes only phone-safe `remote_readiness` metadata for the degradation states `cloud_unreachable` and `malformed_response`; the evidence boundary must remain `software_proof_docker_cloud_unreachable_malformed_response_guard`.

The alias is diagnostics-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

Allowed Robot-visible fields are limited to sanitized guard metadata: `guard`, `degradation_state`, `status`, `evidence_boundary`, `retry_hint`, `safe_copy`, `safe_phone_copy`, `false_states`, `not_proven`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `ack_cursor_fetch_allowed=false`, `retry_replay_resubmit_allowed=false`, `queue_advancement_allowed=false`, and `robot_command_side_effects_allowed=false`.

The alias must not expose bearer tokens, Authorization headers, credentials, DB/queue URLs, OSS AK/SK, raw cloud response bodies, tracebacks, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, HIL/pass wording, delivery success wording, ACK/cursor state, retry/replay/resubmit requests, queue advancement, or hidden robot command side effects. Missing safe metadata, unsupported degradation state, unsafe copy, raw response markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, or `remote_ready=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor fetch, retry, replay, resubmit, queue advancement, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## cloud_manual_takeover_command_safety_guard

`cloud_manual_takeover_command_safety_guard` is the Robot/API safe degraded
state for manual takeover and human-help outcomes. It is emitted when Robot
status or ACK operator status reaches `needs_human_help`, `failed`, or an
explicit `degradation_state=manual_takeover_required`.

The contract is fail-closed:

- `capability=cloud_manual_takeover_command_safety_guard`
- `degradation_state=manual_takeover_required`
- `manual_takeover_required=true`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=contact_support`
- `ack_semantics=manual_takeover_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`
- `safe_phone_copy=需要人工接管；远程主操作已暂停，请按现场/支持指引处理。这不是送达成功。`

Diagnostics remain visible, but only through redacted `remote_readiness`,
`phone_readiness`, `phone_task_flow_readiness`, support handoff, voice prompt,
and offline/resume summaries. Missing canonical fields or unsafe upstream
values such as `remote_ready=true`, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true` must be overwritten
to the fail-closed values above.

This boundary is Docker/local `software_proof` only. It is not real external
cloud proof, true phone/browser proof, HIL, WAVE ROVER/UART proof,
route/elevator field pass, delivery result, or delivery success.

## robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary

`robot_diagnostics_pr5_mandatory_sensor_source_alignment_summary` is the Robot diagnostics safe alias for the `pr5_mandatory_sensor_source_alignment` gate. It consumes only the sanitized summary schema `trashbot.pr5_mandatory_sensor_source_alignment_summary.v1`, whose `source_schema` must point back to `trashbot.pr5_mandatory_sensor_source_alignment.v1` and whose evidence boundary must remain `software_proof_docker_pr5_mandatory_sensor_source_alignment_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized source-alignment metadata: `thread_id`, `source_boundary`, `missing_materials`, `next_required_evidence`, `owner_handoff`, `evidence_boundary`, `false_states`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw source material, raw local paths, serial/UART details, credentials, ROS topic or control details, HIL/pass wording, delivery success wording, GitHub resolution claims, ACK/cursor state, or robot command requests. Missing sanitized summary, unsupported schema or boundary, missing false states, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, hardware validation, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary

`robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary` is the Robot diagnostics safe alias for `pr5_mandatory_sensor_material_followup_escalation_status`. It consumes only the PC sanitized summary schema `trashbot.pr5_mandatory_sensor_material_followup_escalation_status_summary.v1`, whose `source_schema` must point back to `trashbot.pr5_mandatory_sensor_material_followup_escalation_status.v1` and whose evidence boundary must remain `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe follow-up metadata: `followup_status` (`pending`, `overdue`, `escalated`, `blocked`, or `ready_for_reviewer_followup_not_proven`), `source_alignment_status`, `safe_evidence_ref`, `pending_reasons`, `overdue_reasons`, `escalated_reasons`, `blocked_reasons`, `missing_required_material_refs`, `owner_next_step`, `reviewer_next_step`, `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`, `pr5_material_state=hardware_material_pending`, `evidence_boundary`, `proof_boundary`, `false_states`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw manifests, complete artifacts, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, success wording, external-proof wording, HIL/pass wording, installed-sensor wording, PR-resolution wording, ACK/cursor state, or robot command requests. Missing summary, malformed input, unsupported schema or boundary, weak safe evidence ref, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, hardware validation, dropoff/cancel completion, delivery result, and primary robot actions disabled.

This boundary is Docker/local `software_proof` only. It does not prove real 2D LiDAR / ToF SKU/source/receipt/procurement material, mounting/installation material, wiring or power-budget material, calibration, HIL-entry material, operator HIL report, installed sensors, WAVE ROVER/UART proof, route/elevator field pass, delivery success, Objective 5 external proof, verified terminal result, or PR #5 reviewer resolution.

## robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary

`robot_diagnostics_pr5_mandatory_sensor_material_owner_response_intake_summary` is the Robot diagnostics safe alias for `pr5_mandatory_sensor_material_owner_response_intake`. It consumes only the PC sanitized summary schema `trashbot.pr5_mandatory_sensor_material_owner_response_intake_summary.v1`, whose `source_schema` must point back to `trashbot.pr5_mandatory_sensor_material_owner_response_intake.v1` and whose evidence boundary must remain `software_proof_docker_pr5_mandatory_sensor_material_owner_response_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe owner-response intake metadata: `decision` (`accepted`, `missing`, `rejected`, `unsafe`, or `blocked`), `source_followup_status`, `safe_evidence_ref`, `accepted_material_refs`, `missing_material_refs`, `rejected_material_refs`, `unsafe_material_refs`, `next_required_evidence`, `owner_next_step`, `reviewer_next_step`, `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`, `pr5_material_state=hardware_material_pending`, `evidence_boundary`, `proof_boundary`, `false_states`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw owner response bodies, raw manifests, complete artifacts, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, success wording, external-proof wording, HIL pass wording, installed-sensor wording, PR-resolution wording, ACK/cursor state, or robot command requests. Missing summary, malformed input, unsupported schema or boundary, weak safe evidence ref, raw-only owner response input, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, hardware validation, dropoff/cancel completion, delivery result, and primary robot actions disabled.

This boundary is Docker/local `software_proof` only. It does not prove real 2D LiDAR / ToF SKU/source/receipt/procurement material, mounting/installation material, wiring or power-budget material, calibration, HIL-entry material, operator HIL report, installed sensors, WAVE ROVER/UART proof, route/elevator field pass, delivery success, Objective 5 external proof, verified terminal result, PR #5 reviewer resolution, or `accepted` owner material as real hardware proof.

## robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary

`robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_decision_summary` is the Robot diagnostics safe alias for `pr5_mandatory_sensor_material_owner_response_review_decision`. It consumes only the PC sanitized summary schema `trashbot.pr5_mandatory_sensor_material_owner_response_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.pr5_mandatory_sensor_material_owner_response_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe review-decision metadata: `review_decision` (`accepted_for_reviewer_closeout_not_proven`, `needs_more_material_not_proven`, `rejected_unsafe_material_not_proven`, `blocked_missing_owner_response_intake_not_proven`, or `blocked_evidence_ref_mismatch_not_proven`), `source_intake_status`, `safe_evidence_ref`, `missing_material_summaries`, `rejected_material_summaries`, `unsafe_material_summaries`, `decision_reasons`, `reviewer_next_step`, `owner_next_step`, `next_required_evidence`, `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`, `pr5_material_state=hardware_material_pending`, `evidence_boundary`, `proof_boundary`, `evidence_boundary_status=not_proven`, `false_states`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw owner response bodies, raw PR review bodies, real material payloads, complete artifacts, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, success wording, external-proof wording, HIL pass wording, installed-sensor wording, PR-resolution wording, ACK/cursor state, or robot command requests. Missing summary, malformed input, unsupported schema or boundary, weak safe evidence ref, raw-only owner response input, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, hardware validation, dropoff/cancel completion, delivery result, and primary robot actions disabled.

This boundary is Docker/local `software_proof` only. It does not prove real 2D LiDAR / ToF SKU/source/receipt/procurement material, mounting/installation material, wiring or power-budget material, calibration, HIL-entry material, operator HIL report, installed sensors, WAVE ROVER/UART proof, route/elevator field pass, delivery success, Objective 5 external proof, verified terminal result, PR #5 reviewer resolution, or accepted owner material as real hardware proof.

## robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary

`robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary` is the Robot diagnostics safe alias for `pr5_mandatory_sensor_material_owner_response_review_handoff`. It consumes only the PC sanitized summary schema `trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.pr5_mandatory_sensor_material_owner_response_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe review-handoff metadata: `handoff_status` (`handoff_ready_not_proven`, `needs_more_material_not_proven`, `rejected_unsafe_material_not_proven`, `blocked_missing_review_decision_not_proven`, or `blocked_evidence_ref_mismatch_not_proven`), `source_review_decision_status`, `safe_evidence_ref`, `handoff_reasons`, `missing_material_summaries`, `reviewer_next_step`, `owner_next_step`, `support_next_step`, `next_required_evidence`, `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`, `pr5_thread_state=unresolved`, `pr5_material_state=hardware_material_pending`, `evidence_boundary`, `proof_boundary`, `evidence_boundary_status=not_proven`, `false_states`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw owner response bodies, raw PR review bodies, raw artifacts, real material payloads, complete artifacts, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, DB/queue URLs, success wording, external-proof wording, HIL pass wording, installed-sensor wording, PR-resolution wording, ACK/cursor state, remote review update, or robot command requests. Missing summary, malformed input, unsupported schema or boundary, weak safe evidence ref, raw-only handoff input, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, remote review update, Nav2, hardware validation, dropoff/cancel completion, delivery result, and primary robot actions disabled.

This boundary is Docker/local `software_proof` only. It does not prove real 2D LiDAR / ToF SKU/source/receipt/procurement material, mounting/installation material, wiring or power-budget material, calibration, HIL-entry material, operator HIL report, installed sensors, WAVE ROVER/UART proof, route/elevator field pass, delivery success, Objective 5 external proof, verified terminal result, PR #5 reviewer resolution, or accepted owner material as real hardware proof.

## robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary

`robot_diagnostics_hardware_sensor_hil_entry_callback_review_decision_summary` is the Robot diagnostics safe alias for the `hardware_sensor_hil_entry_callback_review_decision` gate. It consumes only the sanitized summary schema `trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.hardware_sensor_hil_entry_callback_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `hardware_material_status=hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe review metadata: `safe_evidence_ref`, `review_status`, `review_decision`, `accepted_materials`, `missing_materials`, `rejected_materials`, `decision_reasons`, `next_required_evidence`, `owner_handoff`, `rerun_commands`, `same_evidence_ref_required`, `same_evidence_ref_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw callback/review artifacts, ROS topic names, ACK/cursor state, Nav2/HIL triggers, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, or success/control claims. Missing sanitized summary, unsupported schema or boundary, weak `safe_evidence_ref`, `same_evidence_ref_required=false`, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary

`robot_diagnostics_hardware_sensor_hil_entry_callback_review_handoff_summary` is the Robot diagnostics safe alias for the `hardware_sensor_hil_entry_callback_review_handoff` gate. It consumes only the sanitized summary schema `trashbot.hardware_sensor_hil_entry_callback_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.hardware_sensor_hil_entry_callback_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_hardware_sensor_hil_entry_callback_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `hardware_material_status=hardware_material_pending`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe handoff metadata: `safe_evidence_ref`, `handoff_status`, `handoff_decision`, `source_review_decision_status`, `missing_materials`, `next_required_evidence`, `owner_handoff`, `rerun_guidance`, `same_evidence_ref_required`, `same_evidence_ref_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw material payloads, raw JSON, raw callback/review/handoff artifacts, ROS topic names, ACK/cursor state, Nav2/HIL triggers, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, complete internal logs, or success/control claims. Missing sanitized summary, malformed input, unsupported schema or boundary, wrong `source`, weak `safe_evidence_ref`, `same_evidence_ref_required=false`, unsafe copy, raw markers, enabled action flags, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` keeps the summary blocked/not_proven and leaves Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_handoff_intake_summary

`robot_diagnostics_field_evidence_rerun_handoff_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_handoff_intake` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_handoff_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_handoff_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_handoff_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe status and routing metadata: `safe_evidence_ref`, `intake_status`, `owner_ack_status`, `next_owner`, `owner_handoff`, `next_required_evidence`, `rerun_guidance`, `blocker_summary`, `same_evidence_ref_required`, `same_evidence_ref_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw artifact data, ROS topic names, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, ACK/cursor state, or success/control claims. Any missing sanitized summary, schema/boundary mismatch, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, or hardware/control wording keeps the summary blocked/not_proven and leaves primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_queue_summary

`robot_diagnostics_field_evidence_rerun_queue_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_queue` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_queue_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_queue.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_queue_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe queue and routing metadata: `safe_evidence_ref`, `queue_status`, `source_handoff_intake_schema`, `source_handoff_intake_status`, `same_evidence_ref_status`, `blocker_summary`, `next_required_evidence`, `owner_handoff`, `safe_rerun_hint`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw artifact data, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, or success/control claims. Any missing sanitized summary, unsupported schema or boundary, `safe_evidence_ref` mismatch, missing required safe metadata, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, or hardware/control wording keeps the summary blocked/not_proven and leaves primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_pack_summary

`robot_diagnostics_field_evidence_rerun_execution_pack_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_pack` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_execution_pack_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_pack.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_pack_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to safe execution-pack metadata: `safe_evidence_ref`, `execution_pack_status`, `source_queue_schema`, `source_queue_status`, `same_evidence_ref_status`, `execution_steps`, `material_templates`, `owner_handoff`, `fail_thresholds`, `pass_thresholds`, `backfill_instructions`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw artifact data, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, or success/control claims. Any missing sanitized summary, unsupported schema or boundary, `safe_evidence_ref` mismatch, missing required safe metadata, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves primary robot actions disabled. It does not prove real field rerun, Nav2, route/elevator field pass, phone/browser validation, WAVE ROVER/UART/HIL, dropoff/cancel completion, or delivery success.

## robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_callback_intake` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_execution_callback_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_callback_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized callback-intake metadata: `safe_evidence_ref`, `source_execution_pack_schema`, `source_execution_pack_status`, `callback_packet_schema`, `callback_packet_status`, `same_evidence_ref_status`, `accepted_materials`, `missing_materials`, `rejected_materials`, `blocked_materials`, `owner_handoff`, `next_required_evidence`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw callback artifacts, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing sanitized summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing required safe metadata, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_callback_review_decision` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_callback_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-decision metadata: `safe_evidence_ref`, `source_callback_intake_schema`, `source_callback_intake_status`, `review_status`, `review_decision`, `same_evidence_ref_status`, `accepted_materials`, `missing_materials`, `rejected_materials`, `blocked_materials`, `decision_reasons`, `owner_handoff`, `next_required_evidence`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw callback/review artifacts, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing sanitized summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing required safe metadata, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_callback_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_callback_review_handoff` gate. It consumes only the sanitized summary schema `trashbot.field_evidence_rerun_execution_callback_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_callback_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized handoff metadata: `safe_evidence_ref`, `handoff_status`, `review_decision`, `owner_handoff`, `next_required_evidence`, `rerun_guidance`, `reconciliation_guidance`, `blocker_summary`, `same_evidence_ref_required`, `same_evidence_ref_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw callback, review, or handoff artifacts, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, PR #5 resolved claims, or success/control claims. Missing sanitized summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing required safe metadata, enabled action flag, unsafe copy, raw marker, local path, checksum, credential, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_result_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_intake` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized result-intake metadata: `safe_evidence_ref`, `result_intake_status`, `owner_handoff`, `missing_reasons`, `rejected_reasons`, `blocked_reasons`, `next_required_evidence`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw result packet material, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw packet marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_result_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_review_decision` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-decision metadata: `safe_evidence_ref`, `review_status`, `review_decision`, `intake_reference`, `source_result_intake_schema`, `source_result_intake_status`, `same_evidence_ref_status`, `blocker_reason`, `rejection_reason`, `backfill_reason`, `next_required_evidence`, `owner_handoff`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw result or review packet material, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw packet marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_review_handoff` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-handoff metadata: `safe_evidence_ref`, `handoff_status`, `source_review_decision`, `source_review_decision_status`, `same_evidence_ref_status`, `owner_handoff`, `blocker_summary`, `next_required_real_materials`, `reconciliation_guidance`, `rerun_guidance`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose unsafe raw review-decision or result packet material, complete artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw packet marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_packet_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_packet` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_packet_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_packet.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized acceptance readiness metadata: `safe_evidence_ref`, `acceptance_status`, `acceptance_verdict`, `same_evidence_ref_required`, `same_evidence_ref_status`, `required_materials`, `accepted_materials`, `missing_materials`, `blocked_materials`, `owner_next_steps`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw task records, raw logs, raw route/elevator artifacts, complete acceptance packet bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution claims, comment `3269642220` reviewer-resolution claims, or success/control claims. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_backfill` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_backfill_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_backfill.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized acceptance-backfill metadata: `safe_evidence_ref`, `backfill_status`, `backfill_verdict`, `same_evidence_ref_required`, `same_evidence_ref_status`, `required_materials`, `accepted_materials`, `missing_materials`, `blocked_materials`, `owner_next_steps`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete acceptance-backfill artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_backfill_review_decision` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_backfill_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_backfill_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-decision metadata: `decision`, `safe_evidence_ref`, `missing_categories`, `rejected_categories`, `owner_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`. Expected safe decision values include `needs_more_material` for incomplete backfill review and `ready_for_field_rerun_result_acceptance_review_handoff` only as an owner next-step handoff label, not as proof that the robot can control or that delivery succeeded.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete review-decision artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, external-proof wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary or backfill, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, `evidence_ref_mismatch`, enabled action flag, `unsafe_rejected`, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_review_handoff` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized handoff metadata: `handoff_status`, `safe_evidence_ref`, `required_materials`, `blocked_categories`, `rejected_categories`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`. Expected handoff status values are exactly `ready_for_field_owner_support_reviewer_handoff_not_proven`, `handoff_needs_more_material`, `handoff_evidence_ref_mismatch`, `handoff_unsafe_rejected`, and `blocked_missing_review_decision`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete handoff artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary or review decision, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, `handoff_unsafe_rejected`, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized intake metadata: `intake_status`, `safe_evidence_ref`, `accepted_material_refs`, `required_checklist`, `blocked_categories`, `rejected_categories`, `owner_next_step`, `support_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected intake status values are exactly `ready_for_acceptance_handoff_owner_intake_not_proven`, `intake_needs_more_material`, `intake_evidence_ref_mismatch`, `intake_unsafe_rejected`, and `blocked_missing_review_handoff`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete intake artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary or review handoff, malformed input, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, `intake_unsafe_rejected`, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-decision metadata: `review_decision_status`, `source_intake_status`, `safe_evidence_ref`, `accepted_material_refs`, `missing_or_rework_reasons`, `rejected_categories`, `owner_next_step`, `support_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected review decision status values are exactly `ready_for_acceptance_handoff_review_handoff_not_proven`, `review_needs_owner_rework`, `review_evidence_ref_mismatch`, `review_unsafe_rejected`, and `blocked_missing_handoff_intake`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete review-decision artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary or source handoff intake, malformed input, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, `review_unsafe_rejected`, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-handoff metadata: `review_handoff_status`, `source_review_decision_status`, `safe_evidence_ref`, `accepted_material_refs`, `missing_or_rework_reasons`, `rejected_categories`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected review handoff status values are exactly `ready_for_acceptance_review_handoff_not_proven`, `handoff_needs_owner_rework`, `handoff_evidence_ref_mismatch`, `handoff_unsafe_rejected`, and `blocked_missing_review_decision`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete review-handoff artifact bodies, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary or source review decision, malformed input, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, enabled action flag, `handoff_unsafe_rejected`, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized follow-up escalation metadata: `followup_state`, `followup_status`, `source_review_handoff_status`, `safe_evidence_ref`, `missing_required_material_refs`, `pending_reason`, `overdue_reason`, `escalated_reason`, `blocked_reason`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected follow-up states are exactly `pending`, `overdue`, `escalated`, and `blocked`.

The alias must not expose raw manifest contents, raw task records, raw logs, raw route/elevator artifacts, complete follow-up artifacts, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, unsupported follow-up state, unsafe copy, raw manifest/record/log/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized owner response intake metadata: `status`, `owner_response_intake_status`, `source_followup_escalation_status`, `safe_evidence_ref`, `accepted_material_refs`, `missing_material_refs`, `rejected_material_refs`, `blocked_material_refs`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected owner response intake status values are exactly `accepted`, `missing`, `rejected`, `blocked`, `accepted_not_proven`, `missing_not_proven`, `rejected_not_proven`, and `blocked_not_proven`.

The alias must not expose raw artifact data, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor state, external-proof wording, HIL/pass wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported owner response status, unsafe copy, raw artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized owner response review decision metadata: `status`, `review_decision_status`, `source_owner_response_intake_status`, `safe_evidence_ref`, `accepted_material_refs`, `missing_material_refs`, `rejected_material_refs`, `blocked_material_refs`, `decision_reasons`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected owner response review decision status values are exactly `ready_for_owner_response_review_handoff_not_proven`, `review_needs_owner_rework`, `review_evidence_ref_mismatch`, `review_unsafe_rejected`, and `blocked_missing_owner_response_intake`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported owner response review decision status, unsafe copy, raw artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized owner response review handoff metadata: `status`, `handoff_status`, `review_handoff_status`, `source_owner_response_review_decision_status`, `safe_evidence_ref`, `handoff_reasons`, `next_required_evidence`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected owner response review handoff status values are exactly `ready_for_owner_response_review_handoff_not_proven`, `handoff_needs_owner_rework`, `handoff_evidence_ref_mismatch`, `handoff_unsafe_rejected`, and `blocked_missing_owner_response_review_decision`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported owner response review handoff status, unsafe copy, raw manifest/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized reviewer ACK intake metadata: `status`, `ack_intake_status`, `reviewer_ack_intake_status`, `source_owner_response_review_handoff_status`, `safe_evidence_ref`, `ack_reasons`, `next_required_evidence`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected reviewer ACK intake status values are exactly `reviewer_acknowledged_not_proven`, `reviewer_ack_needs_reassignment`, `blocked_missing_owner_response_review_handoff`, `reviewer_ack_evidence_ref_mismatch`, and `reviewer_ack_rejected_unsafe`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, cursor state, external-proof wording, HIL/pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported reviewer ACK intake status, unsafe copy, raw manifest/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK posting, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized reviewer ACK review-decision metadata: `status`, `review_decision`, `review_status`, `source_reviewer_ack_intake_status`, `previous_reviewer_ack_intake_ref`, `safe_evidence_ref`, `decision_reasons`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `next_required_evidence`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `review_handoff_recommendation`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected reviewer ACK review-decision status values are exactly `accepted_for_reviewer_ack_review_not_proven`, `needs_reviewer_reassignment_not_proven`, `needs_field_owner_supplement_not_proven`, `rejected_unsafe_reviewer_ack_not_proven`, and `blocked_missing_reviewer_ack_intake_not_proven`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor mutation state, external-proof wording, HIL/pass wording, route/elevator field-pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported reviewer ACK review-decision status, unsafe copy, raw manifest/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, route/elevator field-pass wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK posting, cursor, replay/resubmit, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized reviewer ACK review-handoff metadata: `status`, `handoff_status`, `review_handoff_status`, `source_reviewer_ack_review_decision_schema`, `source_reviewer_ack_review_decision_status`, `previous_reviewer_ack_review_decision_ref`, `safe_evidence_ref`, `handoff_reasons`, `handoff_targets`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `next_required_evidence`, `owner_next_step`, `support_next_step`, `reviewer_next_step`, `review_handoff_recommendation`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected reviewer ACK review-handoff status values are exactly `ready_for_field_owner_reviewer_ack_followup_not_proven`, `needs_reviewer_handoff_reassignment_not_proven`, `needs_field_owner_ack_material_supplement_not_proven`, `rejected_unsafe_reviewer_ack_handoff_not_proven`, and `blocked_missing_reviewer_ack_review_decision_not_proven`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor mutation state, external-proof wording, HIL/pass wording, route/elevator field-pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported reviewer ACK review-handoff status, unsafe copy, raw manifest/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, route/elevator field-pass wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK posting, cursor, replay/resubmit, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary` is the Robot diagnostics safe alias for the `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` gate. It consumes only the canonical sanitized summary schema `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary.v1`, whose `source_schema` must point back to `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status.v1` and whose evidence boundary must remain `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `software_proof=true`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized reviewer ACK follow-up escalation metadata: `status`, `followup_escalation_status`, `source_reviewer_ack_review_handoff_schema`, `source_reviewer_ack_review_handoff_status`, `previous_reviewer_ack_review_handoff_ref`, `safe_evidence_ref`, `missing_evidence_summary`, `next_required_evidence`, `owner_next_step`, `reviewer_next_step`, `support_next_step`, `evidence_boundary_status`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, `software_proof`, and `not_proven`. Expected reviewer ACK follow-up escalation status values are exactly `pending_reviewer_ack_followup_not_proven`, `overdue_reviewer_ack_followup_not_proven`, `escalated_missing_real_material_not_proven`, `blocked_missing_reviewer_ack_review_handoff_not_proven`, and `ready_for_real_material_reviewer_followup_not_proven`.

The alias must not expose raw manifest contents, complete artifacts, local paths, checksum values, tracebacks, raw route/elevator materials, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, full material bodies, ACK/cursor mutation state, external-proof wording, HIL/pass wording, route/elevator field-pass wording, PR-resolution wording, dropoff/cancel completion, delivery result success, or success/control claims. Missing canonical summary, malformed input, unsupported schema or boundary, missing `safe_evidence_ref`, unsupported reviewer ACK follow-up escalation status, unsafe copy, raw manifest/artifact marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, external-proof wording, route/elevator field-pass wording, PR-resolution wording, or enabled action flags keep the summary blocked/not_proven and leave task_orchestrator, Start, Confirm Dropoff, Cancel, ACK posting, cursor, replay/resubmit, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_real_material_request_dispatch_summary

`robot_diagnostics_field_evidence_real_material_request_dispatch_summary` is the Robot diagnostics safe alias for the `field_evidence_real_material_request_dispatch` gate. It consumes the canonical sanitized summary schema `trashbot.field_evidence_real_material_request_dispatch_summary.v1`, or a compatible wrapper that contains that summary and points back to `trashbot.field_evidence_real_material_request_dispatch.v1`; the evidence boundary must remain `software_proof_docker_field_evidence_real_material_request_dispatch_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized request-dispatch metadata: `safe_evidence_ref`, `request_status`, `request_verdict`, `same_evidence_ref_required`, `same_evidence_ref_status`, `required_materials`, `owner_mapping`, `next_required_evidence`, `blocked_claims`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The required material categories are exactly `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `dropoff_cancel_completion`, `delivery_result`, `true_phone_browser_evidence`, and `diagnostics_mobile_safe_summary`. The alias preserves only the same safe `evidence_ref`, owner mapping, next required evidence, and safe copy needed by phone/diagnostics surfaces.

The alias must not expose raw artifact data, raw diagnostics, unsafe material, mismatched `evidence_ref`, success/control claims, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or complete artifact bodies. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing any of the nine material categories, missing owner mapping, missing next required evidence, enabled action flag, unsafe copy, raw artifact/diagnostics marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_real_material_response_intake_summary

`robot_diagnostics_field_evidence_real_material_response_intake_summary` is the Robot diagnostics safe alias for the `field_evidence_real_material_response_intake` gate. It consumes the canonical sanitized summary schema `trashbot.field_evidence_real_material_response_intake_summary.v1`, a compatible artifact wrapper that contains that summary, or the same summary nested under `latest_status.diagnostics`; the source schema must point back to `trashbot.field_evidence_real_material_response_intake.v1` and the evidence boundary must remain `software_proof_docker_field_evidence_real_material_response_intake_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized response-intake metadata: `safe_evidence_ref`, `response_status`, `response_verdict`, `same_evidence_ref_required`, `same_evidence_ref_status`, `required_materials`, `accepted_materials`, `missing_materials`, `rejected_materials`, `blocked_materials`, `material_statuses`, `next_required_evidence`, `blocked_claims`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The response categories are exactly `accepted`, `missing`, `rejected`, and `blocked`. The required material categories are exactly `task_record`, `nav2_fixed_route_runtime_log`, `route_completion_signal`, `elevator_door_floor_evidence`, `human_assistance_note`, `dropoff_cancel_completion`, `delivery_result`, `true_phone_browser_evidence`, and `diagnostics_mobile_safe_summary`. `accepted` only means the sanitized category is ready for later review; it is not route/elevator field pass, delivery result, delivery success, true phone/browser proof, Nav2 proof, HIL pass, WAVE ROVER/UART proof, O5 external proof, or PR #5 reviewer resolution.

The alias must not expose raw materials, raw artifact data, raw diagnostics, unsafe material, mismatched `evidence_ref`, success/control claims, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or complete artifact bodies. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing any of the nine material categories, missing the four response category buckets, missing next required evidence, missing blocked claims, enabled action flag, unsafe copy, raw artifact/diagnostics marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_real_material_response_review_decision_summary

`robot_diagnostics_field_evidence_real_material_response_review_decision_summary` is the Robot diagnostics safe alias for the `field_evidence_real_material_response_review_decision` gate. It consumes the canonical sanitized summary schema `trashbot.field_evidence_real_material_response_review_decision_summary.v1`, a compatible artifact wrapper that contains that summary, or the same summary nested under `latest_status.diagnostics`; the source schema must point back to `trashbot.field_evidence_real_material_response_review_decision.v1` and the evidence boundary must remain `software_proof_docker_field_evidence_real_material_response_review_decision_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-decision metadata: `safe_evidence_ref`, `source_response_intake_schema`, `source_response_intake_status`, `review_status`, `review_decision`, `same_evidence_ref_required`, `same_evidence_ref_status`, `accepted_materials`, `missing_materials`, `rejected_materials`, `blocked_materials`, `decision_reasons`, `owner_handoff`, `next_required_evidence`, `blocked_claims`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

Allowed `review_decision` values are `accepted_for_later_review_not_proven`, `needs_material_backfill_not_proven`, `rejected_unsafe_or_mixed_response_not_proven`, `blocked_real_environment_unavailable_not_proven`, and `blocked_missing_field_evidence_real_material_response_intake_not_proven`. `accepted_for_later_review_not_proven` only means the sanitized response can continue to a later human review; it is not route/elevator field pass, delivery result, delivery success, true phone/browser proof, Nav2 proof, HIL pass, WAVE ROVER/UART proof, O5 external proof, or PR #5 reviewer resolution.

The alias must not expose raw materials, raw artifact data, raw diagnostics, unsafe material, mismatched `evidence_ref`, success/control claims, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor state, HIL/pass wording, dropoff/cancel completion, delivery result success, or complete artifact bodies. Missing canonical summary, unsupported schema or boundary, unsupported decision value, same-`safe_evidence_ref` mismatch, missing review status, missing decision reasons, missing owner handoff, missing next required evidence, missing blocked claims, enabled action flag, unsafe copy, raw artifact/diagnostics marker, local path, checksum, credential, DB/queue URL, traceback marker, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_real_material_response_review_handoff_summary

`robot_diagnostics_field_evidence_real_material_response_review_handoff_summary` is the Robot diagnostics safe alias for the `field_evidence_real_material_response_review_handoff` gate. It consumes the canonical sanitized summary schema `trashbot.field_evidence_real_material_response_review_handoff_summary.v1`, a compatible artifact wrapper that contains that summary, or the same summary nested under `latest_status.diagnostics`; the source schema must point back to `trashbot.field_evidence_real_material_response_review_handoff.v1` and the evidence boundary must remain `software_proof_docker_field_evidence_real_material_response_review_handoff_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized review-handoff metadata: `safe_evidence_ref`, `source_review_decision`, `source_review_decision_status`, `handoff_status`, `handoff_decision`, `same_evidence_ref_required`, `same_evidence_ref_status`, `owner_handoff`, `next_required_evidence`, `blocker_summary`, `rerun_guidance`, `reconciliation_guidance`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

The alias must not expose raw artifacts, raw review-decision materials, raw diagnostics, unsafe material, mismatched `evidence_ref`, success/control claims, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor/control routes, HIL/pass wording, field-pass wording, delivery result success, or complete artifact bodies. Missing canonical summary, unsupported schema or boundary, same-`safe_evidence_ref` mismatch, missing source review decision status, missing owner handoff, missing next required evidence, missing blocker summary, enabled action flag, unsafe copy, raw artifact/review marker, local path, checksum, credential, DB/queue URL, traceback marker, ACK/cursor route, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.

## robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary

`robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary` is the Robot diagnostics safe alias for the `field_evidence_real_material_followup_escalation_status` gate. It consumes the canonical sanitized summary schema `trashbot.field_evidence_real_material_followup_escalation_status_summary.v1`, a compatible artifact wrapper that contains that summary, or the same summary nested under `latest_status.diagnostics`; the source schema must point back to `trashbot.field_evidence_real_material_followup_escalation_status.v1` and the evidence boundary must remain `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate`.

The alias is metadata-only and fail-closed:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `metadata_only=true`

Allowed Robot-visible fields are limited to sanitized field follow-up metadata: `safe_evidence_ref`, `status`, `followup_status`, `material_group`, `field_owner`, `due_status`, `blocked_reason`, `next_required_evidence`, `escalation_level`, `rerun_status_summary`, `source_review_handoff_status`, `owner_handoff`, `material_groups`, `robot_diagnostics_summary`, `safe_copy`, `safe_phone_copy`, and `not_proven`.

This alias is scoped to field-evidence follow-up, including PR review context such as `PRRT_kwDOSWB9286CJ3tX` and comment/material reference `3269642220`, but it does not resolve PR review state. It must not expose raw artifacts, raw review-handoff materials, raw diagnostics, unsafe material, mismatched `evidence_ref`, success/control claims, ROS topic names, `/cmd_vel`, serial/UART or WAVE ROVER details, credentials, DB/queue URLs, OSS secrets, local paths, checksum values, tracebacks, ACK/cursor/control routes, HIL/pass wording, field-pass wording, delivery result success, or complete artifact bodies. Missing canonical summary, unsupported schema or boundary, enabled action flag, unsafe copy, raw artifact/review marker, local path, checksum, credential, DB/queue URL, traceback marker, ACK/cursor route, HIL/pass wording, or hardware/control wording keeps the summary blocked/not_proven and leaves task_orchestrator, Start, Confirm Dropoff, Cancel, ACK, cursor, Nav2, HIL, dropoff/cancel completion, delivery result, and primary robot actions disabled.
