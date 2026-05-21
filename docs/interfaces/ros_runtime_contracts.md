# ROS Runtime Contracts

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
