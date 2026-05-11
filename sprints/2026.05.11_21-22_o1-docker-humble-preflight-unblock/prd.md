# Sprint 2026.05.11_21-22 O1 Docker Humble Preflight Unblock - PRD

## 状态

- 阶段：prd
- 时间：2026-05-11 21:00 Asia/Shanghai
- 产品负责人：`product-okr-owner`
- 目标 owner：`hardware-engineer`

## 背景和问题

近期证据显示，O1 是当前最低完成度目标：`OKR.md` 4.1 中 O1 约 75%，O2/O3 约 77%，O4 约 76%，O5 约 80%。最新 O1 sprint 已尝试把 Docker/Humble preflight 作为真实 HIL 前置门槛，但 `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 被 `osrf/ros:humble-desktop` metadata/unpack 异常阻断，日志包含 `encountered unknown type text/html; children may not be fetched`。

CEO 明确本机只有 Docker、没有真实硬件。因此本轮不能要求真实 WAVE ROVER `--move-test`，不能声明 `hil_pass`，但必须让 Docker/Humble preflight 进入可诊断、可复跑、可交给下一台有硬件的机器继续执行的状态。

## 用户价值和产品北极星

普通用户最终只关心小车能否可靠送垃圾，不关心 Docker、ROS2 或串口细节。对产品来说，O1 preflight 是把“工程机能否稳定履约”变成可审计证据的入口。若 Docker/Humble 环境本身不可诊断，后续 O2 任务闭环和 O3 route replay 的实机证据都无法可靠复账。

本轮价值不是新增功能页面或测试数量，而是让底盘/HIL 履约路径从环境阻塞中前进一格：能成功构建就成功构建；不能成功也要知道卡在 registry/proxy/cache/base image，而不是停在模糊失败。

## OKR 映射

- O1.KR：硬件协议可信底盘。主线修复 Docker/Humble preflight 阻断，为后续 WAVE ROVER UART JSON real run 和 `hil_pass` evidence packet 铺路。
- O2.KR：可恢复任务闭环。保持 same-`evidence_ref` 软件复账成果，不在本轮扩展任务状态机。
- O3.KR：可验证导航与固定路线。保留后续 route replay 与 task record 同 `evidence_ref` 交叉证明口径，不在无硬件/无路线环境下假装实跑。

## KR 拆解或更新

| KR | 用户可感知收益 | 本轮可交付证据 |
| --- | --- | --- |
| O1.KR1 Docker preflight 可诊断 | 工程团队能稳定判断环境是否可用于 ROS2/HIL 履约。 | `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 成功，或输出足够定位 registry/proxy/cache/base image HTML metadata 的失败日志。 |
| O1.KR2 HIL 证据边界清晰 | 不把 dry-run 或无串口主机结果误传成实机能力。 | HIL runbook/checklist 明确 Docker-only host、无 `/dev/ttyUSB*` 只能是 blocked/preflight evidence。 |
| O1.KR3 下一台有硬件机器可接续 | 真机 owner 能按同一入口继续执行 move-test 和 evidence packet 采集。 | 文档和脚本入口保留 `EXTRA_DOCKER_ARGS="--device=<real_serial_device>"` 与 smoke status/move-test 分界。 |
| O2/O3.KR4 同证据引用复账不丢 | 后续真实 route/task record 能继续按 same-`evidence_ref` 对账。 | 本轮不改 O2/O3 主逻辑，不新增宽泛测试，只保留验收口径。 |

## 本轮核心抓手

主抓手是 O1 Docker/Humble preflight unblock。`hardware-engineer` 应从失败证据倒推最小工程改动：让脚本在 Docker registry 返回 HTML、metadata 解包失败、host cache 异常或代理问题时输出明确诊断建议，并尽量恢复 `ros-rbs-humble:dev` image build。

## 做什么

- 修复或增强 `scripts/docker_humble_build.sh` 的 preflight 诊断。
- 如必要，最小修改 `docker/humble/Dockerfile` 以提高基础镜像和镜像源失败的可定位性。
- 如必要，最小同步 `scripts/docker_humble_dev.sh` 的文档化入口，保证 real serial device handoff 清晰。
- 更新 `docs/acceptance/hil_runbook.md` 和 `docs/acceptance/robot_bringup_checklist.md` 的 blocked/preflight evidence 边界。
- 记录本 sprint 的实际改动和验证结果到 `tech-done.md`。

## 不做什么

- 不执行真实 `--move-test`，除非环境实际出现可用 WAVE ROVER 串口设备且 owner 明确记录设备来源。
- 不声明 `hil_pass`。
- 不新增测试文件、不扩展宽泛测试矩阵。
- 不修无关 README whitespace 或其他非本轮 blocker。
- 不触碰 `.codex/config.toml`。

## 优先级

| 优先级 | 需求 | 理由 |
| --- | --- | --- |
| P0 | Docker/Humble preflight 成功或精确阻断归因 | 当前 O1 最低，且最新 blocker 正在这里。 |
| P0 | 无硬件边界写清 | CEO 已说明本机只有 Docker，必须防止虚假 `hil_pass`。 |
| P1 | smoke status 仍可作为 readiness evidence | 后续有硬件时需要同一入口接续。 |
| P2 | O2/O3 same-`evidence_ref` 口径保留 | 防止主线修 O1 时破坏前序软件 proof。 |

## 验收口径

1. `bash -n scripts/docker_humble_build.sh scripts/docker_humble_dev.sh` 通过。
2. `SKIP_COLCON=1 bash scripts/docker_humble_build.sh` 成功；若仍失败，`tech-done.md` 必须记录精确错误和归因，不允许只写“Docker 失败”。
3. `python3 scripts/hardware_smoke_wave_rover.py --status` 能运行并记录当前 `hil_ready`、`blocked_reason`。
4. `git diff --check -- <touched files>` scoped 通过；不因 README 既有 whitespace 阻断本轮。
5. 最终说明明确本轮是 `software/preflight` 或 `blocked/preflight evidence`，不是 `hil_pass`。

## 对应责任 Engineer

- `hardware-engineer`：主责实现、验证、修复和 `tech-done.md` 更新。
- `robot-software-engineer`：如 ROS build contract 或脚本入口影响包构建语义，只做只读咨询或接口事实补充。

## 风险和阻塞

- Docker registry、镜像站或代理返回 HTML，造成 OCI metadata 无法正常拉取或解包。
- Host Docker cache 损坏，导致脚本改动后仍需 operator 清 cache 或换 registry 验证。
- 本机无真实 `/dev/ttyUSB*`，因此 smoke status 只能证明 readiness/blocker，不能证明底盘运动。
- O2/O3 真实复账继续等待 O1 real run 或真实 route/Nav2 run。

## 需要更新的 sprint 文档

- 当前：`pre_start.md`、`prd.md`、`tech-plan.md`
- 实现后：`tech-done.md`
- 验收/收口后：`side2side_check.md`、`final.md`
