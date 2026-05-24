# Tech Plan - Cloud command lifecycle support owner-response review decision

- sprint_type: epic
- sprint: `2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate`
- execution mode: planning docs only in this task; implementation must be delegated to worker subagents.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%；Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，但只推进 Docker/local `software_proof` 的 cloud command lifecycle owner-response review-decision rung。
3. 本 sprint 不提高 OKR 百分比。原因：本机仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser proof、verified terminal result、HIL 和真实 route/elevator field pass。
4. 不规划新的 PR #5 hardware-material governance rung：PR #5 已 closed/merged，Q/U resolved，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，且该 blocker 已被连续消费两轮；本 sprint 只保留该事实作为边界。

## Architecture Boundary

The next capability must extend the existing O5 chain:

`cloud_command_lifecycle_replay_acceptance_packet` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`

The output must remain phone-safe and support-safe. It must not replay commands, resubmit commands, mutate ACK cursors, upload materials, perform GitHub mutations, fetch raw artifacts, trigger Nav2, touch WAVE ROVER/UART, or authorize robot control.

Required invariant strings:

- `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not verified terminal result`
- `not true phone/browser proof`
- `no OKR percentage lift`
- `PRRT_kwDOSWB9286CJ3tX`
- `hardware_material_pending`

## Owner / File Split

### Task A - Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`

Implementation scope:

- Add a read-only Robot/API summary for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`.
- Derive it only from safe owner-response intake / support handoff fields.
- Preserve one safe `command_id`, one safe `evidence_ref`, review decision, reasons, response status, next required evidence, proof boundary, source boundary, and fail-closed flags.
- Reject or mark not_proven for missing safe IDs, conflicting refs, unsafe text, credentials, signed URLs, raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, ACK cursor changes, or control flags.
- Update `docs/product/remote_4g_mvp.md` with the proof boundary and non-claims.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md
```

### Task B - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision.json`
- `docs/product/mobile_user_flow.md`

Implementation scope:

- Add a read-only mobile panel for the review-decision summary.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_summary` first, then only compatible safe fallback fields.
- Show review decision, response status, safe command id, safe `evidence_ref`, next required evidence, proof boundary, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled; do not add replay/resubmit, ACK/cursor, material upload, review mutation, GitHub mutation, diagnostics mutation, owner-response submission, raw artifact fetch, or robot control path.
- Update `docs/product/mobile_user_flow.md` with the same proof and non-claims.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision.json docs/product/mobile_user_flow.md
```

### Task C - Product Manager / OKR Owner Closeout Later

Allowed files:

- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/tech-done.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/side2side_check.md`
- `sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation scope:

- Record worker outputs, exact validation evidence, deviations, and remaining risk.
- Keep Objective 5 around 68% unless real external proof appears during implementation.
- Record that `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending` and this sprint is not PR #5 resolution.
- Preserve proof-boundary language across `OKR.md` and progress log.

Acceptance commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision OKR.md docs/process/okr_progress_log.md
```

## Parallel Dispatch Plan

After this planning-only task, implementation should start 2-3 parallel workers:

- Robot Platform Engineer for Task A.
- User Touchpoint Full-Stack Engineer for Task B.
- Product Manager / OKR Owner for Task C only after Task A/B return, unless the runtime supports a closeout worker that waits on implementation evidence.

Task A and Task B own disjoint product-code files and can run in parallel. Product closeout is sequenced after implementation evidence because it must not invent results.

## Interface Contract

Expected Robot summary fields:

- `capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`
- `proof_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate`
- `review_decision`
- `owner_response_status`
- `decision_reasons`
- `safe_command_id`
- `evidence_ref`
- `next_required_evidence`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed review decisions:

- `accepted_for_followup`
- `missing_materials`
- `rejected_materials`
- `unsafe_materials`
- `blocked_pending_owner`

Any unsupported or unsafe state must render blocked / not_proven and preserve disabled primary actions.

## Risks and Mitigations

- Risk: Owner-response review-decision copy implies verified terminal result. Mitigation: required `rg` strings include `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift`.
- Risk: Mobile fallback consumes raw diagnostic fields. Mitigation: only consume existing safe summaries; tests must cover unsafe/raw field rejection.
- Risk: This becomes a third PR #5 material-governance rung. Mitigation: PR #5 `PRRT_kwDOSWB9286CJ3tX` stays as `hardware_material_pending` context only; no hardware material action is in scope.
- Risk: Broad tests waste time or blur proof boundary. Mitigation: all acceptance commands are targeted and scoped.

## Planning-Task Validation

This planning task itself is accepted when:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision
git diff --check -- sprints/2026.05.24_14-15_cloud-command-lifecycle-support-owner-response-review-decision
```
