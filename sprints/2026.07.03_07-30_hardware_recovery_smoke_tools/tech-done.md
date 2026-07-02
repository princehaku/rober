# 2026.07.03 07:30 硬件恢复 smoke 工具化

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_usb_recovery_smoke.py`：新增相机 USB 恢复 smoke，自动停/启相机服务、关闭 autosuspend、可 reauthorize USB、解绑 USB audio，并用 `YUYV@320x240@20` 与 `MJPG@480x320@30` 直接验证 STREAMON 是否有真实字节输出。
- `onboard/scripts/wave_rover_uart_tx_probe.py`：新增 WAVE ROVER UART TX 接收 probe，默认只发非运动查询 `T=143/T=139/T=900/T=131`，用于区分上位机串口 write 成功和 ESP32 确实解析命令；只有显式 `--motion-test` 才发短 PWM 并自动 stop。
- `docs/product/pc_tools_workstation.md`、`docs/hardware/wave_rover_json_bridge.md`、`docs/vision/board_camera_publisher.md`：同步记录新工具、真机复测结果和剩余硬件风险。

## 验证结果

- `python3 -m py_compile onboard/scripts/camera_usb_recovery_smoke.py onboard/scripts/wave_rover_uart_tx_probe.py`：通过。
- `python3 onboard/scripts/camera_usb_recovery_smoke.py --help`：通过。
- `python3 onboard/scripts/wave_rover_uart_tx_probe.py --help`：通过，本地无 pyserial 时也能显示帮助。
- 上位机 `python3 /root/rober/onboard/scripts/camera_usb_recovery_smoke.py`：输出 `status=streamon_failed`、`frame_observed=false`、`next_action=move_camera_to_high_speed_usb_port_or_powered_hub`；`YUYV@320x240@20` 和 `MJPG@480x320@30` 均 `bytes=0`、`streamon_error=true`。
- 上位机 `python3 /root/rober/onboard/scripts/wave_rover_uart_tx_probe.py` 在 bridge 占用时：输出 `status=port_held`，不抢 `/dev/ttyS5`。
- 上位机停 bridge 后运行 `wave_rover_uart_tx_probe.py`：输出 `status=no_command_response`、`esp32_receive_confirmed=false`、`wheel_lr_nonzero_observed=false`；各窗口均可读到 `T=1001`，但 `T=143/T=139/T=900/T=131` 后无查询响应。
- 复原验证：`esp32_bridge` 已重新启动并持有 `/dev/ttyS5`，`trashbot-local-webrtc-camera.service` active，`8787` 与 `8088` 正常监听；PC 7001 summary 读到 `map_display_default_zoom_percent=45%`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`base_command_chain_serial_write_success_observed=true`、`wheel_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 实时图传仍未完成：当前 DV20 UVC 在 USB `12M` full-speed 下 STREAMON 失败，软件恢复动作未能产生首帧。
- WASD 真实移动仍未完成：ROS/PC/bridge 可以 write，但 ESP32 receive 未确认；下一步必须检查上位机 TX 到 ESP32 RX 接线、UART pinmux 或固件接收路径。
- 完整 Nav2 物理移动闭环和 delivery success 仍未证明。
