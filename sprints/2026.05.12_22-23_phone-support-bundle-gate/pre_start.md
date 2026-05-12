# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 22:00 Asia/Shanghai
- Automation：`skill-progression-map`
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- 目标 evidence boundary：`software_proof_docker_phone_support_bundle_gate`
- 当前主机约束：macOS + Docker-only；无真实手机设备、无真实云/4G、无真实 WAVE ROVER/HIL。

## 开工依据

- `OKR.md` 当前低完成度排序里 O5 约 48%、O6 约 49%，O1/O2/O3/O4 高于 O5/O6。
- `sprints/2026.05.12_20-21_phone-task-flow-readiness-gate/final.md` 已完成 local/Docker phone task-flow readiness，但剩余缺口是无真实手机设备、无 production app、无普通用户实机验收。
- `sprints/2026.05.12_21-22_remote-queue-ordering-drill/final.md` 已完成 Docker/local queue ordering drill，并建议 Docker-only 环境下一轮优先回到 O5 的手机侧可交付。
- 本机没有真实硬件，不能把本轮做成真实 HIL、真实送达、真实手机设备验收或生产云验收。

## 用户价值和产品北极星

本轮面向普通手机用户的失败后求助体验：当小车或远程链路不能继续时，用户能在手机首屏生成一个可交给售后、家人或工程支持的 support bundle / handoff package，而不是截图 raw JSON、解释 ROS topic、暴露串口或凭证。

这服务于北极星：普通用户只用手机交付垃圾，并在失败时知道下一步该找谁、提供什么证据、哪些能力仍未证明。

## OKR 映射

- O5 / KR4：建立远程诊断最小数据包。本轮把软件版本、地图/路线版本、最近任务状态、失败原因、关键日志引用、诊断摘要和 not_proven 边界组织成 phone-safe support bundle。
- O5 / KR5：普通用户不接触命令行、不理解 ROS2，也能在失败时知道该怎么做。本轮把求助入口从 diagnostics 原始入口前移到首屏 handoff package。
- O5 / KR7：手机端 UI 可直接使用。本轮要求首屏存在 support/handoff 入口，文案中文优先，按钮状态清晰，诊断仍可访问。
- O6：只消费已有 remote readiness、queue ordering drill、ACK 文案和 diagnostics 摘要，不新增云后端能力，不提升真实云或 4G 证据。

## 本轮核心抓手

创建 `trashbot.phone_support_bundle.v1` software proof：

- 从 `/api/status`、`/api/diagnostics`、`phone_readiness`、`command_safety`、ACK 文案和 O6 phone-safe 摘要中抽取 support bundle。
- 在 `/api/status` 顶层、`phone_readiness.phone_support_bundle` 和 `/api/diagnostics.phone_support_bundle` 暴露同一 phone-safe summary。
- 在本地 fallback 首屏加入“求助/交接包”入口，展示可复制给支持人员的普通用户摘要。
- 明确过滤 raw ROS topic、串口、baudrate、WAVE ROVER 参数、token、Authorization、OSS AK/SK、DB/queue URL、local path、traceback 和完整 artifact。

## 阻塞和边界

- 本轮不能证明 production app、真实 iPhone/Android 设备、真实手机浏览器 service worker、普通用户实机验收。
- 本轮不能证明真实云、真实 4G/SIM、HTTPS/TLS 公网入口、真实 OSS/CDN 流量、生产 DB/queue 或生产 queue ordering。
- 本轮不能证明 Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、HIL 或真实垃圾送达。
- ACK 仍只表示 command accepted/processing evidence，不表示送达成功。

## Owner

- Task A 主实现：`full-stack-software-engineer`
- Task B robot compatibility fence：`robot-software-engineer`
- Product closeout：`product-okr-owner`

## Sprint 文档计划

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实现完成后再由对应 owner 更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

