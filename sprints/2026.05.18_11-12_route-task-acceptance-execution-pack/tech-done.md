# Sprint 2026.05.18_11-12 Route Task Acceptance Execution Pack - Tech Done

sprint_type: epic

## 1. 实际改动

本轮按 `tech-plan.md` 拆成 Autonomy、Robot、Full-stack 三个 owner 并行执行，Product 只做 closeout、OKR 映射和证据边界核对。

Autonomy Algorithm Engineer:

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py`。
- 新增 `pc-tools/evidence/test_route_task_field_retest_acceptance_execution_pack.py`。
- 新增 `tests/test_route_task_field_retest_acceptance_execution_pack.py`。
- 更新 `docs/interfaces/evidence_contracts.md` 和 `pc-tools/README.md`。
- 产出 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`，消费上一轮 acceptance review decision，输出 owner checklist、rerun commands、safe evidence bundle、required route/elevator materials、handoff owner、next required evidence，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot Platform Engineer:

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `route_task_field_retest_acceptance_execution_pack` diagnostics summary 与 `robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary` safe alias，只读消费执行包，不启用 task_orchestrator、Start Delivery、Confirm Dropoff、Cancel、ACK、Nav2、HIL 或 primary actions。

User Touchpoint Full-Stack Engineer:

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/fixtures/status.json` 和 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增 mobile/web 只读 execution-pack panel，展示 safe `evidence_ref`、owner checklist、rerun commands、safe evidence bundle、required route/elevator materials、handoff owner、next required evidence、boundary flags，并继续保持 Start Delivery、Confirm Dropoff、Cancel gate 不打开。

Product Manager / OKR Owner:

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 最新 sprint 和保守进度边界。
- 更新 `docs/process/okr_progress_log.md` 追加本轮条目。

## 2. 验证结果

Worker 已回报的 owner 围栏：

- Autonomy：`python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py tests/test_route_task_field_retest_acceptance_execution_pack.py` 通过；`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_pack` 通过，`Ran 5 tests OK`；CLI `--help` 通过；`rg` 与 scoped `git diff --check` 通过。
- Robot：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 通过；diagnostics unittest 通过，`Ran 180 tests OK`；`rg` 与 scoped `git diff --check` 通过。
- Full-stack：`node --check mobile/web/app.js` 通过；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 通过，`Ran 76 tests OK`；`rg` 与 scoped `git diff --check` 通过。

Product closeout 需执行的集成围栏：

```bash
rg -n "route_task_field_retest_acceptance_execution_pack|robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
rg -n "route_task_field_retest_acceptance_execution_pack|robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary|software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_11-12_route-task-acceptance-execution-pack
git diff --stat
```

Product closeout 实跑结果记录在 `side2side_check.md` 和 `final.md`。

## 3. 偏差与失败定位

未发现 Product closeout 文件范围内需要修复的失败。若后续集成围栏暴露 engineer 代码范围问题，Product 不擅自改工程代码，应把失败定位交回对应 owner。

本轮没有访问真实电梯、真实手机/browser、ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue、4G 或真实 route/elevator field materials。

## 4. 剩余风险

- 本轮是 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`，不是真实 route/elevator field pass。
- `not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 仍是本轮验收边界。
- Objective 5 仍缺真实 external proof：HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser。
- Objective 1 仍缺真实 WAVE ROVER/HIL：`/dev/ttyUSB*`、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #4 route/elevator 现场验收链仍缺真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 2D LiDAR / ToF vendor/source、SKU、receipt、采购、安装、接线、电源、标定与 HIL-entry 仍是独立缺口。
