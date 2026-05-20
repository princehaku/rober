# ROS Status Contract

## robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary

Robot diagnostics exposes
`robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary` as a
safe alias for `field_evidence_rerun_callback_review_handoff` metadata.

- Source artifact schema:
  `trashbot.field_evidence_rerun_callback_review_handoff.v1`
- Source summary schema:
  `trashbot.field_evidence_rerun_callback_review_handoff_summary.v1`
- Robot alias:
  `robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`

The alias is metadata-only and read-only. It may expose sanitized
`handoff_status`, `review_decision`, safe `evidence_ref`, `owner_handoff`,
`next_required_evidence`, `rerun_guidance`, `blocker_summary`,
`same_evidence_ref_status`, `source=software_proof`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

Missing summary, unsupported schema or boundary, same `evidence_ref` mismatch,
unsafe copy, raw artifact fields, local paths, credentials, ROS topic names,
serial/UART/WAVE ROVER details, ACK/cursor/command/control fields, success
wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed as blocked/not_proven.

This alias must not trigger collect, dropoff, cancel, ACK, cursor updates,
Nav2 runtime, serial/UART, WAVE ROVER, HIL, raw material collection, Objective
5 external proof, Objective 1 hardware proof, route/elevator field pass,
dropoff/cancel completion, or delivery success.
