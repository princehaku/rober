# 2026.07.03 07:20 PC 相机与底盘 TX 诊断收口

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`：命令 debug JSONL 记录 `sent`、`serial_write_returned` 和 `sends_motion`，用于区分“已生成非零 vendor 命令”和“本机串口 write 返回成功”。
- `onboard/scripts/upper_robot_api.py`：`/api/base/status` 汇总非零命令的串口 write 成功计数、失败计数、最新成功非零命令和最新失败命令。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC summary 和普通首屏轮速事实展示新增串口 write 返回字段，并把下一步明确为查上位机 TX 到 ESP32 RX、固件 UART 接收、电机使能、底盘模式和电机电源。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`、`onboard/tests/test_upper_robot_api.py`：补充 bridge command debug 与上车 API 汇总测试，确保串口 write 结果不会被误当成 wheel L/R 非零。
- `docs/product/pc_tools_workstation.md`：同步记录相机直采失败、底盘直连串口复核和 ROS2 配套地图口径。

## 验证结果

- `python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py onboard/tests/test_upper_robot_api.py`：已通过，`Ran 139 tests ... OK (skipped=1)`。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`：已通过。
- `npm run build`（`pc-tools/workstation`）：已通过，仅保留既有 Vite chunk size warning。
- `npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts`（`pc-tools/workstation`）：已通过，`3 passed`、`433 passed`。
- `git diff --check`：已通过。
- 已部署 `esp32_bridge_node.py` 和 `upper_robot_api.py` 到上位机并重启对应服务；PC Node 已重启到 `0.0.0.0:7001`，PID `34290`。
- 现场 PC summary 读回：`map_display_default_zoom_percent=45%`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`base_command_chain_nonzero_count=394`、`base_command_chain_nonzero_sent_count=16`、`base_command_chain_serial_write_success_observed=true`、`base_command_chain_serial_write_success_count=20`、`base_command_chain_write_failed_count=0`、`wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_feedback_lr_nonzero_proven=false`。
- 现场直连复核：相机所有已广告直采模式均 `VIDIOC_STREAMON Input/output error`；停用 bridge 后直接读 `/dev/ttyS5 @115200` 可见 ESP32 `T=1001` 连续反馈，但写 `T=143/T=139/T=900/T=11` 没有命令回显、查询响应或非零 wheel L/R。

## 剩余风险

- 实时视频仍未证明：当前卡在 UVC/USB 物理链路或设备本体，服务共享预览和 PC 页面独占问题已排除。
- 底盘真实运动仍未证明：上位机本地串口 write 返回成功，但 ESP32 RX 是否收到/处理命令未证明，wheel raw L/R 仍为 `0/0`。
- 完整 Nav2 自动驾驶移动闭环和 delivery success 仍未完成；下一步应先查 TX/RX 接线、UART pinmux/固件接收、电机使能、底盘模式和电机电源。
