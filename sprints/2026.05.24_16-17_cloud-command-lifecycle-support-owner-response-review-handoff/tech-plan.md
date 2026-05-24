# Tech Plan - Cloud command lifecycle support owner-response review handoff

- sprint_type: epic
- sprint: `2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`
- execution mode: planning docs only in this task; implementation must be delegated later to worker subagents.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%；Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，继续 Docker/local O5 command lifecycle support branch from `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision` to `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`。
3. 本 sprint 不提高 OKR 百分比。原因：当前 Docker-only host 没有真实手机/browser、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、verified terminal result、HIL、route/elevator field pass 或 delivery success。
4. PR #7 当前 open 且无 review threads/comments；它不解除 Objective 5 外部证据缺口。
5. PR #5 已 merged/closed，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。本 sprint 不规划 PR #5 resolution 或硬件材料进展，只把该事实作为 proof-boundary guardrail。

## Architecture Boundary

The next capability extends the existing O5 support branch:

`cloud_command_lifecycle_replay_acceptance_packet` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`

The output must remain phone-safe and support-safe. It must not replay commands, resubmit commands, mutate ACK cursors, upload materials, perform GitHub mutations, fetch raw artifacts, trigger Nav2, touch WAVE ROVER/UART, or authorize robot control.

Required invariant strings:

- `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not verified terminal result`
- `not true phone/browser proof`
- `no OKR percentage lift`
- `PRRT_kwDOSWB9286CJ3tX`
- `hardware_material_pending`

## Parallel Implementation Tracks

Task A and Task B can run in parallel later because they own disjoint files. Task C is sequenced after A/B because Product closeout must cite actual implementation and validation evidence.

### Task A - Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`

Implementation scope:

- Add a safe Robot/API summary/status/diagnostics embedding for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`.
- Derive it only from safe review-decision / owner-response / support-handoff fields.
- Preserve safe `command_id`, safe `evidence_ref`, review decision, handoff owner, handoff reason, owner response status, next required evidence, blocker summary, source boundary, proof boundary, and false flags.
- Reject or mark not_proven for missing safe IDs, conflicting refs, unsafe text, credentials, bearer tokens, signed URLs, raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, ACK cursor changes, or control flags.
- Update `docs/product/remote_4g_mvp.md` with the proof boundary and non-claims.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|no OKR percentage lift" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md
```

### Task B - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff.json`
- `docs/product/mobile_user_flow.md`

Implementation scope:

- Add a read-only mobile panel after the existing review-decision panel.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_summary` first, then only compatible safe fallback fields.
- Show review decision, handoff owner, handoff reason, owner response status, safe command id, safe `evidence_ref`, next required evidence, blocker summary, proof boundary, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled; do not add replay/resubmit, ACK/cursor, material upload, review mutation, GitHub mutation, diagnostics mutation, owner-response submission, raw artifact fetch, or robot control path.
- Update `docs/product/mobile_user_flow.md` with the same proof and non-claims.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff.json docs/product/mobile_user_flow.md
```

### Task C - Product Manager / OKR Owner Closeout Later

Allowed files:

- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff/tech-done.md`
- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff/side2side_check.md`
- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation scope:

- Record Task A/B changed files, exact validation outputs, deviations, and remaining risk.
- Keep Objective 5 around 68% unless real external proof appears during implementation.
- Record that `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` and this sprint is not PR #5 resolution.
- Preserve `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`, `not true phone/browser proof`, and `no OKR percentage lift` across `OKR.md` and progress log.

Acceptance commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate|not true phone/browser proof|no OKR percentage lift|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff OKR.md docs/process/okr_progress_log.md
```

## Interface Contract

Expected Robot summary fields:

- `capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`
- `proof_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`
- `source_capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision`
- `review_decision`
- `handoff_owner`
- `handoff_reason`
- `owner_response_status`
- `safe_command_id`
- `evidence_ref`
- `next_required_evidence`
- `blocker_summary`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed review-handoff states:

- `ready_for_support_handoff`
- `ready_for_owner_followup`
- `missing_materials`
- `rejected_materials`
- `unsafe_materials`
- `blocked_pending_owner`

Any unsupported or unsafe state must render blocked / not_proven and preserve disabled primary actions.

## Risks And Mitigations

- Risk: Owner-response review-handoff copy implies verified terminal result. Mitigation: required `rg` strings include `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift`.
- Risk: Mobile fallback consumes raw diagnostic fields. Mitigation: only consume safe summaries; tests must cover unsafe/raw field rejection.
- Risk: This becomes PR #5 resolution by wording drift. Mitigation: PR #5 `PRRT_kwDOSWB9286CJ3tX` stays unresolved / `hardware_material_pending`; no hardware material action is in scope.
- Risk: Broad tests waste time or blur proof boundary. Mitigation: all acceptance commands are targeted and scoped.

## Planning-Task Validation

This planning task itself is accepted when:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate|not true phone/browser proof|no OKR percentage lift" sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff
git diff --check -- sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff
```
