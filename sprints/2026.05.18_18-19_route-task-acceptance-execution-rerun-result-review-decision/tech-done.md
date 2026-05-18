# Sprint 2026.05.18_18-19 Route Task Acceptance Execution Rerun Result Review Decision - Tech Done

## 1. Sprint 类型与证据边界

- sprint_type: epic
- 收口时间：2026-05-18 18:25 Asia/Shanghai。
- 本轮证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`。
- Product closeout 判断：三位 Engineer 已完成本轮分工，产物只证明 Docker/local metadata gate、Robot diagnostics safe alias 和 mobile/web read-only panel 的 fail-closed 合约。
- 保守边界：本轮不证明真实 route/elevator field pass、delivery success、HIL、真实手机/browser 或 Objective 5 external proof；仍保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 实际改动

Autonomy Task A 已完成：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`
- `tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

实际效果：

- 新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_decision`。
- 支持 `ready_for_acceptance_execution_rerun_result_handoff`、`needs_acceptance_execution_rerun_result_backfill`、`evidence_ref_mismatch_rerun_result`、`blocked_unsafe_rerun_result`、`blocked_unsupported_rerun_result_intake`。
- 保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot Task B 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实际效果：

- 新增 diagnostics safe alias `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary`。
- Product closeout 前只读集成发现状态名不一致，Robot 已窄修并统一为本轮五类状态。
- Robot diagnostics 只读消费 sanitized summary，不开放控制入口，不证明 ROS runtime、Nav2/fixed-route、route completion、dropoff/cancel completion 或 delivery result。

Full-stack Task C 已完成：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实际效果：

- 新增 mobile/web 只读“受控复跑结果复核决策”panel。
- 手机端展示 decision status、safe evidence ref、owner handoff、next required evidence、boundary flags。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed；本轮不证明真实手机/browser 或真实 delivery success。

## 3. 验证结果

Engineer 已报告的分工验证：

- Autonomy：`py_compile` exit 0；`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_decision` 输出 `Ran 6 tests in 0.034s OK`；required `rg` exit 0；scoped `git diff --check` exit 0。
- Robot：`py_compile` exit 0；`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 187 tests in 0.417s OK`；required `rg` exit 0；scoped `git diff --check` exit 0。
- Full-stack：`node --check mobile/web/app.js` pass；`py_compile` pass；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 90 tests in 0.558s OK`；required `rg` exit 0；scoped `git diff --check` exit 0。

Product closeout 集成围栏复跑结果：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`：exit 0。
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_decision`：`Ran 6 tests in 0.032s OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 187 tests in 0.400s OK`。
- `node --check mobile/web/app.js`：exit 0。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 90 tests in 0.524s OK`。
- required `rg`：exit 0，覆盖本轮 gate、Robot safe alias、证据边界、Objective 5、Objective 1、PR #4、PR #5、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- scoped `git diff --check`：exit 0。

## 4. 偏差与修复

- 集成只读核对发现 Robot 侧状态名曾与 Autonomy/Full-stack contract 不一致。
- Robot 已窄修为统一状态：`ready_for_acceptance_execution_rerun_result_handoff`、`needs_acceptance_execution_rerun_result_backfill`、`evidence_ref_mismatch_rerun_result`、`blocked_unsafe_rerun_result`、`blocked_unsupported_rerun_result_intake`。
- Product closeout 未修改产品代码、测试代码、硬件配置或业务实现，只做 sprint/OKR/progress 收口。

## 5. 剩余风险

- 仍缺 PR #4 真实现场材料：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。
- Objective 5 仍缺真实外部 proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
