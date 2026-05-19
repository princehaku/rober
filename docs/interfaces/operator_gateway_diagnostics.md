# Operator Gateway Diagnostics

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
