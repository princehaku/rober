# elevator_field_evidence_trace_callback_review_handoff

`pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes only the previous `elevator_field_evidence_trace_callback_review_decision` artifact, summary, or wrapper/nested diagnostics JSON.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_callback_review_handoff.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_callback_review_handoff_summary.v1`.

## Boundary

Every output remains:

- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

The gate does not read a real materials directory, ROS graph, Nav2/fixed-route runtime, serial/UART, WAVE ROVER, real elevator state, cloud services, or real phone/browser state. It does not prove real route/elevator field execution, real Nav2/fixed-route execution, real task record validity, real dropoff/cancel completion, delivery success, Objective 5 external proof, or a real phone/browser pass.

## Inputs

CLI:

```bash
python3 pc-tools/evidence/elevator_field_evidence_trace_callback_review_handoff.py \
  --callback-review-decision-json <callback_review_decision_summary.json> \
  --evidence-ref <safe_evidence_ref>
```

`file:<path>` and `env:<VAR>` sources are supported. The source path is used only to load JSON and is not copied into the sanitized summary.

Supported source schemas:

- `trashbot.elevator_field_evidence_trace_callback_review_decision.v1`
- `trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1`

The source must preserve the callback review decision boundary `software_proof_docker_elevator_field_evidence_trace_callback_review_decision_gate`, `source=software_proof`, `overall_status=not_proven`, `same_evidence_ref_required=true`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Handoff Statuses

- `blocked_missing_review_decision_not_proven`: callback review decision artifact or summary is missing.
- `blocked_unsupported_review_decision_not_proven`: JSON is malformed, unreadable, not an object, has an unsupported schema/boundary/source/status, or weakens the required boolean flags.
- `blocked_evidence_ref_mismatch_not_proven`: CLI/source ref is missing or mismatched, source `same_evidence_ref_status` is not matched/ready, or `same_evidence_ref_required` is not boolean `true`.
- `blocked_unsafe_handoff_copy_not_proven`: source copy contains raw paths, credentials, ROS topics, serial/UART/WAVE ROVER wording, checksums, raw responses, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_review_decision_rerun_not_proven`: source review decision is not one of the supported handoff inputs.
- `ready_for_owner_material_backfill_not_proven`: source review decision says route/elevator materials still need owner backfill. This is only owner follow-up readiness, not field pass.
- `ready_for_field_execution_owner_handoff_not_proven`: source review decision is safe, same-ref aligned, and ready for owner handoff. This is still only metadata handoff readiness, not field execution proof.

## Summary Fields

The sanitized summary includes:

- `handoff_status`
- `status_reasons`
- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_status`
- `source_review_decision`
- `required_route_elevator_materials`
- `missing_required_materials`
- `rejected_callback_materials`
- `owner_handoff`
- `next_required_evidence`
- `rerun_commands`
- `safe_copy`
- `not_proven`

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw callback bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, raw robot responses, or success claims. The summary is read-only and must not enable Start Delivery, Confirm Dropoff, Cancel, or any primary action.
