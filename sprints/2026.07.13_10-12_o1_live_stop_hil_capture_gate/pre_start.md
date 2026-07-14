# Pre Start - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Planned start: 2026-07-13 10:12 CST
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Status: Product plan ready; implementation not started
- Proof boundary planned: `software_proof_o1_live_stop_hil_capture_gate_mock_only`

## 用户价值和产品北极星

产品北极星仍是普通用户把垃圾交给小车后，小车能沿固定路线安全送达，并且任何时候都能被可靠停下。本轮用户价值不是让车动起来，而是把下一次现场执行前最关键的停车 HIL 采集入口做成可复验、可 fail-closed 的 gate：只有 explicit operator approval 后，才允许采集 current live `/api/base/stop`、同窗口 UART zero-stop frame、stop 后 `T=1001` L/R 归零和 HIL acceptance。

当前 automation run 没有现场 operator approval，因此本轮计划只允许工程实现 mock/local capture pipeline readiness，不触发硬件、不打开 WAVE ROVER UART、不发运动命令。

## 当前证据和上轮未完成项

- `OKR.md` 当前显示 O5 约 `85%`，是数字最低 Objective；主要缺口是真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser。
- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/final.md` 已把 O5 production readiness packet 收口为 support-only，固定 `okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence`、`production_ready=false`。在没有真实外部条件时继续做 O5 wrapper 只会重复消费同一 blocker。
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/final.md` 已证明 no-motion current stop path readiness：`schema=trashbot.o1.current_stop_path_readiness.v1`、`stop_endpoint=/api/base/stop`、zero-stop command plan 覆盖 `T=1`、`T=11`、`T=13`，并固定 `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`、`uses_real_uart=false`。
- 09:11 sprint 的下一步明确要求 `rober-hardware-engineer` 在 explicit operator approval 后采 current live `/api/base/stop` 调用、UART zero-stop frame capture、stop 后 `T=1001` L/R 归零和 HIL acceptance。

## 本轮方向判断

- O5：本轮暂停继续包装 support-only readiness。方向不是放弃 O5，而是在缺真实公网/4G/production/browser 条件时停止新增 support-only wrapper，等真实外部证据到位后再恢复。
- O1：继续。虽然 O1 已约 `94%`，但它的当前 live HIL 和 safe-to-control 缺口直接挡住后续 route execution；本轮转向 O1 的 operator-gated live stop HIL capture gate，是当前 automation run 里可软件推进的最低风险执行链。
- O3：保持等待真实 stop HIL / safety gate；在没有 HIL 和同窗口 LiDAR/localization/TF readiness 前，不推进 route execution。
- O6/O7：不做 readback-only 或 UI wrapper。
- KR 归档：本轮计划阶段不归档 KR，不更新 `OKR.md`；Product closeout 后再根据实际 artifact 判断是否仅留 support-only 记录。

## 本轮核心抓手

核心抓手是新增 operator-gated live stop HIL capture helper 的工程计划：先用 local mock HTTP stop endpoint 和 `T=1001` feedback fixture 验证 capture pipeline、artifact schema、字段 fail-closed 和验收命令。它只能证明下一次现场 current live stop HIL 采集入口准备好，不证明 current live HIL。

## 当前 automation 安全围栏

本轮没有 explicit operator approval，必须固定以下限制：

- 不实际触发硬件。
- 不调用 `/api/base/manual`。
- 不发布 `/cmd_vel`。
- 不 NavigateToPose。
- 不打开 WAVE ROVER UART。
- 不发送非零运动命令。
- Artifact 必须固定 `hil_pass=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`、`uses_real_uart=false`。

## 责任 Engineer 和协作方式

- 主责 Engineer：`rober-hardware-engineer`。
- 协作模式：单 owner 闭环；Product 只负责计划、验收口径和后续收口，不直接实现硬件 helper 或测试。
- Vendor 资料要求：真实硬件集成前，Hardware 必须再次读取 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER 本地资料，并在实现或 `tech-done.md` 中写明采用来源。Mock/local 阶段可复用模拟控制与反馈协议，但不能把 mock 结果写成真实 UART/HIL。

## 需要创建或更新的 sprint 文档

本 Product plan 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

不得预生成：

- `side2side_check.md`
- `final.md`

后续 Hardware implementation 完成后，必须更新本 sprint 的 `tech-done.md`；Product acceptance 才能补 `side2side_check.md` 和 `final.md`。
