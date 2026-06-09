# WAVE ROVER Feedback Smoke Side-to-Side Check

## 对照目标

- 目标 1：确认 `/dev/ttyS5` raw UART 能否拿到 fresh `T=1001`。
- 目标 2：若 raw 有 `T=1001`，确认 ROS2 `/battery`、`/imu/data` 是否有样本。
- 目标 3：结束后恢复 `upper_robot_api.py` 并验证 `/api/base/status`。

## 实际结果

- 目标 1：已达成。
  - raw UART 成功打开。
  - `T=1001` 连续出现。
  - 字段包含 `L/R/r/p/v`，`y` 字段存在但值为 `"null"`。
- 目标 2：未达成。
  - `/battery` 无样本。
  - `/imu/data` 无样本。
  - `/odom` 有样本，但只是零速积分输出。
- 目标 3：部分达成。
  - API 已恢复。
  - `/api/base/status` 可访问。
  - 但状态仍未反映本轮 fresh `T=1001`。

## 结论

本轮把问题边界从“底盘可能没有反馈”收窄到“软件桥接/发布链没有消费已存在的 `T=1001`”。下一轮不应再重复 raw 串口怀疑，应直接进入 bridge/parser/API readback 排查。
