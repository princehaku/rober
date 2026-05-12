# Sprint 2026.05.12_22-23 Phone Support Bundle Gate - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主线 Objective：O5 手机体验与量产边界
- Evidence boundary：`software_proof_docker_phone_support_bundle_gate`

## 问题

O5 已有本地/Docker phone readiness、browser command-safety、PWA shell 和 task-flow readiness。普通用户在 happy path 上能看到连接、目的地、装载确认、发车、状态解释和诊断入口。

剩余缺口是失败后交接：用户仍可能不知道应该给家人、售后或工程支持看什么；支持人员也需要一个稳定、可复制、脱敏、可追溯的 handoff package，而不是让用户截图 raw diagnostics 或解释 ROS2/硬件字段。

## 用户价值和产品北极星

用户价值：失败时，手机首屏能生成“求助交接包”，用普通中文解释当前状态、失败原因、下一步、ACK 语义、未证明能力和支持摘要。用户不需要 SSH、ROS2、串口、云凭证或硬件知识。

北极星：普通用户只用手机完成垃圾交付；当无法继续时，手机也能把任务安全交接给人，而不是把用户推回工程调试流程。

## OKR 映射

- O5 / KR4：远程诊断最小数据包从 diagnostics 技术包推进到 phone-safe support bundle。
- O5 / KR5：失败时用户知道该怎么做，支持人员知道该看哪些摘要。
- O5 / KR7：首屏新增可直接使用的求助/交接入口，不暴露 raw JSON 或 ROS topic。
- O6 / KR6：只复用已有 remote/queue/artifact phone-safe 摘要，不新增或提升 O6 真实云证据。

## KR 拆解

- KR5.1：新增 `trashbot.phone_support_bundle.v1` schema，包含 `bundle_id`、`generated_at`、`evidence_boundary`、`status_summary`、`failure_summary`、`next_steps`、`ack_semantics`、`support_level`、`safe_copy`、`support_refs`、`not_proven`。
- KR5.2：`/api/status` 顶层与 `phone_readiness.phone_support_bundle` 暴露同一 support bundle summary；旧客户端可忽略。
- KR5.3：`/api/diagnostics.phone_support_bundle` 暴露同一 bundle，方便支持人员从 diagnostics 获取交接口径。
- KR5.4：本地 fallback 首屏新增 support/handoff 入口；Start/Confirm/Cancel blocked 时仍允许打开/复制 support bundle。
- KR5.5：敏感字段过滤：不得暴露 token、Authorization、OSS AK/SK、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback 或完整 artifact。
- KR5.6：ACK 文案保持保守：accepted/processing evidence only，不等于 delivery success。

## 范围

### In Scope

- 本地 `operator_gateway` API 和静态 fallback 页面。
- 复用已有 `/api/status`、`/api/diagnostics`、`phone_readiness`、`command_safety`、remote readiness、queue ordering drill 和 ACK 语义。
- 更新 `docs/product/mobile_user_flow.md`、`docs/interfaces/ros_contracts.md` 中 support bundle contract。
- 最小围栏测试、`py_compile` 和 scoped diff check。

### Out of Scope

- 真实 production app 或 native app。
- 真实手机设备 Safari/Chrome 验收。
- 真实云、真实 4G/SIM、HTTPS/TLS 公网入口、真实 OSS/CDN 流量。
- 生产 DB/queue、多实例一致性、真实 production queue ordering。
- Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、HIL 或真实送达。
- 新硬件、硬件参数、WAVE ROVER 协议改动。

## 优先级

- P0：support bundle schema/API/diagnostics 首屏入口落地，字段脱敏，ACK/not_proven 口径正确。
- P1：UI copy 能覆盖 `ready`、`blocked`、`manual_takeover_required`、`remote_waiting_ack`、`support_required` 等常见状态。
- P2：支持 bundle `bundle_id` 稳定可追踪，但不能依赖真实云或生产账号。

## 验收口径

本轮可接受的完成证据：

- API 返回 `trashbot.phone_support_bundle.v1`，并在 `/api/status`、`phone_readiness`、`/api/diagnostics` 三处保持一致。
- 首屏有 phone-safe support/handoff 入口；主操作 blocked 时仍可打开 diagnostics/support bundle。
- 测试覆盖敏感字段过滤、ACK 不是送达成功、metadata 不触发 robot action、不污染 `trashbot.remote.v1` command/status/ack envelope。
- 文档同步更新 product/interface contract。
- Sprint closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`；若证据成立，`OKR.md` 只能保守记录 O5 software proof 进展。

## 责任 Engineer

- `full-stack-software-engineer`：Task A 主实现，负责 API、HTML、测试和产品/interface 文档。
- `robot-software-engineer`：Task B robot compatibility fence，负责 remote bridge / command envelope / ACK / cursor/action 不变性验证。
- `product-okr-owner`：Product closeout，负责 side2side、final、OKR 保守更新和证据边界核对。

## 风险和需要补齐的证据链

- support bundle 可能被误写成真实售后系统或生产 app；closeout 必须明确它只是 local/Docker software proof。
- diagnostics 里有 local path 或 artifact 细节；Task A 必须只暴露 phone-safe refs 和摘要。
- ACK 文案容易被误读为任务成功；Task B 必须验证 ACK 仍只是 command envelope evidence。
- 当前没有真实手机设备，不能补 O5 最关键的实机用户验收；本轮只能降低失败交接成本。

