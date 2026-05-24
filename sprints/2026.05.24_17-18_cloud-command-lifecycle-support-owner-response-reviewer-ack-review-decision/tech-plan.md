# Tech Plan - Cloud command lifecycle support owner-response reviewer ACK review decision

- sprint_type: epic
- sprint: `2026.05.24_17-18_cloud-command-lifecycle-support-owner-response-reviewer-ack-review-decision`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%；Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，但只推进 Docker/local `software_proof` 的 cloud command lifecycle support owner-response reviewer ACK review-decision rung。
3. 本 sprint 不提高 OKR 百分比，预期结论是 `no OKR percentage lift`。原因：本机仍缺 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、true phone/browser proof、verified terminal result、HIL、WAVE ROVER/UART proof 和真实 route/elevator field pass。
4. 不规划新的硬件材料实现或 PR #5 hardware-material governance rung。PR #5 已 closed/merged，Q/U resolved，但 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`，必须保留为 blocker context。

## Architecture Boundary

The new capability extends the existing O5 support chain:

`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`

The output must remain phone-safe and support-safe. It must not replay commands, resubmit commands, mutate ACK cursors, upload materials, perform GitHub mutations, fetch raw artifacts, submit reviewer ACKs, trigger Nav2, touch WAVE ROVER/UART, or authorize robot control.

This is not a hardware task and does not require `docs/vendor/VENDOR_INDEX.md`, because the allowed implementation scope does not touch WAVE ROVER, ESP32, Orange Pi wiring, UART device names, baud rate, JSON motor commands, speed mapping, feedback protocol, pins, voltage, firmware, or mechanical dimensions.

Required invariant strings:

- `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`
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

- Add a read-only Robot/API summary for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`.
- Derive it only from safe reviewer ACK intake fields for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`.
- Preserve one safe `command_id`, one safe `evidence_ref`, reviewer ACK review decision, source ACK intake status, owner/support/reviewer routing, decision reasons, next required evidence, proof boundary, source boundary, PR #5 blocker context, and fail-closed flags.
- Supported review decisions should include accepted, needs reassignment, missing material, evidence-ref mismatch, unsafe/rejected, and blocked missing source ACK intake states, all marked not_proven.
- Reject or mark not_proven for missing safe IDs, conflicting refs, unsafe text, credentials, bearer tokens, signed URLs, raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, ACK cursor changes, reviewer-ACK mutation, GitHub mutation, or true-state control flags.
- Update `docs/product/remote_4g_mvp.md` with the proof boundary and non-claims.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md
```

### Task B - User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision.json`
- `docs/product/mobile_user_flow.md`

Implementation scope:

- Add a read-only mobile panel for the reviewer ACK review-decision summary.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_summary` first, then only compatible safe fallback fields.
- Show reviewer ACK review decision, source ACK intake status, safe command id, safe `evidence_ref`, owner/support/reviewer routing, decision reasons, next required evidence, blocker status, proof boundary, `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, `not verified terminal result`, and `no OKR percentage lift`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add replay/resubmit, ACK/cursor mutation, material upload, review mutation, handoff mutation, GitHub mutation, diagnostics mutation, owner-response submission, reviewer-ACK submission, raw artifact fetch, or robot control path.
- Update `docs/product/mobile_user_flow.md` with the same proof and non-claims.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision.json >/tmp/cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not true phone/browser proof|not verified terminal result|no OKR percentage lift|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision.json docs/product/mobile_user_flow.md
```

## Parallel Dispatch Plan

Start two parallel implementation workers in the same dispatch batch:

- Robot Platform Engineer for Task A.
- User Touchpoint Full-Stack Engineer for Task B.

The file scopes are disjoint except for interface expectations documented here. No Hardware Infra Engineer is needed because this sprint does not touch hardware facts or configuration. No Autonomy Algorithm Engineer is needed because this sprint does not touch Nav2, fixed-route runtime, route/elevator runtime, or field execution.

## Interface Contract

Expected Robot summary fields:

- `capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`
- `proof_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`
- `source_capability=cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
- `source_ack_intake_status`
- `reviewer_ack_review_decision`
- `safe_command_id`
- `evidence_ref`
- `decision_reasons`
- `owner_next_step`
- `support_next_step`
- `reviewer_next_step`
- `next_required_evidence`
- `pr5_review_thread=PRRT_kwDOSWB9286CJ3tX`
- `pr5_material_status=hardware_material_pending`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed reviewer ACK review decisions:

- `reviewer_ack_accepted_for_support_review_not_proven`
- `reviewer_ack_needs_reassignment_not_proven`
- `reviewer_ack_missing_material_not_proven`
- `reviewer_ack_evidence_ref_mismatch_not_proven`
- `reviewer_ack_rejected_unsafe_not_proven`
- `blocked_missing_reviewer_ack_intake_not_proven`

Any unsupported or unsafe state must render blocked / not_proven and preserve disabled primary actions.

## Risks And Mitigations

- Risk: review-decision wording implies verified terminal result. Mitigation: required `rg` strings include `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift`.
- Risk: Mobile fallback consumes raw diagnostic fields. Mitigation: consume only existing safe summaries or compatible safe fallback fields; focused tests must cover unsafe/raw field rejection.
- Risk: This becomes another PR #5 hardware-material rung. Mitigation: PR #5 `PRRT_kwDOSWB9286CJ3tX` stays as `hardware_material_pending` context only; no hardware material action is in scope.
- Risk: Broad tests waste time or blur proof boundary. Mitigation: all acceptance commands are targeted and scoped.

## Planning-Task Validation

Planning docs are accepted when:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|no OKR percentage lift" sprints/2026.05.24_17-18_cloud-command-lifecycle-support-owner-response-reviewer-ack-review-decision
git diff --check -- sprints/2026.05.24_17-18_cloud-command-lifecycle-support-owner-response-reviewer-ack-review-decision
```
