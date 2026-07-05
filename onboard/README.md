# onboard/ — Orange Pi 上车 ROS2 主链路

本目录是 `rober` 的 **上车（on-vehicle）工作区**：Orange Pi Zero 3（Ubuntu 22.04 + ROS2 Humble）上跑的 ROS2 包、launch、Docker 与运维脚本均在此。

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `onboard/src/ros2_trashbot_*` | 六个 ROS2 包（interfaces / hardware / nav / vision / behavior / bringup） |
| `onboard/docker/humble/Dockerfile` | Humble 开发/构建镜像 |
| `onboard/docker-compose.humble.yml` | Compose：挂载本目录到容器 `/ws` |
| `onboard/scripts/` | `docker_humble_build.sh`、`docker_humble_dev.sh`、`run_smoke_tests.sh`、硬件 smoke 等 |

## 标准命令（从仓库根执行）

```bash
bash onboard/scripts/docker_humble_build.sh
bash onboard/scripts/run_smoke_tests.sh
bash onboard/scripts/docker_humble_dev.sh
```

## RViz2 调试视图

工程调试地图、雷达、TF、小车位置和 Nav2 路线时，可在已 source 上车工作区后启动只读观察视图：

```bash
ros2 launch ros2_trashbot_bringup rviz.launch.py
```

默认配置安装在 `ros2_trashbot_bringup/rviz/trashbot_nav.rviz`，显示 `/map`、`/scan`、TF、`/plan` 和 `/amcl_pose`。
该 RViz 配置不包含 2D Goal 工具；真实发车仍必须走 PC 工作站安全确认后的固定执行入口。

需要浏览器远程观察时，可在已安装 `foxglove_bridge` 的 ROS2 环境中手工启动 bridge：

```bash
ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

Foxglove 只用于远程共享观察 `/map`、`/scan`、TF、路径和位姿；普通操作仍优先使用 PC 工作站 `/map` 大地图和安全确认后的固定控制入口。

2026-06-30 起，PC 工作站调用上车 `/api/nav2/goal/execute` 时会随请求携带当前图上路线元数据
（预览点数、源点数、frame、起点、终点）。`onboard/scripts/upper_robot_api.py` 会把这些字段回显到
Nav2 execution `goal_request` / latest readback，便于现场证明本次执行绑定的是当前图上完整路线读数；
该回显不改变 Nav2 发车门禁，真实执行仍必须由 PC 安全确认后的固定入口触发。

2026-07-06 起，`scripts/upper_robot_api.py` 用 WAVE ROVER `T=1001` feedback 里的 IMU
`r/p` roll/pitch 判断低速短脉冲是否有车体运动迹象，当前阈值为 `0.35°`。该阈值用于 PC
WASD/手控的 `motion_signal_observed=imu_attitude_delta`，不能替代同窗口 wheel raw `L/R` 非零、
Nav2 完整路线或 delivery success。协议字段来源见 `docs/vendor/VENDOR_INDEX.md` 指向的 WAVE ROVER
`IMU_ctrl.h` 和 `json_cmd.h`。

2026-07-01 起，LiDAR driver 每秒 diagnostics 会携带最近一帧 `/scan` 派生的结构化
`scan_preview_points`。上车 `/api/radar/scan-proof/refresh` 默认消费该 diagnostics 写入
`runtime/lidar_scan_proof_latest.json`，不再默认启动 `ros2 topic echo/hz` CLI collector；
只有显式传 `collector_mode=legacy_ros2_cli` 时才走旧工程采样路径。该刷新仍只读雷达 runtime，
不触碰 WAVE ROVER 底盘 UART `/dev/ttyS5`，不发布 `/cmd_vel`，不发送 manual/Nav2/free-roam/delivery
运动命令。现场验证口径以 `/api/map/preview.radar_overlay_status=loaded` 和当前
`radar_overlay.scan_preview_point_count` 为准。

Compose 需在 `onboard/` 下执行，使挂载上下文为上车目录：

```bash
cd onboard
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml run --rm humble
```

## 运行时契约

- **与 `cloud-relay/`**：`remote_bridge` 通过 HTTP 与云端中继交互；phone-safe API 由云端维护。
- **与 `mobile/`、`pc-tools/`**：无直接运行时依赖；PC 工具可离线消费本目录产出的数据文件。

## 资料与纪律

硬件、UART、底盘协议等必须以 `docs/vendor/VENDOR_INDEX.md` 为准；代码注释与验证要求见 `AGENTS.md`。
