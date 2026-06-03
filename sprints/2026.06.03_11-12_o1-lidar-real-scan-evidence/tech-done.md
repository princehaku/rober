# O1 LiDAR Real Scan Evidence Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- 本轮按 O1 最低优先级推进 LiDAR 真实材料线，目标是从 `/dev/ttyACM0` 设备/合同证明继续逼近真实 ROS2 `/scan`。
- Hardware Infra Engineer 已在上位机 `ssh root@192.168.1.11 -p 37878` 做远端验证：
  - `/dev/ttyACM0 @150000` 可打开。
  - 写入 vendor 启动命令 `a5 60` 后，3 秒读到 `4246` bytes。
  - 原始数据中观察到 `0xaa55` sync header `127` 个。
  - 退出时发送 vendor 停止序列 `a5 00 a5 65 a5 65`。
- 本轮没有执行底盘 motion：没有 POST `/api/base/manual`，没有写 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- 同步更新：
  - `OKR.md`：O1 仍约 94%，但证据口径从 LiDAR 设备/合同推进到 raw packet observed；ROS2 `/scan` 仍 `not_proven`。
  - `docs/interfaces/lidar_ros2_closed_loop.md`：补充本轮远端 raw packet 证据与 ROS2 `/scan` blocker。
  - `docs/process/okr_progress_log.md`：追加本轮 O1 收口记录。

## Adopted Sources

- `AGENTS.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `sprints/2026.06.03_04-05_o1-lidar-ttyacm0-ros2/tech-done.md`
- `sprints/2026.06.03_10-11_okr-current-state-refresh/tech-done.md`

## Verification

远端只读/启动停止 smoke：

```text
ssh root@192.168.1.11 -p 37878
LiDAR raw serial smoke:
  port=/dev/ttyACM0
  baudrate=150000
  start_command=a5 60
  bytes_read_3s=4246
  sync_header_0xaa55_count=127
  stop_command=a5 00 a5 65 a5 65
```

ROS2 `/scan` 采集尝试结果：

```text
ros2 scan smoke: not completed
host ROS2: /opt/ros/humble/setup.bash missing; ros2 command not found
workspace install: /root/rober/onboard/install missing
remote repo setup.py: old ros2_trashbot_hardware entry points, no lidar_driver
docker amd64 image on Orange Pi arm64: exec format error
docker pull linux/arm64/v8 osrf/ros:humble-ros-base: Client.Timeout exceeded while awaiting headers
```

本地文档校验：

```text
git diff --check -- OKR.md docs/interfaces/lidar_ros2_closed_loop.md docs/process/okr_progress_log.md sprints/2026.06.03_11-12_o1-lidar-real-scan-evidence/tech-done.md
# passed
```

## Remaining Risks

- 真实 ROS2 `/scan`、`/lidar/raw_packet` topic、`tf2_echo base_link laser_frame`、SLAM/Nav2 消费仍未证明。
- 当前只证明 LiDAR 原始串口数据真实可读，不能声明 ROS2 LiDAR driver、TF、建图质量、长期稳定性或 HIL pass。
- 上位机需要先补齐可运行的 ROS2 Humble arm64 环境、部署当前仓库 install，或提供可用 arm64 ROS2 Docker 镜像缓存后再复跑 `/scan` smoke。
- 底盘 `T=1001`、robot ACK、真实 `/odom`、`/imu/data`、`/battery`、自动停车/急停现场演练和完整上车任务仍为 `not_proven`。
