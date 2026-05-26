# Route/Elevator Field-Session Handoff Diagnostics Modularization

sprint_type: micro

## 实际改动

- 新增 `operator_gateway_diagnostics_route_elevator_field_session.py`，承接 route/elevator field-session handoff 的 schema/gate 常量、默认 blocked summary、`not_proven`、source contract、same-`evidence_ref`、disabled-action guard 和 summarize 逻辑。
- 更新 `operator_gateway_diagnostics.py` 为兼容 facade，从新模块 re-export 原有公开名称；`build_diagnostics_payload` 仍调用原同名 `summarize_route_elevator_field_session_handoff`，payload key 与 alias 未变。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md` 的模块边界说明，明确本次仅做 metadata/code organization，不改变 schema、gate、safe copy、not_proven、unsafe blocking 或控制动作语义。

## 验证结果

- 通过：`cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 关键输出：`Ran 326 tests in 6.983s`，`OK`
- 通过：`cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 关键输出：命令无错误输出，退出码 0。
- 通过：`cd /mnt/e/rober && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_route_elevator_field_session.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_23-24_operator-gateway-route-elevator-field-session-modularization/tech-done.md`
  - 关键输出：命令无错误输出，退出码 0。

## 剩余风险

- 本轮未改硬件/vendor 文档、硬件配置、launch 参数、UART、波特率、电压、引脚、底盘协议或真实设备验收结论。
- 当前改动只验证 diagnostics metadata 兼容性，不覆盖真实 route/elevator field session、真实 Nav2、WAVE ROVER 运动、串口反馈、HIL 或投放/取消闭环。
