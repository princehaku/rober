# WAVE ROVER Feedback Smoke Final

## 结果摘要

- raw UART：成功。
- `T=1001`：成功捕获，且为连续 fresh feedback。
- `T=1001` 字段：包含 `L/R/r/p/v`；`y` 字段存在但值为 `"null"`。
- ROS2 `/battery`：无样本。
- ROS2 `/imu/data`：无样本。
- ROS2 `/odom`：有样本，但仅为零速积分输出。
- `upper_robot_api.py`：已恢复，`/api/base/status` 可访问。

## 最终结论

本轮已经证明 WAVE ROVER 下位机 feedback 经 `/dev/ttyS5` 可直接读出，`T=1001` 不是缺失，而是没有被当前 ROS2 bridge 和 API 状态链正确消费。真实上车证据从“怀疑底盘无反馈”推进到“确认 raw 有反馈、上层发布链断开”。

## blocker

- `esp32_bridge` 未把 fresh `T=1001` 发布成 `/battery`、`/imu/data`。
- `upper_robot_api.py` 恢复后仍显示 `feedback_ack.t1001_observed=false`，且 `feedback_samples_latest` 丢失。

## 剩余风险

- `y=\"null\"` 可能要求软件层做字段兼容或降级处理。
- 本轮没有修改产品代码，因此问题仍留在软件桥接层待修复。
- 只做了静止反馈 smoke，没有扩展到运动状态下的反馈一致性检查。
