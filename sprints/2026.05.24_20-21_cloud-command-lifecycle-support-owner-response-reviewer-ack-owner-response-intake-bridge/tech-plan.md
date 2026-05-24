# Tech Plan - Cloud command lifecycle support owner-response reviewer ACK owner-response intake bridge

- sprint_type: epic
- sprint: `2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`
- implementation mode: Task A and Task B run in parallel, then Task C Product Closeout / Integration Validation

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，目标是 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`。
3. 本 sprint 仅为 Docker/local regression guard，不提高百分比；必须继续记录 `no OKR percentage lift`。
4. 不提高百分比的原因是仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result、WAVE ROVER/UART/HIL、route/elevator field pass、PR #5 thread resolution 和 delivery success。
5. 本 sprint 不把 PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending` 当作再次消费的硬件 blocker；它只作为 owner-response intake bridge 的 blocker field 和非声明边界。

## Architecture

本轮在上一轮 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status` 之后增加一个 owner-response intake bridge。Robot/API 从 safe reviewer ACK follow-up escalation summary 派生 bridge summary；mobile/web 从 Robot diagnostics/status safe summary 渲染只读 bridge 状态，并把它语义上接回 owner-response intake 主线。

这不是新增独立 UI wrapper。它不新增 robot command、ACK/cursor mutation、material upload、review mutation、handoff mutation、GitHub mutation、diagnostics mutation、owner-response submission、reviewer-ACK submission、raw artifact fetch、Nav2 trigger、WAVE ROVER/UART path 或 delivery-success inference。

## Interface Fields

Robot/API summary 必须输出或保留以下字段：

- `schema`: `trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary.v1`
- `capability`: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`
- `proof_boundary`: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`
- `source_capability`: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`
- `source_proof_boundary`: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate`
- `source`: `software_proof`
- `safe_command_id`
- `evidence_ref`
- `source_followup_status`
- `bridge_status`
- `owner_response_intake_readiness`
- `accepted_materials`
- `missing_materials`
- `rejected_materials`
- `unsafe_materials`
- `blocked_materials`
- `owner_route`
- `support_route`
- `reviewer_route`
- `next_required_evidence`
- `blocker_status`: includes `hardware_material_pending`
- `pr_thread_id`: `PRRT_kwDOSWB9286CJ3tX`
- `not_proven`: `true`
- `delivery_success`: `false`
- `primary_actions_enabled`: `false`
- `safe_to_control`: `false`
- `terminal_result_verified`: `false`
- `phone_browser_proof`: `not true phone/browser proof`
- `okr_progress_effect`: `no OKR percentage lift`
- `non_claims`: includes `not verified terminal result`, `not true phone/browser proof`, `not delivery success`

Supported `bridge_status` values:

- `accepted_for_owner_response_intake_bridge_not_proven`
- `owner_response_intake_bridge_missing_owner_material_not_proven`
- `owner_response_intake_bridge_rejected_unsafe_not_proven`
- `owner_response_intake_bridge_blocked_hardware_material_pending_not_proven`
- `blocked_missing_source_reviewer_ack_followup_escalation_status_not_proven`
- `owner_response_intake_bridge_evidence_ref_mismatch_not_proven`
- `owner_response_intake_bridge_source_not_ready_not_proven`

## Parallel Rule

Task A 和 Task B 可并行，且必须并行派发：Robot 文件范围与 mobile/web 文件范围互不重叠。Task C 在 A/B 后收口，不能提前改 `OKR.md` 或 `docs/process/okr_progress_log.md`。

## Task A - Robot Platform Engineer

### Allowed File Scope

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge/tech-done.md`

### Required Work

1. Add Robot/API summary support for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`.
2. Source only from safe reviewer ACK follow-up escalation status summary or compatible safe diagnostics/status summary.
3. Preserve same safe `command_id` and safe `evidence_ref`; mismatch must produce `owner_response_intake_bridge_evidence_ref_mismatch_not_proven`.
4. Reject or block unsafe fields: raw command payload, Authorization, bearer token, signed URL, local path, traceback, checksum, complete artifact, ROS topic, `/cmd_vel`, serial/UART detail, WAVE ROVER detail, true-state flags, verified terminal result wording, success wording, owner-response submission payload, or raw reviewer material.
5. Embed summary under:
   - `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`
   - `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary`
   - `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary`
6. Update `docs/product/remote_4g_mvp.md` with capability, schema, boundary, fields, status values, bridge-to-owner-response-intake semantics, and non-claim boundary.
7. Update `tech-done.md` with files changed, validation output, failure定位 if any, and remaining risk.

### Interface Boundary

- Adds read-only safe summary fields only.
- Does not change command execution, ACK posting, cursor advancement, replay semantics, owner-response submission, reviewer ACK submission, diagnostics mutation, material upload, GitHub mutation, ROS topics, Nav2 behavior, WAVE ROVER/UART behavior, or phone primary action enablement.
- Any unsafe source must fail closed with `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` preserved.
- Must not modify hardware/vendor files.

### Acceptance Commands

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
```

## Task B - User Touchpoint Full-Stack Engineer

### Allowed File Scope

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge/tech-done.md`

### Required Work

1. Add read-only mobile consumption for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge`.
2. Position it after `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`, and make the copy clear that it bridges back to owner-response intake rather than creating a new independent wrapper.
3. Read only safe Robot diagnostics/status summaries; do not fetch raw diagnostics or raw artifacts.
4. Display safe command id, safe `evidence_ref`, source follow-up status, bridge status, owner-response intake readiness, accepted/missing/rejected/unsafe/blocked classifications, owner/support/reviewer route, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, proof boundary and false-state flags.
5. Keep Start Delivery、Confirm Dropoff、Cancel disabled; do not add mutation or command controls.
6. Add fixture with `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not verified terminal result`, `not true phone/browser proof`, and `no OKR percentage lift`.
7. Update `docs/product/mobile_user_flow.md` with bridge contract, status values, owner-response intake semantics, and non-claim boundary.
8. Update `tech-done.md` with files changed, validation output, failure定位 if any, and remaining risk.

### Interface Boundary

- Adds one read-only mobile bridge panel/consumer and fixture only.
- Does not change Start Delivery、Confirm Dropoff、Cancel gating.
- Does not introduce replay/resubmit, ACK/cursor mutation, material upload, review mutation, GitHub mutation, diagnostics mutation, owner-response submission, reviewer ACK submission, raw artifact fetch, route/elevator action, or robot control path.
- Must not modify hardware/vendor files.

### Acceptance Commands

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge.json >/tmp/cloud_command_lifecycle_reviewer_ack_owner_response_intake_bridge.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge.json docs/product/mobile_user_flow.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
```

## Task C - Product Closeout / Integration Validation

### Allowed File Scope

- `sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge/tech-done.md`
- `sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge/side2side_check.md`
- `sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

### Required Work

1. Verify Robot and Full-Stack outputs preserve the same capability and proof boundary.
2. Confirm both surfaces preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not verified terminal result`, `not true phone/browser proof`, and `no OKR percentage lift`.
3. Confirm Task A and Task B did not modify hardware/vendor files, did not trigger GitHub mutation, and did not add robot control actions.
4. Record side-by-side evidence and final closeout.
5. If updating `OKR.md`, keep Objective 5 around 68% and explicitly state no percentage lift unless real external/cloud/terminal-result proof appeared outside this planning scope.

### Acceptance Commands

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior mobile/web docs/product sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
git diff --check -- onboard/src/ros2_trashbot_behavior mobile/web docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge OKR.md docs/process/okr_progress_log.md
```

## Integration Acceptance

After both Engineer owners return, Product/Integrator must verify:

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior mobile/web docs/product sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
git diff --check -- onboard/src/ros2_trashbot_behavior mobile/web docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
```

## Non-Claim Boundary

- This is `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate` only.
- This is not verified terminal result.
- This is not true phone/browser proof.
- This is not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or external cloud proof.
- This is not WAVE ROVER/UART proof, HIL, Nav2/fixed-route runtime pass, route/elevator field pass, PR #5 resolved, delivery result, dropoff completion, cancel completion, delivery success, or OKR percentage lift.
- This does not modify hardware/vendor files, does not trigger GitHub mutation, and does not add robot control actions.

## Planning Validation For This Task

The planning-only acceptance command is:

```bash
rg -n "sprint_type: epic|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate|Objective 5|OKR 最低优先级核对|Task A|Task B|Task C|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
git diff --check -- sprints/2026.05.24_20-21_cloud-command-lifecycle-support-owner-response-reviewer-ack-owner-response-intake-bridge
```
