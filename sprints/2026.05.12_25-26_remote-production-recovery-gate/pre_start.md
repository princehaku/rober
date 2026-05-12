# Sprint 2026.05.12_25-26 Remote Production Recovery Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 25:00 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主线 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- Fresh sprint folder：`sprints/2026.05.12_25-26_remote-production-recovery-gate/`
- Evidence boundary 目标：`software_proof_docker_production_recovery_gate`

## 开工依据

本轮从 live `OKR.md` 和最近 sprint final 重新排序：O5 约 52%，O6 约 51%。O1/O2/O3/O4 虽然约 74-76%，但剩余缺口依赖真实 WAVE ROVER、真实串口、真实 Nav2/fixed-route、真实相机或 HIL；当前主机只有 Docker，没有真实硬件，因此这些缺口本轮不可行动。

`sprints/2026.05.12_23-24_remote-transaction-isolation-gate/final.md` 已把 O6 推进到 `software_proof_docker_transaction_isolation_gate`，但仍缺真实生产 DB/queue、多实例一致性、production backup/disaster recovery、真实云/4G/OSS/CDN。

`sprints/2026.05.12_24-25_phone-voice-prompt-readiness-gate/final.md` 已把 O5 推进到约 52%，并建议 Docker-only 环境下下一轮优先 O6 生产化缺口。因此本轮选择 O6 的 production backup/disaster recovery 上线前置 gate，而不是继续做 O5 phone UI 素材。

## 用户价值和产品北极星

普通手机用户不关心数据库备份、灾备演练或云端恢复策略，但他们需要在远程发车失败、云端状态丢失或服务恢复时得到可信解释：系统不能因为本地 proof 可恢复就宣称真实生产灾备完成，也不能在缺少生产备份/灾备证据时把手机状态显示成绿色 ready。

产品北极星仍是：普通用户只用手机完成垃圾交付，小车通过 4G 云中转完成控制和状态回传。本轮只把 production recovery 风险前置到 Docker/local artifact、preflight、status 和 diagnostics 的 phone-safe gate，不声明真实生产灾备、真实云、真实 4G 或真实送达完成。

## 上轮未完成项和阻塞

- production backup/disaster recovery：未证明。上一轮 transaction isolation 只覆盖并发写入下的 ACK/cursor 保守语义。
- 真实生产 DB/queue：未证明。现有 file/SQLite proof store 不能替代生产数据库或生产队列。
- 多实例一致性：未证明。本轮不做真实多实例集群，只做上线前置 recovery gate 的 Docker/local artifact。
- 真实云/HTTPS/TLS/公网入口/4G/SIM/OSS/CDN 实流量：当前主机没有外部环境，不能作为本轮验收目标。
- 真实手机设备、Nav2/fixed-route、WAVE ROVER、HIL、真实送达：均不在本轮证据范围内。

## 本轮核心抓手

新增 `trashbot.production_recovery_gate` artifact，并接入 relay preflight、operator status 和 diagnostics 的 phone-safe summary。目标是让上线前置缺口可执行、可解释、可阻断：

- artifact 记录 Docker/local backup/restore、recovery drill、state backend、queue/DB、multi-instance、retention、restore objective 等状态。
- preflight 消费 artifact 后可以显示 production recovery gate pass，但必须保持 `production_ready=false` 和 `overall_status=blocked`。
- phone-safe summary 只向手机/支持同学解释 recovery gate 状态，不暴露完整 artifact、checksum、local path、DB/queue URL、token、Authorization、OSS secret、AK/SK、root password、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER 参数或 traceback。
- ACK 仍只代表 command envelope accepted/processing/failure evidence，不等于 delivery success，也不等于灾备恢复完成。

## Owner 和责任边界

- Task A / `full-stack-software-engineer`：主实现。负责 relay artifact、CLI/preflight、operator status/diagnostics phone-safe summary、targeted tests 和产品文档同步。
- Task B / `robot-software-engineer`：compatibility fence。负责 remote bridge 兼容性验证，确认 recovery metadata 不污染 `trashbot.remote.v1` command/status/ack envelope、不触发 robot action、不 ACK、不推进或持久化 cursor；只有发现生产 `remote_bridge.py` 必须改才能保持兼容时才允许改它。
- Task C / `product-okr-owner`：实现完成后 closeout，负责 `OKR.md`、本 sprint docs 的真实收口和进度边界更新。

## 验收口径

本轮验收只接受 Docker/local software proof：

- `trashbot.production_recovery_gate` artifact schema/version/checksum 可验证。
- Artifact 和 preflight 明确 production backup/disaster recovery 仍未真实证明。
- Preflight 可消费 artifact，并输出 `production_recovery=pass` 或等价 recovery check，同时保持 `production_ready=false`、`overall_status=blocked`。
- `/api/status.phone_readiness.production_recovery` 与 `/api/diagnostics.production_recovery` 只输出 phone-safe summary。
- Robot compatibility fence 证明 metadata-only blocked response 不触发 action、不 ACK、不推进或持久化 cursor。
- 文档同步更新 `docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md` 和必要接口文档。
- 验证只做围栏：targeted unittest、`py_compile`、artifact CLI/preflight smoke、remote bridge compatibility fence、scoped `git diff --check`。

## 风险和证据缺口

- 通过本轮后，O6 只能保守增加 Docker/local production recovery gate 证据，不能声明真实生产备份或真实灾备完成。
- 如果实现把 SQLite backup/restore drill 当作 production DR 通过，必须退回修正为 blocked。
- 如果 summary 泄露完整 artifact、checksum、local path、凭证、DB/queue URL、ROS/hardware 细节，必须退回修复。
- 如果 robot fence 无法证明 metadata 不触发 action/ACK/cursor，不能进入 Product closeout。
