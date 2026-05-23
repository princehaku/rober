# verified terminal-result material owner-response reviewer ACK follow-up escalation status

Run time: 2026-05-24 02:03 Asia/Shanghai

`verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status`
is a PC-only evidence gate after
`verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`.
It only derives from safe review-handoff metadata and emits an artifact, a
summary, and the Robot alias
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`.

## Proof Boundary

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`

This gate is not a real terminal result, not verified delivery/dropoff/cancel
result, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not route/elevator field pass,
not WAVE ROVER/UART/HIL proof, not LiDAR/ToF installed proof, not delivery
success, and not PR #5 resolution. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains
`unresolved` / `hardware_material_pending`.

## Inputs

Required CLI input:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py \
  --reviewer-ack-review-handoff-json /tmp/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.json \
  --followup-state overdue \
  --evidence-ref terminal-followup-001 \
  --output-dir /tmp/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status
```

The source JSON must be a safe artifact, summary, Robot alias, or wrapper around
`verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`.
The source boundary must be
`software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`
and it must retain `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

## Outputs

Canonical outputs:

- `verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json`
- `verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.json`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`

Important fields:

- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1`
- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status`
- `safe_evidence_ref` / `evidence_ref`
- `safe_command_id` / `command_id`
- `unresolved_blocker`
- `followup_state`
- `due_status`
- `owner_route`
- `reviewer_route`
- `support_route`
- `escalation_reason`
- `next_required_evidence`
- `pr5_thread.thread_id=PRRT_kwDOSWB9286CJ3tX`
- `pr5_thread.state=unresolved`
- `pr5_thread.material_state=hardware_material_pending`
- `safe_copy`

## Follow-up States

`followup_state` is fixed to five fail-closed classes:

- `pending`: real material follow-up is waiting under the same safe
  `evidence_ref`; no success or control claim is allowed.
- `due`: owner route must provide next required evidence; this is still
  `not_proven`.
- `overdue`: support route should escalate missing real materials without
  claiming PR #5 resolution.
- `escalated`: follow-up has been escalated to owner/support/reviewer routes,
  but PR #5 remains unresolved / `hardware_material_pending`.
- `blocked_missing_real_materials`: source is missing, unsafe, routed
  incorrectly, missing next required evidence, or not ready for follow-up.

## Fail-Closed Rules

The gate blocks instead of passing through unsafe material when it sees success
wording, control flags, missing blocker identity, missing next required evidence,
missing owner/reviewer/support route, unsafe copy, raw fields, complete
artifacts, credentials, tokens, local paths, URLs, DB/queue/OSS endpoints, ROS
topic/service/action details, `/cmd_vel`, serial/UART/WAVE ROVER/ESP32/Orange Pi
details, ACK mutation hints, robot command hints, HIL pass/proof claims, PR #5
resolved claims, `delivery_success=true`, `primary_actions_enabled=true`, or
`safe_to_control=true`.

All blocked outputs still keep `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false` so Robot/mobile consumers cannot accidentally enable
control actions.
