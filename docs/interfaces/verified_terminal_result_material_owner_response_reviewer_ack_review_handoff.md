# verified terminal-result material owner-response reviewer ACK review handoff

Run time: 2026-05-24 00:01 Asia/Shanghai

`verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`
is a PC-only evidence gate after
`verified_terminal_result_material_owner_response_reviewer_ack_review_decision`.
It only derives from that safe review-decision metadata and emits an artifact, a
summary, and the Robot alias
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`.

## Proof Boundary

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`

This gate is not a real terminal result, not verified delivery/dropoff/cancel
result, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not route/elevator field pass,
not WAVE ROVER/UART/HIL proof, not LiDAR/ToF installed proof, not delivery
success, and not PR #5 resolution. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains
`unresolved` / `hardware_material_pending`.

## Inputs

Required CLI input:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.py \
  --reviewer-ack-review-decision-json /tmp/verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.json \
  --evidence-ref terminal-reviewer-handoff-001 \
  --output-dir /tmp/verified_terminal_result_material_owner_response_reviewer_ack_review_handoff
```

The source JSON must be a safe artifact, summary, Robot alias, or wrapper around
`verified_terminal_result_material_owner_response_reviewer_ack_review_decision`.
The source boundary must be
`software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`
and it must retain `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

## Outputs

Canonical outputs:

- `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.json`
- `verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.json`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`

Important fields:

- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_review_handoff`
- `safe_evidence_ref` / `evidence_ref`
- `previous_decision_reference`
- `source_review_decision`
- `handoff_status`
- `handoff_reasons`
- `next_required_evidence`
- `handoff_action`
- `reviewer_handoff`
- `pr5_thread.thread_id=PRRT_kwDOSWB9286CJ3tX`
- `pr5_thread.state=unresolved`
- `pr5_thread.material_state=hardware_material_pending`
- `safe_copy`

## Handoff Classes

`handoff_status` is fixed to six fail-closed classes:

- `ready_for_real_material_reviewer_handoff_not_proven`: safe review-decision
  metadata can be handed to a human real-material reviewer.
- `missing_material_not_proven`: the previous decision still needs safe material
  backfill before reviewer handoff.
- `reassignment_required_not_proven`: the previous decision routes handoff to a
  reassigned reviewer or owner.
- `rejected_unsafe_not_proven`: source includes unsafe raw fields, credentials,
  local paths, ROS/control details, hardware details, success claims, HIL claims,
  PR #5 resolved claims, or true control flags.
- `blocked_missing_source_review_decision_not_proven`: source review-decision is
  missing, unreadable, unsupported, or has the wrong proof boundary.
- `evidence_ref_mismatch_not_proven`: requested/source `evidence_ref` is missing,
  unsafe, or inconsistent.

## Fail-Closed Rules

The gate rejects or blocks instead of passing through unsafe material when it
sees raw fields, complete artifacts, checksums, credentials, tokens, local
paths, URLs, DB/queue/OSS endpoints, ROS topic/service/action details,
`/cmd_vel`, serial/UART/WAVE ROVER/ESP32/Orange Pi details, tracebacks, start /
confirm / cancel command wording, verified terminal-result claims, delivery /
dropoff / cancel success claims, O5 external proof claims, HIL pass/proof
claims, PR #5 resolved claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true`.

All blocked and rejected outputs still keep `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false` so Robot/mobile consumers cannot accidentally enable
control actions.
