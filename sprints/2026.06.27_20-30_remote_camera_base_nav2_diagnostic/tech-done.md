# 2026.06.27 20:30 remote camera/base/Nav2 diagnostic

sprint_type: micro

## 实际改动

- 修正 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge.py`：托管 Nav2 smoke 通过 SIGINT 收尾时，如果 rclpy 已经 shutdown，入口只记录中文 warning，不再把 `rcl_shutdown already called` traceback 当成桥接失败。
- 补充 `onboard/src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`：覆盖重复 shutdown 被忽略、其它 shutdown 异常继续抛出的边界。
- 更新 `docs/product/pc_tools_workstation.md`：记录 2026-06-27 01:48-01:50 真实 SSH 诊断证据，明确摄像头不是独占，低速移动/Nav2 不依赖雷达，当前自动驾驶剩余 blocker 是底盘反馈 L/R 仍为 0/0。

## 验证结果

- 已通过 SSH 连接 `root@192.168.1.11 -p 37878`。
- 摄像头服务 active，`/dev/video1` 为 DV20 UVC，`lsof /dev/video*` 未发现其它 owner；camera health 报 `source_usage.status=not_in_use`、`owner_count=0`、`source_readiness=first_frame_failed`、`capture_read_returned_false`。
- 底盘串口 `/dev/ttyS5 @ 115200` 可打开，`T=130` 能收到连续 `T=1001`，电压约 12.42V，但 L/R 为 `0/0`。
- Nav2 latest 读到 `goal_accepted=true`、`status=goal_succeeded`、`base_command_mode=pwm`、`base_command_nonzero_count=49`，但 `base_feedback_lr_nonzero_proven=false`、`hil_pass=false`。

## 剩余风险

- 本轮未发送新的运动命令，只做只读/已有 artifact 诊断；真实电机能否转动仍需要现场安全确认后继续查电机使能、WAVE ROVER 模式和 PWM 执行链。
- 摄像头仍未出首帧；需要检查 DV20 输入源、USB 线/供电、采集卡模式或替换 known-good UVC。
