# Operator Gateway Payload Route Rerun Result Source Cleanup

## sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py`
  - 将 `route_task_field_retest_acceptance_execution_rerun_result_intake_source`、`route_task_field_retest_acceptance_execution_rerun_result_review_decision_source`、`route_task_field_retest_acceptance_execution_rerun_result_review_handoff_source` 的长 `isinstance(..., dict)` 三元链替换为 `first_dict_value`。
  - 保留既有候选顺序：latest robot summary -> latest plain summary -> diagnostics robot summary -> diagnostics plain summary -> `diagnostics_source["summary"]` -> `diagnostics_source["diagnostics_summary"]` -> `{}`。
  - 添加中文注释说明 aggregate summary 兜底用于兼容历史 acceptance execution rerun result artifact。
- `docs/interfaces/operator_gateway_diagnostics.md`
  - 记录本轮 route task field retest acceptance execution rerun result source 清理边界，明确 ref/env 覆盖路径、payload 字段、ROS2 接口、launch 和硬件行为不变。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，关键输出 `Ran 326 tests in 7.121s`、`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，命令无输出，退出码 0。
- `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_51-52_operator-gateway-payload-route-rerun-result-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_51-52_operator-gateway-payload-route-rerun-result-source-cleanup/tech-done.md`
  - 结果：通过，命令无输出，退出码 0。

## 剩余风险

- 本轮是结构清理，不改硬件参数、launch、接口字段语义或 env/ref 覆盖逻辑。
- 未执行真实 ROS2 节点、HIL、串口或 WAVE ROVER 硬件验证；本轮不涉及硬件参数、底盘运动、串口、传感器或机械假设。
