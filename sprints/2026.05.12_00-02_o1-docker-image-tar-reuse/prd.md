# Sprint 2026.05.12_00-02 O1 Docker Image Tar Reuse - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 00:02 Asia/Shanghai
- 产品 Owner：Product Manager / OKR Owner
- 执行 Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`

## 背景

当前 O1 仍是最低完成度与最高优先级方向。上一轮已经把 Docker/Humble build 的失败从“Docker 不可用”收敛为更具体的环境问题：daemon 和 builder 可用，但 registry mirror/proxy 对 `osrf/ros:humble-desktop` 返回 HTML；同时本地 `ros-rbs-humble:dev` tag 存在但不可运行。

产品上不能继续只把下一步写成“人工 docker load”。这会让下一位执行同学仍然停在口头操作，无法形成可重复的 Docker-only 软件证据。本轮要把可信镜像 tar 转移路径做成脚本级入口，并继续保持 HIL 证据边界。

## 用户价值和产品北极星

北极星：低成本 ROS2 自主垃圾投递机器人最终要能稳定从“用户交付垃圾”走到“固定路线送达”。O1 的可信底盘控制层是这条链路的地基。

本轮用户价值：在没有真实硬件、且 registry mirror/proxy broken 的 Docker-only 主机上，工程师仍然有可执行的复用路径来恢复 ROS Humble build 容器能力，减少环境阻断时间，为后续真实 HIL packet 和同一 `evidence_ref` 复账做准备。

## OKR 映射

- 直接映射 O1：补齐 Docker/Humble 环境 readiness 的可复用路径，支撑后续硬件桥上车验证。
- 间接支撑 O2：后续任务恢复和 task record crosscheck 需要可运行 ROS2 workspace 验证环境。
- 间接支撑 O3：后续 fixed-route replay 和 same-`evidence_ref` 对账需要可运行容器。
- 不映射 O4/O5 的本轮交付；视觉、手机和用户触点不进入本 sprint。

## KR 拆解 / 更新

本轮不更新 `OKR.md` 数字，只定义 sprint 内 KR：

1. 脚本入口：支持 `ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh`，脚本先导入 tar，再走本地目标镜像复用校验。
2. 快速失败：`ROS_HUMBLE_IMAGE_TAR=` 或不存在路径必须非 0 退出，错误信息说明 tar 路径为空或文件不存在。
3. 复用校验：`SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh` 仍校验本地目标镜像是否可运行，不因 tag 存在就通过。
4. 证据边界：所有相关输出和 sprint 留档都保持 `software_proof_docker_only`；不写成 `hil_pass`、不暗示真实底盘运动。

## 本轮核心抓手

把上一轮 final 中的 operator 下一步动作产品化为脚本能力：

```bash
ROS_HUMBLE_IMAGE_TAR=/path/to/ros-rbs-humble-dev.tar SKIP_DOCKER_BUILD=1 bash scripts/docker_humble_build.sh
```

等价方案也可接受，但必须满足：

- 明确输入是可信机器导出的可运行目标镜像 tar。
- 在本机先 `docker load`，再复用 `ROS_HUMBLE_IMAGE` 指向的目标镜像。
- 复用前必须 `docker run` 探针验证 `/opt/ros/humble/setup.bash` 存在。
- 失败提示告诉 operator 修 tar、换镜像、修 Docker daemon 或取消 skip build。

## 做什么

- 修改 `scripts/docker_humble_build.sh`，增加可选 `ROS_HUMBLE_IMAGE_TAR` 路径。
- 保持默认 build 行为不变：未设置 tar 且未 skip build 时仍走 Docker build。
- 保持 `SKIP_DOCKER_BUILD=1` 的严格本地镜像可运行校验。
- 后续实现完成后更新本 sprint 的 `tech-done.md`；验收和复盘阶段再更新 `side2side_check.md`、`final.md`。

## 不做什么

- 不修改 ROS2 package 代码、测试代码、硬件配置、launch 参数、vendor 文件或 `OKR.md`。
- 不要求真实 WAVE ROVER move-test，不设计串口 smoke，不生成 HIL packet。
- 不把 Docker tar load 成功当成 `hil_pass` 或 fixed-route 实跑证据。
- 不做广泛测试；只做脚本语法、错误路径、复用路径和 scoped diff check。

## 优先级

- P0：脚本入口可用，错误路径清晰，复用校验严格。
- P1：preflight 输出包含 tar 路径是否启用和证据边界，便于 operator 复盘。
- P2：执行留档完整，但不预生成后续阶段文档。

## 验收口径

产品验收不是“镜像真的能跑完整 colcon”，因为本机可能没有可信 tar。产品验收是后续 Engineer 能证明：

- 空 tar 路径和缺失 tar 路径被快速拦截。
- 未设置 tar 时，`SKIP_DOCKER_BUILD=1` 仍沿用上一轮的本地目标镜像可运行校验。
- 如提供可信 tar，脚本会先导入再校验目标镜像；如果目标镜像仍不可运行，不能通过。
- 输出和文档清楚标注 `software_proof_docker_only`，不冒充硬件通过。

## 对应责任 Engineer

- `robot-software-engineer`：实现脚本入口、运行围栏验证、更新 `tech-done.md`。
- Product Manager / OKR Owner：验收是否保持 O1/O2/O3 证据边界、是否按 sprint 链路收口。

## 风险、阻塞和需要补齐的证据链

- 仍缺真实硬件：没有 WAVE ROVER、Orange Pi、真实串口和 archived packet。
- 仍缺同一 `evidence_ref` run：O2/O3 不得因本轮 Docker 入口通过而升级。
- 可信 tar 来源风险：必须由 operator 从可信机器导出；脚本只负责导入和校验，不负责证明来源可信。
- Docker daemon 风险：daemon 或 builder 若不可用，仍会阻断；这属于环境修复，不是本轮脚本逻辑失败。

## 需要创建或更新的 sprint 文档

Planning 阶段已创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现阶段由 `robot-software-engineer` 在实际改动后创建或更新：

- `tech-done.md`

验收和收口阶段再创建或更新：

- `side2side_check.md`
- `final.md`
