# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - Side-by-Side Check

## 状态

- 阶段：side2side_check
- Product Owner：`product-okr-owner`
- 收口时间：2026-05-12 20:38 CST
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`

## 用户价值和产品北极星

用户价值：当本地手机入口处于 blocked、等待 ACK、失败或需要人工接管时，普通用户能打开 Support Handoff，复制中文优先、脱敏、可追踪的求助摘要给家人、售后或工程支持，不需要解释 ROS2、串口、云凭证或硬件字段。

产品北极星：普通用户只用手机完成垃圾交付；无法继续时，手机也要把任务安全交接给人，而不是把用户推回命令行、raw diagnostics 或工程调试流程。

## PRD / Tech Plan 对照

| 验收项 | 对照结果 | 证据 |
| --- | --- | --- |
| `trashbot.phone_support_bundle.v1` schema/API 落地 | 通过 | Task A 记录 `/api/status.phone_support_bundle`、`/api/status.phone_readiness.phone_support_bundle`、`/api/diagnostics.phone_support_bundle` 共用同一生成与脱敏逻辑。 |
| 首屏 support/handoff 入口 | 通过 | Task A 记录本地 fallback HTML 新增 `Support Handoff`、脱敏摘要复制区和刷新入口。 |
| Command safety blocked 时仍可打开诊断/交接 | 通过 | Task A 记录 Start/Confirm/Cancel 被 command safety 阻断时，Support Handoff 与 Diagnostics 仍可打开。 |
| `safe_copy` 中文优先且 ACK 保守 | 通过 | Task A 记录 `safe_copy` 明确 ACK 只代表 accepted/processing evidence，不能代表送达成功。 |
| 敏感字段过滤 | 通过 | Task A 覆盖 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum、完整 artifact；Task B 进一步确认 diagnostics support bundle 不暴露 raw ROS topic、serial、baudrate、token、Authorization、DB/queue URL 或 local path。 |
| Remote bridge/robot envelope 不变 | 通过 | Task B 确认 support metadata 不污染 `trashbot.remote.v1` command/status/ack envelope；metadata-only blocked response 不触发 robot action、不 ACK、不推进或持久化 cursor。 |
| 文档同步 | 通过 | `docs/product/mobile_user_flow.md` 和 `docs/interfaces/ros_contracts.md` 路径真实存在，Task A 已记录同步 support handoff 和 interface contract。 |

## OKR 映射

- O5 / KR4：远程诊断最小数据包从技术 diagnostics 推进为 phone-safe support bundle。
- O5 / KR5：失败时用户知道该怎么求助，支持人员知道该看哪些摘要。
- O5 / KR7：本地 fallback 首屏新增可直接使用的 Support Handoff 入口，不暴露 raw JSON、ROS topic 或硬件细节。
- O6：仅复用已有 phone-safe remote/queue/ACK 摘要，不新增真实云、4G、OSS/CDN 或生产队列证据。

## KR 拆解 / 更新

- KR5.1：`trashbot.phone_support_bundle.v1` 已通过 Task A API/static tests 覆盖。
- KR5.2：`/api/status` 顶层与 `phone_readiness.phone_support_bundle` 已共用同一 support bundle 口径。
- KR5.3：`/api/diagnostics.phone_support_bundle` 已接入，Task B 将 skip 清零并验证脱敏。
- KR5.4：Support Handoff 在 command safety blocked 时仍可打开。
- KR5.5：敏感字段过滤通过 Task A/B 双围栏验证。
- KR5.6：ACK 继续保持 accepted/processing evidence only，不等于 delivery success。

## 本轮核心抓手

把 O5 从“首屏任务步骤可读”推进到“失败后可安全交接”：support bundle 把状态、失败摘要、下一步、ACK 语义、未证明能力和脱敏引用收敛成用户可复制的中文 handoff package。

## 优先级和验收口径

- P0：schema/API/diagnostics/首屏入口、字段脱敏、ACK/not_proven 口径正确。结果：通过。
- P1：UI copy 覆盖 blocked、manual takeover、waiting ACK、support required 等支持场景。结果：通过 Task A 文档和静态/HTTP 测试记录。
- P2：`bundle_id` 本地可追踪但不依赖真实云或生产账号。结果：通过 software proof 口径收口。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A 已完成 API、HTML、测试和 docs 同步。
- `robot-software-engineer`：Task B 已完成 remote bridge / diagnostics compatibility fence。
- `product-okr-owner`：本文件、`final.md` 和 `OKR.md` 保守收口。

## 明确未证明范围

本轮没有真实手机设备、production app、真实云/4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达；不能把 local/Docker phone support handoff software proof 写成真实用户验收、生产售后系统、真实云链路或机器人实机能力。

## 风险、阻塞和需要补齐的证据链

- 真实手机 Safari/Chrome、physical phone service worker runtime 和普通用户实机验收仍缺。
- Support Handoff 仍是本地 fallback/operator gateway 能力，不是 production app 或正式售后系统。
- 真实云/4G、OSS/CDN 实流量、生产 DB/queue 和远程手机流程仍归 O6 后续验证。
- Nav2/fixed-route、WAVE ROVER、HIL 和真实送达仍未解锁，O1/O2/O3 不能因本轮提升。

## 需要创建或更新的 sprint 文档

- 已创建：`side2side_check.md`
- 已创建：`final.md`
- 已由 Task A/B 更新：`tech-done.md`
- 已由 Product Closeout 更新：`OKR.md`
