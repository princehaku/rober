# Algorithm / Sensor Live Evidence Report

## 自主能力目标和本轮抓手

- 目标：为现场 O3 验证 lane 补真实上位机的传感器、SLAM/map、rosbag 证据，供后续 O6 archive 和 O7 route replay / labeling 消费。
- 抓手：不改算法代码，不启动无人值守长距离导航；通过 SSH 在真实上位机 `op-z3-b6.home` 上采集 ROS2 package/topic/node、目标 topic smoke、SLAM/map 入口和短 rosbag。
- 硬件资料入口已读：`docs/vendor/VENDOR_INDEX.md`。本轮没有新增引脚、电压、UART、波特率、机械安装或底盘运动假设。

## 远端 runtime 证据

- SSH：`ssh root@192.168.1.11 -p 37878` 成功。
- Host：`op-z3-b6.home`。
- 时间：`Tue Jun  9 10:59:07 PM CST 2026`。
- Kernel：`Linux op-z3-b6.home 6.1.31-sun50iw9 #1.0.4 SMP Thu Jul 11 16:37:41 CST 2024 aarch64`。
- ROS 环境：必须使用远端 `bash` 解释 ROS setup；默认 zsh 下直接 source `/opt/ros/humble/setup.bash` 会导致 `ros2` 不在 PATH。
- 有效 ROS 环境：
  - `ROS_DISTRO=humble`
  - `ros2_path=/opt/ros/humble/bin/ros2`
  - `sourced=/root/rober/onboard/install/setup.bash`

## ROS2 package / node / topic 状态

已发现 trashbot package：

- `ros2_trashbot_behavior`
- `ros2_trashbot_bringup`
- `ros2_trashbot_hardware`
- `ros2_trashbot_nav`
- `ros2_trashbot_vision`

当前 ROS graph：

- Node：空。
- Topic：
  - `/parameter_events [rcl_interfaces/msg/ParameterEvent]`
  - `/rosout [rcl_interfaces/msg/Log]`

结论：工作区和 package 可发现，但现场没有正在运行的传感器、硬件桥、SLAM、map server 或 route recorder 节点。

## 雷达 / 摄像头 / 里程计 / TF / Map 证据

目标 topic smoke 结果：

| Topic | 结果 | 证据摘要 |
| --- | --- | --- |
| `/scan` | 缺失 | `ros2 topic hz` 提示未发布；`ros2 topic info -v` 返回 `Unknown topic '/scan'` |
| `/camera/image_raw` | 缺失 | `ros2 topic hz` 提示未发布；`ros2 topic info -v` 返回 `Unknown topic '/camera/image_raw'` |
| `/odom` | 缺失 | `ros2 topic hz` 提示未发布；`ros2 topic info -v` 返回 `Unknown topic '/odom'` |
| `/tf` | 缺失 | `ros2 topic echo --once` 无法确定类型；`ros2 topic info -v` 返回 `Unknown topic '/tf'` |
| `/map` | 缺失 | `ros2 topic echo --once` 无法确定类型；`ros2 topic info -v` 返回 `Unknown topic '/map'` |

补充 topic：

- `/cmd_vel`、`/imu/data`、`/battery`、`/tf_static` 也均未注册。

## SLAM / map / learn.launch 发现结果

- `slam_toolbox` 已安装：`/opt/ros/humble`。
- `nav2_map_server` 已安装：`/opt/ros/humble`。
- active map/slam service：未发现 `map|slam|serialize|save` 相关服务。
- 既有地图文件：`/root/rober/onboard/runtime/maps/trashbot_map.pgm`。
- `ros2_trashbot_bringup learn.launch.py --show-args` 成功，入口存在，包含：
  - `lidar_enabled`，默认 `false`
  - `lidar_serial_port`，默认 `/dev/ttyACM0`
  - `lidar_serial_baudrate`，默认 `150000`
  - `route_recorder`，默认 `false`
  - `route_output_dir`，默认 `$HOME/.ros/trashbot_runs/run_001`
  - `map_dir`，默认 `$HOME/.ros/trashbot_maps`
- 本轮没有启动 `learn.launch.py` 长跑：目标传感器 topic、odom/tf 和 camera topic 都不存在，启动 SLAM 不能产出有效 live map，且本轮边界是不做无人值守长距离导航。

## Rosbag 证据

- 远端 run 目录：`/root/.ros/trashbot_live_runs/field_full_stack_20260609_230304`
- 目标 topic：`/scan /camera/image_raw /odom /tf /map`
- 缺失目标 topic：全部缺失。
- fallback 录制 topic：`/rosout /parameter_events`
- rosbag metadata：`/root/.ros/trashbot_live_runs/field_full_stack_20260609_230304/route_bag/metadata.yaml`
- storage：`sqlite3`
- message_count：`7`
- topic message counts：
  - `/rosout`: `7`
  - `/parameter_events`: `0`
- `rosbag_rc=124` 是 `timeout 10s` 结束录制的退出码；录制已正常写出 metadata 和 db3。

说明：这是 graph-only fallback bag，不是传感器 rosbag，不能用于路线、SLAM 或视觉评测。

## 失败定位

1. 首次按验收命令直接 SSH 执行时，远端默认 shell 为 zsh，`source /opt/ros/humble/setup.bash` 失败并导致 `ros2: command not found`。用 `ssh ... 'bash -s'` 后恢复。
2. ROS2 runtime 可用，但没有任何业务 node 正在运行。
3. 雷达、摄像头、odom、tf、map topic 均未注册，说明传感器/bringup 链路未启动或未接入 ROS graph。
4. 已有 `learn.launch.py` 和 LiDAR 参数入口，但当前缺 live `/scan`、`/odom`、`/tf`，无法生成有效 `map.yaml` 或 route/keyframe。

## 写入文件

- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/algorithm_raw.log`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/algorithm_report.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/algorithm_topic_snapshot.json`

## 剩余风险和下一步建议

- 剩余风险：本轮只证明真实上位机 ROS2 环境和 package 可用，未证明雷达、摄像头、odom/tf、SLAM 或 Nav2 现场链路可用。
- 下一步建议 1：由硬件/平台 owner 先启动最小 bringup，至少让 `/scan`、`/odom`、`/tf` 进入 ROS graph；如果只有 LiDAR 可用，可用 `learn.launch.py lidar_enabled:=true no_motion_static_odom_tf:=true` 做静态 no-motion SLAM smoke。
- 下一步建议 2：确认 camera driver/launch 入口，产出 `/camera/image_raw` 后再补 keyframe 或图像 metadata。
- 下一步建议 3：传感器 topic 存在后，重跑 30 秒目标 rosbag，并优先生成 `map.yaml`、`route.csv` 或 keyframe，不再消费 graph-only fallback bag。
