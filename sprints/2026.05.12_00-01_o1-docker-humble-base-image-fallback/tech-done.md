# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-11 23:15 Asia/Shanghai
- Owner：`robot-software-engineer`
- 证据边界：`software_proof_docker_only`
- HIL 口径：本轮未接入 WAVE ROVER、串口或真实底盘反馈，不声明 `hil_pass`

## 实际改动

- `docker/humble/Dockerfile`
  - 新增 `ARG ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop`。
  - `FROM` 改为 `FROM ${ROS_HUMBLE_BASE_IMAGE}`，默认 base image 不变。
- `scripts/docker_humble_build.sh`
  - 新增 `ROS_HUMBLE_BASE_IMAGE` 环境变量支持，并在 `docker build` 时传入 `--build-arg ROS_HUMBLE_BASE_IMAGE=...`。
  - 保持 `ROS_HUMBLE_IMAGE` 目标镜像名，默认仍为 `ros-rbs-humble:dev`。
  - 新增 `SKIP_DOCKER_BUILD=1`：先检查目标镜像是否本地存在，再用最小容器探针确认它能作为 ROS Humble build image 启动；通过后复用本地镜像继续执行后续 `SKIP_COLCON` 或 `colcon build` 逻辑；不存在或不可运行时快速失败并输出 `docker pull`、`docker load` 或正常 build 的操作提示。
  - preflight 新增 `evidence_scope=software_proof_docker_only`、`target_image`、`base_image`、`base_image_override`、`skip_docker_build`、`skip_colcon`、`local_target_image_present`、`local_image_reuse`。

## 测试同学复核诊断

### `docker version`

- 结果：通过，Docker daemon 不是完全不可用。
- 关键输出：
  - Client `28.3.3`，Context `desktop-linux`
  - Server `Docker Desktop 4.45.0 (203075)`，Engine `28.3.3`
  - Server `OS/Arch=linux/arm64`

### `docker info` / builder 状态

- 结果：daemon/storage 可查询；registry mirrors 已配置；一个旧 `default` builder endpoint 异常，但当前 `desktop-linux` builder running。
- 关键输出：
  - `Driver=overlayfs`
  - `DockerRootDir=/var/lib/docker`
  - `RegistryMirrors=["https://ef4zg2yg.mirror.aliyuncs.com/","https://registry.dockermirror.com/","https://dockerpull.cn/","https://docker.m.daocloud.io/"]`
  - `desktop-linux` builder `running`，BuildKit `v0.23.2`
  - `default` builder 报 `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`

### `docker image inspect ros-rbs-humble:dev`

- 结果：tag 存在，但 manifest/metadata 明显异常，不等于可运行镜像。
- 关键输出：
  - `RepoTags=["ros-rbs-humble:dev","osrf/ros:humble-desktop"]`
  - `RepoDigests=["ros-rbs-humble@sha256:e0085ae8...","osrf/ros@sha256:e0085ae8..."]`
  - `Architecture=`、`Os=` 为空
  - `Size=20381`

### `docker run --rm ros-rbs-humble:dev true`

- 结果：失败，确认本地 tag 不可运行。
- 关键输出：
  - `error walking manifest for docker.io/library/ros-rbs-humble:dev: descriptor is neither a manifest or index`

### `docker pull osrf/ros:humble-desktop`

- 结果：失败，确认 registry/mirror 拉取链路返回了 Docker 不能 unpack 的 HTML media type。
- 关键输出：
  - `e0085ae8abbb: Already exists`
  - `failed to unpack image on snapshotter overlayfs: unexpected media type text/html for sha256:e0085ae8...: not found`

## 验证结果

### `bash -n scripts/docker_humble_build.sh`

- 结果：通过，shell 语法检查无输出。

### `SKIP_COLCON=1 ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop bash scripts/docker_humble_build.sh`

- 结果：失败，已定位为 registry mirror/proxy 阻断。
- 关键输出：
  - `evidence_scope=software_proof_docker_only`
  - `target_image=ros-rbs-humble:dev`
  - `base_image=osrf/ros:humble-desktop`
  - `base_image_override=env`
  - `skip_docker_build=0`
  - `skip_colcon=1`
  - `local_target_image_present=yes`
  - `local_image_reuse=available_for_explicit_skip_validation_pending`
  - `ERROR: failed to solve: osrf/ros:humble-desktop: failed to resolve source metadata for docker.io/osrf/ros:humble-desktop: encountered unknown type text/html`
  - `category=registry mirror/proxy`

### `SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`

- 结果：失败，已定位为本地目标镜像不可运行。
- 触发原因：本机 `ros-rbs-humble:dev` tag 存在，但镜像元数据异常，`docker run` 返回 `descriptor is neither a manifest or index`。
- 关键输出：
  - `skip_docker_build=1`
  - `local_target_image_present=yes`
  - `local_image_reuse=inspect_present_validation_pending`
  - `ERROR: SKIP_DOCKER_BUILD=1 found target image 'ros-rbs-humble:dev', but it is not runnable as a ROS Humble build image.`
  - operator 提示：`docker pull ros-rbs-humble:dev`、`docker load -i /path/to/ros-rbs-humble-dev.tar`，或取消 `SKIP_DOCKER_BUILD` 后从 base image 重建。

### `SKIP_DOCKER_BUILD=1 SKIP_COLCON=1 ROS_HUMBLE_IMAGE=ros-rbs-humble:missing-skip-build-check bash scripts/docker_humble_build.sh`

- 结果：按预期快速失败。
- 关键输出：
  - `target_image=ros-rbs-humble:missing-skip-build-check`
  - `local_target_image_present=no`
  - `local_image_reuse=missing`
  - `ERROR: SKIP_DOCKER_BUILD=1 was requested, but target image 'ros-rbs-humble:missing-skip-build-check' is not present locally.`

### `git diff --check -- ...`

- 结果：通过，无 whitespace error。

## 偏差与阻塞

- 本轮工程实现完成，但本机验证仍 blocked。
- 默认 build 被 Docker registry mirror/proxy 阻断：`docker.io/osrf/ros:humble-desktop` metadata 返回 `text/html`。
- 本地 skip-build 路径未能跑到 colcon：`ros-rbs-humble:dev` tag 虽存在，但镜像显示 `Architecture=`、`Os=`、`SIZE=0B`，`docker run` 返回 manifest descriptor 异常，属于不可复用本地镜像。

## 剩余风险

- 本轮只证明 Docker-only build path 和本地镜像复用入口可用，不证明真实 WAVE ROVER 串口、底盘运动、`T=1001` 反馈、`/imu/data`、`/battery` 或 `/odom`。
- 当前 operator 必须先获得一个可运行的目标镜像，才能用 `SKIP_DOCKER_BUILD=1` 继续 colcon：修复/更换 Docker registry mirror 后正常 build，或从可信机器 `docker save` 后在本机 `docker load`。
- 未更新 `OKR.md` 完成度。
