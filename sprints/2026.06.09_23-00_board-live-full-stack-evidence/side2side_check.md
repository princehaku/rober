# Board Live Full Stack Evidence Side2Side Check

## 对照结论

本轮满足“不能只停留在 SSH 探针”的验收底线：已经在真实上位机短时启动平台 bringup，并让真实 `/scan`、`/odom`、`/battery`、`/imu/data`、`/cmd_vel`、`/map`、`/tf_static` 进入 ROS graph。

本轮不满足“完整现场 evidence packet”的产品验收：缺 camera topic、动态 `/tf`、`map.yaml`、`route.csv`、keyframes 和 replay JSONL，manifest 正确保持 fail-closed。

## PRD P0 对照

| P0 项 | 状态 | 证据 |
| --- | --- | --- |
| SSH 成功证据 | pass | `op-z3-b6.home`、CST 时间、Linux aarch64 已记录在硬件/算法/软件 raw log。 |
| ROS2 runtime 证据 | pass | `bash` source `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash` 后，trashbot package 可发现。 |
| 雷达证据 | partial pass | `/scan` 注册，`lidar_driver` 发布 LaserScan one-shot 样本。 |
| 摄像头证据 | fail | `/camera/image_raw` unknown，当前没有 ROS camera topic。 |
| 建图证据 | fail | `/map` topic 注册但未保存 `map.yaml`，也没有可复用 SLAM/map artifact。 |
| 运动证据 | fail-closed | `/cmd_vel` 有 subscriber、`/odom` 可观测，但没有安全 gate 和 HIL clearance；未发运动。 |
| artifact root | partial pass | 已集中保存 hardware/algorithm/software raw log、reports、preflight、manifest、graph-only bag 和 bringup logs。 |
| manifest | pass as fail-closed | `field_evidence_manifest.json` 生成，`gate_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。 |

## 四个 Gate 复核

### 雷达

状态：部分通过。

事实：

- `bringup.launch.py lidar_enabled:=true` 后 `/scan` 出现。
- `/scan` publisher 是 `lidar_driver`。
- `topic echo --once /scan` 有非空 ranges 和 intensities。

限制：

- 本轮只做短时 one-shot，没有 30 秒稳定 hz 证明。
- 没有完整传感器 rosbag；现有 rosbag 是 graph-only fallback。

### 摄像头

状态：未通过。

事实：

- 设备层硬件报告看到 `/dev/video0`、`/dev/video1`、`/dev/video2`。
- ROS graph 中 `/camera/image_raw` 不存在。

限制：

- 本轮没有 camera ROS driver 入口证据。
- 无 keyframe、图片样本或 camera metadata artifact。

### 建图

状态：未通过。

事实：

- 短时 bringup 中 `/map` topic 存在。
- pulled graph-only bag 存在，但只含 `/rosout` 和 `/parameter_events`。

限制：

- 没有 `map.yaml`。
- 没有 SLAM save service 成功证据。
- 没有 route/keyframe/replay artifact。

### 运动

状态：未通过，且按安全策略保持关闭。

事实：

- `/cmd_vel` 有 `esp32_bridge` subscriber。
- `/odom` 可 echo，但样本为无运动的零 pose/twist。
- 硬件 agent 已证明 WAVE ROVER `/dev/ttyS5 @ 115200` 可用只读 `T=130` 采到 `T=1001`。

限制：

- `safe_to_control=false`。
- `primary_actions_enabled=false`。
- `delivery_success=false`。
- 本轮无现场安全确认和运动授权，未发布 `/cmd_vel`。

## 与 OKR 的关系

- 对 O3 现场验证 lane：有真实 LiDAR 和 ESP32 bridge topic 证据，但仍不能生成真实地图/路线材料。
- 对 O6 archive：manifest 和 artifact root 已形成 fail-closed intake，可被后续 archive 消费为 blocked evidence。
- 对 O7 replay/labeling：尚缺 route/keyframe/replay 输入，不能推进真实回放和标注。

## 下一步最小验收动作

1. 修复/安装远端 `nav2_simple_commander`，解除 `waypoint_manager` 启动失败。
2. 修复 `task_orchestrator` 的 `elevator_assist_target_floor` 参数类型问题。
3. 启动 camera ROS driver，补 `/camera/image_raw`。
4. 用 `learn.launch.py lidar_enabled:=true no_motion_static_odom_tf:=true` 做静态 no-motion SLAM smoke，验证能否产出 `map.yaml`。
5. 在现场安全 gate 明确通过后，再做低速 `/cmd_vel` smoke 和 stop。
