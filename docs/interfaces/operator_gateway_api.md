# Operator Gateway API

## robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary

`/api/diagnostics` exposes
`robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary` as a
Robot-safe alias for the PC gate summary
`trashbot.field_evidence_material_blocker_escalation_pack_summary.v1`.

- Robot alias schema:
  `trashbot.robot_diagnostics_field_evidence_material_blocker_escalation_pack_summary.v1`
- Source schema: `trashbot.field_evidence_material_blocker_escalation_pack.v1`
- Source summary schema:
  `trashbot.field_evidence_material_blocker_escalation_pack_summary.v1`
- Proof boundary:
  `software_proof_docker_field_evidence_material_blocker_escalation_pack_gate`
- Capability: `field_evidence_material_blocker_escalation_pack`

Allowed fields are summary-only metadata: `status`, `pack_status.verdict`,
`blocked_reason`, `target_owner`, `owner_escalation_level`,
`next_required_evidence`, `owner_handoff`, `safe_evidence_ref`,
`field_safe_copy`, `safe_copy`, `safe_phone_copy`, `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Missing source summaries, unsupported schemas, unsafe fields, enabled primary
actions, control claims, or success claims fail closed as `not_proven`. The
alias must not expose raw artifact bodies, complete local paths, credentials,
checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, baudrate, or
WAVE ROVER parameters.

This alias is read-only. It does not change runtime control authorization and
must not enable Start Delivery, Confirm Dropoff, Cancel, ACK posting, cursor
updates, Nav2 execution, serial/UART access, WAVE ROVER access, real HIL,
route/elevator field pass, verified terminal result, dropoff/cancel completion,
or delivery success.
