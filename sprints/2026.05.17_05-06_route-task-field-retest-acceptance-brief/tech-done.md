# Sprint 2026.05.17_05-06 Route Task Field Retest Acceptance Brief - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`，把上一轮 `route_task_field_retest_drill_console` 推进为现场复测验收简报和 owner handoff packet。证据边界保持 Docker-only / local software proof，不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。

Task A - Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_brief.py` 和 `pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py`。
- 更新 `pc-tools/README.md` 与 `docs/navigation/fixed_route_workflow.md`。
- 实现 dependency-free CLI `route_task_field_retest_acceptance_brief`，消费 drill console artifact、summary、wrapper 和 nested JSON，输出 `trashbot.route_task_field_retest_acceptance_brief.v1` 与 `trashbot.route_task_field_retest_acceptance_brief_summary.v1`。
- Summary 固化 acceptance status、safe `evidence_ref`、field entry prerequisites、execution checklist、pass/fail criteria、required evidence packet、owner handoff、rerun notes、`not_proven` 和 evidence boundary。
- Required evidence packet 明确要求 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result。

Task B - Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 与 `docs/interfaces/ros_contracts.md`。
- 新增 `route_task_field_retest_acceptance_brief` / `_summary` diagnostics metadata-only consumer。
- 支持 artifact、summary wrapper、Robot-compatible summary、nested diagnostics summary；missing、unsupported、unsafe、success wording、actions enabled 均 fail closed。
- 不改变 collect、dropoff、cancel、ACK、Nav2、HIL、cursor、delivery success 语义；继续保持 `delivery_success=false` 和 `primary_actions_enabled=false`。

Task C - User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`、`mobile/web/styles.css`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/web/fixtures/status.json` 与 `docs/product/mobile_user_flow.md`。
- 新增只读“现场复测验收简报” panel，消费 `route_task_field_retest_acceptance_brief` artifact、summary 和 Robot diagnostics compatible summary。
- 展示 acceptance status、safe evidence ref、pass/fail criteria、required evidence packet、owner handoff、safe copy、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- Start Delivery、Confirm Dropoff、Cancel gating 未改变；copy/export 保持 whitelist-only。

Task D - Product Manager / OKR Owner：

- 新增本文件、`side2side_check.md` 和 `final.md`。
- 更新 `OKR.md` 4.1 与 `docs/process/okr_progress_log.md`。
- 保守调整 Objective 2 / Objective 3 / Objective 4；Objective 5 不提升。

## 2. 验证结果

Task A worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_brief.py`：PASS。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_acceptance_brief.py`：`Ran 5 tests ... OK`。
- `python3 pc-tools/evidence/route_task_field_retest_acceptance_brief.py --help`：PASS。
- Required `rg`：PASS。
- Scoped `git diff --check`：PASS。

Task B worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：PASS。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 130 tests ... OK`。
- Required `rg`：PASS。
- Scoped `git diff --check`：PASS。

Task C worker 验证：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 32 tests ... OK`。
- `node --check mobile/web/app.js`：PASS。
- Required `rg`：PASS。
- Scoped `git diff --check`：PASS。

Product closeout 验证：

- `rg -n "route_task_field_retest_acceptance_brief|software_proof_docker_route_task_field_retest_acceptance_brief_gate|Objective 2|Objective 3|Objective 4|Objective 5|Docker-only|not_proven|delivery_success=false|primary_actions_enabled=false|PR #5" sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief OKR.md docs/process/okr_progress_log.md`：PASS，命中 sprint closeout、`OKR.md` 4.1 和 progress log 中的 acceptance brief、OKR、Docker-only 与安全边界条目。
- `git diff --check -- sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/tech-done.md sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/side2side_check.md sprints/2026.05.17_05-06_route-task-field-retest-acceptance-brief/final.md OKR.md docs/process/okr_progress_log.md`：PASS，无输出。

## 3. 失败定位

Task A 首轮 unittest 因 safe summary 自身包含 forbidden wording 触发 `blocked_unsafe_acceptance_brief_summary`。Autonomy worker 已修正 safe copy / summary wording，并复验 py_compile、unittest、CLI help、required `rg` 和 scoped diff check 全部通过。

Task B 和 Task C 未报告遗留失败。Product closeout 若发现围栏失败，将先定位并修复后复验。

## 4. 剩余风险

- 本轮仍不是 route/elevator field pass；没有真实 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 或同一 `evidence_ref` 的实机复账。
- 本轮仍不是 HIL；没有真实 WAVE ROVER、真实串口/UART、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 或 2D LiDAR / ToF HIL-entry。
- 本轮仍不是真实手机/browser 或 production app proof；mobile/web panel 只证明本地 phone-safe read-only summary 消费。
- 本轮仍不是 Objective 5 external proof；没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 所有 Product closeout 结论必须继续保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
