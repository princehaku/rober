# ROS T13 Default Autonomy Control

## Sprint 类型

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py`
  - 将 `esp32_bridge` 的 `command_mode` 默认值从 `speed` 改为 `ros`。
  - 默认控制面改为 vendor WAVE ROVER `T=13 X/Z`，让 Nav2、PC 键盘连续手控和自由移动共享 ROS `/cmd_vel` 语义。
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
  - `command_mode` launch 默认从 `speed` 改为 `ros`，`speed/T=1` 与 `pwm/T=11` 保留为显式诊断 override。
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - autonomous 主入口同步默认 `command_mode=ros`，避免自动驾驶启动后仍走旧 `speed/T=1` 控制面。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py`
  - 更新中文注释，说明 `T=13` 是默认 ROS 控制命令，`T=1/T=11` 是诊断回退。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`
  - 离线硬件诊断 proof 默认同步为 `command_mode=ros`，保持 proof 与 launch/driver 一致。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 静态测试改为断言 bringup/autonomous 默认 `ros/T=13`。
- `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - 增加 bridge 默认配置为 `ros` 的断言。
- `onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - 更新诊断 proof 默认 command mode 断言。
- `docs/hardware/wave_rover_json_bridge.md`
  - 同步记录默认控制面切到 ROS/T=13，且完整 Nav2 路线执行仍必须以同一 artifact 内 action succeeded + `T=1001.L/R` 非零为准。

## 验证结果

- 已通过：`python3 onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - `Ran 18 tests in 0.032s OK`
- 已通过：`python3 onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
  - `Ran 25 tests in 0.013s OK`
- 已通过：`python3 onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - `Ran 10 tests in 0.009s OK`
- 已通过：`python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- 已通过：`rg -n "'command_mode', default_value='speed'|node\.declare_parameter\(\"command_mode\", \"speed\"|\"command_mode\": \"speed\"" onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup`
  - 无匹配；旧默认未残留在硬件桥和 bringup launch 范围内。
- 已通过：`bash onboard/scripts/docker_humble_build.sh`
  - `Summary: 6 packages finished [42.7s]`
  - Docker 保留既有平台 warning：base image 为 `linux/amd64`，host 为 `linux/arm64/v8`。
- 已通过：`git diff --check`
- 未通过环境项：`python3 -m pytest ...`
  - 本机 `/opt/homebrew/Caskroom/miniconda/base/bin/python3` 无 `pytest` 模块；已用同文件的 unittest 入口替代执行。

## 剩余风险

- 本轮没有触发真实 Nav2 execute、manual、keyboard、free-roam start、delivery、stop 或 `/cmd_vel`。
- 该改动让下一次启动默认走 `ros/T=13`，但不证明 WAVE ROVER 实际运动；完整路线仍需现场安全确认后重跑，并在同窗口证明 wheel raw L/R 非零。
- 摄像头 live 仍是 UVC 无首帧且不是页面独占；本轮不处理摄像头硬件输入/供电问题。
