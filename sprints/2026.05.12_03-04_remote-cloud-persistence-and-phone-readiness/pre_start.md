# Sprint 2026.05.12_03-04 Remote Cloud Persistence And Phone Readiness - Pre Start

## 状态

- 阶段：pre_start
- 时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- Sprint 类型：O6 主线功能前进 + O5 手机可读状态支撑
- 证据边界：本机只有 Docker；本轮计划只能形成 `software_proof_docker_only`，不能形成真实 4G、真实云、真实 HIL 或 WAVE ROVER `hil_pass`

## 用户价值和产品北极星

北极星是让普通手机用户在不懂 ROS2、SSH、串口或硬件参数的情况下，通过 4G 云中转给小车下发送垃圾任务、查看状态、理解失败原因，并在弱网或机器人重启后不丢命令、不重复误执行。

本轮用户价值不是再做一个 debug 入口，而是把 02-03 已完成的 local mock command loop 往“正式云之前最小可靠控制面”推进：命令队列要可持久化，robot polling cursor 要跨重启可恢复，phone 读到的 status/ack 要能解释当前远程 readiness。

## OKR 映射

| Objective | 当前证据 | 本轮定位 |
| --- | --- | --- |
| O6：4G 云中转 + OSS/CDN 数据通路产品化 | `OKR.md` 最新快照为约 12%；02-03 final 只证明 local mock cloud / remote bridge command loop，剩余风险指向真实云前的持久化队列、cursor、bearer/鉴权、弱网/重启恢复 | 本轮主线。先在 Docker/local mock 中补齐 cloud persistence 与 recovery contract，为后续真实云部署降风险 |
| O5：手机用户体验与量产边界 | `OKR.md` 最新快照为约 30%；缺正式手机 UI 和普通用户验收 | 本轮只做 phone-readable remote readiness/status，不做空心大 UI、不把 operator/debug 入口冒充正式手机端 |
| O1/O2/O3：硬件、任务闭环、固定路线 | O1/O2/O3 软件链路较高但真实硬件仍受 `/dev/ttyUSB0` 阻断 | 本机无真实硬件，本轮不以 HIL 为主线；如触及硬件只记录 blocked，不升级完成度 |

## 近期证据

1. `OKR.md` 2026-05-12 快照：O6 约 12%，是最低完成度；O5 约 30%，仍缺正式手机 UI/普通用户体验；O1/O2/O3 当前主缺口需要真实硬件或实跑环境。
2. `sprints/2026.05.12_02-03_remote-4g-command-loop/final.md`：02-03 已完成本地 mock cloud command/status/ack、robot outbound polling 和 integration smoke，但明确未做真实云、真实 4G/SIM、弱网恢复、生产鉴权、OSS/CDN。
3. `docs/product/remote_4g_mvp.md`：当前 API contract 已有 commands/status/ack，但 local mock cloud 是内存控制面；正式 4G 路径仍需要 cloud-side command store 与 robot cursor 语义。
4. `docs/product/mobile_user_flow.md`：普通用户不应看到 raw JSON、ROS topic、串口或硬件参数；phone 状态需要使用用户可理解的 copy 和 action readiness。

## 上轮未完成项和阻塞

- 未完成：持久化队列；`last_ack_id` / cursor 跨重启恢复；未知 cursor 策略；bearer token 鉴权边界；弱网/断网后 status 与 ack 恢复。
- 未完成：phone-readable remote readiness/status，即手机端能区分 cloud reachable、robot polling、last command ack、stale status、needs retry 等用户可读状态。
- 阻塞：本机没有真实 `/dev/ttyUSB0`，不能跑 WAVE ROVER/HIL；本轮不得把 Docker-only proof 写成 `hil_pass`。
- 阻塞：没有真实云账号、域名、HTTPS/TLS、公网入口、SIM/运营商网络；本轮目标是生产前 contract 和 Docker-only proof，不声明真云可用。

## 本轮核心抓手

1. `full-stack-software-engineer`：把 local mock cloud 从内存 command loop 推进到可持久化队列和 phone-readable remote readiness/status。
2. `robot-software-engineer`：让 `remote_bridge` 的 cursor/status 边界能跨进程或跨重启复盘，并用 Docker-only integration smoke 证明不重复错取命令。
3. `product-okr-owner`：本轮计划阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`；执行收口时再更新 `tech-done.md`、`side2side_check.md`、`final.md`，必要时保守更新 `OKR.md`。

## 做什么 / 不做什么

做：

- 做 O6 remote cloud persistence/readiness 的最小可执行功能计划。
- 做 O5 手机可读状态支撑，让用户能理解远程控制链路是否 ready、stale、blocked 或需要重试。
- 保持验证围栏：targeted unittest、`py_compile`、scoped `git diff --check`。
- 记录 Docker-only 证据边界。

不做：

- 不做正式美观手机 UI 大改版。
- 不做真实云部署、域名、HTTPS/TLS、SIM 或公网 4G 实测。
- 不做 OSS/CDN 图片链路实现。
- 不做硬件串口、WAVE ROVER 参数或 HIL 运行；没有硬件时不升级 O1 完成度。
- 不新增一堆测试文件；只围绕现有 targeted tests 和必要 smoke。

## 需要创建或更新的 sprint 文档

- 当前计划阶段创建并填写：
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/pre_start.md`
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/prd.md`
  - `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/tech-plan.md`
- 执行收口阶段再创建：
  - `tech-done.md`
  - `side2side_check.md`
  - `final.md`
