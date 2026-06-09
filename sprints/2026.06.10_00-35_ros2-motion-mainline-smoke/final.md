# ROS2 Motion Mainline Smoke Final

## 结果

本轮完成了真实上位机 ROS2 motion mainline smoke。证据显示：

- `upper_robot_api.py` 可被安全停止以释放 `/dev/ttyS5`
- `esp32_bridge` 可在 `/dev/ttyS5 @ 115200` 上连接 WAVE ROVER ESP32
- `command_mode:=speed` 下可以执行一次 `linear.x=0.03` 的低速短脉冲
- 零速命令和 `/trashbot/stop` 都成功执行
- `upper_robot_api.py` 已恢复，`/api/base/status` 可访问

## 对 OKR 的影响

- 直接推进 O1 的真实硬件协议可信底盘证据。
- 为后续把 LiDAR/camera/route 与真实 motion 合并联跑扫清了“串口能不能被 ROS2 bridge 接管”这个关键前置问题。

## 剩余风险

- `/odom` 不是实测轮速里程计，本轮不能据此判断真实行驶距离。
- 本轮未新增 `/battery`、`/imu/data` 的实时样本，因此底盘 feedback stream 仍需单独补证。
- cleanup 过程中暴露出 launch 父进程退出不等于 ROS2 子进程完全退出；下轮若继续上车，应把 stop/cleanup 做成可重复执行的显式 runbook。

## 下一步动作

1. 在有人看护条件下，做一轮带 LiDAR/camera 的低速联跑，并同时采集 `/scan`、图像、`/cmd_vel`、`/trashbot/stop`。
2. 单独验证 `/battery`、`/imu/data` 是否能从当前 ESP32 固件稳定流出，必要时检查 `T=130/T=131` 反馈流配置。
3. 把“停止 launch 后同步清理残留 ROS2 子进程”写入硬件上车 runbook，避免 API 恢复时串口再次被残留 bridge 占用。
