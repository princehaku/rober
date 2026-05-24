# Tech Plan - Cloud command lifecycle support owner-response reviewer ACK follow-up escalation status

- sprint_type: epic
- sprint: `2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate`
- implementation mode: two parallel Engineer owners, then Product closeout

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5，继续推进 O5 Docker-only 软件证明链路。
3. 本 sprint 不提升 OKR 百分比；原因是仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result、WAVE ROVER/UART/HIL、route/elevator field pass、PR #5 thread resolution 和 delivery success。
4. 本 sprint 不把 PR #5 `PRRT_kwDOSWB9286CJ3tX` / `hardware_material_pending` 当作再次消费的硬件 blocker；它只作为 follow-up escalation status 的 blocker field 和非声明边界。

## Architecture

本轮在上轮 `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff` 之后增加一个只读 follow-up escalation status rung。Robot/API 从 safe reviewer ACK review-handoff summary 派生 follow-up escalation summary；mobile/web 从 Robot diagnostics/status safe summary 渲染一个只读 panel。

不新增任何 robot command、ACK/cursor mutation、material upload、review mutation、handoff mutation、GitHub mutation、diagnostics mutation、owner-response submission、reviewer-ACK submission、raw artifact fetch、Nav2 trigger、WAVE ROVER/UART path 或 delivery-success inference。

## Interface Fields

Robot/API summary 必须输出或保留以下字段：

- `schema`: `trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary.v1`
- `capability`: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`
- `proof_boundary`: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate`
- `source_capability`: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`
- `source_proof_boundary`: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate`
- `safe_command_id`
- `evidence_ref`
- `source_review_handoff_status`
- `followup_status`
- `due_status`
- `followup_owner`
- `support_route`
- `reviewer_route`
- `escalation_route`
- `escalation_reason`
- `decision_reasons`
- `next_required_evidence`
- `blocker_status`: includes `hardware_material_pending`
- `pr_thread_id`: `PRRT_kwDOSWB9286CJ3tX`
- `delivery_success`: `false`
- `primary_actions_enabled`: `false`
- `safe_to_control`: `false`
- `terminal_result_verified`: `false`
- `phone_browser_proof`: `not true phone/browser proof`
- `okr_progress_effect`: `no OKR percentage lift`
- `non_claims`: includes `not verified terminal result`, `not true phone/browser proof`, `not delivery success`

Supported `followup_status` values:

- `reviewer_ack_followup_pending_not_proven`
- `reviewer_ack_followup_overdue_not_proven`
- `reviewer_ack_followup_escalated_not_proven`
- `reviewer_ack_followup_blocked_missing_material_not_proven`
- `ready_for_reviewer_followup_not_proven`
- `blocked_missing_source_reviewer_ack_review_handoff_not_proven`
- `reviewer_ack_followup_evidence_ref_mismatch_not_proven`
- `reviewer_ack_followup_rejected_unsafe_not_proven`

## Parallel Task A - Robot Platform Engineer

### Allowed File Scope

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status/tech-done.md`

### Required Work

1. Add Robot/API summary support for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`.
2. Source only from safe reviewer ACK review-handoff summary or compatible safe diagnostics/status summary.
3. Preserve same safe `command_id` and safe `evidence_ref`; mismatch must produce `reviewer_ack_followup_evidence_ref_mismatch_not_proven`.
4. Reject or block unsafe fields: raw command payload, Authorization, bearer token, signed URL, local path, traceback, checksum, complete artifact, ROS topic, `/cmd_vel`, serial/UART detail, WAVE ROVER detail, true-state flags, verified terminal result wording, or success wording.
5. Embed summary under:
   - `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`
   - `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary`
   - `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary`
6. Update `docs/product/remote_4g_mvp.md` with capability, schema, boundary, fields, status values, and non-claim boundary.
7. Update `tech-done.md` with files changed, validation output, failure定位 if any, and remaining risk.

### Interface Impact

- Adds read-only safe summary fields only.
- Does not change command execution, ACK posting, cursor advancement, replay semantics, owner-response submission, reviewer ACK submission, diagnostics mutation, material upload, GitHub mutation, ROS topics, Nav2 behavior, WAVE ROVER/UART behavior, or phone primary action enablement.
- Any unsafe source must fail closed with false-state flags preserved.

### Acceptance Commands

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior docs/product/remote_4g_mvp.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/product/remote_4g_mvp.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
```

## Parallel Task B - User Touchpoint Full-Stack Engineer

### Allowed File Scope

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status.json`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status/tech-done.md`

### Required Work

1. Add a read-only mobile panel for `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`.
2. Position it after `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`.
3. Read only safe Robot diagnostics/status summaries; do not fetch raw diagnostics or raw artifacts.
4. Display safe command id, safe `evidence_ref`, source review-handoff status, follow-up status, due status, follow-up owner, support/reviewer/escalation route, escalation reason, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, proof boundary and false-state flags.
5. Keep Start Delivery、Confirm Dropoff、Cancel disabled; do not add mutation or command controls.
6. Add fixture with `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not verified terminal result`, `not true phone/browser proof`, and `no OKR percentage lift`.
7. Update `docs/product/mobile_user_flow.md` with panel contract, status values, and non-claim boundary.
8. Update `tech-done.md` with files changed, validation output, failure定位 if any, and remaining risk.

### Interface Impact

- Adds one read-only mobile panel and fixture only.
- Does not change Start Delivery、Confirm Dropoff、Cancel gating.
- Does not introduce replay/resubmit, ACK/cursor mutation, material upload, review mutation, GitHub mutation, diagnostics mutation, owner-response submission, reviewer ACK submission, raw artifact fetch, route/elevator action, or robot control path.

### Acceptance Commands

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status.json >/tmp/cloud_command_lifecycle_reviewer_ack_followup_escalation_status.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status.json docs/product/mobile_user_flow.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
```

## Task C - Product Closeout

### Allowed File Scope

- `sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status/tech-done.md`
- `sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

### Required Work

1. Verify Robot and Full-Stack outputs preserve the same capability and proof boundary.
2. Confirm both surfaces preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not verified terminal result`, `not true phone/browser proof`, and `no OKR percentage lift`.
3. Record side-by-side evidence and final closeout.
4. If updating `OKR.md`, keep Objective 5 around 68% and explicitly state no percentage lift unless real external/cloud/terminal-result proof appeared outside this planning scope.

### Acceptance Commands

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior mobile/web docs/product sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- onboard/src/ros2_trashbot_behavior mobile/web docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status OKR.md docs/process/okr_progress_log.md
```

## Integration Acceptance

After both Engineer owners return, Product/Integrator must verify:

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not verified terminal result|not true phone/browser proof|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift" onboard/src/ros2_trashbot_behavior mobile/web docs/product sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- onboard/src/ros2_trashbot_behavior mobile/web docs/product/remote_4g_mvp.md docs/product/mobile_user_flow.md sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
```

## Non-Claim Boundary

- This is `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate` only.
- This is not verified terminal result.
- This is not true phone/browser proof.
- This is not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or external cloud proof.
- This is not WAVE ROVER/UART proof, HIL, Nav2/fixed-route runtime pass, route/elevator field pass, PR #5 resolved, delivery result, dropoff completion, cancel completion, delivery success, or OKR percentage lift.

## Planning Validation For This Task

The planning-only acceptance command is:

```bash
rg -n "sprint_type: epic|cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|no OKR percentage lift|OKR 最低优先级核对" sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- sprints/2026.05.24_19-20_cloud-command-lifecycle-support-owner-response-reviewer-ack-followup-escalation-status
```
