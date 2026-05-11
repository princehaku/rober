# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-11 21:00 Asia/Shanghai
- 主责 owner：`hardware-engineer`
- 协作方式：文件范围简单时由 `hardware-engineer` 单线闭环；`robot-software-engineer` 仅在 ROS build contract 或脚本入口语义不清时只读咨询。

## 目标

修复或增强 Docker/Humble preflight 阻断路径，让 `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 在本机 Docker 环境里至少达到以下之一：

1. 成功构建 `ros-rbs-humble:dev`。
2. 如果仍失败，精确定位为 Docker registry/proxy/base image metadata/host cache 问题，并把错误原文和 operator 下一步写入 sprint `tech-done.md`。

本轮不得把 Docker preflight、smoke status 或无串口 blocked 结果声明为真实 `hil_pass`。

## 事实来源和近期证据

- `OKR.md` 4.1：O1 约 75%，是当前最低完成度目标。
- `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/final.md`：`SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 被 `osrf/ros:humble-desktop` metadata/unpack 失败阻断，错误含 `encountered unknown type text/html; children may not be fetched`。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 same-`evidence_ref` software proof 已收口，targeted tests OK，但缺真实 Nav2/fixed-route/HIL run。
- 当前用户约束：本机只有 Docker，没有真实 WAVE ROVER/串口硬件。

## 文件范围

允许 `hardware-engineer` 在实现阶段修改：

- `scripts/docker_humble_build.sh`
- `scripts/docker_humble_dev.sh`（仅必要时）
- `docker/humble/Dockerfile`（仅必要时）
- `docs/acceptance/hil_runbook.md`
- `docs/acceptance/robot_bringup_checklist.md`
- `sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/*`
- `OKR.md`（仅收口时更新证据和进度，不得提前虚增）

禁止触碰：

- `.codex/config.toml`
- 无关 README whitespace
- O2/O3 代码主逻辑，除非后续主会话另行派发对应 owner
- 宽泛测试矩阵或新测试堆叠

## 任务拆解

### Task 1：Docker/Humble preflight 诊断增强

Owner：`hardware-engineer`

工作内容：

- 检查 `scripts/docker_humble_build.sh` 当前失败路径。
- 让脚本输出当前 Docker builder、base image、registry/proxy/cache 相关诊断信息，便于定位 `text/html` metadata/unpack。
- 若能通过调整 pull/build 参数、cache 策略或错误提示解决，保持改动最小。
- 不改变默认 ROS2 Humble 目标，不为了本机 Ubuntu 24.04 改造项目目标。

验收：

```bash
bash -n scripts/docker_humble_build.sh scripts/docker_humble_dev.sh
SKIP_COLCON=1 bash scripts/docker_humble_build.sh
```

若第二条仍失败，`tech-done.md` 必须记录：

- 完整关键错误片段。
- 失败归因：registry/proxy/cache/base image metadata/host Docker 状态中的哪一类。
- operator 下一步：重试、清 cache、换网络/镜像源或在另一台 Docker host 重跑。

### Task 2：HIL runbook/checklist 边界同步

Owner：`hardware-engineer`

工作内容：

- 更新 `docs/acceptance/hil_runbook.md` 和 `docs/acceptance/robot_bringup_checklist.md`，明确 Docker-only host 与无 `/dev/ttyUSB*` 的验收边界。
- 写清 `python3 scripts/hardware_smoke_wave_rover.py --status` 是 readiness/blocker evidence，不是 move-test。
- 保留真实串口设备 handoff：`EXTRA_DOCKER_ARGS="--device=<real_serial_device>" bash scripts/docker_humble_dev.sh`。

验收：

```bash
python3 scripts/hardware_smoke_wave_rover.py --status
```

预期：

- 能输出 `hil_ready` 与 `blocked_reason`。
- 若无串口，记录为 blocked/preflight evidence。
- 不生成或宣称真实 `hil_pass` evidence packet。

### Task 3：Sprint 执行记录和收口

Owner：`hardware-engineer`

工作内容：

- 在本 sprint 目录更新 `tech-done.md`，记录实际改动、验证输出、Docker preflight 结果和剩余风险。
- 如验收状态发生变化，更新 `side2side_check.md` 和 `final.md`。
- 若 Docker preflight 成功但仍无硬件，结论仍应是 Docker preflight unblocked、HIL real run pending。
- 若 Docker preflight 仍失败，结论应是 blocked with precise diagnosis。

验收：

```bash
git diff --check -- <touched files>
```

注意：只检查 touched files，不使用 repo-wide `git diff --check`，避免无关 README whitespace 干扰。

## 接口影响

- 不改变 ROS2 package API。
- 不改变 WAVE ROVER 协议语义。
- 不改变 O2/O3 same-`evidence_ref` 数据 contract。
- 如修改 Dockerfile 或脚本参数，必须保持现有入口兼容：
  - `bash scripts/docker_humble_build.sh`
  - `SKIP_COLCON=1 bash scripts/docker_humble_build.sh`
  - `bash scripts/docker_humble_dev.sh`

## 验收命令

实现 owner 必须运行并回报：

```bash
bash -n scripts/docker_humble_build.sh scripts/docker_humble_dev.sh
SKIP_COLCON=1 bash scripts/docker_humble_build.sh
python3 scripts/hardware_smoke_wave_rover.py --status
git diff --check -- <touched files>
```

如果 Docker 仍失败，第二条允许失败，但必须在 `tech-done.md` 记录精确错误和定位；不得把失败简写成不可复现的环境问题。

本轮前置文档自身围栏：

```bash
git diff --check --no-index /dev/null sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/pre_start.md
git diff --check --no-index /dev/null sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/prd.md
git diff --check --no-index /dev/null sprints/2026.05.11_21-22_o1-docker-humble-preflight-unblock/tech-plan.md
```

`--no-index /dev/null` 对新文件通常以 exit 1 表示存在差异；只要没有 whitespace error 行，即视为文档围栏通过。

## 风险边界

- Docker registry 或代理返回 HTML：只能记录为 Docker preflight blocked，不能视为代码功能失败。
- Host Docker cache/proxy 问题：可以给出清 cache、换网络或换 host 的下一步，但不能虚构已成功。
- 无真实 `/dev/ttyUSB*`：只能记录 blocked/preflight evidence，不是 `hil_pass`。
- O2/O3 后续 same-`evidence_ref` 复账必须等待真实 HIL 或真实 route/Nav2 run；本轮不以新测试堆叠替代。

## 完成前反思清单

- 是否仍以 O1 为主线，没有漂移到 O2/O3/UI？
- 是否明确区分 `software_proof`、blocked/preflight evidence 和 `hil_pass`？
- 是否只修改允许文件，且未触碰 `.codex/config.toml`？
- 是否运行了围栏命令，或记录了无法运行的具体原因？
- 是否把实现结果写入 `tech-done.md`，并在需要时更新 `side2side_check.md` / `final.md`？
