# 2026.06.27 02:57 Base PWM164 Nav2 Motion Signal

sprint_type: micro

## 实际改动

- 将上位机 PC 点动和 Nav2 托管 bridge 的默认 WAVE ROVER `T=11` PWM 从 90 调整为 vendor 示例值 164，仍保留短脉冲和 `T=11/T=1/T=13` 停车兜底。
- 在 `upper_robot_api.py` 和 `o11_nav2_goal_execution_proof.py` 中拆分三类证据：底盘命令已发送、`T1001 L/R` 轮速非零、`T1001 r/p` IMU 姿态变化。
- `/api/base/manual`、`/api/base/feedback-samples/latest`、Nav2 goal latest 增加 `imu_attitude_delta_observed`、`motion_signal_observed`、`motion_signal_source` 等字段，避免把 L/R 回读和实际运动迹象混为一谈。
- 修正 Nav2 goal execute 外层返回，执行成功时不再保留 no-motion 默认的 `blocked_devices_not_touched=/dev/ttyS5` 和 `blocked_commands_not_sent`。
- 同步更新 WAVE ROVER 协议默认值、硬件诊断 proof 文案和相关单测。

## 资料来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## 验证结果

- 本地：`python3 -m unittest onboard.tests.test_upper_robot_api onboard.tests.test_o11_nav2_goal_execution_proof onboard.src.ros2_trashbot_hardware.test.test_waveshare_json_bridge onboard.src.ros2_trashbot_hardware.test.test_hardware_diagnostics_proof` 通过，100 tests OK。
- 本地：`python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o11_nav2_goal_execution_proof.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py` 通过。
- 本地：`git diff --check` 通过。
- 真机部署：已同步 `upper_robot_api.py`、`o11_nav2_goal_execution_proof.py`、`wave_rover_protocol.py`、`hardware_diagnostics_proof.py` 到 `root@192.168.1.11:/root/rober/onboard/`，`trashbot-upper-robot-api.service` 重启后 `active`。
- 真机手控：`POST /api/base/manual` 使用 `{"T":11,"L":164,"R":164}`，运动中 `T1001 L/R=164/164`，停车后 `0/0`，`motion_signal_observed=true`。
- 真机 Nav2：`POST /api/nav2/goal/execute` 返回 `goal_succeeded`、`goal_accepted=true`、`result_status=succeeded`、`robot_control_executed=true`；latest 显示 `base_pwm_min_abs=164`、`base_pwm_max_abs=164`、非零命令 `{"T":11,"L":164,"R":-164}`、`uses_base_uart=true`、`sends_base_motion_commands=true`、`imu_attitude_delta_observed=true`。

## 剩余风险

- 摄像头仍是 `/dev/video1` 能打开但 `read()` 无帧，已排除普通浏览器独占，剩余风险偏硬件 USB/供电/线材/摄像头 UVC 输出。
- Nav2 长执行日志中 `T1001 L/R` 仍可能保持 0，但 IMU 姿态变化和非零命令已证明底盘运动链路不依赖雷达；后续若要完全闭环，需继续确认下位机固件的 L/R 回填策略或编码器配置。
- 交付成功仍需要 operator/dropoff 材料确认，本轮不声明 `delivery_success=true`。
