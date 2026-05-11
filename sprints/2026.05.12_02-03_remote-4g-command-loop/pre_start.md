# Sprint 2026.05.12_02-03 Remote 4G Command Loop - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 02:03 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主目标：O6-first，本地 Docker-only 可验证的 mock cloud / cloud API 最小命令闭环
- 证据边界：本轮目标是 `software_proof_docker_only`，不声明真实 4G、真实云部署、真实 SIM、真实硬件或 HIL

## 用户价值和产品北极星

北极星是普通用户只用手机即可让低成本 ROS2 垃圾投递机器人接收任务、回报状态、暴露异常并可复盘。当前最低完成度是 O6 4G 云中转，只有约 5% 的产品契约和基础设施方向；若没有云端命令/状态/ACK 闭环，手机端即使美观也仍停留在本地 fallback，无法支撑“手机和小车不在同一 WiFi”的正式使用路径。

本轮价值是先把 4G 正式链路压缩成 Docker-only 可验证的本地 mock cloud：phone/web 或脚本提交 command，robot `remote_bridge` 只做 outbound polling 拉取命令、post status、post ack。O5 手机体验只作为最小安全触点，不做大 UI 重构；O1/HIL 继续保留阻塞事实，不作为本轮主线。

## 近期证据

| 证据 | 对本轮的含义 |
| --- | --- |
| `OKR.md` 最新快照：O6 约 5%，O5 下调到 30%，O1/O2/O3 约 75% 且真实硬件 blocked | 优先推进完成度最低的 O6；O5 只做支撑入口；不把本机无硬件的环境继续消耗在 O1/HIL 主线上 |
| `sprints/2026.05.12_01-02_mac-docker-humble-env/final.md` | Docker/Humble 与 `colcon build` 已恢复通过，但证据是 `software_proof_docker_only`，适合做本地 mock cloud 和 bridge 验证 |
| `sprints/2026.05.11_23-24_hil-packet-crosscheck-bridge/final.md` | HIL/crosscheck 桥已就绪，但仍没有真机；继续冲 O1 不能在本机产生真实 `hil_pass` |
| `docs/product/remote_4g_mvp.md` | O6 已有正式 contract：cloud API、command/status/ack、安全边界；缺的是可运行的云中转服务和机器人 outbound polling 闭环 |

## OKR 映射

- O6：主推进。把文档级 contract 推进到本地可运行、可测试、可复现的 mock cloud / cloud API / remote bridge 命令闭环。
- O5：支撑推进。只提供 phone-safe 操作/状态入口，确保普通用户入口不会暴露 `/cmd_vel` 或硬件细节。
- O2：间接受益。remote bridge 只调用 behavior-level 合同，不绕过任务状态机。
- O1/O3：不作为本轮主线。本机无真实硬件，真实 HIL 和实机 route replay 不在本轮验收范围内。

## KR 拆解

### O6-KR1：mock cloud API 最小闭环

- 用户或脚本可提交 `collect` / `confirm_dropoff` / `cancel` command。
- robot 侧可通过 outbound polling 获取 next command。
- robot 侧可 post status。
- robot 侧可 post ack，ack state 限定为 `acked` / `failed` / `ignored`。
- command id 具备幂等语义，重复 id 不重复执行。

### O6-KR2：remote bridge 最小执行路径

- `remote_bridge` 只从 cloud 拉命令，不接受 inbound robot 连接。
- bridge 验证 command contract：`protocol_version`、`id`、`type`、`expires_at`、`payload`。
- bridge 不暴露 `/cmd_vel`，只走 behavior-level ROS 合同或 Docker/local mock 行为适配层。
- malformed / expired / duplicate / busy command 有明确 ack。

### O5-KR1：最小 phone-safe 入口

- 只实现或保留一页/一个脚本级入口：提交 command、读取 robot status、读取 ack。
- 文案面向普通用户状态，不要求理解 ROS2、SSH、串口或 `/cmd_vel`。
- 不做视觉重构、全量 UI 改版、登录体系、OSS 图片流或美术大改。

## 本轮核心抓手

把 `docs/product/remote_4g_mvp.md` 的 contract 落成一个 Docker-only 可跑的“命令 -> polling -> ack/status”闭环，并用围栏测试证明：

1. command 从 phone/web/script 进入 cloud API。
2. robot bridge 通过 outbound polling 取得 command。
3. bridge 提交或模拟提交到 behavior-level 合同。
4. bridge 回写 ack 和 status。
5. phone/web/script 能读到状态和 ack。

## 做什么 / 不做什么

做：

- 创建本地 mock cloud / cloud API。
- 创建或接入 robot `remote_bridge` outbound polling。
- 增加最小 phone-safe command/status/ack 入口。
- 增加围栏级验证：contract 单测、bridge mocked-loop 测试、Docker/Humble 可运行验证、scoped diff check。
- 更新本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md` 后再收口。

不做：

- 不做真实云部署、域名、TLS、生产鉴权、账号体系、STS、OSS 图片上传或 CDN 流水线。
- 不做真实 4G SIM、运营商网络、NAT、弱网或断网恢复实测。
- 不做大 UI 重构，不把 O5 作为主目标。
- 不碰 WAVE ROVER、ESP32、UART、引脚、电压、波特率或硬件配置。
- 不声明 O1/HIL、真实底盘运动、真实 route replay 或 `hil_pass`。

## 优先级和验收口径

| 优先级 | 抓手 | 验收口径 | Owner |
| --- | --- | --- | --- |
| P0 | mock cloud API | 本地可启动；command/status/ack 三个 contract 可读写；非法 command 有确定响应 | `full-stack-software-engineer` |
| P0 | remote bridge outbound polling | bridge 拉取 command、提交行为适配、post ack/status；duplicate/expired/busy/malformed 有围栏测试 | `robot-software-engineer` |
| P1 | phone-safe 最小入口 | 页面或脚本能发 command、看 status/ack；不暴露 `/cmd_vel` 和硬件细节 | `full-stack-software-engineer` |
| P1 | Docker-only 验证 | 在 Mac Docker/Humble 环境内完成最小闭环验证；记录为 `software_proof_docker_only` | `robot-software-engineer` |
| P2 | 产品收口 | 更新 sprint 后三份留档；明确 O6 进度和剩余风险，不更新 O1/HIL | `product-okr-owner` |

## 风险、阻塞和证据链

- 当前没有真实硬件、SIM 或云部署，本轮只能形成 `software_proof_docker_only`。
- 如果 Docker/Humble 构建入口再次漂移到 WSL bind mount 路径，按环境口径问题处理，不改成本轮 O6 范围。
- 鉴权只能做本地 bearer token/环境变量占位，不能宣称生产安全已完成。
- command accepted/acked 不等于送达完成；最终状态必须靠 status 后续更新表达。
- O6 完成度只能在 mock cloud + bridge + phone-safe 入口实际实现并验证后上调；计划文档本身不提升 OKR。

## 需要创建或更新的 sprint 文档

本轮先创建：

- `sprints/2026.05.12_02-03_remote-4g-command-loop/pre_start.md`
- `sprints/2026.05.12_02-03_remote-4g-command-loop/prd.md`
- `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-plan.md`

实现后必须继续更新：

- `sprints/2026.05.12_02-03_remote-4g-command-loop/tech-done.md`
- `sprints/2026.05.12_02-03_remote-4g-command-loop/side2side_check.md`
- `sprints/2026.05.12_02-03_remote-4g-command-loop/final.md`
