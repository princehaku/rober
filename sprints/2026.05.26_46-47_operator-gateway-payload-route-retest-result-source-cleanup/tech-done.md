# route retest result source cleanup tech-done

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `route_task_field_retest_result_review_dispatch_source`、`route_task_field_retest_result_review_intake_source`、`route_task_field_retest_result_review_decision_source`、`route_task_field_retest_result_review_handoff_source`、`route_task_field_retest_result_callback_intake_source`、`route_task_field_retest_result_callback_review_decision_source`、`route_task_field_retest_result_callback_review_handoff_source` 的重复三元链改为显式 keys tuple + `first_status_dict`。
  - 保持所有七处来源顺序为 `latest_status` 先于 `diagnostics_source`，默认 `{}`，不启用 whole-`diagnostics_source` fallback。
  - `review_dispatch` 只保留 raw 和 plain summary 两个 alias，并用中文注释记录不能补造 `robot_diagnostics_*` alias 的历史兼容边界。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录 route task field retest result source 已迁移到 resolver，并说明 dispatch 不补 robot alias。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.137s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_46-47_operator-gateway-payload-route-retest-result-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_46-47_operator-gateway-payload-route-retest-result-source-cleanup/tech-done.md`
  - 结果：通过，无输出。
- `rg` 辅助核对七个目标 source：
  - 结果：七个目标 source 均已通过 `first_status_dict` 解析，保留后续 safe-copy 阶段对同名变量的消费。

## 剩余风险

- 本轮只做 Python 单测、语法编译和静态 diff 检查前置核对，未运行 ROS2 launch、Docker colcon build、真实 `/api/diagnostics` HTTP 请求或硬件 HIL。
- 本轮不涉及硬件、串口、UART、WAVE ROVER、launch 或 ROS2 接口变更；无需 Hardware、Autonomy、Full-Stack 协同。
