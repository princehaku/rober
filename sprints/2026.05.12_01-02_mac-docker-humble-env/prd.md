# Sprint 2026.05.12_01-02 Mac Docker Humble Env - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 01:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 证据边界：Mac 本地 Docker/Humble 环境口径修正；不声明 HIL

## 用户价值和产品北极星

普通用户价值最终依赖机器人能稳定上车验证和交付垃圾；开发侧价值是让 Mac 本机能稳定进入 ROS2 Humble 容器验证，不再把 WSL 路径残留当作 Docker、ROS2 或硬件本身的问题。

本轮不是新增机器人能力，而是清理环境入口：所有本地验证默认面向 macOS + Docker Desktop/Engine，仓库挂载到容器 `/ws`。这支撑 O1 后续从 Docker/Humble 软件围栏回到真实 HIL。

## OKR 映射

- Objective 1：支撑可信底盘控制层的本地 Humble 验证入口，保持约 75%，不更新完成度。
- Objective 2：不更新。任务闭环仍等待真实或可复账运行证据。
- Objective 3：不更新。固定路线 replay 仍等待同一 `evidence_ref` 的真实上车证据。
- Objective 4/5/6：不更新。本轮不涉及视觉、手机体验或 4G 云中转交付。

## KR 拆解或更新

本轮不修改 `OKR.md` KR 文本，不更新完成度。

Sprint 内验收 KR：

- KR-A：`AGENTS.md` 本地环境记忆不再把当前主机描述为 Windows/WSL `Ubuntu-24.04`。
- KR-B：本轮 sprint 文档明确 Mac-first Docker Desktop/Engine 是默认验证入口。
- KR-C：产品验收口径明确 WSL bind mount 路径是环境口径漂移，不能算作 HIL、ROS2 构建成功或硬件失败。
- KR-D：工程实现责任清楚归属 `robot-software-engineer`，Product 不改 Compose、脚本、README。

## 本轮核心抓手

将“我们现在在 Mac 上，没有 WSL”固化为项目工作记忆和本轮验收标准，避免后续 agent 继续沿用旧 WSL 口径。

## 范围

做：

- 更新 `AGENTS.md` 本地环境记忆。
- 创建 `pre_start.md`、`prd.md`、`tech-plan.md`、`side2side_check.md`、`final.md`。
- 保持 `software_proof_docker_only` 口径。

不做：

- 不改 Docker Compose、脚本、README。
- 不改 `OKR.md`。
- 不改硬件/vendor/ROS2 产品代码。
- 不声称真实 HIL、串口接入、底盘运动、`T=1001` 反馈或同一 `evidence_ref` replay。

## 优先级和验收口径

P0：

- 本地环境记忆必须改成 Mac-first。
- sprint 文档必须写清 Docker Compose WSL 路径残留的验收失败条件。
- scoped `git diff --check` 必须通过。

P1：

- 与并行工程 worker 的 Compose/脚本/README 改动在口径上保持一致，但 Product 不直接改其文件。

## 对应责任 Engineer

- Product Manager / OKR Owner：`AGENTS.md` 本地环境记忆、产品目标、验收口径、sprint 收口。
- `robot-software-engineer`：Docker Compose、脚本、README 的 Mac-first 工程实现和运行验证。

## 风险、阻塞和证据链

- 仍需工程 worker 提供实际 Docker Compose 或脚本运行证据，证明不再生成 WSL bind mount 路径。
- 本轮产品文档通过只能证明口径修正，不证明 Docker/Humble colcon 全量可用。
- 没有真实硬件和串口 evidence packet，O1 不能升级为 `hil_pass`。
