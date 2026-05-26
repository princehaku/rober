# 2026.05.26 43-44 operator-gateway payload elevator trace source cleanup

## sprint_type: micro

## 实际改动

- `operator_gateway_diagnostics_payload.py`：将 elevator field evidence trace callback/material-backfill 六个 source 三元链替换为 `first_status_dict` resolver 调用。
- `docs/interfaces/operator_gateway_diagnostics.md`：记录六个 elevator field evidence trace source 查找已改用 resolver，并明确只接受字段级 alias。
- 本轮没有修改 ROS2 interface、launch、硬件配置、UART/serial 行为，也没有修改 hardware/hardware_sensor/PR5/field-evidence-rerun payload 区域。

## 验证结果

- `cd /mnt/e/rober/onboard && python3 -m unittest src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 结果：通过，`Ran 326 tests in 7.173s`，`OK`。
- `cd /mnt/e/rober/onboard && python3 -m compileall -q src/ros2_trashbot_behavior/ros2_trashbot_behavior`
  - 结果：通过，无输出。
- `rg` 局部核对六个目标 source 变量均已赋值为 `first_status_dict(...)`；本轮目标区没有新增 `fallback_to_diagnostics_source=True`。
- `cd /mnt/e/rober && git add -N onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py sprints/2026.05.26_43-44_operator-gateway-payload-elevator-trace-source-cleanup/tech-done.md && git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics_payload_sources.py docs/interfaces/operator_gateway_diagnostics.md sprints/2026.05.26_43-44_operator-gateway-payload-elevator-trace-source-cleanup/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮是软件 payload source 查找去重，不涉及真实 ROS graph、机器人硬件、串口、WAVE ROVER、Nav2 或 HIL 验证。
- 工作区已有大量既有未提交/未跟踪改动，本轮仅在允许范围内追加改动，未整理其他 sprint 或模块状态。
