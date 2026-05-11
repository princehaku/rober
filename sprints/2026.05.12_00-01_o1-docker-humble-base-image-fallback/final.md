# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - Final

## 状态

- 阶段：final
- 时间：2026-05-11 23:15 Asia/Shanghai
- 结果：工程实现完成；Docker daemon 可用，运行验证 blocked 在 Docker registry mirror/proxy 和本地镜像 manifest 不可运行
- 证据范围：`software_proof_docker_only`
- OKR 更新：未更新 `OKR.md` 完成度

## 本轮完成内容

- Docker Humble base image 从硬编码 `FROM osrf/ros:humble-desktop` 改为可配置 `ROS_HUMBLE_BASE_IMAGE`，默认行为不变。
- `scripts/docker_humble_build.sh` 支持把 `ROS_HUMBLE_BASE_IMAGE` 传给 Docker build。
- 新增 `SKIP_DOCKER_BUILD=1` 本地目标镜像复用路径：
  - 本地已有且可运行的 `ROS_HUMBLE_IMAGE` 时跳过 Docker build，继续 `SKIP_COLCON` 或容器内 `colcon build`。
  - 本地缺失或不可运行时快速失败，提示 `docker pull`、`docker load` 或取消 skip build 后正常构建。
- preflight 明确输出目标镜像、base image、override 状态、skip 状态、本地镜像复用状态和 `software_proof_docker_only` 证据边界。

## 验证

- `docker version`：通过，Client/Server 均为 `28.3.3`，Docker Desktop `4.45.0`，daemon 可响应。
- `docker info` / `docker buildx ls`：当前 `desktop-linux` builder running，storage driver 为 `overlayfs`，registry mirrors 已配置；旧 `default` builder endpoint 报 `/var/run/docker.sock` 不通，但当前构建用的是 `desktop-linux`。
- `docker image inspect ros-rbs-humble:dev`：tag 存在，但 `Architecture=`、`Os=` 为空且 `Size=20381`，不是可运行证据。
- `docker run --rm ros-rbs-humble:dev true`：失败，`descriptor is neither a manifest or index`。
- `docker pull osrf/ros:humble-desktop`：失败，`unexpected media type text/html`。
- `bash -n scripts/docker_humble_build.sh`：通过。
- `SKIP_COLCON=1 ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop bash scripts/docker_humble_build.sh`：失败，`docker.io/osrf/ros:humble-desktop` metadata 返回 `text/html`，分类为 `registry mirror/proxy`。
- `SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`：失败，目标镜像 tag 存在但不可运行，`docker run` 返回 `descriptor is neither a manifest or index`，脚本快速提示替换本地镜像。
- `SKIP_DOCKER_BUILD=1 SKIP_COLCON=1 ROS_HUMBLE_IMAGE=ros-rbs-humble:missing-skip-build-check bash scripts/docker_humble_build.sh`：按预期快速失败，验证缺失本地镜像时的 operator 提示。
- `git diff --check -- scripts/docker_humble_build.sh docker/humble/Dockerfile sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/tech-done.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/side2side_check.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md`：通过。

## Block 状态

- 本轮工程实现未 blocked，但 Docker-only 运行验证 blocked。
- Docker daemon 不属于完全不可用：daemon、context、storage、当前 builder 可查询且可进入 build 流程。
- 默认 build blocked：Docker registry mirror/proxy 对 `docker.io/osrf/ros:humble-desktop` 返回 HTML。
- skip-build blocked：本机 `ros-rbs-humble:dev` tag 存在但不可运行，镜像表现为 0B/manifest descriptor 异常。
- 下一步 operator 动作：修复或更换 Docker registry mirror/proxy 后正常 build；或从可信机器导出可运行 `ros-rbs-humble:dev` 后在本机 `docker load`，再执行 `SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`。

## OKR 与剩余风险

- 本轮只推进 O1 的 Docker/Humble build readiness，属于软件证据。
- 未接入真实串口、WAVE ROVER、ESP32 或 Orange Pi；没有 `command.txt`、`serial.log`、`feedback_T1001.log` evidence packet。
- 不声明 `hil_pass`，不证明底盘真实运动、反馈解析或同一 `evidence_ref` 的路线 replay。

## 协同需求

- Product：无需变更 OKR 完成度；后续有真实 HIL evidence packet 后再更新。
- Hardware：下一步仍需真实串口和 WAVE ROVER 上车证据。
- Autonomy：本轮不涉及 route replay 或 Nav2 实跑。
- Full-Stack：本轮不涉及手机/Web 触点。
