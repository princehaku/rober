# elevator_field_evidence_trace_material_backfill_intake

`pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes the previous `elevator_field_evidence_trace_callback_review_handoff` artifact or summary plus an operator-provided safe material packet/file refs JSON.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_material_backfill_intake.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1`.

## Boundary

Every output remains:

- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

The boundary is `software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate`.

The gate does not scan a real material directory, read raw field files, access ROS graph, Nav2/fixed-route runtime, serial/UART, WAVE ROVER, real elevator state, cloud services, or real phone/browser state. It does not prove real route/elevator field execution, real Nav2/fixed-route execution, real task record validity, real dropoff/cancel completion, delivery success, Objective 5 external proof, or a real phone/browser pass.

## Inputs

CLI:

```bash
python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py \
  --handoff-json <callback_review_handoff_summary.json> \
  --material-packet-json <safe_material_packet.json> \
  --evidence-ref <safe_evidence_ref>
```

`file:<path>` and `env:<VAR>` sources are supported. Source paths are used only to load JSON and are not copied into the sanitized summary.

Supported handoff source schemas:

- `trashbot.elevator_field_evidence_trace_callback_review_handoff.v1`
- `trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1`

The handoff source must preserve the `elevator_field_evidence_trace_callback_review_handoff` boundary `software_proof_docker_elevator_field_evidence_trace_callback_review_handoff_gate`, `source=software_proof`, `overall_status=not_proven`, `same_evidence_ref_required=true`, `delivery_success=false`, and `primary_actions_enabled=false`.

The operator material packet may use schema `trashbot.elevator_field_evidence_trace_material_backfill_packet.v1` or a schema-less safe wrapper. It must provide only safe material refs, not raw file paths or raw content.

## Required Materials

The required material categories are:

- `real_elevator_door_state`
- `real_target_floor_confirmation`
- `real_human_assistance_record`
- `real_nav2_or_fixed_route_runtime_log`
- `real_route_completion_signal`
- `real_field_task_record`
- `real_dropoff_or_cancel_completion`
- `real_delivery_result`

The gate checks whether every category has a non-placeholder safe ref under the same `safe_evidence_ref`. It does not open, parse, or validate the real material file content.

## Intake Statuses

- `blocked_missing_handoff_not_proven`: previous callback review handoff artifact or summary is missing, unreadable, malformed, or not an object.
- `blocked_unsupported_handoff_not_proven`: handoff has an unsupported schema/boundary/source/status, weakens required booleans, or the operator packet has unsupported fields.
- `blocked_missing_material_packet_not_proven`: operator material packet/file refs JSON is missing, unreadable, malformed, or not an object.
- `blocked_evidence_ref_mismatch_not_proven`: CLI, source handoff, and operator packet refs are missing or mismatched, or `same_evidence_ref_required` is not boolean `true`.
- `blocked_unsafe_material_ref_not_proven`: handoff or operator material packet contains raw paths, credentials, ROS topics, serial/UART/WAVE ROVER wording, checksums, raw responses, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_required_material_backfill_not_proven`: material packet is safe but one or more required material refs are missing, placeholder, rejected, or outside the required list.
- `ready_for_material_review_not_proven`: all required materials have safe refs with the same evidence ref. This is only readiness for material review, not field pass.

## Summary Fields

The sanitized summary includes:

- `intake_status`
- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_required`
- `same_evidence_ref_status`
- `source_handoff`
- `operator_material_packet`
- `required_materials`
- `accepted_material_refs`
- `missing_required_materials`
- `rejected_material_refs`
- `next_required_evidence`
- `rerun_commands`
- `safe_copy`
- `not_proven`

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw callback bodies, raw material packet bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, raw robot responses, or success claims. The summary is read-only and must not enable Start Delivery, Confirm Dropoff, Cancel, or any primary action.
