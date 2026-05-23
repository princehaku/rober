# Verified Terminal Result Material Owner Response Reviewer ACK Follow-up Escalation Status Tech Plan

Run time: 2026-05-24 02:03 Asia/Shanghai

## Sprint Type

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的最低目标，但只做 `verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status`，用于暴露 follow-up escalation status 和真实材料缺口。
3. 本 sprint 不提升 Objective 5 完成度。当前主机是 Docker-only，没有真实硬件、真实 4G/公网/OSS/CDN/生产 DB/queue、真实手机浏览器、真实 route/elevator field 或 HIL；因此本轮必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和 `no OKR percentage lift`。
4. 最新 final 的红线继续生效：`Do not repeat another local-only metadata wrapper as OKR progress`。本轮只能把 unresolved blocker、owner/reviewer route、due/overdue/escalated state 和 next required evidence 做成可复账状态门。

## Architecture

Capability: `verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status`

Evidence boundary: `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`

Data flow:

1. Autonomy / PC gate consumes prior safe reviewer ACK review-handoff metadata or a safe fixture.
2. PC gate emits a sanitized summary with unresolved blocker, follow-up state, owner route, reviewer route, support route, escalation reason, due/overdue/escalated status, next required evidence, and proof boundary flags.
3. Robot diagnostics safe alias exposes only the sanitized summary to robot/operator surfaces.
4. `mobile/web` displays the alias as a read-only panel; all primary actions stay disabled.
5. Product closeout records software-proof boundary and no OKR lift after engineer validation.

## Parallel Owner Split

### Task A: Autonomy / PC Evidence Gate

Owner: Autonomy Algorithm Engineer

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py`
- `pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py`
- `pc-tools/README.md`
- `docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.md`

Implementation requirements:

- Emit schema `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1`.
- Emit summary schema `trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1`.
- Emit boundary `software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Preserve PR #5 thread `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending`.
- Model follow-up states: `pending`, `due`, `overdue`, `escalated`, `blocked_missing_real_materials`.
- Fail closed on success wording, control flags, missing blocker identity, missing next required evidence, missing owner/reviewer route, unsafe copy, raw paths, credentials, ROS topic exposure, `/cmd_vel`, UART/serial details, ACK mutation hints, and robot command hints.

Acceptance commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_autonomy python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_autonomy python3 -m unittest pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|hardware_material_pending|overdue|escalated" pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.md
git diff --check -- pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.md
```

### Task B: Robot Diagnostics Safe Alias

Owner: Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Implementation requirements:

- Add `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`.
- Consume only sanitized PC summary fields.
- Preserve read-only semantics and never enable command/control hints.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Include `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, owner/support/reviewer route, due/overdue/escalated state, and next required evidence.
- Reject raw artifacts, credentials, local paths, raw robot responses, ROS topics, `/cmd_vel`, UART/serial details, ACK payloads, cursor values, diagnostics fetch mutation hints, and robot command hints.

Acceptance commands:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_robot python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_robot python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary|verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|hardware_material_pending|overdue|escalated" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### Task C: Full-Stack Mobile Read-only Panel

Owner: User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only panel for `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`.
- Show blocker identity, follow-up state, owner route, support route, reviewer route, due/overdue/escalated state, escalation reason, next required evidence, and safe copy.
- Preserve disabled Start Delivery, Confirm Dropoff, and Cancel behavior.
- Preserve `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Avoid success wording, control authorization, upload/procurement/review actions, raw JSON, raw artifact paths, credentials, ROS topics, `/cmd_vel`, UART/serial details, ACKs, cursors, diagnostics fetch mutation hints, and robot commands.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json >/tmp/rober_followup_mobile_fixture.json
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_mobile python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary|verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|hardware_material_pending|overdue|escalated" mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

### Task D: Product Closeout

Owner: Product Manager / OKR Owner

Allowed files after Tasks A-C return evidence:

- `sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/tech-done.md`
- `sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record engineer file changes, validation evidence, failures, fixes, and remaining risks.
- Confirm Objective 5 remains about 68% and `no OKR percentage lift` unless real external/material evidence arrives.
- Confirm `Do not repeat another local-only metadata wrapper as OKR progress`.
- Confirm PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless GitHub reviewer state actually changes.
- Confirm `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.

Acceptance commands:

```bash
test -f sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/tech-done.md
test -f sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/side2side_check.md
test -f sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status/final.md
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift|Do not repeat another local-only metadata wrapper" OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.24_02-03_verified-terminal-result-material-owner-response-reviewer-ack-followup-escalation-status
```

## Integration Acceptance

After Tasks A-C finish, the integration owner must run:

```bash
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_integration python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONPYCACHEPREFIX=/tmp/rober_pycache_followup_integration python3 -m unittest pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json >/tmp/rober_followup_mobile_fixture_integration.json
rg -n "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status|software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate|robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary|Objective 5|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|hardware_material_pending|overdue|escalated|no OKR percentage lift" pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product
git diff --check -- pc-tools/evidence/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/evidence/test_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.py pc-tools/README.md docs/interfaces/verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md mobile/web/app.js mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

## Proof Boundary

This sprint can prove only local schema, fail-closed diagnostics, and read-only UI behavior. It is not real terminal result, not O5 external proof, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not route/elevator field pass, not Nav2/fixed-route runtime pass, not HIL, not WAVE ROVER/UART proof, not LiDAR/ToF installed proof, not PR #5 resolved, and not delivery success.
