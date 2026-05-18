# Sprint 2026.05.18_17-18 Route Task Acceptance Execution Rerun Result Intake - Tech Done

## 1. 完成状态

- sprint_type: epic
- 收口时间：2026-05-18 17:23 Asia/Shanghai。
- 本轮证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`。
- 结论：三位 Engineer 已完成 Autonomy PC gate、Robot diagnostics sanitized consumer、mobile/web 只读 panel，Product closeout 复跑集成围栏通过。
- 统一边界保持：`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 实际改动

Autonomy Algorithm Engineer：

- 新增 `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py`。
- 新增 `tests/test_route_task_field_retest_acceptance_execution_rerun_result_intake.py`。
- 更新 `pc-tools/README.md` 和 `docs/interfaces/evidence_contracts.md`。
- 输出 `trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1` / summary，覆盖 ready、backfill、mismatch、unsafe、unsupported 状态。

Robot Platform Engineer：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 新增 `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary` safe alias，只读转发 sanitized summary。

User Touchpoint Full-Stack Engineer：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“受控复跑结果回执入口”panel，保持 Start Delivery、Confirm Dropoff、Cancel fail-closed。

Product Manager / OKR Owner：

- 新增本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前快照与 §6 当前最高优先级。
- 更新 `docs/process/okr_progress_log.md` 顶部 2026-05-18 系列。

## 3. 验证结果

Product closeout 于 2026-05-18 17:23 Asia/Shanghai 复跑集成围栏：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_intake.py`: exit 0。
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_intake`: `Ran 6 tests in 0.052s`，`OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: `Ran 186 tests in 0.472s`，`OK`。
- `node --check mobile/web/app.js`: exit 0。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`: `Ran 88 tests in 0.467s`，`OK`。

- required `rg`: exit 0，覆盖 `route_task_field_retest_acceptance_execution_rerun_result_intake`、`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary`、`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`、`Objective 5`、`Objective 1`、`PR #4`、`PR #5`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- scoped `git diff --check`: exit 0。

## 4. 偏差和失败定位

- 未发现验证失败。
- 本轮没有修改实现文件之外的 Product closeout 范围；Product 只更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- Engineer 已完成的代码侧文件仍是未提交工作区改动，Product 未回滚或覆盖这些变更。

## 5. 证据边界

本轮只证明 repo 内 Docker/local metadata gate、Robot diagnostics sanitized summary 和 mobile/web read-only panel 的 fail-closed 合约。它不是 real route/elevator field pass、not delivery success、not HIL、not real phone/browser、not O5 external proof。

仍保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 6. 剩余风险

- 真实 route/elevator field pass 仍缺：真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、task record、dropoff/cancel completion、delivery result。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery` 和 operator HIL report。
- Objective 5 仍缺真实 HTTPS/TLS、公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser external proof。
- PR #5 review 指出的 hardware baseline/vendor source/2D LiDAR/ToF 风险仍需真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料补齐。
