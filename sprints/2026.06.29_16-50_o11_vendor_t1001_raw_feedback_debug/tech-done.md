# 2026.06.29 16:50 O11 原始 T1001 反馈证据

sprint_type: micro

## 实际改动

- 按 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 的 WAVE ROVER 串口协议来源，保留 vendor `T=1001` 原始反馈字段。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py` 在解析有效 `T=1001` 时返回 `vendor_frame={"T","L","R","r","p","y","v"}`。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py` 的 feedback debug JSONL 写入 `vendor_frame`，后续 O11 Nav2 复验可以直接看到厂商原始 L/R。
- `onboard/scripts/o11_nav2_goal_execution_proof.py` 的 feedback debug 汇总支持从 `vendor_frame.L/R` 兜底读取轮速，兼容新旧 debug log。
- 更新硬件 bridge 测试、O11 测试和 `docs/hardware/wave_rover_json_bridge.md`。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof`，结果 `Ran 9 tests ... OK`。
- 通过：`python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_waveshare_json_bridge`，结果 `Ran 26 tests ... OK`。
- 本机 `python3 -m pytest ...` 未运行：当前 macOS 环境没有安装 `pytest`，已用等价 `unittest` 路径覆盖相关测试文件。
- 已同步到上车机 `root@192.168.1.11:37878`：
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_feedback.py`
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py`
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge.py`
  - `onboard/scripts/o11_nav2_goal_execution_proof.py`
  - 对应测试文件
- 上车机构建通过：`cd /root/rober/onboard && source /opt/ros/humble/setup.bash && colcon build --symlink-install --packages-select ros2_trashbot_hardware`，结果 `1 package finished`。
- 上车机 O11 测试通过：`python3 tests/test_o11_nav2_goal_execution_proof.py`，结果 `Ran 9 tests ... OK`。
- 上车机 bridge 测试通过：`python3 src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`，结果 `Ran 26 tests ... OK`。
- 上车机 install 后 parser 验证通过：`parse_feedback_line(...)` 返回 `vendor_frame.L=0.2`、`vendor_frame.R=0.3`。

## 剩余风险

- 本轮不触发真实发车、不执行 Nav2、不启动雷达或相机，只增强下一次现场复验的原始反馈证据。
- 现场最新 O11 旧 artifact 仍显示 PWM 行程有非零底盘命令和 IMU 姿态变化，但 `T=1001` L/R 为 `0/0`；完整 Nav2 闭环仍需安全确认后用 ROS 模式重跑，并在同窗口证明 vendor `T=1001.L/R` 非零。
