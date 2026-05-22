# Verified Terminal Result Material Review Handoff Tech Plan

Run time: 2026-05-22 12:13 Asia/Shanghai

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。Objective 1 约 81%，Objective 2/3/4 约 99%。
2. 本 sprint 针对 Objective 5 的下一步可行动 terminal-result material 路径：`verified_terminal_result_material_review_handoff`。
3. 本 sprint 不继续包装上一轮 `missing_real_owner_response_material` blocker；它承接 `verified_terminal_result_material_review_decision`，把 verified terminal delivery/dropoff/cancel result material 的复核结果转成 owner handoff。
4. 本 sprint 不提升 Objective 5 百分比，除非 field owner 在本轮提供真实 terminal delivery/dropoff/cancel result evidence bundle，并且 Product closeout 能按同一 safe `evidence_ref` 验证通过。
5. 本 sprint 不推进 Objective 1 completion。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；comment `3269642220` 只是 software-proof publication；当前 Docker-only 主机不能产生真实 WAVE ROVER/UART/HIL、2D LiDAR/ToF source/procurement/install/calibration 或 reviewer resolution。

## Architecture Decision

`verified_terminal_result_material_review_handoff` is a three-surface software-proof gate:

1. PC handoff CLI reads a prior review-decision artifact, summary, or Robot safe alias and emits a sanitized owner-handoff artifact plus summary.
2. Robot diagnostics/status consumes the handoff summary and exposes a safe alias for support/mobile.
3. Mobile/web renders a read-only panel with safe copy support.

Every surface must preserve:

- `capability=verified_terminal_result_material_review_handoff`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Interface Contract

Supported input source schemas and aliases:

- `trashbot.verified_terminal_result_material_review_decision.v1`
- `trashbot.verified_terminal_result_material_review_decision_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_review_decision_summary`
- `trashbot.robot_diagnostics_verified_terminal_result_material_review_decision_summary.v1`

Expected output schemas:

- Artifact: `trashbot.verified_terminal_result_material_review_handoff.v1`
- Summary: `trashbot.verified_terminal_result_material_review_handoff_summary.v1`
- Robot alias: `trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1`

Required safe output fields:

- `schema`
- `capability`
- `source_review_decision`
- `handoff_status`
- safe `evidence_ref`
- safe `command_id` when present
- `terminal_result_type`
- `material_status_summary`
- `accepted_material_refs`
- `missing_required_materials`
- `rejected_material_refs`
- `owner_handoff`
- `next_required_evidence`
- `blocked_reason` when applicable
- `safe_copy`
- `evidence_boundary`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Allowed handoff statuses:

- `ready_for_owner_handoff`
- `needs_material_backfill`
- `rejected`
- `blocked`

Forbidden in safe output:

- raw artifact bodies, complete JSON dumps, raw robot responses, credentials, bearer tokens, Authorization headers, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, raw ROS topics, `/cmd_vel`, serial/UART details, baudrate values, WAVE ROVER control details, hardware device paths, reviewer-resolution claims, or success/control claims.

## Parallel Owner Plan

Launch Task A, Task B, and Task C in parallel via `spawn_agent(agent_type=worker)` because file scopes are distinct. Task D runs after worker evidence returns.

### Task A - Autonomy Algorithm Engineer

Goal: add the PC handoff CLI and tests for `verified_terminal_result_material_review_handoff`.

Allowed files:

- `pc-tools/evidence/verified_terminal_result_material_review_handoff.py`
- `tests/test_verified_terminal_result_material_review_handoff.py`
- `docs/interfaces/verified_terminal_result_material_review_handoff.md`
- `pc-tools/README.md`

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/verified_terminal_result_material_review_handoff.py tests/test_verified_terminal_result_material_review_handoff.py
python3 -m unittest tests.test_verified_terminal_result_material_review_handoff
python3 pc-tools/evidence/verified_terminal_result_material_review_handoff.py --help
rg -n "verified_terminal_result_material_review_handoff|software_proof_docker_verified_terminal_result_material_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|ready_for_owner_handoff|needs_material_backfill|rejected|blocked|evidence_ref" pc-tools/evidence/verified_terminal_result_material_review_handoff.py tests/test_verified_terminal_result_material_review_handoff.py docs/interfaces/verified_terminal_result_material_review_handoff.md pc-tools/README.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
git diff --check -- pc-tools/evidence/verified_terminal_result_material_review_handoff.py tests/test_verified_terminal_result_material_review_handoff.py docs/interfaces/verified_terminal_result_material_review_handoff.md pc-tools/README.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
```

### Task B - Robot Platform Engineer

Goal: expose a Robot diagnostics/status safe alias for the handoff summary while keeping all controls disabled.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "verified_terminal_result_material_review_handoff|robot_diagnostics_verified_terminal_result_material_review_handoff_summary|software_proof_docker_verified_terminal_result_material_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
```

### Task C - User Touchpoint Full-Stack Engineer

Goal: add a mobile/web read-only terminal-result material handoff panel with safe copy support.

Allowed files:

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_review_handoff.json`
- `docs/product/mobile_user_flow.md`

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_verified_terminal_result_material_review_handoff.json >/tmp/robot_diagnostics_verified_terminal_result_material_review_handoff.json
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "verified_terminal_result_material_review_handoff|software_proof_docker_verified_terminal_result_material_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|owner handoff|evidence_ref" mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
git diff --check -- mobile/web docs/product/mobile_user_flow.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
```

### Task D - Product Manager / OKR Owner Closeout

Goal: integrate worker evidence, update sprint closeout, and update OKR/progress only with conservative proof language.

Allowed files:

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/tech-done.md`
- `sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/side2side_check.md`
- `sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/final.md`

Acceptance commands:

```bash
test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/tech-done.md && test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/side2side_check.md && test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/final.md
rg -n "verified_terminal_result_material_review_handoff|software_proof_docker_verified_terminal_result_material_review_handoff_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|3269642220|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
```

## Validation Fence For Planning

```bash
test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/pre_start.md && test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/prd.md && test -f sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/tech-plan.md
rg -n "sprint_type: epic|verified_terminal_result_material_review_handoff|software_proof_docker_verified_terminal_result_material_review_handoff_gate|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|3269642220" sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
git diff --check -- sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff
```

Implementation owners must run only scoped fenced commands unless a failure requires targeted diagnosis and rerun.
