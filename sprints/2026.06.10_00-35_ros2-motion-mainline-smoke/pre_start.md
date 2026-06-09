# ROS2 Motion Mainline Smoke Pre-Start

## sprint_type: epic

## 背景

CEO 已确认真实上位机 `root@192.168.1.11 -p 37878` 可以连接，并要求继续推进真实上车证据：雷达、摄像头、建图、运动都走一圈。上一轮已完成真实上位机 no-motion LiDAR/camera/TF/synthetic odom/map/route/keyframe 证据，但还没有验证 ROS2 `/cmd_vel` 到 WAVE ROVER ESP32 的真实串口运动主链路。

## 本轮目标

在安全低速边界内，用现有 `esp32_bridge` 通过 `/dev/ttyS5 @ 115200` 连接 WAVE ROVER ESP32，完成一次 ROS2 `/cmd_vel` 低速短脉冲 smoke，并保留 `/odom`、`/battery`、`/imu/data`、`/trashbot/stop`、串口占用、API 服务恢复证据。

本轮只做主链路 smoke，不提升 `safe_to_control`，不把命令积分 `/odom` 宣称为实测轮速里程计。

## Owner

- 主责：`robot-hardware-engineer`
- 咨询边界：如发现 ROS2 bridge 代码缺陷，再派 `robot-software-engineer`；默认不改代码。

## 资料来源

本轮硬件设计必须引用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

已采用的事实：

- WAVE ROVER UART 使用 UTF-8 newline-delimited JSON。
- 厂商默认下位机波特率为 `115200`。
- `T=1` 是左右轮 speed control。
- `T=13` 是 ROS control，但项目规则要求硬件验证后再作为默认映射。
- Orange Pi 目标串口路径以现场确认为准；本项目当前实测使用 `/dev/ttyS5`。

## 安全边界

- 先记录并停止当前占用 `/dev/ttyS5` 的 `upper_robot_api.py`，只释放底盘串口，不主动停止 camera/WebRTC 服务。
- ROS2 bridge 使用 `command_mode:=speed`，不启用 `T=13`。
- 低速脉冲不超过 `linear.x=0.03`，持续不超过 `0.5s`。
- 脉冲后必须发布零 `/cmd_vel`，再调用 `/trashbot/stop`。
- 停止 ROS2 launch 前后都要确认已发送 stop。
- 结束必须恢复 `upper_robot_api.py`，并验证 `http://127.0.0.1:8787/api/base/status` 可访问。

## 验收口径

通过条件：

- SSH 连通真实上位机。
- `/dev/ttyS5` 能被 ROS2 `esp32_bridge` 打开。
- ROS2 graph 存在 `/cmd_vel` 订阅、`/odom`、`/battery`、`/imu/data`、`/trashbot/stop`。
- 发布低速 `/cmd_vel` 后可调用 stop，且 launch log/服务返回能证明停止路径执行。
- 至少拿到 `/odom` 前后样本；若有 WAVE ROVER `T=1001` feedback，则拿到 `/battery` 或 `/imu/data` 样本。
- `upper_robot_api.py` 在结束后恢复，`/api/base/status` 返回正常。

部分完成条件：

- 若串口占用、反馈缺失或 ROS2 bridge 启动失败，必须保存现场日志、失败命令、恢复 API 服务，并明确下一步修复。

## 风险

- `/odom` 当前来自 ROS-side command integration，不是实测轮速。即使 x 变化，也只能证明 bridge 收到 `/cmd_vel` 并积分。
- `/battery`/`/imu/data` 依赖 ESP32 `T=1001` feedback stream；若没有反馈，不能宣称底盘反馈已闭环。
- 真实运动必须保证现场有人看护、车体有空间、可物理断电或拿起底盘。
