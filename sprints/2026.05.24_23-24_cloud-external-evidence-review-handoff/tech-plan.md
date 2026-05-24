# Tech Plan: cloud external evidence review handoff

- sprint_type: epic
- target capability: `cloud_external_evidence_review_handoff`
- upstream capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_gate`
- expected closeout: `software_proof`, `not_proven`, `no OKR percentage lift`

## OKR 最低优先级核对

1. 当前 `OKR.md` §4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5。
3. 选择 Objective 5 的理由：用户要求优先推进完成度低的部分；上一轮 `cloud_external_evidence_review_decision` 已完成 review-decision 软件门，但还缺 owner/support/reviewer handoff，导致 future real external evidence 到达后仍缺下一步责任链。
4. 不提升 OKR 的理由：本机没有真实硬件，只有 Docker；本轮没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result、HIL、WAVE ROVER/UART proof、route/elevator field pass 或 delivery success。因此本轮只能是 `software_proof_docker_cloud_external_evidence_review_handoff_gate`，并明确 `no OKR percentage lift`。

## Implementation Shape

Create the next O5 software rung after `cloud_external_evidence_review_decision`: a handoff packet that preserves the source review decision and routes the result to field owner, support owner, and reviewer follow-up. The handoff must be metadata-only and fail closed.

Canonical handoff state should support these outcomes:

- `ready_for_owner_support_reviewer_handoff_not_proven`
- `needs_external_evidence_backfill_handoff_not_proven`
- `rejected_unsafe_external_evidence_handoff_not_proven`
- `blocked_missing_external_evidence_handoff_not_proven`
- `external_evidence_ref_mismatch_handoff_not_proven`

Required shared fields:

- `capability=cloud_external_evidence_review_handoff`
- `source_capability=cloud_external_evidence_review_decision`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_cloud_external_evidence_review_handoff_gate`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_true_phone_browser_proof=true`
- `okr_percentage_lift=false`
- `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`
- `pr5_status=hardware_material_pending`

## Interface Boundaries

- PC gate may consume only sanitized review-decision summaries or fixtures. It must not fetch public endpoints, call GitHub mutations, read secrets, or require network.
- Robot diagnostics may expose only a safe alias summary. It must not alter command safety, ACK/cursor state, ROS task execution, launch parameters, `/cmd_vel`, serial, UART, WAVE ROVER, or hardware config.
- `mobile/web` may render a read-only handoff panel only. It must not enable Start Delivery, Confirm Dropoff, Cancel, replay, resubmit, ACK lookup mutation, artifact upload/download, raw diagnostics fetch, or robot control paths.
- Docs updated during implementation must preserve the same evidence boundary and must not edit `OKR.md` until Product closeout.
- Technical code comments added during implementation must be Chinese and meet the project comment-ratio expectation where code is changed.

## Task A: User Touchpoint Full-Stack Engineer

**Goal:** Add a read-only phone/support panel for `cloud_external_evidence_review_handoff`.

**Allowed files:**

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`

**Must not touch:**

- Robot behavior code.
- Hardware/vendor docs or config.
- `OKR.md`.
- `docs/process/okr_progress_log.md`.

**Implementation requirements:**

1. Add a fixture with `robot_diagnostics_cloud_external_evidence_review_handoff_summary`.
2. Render a read-only panel named `cloud_external_evidence_review_handoff`.
3. Show source decision, handoff status, owner/support/reviewer route, next required evidence, `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, and false-state flags.
4. Keep all primary actions disabled through `primary_actions_enabled=false` and `safe_to_control=false`.
5. Document that this is Docker/local `software_proof`, not true phone/browser proof and not delivery success.

**Acceptance commands for Task A:**

```bash
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json >/tmp/cloud_external_evidence_review_handoff_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_handoff
rg -n "cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_gate|cloud_external_evidence_review_decision|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
```

## Task B: Robot Platform Engineer

**Goal:** Add the Robot diagnostics safe alias and behavior-side handoff metadata exposure.

**Allowed files:**

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

**Must not touch:**

- `mobile/web/*`.
- Hardware/vendor docs or config.
- Launch parameters.
- `OKR.md`.
- `docs/process/okr_progress_log.md`.

**Implementation requirements:**

1. Add `robot_diagnostics_cloud_external_evidence_review_handoff_summary` as a safe read-only diagnostics alias.
2. Accept sanitized `cloud_external_evidence_review_handoff` summaries from diagnostics/status payloads.
3. Preserve source capability `cloud_external_evidence_review_decision`.
4. Preserve `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
5. Reject or ignore raw command/control, secret, serial, UART, WAVE ROVER, `/cmd_vel`, ACK/cursor mutation, and success/completion claims.

**Acceptance commands for Task B:**

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_handoff
rg -n "robot_diagnostics_cloud_external_evidence_review_handoff_summary|cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_gate|cloud_external_evidence_review_decision|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift|/cmd_vel|serial|UART|WAVE ROVER" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

## Task C: Product Manager / OKR Owner

**Goal:** Close out the Epic after Task A and Task B return.

**Allowed files:**

- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-done.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/side2side_check.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

**Closeout requirements:**

1. Record the exact Task A/B changed files and validation outputs.
2. Confirm no product action enables Start Delivery, Confirm Dropoff, Cancel, ACK/cursor mutation, or robot control.
3. Update `OKR.md` and progress log conservatively: Objective 5 remains about 68% unless real external proof appears. Default expected result is `no OKR percentage lift`.
4. Explicitly state that `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live GitHub evidence proves otherwise.
5. State that the proof is Docker/local `software_proof`, not true phone/browser proof, not external proof, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, and not delivery success.

**Acceptance commands for Task C:**

```bash
rg -n "cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_gate|cloud_external_evidence_review_decision|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Parallel Dispatch Plan

After this planning task, start Task A and Task B in parallel because their write scopes are disjoint:

- Task A owns `mobile/web` plus product docs.
- Task B owns `onboard/src/ros2_trashbot_behavior` plus interface docs.

Task C waits for both implementation tasks and must not run early because it needs actual changed-file lists, validation logs, and final evidence boundaries.

## Planning Validation Commands

```bash
test -f sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/pre_start.md && test -f sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/prd.md && test -f sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_external_evidence_review_handoff|cloud_external_evidence_review_decision|software_proof_docker_cloud_external_evidence_review_handoff_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/pre_start.md sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/prd.md sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-plan.md
git diff --check -- sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/pre_start.md sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/prd.md sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-plan.md
```

## Risks

- The handoff could be misread as real external proof. Mitigation: every artifact must carry `software_proof_docker_cloud_external_evidence_review_handoff_gate` and `no OKR percentage lift`.
- The phone panel could be misread as true phone/browser proof. Mitigation: render read-only copy and preserve `not true phone/browser proof`.
- The unresolved PR #5 thread can pull the sprint into hardware work. Mitigation: use `PRRT_kwDOSWB9286CJ3tX` and `hardware_material_pending` only as evidence input, not as implementation target.
- Broad tests can waste the sprint. Mitigation: use only the fenced commands above plus scoped diff checks.

