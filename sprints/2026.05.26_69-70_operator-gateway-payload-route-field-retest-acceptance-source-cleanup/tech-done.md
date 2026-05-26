## sprint_type: micro

## 实际改动

- 将 `operator_gateway_diagnostics_payload.py` 中三条 route task field retest acceptance source 链改为 `first_dict_value(..., default={})`：
  - `route_task_field_retest_acceptance_brief_source`
  - `route_task_field_retest_acceptance_review_decision_source`
  - `route_task_field_retest_acceptance_execution_pack_source`
- 三条链均保持旧候选顺序：latest raw、latest plain summary、latest robot diagnostics summary、diagnostics raw、diagnostics plain summary、diagnostics robot diagnostics summary、diagnostics `summary`、diagnostics `diagnostics_summary`、`{}`。
- 同步更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录本轮 helper 化只做结构清理，不改变 env/ref 覆盖、summarizer、payload key、ROS2 接口、launch、硬件或 UART/serial 行为。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.194s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，命令无输出，退出码 0。
- `cd /mnt/e/rober && git add -N sprints/2026.05.26_69-70_operator-gateway-payload-route-field-retest-acceptance-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_69-70_operator-gateway-payload-route-field-retest-acceptance-source-cleanup/tech-done.md`
  - 结果：通过，命令无输出，退出码 0。

## 剩余风险

- 本轮未触碰硬件、launch、UART/serial、WAVE ROVER、ROS2 接口或测试断言语义。
- 本轮只覆盖软件单测、Python 编译检查和 diff 空白检查；未做 ROS2 launch、Docker colcon、HIL 或真实机器人运行验证。
