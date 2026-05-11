# Sprint 2026.05.12_01-02 Mac Docker Humble Env - Final

## 状态

- 阶段：final
- 时间：2026-05-12 01:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- Engineering Owner：`robot-software-engineer`
- 证据范围：`software_proof_docker_only`
- 收口结论：Product 侧 Mac-first 环境口径完成；Mac-first Compose/X11 配置修正可收口；Docker/Humble build、`colcon build` 和 `ros2 pkg prefix ros2_trashbot_bringup` 已由 Robot 证据恢复通过；不更新 `OKR.md` 完成度；不声明 HIL

## 用户价值和产品北极星

北极星仍是低成本、可验证、可复盘的 ROS2 自主垃圾投递机器人。当前 Product 交付的价值是把本地验证入口从错误的 WSL 记忆切回 Mac-first，并把 Docker/Humble build 已恢复通过的真实状态写清楚，避免后续工程排查继续被 `/run/desktop/mnt/host/wsl/docker-desktop-bind-mounts/Ubuntu-24.04/...` 或过期 blocked 口径误导。

## OKR 映射

- O1：环境入口口径修正，支撑后续 Docker/Humble 和 HIL 准备；Docker/Humble build 只作为 `software_proof_docker_only`，完成度不变。
- O2：不更新。
- O3：不更新。
- O4/O5/O6：不更新。

## KR 拆解结果

完成：

- `AGENTS.md` 本地环境记忆已改为 macOS + Docker Desktop/Engine 优先。
- `AGENTS.md` 已删除过期 blocked 结论，改为当前真实状态：Mac-first Compose/X11 口径已修正，Docker/Humble build、`colcon build` 和 package prefix 验证已恢复通过。
- 新 sprint `sprints/2026.05.12_01-02_mac-docker-humble-env/` 已创建产品侧留档。
- 验收口径已明确：Mac 上不应出现 WSL bind mount 路径；出现则视为环境口径漂移。
- Robot 最新证据已记录：`docker pull osrf/ros:humble-desktop` 通过，digest `sha256:49e87123022a2622a8a098eb3d71d6df8265469ad4d46c6dbde0326f8aa97bb3`；`docker compose -f docker-compose.humble.yml build --pull --no-cache humble` 通过并输出 `ros-rbs-humble:dev Built`。
- Robot 已定位第一次 `colcon build` 失败为 `ros2_trashbot_bringup` packaging 安装不存在的 `config` 目录，并修复 `src/ros2_trashbot_bringup/CMakeLists.txt` 只安装实际存在的 `launch` 目录。
- 复验已记录：`colcon build --symlink-install` 通过，输出 `Summary: 6 packages finished [32.4s]`；`ros2 pkg prefix ros2_trashbot_bringup` 输出 `/ws/install/ros2_trashbot_bringup`；diff check 通过。
- 文档明确 Product 不负责改 Docker Compose、脚本、README 或工程文件；Robot 的工程修复保持原样。

未完成且留给工程侧：

- 真实串口、WAVE ROVER、`T=1001` 反馈和 HIL evidence packet。
- 同一 `evidence_ref` 下的 O2/O3 实机任务复盘和 route replay。

## 本轮核心抓手

将“当前主机是 Mac，没有 WSL”以及“Docker/Humble build、colcon、bringup package prefix 已恢复通过，但证据边界仅为 `software_proof_docker_only`”固化到 `AGENTS.md` 和 sprint 验收文档，作为后续所有 agent 处理 Docker/Humble 环境问题的默认事实。

## 做什么 / 不做什么

做了：

- 更新 `AGENTS.md` 的“本地环境记忆”。
- 补正 `side2side_check.md` / `final.md` 的 Product 收口，承认工程侧 Mac-first Compose/X11 配置修正已完成，同时明确 Docker/Humble build、`colcon build` 和 package prefix 已恢复通过。
- 创建 `pre_start.md`、`prd.md`、`tech-plan.md`、`side2side_check.md`、`final.md`。
- 运行 Product scoped `git diff --check`。

没有做：

- 未改 `docker-compose.humble.yml`、`scripts/*`、`README.md`。
- 未改 `OKR.md`。
- 未改 ROS2 产品代码、测试代码、硬件配置或 vendor 文件；Robot 已完成的 `src/ros2_trashbot_bringup/CMakeLists.txt` 修复保持原样。
- 未声称 HIL、真实底盘运动、真实反馈、route replay 或 `evidence_ref` 复账已通过。
- 未更新 `OKR.md` 完成度。

## 验收结果

Product scoped validation：

```bash
git diff --check -- AGENTS.md sprints/2026.05.12_01-02_mac-docker-humble-env/side2side_check.md sprints/2026.05.12_01-02_mac-docker-humble-env/final.md
```

结果：exit 0，无输出。

## 失败定位

本轮 Product 文档侧未发现 diff check 失败。原始环境口径失败信号是 Docker Compose 输出 WSL bind mount 路径，定位为本地环境口径与工程入口残留 WSL 假设；该 Mac-first Compose/X11 配置修正可收口。

已解除的工程阻塞包括：`docker pull osrf/ros:humble-desktop`、Docker Compose image build、`colcon build --symlink-install` 和 `ros2 pkg prefix ros2_trashbot_bringup`。第一次 `colcon build` 失败定位为 bringup packaging 安装不存在的 `config` 目录，Robot 已修复为只安装实际存在的 `launch` 目录并复验通过。

## 剩余风险

- 本 Product 文档只记录收口口径，不替代 Robot 的 `tech-done.md` 工程证据。
- 当前证据只证明 Docker 容器软件构建与 ROS2 package prefix 可用，不证明真实串口、WAVE ROVER 底盘运动、`T=1001` 反馈、IMU、电池或 HIL 已通过。
- `src/ros2_trashbot_bringup/CMakeLists.txt` 修复解决 packaging 缺目录问题，不证明 launch 行为或完整上车 bringup 已完成。
- O1 仍缺 HIL evidence packet，O2/O3 仍缺同一 `evidence_ref` 实机复账；本轮不更新 `OKR.md` 完成度。
