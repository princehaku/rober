# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 00:01 Asia/Shanghai
- Sprint 目录：`sprints/2026.05.12_00-01_o1-docker-humble-base-image-fallback/`
- Product Owner：`product-okr-owner`
- 工程主责：`robot-software-engineer`
- 只读咨询：`hardware-engineer`，仅用于确认本轮不升级为真实 HIL 验收

## 用户价值和产品北极星

北极星仍是让普通手机用户面对一台可验证可靠的低成本 ROS2 垃圾投递机器人，而不是只能在开发机上解释失败原因的 demo。本轮不解决真实 WAVE ROVER 上车问题；本轮先把 Docker/Humble 基础构建链路从“registry mirror/proxy 阻断后只能分类”推进为“可配置 base image、可复用本地镜像、可跳过重建直接跑 colcon”的 Docker-only build path。

用户价值是让无硬件的开发机也能继续验证 ROS2 Humble 工作区构建，减少 O1 硬件协议主链路在 base image 拉取问题上的等待时间。这个结果只算 `software_proof`，不能写成真实 `hil_pass`。

## OKR 映射

- 主目标：Objective 1，打通官方硬件协议，建立可信底盘控制层。
- 当前进度证据：`OKR.md` 4.1 记录 O1 约 75%，低于 O2/O3 约 77%、O4 约 76%、O5 约 80%，最低完成度仍是 O1。
- 近期证据：
  - `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/final.md`：Docker daemon 和 builder 可用，但 `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 被 Docker registry mirror/proxy 返回 HTML 阻断。
  - `sprints/2026.05.11_22-23_hil-evidence-packet-gate/final.md`：HIL packet gate ready，但真实 `hil_pass` pending。
  - `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/final.md`：HIL gate output 已接入 run-level evidence crosscheck，但仍不是实车 HIL pass。

## 上轮未完成项和阻塞

- Docker/Humble base image 仍受 registry mirror/proxy 返回 HTML 影响，直接重建 `osrf/ros:humble-desktop` 路径不稳定。
- 本机没有真实 WAVE ROVER、没有真实串口设备，不能规划 `/dev/ttyUSB0` HIL 为本轮验收。
- HIL gate 和 crosscheck 已具备软件证据链，但没有真实 packet，因此 O1 不能提完成度。

## 本轮核心抓手

把 `scripts/docker_humble_build.sh` 与 `docker/humble/Dockerfile` 的 Docker-only 构建路径补成三条可执行分支：

1. base image 可通过 `ROS_HUMBLE_BASE_IMAGE` 覆盖，避免硬编码卡死在单一上游镜像路径。
2. 当本地已有 `ros-rbs-humble:dev` 时，可通过显式 env 跳过 docker build，直接运行容器内 `colcon build --symlink-install`。
3. preflight 输出明确标记 base image override、reused local image、skip docker build、Docker-only/software proof，防止被误写成 `hil_pass`。

## 做什么

- 只推进 Docker/Humble 构建履约路径，不碰真实硬件 smoke。
- 明确 Engineer owner、文件范围、接口影响、风险边界和围栏验收命令。
- 让后续工程子 agent 可直接按 `tech-plan.md` 实现、验证并更新 `tech-done.md`。

## 不做什么

- 不新增大测试矩阵，不做泛化 CI 改造。
- 不修改 OKR 完成度。
- 不把 Docker-only build success、`py_compile`、help/status 输出写成真实 `hil_pass`。
- 不规划真实 `/dev/ttyUSB0`、WAVE ROVER move-test 或实机 packet 作为本轮验收。

## 责任 Engineer

- 主责：`robot-software-engineer`
- 允许改动：`scripts/docker_humble_build.sh`、`docker/humble/Dockerfile`、本 sprint 后续留档。
- 咨询：`hardware-engineer` 只读确认 evidence 边界，不改硬件配置或 vendor 文档。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 下一步创建：`prd.md`
- 下一步创建：`tech-plan.md`
- 工程完成后必须补：`tech-done.md`
- 验收或风险状态变化后必须补：`side2side_check.md`、`final.md`

## 完成前反思

- 本轮 sprint 新目录已独立创建，没有复用旧 sprint。
- 本轮范围围绕最低完成度 O1，没有漂移到 O2/O3/O4/O5。
- 本轮没有真实硬件，因此所有验收口径必须停留在 Docker-only `software_proof`。
