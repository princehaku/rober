# Sprint 2026.05.12_00-01 O1 Docker Humble Base Image Fallback - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 00:01 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 工程主责：`robot-software-engineer`

## 用户价值和产品北极星

普通用户最终需要的是一台可验证可靠的 ROS2 垃圾投递机器人；工程团队当前需要的是在无真实硬件的 Docker-only 主机上持续推进 ROS2 Humble 构建验证，而不是被 base image 拉取链路卡住。北极星不变：真实底盘可信和 HIL evidence 才能证明 O1 闭环；本轮只是修复通往该闭环的 Docker/Humble 开发基础设施。

## 问题陈述

近期 O1 证据显示，Docker daemon、context、builder 都可用，但 `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 在拉取 `osrf/ros:humble-desktop` metadata/layer 时被 registry mirror/proxy 返回 HTML 阻断。现有脚本已经能分类问题，但还不能给工程团队一个可复用的 fallback 路径：换 base image、复用本地已有镜像、或跳过 docker build 直接跑 colcon。

## OKR 映射

- Objective：O1 硬件协议可信底盘，当前约 75%，是最低完成度目标。
- KR 影响：
  - 支撑 KR4/KR5 的 ROS2 Humble 构建验证和硬件桥软件验证环境。
  - 间接支撑后续真实 HIL packet gate，但本轮不产生真实 `hil_pass`。
- 不提升完成度的边界：本轮没有 WAVE ROVER、没有 `/dev/ttyUSB0`、没有真实 `T=1001`、`/odom`、`/imu/data`、`/battery` 实机样本。

## KR 拆解或更新

- KR-A：Dockerfile base image 可被 `ROS_HUMBLE_BASE_IMAGE` 或等价 build arg 覆盖，默认仍保持当前 Humble base。
- KR-B：build 脚本 preflight 输出实际 base image、override 状态、目标镜像、本地镜像复用状态和 skip docker build 状态。
- KR-C：当本地已有目标镜像时，可用显式 env 跳过 `docker build`，直接运行容器内 `colcon build --symlink-install`。
- KR-D：当跳过 docker build 但目标镜像不存在时，脚本必须快速失败并给出可操作原因，不静默回退。
- KR-E：文档和输出必须保留 `software_proof` 边界，不暗示真实 HIL 或实机通过。

## 本轮核心抓手

把 Docker registry mirror/proxy 阻断后的下一步从“人工改 Docker Desktop 或换网络再试”扩展成“可配置、可复用、可验证”的工程路径。这样即使上游 mirror 短期不可用，只要本机或团队已有可用 Humble 镜像，仍可执行 Docker-only `colcon build` 围栏。

## 做什么

- 支持 `ROS_HUMBLE_BASE_IMAGE` 覆盖 Dockerfile `FROM`。
- 支持显式 env 跳过 docker build 并复用现有 `ROS_HUMBLE_IMAGE`。
- 扩展 preflight 输出，清楚标记 Docker-only 路径和软件证据边界。
- 运行围栏验收命令，不新增大范围测试。

## 不做什么

- 不跑真实 HIL，不要求 `/dev/ttyUSB0`。
- 不新增或重构硬件协议代码。
- 不修改 `OKR.md` 进度。
- 不新增测试文件，不扩大到 O2/O3 行为或导航实现。
- 不把 synthetic fixture、Docker build、colcon 成功写成 `hil_pass`。

## 优先级和验收口径

P0：
- `ROS_HUMBLE_BASE_IMAGE=<image> SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 能把 override 传入 Docker build，并在 preflight 中显示实际 base image。
- 本地已有 `ros-rbs-humble:dev` 时，显式 skip-build env 能绕过 docker build 并直接进入 colcon 验证路径。

P1：
- skip-build 目标镜像不存在时快速失败并说明需先 build/pull/load 目标镜像。
- preflight 输出包含 `software_proof` 或等价边界提示。

P2：
- 保持原 `SKIP_COLCON=1` 只构建镜像不跑 colcon 的语义，不破坏现有脚本使用方式。

## 对应责任 Engineer

- `robot-software-engineer`：实现 Docker/Humble build path、运行围栏验证、更新 `tech-done.md`。
- `hardware-engineer`：只读咨询 HIL 边界，确认本轮不需要读取 vendor 细节或修改硬件参数。

## 风险、阻塞和证据链

- 风险：如果本机既不能访问 registry，又没有本地 `ros-rbs-humble:dev`，skip-build colcon 路径仍无法执行。
- 风险：Dockerfile 使用 build arg for `FROM` 时需保证默认值稳定，避免破坏已有 Docker build。
- 风险：过度包装 Docker-only 通过会误导 O1 完成度；所有输出和 sprint 收口必须写清 `software_proof`。
- 阻塞：本机无真实硬件，因此 HIL evidence packet 仍 pending。
- 证据链：后续工程验收必须附 `bash -n`、`SKIP_COLCON=1` 或 skip-build colcon 结果、`git diff --check`，并在 `tech-done.md` 标注 Docker-only。

## 需要创建或更新的 sprint 文档

- 已完成：`pre_start.md`
- 已完成：`prd.md`
- 待完成：`tech-plan.md`
- 工程完成后：`tech-done.md`
- 收口后：`side2side_check.md`、`final.md`
