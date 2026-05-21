# Operator Gateway Diagnostics

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
