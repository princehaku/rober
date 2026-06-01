# Tech Done

sprint_type: micro

## 实际改动

- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - 增加 `lidar_enabled` gate，默认 `false`，避免无真实 LiDAR 串口时阻塞学习阶段。
  - 增加与 `bringup.launch.py` 对齐的 LiDAR 参数：`lidar_serial_port`、`lidar_serial_baudrate`、`lidar_frame_id`、`lidar_scan_topic`、`lidar_raw_packet_topic`、`lidar_publish_raw_packets`、range/timing、TF offset、`lidar_mock_packets`、`lidar_mock_scan`。
  - `lidar_enabled:=true` 时启动 `ros2_trashbot_hardware/lidar_driver` 和 `tf2_ros/static_transform_publisher`，提供 `base_link -> laser_frame` 占位 TF。
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`
  - 静态 launch contract 从只覆盖 `bringup.launch.py` 扩展到同时覆盖 `learn.launch.py`。
  - 增加学习阶段 LiDAR 节点在 SLAM 节点前声明的 contract 检查，确保真机建图 smoke 的输入链路先就绪。
- `docs/hardware/lidar_ros_reference.md`
  - 更新 Stage 2 状态：`learn.launch.py` 也支持 gated LiDAR/TF，且参数名与 bringup 对齐。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 更新 launch owner 和真机建图 smoke 入口说明，明确静态验证不能替代真机 LiDAR/TF/SLAM 证据。

## 验证结果

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'`
  - 结果：`Ran 11 tests in 0.083s`，`OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'`
  - 结果：`Ran 5 tests in 0.001s`，`OK`。
- `python3 -m compileall -q onboard/src/ros2_trashbot_bringup onboard/src/ros2_trashbot_hardware`
  - 结果：通过，无输出。
- `git diff --check -- onboard/src/ros2_trashbot_bringup/launch/learn.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py docs/hardware/lidar_ros_reference.md docs/interfaces/lidar_ros2_closed_loop.md sprints/2026.06.02_00-01_lidar-real-slam-smoke/tech-done.md`
  - 结果：通过，无输出。

## 剩余风险

- 本轮未运行底盘运动命令，也不应把本轮结果解释为底盘 HIL 或真机 LiDAR 通过。
- 真实 LiDAR USB path、`150000` 波特率稳定性、`base_link -> laser_frame` 实测安装位姿、`/scan` 连续发布、SLAM/Nav2 消费链路仍需 Hardware/Algorithm 上车验证。
- `lidar_tf_x/y/z/roll/pitch/yaw` 默认全零只是软件闭环占位；真机建图前必须用实测安装位姿覆盖。

## OKR 最低优先级提示

本 micro sprint 针对当前最低 Objective O1：硬件协议可信底盘中的真实 LiDAR/SLAM 缺口推进软件侧 launch contract。

## Algorithm runtime 验证补充（2026-06-02）

### 自主能力目标和本轮抓手

- 目标：验证“真机 LiDAR + ROS2 建图”能否进入最小 no-motion runtime smoke。
- 抓手：先只读确认真实 LiDAR 设备路径、远端 `learn.launch.py` 是否已包含 `lidar_enabled` gate、远端是否存在 ROS2/colcon 或可用 Docker/Humble 入口。
- 安全边界：未发送 `cmd_vel`、`T=1`、`T=13`、`T=131` 或任何底盘运动命令；没有把 `/dev/ttyACM0` 当 LiDAR；没有启动 LiDAR driver。

### 只读验证命令与关键输出

1. 远端设备/环境复核：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'sh -lc "hostname; ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/* 2>/dev/null || true; command -v ros2 || true; command -v colcon || true; docker --version || true"'
```

关键输出：

```text
op-z3-b6.home
/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0
/dev/ttyACM0
Docker version 27.3.1, build ce12230
```

结论：未发现 `/dev/ttyUSB0`；唯一 by-id 是 `usb-STC_STC_USB_Serial-if00`，只能归因于 STC USB Serial，不能作为 LiDAR。`command -v ros2` 和 `command -v colcon` 无输出，宿主机 ROS2/colcon 不在 PATH。

2. 远端 `learn.launch.py` 和 install/src 状态：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'sh -lc "grep -n \"lidar_enabled\|async_slam_toolbox_node\" /root/rober/onboard/src/ros2_trashbot_bringup/launch/learn.launch.py 2>/dev/null || true; ls -ld /root/rober/onboard/install /root/rober/onboard/src 2>/dev/null || true"'
```

关键输出：

```text
94:            executable='async_slam_toolbox_node',
drwxrwxrwx 9 root root 4096 May 13 01:22 /root/rober/onboard/src
```

结论：远端 `learn.launch.py` 尚未包含本地新增的 `lidar_enabled` 参数或 gated LiDAR/TF；`/root/rober/onboard/install` 未列出，不能证明远端已有已构建 install。

3. 额外只读 Docker/Humble 入口复核：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'sh -lc "cd /root/rober/onboard 2>/dev/null && ls -l scripts/docker_humble_dev.sh scripts/docker_humble_build.sh docker-compose.humble.yml 2>/dev/null || true; docker image ls --format \"{{.Repository}}:{{.Tag}} {{.ID}} {{.CreatedSince}}\" | grep -E \"(^ros-rbs-humble:dev|osrf/ros:humble)\" || true"'
```

关键输出：

```text
docker-compose.humble.yml
scripts/docker_humble_build.sh
scripts/docker_humble_dev.sh
osrf/ros:humble-desktop 3b72f30a8344 2 weeks ago
```

结论：远端存在 Docker/Humble 脚本和 `osrf/ros:humble-desktop` 基础镜像，但未观察到 `ros-rbs-humble:dev` 本项目镜像；结合缺少真实 LiDAR 设备和远端 launch 未部署，本轮不启动容器 runtime smoke。

### 失败定位分类

- LiDAR 设备缺失：blocked。当前只看到 STC `/dev/ttyACM0`，没有可合理归因于 LiDAR 的 `/dev/ttyUSB*` 或 by-id 节点。
- 远端 learn launch 未部署：blocked。远端 `learn.launch.py` 只有 `async_slam_toolbox_node` 命中，没有 `lidar_enabled` 命中。
- Docker/ROS 可运行性：partial。Docker daemon 和基础镜像存在，但宿主 `ros2`/`colcon` 不在 PATH，远端 `install/` 和 `ros-rbs-humble:dev` 项目镜像未观察到。
- SLAM 订阅失败：not_run。由于真实 LiDAR 设备 unknown，按安全边界没有启动 driver，也没有启动 SLAM runtime smoke。

### 数据、样本或调试输出变化

- 本轮没有产生真实 `/scan` 样本。
- 本轮没有产生真实 `base_link -> laser_frame` TF 输出。
- 本轮没有产生 `/map` 或 SLAM Toolbox 建图证据。
- 本轮新增的唯一证据是远端只读设备、launch 部署和 Docker/Humble 入口日志。

### 剩余风险和下一步建议

- 先由 Hardware Infra 现场确认 LiDAR 供电、USB 线、USB-UART 枚举和 by-id 命名；在出现非 STC、非 `/dev/ttyACM0` 且可归因于 LiDAR 的设备前，不应启动 LiDAR driver。
- 将本地包含 `lidar_enabled` 的 `learn.launch.py` 和相关 ROS2 LiDAR 包部署到远端后，再验证 `install/` 或项目 Docker 镜像。
- 下一轮 no-motion smoke 的准入条件：明确 `<real_lidar_device>`、远端 `learn.launch.py` 命中 `lidar_enabled`、容器或 install 可用；再采集 `ros2 topic echo --once /scan`、`ros2 topic hz /scan`、`tf2_echo base_link laser_frame` 和 `/map`/SLAM 订阅证据。
