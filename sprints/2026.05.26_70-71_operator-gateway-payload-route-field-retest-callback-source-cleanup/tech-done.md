## sprint_type: micro

## 实际改动

- 将 `operator_gateway_diagnostics_payload.py` 中三条
  `route_task_field_retest_acceptance_execution_callback_*_source` 三元 fallback
  链改为显式 `first_dict_value(..., default={})` 候选列表。
- 三条 source 均保持旧顺序：latest raw、latest plain summary、latest robot
  diagnostics summary、diagnostics raw、diagnostics plain summary、diagnostics
  robot diagnostics summary、`diagnostics_source["summary"]`、
  `diagnostics_source["diagnostics_summary"]`、`{}`。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 callback
  intake、review decision、review handoff helper 化后仍保留空 dict 命中和
  generic summary fallback 相对顺序。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键结果：`Ran 326 tests in 8.566s`，`OK`。
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键结果：命令无输出，退出码 0。
- 通过：`cd /mnt/e/rober && git add -N sprints/2026.05.26_70-71_operator-gateway-payload-route-field-retest-callback-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_70-71_operator-gateway-payload-route-field-retest-callback-source-cleanup/tech-done.md`
  - 关键结果：命令无输出，退出码 0。

## 剩余风险

- 本轮只做非硬件 source 链结构清理，不覆盖真实 ROS2 runtime、HIL、UART/serial
  或 WAVE ROVER 实机行为。
