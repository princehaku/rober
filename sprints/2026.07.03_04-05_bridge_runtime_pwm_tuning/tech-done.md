# Bridge 运行中 PWM 调参和底盘三模式复验

## sprint_type

micro

## 实际改动

- 修改 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`：新增 ROS 参数运行时回调，支持不中断 UART owner 调整 `command_mode`、`track_width_m`、`max_wheel_speed_mps`、`pwm_min_abs`、`pwm_max_abs`、`feedback_debug_log_path` 和 `command_debug_log_path`。
- 修改 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`：调参前复用启动参数校验，非法 PWM 范围拒绝且不污染当前参数；合法调参写入 `wave_rover_command_debug.jsonl`，标记 `source=esp32_bridge_runtime_parameter_callback` 和 `sends_motion=false`。
- 修改 `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`：补 ROS `SetParametersResult` 测试桩，新增运行中 PWM 调高影响下一帧 `/cmd_vel` 映射、非法 PWM 原子拒绝两条单测。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/hardware/wave_rover_json_bridge.md`：同步本轮最新现场结论，明确 PC/WASD/Robot API/ROS `/cmd_vel`/UART JSON 链路已通，但 wheel raw 非零和真实物理移动仍未证明。
- 上位机同步并部署：把 `esp32_bridge_node.py` 和 `test_waveshare_json_bridge.py` 同步到 `root@192.168.1.11:/root/rober/onboard/src/ros2_trashbot_hardware/`，重建 `ros2_trashbot_hardware`，重启独立 `/esp32_bridge` 进程。

## 验证结果

- 本地单测：`python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_waveshare_json_bridge` 通过，`Ran 28 tests` / `OK`。
- 上位机重建：`colcon build --symlink-install --packages-select ros2_trashbot_hardware` 通过，`Summary: 1 package finished [9.90s]`。
- 上位机单测：`python3 -m unittest src.ros2_trashbot_hardware.test.test_waveshare_json_bridge` 通过，`Ran 28 tests` / `OK`。
- 上位机 bridge 重启：`esp32_bridge` 已重新连接 `/dev/ttyS5 @ 115200`，日志显示 `command_mode=pwm`、反馈日志和命令日志均启用。
- 参数拒绝验证：`ros2 param set /esp32_bridge pwm_min_abs 260` 返回 `Setting parameter failed: pwm_min_abs/pwm_max_abs must satisfy 0 <= min <= max <= 255`，随后 `pwm_min_abs` 仍为 `164`。
- 参数生效验证：设置 `pwm_min_abs/max_abs=220` 后，PC first-jog 命令日志出现多帧 `{"T":11,"L":220,"R":220}`；设置 `255/255` 后出现多帧 `{"T":11,"L":255,"R":255}`，均自动 stop。
- 诊断模式对照：`command_mode=speed` 时 PC first-jog 发送 `{"T":1,"L":0.061538,"R":0.061538}`；`command_mode=ros` 时发送 `{"T":13,"X":0.08,"Z":0.0}`；最后已切回 `command_mode=pwm`，当前 runtime PWM 为 `255/255`。
- 底盘反馈结果：上述 `PWM220`、`PWM255`、`T=1`、`T=13` 四组 PC first-jog 均返回 `proxy_status=command_forwarded`、`manual_command_executed=true`、`auto_stop_executed=true`，但 `wheel_feedback_lr_nonzero_proven=false`，`T=1001.L/R` 仍为 `0/0`。

## 剩余风险

- 当前证明了 PC 到上位机、ROS `/cmd_vel`、`esp32_bridge` 和 WAVE ROVER UART JSON 的命令链路，仍没有证明 wheel raw 非零、真实物理移动、Nav2 完整路线执行或 delivery success。
- 底盘不动的主嫌疑已从 PC/WASD/ROS 发布链路转到 WAVE ROVER 电机使能、底盘模式、下位机固件状态、驱动供电或 `T=1001.L/R` 反馈语义；需要现场检查底盘电源/电机开关/遥控或固件模式。
- 当前上位机 runtime 已保留 `command_mode=pwm`、`pwm_min_abs/max_abs=255` 便于继续现场试动；代码和 launch 默认仍是 vendor 样例 `164/164`，重启 bridge 后会回到保守默认。
- 相机仍受 USB full-speed 无首帧问题影响；本轮未改变相机链路。
