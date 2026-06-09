# Board Bringup Blocker Fix Pre Start

## sprint_type: epic

## 背景

上一轮 `sprints/2026.06.09_23-00_board-live-full-stack-evidence/` 已在真实上位机短时启动 ESP32 bridge 与 LiDAR driver，证明 `/scan`、`/odom`、`/battery`、`/imu/data`、`/cmd_vel`、`/map`、`/tf_static` 可进入 ROS graph。

剩余 blocker 已从“现场不通”收敛为具体软件/运行时缺口：

- `task_orchestrator`：`elevator_assist_target_floor` 被 launch 解析成 INTEGER，但节点声明为 STRING。
- `waypoint_manager`：板上缺 `nav2_simple_commander`，导致 import 阶段崩溃。
- 摄像头：设备存在、WebRTC camera smoke 在跑，但 ROS graph 没有 `/camera/image_raw`。
- preflight：现有 SSH 模式未 source ROS setup，导致 `blocked_ros2_cli_missing` 假阴性。

## 目标

修复最小 bringup blocker，并重新上板验证：

1. full bringup 不再因 `task_orchestrator` 参数类型崩溃。
2. `waypoint_manager` 在缺 `nav2_simple_commander` 时至少能以 learn/waypoint service 模式存活，不阻塞 bringup。
3. `bringup.launch.py` 可选启动真实 camera ROS publisher，产出 `/camera/image_raw`。
4. `field_route_evidence_preflight.py --mode ssh` 能在远端正确 source ROS2/workspace 后检测 ROS2。
5. 重新短时上板验证 `/scan`、`/camera/image_raw`、`/odom`、`/tf_static`、`/map`，并尝试 no-motion map/keyframe/manifest gate。

## Owner

- 主责：`robot-software-engineer`
- 协作事实来源：上一轮 hardware/algorithm/software artifact

## 边界

- 不改 WAVE ROVER 协议、串口默认硬件假设或固件。
- 不执行运动 smoke；本轮先消除 bringup / camera / preflight blocker。
- `/cmd_vel` 可观测不等于可运动，`safe_to_control` 继续 false。
