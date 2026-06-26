# First-Jog PWM 运动链路

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`
  - 新增 `default_motion_read_window_s()`，让 `/api/base/manual` 的默认运动中反馈读窗跟随点动时长。
  - 500ms first-jog 默认读约 450ms，避免旧 220ms 上限在停车前漏掉 WAVE ROVER 约 200ms 节奏的 `T=1001 L/R`。
  - 240ms PC 键盘连续 pulse 默认读约 190ms，保留短周期续发体验，同时仍由上位机串口事务写入 stop 兜底。
  - 基于真机 smoke，把默认 `base_command_mode` 切到 `pwm`，PC first-jog/键盘 manual 默认发送 vendor `T=11` direct PWM。
  - 非 stop 点动后按顺序补发 `T=11`、`T=1`、`T=13` 零速，避免后续切换底盘控制模式时残留运动。
  - manual 运动中的 `T=1001` 样本会写入既有 `base_feedback_samples_latest` artifact，避免 PC 刷新 summary 后被停车后的 `0/0` 读回覆盖。
- `onboard/src/ros2_trashbot_hardware/`
  - `wave_rover_protocol.py` 新增 `/cmd_vel -> T=11 PWM` 模式。
  - `esp32_bridge_node.py` 支持 `command_mode=pwm`，`/trashbot/stop` 同时覆盖 PWM、speed 和 ROS 三种零速。
  - `bridge_config.py`、`hardware_diagnostics_proof.py` 与测试同步新增 `pwm_min_abs/pwm_max_abs`。
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
  - 默认 `command_mode=pwm`、`pwm_min_abs=90`、`pwm_max_abs=90`，让 Nav2/free-roam `/cmd_vel` 走本轮真机已观测非零反馈的底盘路径。
- `onboard/tests/test_upper_robot_api.py`
  - 增加 first-jog 500ms 与键盘 pulse 240ms 的默认读窗回归测试。
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
 - `docs/interfaces/ros_contracts.md`
 - `docs/hardware/wave_rover_json_bridge.md`
  - 同步记录底盘 manual/ROS bridge 的 PWM 控制设计、WAVE ROVER 本地资料依据和“不依赖雷达/摄像头才能低速试动”的边界。

## 验证结果

- 通过：`python3 onboard/tests/test_upper_robot_api.py`，57 tests passed。
- 通过：`python3 onboard/scripts/test_upper_robot_api_free_roam.py`，1 test passed。
- 通过：`python3 onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`，22 tests passed。
- 通过：`python3 onboard/src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`，10 tests passed。
- 通过：`python3 onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`，17 tests passed。
- 真机 smoke：
  - `T=1 L=0.12/R=0.12 duration=800ms`：串口写入和 stop 成功，`T=1001` observed，但 `L/R=0/0`。
  - `T=13 X=0.12/Z=0 duration≈750ms`：`T=1001` observed，但 `L/R=0/0`。
  - `T=11 L=90/R=90 duration≈550ms`：`T=1001 L/R=90/90`，`nonzero=true`。
- 部署到上位机并重启 `trashbot-upper-robot-api.service` 后：
  - `GET /api/base/status` 返回 `control_policy.base_command_mode=pwm`、`manual_pwm_min_abs=90`、`manual_pwm_max_abs=90`。
  - PC 7001 `POST /api/robot-control/base/first-jog` 返回 HTTP 200，`remote_motion_key_values.wheel_feedback_lr_nonzero_proven=true`、`wheel_feedback_latest_raw_left=90`、`wheel_feedback_latest_raw_right=90`。
  - PC 7001 summary 刷新后 `readback_summary.base.wheel_feedback_lr_nonzero_proven=true`，说明 manual artifact 已保留非零轮速证据。
  - PC 7001 `POST /api/robot-control/base/manual` 240ms pulse 返回 HTTP 200，`wheel_feedback_lr_nonzero_proven=true`、`raw L/R=90/90`，覆盖键盘连续手控所用短 pulse。

## 剩余风险

- 本轮已证明 direct PWM、PC first-jog 固定代理和 PC manual 240ms pulse 均可读到非零 `T=1001 L/R`。
- 摄像头当前仍是设备可打开但无首帧输出；这不会阻止低速移动，但会阻止本轮按“可建图”验收。
- Nav2 最近 artifact 显示 action 成功但 `hil_pass=false`；bridge 已切到 PWM 默认后，还需要重新跑完整路线执行，确认 controller `/cmd_vel` 到底盘的 HIL。
