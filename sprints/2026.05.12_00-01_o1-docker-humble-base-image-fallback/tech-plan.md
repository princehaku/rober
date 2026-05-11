# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 00:01 Asia/Shanghai
- 主责 owner：`robot-software-engineer`
- 咨询 owner：`hardware-engineer` 只读咨询 HIL 边界
- 计划状态：ready for engineering subagent execution

## 用户价值和产品北极星

本轮服务于 O1 的可信底盘主线，但不直接做实车 HIL。产品价值是让工程团队在 Docker-only 主机上继续构建和验证 ROS2 Humble 工作区，即使 Docker registry mirror/proxy 阻断默认 base image 拉取，也能通过可配置 base image 或复用本地镜像继续推进。北极星仍要求真实 WAVE ROVER evidence packet 才能写 `hil_pass`。

## OKR 映射

- O1 当前约 75%，低于 O2/O3 约 77%、O4 约 76%、O5 约 80%，是当前最低完成度目标。
- 本轮推进 O1 的 Docker/Humble build readiness，不提升 HIL 完成度。
- 本轮验收结果只能作为 `software_proof`，不能作为真实底盘运动、`T=1001` 反馈或同一 `evidence_ref` route replay 的证据。

## 本轮核心抓手

在现有 `scripts/docker_humble_build.sh` 和 `docker/humble/Dockerfile` 上补 fallback：

1. `ROS_HUMBLE_BASE_IMAGE` 覆盖 Dockerfile base image。
2. 显式 env 复用已存在 `ros-rbs-humble:dev` 或 `ROS_HUMBLE_IMAGE`，跳过 `docker build` 后直接跑 colcon。
3. preflight 清楚输出 base image override、skip build、local image reuse、Docker-only/software proof 边界。

## 文件范围

`robot-software-engineer` 允许修改：

- `scripts/docker_humble_build.sh`
- `docker/humble/Dockerfile`
- `sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/tech-done.md`
- `sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/side2side_check.md`
- `sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md`

`hardware-engineer` 只读咨询允许读取：

- `sprints/2026.05.11_22-23_hil-evidence-packet-gate/final.md`
- `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/final.md`
- `docs/acceptance/hil_runbook.md`
- `docs/acceptance/wave_rover_hil_evidence.md`

禁止修改：

- `OKR.md`
- 产品代码、测试代码、硬件配置、launch 参数
- 其他 sprint 目录
- vendor 文件

## 设计要求

### Dockerfile

- 将默认 base image 从硬编码 `FROM osrf/ros:humble-desktop` 调整为可通过 build arg 覆盖的形式。
- 默认值必须仍是 `osrf/ros:humble-desktop`，保持现有行为。
- build arg 名称优先使用 `ROS_HUMBLE_BASE_IMAGE`，与用户和 sprint 口径一致。

### Build script

- 保持 `ROS_HUMBLE_IMAGE` 作为目标镜像名，默认 `ros-rbs-humble:dev`。
- 新增 `ROS_HUMBLE_BASE_IMAGE` 读取，默认从 Dockerfile 默认值或 `osrf/ros:humble-desktop` 得出；实际 docker build 必须传入 `--build-arg ROS_HUMBLE_BASE_IMAGE=...`。
- 新增显式 skip docker build env，例如 `SKIP_DOCKER_BUILD=1`。命名可由工程 owner 微调，但必须在 `tech-done.md` 写清。
- 当 `SKIP_DOCKER_BUILD=1`：
  - 先检查目标镜像是否存在，例如 `docker image inspect "$image"`。
  - 存在时跳过 `docker build`，直接进入后续逻辑。
  - 不存在时快速失败，并输出需要先 `docker pull`、`docker load` 或正常 build 的提示。
- 保持 `SKIP_COLCON=1` 语义：镜像 ready 后退出，不跑 colcon。
- 默认路径仍执行 docker build 后再跑 colcon，不改变现有用户习惯。

### Preflight 输出

必须清楚输出：

- `target_image`
- `base_image`
- `base_image_override` 或等价字段
- `skip_docker_build`
- `skip_colcon`
- `local_image_reuse` 或等价字段
- Docker-only/software proof 边界提示，例如 `evidence_scope=software_proof_docker_only`

输出不得使用会被误读为 `hil_pass` 的措辞。

## 接口影响

- Shell env 新增：`ROS_HUMBLE_BASE_IMAGE`。
- Shell env 新增或明确：`SKIP_DOCKER_BUILD`。
- 保持：`ROS_HUMBLE_IMAGE`、`SKIP_COLCON`、镜像名默认值、容器内 `colcon build --symlink-install`。
- 不影响 ROS2 topic/action/srv。
- 不影响 hardware smoke、HIL gate、evidence crosscheck 的 CLI 契约。

## 风险边界

- 本轮不解决 Docker Desktop registry mirror/proxy 配置本身，只提供绕行和复用路径。
- 本轮不保证没有本地镜像时可离线构建。
- 本轮不证明 WAVE ROVER 串口、速度映射、反馈协议或真实运动。
- 本轮验收最多证明 Docker-only Humble build path 可用，不能提升 `hil_pass` 状态。

## 围栏验收命令

工程子 agent 必须运行并报告以下命令。若某条因本机 Docker registry/proxy 或本地镜像缺失失败，必须定位原因并在 `tech-done.md` 写清影响，不能把失败直接口头交差。

```bash
bash -n scripts/docker_humble_build.sh
```

```bash
SKIP_COLCON=1 ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop bash scripts/docker_humble_build.sh
```

如果上一条仍因 registry mirror/proxy 返回 HTML blocked，但本地已有目标镜像，则必须运行：

```bash
SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

如果本地没有目标镜像，则必须运行并记录快速失败输出：

```bash
SKIP_DOCKER_BUILD=1 SKIP_COLCON=1 bash scripts/docker_humble_build.sh
```

最终必须运行：

```bash
git diff --check -- scripts/docker_humble_build.sh docker/humble/Dockerfile sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/tech-done.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/side2side_check.md sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/final.md
```

## 子 Agent 执行要求

`robot-software-engineer` 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果，日志片段即可。
3. 失败定位，如 Docker registry mirror/proxy、目标镜像不存在、Docker daemon/builder 问题。
4. 剩余风险，尤其是没有真实硬件时不能声明 `hil_pass`。

## 阶段收口要求

- 实现完成后更新 `tech-done.md`，写清实际改动、验证结果和偏差。
- 若 Docker-only colcon 通过，`side2side_check.md` 和 `final.md` 只能写 `software_proof_docker_only`。
- 若仍 blocked，`final.md` 必须写清 block 分类和下一步 operator 动作。
- 无论通过或 blocked，都不得修改 `OKR.md` 完成度，除非后续有真实 HIL evidence packet。
