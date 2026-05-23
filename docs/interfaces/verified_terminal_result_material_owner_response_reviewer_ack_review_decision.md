# verified terminal-result material owner-response reviewer ACK review decision

Run time: 2026-05-24 00:01 Asia/Shanghai

`verified_terminal_result_material_owner_response_reviewer_ack_review_decision`
is a PC-only evidence gate after
`verified_terminal_result_material_owner_response_reviewer_ack_intake`. It only
derives from that safe intake metadata and emits an artifact, a summary, and the
Robot alias
`robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary`.

## Proof Boundary

- `source=software_proof`
- `status=not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`

This gate is not a real terminal result, not verified delivery/dropoff/cancel
result, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not route/elevator field pass,
not WAVE ROVER/UART/HIL proof, not LiDAR/ToF installed proof, not delivery
success, and not PR #5 resolution. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains
`unresolved` / `hardware_material_pending`.

## Inputs

Required CLI input:

```bash
python3 pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_review_decision.py \
  --reviewer-ack-intake-json /tmp/verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.json \
  --evidence-ref terminal-reviewer-decision-001 \
  --output-dir /tmp/verified_terminal_result_material_owner_response_reviewer_ack_review_decision
```

The source JSON must be a safe artifact, summary, Robot alias, or wrapper around
`verified_terminal_result_material_owner_response_reviewer_ack_intake`. The
source boundary must be
`software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
and it must retain `source=software_proof`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

## Outputs

Canonical outputs:

- `verified_terminal_result_material_owner_response_reviewer_ack_review_decision.json`
- `verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.json`
- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary`

Important fields:

- `schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision.v1`
- `capability=verified_terminal_result_material_owner_response_reviewer_ack_review_decision`
- `safe_evidence_ref` / `evidence_ref`
- `previous_intake_reference`
- `reviewer_ack_state`
- `review_decision`
- `decision_reasons`
- `next_required_evidence`
- `owner_action`
- `review_handoff_recommendation`
- `pr5_thread.thread_id=PRRT_kwDOSWB9286CJ3tX`
- `pr5_thread.state=unresolved`
- `pr5_thread.material_state=hardware_material_pending`
- `safe_copy`

## Decision Classes

`review_decision` is fixed to six fail-closed classes:

- `accepted_for_review_not_proven`: safe ACK intake can enter human review.
- `missing_material_not_proven`: safe intake says more material/backfill is
  still required.
- `reassignment_required_not_proven`: safe ACK intake routes review to another
  reviewer/owner.
- `rejected_unsafe_not_proven`: source includes unsafe raw fields, credentials,
  local paths, ROS/control details, hardware details, success claims, HIL claims,
  PR #5 resolved claims, or true control flags.
- `blocked_missing_source_intake_not_proven`: source intake is missing,
  unreadable, unsupported, or has the wrong proof boundary.
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
