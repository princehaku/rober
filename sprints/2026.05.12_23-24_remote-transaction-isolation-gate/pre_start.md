# Sprint 2026.05.12_23-24 Remote Transaction Isolation Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 23:00 CST
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- Fresh sprint folder：`sprints/2026.05.12_23-24_remote-transaction-isolation-gate/`
- Evidence boundary 目标：`software_proof_docker_transaction_isolation_gate`

## 开工依据

本轮从 live `OKR.md` 重新排序：O5 约 50%，O6 约 49%。当前主机仍是 Docker-only，没有真实硬件、真实手机、真实云或 4G 条件，因此 O6 是最低可行动项。

上一轮 `sprints/2026.05.12_22-23_phone-support-bundle-gate/final.md` 已完成 O5 local/Docker phone support bundle gate，并明确如果仍是 Docker-only，应继续 O6 生产化前置 gate。更早的 `sprints/2026.05.12_21-22_remote-queue-ordering-drill/final.md` 已覆盖 Docker/local queue ordering drill，但仍把 `transaction isolation`、真实生产 DB/queue、多实例一致性和真实云/4G 列为 `not_proven`。

## 用户价值和产品北极星

普通用户不会理解 command queue、ACK cursor 或 transaction isolation。产品价值是：未来手机通过 4G 云中转发车时，即使同一台 robot 出现并发 command/status/ack 写入，系统也不能把未完成命令跳过去，不能让 ACK cursor 越过未完成命令，更不能把 ACK 包装成真实送达成功。

本轮只推进 Docker/local software proof，把风险前置到 preflight、phone readiness 和 diagnostics。它服务于“普通用户只用手机，小车完成 trash delivery”的北极星，但不声明真实云、真实 4G、真实生产 DB/queue 或真实送达已经完成。

## 上轮未完成项和阻塞

- `transaction isolation`：未证明。需要新增 Docker/local artifact/preflight/phone-safe summary 来验证并发 command/status/ack 写入下的 cursor 保守语义。
- 真实生产 DB/queue：未证明。Docker/local gate 必须继续保留 `production_ready=false`。
- 多实例一致性：未证明。本轮不做多进程或多节点一致性，只做同一 robot 在本地 proof store 上的并发写入隔离语义。
- 真实云/4G/SIM/HTTPS 公网入口：未提供环境，不能作为验收目标。
- 真实手机设备、Nav2/fixed-route、WAVE ROVER、HIL、真实送达：均不在本轮证据范围内。

## 本轮核心抓手

新增 `trashbot.transaction_isolation_drill` artifact gate，并接入 production preflight、operator status/diagnostics 的 phone-safe summary。验证同一 robot 的并发 command/status/ack 写入满足：

- ACK cursor 只能推进到已 terminal ACK 且之前命令没有未完成缺口的位置。
- 未完成命令存在时，后续 ACK 不得让 cursor 越过该缺口。
- ACK 只代表 command envelope 被接受、处理、忽略或失败记录，不代表 delivery success。
- Artifact 和 phone-safe summary 不暴露 token、Authorization、DB/queue URL、local path、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER 参数或 traceback。
- `production_ready=false` 必须保持，且明确不等于真实生产 DB/queue、多实例一致性、真实云或真实 4G。

## Owner 和责任边界

- Task A / `full-stack-software-engineer`：主实现。负责 relay artifact、CLI/preflight、operator status/diagnostics phone-safe summary、相关 full-stack/operator tests 和产品文档同步。
- Task B / `robot-software-engineer`：compatibility fence。负责 remote bridge 兼容性验证，确认新 metadata 不污染 `trashbot.remote.v1` command/status/ack envelope、不触发 robot action、不 ACK、不推进或持久化 cursor。
- Product closeout / `product-okr-owner`：实现完成后再更新 `OKR.md`、`tech-done.md`、`side2side_check.md`、`final.md`。本次规划阶段不创建 closeout docs。

## 验收口径

本轮验收只接受 Docker/local software proof：

- `trashbot.transaction_isolation_drill` artifact schema/version/checksum 可验证。
- Preflight 可消费 artifact，并在有效时输出 transaction isolation gate pass，但 `production_ready=false` 保持。
- `/api/status.phone_readiness.transaction_isolation` 与 `/api/diagnostics.transaction_isolation` 只输出 phone-safe summary。
- Robot compatibility fence 确认 metadata-only blocked response 不触发 action、不 ACK、不推进或持久化 cursor。
- 文档同步更新 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md` 和必要接口文档。
- 验证只做围栏：targeted unittest、`py_compile`、CLI smoke、scoped `git diff --check`。

## 风险和证据缺口

- 通过本轮后，O6 只能保守增加 Docker/local transaction-isolation gate 证据，不能声明生产级 transaction isolation。
- 如果实现只验证 happy path ACK，而没有构造“中间命令未完成、后续 ACK 到达”的缺口场景，则不满足本轮验收。
- 如果 phone-safe summary 泄露完整 artifact、checksum、路径、凭证、DB/queue URL、ROS/hardware 细节，必须退回修复。
- 如果 robot fence 无法证明 metadata 不触发 action/ACK/cursor，不能进入 Product closeout。
