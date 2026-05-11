# Sprint 2026.05.12_01-02 Mac Docker Humble Env - Side2Side Check

## 状态

- 阶段：side2side_check
- 时间：2026-05-12 01:02 Asia/Shanghai
- Product Owner：Product Manager / OKR Owner
- 对照对象：用户原始反馈和本轮允许文件范围

## 用户反馈对照

用户指出：

```text
我们现在在mac上 没有wsl了啊 全部改一下。。
```

对照结论：

- `AGENTS.md` 本地环境记忆已从 Windows/WSL `Ubuntu-24.04` 改为 macOS + Docker Desktop/Engine。
- sprint 文档已把 WSL bind mount 路径残留定义为环境口径漂移。
- Product 收口已补正：Mac-first Docker Compose/X11 口径已完成修正，且 Robot 最新证据显示 Docker/Humble build 与 package prefix 验证已恢复通过。
- Robot 证据链：`docker pull osrf/ros:humble-desktop` 通过，digest `sha256:49e87123022a2622a8a098eb3d71d6df8265469ad4d46c6dbde0326f8aa97bb3`；`docker compose -f docker-compose.humble.yml build --pull --no-cache humble` 通过并输出 `ros-rbs-humble:dev Built`；修复 `src/ros2_trashbot_bringup/CMakeLists.txt` 后，`colcon build --symlink-install` 通过，输出 `Summary: 6 packages finished [32.4s]`；`ros2 pkg prefix ros2_trashbot_bringup` 输出 `/ws/install/ros2_trashbot_bringup`。
- Product 未改 Docker Compose、脚本、README 或工程文件；Robot 对 `src/ros2_trashbot_bringup/CMakeLists.txt` 的修复保持原样。

## OKR 对照

- O1：Docker/Humble 本地验证入口恢复为可用软件证据，但只记为 `software_proof_docker_only`，不更新完成度。
- O2/O3：不借本轮环境文档升级任务闭环或 route replay。
- HIL：无真实串口、无 WAVE ROVER feedback、无 evidence packet；不声明 `hil_pass`，不把 Docker build/prefix 证据升级为硬件证据。

## 范围对照

已覆盖：

- 用户价值和产品北极星。
- OKR 映射。
- Sprint 内 KR 拆解。
- 本轮核心抓手。
- 做什么和不做什么。
- 优先级和验收口径。
- 对应责任 Engineer。
- 风险、阻塞和证据链。
- 需要创建或更新的 sprint 文档。

未覆盖且不应由 Product 本轮覆盖：

- Docker Compose 文件修复。
- shell 脚本修复。
- README 使用说明修复。
- ROS2/HIL/硬件运行验证。

## 验收结果占位

Product scoped diff check 结果记录在 `final.md`。工程侧 Docker Compose/build/colcon/package prefix 运行证据由 `robot-software-engineer` 在其交付中记录；Product 只在本文件做收口对照。

当前 Product 验收判断：

- Mac-first Compose/X11 环境口径：工程侧配置修正可作为本轮完成项记录。
- Docker/Humble 完整 build：已恢复通过，可作为 `software_proof_docker_only` 完成项记录。
- ROS2 package prefix：`ros2 pkg prefix ros2_trashbot_bringup` 已返回 `/ws/install/ros2_trashbot_bringup`，说明 bringup 包在容器构建产物中可解析。
- HIL/真实硬件链路：无新增通过证据，不声明真实串口、底盘运动、反馈流或 `hil_pass`。

## 剩余风险

- 当前证据来自 Docker 容器软件验证，不覆盖真实串口设备、WAVE ROVER 反馈、轮向/速度单位、IMU、电池或 HIL evidence packet。
- `src/ros2_trashbot_bringup/CMakeLists.txt` 的修复解决的是 packaging 安装不存在 `config` 目录的问题，不代表 launch 行为、硬件 bringup 或实机任务闭环已验证。
- Product 不更新 `OKR.md` 完成度；后续 O1 仍需真实硬件/HIL 证据才能推进完成度。
