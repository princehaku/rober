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
