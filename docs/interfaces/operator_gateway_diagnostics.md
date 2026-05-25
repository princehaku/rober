# Operator Gateway Diagnostics

## 2026-05-25 structure refactor boundary

`operator_gateway_diagnostics.py` and `remote_cloud_relay.py` now keep the
mobile/web diagnostics surface as a compatibility facade while the internal
logic is split into named helpers for:

- phone-safe lifecycle summary construction;
- historical alias expansion for `/api/status` and `/api/diagnostics`;
- cloud-hosted mobile web state normalization;
- fail-closed cleanup of stale/raw diagnostic sibling fields before canonical
  Robot diagnostics aliases are emitted.

This is a structure-only refactor. The public endpoints, schema names and
Robot-safe alias keys stay compatible. The required false-state boundary also
stays unchanged: `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

The refactor must not be interpreted as true phone/browser proof, public
HTTPS/TLS proof, 4G/SIM proof, OSS/CDN live proof, HIL, route/elevator field
pass, verified terminal delivery/dropoff/cancel result, or delivery success.
Start Delivery, Confirm Dropoff and Cancel remain disabled unless a separate
runtime control contract explicitly authorizes them.

## robot_diagnostics_cloud_command_lifecycle_audit_export_summary

Robot/API exposes `cloud_command_lifecycle_audit_export`,
`cloud_command_lifecycle_audit_export_summary`, and
`robot_diagnostics_cloud_command_lifecycle_audit_export_summary` on
`/api/status` and `/api/diagnostics` for mobile/web and support handoff to
copy a phone-safe command lifecycle audit.

- API schema: `trashbot.cloud_command_lifecycle_audit_export_summary.v1`
- Capability: `cloud_command_lifecycle_audit_export`
- Evidence boundary:
  `software_proof_docker_cloud_command_lifecycle_audit_export_gate`
- Required safe fields: safe `command_id`, safe `evidence_ref`,
  `lifecycle_timeline`, `terminal_result_status`, `next_required_evidence`,
  and `copy_export_text`

The summary is metadata-only and read-only. It binds one safe `command_id` to
one safe `evidence_ref`, then lists lifecycle stages for command identity,
queue state, robot poll/status state, ACK lookup or accepted/processing state,
and the still-missing verified terminal result.

Missing safe `command_id`, missing safe `evidence_ref`, conflicting command
IDs across lifecycle sources, unsafe copy, raw paths, credentials, URLs,
tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
success wording, `delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

The required false-state boundary is `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. It must not enable Start Delivery, Confirm
Dropoff, Cancel, ACK posting, cursor updates, persistence updates, command
replay/resubmit, terminal ACK, Nav2, route execution, WAVE ROVER, HIL,
verified delivery/dropoff/cancel result, PR #5 reviewer resolution, or delivery
success.

## robot_diagnostics_cloud_command_lifecycle_replay_drill_summary

Robot/API exposes `cloud_command_lifecycle_replay_drill`,
`cloud_command_lifecycle_replay_drill_summary`, and
`robot_diagnostics_cloud_command_lifecycle_replay_drill_summary` on
`/api/status` and `/api/diagnostics` for support to rehearse the already
sanitized lifecycle audit as a read-only drill.

- API schema: `trashbot.cloud_command_lifecycle_replay_drill_summary.v1`
- Source schema: `trashbot.cloud_command_lifecycle_audit_export_summary.v1`
- Capability: `cloud_command_lifecycle_replay_drill`
- Evidence boundary:
  `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`
- Required safe fields: safe `command_id`, safe `evidence_ref`,
  `replay_timeline`, `ack_semantics`, `terminal_result_status`,
  `next_required_evidence`, and `support_drill_copy`

The drill is derived only from `cloud_command_lifecycle_audit_export` or
`robot_diagnostics_cloud_command_lifecycle_audit_export_summary`. It preserves
the ordered lifecycle timeline, ACK meaning
`accepted_processing_only_not_delivery_success`, terminal result pending
status, next required evidence, and support drill copy. It is a support drill
artifact, not a command replay, ACK post, cursor update, persistence update, or
robot control route.

Missing safe IDs, conflicting command/evidence refs, unsafe copy, raw paths,
credentials, secret URLs, tracebacks, ROS topics, `/cmd_vel`, serial/UART
details, WAVE ROVER details, complete artifacts, checksums, success wording,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

The required false-state boundary is `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. It must not enable Start Delivery, Confirm
Dropoff, Cancel, command replay/resubmit, ACK posting, cursor mutation,
persistence mutation, Nav2, route execution, WAVE ROVER, HIL, verified
delivery/dropoff/cancel result, real external cloud proof, or delivery success.

## robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary

Robot/API exposes `cloud_command_lifecycle_replay_acceptance_packet`,
`cloud_command_lifecycle_replay_acceptance_packet_summary`, and
`robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` on
`/api/status` and `/api/diagnostics` for support / field-owner acceptance
review of the already sanitized replay drill.

- API schema:
  `trashbot.cloud_command_lifecycle_replay_acceptance_packet_summary.v1`
- Source schema: `trashbot.cloud_command_lifecycle_replay_drill_summary.v1`
- Capability: `cloud_command_lifecycle_replay_acceptance_packet`
- Evidence boundary:
  `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
- Required safe fields: safe `command_id`, safe `evidence_ref`,
  `replay_timeline`, `ack_semantics`, `terminal_result_status`,
  `acceptance_packet_status`, `owner_handoff`, `next_required_evidence`, and
  `support_acceptance_copy`

The acceptance packet is derived only from `cloud_command_lifecycle_replay_drill`
or `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary`. It
preserves the ordered lifecycle timeline, ACK meaning
`accepted_processing_only_not_delivery_success`, pending terminal result,
owner handoff, next required evidence, and support-safe copy. It is a review
packet, not a command replay, ACK post, cursor update, persistence update,
material upload, review action, GitHub action, or robot control route.

Missing safe IDs, conflicting command/evidence refs, unsafe copy, raw paths,
credentials, secret URLs, tracebacks, ROS topics, `/cmd_vel`, serial/UART
details, WAVE ROVER details, complete artifacts, checksums, ACK payloads,
cursors, success wording, `delivery_success=true`, `primary_actions_enabled=true`,
or `safe_to_control=true` must fail closed as blocked/not_proven.

The required false-state boundary is `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. It must not enable Start Delivery, Confirm
Dropoff, Cancel, command replay/resubmit, ACK posting, cursor mutation,
persistence mutation, material upload, review action, GitHub action, Nav2,
route execution, WAVE ROVER, UART, HIL, verified delivery/dropoff/cancel
result, PR #5 resolution, real external cloud proof, or delivery success.

## cloud_support_handoff_safe_export

Robot/API exposes `cloud_support_handoff_safe_export` on `/api/status` and
`/api/diagnostics` for mobile/web to consume a read-only cloud degraded-state
support export package.

- Source objects: sanitized `phone_readiness`, `phone_support_bundle`, and
  diagnostics summaries
- API schema: `trashbot.cloud_support_handoff_safe_export_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_cloud_support_handoff_safe_export_summary.v1`
- Evidence boundary:
  `software_proof_docker_cloud_support_handoff_safe_export_gate`

The export is metadata-only. It may expose sanitized `degradation_state`, safe
copy, support bundle id, support level, next action, short `export_refs`, and
OKR/review context for `Objective 5 ~68%`, `Objective 1 ~81%`, PR thread
`PRRT_kwDOSWB9286CJ3tX`, and comment `3269642220`.

The required false-state boundary is `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. The alias must also keep ACK posting, cursor
updates, Nav2 triggering, and HIL pass false.

Unsafe copy, raw diagnostics, raw cloud bodies, credentials, URLs, local paths,
tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
success wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed as blocked/not_proven.

This export must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, route
execution, WAVE ROVER, HIL, Objective 5 external proof, true phone/browser
proof, route/elevator field pass, PR #5 reviewer resolution, or delivery
success.

## robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary

Robot diagnostics exposes
`robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary` as the safe
alias for `GET /robots/{robot_id}/commands/{command_id}/ack` returning
`ack_not_found` while the robot has not processed that command.

- Source state: `remote_readiness.degradation_state=ack_lookup_pending`
- Robot alias schema:
  `trashbot.robot_diagnostics_cloud_ack_lookup_pending_status_guard_summary.v1`
- Capability: `cloud_ack_lookup_pending_status_guard`
- Evidence boundary:
  `software_proof_docker_cloud_ack_lookup_pending_status_guard`

The alias is metadata-only and read-only. It may expose sanitized
`degradation_state=ack_lookup_pending`, phone-safe copy,
`retry_hint=continue_polling_or_contact_support`,
`ack_semantics=ack_lookup_pending_not_delivery_success`,
`source=software_proof`, `not_proven`, `remote_ready=false`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Unsafe copy, raw cloud bodies, bearer token, Authorization header, raw JSON,
raw command path, traceback, ROS topic, `/cmd_vel`, serial/UART details,
WAVE ROVER details, success wording, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` must fail closed as
blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK cursor
fetch, cursor updates, persistence updates, terminal ACK, commands, Nav2, route
execution, WAVE ROVER, HIL, Objective 5 external proof, true phone/browser
proof, route/elevator field pass, or delivery success.

## robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary

Robot diagnostics exposes
`robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary` as the safe
alias for an ACK that is already accepted/processing while no terminal result,
delivery result, dropoff completion, or cancel completion exists yet.

- Source state: `remote_readiness.degradation_state=ack_accepted_result_pending`
- Robot alias schema:
  `trashbot.robot_diagnostics_cloud_ack_accepted_result_pending_guard_summary.v1`
- Capability: `cloud_ack_accepted_result_pending_guard`
- Evidence boundary:
  `software_proof_docker_cloud_ack_accepted_result_pending_guard`

The alias is metadata-only and read-only. It may expose sanitized
`degradation_state=ack_accepted_result_pending`, phone-safe copy,
`retry_hint=wait_for_delivery_result_or_contact_support`,
`ack_semantics=accepted_processing_only_not_delivery_success`,
`source=software_proof`, `not_proven`, `remote_ready=false`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Unsafe copy, raw cloud bodies, bearer token, Authorization header, raw JSON,
raw command path, traceback, ROS topic, `/cmd_vel`, serial/UART details,
WAVE ROVER details, success wording, terminal-result wording,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK cursor
fetch, cursor updates, persistence updates, terminal ACK, commands, Nav2, route
execution, WAVE ROVER, HIL, Objective 5 external proof, true phone/browser
proof, route/elevator field pass, dropoff completion, cancel completion,
delivery result, or delivery success.

## robot_diagnostics_cloud_terminal_result_verification_guard_summary

Robot diagnostics exposes
`robot_diagnostics_cloud_terminal_result_verification_guard_summary` as the safe
alias for ACK payloads that contain `delivery_result`, `terminal_result`,
`dropoff_completion`, or `cancel_completion` fields whose values are still
non-terminal, such as `pending`, `accepted`, or `processing`.
`unknown` is also non-terminal when the field exists but verified result
evidence has not arrived.

- Source state: `remote_readiness.degradation_state=terminal_result_pending`
- Robot alias schema:
  `trashbot.robot_diagnostics_cloud_terminal_result_verification_guard_summary.v1`
- Capability: `cloud_terminal_result_verification_guard`
- Evidence boundary:
  `software_proof_docker_cloud_terminal_result_verification_guard`

The alias is metadata-only and read-only. It may expose sanitized
`degradation_state=terminal_result_pending`, phone-safe copy,
`retry_hint=wait_for_verified_terminal_result_or_contact_support`,
`ack_semantics=accepted_processing_only_not_delivery_success`,
`source=software_proof`, `not_proven`, `remote_ready=false`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Unsafe copy, raw cloud bodies, bearer token, Authorization header, raw JSON,
raw command path, traceback, ROS topic, `/cmd_vel`, serial/UART details,
WAVE ROVER details, success wording, verified terminal-result wording,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK cursor
fetch, cursor updates, persistence updates, terminal ACK, commands, Nav2, route
execution, WAVE ROVER, HIL, Objective 5 external proof, true phone/browser
proof, route/elevator field pass, dropoff completion, cancel completion,
verified delivery result, or delivery success.

## robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary

Robot diagnostics exposes
`robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary` as the safe
alias for cloud cancel while collect goal acceptance is still pending.

- Source state: `remote_readiness.degradation_state=cancel_pending_goal_acceptance`
- Robot alias schema:
  `trashbot.robot_diagnostics_cloud_cancel_pending_command_safety_guard_summary.v1`
- Capability: `cloud_cancel_pending_command_safety_guard`
- Evidence boundary:
  `software_proof_docker_cloud_cancel_pending_command_safety_guard`

The alias is metadata-only and read-only. It may expose sanitized
`degradation_state=cancel_pending_goal_acceptance`, phone-safe copy,
`retry_hint=wait_for_goal_acceptance`,
`ack_semantics=cancel_pending_not_delivery_success`,
`source=software_proof`, `not_proven`, `remote_ready=false`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Unsafe copy, raw cloud bodies, bearer token, Authorization header, raw JSON,
traceback, ROS topic, `/cmd_vel`, serial/UART details, WAVE ROVER details,
success wording, `delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor
updates, persistence updates, terminal ACK, commands, Nav2, route execution,
real goal acceptance, cancel completion, WAVE ROVER, HIL, Objective 5 external
proof, true phone/browser proof, route/elevator field pass, or delivery success.

## robot_diagnostics_cloud_poll_backoff_rate_limit_guard_summary

Robot diagnostics exposes
`robot_diagnostics_cloud_poll_backoff_rate_limit_guard_summary` as the safe
alias for O5 poll backoff / rate-limit visibility.

- Source state: `remote_readiness.degradation_state=cloud_poll_backoff`
- Robot alias schema:
  `trashbot.cloud_poll_backoff_rate_limit_guard_summary.v1`
- Evidence boundary:
  `software_proof_docker_cloud_poll_backoff_rate_limit_guard`

The alias is metadata-only and read-only. It may expose sanitized
`degradation_state=cloud_poll_backoff`, phone-safe copy,
`retry_hint=wait_for_backoff_window`, optional redacted `backoff_until` or
`backoff_duration_sec`, `source=software_proof`, `not_proven`,
`remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

This state must not weaken more specific O5 states: `auth_failed`,
`media_degraded`, `cloud_unreachable`, `malformed_response`,
`command_expired`, `command_pending`, `command_duplicate_deduped`,
`command_id_conflict`, and `command_sequence_regression` keep their own proof
boundaries and recovery hints.

Unsafe copy, raw cloud bodies, raw base URL, bearer token, Authorization header,
local state path, traceback, ROS topic, `/cmd_vel`, serial/UART details,
WAVE ROVER details, success wording, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` must fail closed as
blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor
updates, persistence updates, terminal ACK, commands, Nav2, route execution,
WAVE ROVER, HIL, Objective 5 external proof, true phone/browser proof,
production DB/queue, OSS/CDN live traffic, PR #5 reviewer resolution, or
delivery success.

## robot_diagnostics_task_terminal_completion_mainline_summary

Robot diagnostics exposes
`robot_diagnostics_task_terminal_completion_mainline_summary` as a safe alias
for Robot task-record terminal-action mainline metadata.

- Source schema: `trashbot.task_terminal_completion_mainline.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_task_terminal_completion_mainline_summary.v1`
- Evidence boundary:
  `software_proof_docker_task_terminal_completion_mainline_gate`

The alias is metadata-only and read-only. It may expose sanitized
`terminal_action`, `terminal_status`, safe `evidence_ref`, operator
confirmation status, missing required materials, next required evidence,
failure reason, route-progress metadata, `software_proof`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

Missing summary, unsupported schema or boundary, same `evidence_ref` mismatch,
unsafe copy, raw artifact fields, ACK/cursor/command/control fields, success
wording, `delivery_success=true`, or `primary_actions_enabled=true` must fail
closed as blocked/not_proven. Missing real field materials must keep
`dropoff_completion_proven=false` and `cancel_completion_proven=false`.

This alias must not read hardware, serial/UART, ROS graph, raw artifacts,
cloud resources, or mobile browser state. It must not enable Start Delivery,
Confirm Dropoff, Cancel, ACK, cursor updates, persistence updates, terminal
ACK, commands, Nav2, WAVE ROVER, HIL, material collection, Objective 5
external proof, dropoff/cancel completion, or delivery success.

## robot_diagnostics_task_terminal_field_material_intake_summary

Robot diagnostics exposes
`robot_diagnostics_task_terminal_field_material_intake_summary` as a safe alias
for the task-terminal field-material intake entrypoint.

- Source artifact schema: `trashbot.task_terminal_field_material_intake.v1`
- Source summary schema:
  `trashbot.task_terminal_field_material_intake_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_task_terminal_field_material_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_task_terminal_field_material_intake_gate`

The alias is metadata-only and read-only. It may expose sanitized
`status`, `source=software_proof`, safe `evidence_ref`, accepted safe refs,
missing materials, next required evidence, phone-safe copy, `software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Missing payload, unsupported schema or boundary, unsafe copy, raw artifact or
local-path fields, checksums, credentials, success wording, field-pass
wording, HIL/pass wording, Objective 5 external proof wording, control grants,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not read raw artifacts, hardware, serial/UART, ROS graph,
cloud resources, mobile browser state, ACK payloads, command envelopes, or
completion cursors. It must not enable Start Delivery, Confirm Dropoff,
Cancel, ACK, cursor updates, persistence updates, terminal ACK, commands,
Nav2, route execution, WAVE ROVER, HIL, material collection, Objective 5
external proof, dropoff/cancel completion, route/elevator field pass, or
delivery success.

## robot_diagnostics_task_terminal_field_material_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_task_terminal_field_material_review_decision_summary` as a
safe alias for task-terminal field-material review-decision metadata.

- Source artifact schema:
  `trashbot.task_terminal_field_material_review_decision.v1`
- Source summary schema:
  `trashbot.task_terminal_field_material_review_decision_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_task_terminal_field_material_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_task_terminal_field_material_review_decision_gate`

The alias is metadata-only and read-only. It may expose sanitized
`status`, `source=software_proof`, review decision, safe `evidence_ref`,
accepted materials, missing materials, rejected materials, blocked materials,
`owner_handoff`, `next_required_evidence`, `rerun_guidance`, phone-safe copy,
`software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Missing payload, unsupported schema or boundary, unsafe copy, raw artifact or
local-path fields, checksums, credentials, success wording, field-pass
wording, HIL/pass wording, Objective 5 external proof wording, control grants,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not read raw artifacts, hardware, serial/UART, ROS graph,
cloud resources, mobile browser state, ACK payloads, command envelopes, or
completion cursors. It must not enable Start Delivery, Confirm Dropoff,
Cancel, ACK, cursor updates, persistence updates, terminal ACK, commands,
Nav2, route execution, WAVE ROVER, HIL, material collection, Objective 5
external proof, dropoff/cancel completion, route/elevator field pass, PR #4
field pass, PR #5 hardware-material closure, or delivery success. It supports
Objective 2 and Objective 3 evidence hygiene only as `software_proof` /
`not_proven` reviewability.

## robot_diagnostics_pr5_vendor_source_review_packet_summary

Robot diagnostics exposes
`robot_diagnostics_pr5_vendor_source_review_packet_summary` as a safe alias
for Hardware's PR #5 vendor/source review packet summary.

- Source artifact schema:
  `trashbot.pr5_vendor_source_review_packet.v1`
- Source summary schema:
  `trashbot.pr5_vendor_source_review_packet_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_pr5_vendor_source_review_packet_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_vendor_source_review_packet_gate`

The alias is metadata-only and read-only. It may expose only sanitized
`thread_id`, `source=software_proof`, `proof_boundary`,
`vendor_source_boundary`, missing materials, next required evidence, safe copy,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
The PR #5 unresolved thread is `PRRT_kwDOSWB9286CJ3tX`; the current packet
must remain `not_proven` until real 2D LiDAR / ToF SKU, vendor/source,
receipt, procurement, installation, wiring, power, calibration, and HIL-entry
materials are independently supplied and reviewed.

Missing summary, unreadable input, unsupported schema or boundary, unsafe
copy, raw artifact body fields, raw review body, credentials, local paths,
serial/UART paths, baudrate, ROS topics, `/cmd_vel`, ACK/cursor/command
fields, success wording, HIL/pass wording, field-pass wording,
`delivery_success=true`, or `primary_actions_enabled=true` must fail closed as
blocked/not_proven.

This alias must not read raw artifacts, hardware, serial/UART, ROS graph,
cloud resources, mobile browser state, ACK payloads, command envelopes, or
completion cursors. It must not enable Start Delivery, Confirm Dropoff,
Cancel, ACK, cursor updates, persistence updates, terminal ACK, commands,
Nav2, WAVE ROVER, HIL, material collection, Objective 5 external proof,
dropoff/cancel completion, route/elevator field pass, PR #5 material closure,
or delivery success.

## robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary

Robot diagnostics exposes
`robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary` as a safe
alias for Hardware's PR #5 vendor/source review reply-dispatch summary.

- Source artifact schema:
  `trashbot.pr5_vendor_source_review_reply_dispatch.v1`
- Source summary schema:
  `trashbot.pr5_vendor_source_review_reply_dispatch_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_pr5_vendor_source_review_reply_dispatch_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_vendor_source_review_reply_dispatch_gate`

The alias is metadata-only and read-only. It may expose only sanitized
`thread_id=PRRT_kwDOSWB9286CJ3tX`, `source=software_proof`, `proof_boundary`,
reply-dispatch status, missing materials, next required evidence, owner
handoff, safe copy, `not_proven`, `hardware_material_pending`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Missing sanitized summary, unreadable input, unsupported schema or boundary,
raw body fields, credentials, tokens, serial/UART details, ROS/control fields,
ACK/cursor/command fields, success wording, HIL/pass wording, field-pass
wording, `delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not read raw reply bodies, raw artifacts, hardware,
serial/UART, ROS graph, cloud resources, or mobile browser state. It must not
enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor updates,
persistence updates, terminal ACK, commands, Nav2, WAVE ROVER, HIL, material
collection, Objective 5 external proof, dropoff/cancel completion,
route/elevator field pass, PR #5 material closure, or delivery success.

## robot_diagnostics_hardware_real_material_escalation_request_summary

Robot diagnostics exposes
`robot_diagnostics_hardware_real_material_escalation_request_summary` as a
safe alias for Hardware's real-material escalation request summary.

- Source artifact schema:
  `trashbot.hardware_real_material_escalation_request.v1`
- Source summary schema:
  `trashbot.hardware_real_material_escalation_request_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_hardware_real_material_escalation_request_summary.v1`
- Evidence boundary:
  `software_proof_docker_hardware_real_material_escalation_request_gate`

The alias is metadata-only and read-only. It may expose sanitized request
status, safe `evidence_ref`, missing real materials, required real materials,
next required evidence, owner handoff, safe copy, `software_proof`,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
The expected missing-material families include WAVE ROVER, UART, HIL,
PR #5 2D LiDAR / ToF procurement/source/receipt, installation, wiring, power,
calibration, and HIL-entry materials.

Missing summary, unreadable input, unsupported schema or boundary, unsafe
copy, raw artifact fields, raw material body, ROS topics, `/cmd_vel`,
serial/UART device paths, baudrate, WAVE ROVER raw details, credentials, local
paths, checksums, tracebacks, ACK/cursor/command/control fields, success
wording, `delivery_success=true`, or `primary_actions_enabled=true` must fail
closed as blocked/not_proven.

This alias must not read raw artifacts, serial devices, hardware devices, or
the ROS graph. It must not enable Start Delivery, Confirm Dropoff, Cancel,
ACK, cursor updates, persistence updates, terminal ACK, commands, Nav2,
WAVE ROVER, HIL, material collection, production readiness, dropoff/cancel
completion, or delivery success. It also does not prove real WAVE ROVER/UART,
real 2D LiDAR / ToF, real PR #4 route/elevator field pass, real phone/browser
validation, Objective 5 external proof, or any hardware/HIL result.

## robot_diagnostics_real_material_readiness_board_summary

Robot diagnostics exposes
`robot_diagnostics_real_material_readiness_board_summary` as a safe alias for
the PC/evidence real-material readiness board.

- Source artifact schema: `trashbot.real_material_readiness_board.v1`
- Source summary schema: `trashbot.real_material_readiness_board_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_real_material_readiness_board_summary.v1`
- Evidence boundary:
  `software_proof_docker_real_material_readiness_board_gate`

The alias is metadata-only, routing-only, and read-only. It may expose
sanitized `material_groups`, safe `evidence_ref`, owner handoff,
`next_required_evidence`, safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Missing board input, unreadable JSON, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
copy, raw artifact fields, credentials, local paths, raw ROS topics,
`/cmd_vel`, serial/UART details, ACK/cursor/command/control fields, success
wording, `delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not read raw artifacts, serial devices, hardware devices, the
ROS graph, cloud resources, or mobile browser state. It must not enable Start
Delivery, Confirm Dropoff, Cancel, ACK, cursor updates, persistence updates,
terminal ACK, commands, Nav2, WAVE ROVER, HIL, material collection, Objective
5 external proof, production readiness, dropoff/cancel completion, or delivery
success. It is only a routing surface for missing real-material evidence across
Objective 5 external readiness, Objective 1 / PR #5 hardware materials, PR #4
route/elevator materials, and Objective 4 real phone/browser materials.

## robot_diagnostics_real_material_evidence_intake_summary

Robot diagnostics exposes
`robot_diagnostics_real_material_evidence_intake_summary` as a safe alias for
real-material evidence intake.

- Source artifact schema: `trashbot.real_material_evidence_intake.v1`
- Source summary schema: `trashbot.real_material_evidence_intake_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_real_material_evidence_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_real_material_evidence_intake_gate`

The alias is metadata-only and read-only. It may expose only sanitized intake
status, safe `evidence_ref`, accepted material labels, missing real materials,
rejected material labels, next required evidence, owner handoff, safe copy,
and the safe alias `real_material_manifest_template`. That template alias may
only expose sanitized `manifest_template`, `template_groups`, and
`required_item_templates` entries containing phone-safe template keys:
schema/status/boundary/source/not_proven, `material_group`, required item
names, `summary_hint`, `material_ref_hint`, `owner_handoff`, `objective_ref`,
`next_action`, `same_evidence_ref_required=true`, safe `evidence_ref`, and
safe template `evidence_ref`. The alias must continue to expose
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Missing summary, unreadable input, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
`evidence_ref`, unsafe copy, unsafe manifest template keys, raw artifact
fields, raw JSON, credentials, local paths, checksums, raw ROS topics,
`/cmd_vel`, serial/UART details, success/control claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` must fail closed as
blocked/not_proven.

This alias must not read raw manifests, serial devices, hardware devices, the
ROS graph, cloud resources, mobile browser state, credentials, checksums, or
raw JSON. It must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER,
HIL, material collection, production readiness, real phone/browser proof,
public cloud proof, dropoff/cancel completion, or delivery success.

## robot_diagnostics_verified_terminal_result_material_intake_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_intake_summary` as a safe
alias for verified terminal-result material intake.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_intake.v1`
- Source summary schema and Robot alias schema:
  `trashbot.verified_terminal_result_material_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_intake_gate`

The alias is metadata-only and read-only. It may consume
`verified_terminal_result_material_intake`,
`verified_terminal_result_material_intake_summary`, the Robot alias, or a
compatible nested diagnostics/status summary. It may expose only sanitized
intake status, safe `evidence_ref`, accepted/missing/rejected material labels,
next required evidence, owner handoff, safe copy, `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Missing summary, unreadable input, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
`evidence_ref`, unsafe copy, raw artifact fields, raw JSON, credentials, local
paths, checksums, ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation
hints, replay/resubmit hints, serial/UART details, success/control claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias is not terminal delivery proof. It must not enable Start Delivery,
Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, dropoff/cancel completion, or delivery success.

## robot_diagnostics_verified_terminal_result_material_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_review_decision_summary`
as a safe alias for verified terminal-result material review decision.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_review_decision.v1`
- Source summary schema and Robot alias schema:
  `trashbot.verified_terminal_result_material_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_review_decision_gate`

The alias is metadata-only and read-only. It may consume
`verified_terminal_result_material_review_decision`,
`verified_terminal_result_material_review_decision_summary`, the Robot alias,
or a compatible nested diagnostics/status summary. It may expose only sanitized
review decision, source intake status, safe `evidence_ref`, safe `command_id`,
terminal result type, decision reasons, material status summary,
blocked/rejected reason, next required evidence, owner handoff, safe copy,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Missing summary, unreadable input, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
`evidence_ref`, unsafe copy, raw artifact fields, raw JSON, credentials, local
paths, checksums, ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation
hints, replay/resubmit hints, serial/UART details, success/control claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias is not terminal delivery proof and `accepted_for_review` is not
delivery success. It must not enable Start Delivery, Confirm Dropoff, Cancel,
ACK mutation, cursor mutation, replay, resubmit, robot control, commands, Nav2,
WAVE ROVER, HIL, material collection, production readiness, dropoff/cancel
completion, or delivery success.

## robot_diagnostics_verified_terminal_result_material_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
as the safe alias for `verified_terminal_result_material_review_handoff`.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_review_handoff.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_review_handoff_gate`

The alias is metadata-only and read-only. It may consume
`verified_terminal_result_material_review_handoff`,
`verified_terminal_result_material_review_handoff_summary`, the Robot alias,
or a compatible nested diagnostics/status summary. A raw artifact wrapper is
accepted only when it contains the sanitized summary.

Allowed handoff statuses are `ready_for_owner_handoff`,
`needs_material_backfill`, `rejected`, and `blocked`. These are owner-handoff
metadata states only; they are not delivery success, dropoff/cancel completion,
readiness, or permission to operate the robot.

Allowed fields are limited to source review decision summary, handoff status,
safe `evidence_ref`, safe `command_id`, terminal result type, material status
summary, accepted material refs, missing required materials, rejected material
refs, owner handoff, next required evidence, blocked reason, safe copy,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

The alias must fail closed for missing sanitized summary, unreadable input,
unsupported schema or evidence boundary, `source` other than `software_proof`,
`overall_status` other than `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw artifact fields, raw diagnostics fetch fields, credentials, local paths,
checksums, ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation hints,
replay/resubmit hints, serial/UART details, WAVE ROVER details,
success/control claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, dropoff/cancel completion, cancel completion, delivery result, or
delivery success.

## robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary`
as the safe alias for
`verified_terminal_result_material_followup_escalation_status`.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`

The alias is metadata-only and read-only. It may consume the sanitized summary,
the Robot alias, or a compatible nested diagnostics/status summary. A raw
artifact wrapper is accepted only when it contains the sanitized follow-up
summary; Robot output strips raw sibling keys and re-emits only the safe alias.

Allowed follow-up statuses are
`escalated_for_terminal_result_material_followup_not_proven`,
`waiting_for_terminal_result_material_backfill_not_proven`,
`needs_support_owner_reassignment_not_proven`,
`rejected_unsafe_terminal_result_followup_not_proven`, and
`blocked_missing_terminal_result_review_handoff_not_proven`. These are
material follow-up states only; they are not reviewer resolution, delivery
success, dropoff/cancel completion, HIL pass, readiness, or permission to
operate the robot.

Allowed fields are limited to source handoff status, follow-up status, safe
`evidence_ref`, safe `command_id`, terminal result type, assigned owner,
support owner, reviewer route, required material backfill, escalation reason,
blocked reason, next required evidence, safe copy, `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The alias must fail closed for missing sanitized summary, unreadable input,
unsupported schema or evidence boundary, `source` other than `software_proof`,
`overall_status` other than `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw source, raw artifact, complete JSON, credentials, local paths, checksums,
ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation hints,
replay/resubmit hints, serial/UART details, WAVE ROVER details, hardware raw
details, reviewer-resolution claims, success/completion claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true`.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, dropoff/cancel completion, terminal delivery
result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_intake`.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_intake.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`

The alias is metadata-only and read-only. It may consume the sanitized summary,
the Robot alias, or a compatible nested diagnostics/status summary. A raw
artifact wrapper is accepted only when it contains the sanitized owner-response
intake summary; Robot output strips raw sibling keys and re-emits only the safe
alias.

Allowed intake statuses are `accepted_not_proven`, `missing_not_proven`,
`rejected_not_proven`, `blocked_not_proven`,
`accepted_for_later_review_not_proven`, and
`blocked_missing_terminal_result_followup_not_proven`. `accepted` material only
means the response can enter a later review queue. It is not reviewer
resolution, PR #5 resolution, delivery success, dropoff/cancel completion, HIL
pass, readiness, or permission to operate the robot.

Allowed fields are limited to owner-response status, safe `evidence_ref`, safe
`command_id`, terminal result type, source follow-up status, accepted/missing/
rejected/unsafe material summaries, next required evidence, operator support
handoff, safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The alias must fail closed for missing sanitized summary, unreadable input,
unsupported schema or evidence boundary, `source` other than `software_proof`,
`overall_status` other than `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw source, raw artifact, complete JSON, credentials, local paths, checksums,
ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation hints,
collect/dropoff/cancel hints, replay/resubmit hints, serial/UART details, WAVE
ROVER details, hardware raw details, reviewer-resolution or PR-resolution
claims, success/completion claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`.

PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved /
`hardware_material_pending`. This alias must not enable Start Delivery, Confirm
Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, raw
diagnostics fetch, robot control, commands, Nav2, WAVE ROVER, HIL, material
collection, production readiness, reviewer resolution, PR closeout,
dropoff/cancel completion, terminal delivery result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_review_decision`.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_review_decision.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`

The alias is metadata-only and read-only. It may consume the sanitized summary,
the Robot alias, or a compatible nested diagnostics/status summary. A raw
artifact wrapper is accepted only when it contains the sanitized owner-response
review-decision summary; Robot output strips raw sibling keys and re-emits only
the safe alias.

Allowed review statuses are `accepted_for_next_handoff_not_proven`,
`missing_not_proven`, `rejected_not_proven`, `blocked_not_proven`, and
`blocked_missing_terminal_result_owner_response_intake_not_proven`. Accepted
material only means the owner response can enter the next handoff. It is not
reviewer resolution, delivery success, dropoff/cancel completion, HIL pass,
readiness, or permission to operate the robot.

Allowed fields are limited to owner-response review decision, safe
`evidence_ref`, safe `command_id`, terminal result type, source owner-response
status, accepted/missing/rejected/unsafe material summaries, next required
evidence, owner handoff, safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The alias must fail closed for missing sanitized summary, unreadable input,
unsupported schema or evidence boundary, `source` other than `software_proof`,
`overall_status` other than `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw source, raw artifact, complete JSON, credentials, local paths, checksums,
ROS topics, `/cmd_vel`, ACK mutation hints, cursor mutation hints,
collect/dropoff/cancel hints, replay/resubmit hints, serial/UART details, WAVE
ROVER details, hardware raw details, handoff-authorization claims,
success/completion claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, handoff authorization, dropoff/cancel
completion, terminal delivery result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_review_handoff`. The alias is
derived from the sanitized
`verified_terminal_result_material_owner_response_review_decision` safe summary
when no explicit handoff summary is present.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_review_handoff.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- Upstream safe source:
  `trashbot.verified_terminal_result_material_owner_response_review_decision.v1`
  with
  `software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`

The alias is metadata-only and read-only. It preserves the upstream review
decision status, safe `evidence_ref`, safe `command_id`, terminal result type,
source owner-response status, accepted/missing/rejected/unsafe summaries, next
required evidence, owner handoff, support handoff, reviewer routing, safe copy,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and
`hardware_material_pending` remains true. The handoff alias does not prove real
terminal result material, O5 external proof, true phone/browser proof, public
HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover,
route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5 resolution, or
delivery success.

The alias must fail closed for missing sanitized summaries, unsupported
upstream schema or boundary, `source` other than `software_proof`,
`overall_status` other than `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw fields, credentials, local paths, ROS topics, `/cmd_vel`, serial/UART
details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success
wording, true control flags, PR-resolution claims, handoff authorization,
ACK/cursor mutation hints, collect/dropoff/cancel hints, or hardware proof
claims.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, PR resolution, handoff authorization,
dropoff/cancel completion, terminal delivery result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_reviewer_ack_intake`. The
alias first consumes the sanitized
`verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`
or its Robot-safe alias. If no ACK summary is present, it can derive a blocked
read-only state from the sanitized owner-response review handoff summary.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
- Upstream safe handoff source:
  `trashbot.verified_terminal_result_material_owner_response_review_handoff.v1`
  with
  `software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`

The alias is metadata-only and read-only. It preserves source handoff status,
safe `evidence_ref`, safe `command_id`, terminal result type, source review
decision status, source owner-response status, reviewer ACK status,
acknowledged-by/acknowledged-at metadata, ACK reasons,
accepted/missing/rejected/unsafe summaries, next required evidence, owner
handoff, support handoff, reviewer routing, safe copy, `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and
`hardware_material_pending`. The reviewer ACK intake alias does not prove real
terminal result material, O5 external proof, true phone/browser proof, public
HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover,
route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5 resolution,
reviewer resolution, or delivery success.

The alias must fail closed for missing sanitized summaries, unsupported source
schema or boundary, `source` other than `software_proof`, `overall_status`
other than `not_proven`, unsafe `evidence_ref`, unsafe copy, raw fields,
credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE
ROVER details, tracebacks, complete artifacts, checksums, success wording, true
control flags, PR-resolution claims, reviewer-resolution claims, handoff
authorization, ACK/cursor mutation hints, collect/dropoff/cancel hints, or
hardware proof claims.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, handoff authorization, dropoff/cancel
completion, terminal delivery result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_reviewer_ack_review_decision`.
The alias first consumes the sanitized review-decision summary or its
Robot-safe alias. If no decision summary is present, it can derive a blocked
read-only state from the sanitized reviewer ACK intake summary.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`
- Upstream safe intake source:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1`
  with
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`

The alias is metadata-only and read-only. It preserves source reviewer ACK
intake status, review decision, safe `evidence_ref`, safe `command_id`,
terminal result type, source handoff/review/owner-response status,
acknowledged-by/acknowledged-at metadata, decision reasons, ACK reasons,
accepted/missing/rejected/unsafe material summaries, reassignment reason, next
required evidence, owner handoff, support handoff, reviewer routing, safe copy,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and
`hardware_material_pending`. The reviewer ACK review-decision alias does not
prove real terminal result material, O5 external proof, true phone/browser
proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue,
worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5
resolution, reviewer resolution, review authorization, or delivery success.

The alias must fail closed for missing sanitized summaries, unsupported source
schema or boundary, `source` other than `software_proof`, `overall_status`
other than `not_proven`, unsafe `evidence_ref`, unsafe copy, raw fields,
credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE
ROVER details, tracebacks, complete artifacts, checksums, success wording, true
control flags, PR-resolution claims, reviewer-resolution claims, HIL wording,
review authorization, ACK/cursor mutation hints, collect/dropoff/cancel hints,
or hardware proof claims.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, review authorization, handoff authorization,
dropoff/cancel completion, terminal delivery result, or delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`.
The alias first consumes the sanitized review-handoff summary or its Robot-safe
alias. If no handoff summary is present, it can derive a blocked read-only state
from the sanitized reviewer ACK review-decision summary.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`
- Upstream safe review-decision source:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision.v1`
  with
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`

The alias is metadata-only and read-only. It preserves source reviewer ACK
review-decision status, handoff status, safe `evidence_ref`, safe `command_id`,
terminal result type, source reviewer ACK intake/handoff/review/owner-response
status, acknowledged-by/acknowledged-at metadata, handoff reasons, decision
reasons, ACK reasons, accepted/missing/rejected/unsafe material summaries,
reassignment reason, next required evidence, owner handoff, support handoff,
reviewer routing, safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and
`hardware_material_pending`. The reviewer ACK review-handoff alias does not
prove real terminal result material, O5 external proof, true phone/browser
proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue,
worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5
resolution, reviewer resolution, review authorization, handoff authorization,
or delivery success.

The alias must fail closed for missing sanitized summaries, unsupported source
schema or boundary, `source` other than `software_proof`, `overall_status`
other than `not_proven`, unsafe `evidence_ref`, unsafe copy, raw fields,
credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE
ROVER details, tracebacks, complete artifacts, checksums, success wording, true
control flags, PR-resolution claims, reviewer-resolution claims, HIL wording,
true phone/browser proof, review authorization, handoff authorization,
ACK/cursor mutation hints, collect/dropoff/cancel hints, or hardware proof
claims.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, review authorization, handoff authorization,
dropoff/cancel completion, terminal delivery result, phone/browser proof, or
delivery success.

## robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary

Robot diagnostics exposes
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`
as the safe alias for
`verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status`.
The alias consumes only the sanitized PC summary or its Robot-safe alias. If no
follow-up summary is present, it can derive a blocked read-only state from the
sanitized reviewer ACK review-handoff summary.

- Source artifact schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`
- Upstream safe handoff source:
  `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1`
  with
  `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`

The alias is metadata-only and read-only. It preserves source reviewer ACK
review-handoff status, follow-up status, safe `evidence_ref`, safe
`command_id`, terminal result type, acknowledged-by/acknowledged-at metadata,
due/overdue/escalated state, escalation reason, blocked reason,
owner/support/reviewer route, next required evidence, safe copy,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and
`hardware_material_pending`. The alias must express the owner/support/reviewer
route, due/overdue/escalated state, and next required evidence, but it does not
prove real terminal result material, O5 external proof, true phone/browser
proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue,
worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5
resolution, reviewer resolution, review authorization, handoff authorization,
or delivery success.

The alias must fail closed for missing sanitized summaries, unsupported source
schema or boundary, `source` other than `software_proof`, `overall_status`
other than `not_proven`, unsafe `evidence_ref`, unsafe copy, raw artifacts,
credentials, local paths, raw robot responses, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, ACK payloads, cursor values,
diagnostics fetch mutation hints, robot command hints, success wording, true
control flags, PR-resolution claims, reviewer-resolution claims, HIL wording,
field-pass wording, true phone/browser proof, review authorization, handoff
authorization, collect/dropoff/cancel hints, or hardware proof claims.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, raw diagnostics fetch, robot
control, robot commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, reviewer resolution, review authorization, handoff authorization,
dropoff/cancel completion, terminal delivery result, phone/browser proof, OKR
percentage lift, or delivery success.

## robot_diagnostics_real_material_followup_escalation_status_summary

Robot diagnostics exposes
`robot_diagnostics_real_material_followup_escalation_status_summary` as a safe
alias for real-material follow-up escalation status.

- Source artifact schema:
  `trashbot.real_material_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.real_material_followup_escalation_status_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_real_material_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_real_material_followup_escalation_status_gate`

The alias is metadata-only and read-only. It may expose only sanitized follow-up
status, safe `evidence_ref`, `material_group`, `field_owner`, `due_status`,
`blocked_reason`, `next_required_evidence`, `escalation_level`,
`rerun_command`, `rerun_status_summary`, `source_template_status`,
`source_intake_status`, `review_route`, `owner_handoff`, `material_groups`,
safe copy, `source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Missing summary, unreadable input, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
`evidence_ref`, unsafe copy, raw manifest/material fields, raw JSON,
credentials, local paths, checksums, ROS topics, serial/UART details,
success/control claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` must fail closed as
blocked/not_proven.

This alias must not read raw manifests, raw materials, serial devices, hardware
devices, the ROS graph, cloud resources, mobile browser state, credentials,
checksums, or raw JSON. It must not enable Start Delivery, Confirm Dropoff,
Cancel, ACK, cursor updates, persistence updates, terminal ACK, commands, Nav2,
WAVE ROVER, HIL, material collection, production readiness, real phone/browser
proof, public cloud proof, route/elevator field pass, dropoff/cancel
completion, or delivery success.

## robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary

Robot diagnostics exposes
`robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary`
as the safe alias for the field-evidence real-material follow-up escalation
status.

- Source artifact schema:
  `trashbot.field_evidence_real_material_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.field_evidence_real_material_followup_escalation_status_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_field_evidence_real_material_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate`

The alias is metadata-only and read-only. It may expose only sanitized follow-up
status, safe `evidence_ref`, `material_group`, `field_owner`, `due_status`,
`blocked_reason`, `next_required_evidence`, `escalation_level`,
`rerun_status_summary`, `source_review_handoff_status`, `owner_handoff`,
`material_groups`, safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The field-evidence variant is distinct from the older
`real_material_followup_escalation_status` alias. It can carry sanitized PR
context such as `PRRT_kwDOSWB9286CJ3tX` and material/comment reference
`3269642220`, but it does not mark review threads resolved and does not prove a
field rerun.

Missing summary, unreadable input, unsupported schema or evidence boundary,
`source` other than `software_proof`, status other than `not_proven`, unsafe
`evidence_ref`, unsafe copy, raw artifacts, raw review-handoff materials, raw
JSON, credentials, local paths, checksums, ROS topics, serial/UART details,
WAVE ROVER details, tracebacks, success/control claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` must fail closed as blocked/not_proven.

This alias must not read raw artifacts, serial devices, hardware devices, the
ROS graph, cloud resources, mobile browser state, credentials, checksums, or raw
JSON. It must not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor
updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER, HIL,
material collection, production readiness, real phone/browser proof, public
cloud proof, route/elevator field pass, dropoff/cancel completion, or delivery
success.

## robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary

`robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary`
is the Robot diagnostics safe alias for
`field_evidence_real_material_owner_ack_intake`. It consumes the canonical
summary from latest status or nested diagnostics, then republishes only
sanitized owner acknowledgement metadata for phone/Robot diagnostics.

- Source artifact schema:
  `trashbot.field_evidence_real_material_owner_ack_intake.v1`
- Source summary schema:
  `trashbot.field_evidence_real_material_owner_ack_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_real_material_owner_ack_intake_gate`

Required boundary states are `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Allowed fields are limited to safe owner acknowledgement status, safe
`evidence_ref`, owner/time labels, accepted/missing/rejected material summaries,
next required evidence, owner next steps, safe copy, and not-proven reasons.
The alias must not expose raw packets, local paths, credentials, ROS topics,
serial/UART/WAVE ROVER details, HIL/pass wording, checksums, complete artifacts,
success/control claims, or enabled action flags. Inputs with
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true` fail closed as blocked/not_proven.

## robot_diagnostics_wave_rover_hil_packet_collection_drill_summary

Robot diagnostics exposes `wave_rover_hil_packet_collection_drill`,
`wave_rover_hil_packet_collection_drill_summary`, and
`robot_diagnostics_wave_rover_hil_packet_collection_drill_summary` as the safe
alias for the PC-side WAVE ROVER HIL packet collection drill gate.

- Source artifact schema:
  `trashbot.wave_rover_hil_packet_collection_drill.v1`
- Source summary schema:
  `trashbot.wave_rover_hil_packet_collection_drill_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.wave_rover_hil_packet_collection_drill_summary.v1`
- Evidence boundary:
  `software_proof_docker_wave_rover_hil_packet_collection_drill_gate`

The local hardware source boundary for this alias is
`docs/vendor/VENDOR_INDEX.md`: WAVE ROVER upper/lower communication is UART
newline-delimited JSON, vendor Raspberry Pi examples are not Orange Pi launch
defaults, and Robot diagnostics must not open serial or send WAVE ROVER
commands.

Allowed fields are limited to collection drill status, safe `evidence_ref`,
required material templates, preflight checklist, collection sequence,
backfill commands, owner handoff, blocked reasons, evidence boundary,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

The alias is read-only metadata. Missing summary, unreadable input, unsupported
schema or boundary, missing `not_proven`, unsafe `evidence_ref`, unsafe copy,
raw artifacts, raw JSON, local paths, credentials, checksums, tracebacks, ROS
topics, `/cmd_vel`, serial/UART details, WAVE ROVER raw details, ACK/cursor
payloads, Nav2 route/runtime hints, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` must fail closed as
blocked/not_proven.

`ready_for_collection_drill_not_proven` only means the next real collection
drill has a sanitized checklist. It is not delivery success, real WAVE ROVER
proof, real UART feedback, real `feedback_T1001.log`, real odom/IMU/battery
material, HIL pass, Nav2 runtime proof, PR #5 reviewer resolution, Objective 5
external proof, or permission to start/confirm/cancel/ACK/replay/resubmit
robot commands.

## robot_diagnostics_field_evidence_material_resolution_intake_summary

`robot_diagnostics_field_evidence_material_resolution_intake_summary` is the
Robot diagnostics safe alias for `field_evidence_material_resolution_intake`.
It consumes only sanitized
`trashbot.field_evidence_material_resolution_intake_summary.v1` input, or a
compatible nested safe summary from latest status / diagnostics.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_intake.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_intake_gate`

Allowed fields are limited to decision values `accepted`, `missing`,
`rejected`, or `blocked`; safe `evidence_ref`; accepted/missing/rejected/blocked
summaries; next required evidence; owner handoff; evidence boundary; safe copy;
`source=software_proof`; `not_proven`; `delivery_success=false`;
`primary_actions_enabled=false`; and `safe_to_control=false`.

The alias is read-only metadata. It must not expose raw artifact bodies, local
paths, credentials, bearer tokens, ACK/cursor payloads, complete artifacts,
checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
tracebacks, success/pass/control copy, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`. Unsafe inputs fail
closed as blocked/not_proven.

`accepted` only means the safe resolution summary was accepted for later
Product review. It is not delivery success, a real field pass, a verified
terminal delivery/dropoff/cancel result, real phone/browser proof, public cloud
proof, PR #5 reviewer resolution, HIL, Nav2 runtime proof, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

## robot_diagnostics_field_evidence_material_resolution_review_decision_summary

`robot_diagnostics_field_evidence_material_resolution_review_decision_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_review_decision`. It consumes only sanitized
`trashbot.field_evidence_material_resolution_review_decision_summary.v1` input,
or a compatible nested safe summary from latest status / diagnostics.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_review_decision.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_review_decision_gate`

Allowed decision values are
`accepted_for_owner_review_not_proven`,
`needs_more_evidence_not_proven`,
`rejected_unsafe_resolution_not_proven`, and
`blocked_missing_resolution_intake_not_proven`.

Allowed fields are limited to decision, safe `evidence_ref`, reason, next
required evidence, owner review handoff, evidence boundary,
`source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

The alias is read-only metadata. It must not expose raw artifact bodies, local
paths, credentials, bearer tokens, ACK/cursor payloads, complete artifacts,
checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
tracebacks, success/pass/control copy, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`. Unsafe inputs fail
closed as blocked/not_proven.

`accepted_for_owner_review_not_proven` only means the safe resolution decision
can be reviewed by the owner. It is not delivery success, a real field result,
a verified terminal delivery/dropoff/cancel result, real phone/browser proof,
public cloud proof, PR #5 reviewer resolution, HIL, Nav2 runtime proof, or
permission to start/confirm/cancel/ACK/replay/resubmit robot commands.

## robot_diagnostics_field_evidence_material_resolution_review_handoff_summary

`robot_diagnostics_field_evidence_material_resolution_review_handoff_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_review_handoff`. It consumes only sanitized
`trashbot.field_evidence_material_resolution_review_handoff_summary.v1` input,
or a compatible nested safe summary from latest status / diagnostics. A raw
artifact wrapper is accepted only when it contains the sanitized summary.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_review_handoff.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_review_handoff_gate`

Allowed handoff statuses are `ready_for_owner_handoff_not_proven`,
`needs_more_evidence_not_proven`,
`blocked_missing_review_decision_not_proven`, and
`blocked_unsafe_handoff_not_proven`. These are handoff metadata states only;
they are not readiness, success, or permission to operate the robot.

Allowed fields are limited to safe `evidence_ref`, previous review decision
reference, previous review decision, accepted material refs, rejected material
refs, missing required materials, owner handoff role, owner next action, next
required real evidence, blocked categories for `external_cloud`,
`terminal_result`, `phone_browser`, `field_route_elevator`, `hardware_hil`, and
`pr5`, evidence boundary, `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The alias is read-only metadata. It must not expose raw artifact bodies, local
paths, credentials, bearer tokens, ACK/cursor payloads, complete artifacts,
checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
tracebacks, success/pass/control copy, readiness claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`. Unsafe inputs fail
closed as blocked/not_proven.

`ready_for_owner_handoff_not_proven` only means the owner has a sanitized
handoff package for collecting real evidence. It is not delivery success, a
real field result, a verified terminal delivery/dropoff/cancel result, real
phone/browser proof, public cloud proof, PR #5 reviewer resolution, HIL, Nav2
runtime proof, or permission to start/confirm/cancel/ACK/replay/resubmit robot
commands.

## robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary

`robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_followup_escalation_status`. It consumes
only the sanitized
`trashbot.field_evidence_material_resolution_followup_escalation_status_summary.v1`
PC summary, a wrapper that contains that safe summary, or compatible latest
status / diagnostics fallback metadata. It never reads or republishes raw
GitHub data, raw artifacts, or local material paths.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_followup_escalation_status_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate`

Allowed follow-up statuses are `pending_owner_response_not_proven`,
`overdue_owner_response_not_proven`, and
`escalated_for_owner_action_not_proven`. Allowed owner response material states
are `missing`, `pending`, and `escalate`. These states are escalation and
support metadata only; they are not readiness, reviewer resolution, material
completion, route/elevator field pass, or robot-control authorization.

Allowed fields are limited to safe `evidence_ref`, previous handoff ref,
previous review decision ref, owner response material status, due status,
blocked reason, next required evidence, owner action, CEO escalation
recommendation, PR #5 thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 thread state
`unresolved`, PR #5 material state `hardware_material_pending`, reply comment
`3269642220`, reply resolution claim `not_reviewer_resolution`, evidence
boundary, `source=software_proof`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

The alias is read-only diagnostics metadata. It must fail closed on raw
artifacts, raw GitHub payloads, local paths, credentials, bearer tokens,
complete artifacts, checksums, ROS topics, `/cmd_vel`, serial/UART details,
WAVE ROVER parameters, ACK/cursor/command data, success/pass/control copy,
field/cloud/phone/HIL proof claims, reviewer-resolution claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true`.

`escalated_for_owner_action_not_proven` only means the missing owner response
material should be escalated. It is not delivery success, a real field result,
a verified terminal delivery/dropoff/cancel result, real phone/browser proof,
public cloud proof, PR #5 reviewer resolution, HIL, Nav2 runtime proof, or
permission to start/confirm/cancel/ACK/replay/resubmit robot commands.

## robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary

`robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary`
is the Robot diagnostics safe alias for
`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`.
When Autonomy PC gate produces the reviewer ACK follow-up -> owner response
intake bridge, Robot diagnostics may expose only the bridge-safe fields:
`source_bridge`, source follow-up status, the same safe `evidence_ref`, owner
route, reviewer/support route, next required field-owner materials, false-state
flags, and phone-safe copy.

- Source artifact schema:
  `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1`
- Source summary schema:
  `trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1`
- Bridge capability marker:
  `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`
- Supported bridge source:
  `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`
- Bridge evidence boundary:
  `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`

The alias must preserve `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. `accepted_for_owner_response_intake_not_proven` only
means a sanitized reviewer ACK follow-up bridge is available for owner-response
intake review; it is not task record proof, dropoff completion, cancel
completion, Nav2 route completion, elevator proof, phone/browser proof, HIL, or
permission to control the robot.

The bridge alias must fail closed on raw artifacts, credentials, local paths,
raw robot responses, ROS topics, `/cmd_vel`, serial/UART details, ACK/cursor
payloads, diagnostics fetch mutation hints, GitHub mutation hints, robot command
hints, success/pass/control wording, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`.

## robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary

`robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_owner_response_intake`. It consumes only
the PC safe summary
`trashbot.field_evidence_material_resolution_owner_response_intake_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata. When the PC summary was produced by
`field_evidence_material_resolution_reviewer_ack_owner_response_intake_bridge`,
Robot diagnostics may expose only the safe marker
`source_bridge=field_evidence_material_resolution_reviewer_ack_followup_escalation_status`
and the sanitized source reviewer ACK follow-up status. It must not expose raw
source artifacts, local paths, raw GitHub payloads, credentials, or control
fields from the bridge.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_owner_response_intake.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_owner_response_intake_summary.v1`
- Supported bridge source:
  `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_owner_response_intake_gate`

Allowed intake statuses are `accepted_not_proven`, `missing_not_proven`,
`rejected_not_proven`, `blocked_not_proven`, and
`accepted_for_owner_response_intake_not_proven`. These statuses are
metadata-only intake states; they are not delivery success, owner-material real
acceptance, field pass, PR #5 reviewer resolution, or robot-control
authorization.

Allowed fields are limited to capability, schema, evidence boundary, source,
safe `evidence_ref`, owner response intake status, source reviewer ACK
follow-up status, accepted/missing/rejected/unsafe material summaries, next
required evidence, phone-safe copy, `source=software_proof`, `not_proven`,
`delivery_success=false`, `safe_to_control=false`, and
`primary_actions_enabled=false`.

The alias must fail closed on unsupported source schema or bridge markers,
unsafe raw/path/credential/control material, bearer tokens, DB/queue URLs, OSS
secrets, raw GitHub payloads, complete artifacts, checksums, ROS topics,
`/cmd_vel`, serial/UART details, WAVE ROVER parameters, ACK/cursor/command
data, tracebacks, readiness/review-acceptance claims, `delivery_success=true`,
`safe_to_control=true`, or `primary_actions_enabled=true`.

`accepted_for_owner_response_intake_not_proven` only means the reviewer ACK
follow-up bridge produced sanitized owner-response-intake metadata. It remains
`software_proof` and `not_proven`; it is not real O5 external proof, HIL, real
phone/browser proof, public cloud proof, a route/elevator field pass, PR #5
thread `PRRT_kwDOSWB9286CJ3tX` resolution, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

## robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary

`robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_owner_response_review_decision`. It
consumes only the PC safe summary
`trashbot.field_evidence_material_resolution_owner_response_review_decision_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_owner_response_review_decision.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_owner_response_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`

Allowed review decisions are
`accepted_for_material_review_not_proven`,
`needs_more_evidence_not_proven`,
`rejected_unsafe_material_response_not_proven`, and
`blocked_missing_owner_response_intake_not_proven`. These decisions are
read-only review-routing metadata only.

Allowed fields are limited to safe `evidence_ref`, source owner response
status, previous owner-response intake ref, decision reasons,
accepted/missing/rejected/unsafe material categories, next required evidence,
owner action, CEO escalation recommendation, review handoff recommendation,
PR #5 thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 state `unresolved`, material
state `hardware_material_pending`, reply comment `3269642220`, reply
resolution claim `not_reviewer_resolution`, evidence boundary,
`source=software_proof`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The alias must never turn review decision metadata into readiness, command
authorization, delivery success, owner-material real acceptance, or PR
reviewer resolution. It must fail closed on raw artifacts, raw GitHub payloads,
local paths, credentials, bearer tokens, DB/queue URLs, OSS secrets, complete
artifacts, checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER
parameters, ACK/cursor/command data, tracebacks, field/cloud/phone/HIL proof
claims, reviewer-resolution claims, owner-material acceptance claims,
`safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true`.

`accepted_for_material_review_not_proven` only means a sanitized owner
response can enter a later material review. It is not delivery success, real
route/elevator field pass, verified terminal delivery/dropoff/cancel result,
real phone/browser proof, public cloud proof, PR #5 reviewer resolution, HIL,
Nav2 runtime proof, or permission to start/confirm/cancel/ACK/replay/resubmit
robot commands.

## robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary

`robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_owner_response_review_handoff`. It
consumes only the PC safe summary
`trashbot.field_evidence_material_resolution_owner_response_review_handoff_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_owner_response_review_handoff.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_owner_response_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_owner_response_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`

Allowed handoff statuses are
`accepted_for_resolution_owner_handoff_not_proven`,
`needs_more_evidence_not_proven`,
`rejected_unsafe_owner_response_review_handoff_not_proven`, and
`blocked_missing_owner_response_review_handoff_not_proven`. These statuses are
read-only review handoff metadata only.

Allowed fields are limited to safe `evidence_ref`, source owner-response
review-decision schema/status, previous owner-response review-decision ref,
handoff reasons, handoff targets, accepted/missing/rejected/unsafe material
categories, next required evidence, owner action, CEO escalation
recommendation, PR #5 thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 state
`unresolved`, material state `hardware_material_pending`, reply comment
`3269642220`, reply resolution claim `not_reviewer_resolution`, evidence
boundary, `source=software_proof`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The alias must never turn review-handoff metadata into readiness, command
authorization, delivery success, owner-material real acceptance, PR reviewer
resolution, ACK/cursor mutation, replay, resubmit, serial open, WAVE ROVER
command, Nav2 route execution, or action-result mutation. It must fail closed
on raw artifacts, raw GitHub payloads, local paths, credentials, bearer tokens,
DB/queue URLs, OSS secrets, complete artifacts, checksums, ROS topics,
`/cmd_vel`, serial/UART details, WAVE ROVER parameters, ACK/cursor/command
data, tracebacks, field/cloud/phone/HIL proof claims, reviewer-resolution
claims, owner-material acceptance claims, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true`.

`accepted_for_resolution_owner_handoff_not_proven` only means a sanitized
owner-response review can be handed to the resolution owner for follow-up. It
is not delivery success, real route/elevator field pass, verified terminal
delivery/dropoff/cancel result, real phone/browser proof, public cloud proof,
PR #5 reviewer resolution, HIL, Nav2 runtime proof, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

## robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary

`robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_reviewer_ack_intake`. It consumes only the
phone-safe ACK intake summary
`trashbot.field_evidence_material_resolution_reviewer_ack_intake_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_intake.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_intake_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`

Allowed ACK statuses are `accepted_not_proven`, `missing_not_proven`,
`rejected_not_proven`, and `blocked_not_proven`. These statuses are read-only
reviewer ACK routing metadata only.

Allowed fields are limited to safe `evidence_ref`, source owner-response
review-handoff schema/status, previous owner-response review-handoff ref,
acknowledged by/at metadata, ACK reasons, accepted/missing/rejected/unsafe
material categories, next required evidence, owner action, CEO escalation
recommendation, PR #5 thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 state
`unresolved`, material state `hardware_material_pending`, reply comment
`3269642220`, reply resolution claim `not_reviewer_resolution`, evidence
boundary, `source=software_proof`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The alias must never turn reviewer ACK metadata into readiness, command
authorization, delivery success, owner-material real acceptance, PR reviewer
resolution, ACK mutation, cursor mutation, replay, resubmit, serial open,
WAVE ROVER command, Nav2 route execution, dropoff/cancel/result mutation, or
any control endpoint. It must fail closed on raw artifacts, raw GitHub
payloads, local paths, credentials, bearer tokens, DB/queue URLs, OSS secrets,
complete artifacts, checksums, ROS topics, `/cmd_vel`, serial/UART details,
WAVE ROVER parameters, ACK/cursor/command data, tracebacks,
field/cloud/phone/HIL proof claims, reviewer-resolution claims,
owner-material acceptance claims, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true`.

`accepted_not_proven` only means a sanitized reviewer ACK intake summary is
visible in Robot diagnostics. It is not delivery success, real route/elevator
field pass, verified terminal delivery/dropoff/cancel result, real
phone/browser proof, public cloud proof, PR #5 reviewer resolution, HIL, Nav2
runtime proof, or permission to start/confirm/cancel/ACK/replay/resubmit robot
commands.

Reviewer ACK intake must preserve the false-state boundary:
`software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`,
`not_proven`, `delivery_success=false`, `safe_to_control=false`, and
`primary_actions_enabled=false`.

It must not add or imply any control endpoint, ACK mutation, cursor mutation,
replay/resubmit, serial open, WAVE ROVER command, Nav2 route execution, or
dropoff/cancel/result mutation.

## robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary

`robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_reviewer_ack_review_decision`. It consumes
only the phone-safe Autonomy review-decision summary
`trashbot.field_evidence_material_resolution_reviewer_ack_review_decision_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_review_decision.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`

Allowed review decisions are
`accepted_for_material_review_not_proven`,
`needs_reassignment_not_proven`,
`needs_field_owner_supplement_not_proven`,
`rejected_unsafe_ack_not_proven`, and
`blocked_missing_reviewer_ack_intake_not_proven`. These decisions are read-only
review-routing metadata only.

Allowed fields are limited to safe `evidence_ref`, source reviewer ACK intake
schema/status, previous reviewer ACK intake ref, decision reasons,
accepted/missing/rejected/unsafe material categories, next required evidence,
owner action, CEO escalation recommendation, review handoff recommendation,
PR #5 thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 state `unresolved`, material
state `hardware_material_pending`, reply comment `3269642220`, reply
resolution claim `not_reviewer_resolution`, evidence boundary,
`source=software_proof`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.

The alias must never turn reviewer ACK review-decision metadata into readiness,
command authorization, delivery success, owner-material real acceptance, PR
reviewer resolution, ACK mutation, cursor mutation, replay, resubmit, serial
open, WAVE ROVER command, Nav2 route execution, or action-result mutation. It
must fail closed on raw ACK artifacts, complete artifacts, raw GitHub payloads,
local paths, credentials, bearer tokens, DB/queue URLs, OSS secrets, checksums,
ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters,
ACK/cursor/command data, tracebacks, field/cloud/phone/HIL proof claims,
reviewer-resolution claims, owner-material acceptance claims,
`safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true`.

`accepted_for_material_review_not_proven` only means a sanitized reviewer ACK
review decision can enter a later material review. It is not delivery success,
real route/elevator field pass, verified terminal delivery/dropoff/cancel
result, real phone/browser proof, public cloud proof, PR #5 reviewer
resolution, HIL, Nav2 runtime proof, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

Reviewer ACK review decision must preserve the false-state boundary:
`software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_decision_gate`,
`not_proven`, `delivery_success=false`, `safe_to_control=false`, and
`primary_actions_enabled=false`.

## robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary

`robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_reviewer_ack_review_handoff`. It consumes
only the phone-safe Autonomy reviewer ACK review-handoff summary
`trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate`

Allowed handoff statuses are
`accepted_for_material_review_handoff_not_proven`,
`needs_reassignment_not_proven`,
`needs_field_owner_supplement_not_proven`,
`rejected_unsafe_ack_review_handoff_not_proven`, and
`blocked_missing_reviewer_ack_review_decision_not_proven`. These statuses are
read-only review-routing metadata only.

Allowed fields are limited to safe `evidence_ref`, source reviewer ACK review
decision schema/status, previous reviewer ACK review-decision ref, handoff
reasons, handoff targets, accepted/missing/rejected/unsafe material categories,
next required evidence, owner action, CEO escalation recommendation, PR #5
thread id `PRRT_kwDOSWB9286CJ3tX`, PR #5 state `unresolved`, material state
`hardware_material_pending`, reply comment `3269642220`, reply resolution
claim `not_reviewer_resolution`, evidence boundary, `source=software_proof`,
`not_proven`, `safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

The alias must never turn reviewer ACK review-handoff metadata into readiness,
command authorization, delivery success, owner-material real acceptance, PR
reviewer resolution, ACK mutation, cursor mutation, replay, resubmit, serial
open, WAVE ROVER command, Nav2 route execution, or action-result mutation. It
must fail closed on raw ACK artifacts, complete artifacts, raw GitHub payloads,
local paths, credentials, bearer tokens, DB/queue URLs, OSS secrets, checksums,
ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters,
ACK/cursor/command data, tracebacks, field/cloud/phone/HIL proof claims,
reviewer-resolution claims, owner-material acceptance claims,
`safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true`.

`accepted_for_material_review_handoff_not_proven` only means a sanitized
reviewer ACK review handoff can enter a later material-review follow-up. It is
not delivery success, real route/elevator field pass, verified terminal
delivery/dropoff/cancel result, real phone/browser proof, public cloud proof,
PR #5 reviewer resolution, HIL, Nav2 runtime proof, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

Reviewer ACK review handoff must preserve the false-state boundary:
`software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate`,
`not_proven`, `delivery_success=false`, `safe_to_control=false`, and
`primary_actions_enabled=false`.

## robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary

`robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary`
is the Robot diagnostics safe alias for
`field_evidence_material_resolution_reviewer_ack_followup_escalation_status`.
It consumes only the phone-safe PC followup escalation status summary
`trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`,
an artifact wrapper containing that summary, or compatible latest status /
diagnostics fallback metadata.

- Source artifact schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status.v1`
- Source summary schema:
  `trashbot.field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`

Allowed followup statuses are
`owner_response_pending_not_proven`,
`owner_response_overdue_escalate_not_proven`,
`blocked_missing_required_materials_not_proven`,
`blocked_unsafe_material_claims_not_proven`,
`accepted_for_owner_response_intake_not_proven`, and
`blocked_missing_reviewer_ack_handoff_not_proven`. These statuses are
read-only reviewer ACK follow-up metadata only.

Allowed fields are limited to capability, schema, evidence boundary,
`source=software_proof`, safe `evidence_ref`, `followup_status`,
`due_status`, source handoff status/schema/ref, owner handoff hints, missing
required evidence, next required evidence, phone-safe copy, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

The alias must never expose raw artifacts, complete artifacts, raw GitHub
payloads, local paths, credentials, bearer tokens, signed URLs, DB/queue URLs,
OSS secrets, raw checksums, complete internal logs, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER parameters, raw tracebacks, ACK/cursor/command
data, control permissions, success claims, reviewer-resolution claims,
owner-material acceptance claims, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true`.

`accepted_for_owner_response_intake_not_proven` only means a sanitized followup
status can enter a later owner-response intake. It is not delivery success,
real route/elevator field pass, verified terminal delivery/dropoff/cancel
result, real phone/browser proof, public cloud proof, PR #5 reviewer
resolution, HIL, Nav2 runtime proof, or permission to
start/confirm/cancel/ACK/replay/resubmit robot commands.

Reviewer ACK followup escalation status must preserve the false-state boundary:
`software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`,
`not_proven`, `delivery_success=false`, `safe_to_control=false`, and
`primary_actions_enabled=false`.

## robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary

`robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary`
is the Robot diagnostics safe alias for
`field_evidence_real_material_owner_ack_review_decision`. It consumes the
canonical review-decision summary from latest status, nested diagnostics, an
explicit ref, or the matching environment override, then republishes only
sanitized owner acknowledgement review metadata for phone/Robot diagnostics.

- Capability: `field_evidence_real_material_owner_ack_review_decision`
- Source artifact schema:
  `trashbot.field_evidence_real_material_owner_ack_review_decision.v1`
- Source summary schema:
  `trashbot.field_evidence_real_material_owner_ack_review_decision_summary.v1`
- Robot diagnostics alias schema:
  `trashbot.robot_diagnostics_field_evidence_real_material_owner_ack_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_real_material_owner_ack_review_decision_gate`

Required boundary states are `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Allowed fields are limited to review decision, source owner ack status, safe
`evidence_ref`, same-ref status, decision reasons, missing materials, next
required evidence, owner handoff, proof boundary, safe copy, and not-proven
reasons. The alias must not expose raw artifacts, complete logs, local paths,
credentials, ROS topics, `/cmd_vel`, serial/UART/WAVE ROVER details,
checksums, HIL/pass wording, delivery success wording, control claims, or
PR #5 resolved wording. Inputs with `delivery_success=true`,
`primary_actions_enabled=true`, `safe_to_control=true`, raw material fields, or
unsafe copy fail closed as blocked/not_proven.

## robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary`
as a safe alias for Autonomy's elevator field evidence trace material
backfill review handoff summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_review_handoff.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_material_backfill_review_handoff_gate`

The alias is metadata-only and read-only. It may expose sanitized handoff
status such as `ready_for_field_owner_material_backfill_rerun_not_proven` or
`needs_field_owner_material_handoff_not_proven`, safe `evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_status=matched`, source
material backfill review decision metadata, field owner handoff rows, safe
rerun hints, phone-safe copy, missing required materials, rejected materials,
next required evidence, safe copy, `software_proof`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary,
`source` other than `software_proof`, `overall_status` other than
`not_proven`, same `evidence_ref` mismatch, missing owner handoff fields,
unsafe copy, raw material body, raw material refs, raw route/elevator logs,
raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
credentials, local paths, checksums, tracebacks, ACK/cursor/command/control
fields, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed as blocked/not_proven.

This alias must not expose a complete artifact or enable Start Delivery,
Confirm Dropoff, Cancel, ACK, cursor updates, persistence updates, terminal
ACK, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, dropoff/cancel completion, or delivery success. It also does not
prove a real elevator run, real Nav2/fixed-route runtime, real field task
record, real phone/browser validation, Objective 5 external proof, or any
hardware/HIL result.

## robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary`
as a safe alias for Autonomy's elevator field evidence trace material
backfill review decision summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate`

The alias is metadata-only and read-only. It may expose sanitized review
decision values such as `needs_required_material_backfill_not_proven` or
`ready_for_field_evidence_material_review_handoff_not_proven`, safe
`evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, source material backfill intake metadata,
accepted material refs, missing required materials, rejected materials,
decision reasons, next required evidence, owner handoff, safe copy,
`software_proof`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary,
`source` other than `software_proof`, `overall_status` other than
`not_proven`, same `evidence_ref` mismatch, unsafe copy, raw material body,
raw material refs, raw route/elevator logs, raw ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, credentials, local paths, checksums,
tracebacks, ACK/cursor/command/control fields, success wording,
`delivery_success=true`, or `primary_actions_enabled=true` must fail closed as
blocked/not_proven.

This alias must not expose a complete artifact or enable Start Delivery,
Confirm Dropoff, Cancel, ACK, cursor updates, persistence updates, terminal
ACK, commands, Nav2, WAVE ROVER, HIL, material collection, production
readiness, dropoff/cancel completion, or delivery success. It also does not
prove a real elevator run, real Nav2/fixed-route runtime, real field task
record, real phone/browser validation, Objective 5 external proof, or any
hardware/HIL result.

## robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary`
as a safe alias for Autonomy's elevator field evidence trace material
backfill intake summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_intake.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate`

The alias is metadata-only and read-only. It may expose sanitized intake
status such as `ready_for_material_review_not_proven` or
`needs_required_material_backfill_not_proven`, safe `evidence_ref`,
`same_evidence_ref_required=true`, source callback review handoff metadata,
accepted backfill materials, missing required materials, rejected backfill
materials, next required evidence, owner handoff, safe copy,
`software_proof`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary,
`source` other than `software_proof`, `overall_status` other than
`not_proven`, same `evidence_ref` mismatch, unsafe copy, raw material body,
raw route/elevator logs, raw ROS topics, `/cmd_vel`, serial/UART details,
WAVE ROVER details, credentials, local paths, checksums, tracebacks,
ACK/cursor/command/control fields, success wording, `delivery_success=true`,
or `primary_actions_enabled=true` must fail closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER,
HIL, material collection, production readiness, dropoff/cancel completion, or
delivery success. It also does not prove a real elevator run, real
Nav2/fixed-route runtime, real field task record, real phone/browser
validation, Objective 5 external proof, or any hardware/HIL result.

## robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary` as a
safe alias for Autonomy's elevator field evidence trace callback intake
summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_callback_intake.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_callback_intake_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_callback_intake_gate`

The alias is metadata-only and read-only. It may expose sanitized intake
status, safe `evidence_ref`, `same_evidence_ref_required=true`, source trace
summary metadata, source diagnostics metadata, redacted callback packet
metadata, accepted callback materials, missing required materials, owner
handoff, next required evidence, safe copy, `software_proof`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary, unsafe copy,
raw callback body, raw route/elevator logs, raw ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, credentials, local paths, checksums,
tracebacks, ACK/cursor/command/control fields, success wording,
`delivery_success=true`, or `primary_actions_enabled=true` must fail closed as
blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER,
HIL, material collection, production readiness, dropoff/cancel completion, or
delivery success. It also does not prove a real elevator run, real
Nav2/fixed-route runtime, real field task record, real phone/browser
validation, Objective 5 external proof, or any hardware/HIL result.

## robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary`
as a safe alias for Autonomy's elevator field evidence trace callback review
handoff summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_callback_review_handoff.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate`

The alias is metadata-only and read-only. It may expose sanitized handoff
status, safe `evidence_ref`, `same_evidence_ref_required=true`, source review
decision metadata, handoff reasons, missing required materials, next required
evidence, owner handoff, safe copy, `software_proof`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary,
`source` other than `software_proof`, `overall_status` other than
`not_proven`, unsafe copy, raw callback body, raw route/elevator logs, raw ROS
topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials,
local paths, checksums, tracebacks, ACK/cursor/command/control fields, success
wording, `delivery_success=true`, or `primary_actions_enabled=true` must fail
closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER,
HIL, material collection, production readiness, dropoff/cancel completion, or
delivery success. It also does not prove a real elevator run, real
Nav2/fixed-route runtime, real field task record, real phone/browser
validation, Objective 5 external proof, or any hardware/HIL result.

## robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary

Robot diagnostics exposes
`robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary`
as a safe alias for Autonomy's elevator field evidence trace callback review
decision summary.

- Source artifact schema:
  `trashbot.elevator_field_evidence_trace_callback_review_decision.v1`
- Source summary schema:
  `trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1`
- Robot alias schema:
  `trashbot.robot_diagnostics_elevator_field_evidence_trace_callback_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate`

The alias is metadata-only and read-only. It may expose sanitized review
decision, safe `evidence_ref`, `same_evidence_ref_required=true`, source
callback intake metadata, decision reasons, missing required materials,
rejected callback materials, next required evidence, owner handoff, safe copy,
`software_proof`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Missing summary, unreadable input, unsupported schema or boundary,
`source` other than `software_proof`, `overall_status` other than
`not_proven`, unsafe copy, raw callback body, raw route/elevator logs, raw ROS
topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials,
local paths, checksums, tracebacks, ACK/cursor/command/control fields, success
wording, `delivery_success=true`, or `primary_actions_enabled=true` must fail
closed as blocked/not_proven.

This alias must not enable Start Delivery, Confirm Dropoff, Cancel, ACK,
cursor updates, persistence updates, terminal ACK, commands, Nav2, WAVE ROVER,
HIL, material collection, production readiness, dropoff/cancel completion, or
delivery success. It also does not prove a real elevator run, real
Nav2/fixed-route runtime, real field task record, real phone/browser
validation, Objective 5 external proof, or any hardware/HIL result.
