# elevator_field_evidence_trace_callback_intake

`pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py` is a PC-only evidence gate for the elevator field evidence trace chain. It consumes a safe callback packet, an `elevator_action_feedback_trace` summary, a Robot diagnostics summary such as `robot_diagnostics_elevator_action_feedback_trace_summary`, and optional required route/elevator material metadata.

The output is an artifact with schema `trashbot.elevator_field_evidence_trace_callback_intake.v1` and a sanitized summary with schema `trashbot.elevator_field_evidence_trace_callback_intake_summary.v1`.

## Boundary

Every output remains:

- `source=software_proof`
- `overall_status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

The gate does not read a real materials directory, ROS graph, Nav2/fixed-route runtime, hardware, WAVE ROVER/UART/HIL, cloud services, or real phone/browser state. It does not prove `real_route_elevator_field_pass`, real Nav2/fixed-route execution, real task record validity, real elevator operation, dropoff/cancel completion, delivery success, Objective 5 external proof, or a real phone/browser pass.

## Inputs

CLI:

```bash
python3 pc-tools/evidence/elevator_field_evidence_trace_callback_intake.py \
  --callback-json <safe_callback_packet.json> \
  --trace-summary-json <elevator_action_feedback_trace_summary.json> \
  --diagnostics-summary-json <diagnostics_summary.json> \
  --required-materials-json <required_materials.json> \
  --evidence-ref <safe_evidence_ref>
```

`file:<path>` and `env:<VAR>` sources are supported for all JSON inputs. The source path is used only to load JSON and is not copied into the sanitized summary.

Supported trace schemas:

- `trashbot.elevator_action_feedback_trace.v1`
- `trashbot.elevator_action_feedback_trace_summary.v1`
- `trashbot.robot_diagnostics_elevator_action_feedback_trace_summary.v1`

Supported callback packet schemas:

- empty schema for a minimal sanitized packet
- `trashbot.elevator_field_evidence_trace_callback_packet.v1`
- `trashbot.elevator_field_evidence_trace_callback_packet_summary.v1`

## Status Mapping

- `blocked_missing_callback_packet_not_proven`: callback packet is missing or not readable as required input.
- `blocked_unsupported_or_bad_json_not_proven`: an input JSON file is malformed, unreadable, or not an object.
- `blocked_missing_trace_summary_not_proven`: required `elevator_action_feedback_trace` summary is missing.
- `blocked_missing_diagnostics_summary_not_proven`: required diagnostics/mobile safe summary is missing.
- `blocked_unsupported_callback_packet_not_proven`: callback schema, boundary, fields, or material response types are unsupported.
- `blocked_unsupported_trace_or_diagnostics_summary_not_proven`: trace or diagnostics summary does not preserve the expected schema, software-proof source, not-proven status, or disabled action flags.
- `blocked_evidence_ref_mismatch_not_proven`: callback packet, trace summary, diagnostics summary, required materials metadata, or CLI expectation lacks a safe ref, weakens `same_evidence_ref_required`, or uses a different ref.
- `blocked_unsafe_callback_or_summary_copy_not_proven`: callback or summary contains raw paths, ROS topics, serial/UART/WAVE ROVER wording, credentials, checksum/raw artifact text, traceback, success wording, `delivery_success=true`, or `primary_actions_enabled=true`.
- `needs_route_elevator_material_backfill_not_proven`: packet is safe and refs align, but one or more required route/elevator material classes are missing or rejected.
- `callback_packet_intake_ready_for_review_not_proven`: packet is safe, same `safe_evidence_ref` is aligned, and every required material class has a sanitized callback response. This still requires review and is not field pass.

## Summary Fields

The sanitized summary includes:

- `safe_evidence_ref` / `evidence_ref`
- `same_evidence_ref_status`
- `source_trace`
- `source_diagnostics`
- `callback_packet`
- `required_route_elevator_materials`
- `accepted_callback_materials`
- `missing_required_materials`
- `rejected_callback_materials`
- `owner_handoff`
- `rerun_commands`
- `safe_copy`
- `not_proven`

Robot diagnostics and mobile consumers should read the summary or `safe_copy` only. They must not render raw callback bodies, raw local paths, ROS topic names, credentials, hardware transport details, checksums, or success claims.
