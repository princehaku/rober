# Tech Plan - Cloud command lifecycle support owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%；Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，但只推进 Docker/local `software_proof` 的 cloud command lifecycle owner-response reviewer ACK intake rung。
3. 本 sprint 不提高 OKR 百分比。原因：本机仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser proof、verified terminal result、HIL、WAVE ROVER/UART proof 和真实 route/elevator field pass。
4. 不规划新的 PR #5 hardware-material governance rung：PR #5 已 closed/merged，Q/U resolved，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`。

## Architecture Boundary

The new capability extends the existing O5 chain:

`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`

The output must remain phone-safe and support-safe. It must not replay commands, resubmit commands, mutate ACK cursors, upload materials, perform GitHub mutations, fetch raw artifacts, trigger Nav2, touch WAVE ROVER/UART, or authorize robot control.

Required invariant strings:

- `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate`
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

- Add a read-only Robot/API summary for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`.
- Derive it only from safe owner-response review-handoff fields.
- Preserve one safe `command_id`, one safe `evidence_ref`, reviewer ACK status, source handoff status, owner/support/reviewer routing, ACK reasons, next required evidence, proof boundary, source boundary, and fail-closed flags.
- Reject or mark not_proven for missing safe IDs, conflicting refs, unsafe text, credentials, signed URLs, raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, ACK cursor changes, or control flags.
- Update `docs/product/remote_4g_mvp.md` with the proof boundary and non-claims.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md
```

### Task B - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake.json`
- `docs/product/mobile_user_flow.md`

Implementation scope:

- Add a read-only mobile panel for the reviewer ACK intake summary.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_summary` first, then only compatible safe fallback fields.
- Show reviewer ACK status, source handoff status, safe command id, safe `evidence_ref`, owner/support/reviewer routing, ACK reasons, next required evidence, proof boundary, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled; do not add replay/resubmit, ACK/cursor, material upload, review mutation, handoff mutation, GitHub mutation, diagnostics mutation, owner-response submission, raw artifact fetch, or robot control path.
- Update `docs/product/mobile_user_flow.md` with the same proof and non-claims.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake.json docs/product/mobile_user_flow.md
```

### Task C - Product Manager / OKR Owner Closeout Later

Allowed files:

- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Implementation scope:

- Record worker outputs, exact validation evidence, deviations, and remaining risk.
- Keep Objective 5 around 68% unless real external proof appears during implementation.
- Record that `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending` and this sprint is not PR #5 resolution.
- Preserve proof-boundary language across `OKR.md` and progress log.

Acceptance commands:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
```

## Parallel Dispatch Plan

Start two parallel implementation workers:

- Robot Platform Engineer for Task A.
- User Touchpoint Full-Stack Engineer for Task B.

Product closeout is sequenced after implementation evidence because it must not invent results.

## Interface Contract

Expected Robot summary fields:

- `capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
- `proof_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate`
- `reviewer_ack_status`
- `source_handoff_status`
- `safe_command_id`
- `evidence_ref`
- `ack_reasons`
- `owner_next_step`
- `support_next_step`
- `reviewer_next_step`
- `next_required_evidence`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed reviewer ACK statuses:

- `reviewer_acknowledged_not_proven`
- `reviewer_ack_needs_reassignment`
- `reviewer_ack_missing_material_not_proven`
- `blocked_missing_owner_response_review_handoff`
- `reviewer_ack_evidence_ref_mismatch`
- `reviewer_ack_rejected_unsafe`

Any unsupported or unsafe state must render blocked / not_proven and preserve disabled primary actions.

## Risks and Mitigations

- Risk: ACK wording implies verified terminal result. Mitigation: required `rg` strings include `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift`.
- Risk: Mobile fallback consumes raw diagnostic fields. Mitigation: only consume existing safe summaries; tests must cover unsafe/raw field rejection.
- Risk: This becomes another PR #5 hardware-material rung. Mitigation: PR #5 `PRRT_kwDOSWB9286CJ3tX` stays as `hardware_material_pending` context only; no hardware material action is in scope.
- Risk: Broad tests waste time or blur proof boundary. Mitigation: all acceptance commands are targeted and scoped.

## Planning-Task Validation

Planning docs are accepted when:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake
git diff --check -- sprints/2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-reviewer-ack-intake
```
