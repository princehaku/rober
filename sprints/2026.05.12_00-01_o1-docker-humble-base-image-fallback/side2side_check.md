# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-11 23:15 Asia/Shanghai
- 检查结论：Docker daemon、storage、当前 builder 可响应；运行验证 blocked 在 Docker registry mirror/proxy 返回 HTML 与本地镜像 tag manifest 不可运行，证据范围限定为 `software_proof_docker_only`

## 对照检查

| 需求 | 结果 | 证据 |
| --- | --- | --- |
| Dockerfile 支持 `ARG ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop` 并作为 `FROM` | 通过 | `docker/humble/Dockerfile` 已改为 ARG + `FROM ${ROS_HUMBLE_BASE_IMAGE}` |
| build script 支持 `ROS_HUMBLE_BASE_IMAGE` 并传入 build arg | 通过 | `docker build` 增加 `--build-arg ROS_HUMBLE_BASE_IMAGE=...` |
| 保持 `ROS_HUMBLE_IMAGE` 和 `SKIP_COLCON` 语义 | 通过 | 默认目标镜像仍为 `ros-rbs-humble:dev`；`SKIP_COLCON=1` 镜像 ready 后退出 |
| 新增 `SKIP_DOCKER_BUILD=1` 本地镜像复用路径 | 通过实现，当前本机运行 blocked | 目标镜像存在且可运行时跳过 build；目标镜像缺失或不可运行时快速失败并提示 `docker pull`/`docker load`/正常 build |
| preflight 输出软件证据边界和关键字段 | 通过 | 输出 `evidence_scope=software_proof_docker_only`、`target_image`、`base_image`、`base_image_override`、`skip_docker_build`、`skip_colcon`、`local_target_image_present`、`local_image_reuse` |
| 不声明真实 HIL 或 `hil_pass` | 通过 | 文档和输出均限定为 Docker-only/software proof |

## 验收摘要

- `docker version`：通过，Client/Server 均为 `28.3.3`，Docker Desktop `4.45.0`，说明 daemon 不属于完全不可用。
- `docker info` / `docker buildx ls`：`desktop-linux` builder running，registry mirrors 包含 Aliyun、dockermirror、dockerpull、DaoCloud；旧 `default` builder endpoint 异常但非当前构建实例。
- `docker image inspect ros-rbs-humble:dev`：tag 存在，但 `Architecture=`、`Os=` 为空且 `Size=20381`，属于不可直接视为可运行镜像的异常元数据。
- `docker run --rm ros-rbs-humble:dev true`：失败，`descriptor is neither a manifest or index`。
- `docker pull osrf/ros:humble-desktop`：失败，`unexpected media type text/html`。
- `bash -n scripts/docker_humble_build.sh`：通过。
- `SKIP_COLCON=1 ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop bash scripts/docker_humble_build.sh`：失败，`osrf/ros:humble-desktop` metadata 返回 `text/html`，分类为 `registry mirror/proxy`。
- `SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`：失败，`ros-rbs-humble:dev` tag 存在但不可运行，`docker run` 返回 `descriptor is neither a manifest or index`。
- `SKIP_DOCKER_BUILD=1 SKIP_COLCON=1 ROS_HUMBLE_IMAGE=ros-rbs-humble:missing-skip-build-check bash scripts/docker_humble_build.sh`：按预期快速失败，用于证明缺失本地镜像时不会继续冒充 build path。
- `git diff --check -- scripts/docker_humble_build.sh docker/humble/Dockerfile sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/tech-done.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/side2side_check.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md`：通过。

## 用户侧判定

本轮把“Docker 不能用吗”拆成了可验证结论：Docker daemon 和当前 builder 可用；外部 base image 拉取链路和本地目标镜像 manifest 不可用。registry mirror/proxy 阻断后的操作路径从“只能分类失败”推进为三条可执行路径，但本机仍缺可运行目标镜像：

1. 覆盖 `ROS_HUMBLE_BASE_IMAGE` 使用可访问的 Humble base image。
2. 预先准备可运行的 `ROS_HUMBLE_IMAGE` 目标镜像后用 `SKIP_DOCKER_BUILD=1` 直接跑后续逻辑。
3. 本地镜像缺失时快速失败，给出明确 operator 动作。

本轮仍不是上车验收，不能升级 O1 的 HIL 完成度。
