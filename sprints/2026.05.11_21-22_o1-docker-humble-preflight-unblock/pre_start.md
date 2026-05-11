# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-11 21:00 Asia/Shanghai
- 触发请求：开始下一轮迭代，根据近期 PR 和评审继续完成 OKR；优先推进完成度最低的 OKR；本机只有 Docker、没有真实硬件；测试只做围栏；最后由主会话在实现收口后提交并推送。

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车能沿固定路线完成低成本、可复盘、可恢复的送垃圾闭环。当前最影响北极星可信度的不是继续新增上层功能，而是 O1 底盘/HIL 证据链仍未形成真实 `hil_pass`，且最近 Docker/Humble preflight 被基础镜像拉取/解包异常阻断。

本轮用户价值：把本机 Docker 环境从“失败但难定位”推进到“失败可诊断、可重试、可区分 registry/proxy/cache/host 串口缺失”，为后续真实 WAVE ROVER 串口 run 提供清晰入口。

## OKR 映射

| 优先级 | Objective | 当前证据 | 本轮判断 |
| --- | --- | --- | --- |
| P0 | O1 硬件协议可信底盘 | `OKR.md` 4.1 显示 O1 约 75%，低于 O2/O3/O4/O5；最新 O1 sprint 因 `osrf/ros:humble-desktop` metadata/unpack 失败和本机无串口 blocked。 | 主线深入 O1，先解 Docker/Humble preflight 可诊断性，不声明 `hil_pass`。 |
| P1 | O2 可恢复送垃圾任务闭环 | 最新 O2/O3 sprint 已用 same-`evidence_ref` software proof 收口，targeted tests OK。 | 保持复账口径，不扩大测试堆叠，不抢 O1 主线。 |
| P1 | O3 可验证导航与固定路线 | `evidence_crosscheck.py` 已能按同一 `evidence_ref` 对齐 task record，但缺真实 Nav2/fixed-route run。 | 仅在文档中保持后续复账边界，等 O1 real run 解锁。 |

## 上轮未完成项和阻塞

- `sprints/2026.05.11_10-11_hil-docker-preflight-to-real-run/final.md`：`SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 被 `osrf/ros:humble-desktop` metadata/unpack 失败阻断，错误包含 `encountered unknown type text/html; children may not be fetched`。
- 同一 O1 sprint：本机没有真实 `/dev/ttyUSB*` 串口设备，无法产生 WAVE ROVER `hil_pass` evidence packet。
- `sprints/2026.05.11_10-11_o2-task-recovery-route-replay-docker-proof/final.md`：O2/O3 software proof 已收口，但仍缺真实 Nav2/fixed-route/HIL run。

## KR 拆解

| KR | 目标 | 证据口径 |
| --- | --- | --- |
| O1.KR-A | Docker/Humble preflight 能区分镜像 metadata HTML、registry/proxy、host cache 和脚本自身错误。 | `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 成功，或失败时日志能明确定位到外部 registry/proxy/cache。 |
| O1.KR-B | HIL runbook 明确 Docker-only host 的边界。 | 文档写清无真实 `/dev/ttyUSB*` 只能形成 blocked/preflight evidence，不是 `hil_pass`。 |
| O1.KR-C | smoke status 仍作为真实硬件前置检查，不替代 move-test。 | `python3 scripts/hardware_smoke_wave_rover.py --status` 输出被记录为 readiness/blocker evidence。 |
| O2/O3.KR-D | 保持 same-`evidence_ref` 后续复账口径。 | 不新增宽泛测试矩阵；只保留后续真实 run 后的对账入口。 |

## 本轮核心抓手

1. 由 `hardware-engineer` 主责 Docker/Humble preflight 履约：优先修复或增强脚本和 Dockerfile 的可诊断路径。
2. `robot-software-engineer` 只做脚本/ROS build contract 只读咨询；若文件范围保持简单，本轮由 `hardware-engineer` 单线闭环。
3. 把所有结论按 `software_proof`、`blocked/preflight evidence`、真实 `hil_pass` 分开记录。

## 做什么

- 创建本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 下一阶段允许 `hardware-engineer` 针对 Docker/Humble preflight 的脚本、Dockerfile 和 HIL 文档做最小改动。
- 围栏验证：shell syntax、Docker image preflight 或精确失败记录、hardware smoke status、scoped diff check。

## 不做什么

- 不做真实 `--move-test`，因为本机没有真实 WAVE ROVER/串口设备。
- 不声明 `hil_pass`。
- 不新增宽泛测试矩阵，不用测试堆叠代替功能推进。
- 不修无关 README whitespace。
- 不触碰 `.codex/config.toml` 或其他本轮范围外文件。

## 优先级和验收口径

| 优先级 | 验收点 | 通过标准 |
| --- | --- | --- |
| P0 | Docker/Humble preflight unblock | `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 成功，或失败日志精确归因 registry/proxy/cache/base image metadata。 |
| P0 | HIL 边界 | 文档和最终汇总明确：本机无真实硬件，只能 blocked/preflight evidence，不能 `hil_pass`。 |
| P1 | smoke readiness | `python3 scripts/hardware_smoke_wave_rover.py --status` 可运行并记录 `hil_ready`/`blocked_reason`。 |
| P2 | O2/O3 复账保留 | 保持 same-`evidence_ref` 后续入口，不新增大范围测试。 |

## 对应责任 Engineer

- 主责：`hardware-engineer`，负责 Docker/Humble preflight、HIL runbook/checklist、真实硬件边界。
- 咨询：`robot-software-engineer`，仅在 ROS build contract 或脚本入口语义不清时做只读接口咨询。
- 不介入：`autonomy-engineer`、`full-stack-software-engineer`，本轮不扩展 Nav2/UI 功能。

## 风险、阻塞和证据链缺口

- Docker registry 或代理返回 HTML，导致 base image metadata/unpack 阻断。
- Host Docker cache 或 Docker Desktop/Engine 状态导致同一脚本在不同机器表现不一致。
- 本机没有真实 `/dev/ttyUSB*`，无法形成 `command.txt`、`serial.log`、`feedback_T1001.log`、ROS topic samples 的 `hil_pass` evidence packet。
- O2/O3 真实 route/task_record 交叉复账仍等待 O1 real run 或真实 fixed-route/Nav2 run。

## 需要创建或更新的 sprint 文档

- 已创建：`pre_start.md`
- 本轮同时创建前置文档：`prd.md`、`tech-plan.md`
- 实现后必须由执行 owner 更新：`tech-done.md`
- 如验收或风险状态变化，继续更新：`side2side_check.md`、`final.md`
