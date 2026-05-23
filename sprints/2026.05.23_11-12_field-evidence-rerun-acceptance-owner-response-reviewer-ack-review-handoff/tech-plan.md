# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Review Handoff Tech Plan

Run time: 2026-05-23 11:12 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. Current `OKR.md` 4.1 lowest Objective: Objective 5 at about 68%.
2. This sprint does not directly target Objective 5 external proof.
3. Reason: Objective 5 movement requires real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal result. This Docker-only host cannot produce those materials. Objective 1 is next at about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` and requires real 2D LiDAR / ToF and HIL-entry materials unavailable here.
4. Current actionable continuation: `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff`. This follows the latest completed reviewer ACK review-decision rung and keeps function moving forward as software-proof evidence governance without claiming O5 external proof.

Expected closeout: no OKR percentage lift.

## Capability And Boundary

Capability:

`field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff`

Boundary:

`software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_gate`

Fixed flags and phrases:

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift
- `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`

Not claimed:

- Not O5 external proof.
- Not O1 HIL or PR #5 resolution.
- Not true phone/browser proof.
- Not route/elevator field pass.
- Not Nav2/fixed-route runtime pass.
- Not verified terminal delivery/dropoff/cancel result.
- Not dropoff/cancel completion.
- Not delivery success.

## Required Handoff States

Implementation must support exactly these user-visible / support-visible handoff states unless a worker documents a compatibility reason in `tech-done.md`:

- `ready_for_field_owner_reviewer_ack_followup_not_proven`
- `needs_reviewer_handoff_reassignment_not_proven`
- `needs_field_owner_ack_material_supplement_not_proven`
- `rejected_unsafe_reviewer_ack_handoff_not_proven`
- `blocked_missing_reviewer_ack_review_decision_not_proven`

## Parallel Worker Plan

The implementation phase must launch Tasks A, B, and C in parallel with `spawn_agent(agent_type=worker)` because file ownership is non-overlapping. Product Task D runs after worker evidence returns.

### Task A - Autonomy Algorithm Engineer

Owner role: `autonomy-engineer`

Allowed files:

- `pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py`
- `pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Implementation requirements:

- Create a PC evidence gate that consumes the prior reviewer ACK review-decision safe artifact or summary.
- Emit a sanitized review handoff artifact and summary with the capability and boundary above.
- Preserve same safe `evidence_ref` and reject evidence-ref mismatch.
- Fail closed on raw ROS topics, `/cmd_vel`, serial/UART paths, local filesystem paths, credentials, DB/queue URLs, complete artifacts, checksums, tracebacks, HIL/pass wording, delivery success claims, dropoff/cancel completion claims, true phone/browser claims, and route/elevator field-pass claims.
- Include the required handoff states exactly.
- Keep technical comments in Chinese and above the repo's 20% meaningful-comment bar for new code.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py
python3 -m unittest pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py
python3 pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py --help
rg -n "ready_for_field_owner_reviewer_ack_followup_not_proven|needs_reviewer_handoff_reassignment_not_proven|needs_field_owner_ack_material_supplement_not_proven|rejected_unsafe_reviewer_ack_handoff_not_proven|blocked_missing_reviewer_ack_review_decision_not_proven|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py pc-tools/evidence/test_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.py pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B - Robot Platform Engineer

Owner role: `robot-software-engineer`

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Implementation requirements:

- Add a Robot diagnostics safe alias for the reviewer ACK review-handoff summary.
- Prefer sanitized `robot_diagnostics_*_summary` fields over raw artifacts.
- Preserve `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Do not expose raw ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER parameters, credentials, local paths, complete artifacts, checksums, tracebacks, HIL/pass wording, route/elevator field-pass claims, or delivery success claims.
- Keep technical comments in Chinese and above the repo's 20% meaningful-comment bar for touched code.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff|ready_for_field_owner_reviewer_ack_followup_not_proven|needs_reviewer_handoff_reassignment_not_proven|needs_field_owner_ack_material_supplement_not_proven|rejected_unsafe_reviewer_ack_handoff_not_proven|blocked_missing_reviewer_ack_review_decision_not_proven|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

### Task C - User Touchpoint Full-Stack Engineer

Owner role: `full-stack-software-engineer`

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only `mobile/web` panel for the reviewer ACK review-handoff summary.
- Place it after the latest reviewer ACK review-decision panel.
- Consume only safe summary fields from status, diagnostics, nested diagnostics summaries, or Robot safe alias.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled when this panel is present.
- Fixture must include `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `source=software_proof`, `software_proof`, and `not_proven`.
- Do not expose raw artifacts, ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER parameters, credentials, local paths, complete logs, checksums, tracebacks, HIL/pass wording, route/elevator field-pass claims, true phone/browser proof, or delivery success claims.
- Keep technical comments in Chinese and above the repo's 20% meaningful-comment bar for touched code.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.json >/tmp/reviewer_ack_review_handoff_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff|ready_for_field_owner_reviewer_ack_followup_not_proven|needs_reviewer_handoff_reassignment_not_proven|needs_field_owner_ack_material_supplement_not_proven|rejected_unsafe_reviewer_ack_handoff_not_proven|blocked_missing_reviewer_ack_review_decision_not_proven|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D - Product Closeout Later

Owner role: `product-okr-owner`

Allowed files after Tasks A/B/C return:

- `sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/tech-done.md`
- `sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/side2side_check.md`
- `sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record worker file lists and validation snippets.
- State `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live evidence changes.
- State no OKR percentage lift.
- Preserve the proof boundary and false safety flags.
- Explain remaining O5, O1, route/elevator, phone/browser, and delivery proof gaps.

Acceptance commands:

```bash
test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/tech-done.md && test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/side2side_check.md && test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/final.md
rg -n "field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff|software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_gate|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Integration Order

1. Launch Task A, Task B, and Task C in parallel.
2. Require each worker to return changed files, validation output, failure analysis if any, and residual risk.
3. If any worker validation fails, return the issue to that owner before closeout.
4. Product Task D integrates evidence and updates closeout docs, `OKR.md`, and progress log.
5. Commit and push only after scoped validation passes and unrelated local churn is excluded.

## Planning-Phase Validation

Run after creating `pre_start.md`, `prd.md`, and `tech-plan.md`:

```bash
test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/pre_start.md
test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/prd.md
test -f sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff|Autonomy|Robot|Full-Stack" sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff
git diff --check -- sprints/2026.05.23_11-12_field-evidence-rerun-acceptance-owner-response-reviewer-ack-review-handoff
```
