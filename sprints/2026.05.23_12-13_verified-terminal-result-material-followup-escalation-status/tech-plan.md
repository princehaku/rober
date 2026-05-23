# Verified Terminal Result Material Followup Escalation Status Tech Plan

Run time: 2026-05-23 12:05 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的下一步可行动 terminal-result material 路径：`verified_terminal_result_material_followup_escalation_status`。
3. 本 sprint 承接 `verified_terminal_result_material_review_handoff`，把 owner handoff / next required evidence 转成 field owner / support / reviewer 可执行的 follow-up escalation status。
4. 本 sprint 不是 generic blocker wrapper，不继续消费 field-evidence rerun 缺真实材料链，也不关闭 PR #5 `PRRT_kwDOSWB9286CJ3tX`。
5. 本 sprint 不提升 Objective 5 百分比，除非真实 terminal delivery/dropoff/cancel result material 或真实 O5 external evidence 在后续 closeout 前到位并按同一 safe `evidence_ref` 验证通过。默认 closeout 口径是 `no OKR percentage lift`。

## Architecture Decision

`verified_terminal_result_material_followup_escalation_status` is a three-surface software-proof gate:

1. PC CLI reads a prior `verified_terminal_result_material_review_handoff` artifact, summary, Robot alias, or compatible nested diagnostics/status summary and emits sanitized follow-up escalation status.
2. Robot diagnostics/status consumes the follow-up summary and exposes a safe alias for support/mobile.
3. Mobile/web renders a read-only follow-up escalation status panel for field owner / support / reviewer.

Every surface must preserve:

- `capability=verified_terminal_result_material_followup_escalation_status`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`
- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

## Interface Contract

Supported input source schemas and aliases:

- `trashbot.verified_terminal_result_material_review_handoff.v1`
- `trashbot.verified_terminal_result_material_review_handoff_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1`
- compatible nested diagnostics/status summaries that preserve the same safe `evidence_ref`

Expected output schemas:

- Artifact: `trashbot.verified_terminal_result_material_followup_escalation_status.v1`
- Summary: `trashbot.verified_terminal_result_material_followup_escalation_status_summary.v1`
- Robot alias: `trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1`

Required statuses:

- `escalated_for_terminal_result_material_followup_not_proven`
- `waiting_for_terminal_result_material_backfill_not_proven`
- `needs_support_owner_reassignment_not_proven`
- `rejected_unsafe_terminal_result_followup_not_proven`
- `blocked_missing_terminal_result_review_handoff_not_proven`

Required safe output fields:

- `schema`
- `capability`
- `source_schema`
- `source=software_proof`
- safe `evidence_ref`
- safe `command_id` when present
- `terminal_result_type`
- `source_handoff_status`
- `followup_status`
- `assigned_owner`
- `support_owner`
- `reviewer_route`
- `required_material_backfill`
- `escalation_reason`
- `blocked_reason` when applicable
- `next_required_evidence`
- `safe_copy`
- `evidence_boundary`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`

Forbidden in safe output:

- raw artifact bodies, complete JSON dumps, raw robot responses, raw terminal material, credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER control details, hardware device paths, ACK/cursor mutation hints, replay/resubmit hints, reviewer-resolution claims, success claims, or control claims.

## Parallel Owner Plan

Launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct and do not overlap. Task D is Product closeout and must run only after worker evidence returns.

### Task A - Autonomy Algorithm Engineer

Goal: add the PC follow-up escalation CLI and tests for `verified_terminal_result_material_followup_escalation_status`.

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py`
- `tests/test_verified_terminal_result_material_followup_escalation_status.py`
- `docs/interfaces/verified_terminal_result_material_followup_escalation_status.md`
- `pc-tools/README.md`

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py tests/test_verified_terminal_result_material_followup_escalation_status.py
python3 -m unittest tests.test_verified_terminal_result_material_followup_escalation_status
python3 pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py --help
rg -n "verified_terminal_result_material_followup_escalation_status|software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|escalated_for_terminal_result_material_followup_not_proven|waiting_for_terminal_result_material_backfill_not_proven|needs_support_owner_reassignment_not_proven|rejected_unsafe_terminal_result_followup_not_proven|blocked_missing_terminal_result_review_handoff_not_proven|evidence_ref" pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py tests/test_verified_terminal_result_material_followup_escalation_status.py docs/interfaces/verified_terminal_result_material_followup_escalation_status.md pc-tools/README.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
git diff --check -- pc-tools/evidence/verified_terminal_result_material_followup_escalation_status.py tests/test_verified_terminal_result_material_followup_escalation_status.py docs/interfaces/verified_terminal_result_material_followup_escalation_status.md pc-tools/README.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
```

### Task B - Robot Platform Engineer

Goal: expose a Robot diagnostics/status safe alias for the follow-up escalation summary while keeping all controls disabled.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "verified_terminal_result_material_followup_escalation_status|robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary|software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
```

### Task C - User Touchpoint Full-Stack Engineer

Goal: add a mobile/web read-only terminal-result material follow-up escalation panel with safe copy support.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_followup_escalation_status.json`
- `docs/product/mobile_user_flow.md`

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_followup_escalation_status.json >/tmp/robot_diagnostics_verified_terminal_result_material_followup_escalation_status.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "verified_terminal_result_material_followup_escalation_status|software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|terminal result material follow-up|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
```

### Task D - Product Manager / OKR Owner Closeout

Goal: integrate worker evidence, update sprint closeout, and update OKR/progress only with conservative proof language. This task is intentionally deferred; do not create these files during the planning-only run.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/tech-done.md`
- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/final.md`

Acceptance commands:

```bash
test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/tech-done.md && test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/side2side_check.md && test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/final.md
rg -n "verified_terminal_result_material_followup_escalation_status|software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" OKR.md docs/process/okr_progress_log.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
```

## Validation Fence For Planning

```bash
test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/pre_start.md
test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/prd.md
test -f sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|verified_terminal_result_material_followup_escalation_status|software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate|Autonomy|Robot|Full-Stack|source=software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|no OKR percentage lift" sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
git diff --check -- sprints/2026.05.23_12-13_verified-terminal-result-material-followup-escalation-status
```

Implementation owners must run only scoped fenced commands unless a failure requires targeted diagnosis and rerun. Broad build or large regression commands are out of scope for this sprint plan.
