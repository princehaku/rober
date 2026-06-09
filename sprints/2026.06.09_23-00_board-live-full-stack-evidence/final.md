# Board Live Full Stack Evidence Final

## 收口状态

状态：部分完成，fail-closed。

本轮把 ROS graph blocker 从“只有 `/rosout` 和 `/parameter_events`”推进到“真实上位机可短时启动 ESP32 bridge 和 LiDAR driver，并发布 `/scan`、`/odom`、`/battery`、`/imu/data`、`/cmd_vel`、`/map`、`/tf_static`”。这证明平台最小 bringup 有可用入口，不再是纯 SSH 或 package proof。

本轮没有达成完整 field evidence packet：缺 `/camera/image_raw`、动态 `/tf`、`map.yaml`、`route.csv`、keyframes、replay JSONL 和安全运动 smoke。`field_evidence_manifest.json` 已按预期保持 fail-closed。

## 关键证据

- 远端 `bringup.launch.py --show-args` 成功，包含 `serial_port`、`serial_baudrate`、`command_mode`、`lidar_enabled`、`lidar_serial_port`、`lidar_serial_baudrate` 等参数。
- 远端 `learn.launch.py --show-args` 成功，包含 `route_recorder`、`route_output_dir`、`route_camera_topic`、`route_odom_topic`、`lidar_enabled`、`no_motion_static_odom_tf`、`map_dir` 等参数。
- 短时 bringup 使用硬件 agent 已证明的 `/dev/ttyS5 @ 115200` 和 LiDAR `/dev/ttyACM0 @ 150000`。
- `esp32_bridge` 日志显示已连接 WAVE ROVER ESP32。
- `lidar_driver` 日志显示 LiDAR serial 已启动。
- `/scan` one-shot LaserScan 样本已保存。
- `/odom` one-shot 样本已保存。
- graph-only bag 已拉到本地 artifact root。

## 未通过项

- `waypoint_manager` 失败：`ModuleNotFoundError: No module named 'nav2_simple_commander'`。
- `task_orchestrator` 失败：`elevator_assist_target_floor` 参数被 launch/ROS 解析成 INTEGER，但节点期待 STRING。
- 摄像头未进入 ROS graph：`/camera/image_raw` unknown。
- 动态 TF 未进入 ROS graph：`/tf` 未发布，仅 `/tf_static` 存在。
- 建图未完成：没有 `map.yaml` 或 SLAM save 成功证据。
- 运动未执行：未满足安全 gate，且本轮任务默认不做 motion。

## Manifest 结论

`artifacts/field_evidence_manifest.json`：

- `status=blocked_artifacts_missing`
- `gate_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `present_artifacts=["rosbag"]`
- `missing_artifacts=["map_yaml","route_csv","keyframes","replay_jsonl"]`

`artifacts/preflight_ssh.json`：

- `status=blocked_ros2_cli_missing`
- 这是脚本环境探测限制：现有脚本直接远端执行 `command -v ros2`，没有 source setup；手工 `bash -lc` source 后 ROS2 实际可用。

## OKR 进展回顾

- O3 现场验证 lane：进展增加。已拿到真实 LiDAR 和底盘 bridge ROS topic 证据，但还没形成 map/route/keyframe/replay 可复用材料。
- O6：可消费本轮 fail-closed manifest 和 artifact root，作为真实上位机 blocked evidence。
- O7：仍缺真实 route/keyframe/replay，PC route replay / labeling 不能因此解锁。
- O1：真实 WAVE ROVER UART 可由硬件 agent 的只读反馈和本轮 `esp32_bridge` 连接共同支撑，但未做运动/HIL，不能宣称 HIL 通过。

## 下一步

1. 在板上修复 `nav2_simple_commander` 依赖和 `elevator_assist_target_floor` 参数类型，确保 full bringup 不再有业务节点启动崩溃。
2. 明确 camera ROS driver 启动入口，产出 `/camera/image_raw`。
3. 用短时 `learn.launch.py lidar_enabled:=true no_motion_static_odom_tf:=true` 生成 no-motion SLAM smoke，目标是 `map.yaml`。
4. 只有当现场安全 gate 明确通过，且 `/cmd_vel` subscriber、`/odom` before/after、stop 观察链齐备时，再执行低速 motion smoke。

## 最终风险

- 当前证据不是完整路线采集，不可用于真实送达成功声明。
- 当前 `/odom` 仍需通过真实运动验证；无运动时零 pose/twist 只能证明 topic 链路存在。
- 当前 graph-only bag 不含 `/scan` 或 `/odom`，后续必须在 bringup 已启动状态下重录目标 rosbag。
- 远端安装包与本地源码存在差异，后续改代码前需要先同步板上 commit/build 状态。
