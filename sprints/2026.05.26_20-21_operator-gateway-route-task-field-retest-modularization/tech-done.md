# route task field retest modularization tech done

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_route_task_field_retest.py`，承接 `route_task_field_retest` 诊断域的 `ROUTE_TASK_FIELD_RETEST_*` schema/gate 常量、`_route_task_field_retest_*_not_proven` helper、默认 summary helper、source contract/unsafe field helper，以及 `summarize_route_task_field_retest_*` 函数。
- `operator_gateway_diagnostics.py` 改为 compatibility facade，通过新模块 re-export 原有 public import/API；payload 聚合处继续使用原符号名，不改变调用点 import。
- `docs/interfaces/operator_gateway_diagnostics.md` 补充 route task field retest implementation module 说明，明确本轮仅实现模块化，不改变 schema、gate、alias key、payload 字段、false-state、safe copy、命令可用性或 `not_proven` 语义。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：`Ran 326 tests in 6.902s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：无输出，退出码 0
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_task_field_retest.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_20-21_operator-gateway-route-task-field-retest-modularization/tech-done.md`
  - 结果：无输出，退出码 0

## 剩余风险

- 本轮是 metadata-only software proof，只覆盖 Python 单测、compileall 和 diff whitespace 检查；未覆盖真实硬件、串口、WAVE ROVER、ESP32、Orange Pi、UART、波特率、速度映射、机械参数、HIL、Nav2 runtime 或真实现场 retest。
