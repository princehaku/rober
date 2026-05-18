# Sprint 2026.05.18_13-14 Route Task Acceptance Execution Callback Review Decision - Tech Done

## 1. Sprint 类型

- sprint_type: epic
- closeout 时间：2026-05-18 13:18 Asia/Shanghai
- 本轮证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- 固定结论：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`

## 2. 实际改动

### Autonomy Algorithm Engineer

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py`。
- 新增 `tests/test_route_task_field_retest_acceptance_execution_callback_review_decision.py`。
- 功能口径：消费上一轮 acceptance execution callback intake artifact / summary，把 callback packet 的 received / missing / rejected 状态转换为 `ready_for_controlled_field_rerun`、`needs_material_backfill` 或 `evidence_ref_mismatch_rerun` 等 fail-closed review decision。

### Robot Platform Engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 新增 `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary` safe alias，只读输出 sanitized summary，不暴露 raw artifacts、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER 参数、凭证、local paths、checksums 或 tracebacks。

### User Touchpoint Full-Stack Engineer

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 新增 mobile/web 只读 “现场回执复核决策” panel，消费主 summary 或 Robot diagnostics safe alias，展示 review decision、source callback intake status、safe `evidence_ref`、owner handoff、next required evidence、safe rerun hint 和固定边界标记。

### Product Manager / OKR Owner

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前快照、第 6 节当前最高优先级、第 7 节风险口径。
- 更新 `docs/process/okr_progress_log.md` 追加本轮进展。
- 更新 `docs/product/mobile_user_flow.md` 记录 mobile/web 新增只读现场回执复核决策 panel。

## 3. 验证结果

Engineer 已完成 focused validation：

- Autonomy：`py_compile` 通过；`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_decision` 输出 `Ran 6 tests OK`；CLI `--help` 通过；required `rg` 与 scoped `git diff --check` 通过。
- Robot：`py_compile` 通过；diagnostics unittest 输出 `Ran 182 tests OK`；required `rg` 与 scoped `git diff --check` 通过。
- Full-stack：`node --check mobile/web/app.js` 通过；mobile unittest 输出 `Ran 80 tests OK`；required `rg` 与 scoped `git diff --check` 通过。

Product closeout 需要另行运行：

```bash
test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/tech-done.md && test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/side2side_check.md && test -f sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision/final.md
rg -n "route_task_field_retest_acceptance_execution_callback_review_decision|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.18_13-14_route-task-acceptance-execution-callback-review-decision
```

## 4. 偏差和边界

- 本轮没有新增真实 WAVE ROVER、UART、HIL packet、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 或 operator HIL report；Objective 1 保持约 81%。
- 本轮没有真实 route/elevator field pass、真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 task record、真实 dropoff/cancel completion、真实 delivery result、真实门状态、真实楼层确认或真实人工协助记录；Objective 2 / 3 / 4 只保守维持当前 software proof 水位。
- 本轮没有真实手机设备、真实 iPhone/Android browser、production app、真实 PWA prompt/user choice 或现场 phone behavior。
- 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或其他 Objective 5 external proof。

## 5. 剩余风险

- PR #4 route/elevator 现场材料仍需要真实受控现场回填，尤其是门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 与 delivery result。
- PR #5 hardware baseline / vendor source / 2D LiDAR / ToF 风险仍需要真实 SKU/source、receipt、采购、安装、接线、电源、标定和 HIL-entry 材料。
- `ready_for_controlled_field_rerun` 只表示材料复核决策可进入受控现场复跑准备，不表示真实现场通过或 delivery success。
