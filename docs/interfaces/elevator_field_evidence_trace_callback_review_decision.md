# elevator_field_evidence_trace_callback_review_decision

`pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes only the previous `elevator_field_evidence_trace_callback_intake` artifact, summary, or wrapper/nested JSON.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_callback_review_decision.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_callback_review_decision_summary.v1`.

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
python3 pc-tools/evidence/elevator_field_evidence_trace_callback_review_decision.py \
  --callback-intake-json <callback_intake_summary.json> \
  --evidence-ref <safe_evidence_ref>
```

`file:<path>` and `env:<VAR>` sources are supported. The source path is used only to load JSON and is not copied into the sanitized summary.

Supported source schemas:

- `trashbot.elevator_field_evidence_trace_callback_intake.v1`
- `trashbot.elevator_field_evidence_trace_callback_intake_summary.v1`

The source must preserve the callback intake boundary `software_proof_docker_elevator_field_evidence_trace_callback_intake_gate`, `source=software_proof`, `overall_status=not_proven`, `same_evidence_ref_required=true`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Review Decisions

- `blocked_missing_callback_intake_not_proven`: callback intake artifact or summary is missing.
- `blocked_unsupported_callback_intake_not_proven`: JSON is malformed, unreadable, not an object, has an unsupported schema/boundary/source/status, or weakens the required boolean flags.
- `blocked_evidence_ref_mismatch_not_proven`: CLI/source ref is missing or mismatched, source `same_evidence_ref_status` is not matched/ready, or `same_evidence_ref_required` is not boolean `true`.
- `blocked_unsafe_callback_review_copy_not_proven`: source copy contains raw paths, credentials, ROS topics, serial/UART/WAVE ROVER wording, checksums, raw responses, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_callback_packet_rerun_not_proven`: source intake exists but is not ready and does not carry material backfill/rejection status.
- `needs_route_elevator_material_backfill_not_proven`: source intake is ready or backfill-marked but still lists missing or rejected route/elevator material categories.
- `ready_for_elevator_field_owner_handoff_not_proven`: source intake is ready, safe ref is aligned, and no missing/rejected material categories remain. This is only owner handoff readiness, not field pass.

## Summary Fields

The sanitized summary includes:

- `review_decision`
- `decision_reasons`
- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_status`
- `source_callback_intake`
- `required_route_elevator_materials`
- `missing_required_materials`
- `rejected_callback_materials`
- `next_required_evidence`
- `owner_handoff`
- `rerun_commands`
- `safe_copy`
- `not_proven`

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw callback bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, raw robot responses, or success claims. The summary is read-only and must not enable Start Delivery, Confirm Dropoff, Cancel, or any primary action.
