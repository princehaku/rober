# Sprint 2026.05.18_19-20 Route Task Acceptance Execution Rerun Result Review Handoff - Tech Done

## 1. Sprint 类型与证据边界

- sprint_type: epic
- 收口时间：2026-05-18 19:20 Asia/Shanghai。
- 本轮证据边界：`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。
- Product closeout 判断：三位 Engineer 已完成本轮分工，产物只证明 Docker/local metadata gate、Robot diagnostics safe alias 和 mobile/web read-only panel 的 fail-closed 交接合约。
- 保守边界：本轮不证明真实 route/elevator field pass、delivery success、HIL、真实手机/browser 或 Objective 5 external proof；仍保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 实际改动

Autonomy Task A 已完成：

- `pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`
- `tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

实际效果：

- 新增 PC gate `route_task_field_retest_acceptance_execution_rerun_result_review_handoff`。
- 将上一轮 review decision 转成 owner handoff package，覆盖 ready handoff、material backfill、mismatch、unsafe 和 unsupported 分支。
- 输出保持 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot Task B 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实际效果：

- 新增 diagnostics safe alias `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary`。
- Robot diagnostics 只读消费 sanitized handoff summary，不开放控制入口，不证明 ROS runtime、Nav2/fixed-route、route completion、dropoff/cancel completion 或 delivery result。
- safe alias 仅用于 support metadata，不透出 raw artifact、local path、checksum、credentials、DB/queue URL、ROS topic、serial/UART、WAVE ROVER low-level control、success 或 control wording。

Full-stack Task C 已完成：

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实际效果：

- 新增 mobile/web 只读“受控复跑交接”panel。
- 手机端展示 handoff status、owner role、safe evidence ref、next required evidence、rerun summary 和 boundary flags。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail-closed；本轮不证明真实手机/browser 或真实 delivery success。

## 3. 验证结果

Engineer 已报告的分工验证：

- Autonomy：`py_compile` pass；`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff` 输出 `Ran 5 tests in 0.033s OK`；required `rg` pass；scoped `git diff --check` pass。
- Robot：`py_compile` exit 0；diagnostics unittest 输出 `Ran 188 tests in 0.408s OK`；required `rg` pass；scoped `git diff --check` pass。
- Full-stack：`node --check mobile/web/app.js` pass；`py_compile` pass；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 92 tests in 0.542s OK`；required `rg` pass；scoped `git diff --check` pass。

Product closeout 集成围栏复跑结果：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`：exit 0。
- `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff`：`Ran 5 tests in 0.032s OK`。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 188 tests in 0.418s OK`。
- `node --check mobile/web/app.js`：exit 0。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 92 tests in 0.567s OK`。
- required `rg`：exit 0，覆盖本轮 handoff gate、Robot safe alias、证据边界、Objective 5、Objective 1、PR #4、PR #5、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- scoped `git diff --check`：exit 0。

## 4. 偏差与修复

- Product closeout 未修改实现文件、测试文件、硬件配置或 launch 参数，只更新允许范围内的 sprint/OKR/progress 文档。
- 本轮没有发现需要返派 Engineer 的实现失败；若集成围栏后续失败，应按失败归属返派 Autonomy、Robot 或 Full-stack 对应 owner，而不是由 Product 修改实现。

## 5. 剩余风险

- 仍缺 PR #4 真实现场材料：真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result。
- Objective 5 仍缺真实外部 proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report。
- PR #5 仍缺真实 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
