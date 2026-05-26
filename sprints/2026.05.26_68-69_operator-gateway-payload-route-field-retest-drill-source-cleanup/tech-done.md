## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py`：将
  `route_task_field_retest_material_callback_review_decision_source`、
  `route_task_field_retest_operator_drill_source`、
  `route_task_field_retest_drill_console_source` 三条重复三元 fallback 链改为
  `first_dict_value(..., default={})` 显式候选列表。
- 三条链均保持旧顺序：latest raw、latest plain summary、latest robot diagnostics
  summary、diagnostics raw、diagnostics plain summary、diagnostics robot diagnostics
  summary、`diagnostics_source["summary"]`、
  `diagnostics_source["diagnostics_summary"]`、`{}`。
- `docs/interfaces/operator_gateway_diagnostics.md`：补充本轮 helper 化范围和顺序保持说明。

## 验证结果

- 通过：
  `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 7.215s`，`OK`。
- 通过：
  `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令退出码 0，无错误输出。
- 通过：
  `cd /mnt/e/rober && git add -N sprints/2026.05.26_68-69_operator-gateway-payload-route-field-retest-drill-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_68-69_operator-gateway-payload-route-field-retest-drill-source-cleanup/tech-done.md`
  - 关键输出：命令退出码 0，无空白错误。

## 剩余风险

- 本轮为非硬件结构清理，未修改 ROS2 接口、launch、硬件、UART/serial 或 WAVE ROVER 路径。
- 验证范围是现有 operator gateway diagnostics 单测、Python 编译检查和限定文件 diff 空白检查；
  未运行 Docker/Humble `colcon build`，未覆盖真实 ROS graph、硬件、串口或 WAVE ROVER HIL。
