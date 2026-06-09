# ROS2 Motion Mainline Smoke Side-by-Side Check

## CEO 目标

“雷达、摄像头、建图、运动，都走一圈。”

## 本轮实际对齐

- 运动主链路：已补齐真实上位机 `/cmd_vel -> esp32_bridge -> /trashbot/stop` smoke 证据。
- 底盘串口：已验证 `/dev/ttyS5 @ 115200` 可被 ROS2 bridge 打开。
- API 恢复：已恢复 `upper_robot_api.py` 并验证 `/api/base/status`。

## 仍未对齐的点

- 本轮只做了 base-only motion smoke，没有同时携带 LiDAR/camera 实时节点联跑。
- `/odom` 不是实测轮速里程计，因此“运动已完全闭环”仍不能成立。
- 本轮没有拿到新的 `/battery` 或 `/imu/data` 样本，不能把反馈链路说成已经重新实测通过。

## 对 CEO 口径的结论

可以把“真实上位机 ROS2 运动主链路 smoke”标记为已完成一圈，但还不能把“整机带传感器联跑运动”标记为完成，也不能把“底盘反馈闭环”标记为完成。

