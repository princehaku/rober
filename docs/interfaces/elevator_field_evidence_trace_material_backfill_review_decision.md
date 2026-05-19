# elevator_field_evidence_trace_material_backfill_review_decision

`pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_decision.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes the previous `elevator_field_evidence_trace_material_backfill_intake` artifact, summary, or Robot diagnostics safe alias.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1`.

## Boundary

Every output remains:

- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

The boundary is `software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate`.

The gate does not scan a real material directory, read raw field files, access ROS graph, Nav2/fixed-route runtime, serial/UART, WAVE ROVER, real elevator state, cloud services, or real phone/browser state. It does not prove real route/elevator field execution, real Nav2/fixed-route execution, real task record validity, real dropoff/cancel completion, delivery success, Objective 5 external proof, or a real phone/browser pass.

## Inputs

CLI:

```bash
python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_decision.py \
  --material-backfill-intake-json <material_backfill_intake_summary.json> \
  --evidence-ref <safe_evidence_ref>
```

`--material-backfill-intake-summary` is an alias for summary inputs. `file:<path>` and `env:<VAR>` sources are supported. Source paths are used only to load JSON and are not copied into the sanitized summary.

Supported source schemas:

- `trashbot.elevator_field_evidence_trace_material_backfill_intake.v1`
- `trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1`

Wrappers are supported when they contain `robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary`.

The source intake must preserve the `elevator_field_evidence_trace_material_backfill_intake` boundary `software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate`, `source=software_proof`, `overall_status=not_proven`, `same_evidence_ref_required=true`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Required Materials

The required material categories are inherited from the intake gate:

- `real_elevator_door_state`
- `real_target_floor_confirmation`
- `real_human_assistance_record`
- `real_nav2_or_fixed_route_runtime_log`
- `real_route_completion_signal`
- `real_field_task_record`
- `real_dropoff_or_cancel_completion`
- `real_delivery_result`

The review decision checks whether every required category has a safe accepted ref under the same `safe_evidence_ref`. It does not open, parse, or validate the real material file content.

## Review Decision Statuses

- `blocked_missing_material_backfill_intake_not_proven`: previous material backfill intake artifact or summary is missing, unreadable, malformed, or not an object.
- `blocked_unsupported_material_backfill_intake_not_proven`: intake has an unsupported schema/boundary/source/status, weakens required booleans, or sets `delivery_success` / `primary_actions_enabled` outside the false boundary.
- `blocked_evidence_ref_mismatch_not_proven`: CLI/source refs are missing or mismatched, unsafe, or `same_evidence_ref_required` is not boolean `true`.
- `blocked_unsafe_material_review_decision_not_proven`: intake or material review copy contains raw paths, credentials, ROS topics, `/cmd_vel`, serial/UART/WAVE ROVER wording, checksums, complete raw artifact wording, traceback, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_required_material_backfill_not_proven`: intake is safe but one or more required material refs are missing, rejected, or not safely accepted.
- `ready_for_field_evidence_material_review_handoff_not_proven`: all required materials have safe refs with the same evidence ref. This is only readiness for later material review handoff, not a real route/elevator field pass.

## Summary Fields

The sanitized summary includes:

- `review_decision`
- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_required`
- `same_evidence_ref_status`
- `source_intake`
- `required_materials`
- `accepted_material_refs`
- `missing_required_materials`
- `rejected_material_refs`
- `material_review_state`
- `decision_reasons`
- `next_required_evidence`
- `owner_handoff`
- `rerun_commands`
- `safe_copy`
- `not_proven`

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw source intake bodies, raw material packet bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, complete artifacts, tracebacks, or success claims. The summary is read-only and must not enable Start Delivery, Confirm Dropoff, Cancel, or any primary action.
