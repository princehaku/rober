# Tech Done

## sprint_type

micro

## 实际改动

- 新增 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_field_evidence_material.py`，承接 field evidence real-material、material blocker、material resolution 诊断域的 schema/gate/status 常量、not_proven helper、默认 summary helper、source contract helper、unsafe field helper 和 `summarize_*` 函数。
- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py` 为兼容 facade，从新模块 re-export 原有 public/internal 符号，保持现有调用方 import 路径不变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`，记录 field evidence material 诊断域的新内部模块位置，并声明本轮不改变 payload/schema/gate/API 语义。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 6.968s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_field_evidence_material.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_18-19_operator-gateway-field-evidence-material-modularization/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮是 metadata-only software proof，只验证 Python API、payload 兼容性和语法编译；未进行 ROS2 colcon、HIL、真实串口、WAVE ROVER、ESP32、Orange Pi、UART、波特率、速度映射或机械参数验证。
- 新模块仍通过延迟 facade helper 复用通用安全清洗逻辑；这是为了保持本轮兼容性，后续可继续拆分共享 helper，降低 facade 体积。
