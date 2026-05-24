# Tech Plan: cloud external evidence review handoff followup escalation status

- sprint_type: epic
- target capability: `cloud_external_evidence_review_handoff_followup_escalation_status`
- upstream capability: `cloud_external_evidence_review_handoff`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`
- expected closeout: `software_proof`, `not_proven`, `no OKR percentage lift`

## OKR 最低优先级核对

1. 当前 `OKR.md` §4.1 里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5。
3. 选择 Objective 5 的理由：用户要求优先推进完成度低的部分；上一轮 `cloud_external_evidence_review_handoff` 已完成 owner/support/reviewer handoff 软件门，但还缺 follow-up due status、blocked reason、owner action 和 CEO escalation recommendation，导致 handoff 可能停在无人跟进状态。
4. 不提升 OKR 的理由：本机没有真实硬件，只有 Docker；本轮没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、true phone/browser proof、verified terminal result、HIL、WAVE ROVER/UART proof、route/elevator field pass 或 delivery success。因此本轮只能是 `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`，并明确 `no OKR percentage lift`。

## Implementation Shape

Create the next O5 software rung after `cloud_external_evidence_review_handoff`: a follow-up escalation status packet that preserves the source handoff, computes or records follow-up due state, names blocked reasons, assigns owner/support/reviewer actions, and recommends whether CEO escalation is needed.

Canonical follow-up states should include:

- `followup_pending_not_proven`
- `followup_due_soon_not_proven`
- `followup_overdue_not_proven`
- `followup_blocked_missing_external_evidence_not_proven`
- `followup_escalated_to_ceo_not_proven`
- `ready_for_real_external_evidence_followup_not_proven`
- `followup_evidence_ref_mismatch_not_proven`
- `followup_rejected_unsafe_material_not_proven`

Required shared fields:

- `capability=cloud_external_evidence_review_handoff_followup_escalation_status`
- `source_capability=cloud_external_evidence_review_handoff`
- `upstream_capability=cloud_external_evidence_review_decision`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `not_true_phone_browser_proof=true`
- `okr_percentage_lift=false`
- `pr5_thread_id=PRRT_kwDOSWB9286CJ3tX`
- `pr5_status=hardware_material_pending`
- `ceo_escalation_recommendation` with a safe enum, not free-form secrets or raw artifacts.

## Interface Boundaries

- PC evidence gate may consume only sanitized handoff summaries or fixtures. It must not fetch public endpoints, call GitHub mutations, read secrets, upload materials, or require network.
- Robot diagnostics may expose only a safe alias summary. It must not alter command safety, ACK/cursor state, ROS task execution, launch parameters, `/cmd_vel`, serial, UART, WAVE ROVER, or hardware config.
- `mobile/web` may render a read-only follow-up status panel only. It must not enable Start Delivery, Confirm Dropoff, Cancel, replay, resubmit, ACK lookup mutation, artifact upload/download, raw diagnostics fetch, reviewer mutation, GitHub mutation, or robot control paths.
- Docs updated during implementation must preserve the same evidence boundary and must not edit `OKR.md` until Product closeout.
- Technical code comments added during implementation must be Chinese and meet the project comment-ratio expectation where code is changed.

## Parallelism Decision

Task A and Task B have disjoint write scopes and can be dispatched in parallel:

- Task A owns PC evidence gate, `mobile/web`, fixtures, tests, and product docs.
- Task B owns Robot diagnostics safe alias, behavior tests, and interface docs.

Task C waits until both Task A and Task B return because it needs actual changed-file lists, validation logs, final proof boundary, and any deviations before updating `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.

## Task A: User Touchpoint Full-Stack Engineer

**Goal:** Add the PC evidence gate and read-only phone/support panel for `cloud_external_evidence_review_handoff_followup_escalation_status`.

**Allowed files:**

- `pc-tools/evidence/cloud_external_evidence_review_handoff_followup_escalation_status.py`
- `pc-tools/evidence/test_cloud_external_evidence_review_handoff_followup_escalation_status.py`
- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status.json`
- `docs/product/mobile_user_flow.md`
- `docs/product/remote_4g_mvp.md`

**Must not touch:**

- Robot behavior code.
- Hardware/vendor docs or config.
- Launch parameters.
- `OKR.md`.
- `docs/process/okr_progress_log.md`.
- Any real credential, `.env`, production endpoint, or GitHub mutation path.

**Implementation requirements:**

1. Add a PC evidence gate that accepts sanitized `cloud_external_evidence_review_handoff` input and emits `cloud_external_evidence_review_handoff_followup_escalation_status` safe output.
2. Add a fixture with `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary`.
3. Render a read-only panel named `cloud_external_evidence_review_handoff_followup_escalation_status`.
4. Show source handoff status, due status, blocked reason, owner action, support action, reviewer action, CEO escalation recommendation, next required evidence, `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, and false-state flags.
5. Keep all primary actions disabled through `primary_actions_enabled=false` and `safe_to_control=false`.
6. Document that this is Docker/local `software_proof`, not true phone/browser proof, not external proof, not HIL, and not delivery success.
7. Keep code comments in Chinese where comments are needed for non-obvious safety logic.

**Acceptance commands for Task A:**

```bash
python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_handoff_followup_escalation_status.py
python3 -m unittest pc-tools/evidence/test_cloud_external_evidence_review_handoff_followup_escalation_status.py
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status.json >/tmp/cloud_external_evidence_review_handoff_followup_escalation_status_fixture.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_handoff_followup_escalation_status
rg -n "cloud_external_evidence_review_handoff_followup_escalation_status|cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence mobile/web docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
git diff --check -- pc-tools/evidence/cloud_external_evidence_review_handoff_followup_escalation_status.py pc-tools/evidence/test_cloud_external_evidence_review_handoff_followup_escalation_status.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status.json docs/product/mobile_user_flow.md docs/product/remote_4g_mvp.md
```

## Task B: Robot Platform Engineer

**Goal:** Add the Robot diagnostics safe alias and interface documentation for follow-up escalation status metadata.

**Allowed files:**

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

**Must not touch:**

- `pc-tools/evidence/*`.
- `mobile/web/*`.
- Product docs owned by Task A.
- Hardware/vendor docs or config.
- Launch parameters.
- `OKR.md`.
- `docs/process/okr_progress_log.md`.

**Implementation requirements:**

1. Add `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary` as a safe read-only diagnostics alias.
2. Accept sanitized `cloud_external_evidence_review_handoff_followup_escalation_status` summaries from diagnostics/status payloads.
3. Preserve source capability `cloud_external_evidence_review_handoff` and upstream capability `cloud_external_evidence_review_decision`.
4. Preserve `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
5. Reject or ignore raw command/control, secret, serial, UART, WAVE ROVER, `/cmd_vel`, ACK/cursor mutation, production endpoint, signed URL, and success/completion claims.
6. Keep comments in Chinese where safety filtering or alias selection is not self-evident.

**Acceptance commands for Task B:**

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_handoff_followup_escalation_status
rg -n "robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary|cloud_external_evidence_review_handoff_followup_escalation_status|cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|/cmd_vel|serial|UART|WAVE ROVER" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_runtime_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md
```

## Task C: Product Manager / OKR Owner

**Goal:** Close out the Epic after Task A and Task B return.

**Allowed files:**

- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-done.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

**Must not touch before Task A/B finish:**

- Product code.
- Test code.
- Hardware config.
- Launch files.
- Any unrelated sprint folder.

**Closeout requirements:**

1. Record exact Task A/B changed files and validation outputs.
2. Confirm no product action enables Start Delivery, Confirm Dropoff, Cancel, ACK/cursor mutation, material upload, GitHub mutation, or robot control.
3. Update `OKR.md` and progress log conservatively: Objective 5 remains about 68% unless real external proof appears. Default expected result is `no OKR percentage lift`.
4. Explicitly state that `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live GitHub evidence proves otherwise.
5. State that the proof is Docker/local `software_proof`, not true phone/browser proof, not external proof, not HIL, not WAVE ROVER/UART proof, not route/elevator field pass, not verified terminal result, and not delivery success.
6. Check that docs under `docs/` were synchronized by Task A/B for their surfaces before accepting closeout.

**Acceptance commands for Task C:**

```bash
rg -n "cloud_external_evidence_review_handoff_followup_escalation_status|cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Planning Validation Commands

```bash
test -f sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/pre_start.md && test -f sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/prd.md && test -f sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_external_evidence_review_handoff_followup_escalation_status|cloud_external_evidence_review_handoff|software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|Docker|software_proof|not true phone/browser|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/pre_start.md sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/prd.md sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-plan.md
git diff --check -- sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/pre_start.md sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/prd.md sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-plan.md
```

## Risks

- The follow-up escalation status could be misread as real external proof. Mitigation: every artifact must carry `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate` and `no OKR percentage lift`.
- The mobile panel could be misread as true phone/browser proof. Mitigation: render read-only copy and preserve `not true phone/browser proof`.
- The unresolved PR #5 thread can pull the sprint into hardware work. Mitigation: use `PRRT_kwDOSWB9286CJ3tX` and `hardware_material_pending` only as evidence input, not as implementation target.
- Broad tests can waste the sprint. Mitigation: use only the fenced commands above plus scoped `git diff --check`.
- Docker/local proof can look complete because the status chain is well structured. Mitigation: Product closeout must explicitly keep `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `no OKR percentage lift`.
