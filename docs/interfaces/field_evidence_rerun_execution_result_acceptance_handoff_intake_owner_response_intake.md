# field evidence rerun acceptance handoff intake owner response intake

Run time: 2026-05-24 Asia/Shanghai

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`
is a PC-only evidence gate. It accepts a sanitized source from the existing
`field_evidence_rerun_execution_result_acceptance_handoff_intake_followup_escalation_status`
chain, or the reviewer-ACK bridge source
`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.
It does not create a new owner-response mainline.

## Proof Boundary

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- normal boundary:
  `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_gate`
- reviewer-ACK bridge boundary:
  `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`

The bridge output carries
`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`
and
`source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.

## Inputs

Required CLI input:

```bash
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.py \
  --followup-status-json /tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary.json \
  --owner-response-json /tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_packet.json \
  --evidence-ref field-rerun-owner-response-001 \
  --output /tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.json \
  --summary-output /tmp/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.json
```

The source JSON must be a sanitized artifact, summary, Robot alias, or wrapper.
For bridge mode, its source boundary must be
`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate`
and the source must retain `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

The owner response packet must use the same safe `evidence_ref`. Any mismatch
fails closed.

## Required Next Materials

The owner response checklist is metadata-only and must cover:

- `real task record`
- `dropoff/cancel completion`
- `Nav2/fixed-route runtime log`
- `route completion signal`
- `elevator door status`
- `floor confirmation`
- `human assistance note`
- `delivery result`
- `route/elevator field pass`
- `true phone/browser evidence`
- `PR #5 hardware material remains pending unless PRRT_kwDOSWB9286CJ3tX is live resolved by reviewer`

## Outputs

Canonical outputs:

- `schema=trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake.v1`
- `schema=trashbot.field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary.v1`
- `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary`

Important fields:

- `capability=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake`
- `bridge_capability=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`
- `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`
- `owner_response_status`
- `allowed_owner_response_statuses`
- `owner_response_reasons`
- `safe_evidence_ref` / `evidence_ref`
- `previous_followup_reference`
- `accepted_materials`
- `missing_materials`
- `rejected_materials`
- `blocked_materials`
- `required_owner_response_materials`
- `material_response_details`
- `next_required_evidence`
- `safe_copy`

`owner_response_status` is limited to `accepted`, `missing`, `rejected`, and
`blocked`. `accepted` only means `accepted_for_review_not_proven`.

## Fail-Closed Rules

The gate blocks instead of accepting unsafe source or owner response material
when it sees success wording, control flags, missing/unsafe bridge metadata, raw
artifact paths, credentials, ROS topics, `/cmd_vel`, serial/UART details,
ACK/cursor mutation, GitHub mutation, upload/review action, robot command hints,
O5 external proof claims, O1 HIL claims, PR #5 resolution claims,
`delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true`.

This gate is not a real task record, not a real Nav2/fixed-route runtime log,
not a route completion signal, not an elevator door status or floor
confirmation, not a human assistance note, not dropoff/cancel completion, not a
delivery result, not a route/elevator field pass, not true phone/browser
evidence, not HIL, not PR #5 resolution, and not OKR completion lift.
