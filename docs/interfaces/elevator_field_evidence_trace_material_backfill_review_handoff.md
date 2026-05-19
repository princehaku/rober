# elevator_field_evidence_trace_material_backfill_review_handoff

`pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_handoff.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes only the previous `elevator_field_evidence_trace_material_backfill_review_decision` artifact, summary, or Robot diagnostics safe alias.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_material_backfill_review_handoff.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1`.

## Boundary

Every output remains:

- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

The handoff boundary is `software_proof_docker_elevator_field_evidence_trace_material_backfill_review_handoff_gate`. The required source boundary is `software_proof_docker_elevator_field_evidence_trace_material_backfill_review_decision_gate`.

The gate does not read a real materials directory, ROS graph, Nav2/fixed-route runtime, serial/UART, WAVE ROVER, real elevator state, external cloud, or real phone/browser state. It does not prove real route/elevator field execution, real Nav2/fixed-route execution, real task record validity, real dropoff/cancel completion, delivery success, Objective 5 external proof, or a real phone/browser pass.

## Inputs

CLI:

```bash
python3 pc-tools/evidence/elevator_field_evidence_trace_material_backfill_review_handoff.py \
  --material-backfill-review-decision-json <material_backfill_review_decision_summary.json> \
  --evidence-ref <safe_evidence_ref>
```

`--material-backfill-review-decision-summary` is an alias for summary inputs. `file:<path>` and `env:<VAR>` sources are supported. Source paths are used only to load JSON and are not copied into the sanitized summary.

Supported source schemas:

- `trashbot.elevator_field_evidence_trace_material_backfill_review_decision.v1`
- `trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1`

Wrappers are supported when they contain `robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary`.

The source review decision must preserve `source=software_proof`, `overall_status=not_proven`, `same_evidence_ref_required=true`, `delivery_success=false`, `primary_actions_enabled=false`, and the same safe `safe_evidence_ref`.

## Handoff Statuses

- `blocked_missing_material_backfill_review_decision_not_proven`: previous material backfill review decision artifact or summary is missing, unreadable, malformed, or not an object.
- `blocked_unsupported_material_backfill_review_decision_not_proven`: review decision has an unsupported schema/boundary/source/status, weakens required booleans, or sets `delivery_success` / `primary_actions_enabled` outside the false boundary.
- `blocked_evidence_ref_mismatch_not_proven`: CLI/source refs are missing, unsafe, mismatched, source same-ref status is not matched/ready, or `same_evidence_ref_required` is not boolean `true`.
- `blocked_unsafe_material_review_handoff_not_proven`: review decision, handoff copy, `safe_rerun_hints`, or `phone_safe_copy` contains raw paths, credentials, ROS topics, `/cmd_vel`, serial/UART/WAVE ROVER wording, checksums, complete raw artifact wording, traceback, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_field_owner_material_handoff_not_proven`: source review decision is safe but missing or rejected material refs still require field owner backfill.
- `ready_for_field_owner_material_backfill_rerun_not_proven`: handoff package is safe and complete enough for a field owner to backfill or rerun the material review chain. This is not a real route/elevator field pass.

## Summary Fields

The sanitized summary includes:

- `handoff_status`
- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_required`
- `same_evidence_ref_status`
- `source_review_decision`
- `field_owner_handoff`
- `safe_rerun_hints`
- `phone_safe_copy`
- `missing_required_materials`
- `rejected_materials`
- `safe_copy`
- `not_proven`

`field_owner_handoff` contains owner/material/next action rows for field owner follow-up. `safe_rerun_hints` contains only PC evidence-gate rerun guidance and same-ref reminders. `phone_safe_copy` is read-only status copy for mobile surfaces and must not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor advancement, or any robot command.

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw source review decision bodies, raw material bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, complete artifacts, tracebacks, or success claims.
