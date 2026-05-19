# Operator Gateway Diagnostics

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
