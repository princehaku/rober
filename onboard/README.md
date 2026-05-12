# onboard/ — Orange Pi 上车 ROS2 主链路

本目录是 `ros_rbs` 的 **上车（on-vehicle）工作区**：Orange Pi Zero 3（Ubuntu 22.04 + ROS2 Humble）上跑的 ROS2 包、launch、Docker 与运维脚本均在此。

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
