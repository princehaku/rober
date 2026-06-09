# Board Bringup Blocker Fix Tech Plan

## sprint_type: epic

## OKR 最低优先级核对

- 当前最低当前 Objective：O7（约 12%），其次 O6（约 30%）。
- 本 sprint 直接服务现场 O3 lane，间接服务 O7/O6：相机 topic、map/keyframe/rosbag 是 O7 route replay / labeling 和 O6 archive 的真实数据前提。

## 设计

### 1. Launch 参数类型修复

在 `bringup.launch.py` 中对 `elevator_assist_target_floor` 使用 ROS launch typed parameter wrapper，确保传给 `task_orchestrator` 时是 string，而不是被 YAML 规则解析成 integer。

### 2. Waypoint manager 缺依赖降级

`waypoint_manager` 目前 top-level import `nav2_simple_commander`，板上缺依赖会导致节点无法启动。改为可选 import：

- 依赖存在：保留现有 Nav2 行为。
- 依赖缺失：节点仍提供 waypoint/learn_mode 服务和 topic；调用导航方法时返回失败并给出可读原因。

### 3. 最小 ROS camera publisher

新增 `ros2_trashbot_vision` console script，例如 `camera_publisher`：

- 参数：`device`、`topic`、`frame_id`、`width`、`height`、`fps`。
- 使用 OpenCV `VideoCapture` 从 `/dev/video0` 读取真实帧，发布 `sensor_msgs/Image`。
- 无法打开设备时 fail closed 并记录原因。
- 加入 `bringup.launch.py` 的可选参数：`camera_enabled` 默认 `false`，避免开发机无相机时影响 build/test。

### 4. SSH preflight source 修复

`field_route_evidence_preflight.py --mode ssh` 的远端 ROS2 检查应通过 `bash -lc` source `/opt/ros/humble/setup.bash` 和候选 workspace setup，再运行 `command -v ros2`、`ros2 pkg list`、`ros2 topic list`。

### 5. 上板验证

构建后同步到真实上位机或在上位机仓库构建，短时运行：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  serial_port:=/dev/ttyS5 \
  serial_baudrate:=115200 \
  lidar_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video0
```

采样：

- `/scan`
- `/camera/image_raw`
- `/odom`
- `/battery`
- `/imu/data`
- `/tf_static`
- `/map`

本轮不发布 `/cmd_vel`。

## 文件范围

允许改动：

- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/waypoint_manager.py`
- `onboard/src/ros2_trashbot_nav/test/test_waypoint_manager_learn_mode_static.py`
- `onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py`
- `onboard/src/ros2_trashbot_vision/setup.py`
- `onboard/src/ros2_trashbot_vision/test/**`
- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/vision/**`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/**`

不得改动：

- WAVE ROVER vendor 文件
- factory firmware
- 串口/速度 launch 默认值，除非只是新增显式 camera 参数

## 验收命令

必须执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/waypoint_manager.py \
  onboard/src/ros2_trashbot_vision/ros2_trashbot_vision/camera_publisher.py \
  onboard/scripts/field_route_evidence_preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/tests/test_field_route_evidence_preflight.py \
  onboard/src/ros2_trashbot_nav/test/test_waypoint_manager_learn_mode_static.py
bash onboard/scripts/docker_humble_build.sh
```

上板验证：

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args"'
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 8 --output sprints/2026.06.09_23-20_board-bringup-blocker-fix/artifacts/preflight_ssh_after_fix.json
```

如能部署到板上，执行短时 bringup + topic sample，并记录 artifact。

## 成功标准

- 本地测试/构建通过。
- preflight SSH 不再假阴性 `blocked_ros2_cli_missing`。
- 若部署成功：`/camera/image_raw` 出现在 ROS graph。
- `task_orchestrator` 和 `waypoint_manager` 不再因上述两个已知 blocker 崩溃。
- manifest 继续 fail-closed，直到 map/route/keyframe/replay 齐全。

## 追加设计：实板传感器栈对齐

硬件排查已经把剩余问题收敛为 launch 组成和实板设备号：

- `/dev/video0` 是 Orange Pi `cedrus` V4L2 M2M 编解码节点，不是图像采集相机；`DV20 USB` 的真实图像节点是 `/dev/video1`，OpenCV 已实读 `480x640x3` 帧。
- `/dev/ttyACM0` 是 STC USB Serial LiDAR，单独运行 `lidar_driver` 可产出 `/scan`。
- 当前 `bringup.launch.py` 没有纳入 `lidar_driver` 或静态 laser TF，因此不能用它判定 `/scan`/`/tf_static` 失败。
- `upper_robot_api.py` 常驻占用 `/dev/ttyS5`，当前 sprint 不做运动，因此传感器 smoke 需要允许跳过 ESP32 bridge，避免串口独占阻塞 camera/LiDAR evidence。

本追加设计只补传感器 evidence 入口，不宣称运动、HIL 或已标定建图完成：

1. 将板上已验证的 `lidar_driver` / `lidar_packets` 同步进本地源码，并注册 console script，消除板端与仓库漂移。
2. `bringup.launch.py` 增加 `base_enabled`，默认 `true`；现场 sensor-only smoke 显式传 `base_enabled:=false`，不碰 `/cmd_vel`，不抢 `/dev/ttyS5`。
3. `bringup.launch.py` 增加 `lidar_enabled`、`lidar_serial_port`、`lidar_serial_baudrate`、`lidar_frame_id`、`lidar_scan_topic` 等参数，默认不启用 LiDAR；现场显式用 `/dev/ttyACM0 @ 150000`。
4. `bringup.launch.py` 增加 `static_laser_tf_enabled` 和 `base_frame_id`/`lidar_frame_id` 相关参数。默认不启用；现场 smoke 可显式启用，用于证明 `/tf_static` topic 链路。该 TF 是 smoke/拓扑证据，不是机械安装标定。
5. camera 默认保持通用 `/dev/video0`，不把单台实板设备号写死；现场命令显式传 `camera_device:=/dev/video1`，并在 docs 记录来源。

追加允许改动：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py`
- `onboard/src/ros2_trashbot_hardware/setup.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py`
- `onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py`
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/**`
- `docs/hardware/**`
- `docs/vision/board_camera_publisher.md`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/**`

追加验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_packets.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py \
  onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_packets.py \
  onboard/src/ros2_trashbot_hardware/test/test_lidar_driver_stubs.py
bash onboard/scripts/docker_humble_build.sh
```

追加上板 smoke（禁止发布 `/cmd_vel`）：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

采样 `/scan`、`/camera/image_raw`、`/tf_static`、`/map`。`/odom` 和运动 smoke 留到串口独占关系处理后单独推进。

## 追加设计：低速运动 Gate

当前底盘串口 `/dev/ttyS5 @ 115200` 被 `upper_robot_api.py` 常驻占用，该服务已证明能发送只读 `T=130` 并观察到 vendor `T=1001` 反馈。为避免主会话绕过现有安全策略，本轮运动尝试采用以下顺序：

1. 先读取 `upper_robot_api.py` 的本地/远端代码和 API 状态，确认是否存在受限 manual/stop endpoint。
2. 只在 API 明确允许、可立即 stop、且能采集前后 feedback 时，执行低速短时 motion smoke。
3. 运动命令上限不得超过 `upper_robot_api.py --max-speed 0.12`，建议 `linear_x<=0.03m/s`、`duration<=1s`，随后立即 stop。
4. 若 API `safe_to_control=false`、`primary_actions_enabled=false` 或 manual endpoint 拒绝执行，则保持 fail-closed，不改用裸串口 `T=1/T=13` 绕过。
5. 本 motion gate 只验证“可控低速运动/停止入口”，不等同 HIL、里程计标定、Nav2 或 delivery success。

追加允许改动：

- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/**`
- `docs/hardware/**`

追加验收命令：

```bash
ssh -p 37878 root@192.168.1.11 'bash -lc "curl -s http://127.0.0.1:8787/; echo; curl -s http://127.0.0.1:8787/api/base/status; echo"'
ssh -p 37878 root@192.168.1.11 'bash -lc "sed -n \"1,260p\" /root/rober/onboard/scripts/upper_robot_api.py"'
```

如果且仅如果 API 明确允许 manual motion，执行一次低速短时命令并立即 stop，同时保存 feedback before/after。若不允许，产出 blocked artifact。

## 追加设计：no-motion 现场证据采集闭环

2026-06-10 的 no-motion 采集已经证明 `/scan`、`/camera/image_raw`、`/tf_static` 和短 rosbag 可用，但 `map.yaml`、`route.csv` 仍失败。根因不是传感器不可用，而是现场 capture 组合还缺三个软件入口：

1. `learn.launch.py` 启动了 `slam_toolbox` 和 `map_recorder`，但没有把本轮已验证的 camera/LiDAR/static TF 组合纳入同一 launch，现场需要手工并跑多个 launch，容易漂移。
2. `route_data_recorder` top-level 依赖 `cv_bridge`，板上缺包时节点在订阅 `/odom` 前直接退出，不能退化为“只记录 route.csv 或无 keyframe”。
3. no-motion 阶段本来不会有真实 `/odom`，但为了验证 route/keyframe/manifest 软件链路，需要显式、默认关闭的 synthetic odom 入口。该入口只能用于 no-motion capture，不得声明运动、里程计标定或 HIL。

本轮功能设计：

- `learn.launch.py`
  - 增加可选 `camera_enabled`、`lidar_enabled`、`static_laser_tf_enabled`，参数名与 `bringup.launch.py` 对齐，默认全部 `false`。
  - 增加 `no_motion_static_odom_tf` 和 `no_motion_mock_odom_enabled`，默认 `false`；现场显式启用时提供静态 `odom -> base_link` 拓扑和零速 `/odom`，仅用于 no-motion route/keyframe/manifest 软件链路验证。
  - 保持 `slam_toolbox` 和 `map_recorder` 默认启动，新增参数不得改变正常学习阶段的运动/传感器默认行为。
- `route_data_recorder.py`
  - 将 `cv_bridge` 改为可选依赖。优先使用 `cv_bridge`；缺失时对常见 `rgb8`、`bgr8`、`mono8`、`bgra8`、`rgba8` 通过 `numpy` + `cv2` 转换；无法转换时只记录 route.csv 并写明原因，不崩溃。
  - 保持 route.csv 表头和 keyframe manifest 契约兼容。
- 测试
  - 增加/更新静态或纯 Python 单测，覆盖 launch 参数、可选依赖降级、unsupported encoding fail-closed。
- 文档
  - 更新 `docs/navigation/field_route_evidence_preflight.md` 和/或新增 no-motion capture 文档，明确 synthetic odom / static TF 是软件证据入口，不是运动或标定证据。

追加允许改动：

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/**`
- `onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py`
- `onboard/src/ros2_trashbot_nav/test/**`
- `docs/navigation/**`
- `sprints/2026.06.09_23-20_board-bringup-blocker-fix/**`

追加验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_bringup/launch/learn.launch.py \
  onboard/src/ros2_trashbot_nav/ros2_trashbot_nav/route_data_recorder.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py \
  onboard/src/ros2_trashbot_nav/test/test_route_data_recorder_static.py
bash onboard/scripts/docker_humble_build.sh
```

追加上板验证（禁止发布 `/cmd_vel`）：

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  no_motion_static_odom_tf:=true \
  no_motion_mock_odom_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1 \
  route_recorder:=true \
  route_output_dir:=/tmp/trashbot_no_motion_route
```

期望结果：

- `route_data_recorder` 不再因 `cv_bridge` 缺失退出。
- `/scan`、`/camera/image_raw`、`/tf_static`、`/odom` 可采样。
- `route.csv` 至少产生 1 条 no-motion 软件链路样本；若 keyframe 可写，`keyframes/` 和 `manifest.json` 同步产生。
- `map.yaml` 若仍失败，必须保存 `slam_toolbox` / TF / scan 失败日志，作为下一轮 SLAM 参数或 TF 修复输入。
