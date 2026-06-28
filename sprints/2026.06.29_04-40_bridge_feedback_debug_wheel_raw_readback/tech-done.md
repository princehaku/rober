# 2026.06.29 04:40 Bridge Feedback Debug Wheel Raw Readback

## sprint_type

micro

## 实际改动

- `ros2_trashbot_hardware` 的 bridge 默认启用反馈 debug JSONL：`/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl`。
- `esp32_bridge_node` 每次写反馈 debug 行前动态读取 `feedback_debug_log_path` 参数，并自动创建父目录，便于现场运行时切换日志路径。
- 上位机 `GET /api/base/status` 新增 bridge feedback JSONL 只读汇总，优先使用 fresh bridge `T=1001` 反馈生成 `wheel_feedback_summary`、`bridge_feedback_debug`、`motion_signal_observed` 和 `imu_attitude_delta_observed`；bridge 日志 fresh 时跳过旧 direct `T=130` 串口 readback，避免状态刷新抢 `/dev/ttyS5`。
- 补充硬件 bridge 单测和上位机 API 单测，覆盖动态参数写日志、fresh bridge feedback 提升到 base status、旧 samples 不覆盖当前 bridge readback。
- 同步 PC 和建图产品文档：wheel raw L/R 当前读回由 `/esp32_bridge` 持有 UART 后的只读日志提供，PC/上位机不再为了轮速刷新抢 `/dev/ttyS5`。

## 验证结果

- 本地已通过 `python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_waveshare_json_bridge`，26 tests OK。
- 本地已通过 `python3 -m unittest onboard.tests.test_upper_robot_api`，77 tests OK。
- 本地已通过 `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/bridge_config.py onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge_node.py && git diff --check`。
- 已部署到 `root@192.168.1.11:37878`，重启 `trashbot-upper-robot-api.service` 并重启 `/esp32_bridge`。
- 真实上车只读证据：`ros2 param get /esp32_bridge feedback_debug_log_path` 返回 `/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl`；`/dev/ttyS5` holder 是 `/esp32_bridge`；日志已写入 `wave_rover_uart_t1001` 记录；`GET /api/base/status` 返回 `feedback_ack.source=fresh_bridge_feedback_debug_log`、`feedback_readback.schema=trashbot.upper_robot_api.v1.base_status_feedback_skipped`、`feedback_readback.request.attempted=false`、`bridge_feedback_debug.freshness=fresh`、`t1001_observed_count=80`、latest L/R=`0/0`。

## 剩余风险

- 本轮没有发送 manual、Nav2 goal、free-roam start、delivery 或 `/cmd_vel`，因此只证明 bridge-owned UART 反馈 readback 链路恢复，不证明 wheel raw L/R 已非零。
- 现场当前 bridge 日志里的 wheel raw L/R 仍为 `0/0`，所以完整 Nav2 路线执行、delivery success 和 PC 键盘连续手控的真实运动闭环仍需在 operator 安全确认后复验。
- 重启 bridge 的部署脚本末尾曾被 ROS setup 的 `set -u` 环境变量检查打断，但 bridge 进程、参数、串口 holder 和 API readback 后续验证均已通过。
