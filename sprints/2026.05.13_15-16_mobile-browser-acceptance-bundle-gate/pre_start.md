# Sprint 2026.05.13_15-16 Mobile Browser Acceptance Bundle Gate - Pre Start

## Sprint 声明

- sprint_type: epic
- 主目标：Objective 4 手机用户体验与低成本量产边界。
- 证据边界：`software_proof_docker_mobile_browser_acceptance_bundle_gate`。
- 当前主机约束：macOS + Docker-only；没有真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达证据。

## 启动依据

1. `OKR.md` 4.1 显示 Objective 4 约 66%，Objective 5 约 67%，Objective 4 是当前最低完成度 Objective。
2. `OKR.md` 第 6 节写明下一轮应优先 Objective 4 的真实手机设备/browser、production app 或 PWA install prompt 验收；如果继续 Objective 5，必须引入真实外部证据，避免继续增加本地 metadata 深度。
3. `sprints/2026.05.13_13-14_mobile-device-acceptance-readiness-gate/final.md` 已完成 `software_proof_docker_mobile_device_acceptance_readiness_gate`，但仍缺真实手机设备/browser、production app 和真实 PWA install prompt。
4. `sprints/2026.05.13_14-15_oss-cdn-live-probe-gate/final.md` 收口后 Objective 5 上调到约 67%，并明确下一轮建议回到 Objective 4；该轮还证明继续补 O5 本地 metadata 已不是当前最低优先级。
5. `docs/product/mobile_user_flow.md` 已有 mobile web entrypoint、PWA shell、device acceptance readiness、operation log、action feedback 和 support bundle 口径；下一步需要把这些 phone-safe 状态组织成可交接的浏览器验收包，而不是再增加一个孤立 readiness 字段。

## 用户价值和产品北极星

北极星：普通用户只用手机完成垃圾交付，并且在失败或未验收时能把安全、脱敏、可复现的材料交给售后或工程支持。

本轮用户价值是让用户或测试者在没有真实设备验收条件时，也能从手机首屏生成一份“浏览器验收包/验收证据”摘要：它说明 viewport、touch、PWA/offline、diagnostics、cloud gate、action fail-closed、ACK 语义和 client timestamp 的当前状态，同时明确哪些能力仍未证明。

## 本轮核心抓手

把“真实手机设备/browser 验收缺口”推进成一个 phone-safe acceptance bundle：

- Full-stack 在 mobile web 首屏生成和显示验收包，支持复制为售后/验收交接材料。
- Robot 侧证明 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle` 只是 metadata，不会触发 robot action、ACK 或 cursor 推进。
- Product Closeout 只在 A/B 都完成并验证通过后，保守更新 Objective 4；证据边界必须停在 Docker/local software proof。

## 需要做什么

1. 在 mobile web 中增加“浏览器验收包/验收证据”能力，聚合 phone-safe readiness、command safety、diagnostics/support、cloud gate、offline/PWA 和 action feedback 摘要。
2. 保持 Start Delivery、Confirm Dropoff、Cancel fail closed；Diagnostics 和 Support Handoff 继续可用。
3. 在 robot remote bridge/protocol 测试中加入 metadata-only compatibility fence，防止验收包字段被误读为 command/status/ACK envelope。
4. 待工程任务完成后由 Product closeout 更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和进度日志。

## Team 和 Owner

- Task A：`full-stack-software-engineer`，负责手机首屏 acceptance bundle、fixture、静态 smoke 和产品文档同步。
- Task B：`robot-software-engineer`，负责 remote bridge/protocol metadata-only fence 和接口文档同步。
- Task C：`product-okr-owner`，负责 A/B 证据验收、sprint closeout、OKR 和进度日志更新。

## 优先级和验收口径

- P0：手机首屏能生成并显示 phone-safe acceptance bundle，覆盖 viewport、touch、PWA/offline、diagnostics、cloud、action fail-closed、ACK 语义和 client timestamp。
- P0：验收包可复制/显示为支持交接材料，且不得包含 tokens、ROS topics、serial、`/cmd_vel` 或完整 artifact。
- P0：Start/Confirm/Cancel 在无真实设备、production app 或 safe-to-control 证据时 fail closed；Diagnostics/Support 可用。
- P0：Robot metadata-only fence 证明验收包字段不触发 collect/dropoff/cancel、不 POST ACK、不推进或持久化 cursor。
- P1：文档明确本轮只形成 `software_proof_docker_mobile_browser_acceptance_bundle_gate`，不把 ACK、metadata 或 Docker/local browser proof 写成真实送达或真实设备验收。

## 风险、阻塞和证据链缺口

- 当前没有真实手机设备/browser、production app 或真实 PWA install prompt，本轮不能补齐真实用户设备验收。
- 当前没有真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达，本轮不得更新这些目标的证据边界。
- ACK 只能表示 accepted/processing evidence，不是 delivery success。
- metadata 只能作为 phone/support/readiness 材料，不得触发 robot action。

## 需要创建或更新的 sprint 文档

- 本轮启动创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Task A/B 完成后由 Task C 创建或更新：`tech-done.md`、`side2side_check.md`、`final.md`。
