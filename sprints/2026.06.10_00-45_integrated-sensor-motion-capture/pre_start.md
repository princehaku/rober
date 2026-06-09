# Integrated Sensor Motion Capture Pre-Start

## sprint_type: epic

## 背景

原始目标是“真实上车 evidence capture，雷达，摄像头，建图，运动，都走一圈”。已有两轮证据：

- `2026.06.10_00-25_no-motion-map-route-evidence`：真实上位机 no-motion LiDAR/camera/SLAM/map/route/keyframe 证据已通过，但没有运动。
- `2026.06.10_00-35_ros2-motion-mainline-smoke`：真实上位机 ROS2 `/cmd_vel -> esp32_bridge -> /trashbot/stop` 低速 motion smoke 已通过，但没有同轮携带 LiDAR/camera/SLAM。

本轮把两条链路合并：同一轮启动底盘 bridge、LiDAR、camera、SLAM、map recorder、route recorder，执行一次低速短脉冲，采集 route/keyframes/map/topic 样本。

## 本轮目标

在真实上位机 `root@192.168.1.11:37878` 上完成 integrated capture：

- `/dev/ttyS5 @ 115200` 由 ROS2 `esp32_bridge` 接管。
- `/dev/ttyACM0 @ 150000` 发布 `/scan`。
- `/dev/video1` 发布 `/camera/image_raw`。
- `learn.launch.py` 发布 `/map` 并由 `map_recorder` 保存 map YAML/PGM。
- `route_data_recorder` 使用真实 `esp32_bridge` `/odom` 记录 `route.csv` 和 keyframes。
- 发布一次低速 `/cmd_vel linear.x=0.03`，随后零速和 `/trashbot/stop`。
- 尝试采集 `/battery`、`/imu/data`，如无样本必须保留失败证据。

## Owner

- 主责：`robot-hardware-engineer`
- 如发现必须修改 ROS2 bridge 或 launch 才能完成，再由主节点派 `robot-software-engineer`，本轮硬件 agent 不擅自扩大到产品代码。

## 资料来源

硬件事实必须引用：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

采用事实：

- WAVE ROVER UART 是 UTF-8 newline-delimited JSON。
- 厂商默认下位机波特率为 `115200`。
- `T=1` 是左右轮 speed control；本轮继续使用 `command_mode:=speed`。
- `T=13` 不在本轮启用。
- 当前真实底盘串口为 `/dev/ttyS5`；LiDAR 为 `/dev/ttyACM0`；camera 为 `/dev/video1`，均以现场实测为准。

## 证据边界

- `esp32_bridge` 当前只发布 `/odom` 消息，不发布动态 `odom -> base_link` TF。
- 为让 `slam_toolbox` 在 integrated smoke 中有 TF 拓扑，本轮允许启用 `no_motion_static_odom_tf:=true`，但这只能证明 `/scan -> SLAM -> /map -> save_map` 软件链路，不代表运动中的真实 TF/SLAM 标定完成。
- `route.csv` 使用真实 `/odom` topic，但该 `/odom` 仍是 ROS-side command integration，不是实测轮速里程计。
- 本轮不提升 `safe_to_control`，不打开 primary actions。

## 安全边界

- 开始前清理上一轮 ROS2 残留，确认 `/dev/ttyS5`、`/dev/ttyACM0`、`/dev/video1` 占用。
- 只停止 `upper_robot_api.py` 释放 `/dev/ttyS5`，不主动停止 WebRTC/camera 服务，除非它实际占用 `/dev/video1` 且需要执行本轮 camera capture；如需停止，必须记录原因并恢复。
- 运动脉冲 `linear.x <= 0.03`，持续不超过 `0.3s`。
- 脉冲后必须零速 `/cmd_vel` 和 `/trashbot/stop`。
- 结束后必须恢复 `upper_robot_api.py` 并验证 `/api/base/status`。

## 验收口径

通过条件：

- 同一轮证据中存在 `/scan`、`/camera/image_raw`、`/odom`、`/cmd_vel` subscriber、`/trashbot/stop` 成功返回。
- `route.csv`、`manifest.json`、至少一个 keyframe JPG/JSON 生成。
- `/trashbot/save_map` 返回 success，map YAML/PGM 生成。
- `upper_robot_api.py` 结束后恢复，`/api/base/status` 可访问。

增强通过：

- `/battery` 或 `/imu/data` 有新鲜 topic 样本，或日志清楚证明 `T=1001` feedback 已被 bridge 解析。

部分完成：

- 如果 feedback、map 或某个设备失败，必须保留命令输出、进程/设备占用、launch log，并恢复 API 服务。
