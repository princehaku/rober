# Sprint 2026.05.12_01-02 Mac Docker Humble Env - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 01:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 触发：用户指出当前已经在 Mac 上，没有 WSL；Docker Compose 报错路径仍含 `/run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/Ubuntu-24.04/...`
- 证据边界：环境口径修正与 Docker/Humble 软件围栏；不声明 HIL

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车能以低成本、可验证、可复盘的方式完成固定路线送达。当前阻塞不在用户流程本身，而在 O1 真实上车前的 Docker/Humble 本地验证入口仍残留 WSL 口径，导致 Mac 本机环境不能稳定承接后续硬件验证。

本轮用户价值是把开发与验证入口切回 Mac-first：本机 Docker Desktop/Engine 应该直接挂载当前仓库到 Linux 容器 `/ws`，不再出现 WSL `Ubuntu-24.04` bind mount 路径。这样后续 `robot-software-engineer` 才能继续修 Docker Compose、脚本和 README，而产品侧不把环境问题误记为硬件或 ROS2 问题。

## 上轮未完成项和阻塞

- O1 仍缺真实 WAVE ROVER HIL evidence packet，不得用 Docker 环境进展替代。
- 上一轮 Docker/Humble 证据主要是 `software_proof_docker_only`，本轮继续保持该边界。
- 本轮新增阻塞信号：Mac 本机运行 Docker Compose 时出现 WSL bind mount 路径，说明文档或流程残留 Windows/WSL 假设。

## 本轮核心抓手

把本地环境记忆和 sprint 验收口径改成 Mac-first Docker/Humble：

- `AGENTS.md` 的“本地环境记忆”删除 Windows/WSL 主机假设。
- 新 sprint 留档写清 Mac Docker Desktop/Engine 是当前默认入口。
- 工程实现由 `robot-software-engineer` 在独立文件范围处理 Docker Compose、脚本和 README。

## 做什么 / 不做什么

做：

- 创建本 sprint 文档链路中的产品计划、验收和收口文件。
- 更新 `AGENTS.md` 本地环境记忆为 Mac-first。
- 明确本轮只处理本地 Docker/Humble 环境口径，不改 OKR 完成度。

不做：

- 不改 `docker-compose.humble.yml`、`scripts/*`、`README.md`，这些由并行 `robot-software-engineer` 负责。
- 不改 ROS2 产品代码、测试代码、硬件配置或 vendor 文件。
- 不运行或声称真实串口、WAVE ROVER、Orange Pi、`T=1001`、HIL evidence packet。

## 风险和证据链

- 如果工程侧只修脚本但文档仍写 WSL，后续 agent 会继续按错误环境排查。
- 如果 Docker Compose 仍输出 WSL bind mount 路径，本轮产品验收不能关闭。
- 本轮不产生 `hil_pass`；真实 O1 仍需要串口设备、底盘反馈和归档 evidence packet。

## 需要创建或更新的文档

- `AGENTS.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/pre_start.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/prd.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/tech-plan.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/side2side_check.md`
- `sprints/2026.05.12_01-02_mac-docker-humble-env/final.md`
