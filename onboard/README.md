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

Compose 需在 `onboard/` 下执行，使挂载上下文为上车目录：

```bash
cd onboard
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml run --rm humble
```

## Orange Pi 上位机部署

上位机缺少裸机 ROS2/colcon 时，优先把仓库同步到独立目录（例如 `/root/rober`），再在远端执行 `bash onboard/scripts/docker_humble_build.sh` 做 Docker/Humble 构建验证。同步时排除 `.git/`、`build/`、`install/`、`log/`、`__pycache__/`、`node_modules/` 等派生产物，避免覆盖远端未知业务目录。

Orange Pi 上的 Docker 可能只有 legacy builder，没有 `buildx`，此时脚本会自动省略 `docker build --progress` 参数并打印 `docker_build_progress_arg=unsupported_legacy_builder`。这只是构建入口降级，不代表 ROS2 构建通过；若继续失败在 `FROM osrf/ros:humble-desktop`，优先检查国内 Docker registry mirror、DNS 和离线 arm64 镜像导入。

## LAN-only WebRTC 摄像头 smoke

摄像头首轮上车验证使用 `onboard/scripts/local_webrtc_camera_smoke.py`。该服务跑在 Orange Pi 上，页面和 signaling 都是本机 HTTP，同 WiFi / 同 LAN 浏览器只接收 WebRTC 视频，不发送机器人控制，不连接云 relay，也不要求公网 TURN。

```bash
PORT=8088 ROBER_CAMERA_SOURCE=0 bash onboard/scripts/local_webrtc_camera_smoke.sh
```

浏览器访问 `http://<orange-pi-lan-ip>:8088/`。诊断接口为 `/health` 和 `/devices`；如果缺 `aiortc`、`av`、`aiohttp` 或 OpenCV，服务会降级为诊断页并让 `/offer` 返回明确依赖错误，不能把该状态当作 WebRTC 播放成功。

机器可读 offer-level 自检：

```bash
python3 onboard/scripts/local_webrtc_camera_smoke.py --self-test-url http://127.0.0.1:8088 --self-test-timeout 8
```

自检会输出单行 JSON：`status=ok` 表示 `/offer` 返回 answer 且收到至少一帧；`status=degraded/failed` 会给出依赖缺失、服务不可达、offer 拒绝或首帧未到的明确原因。接口和 vendor 来源边界见 `docs/interfaces/o7_local_webrtc_camera_smoke.md`。

自检成功后会用 `/offer` answer 返回的 `peer_id` 主动关闭本次服务端 peer，避免连续运行时被单连接保护误判为 `camera_in_use`。

## 运行时契约

- **与 `cloud-relay/`**：`remote_bridge` 通过 HTTP 与云端中继交互；phone-safe API 由云端维护。
- **与 `mobile/`、`pc-tools/`**：无直接运行时依赖；PC 工具可离线消费本目录产出的数据文件。

## 资料与纪律

硬件、UART、底盘协议等必须以 `docs/vendor/VENDOR_INDEX.md` 为准；代码注释与验证要求见 `AGENTS.md`。
