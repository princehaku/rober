# Operator Gateway Payload Route Terminal Source Cleanup

## sprint_type: micro

## 实际改动

- 将 `route_task_terminal_completion_rehearsal_source`、`task_terminal_completion_mainline_source`、`route_task_terminal_review_decision_source` 的长 `isinstance(..., dict)` 三元 fallback 链收敛为 `first_status_dict(...)`。
- 保持历史 resolver 顺序不变：两条 route terminal 链只使用 raw artifact -> plain summary；mainline 链使用 raw artifact -> plain summary -> robot diagnostics summary。
- 未新增 `diagnostics_source["summary"]` 或 `diagnostics_source["diagnostics_summary"]` 兜底，未修改后续 task-record helper fallback、ref/env 覆盖、payload 字段语义、launch 或硬件参数。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本轮 resolver 顺序和不变项。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.222s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N sprints/2026.05.26_65-66_operator-gateway-payload-route-terminal-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_65-66_operator-gateway-payload-route-terminal-source-cleanup/tech-done.md`
  - 关键输出：命令无输出，退出码 0。

## 剩余风险

- 本轮仅做 payload resolver 结构清理，未运行 ROS2 Docker colcon 构建、launch bringup、真实机器人、串口、WAVE ROVER 或 HIL 验证。
- 本轮未改硬件参数、launch、接口字段语义或后续 ref/env/helper fallback；剩余风险限于未覆盖真实运行时输入组合。
