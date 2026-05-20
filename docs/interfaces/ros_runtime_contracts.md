# ROS Runtime Contracts

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
