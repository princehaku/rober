# Pre Start - O5 Delivery State Live Success Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/`
- Start time: 2026-07-14 05:28 CST
- Product owner: `product-okr-owner`
- Implementation owner: `Robot Software`
- Planned artifact schema: `trashbot.o5.delivery_state_live_success_gate.v1`
- Planned proof boundary: `software_proof_o5_delivery_state_live_success_gate_only`
- Planned current-run live claim: none

## User Value And Product North Star

用户价值是让普通手机用户看到的"送达成功"只在机器人真的完成同一任务的现场送达闭环后才成立。产品北极星仍是低成本 ROS2 垃圾投递机器人：用户放入垃圾，小车沿固定路线出发，到达投放点，完成 dropoff/operator acceptance，并能被手机/云端可靠复盘。

本轮不做新的外部证据 wrapper，也不把 synthetic fixture 包装成真实交付。它只给 `DeliveryStateMachine` 增加一个 live success gate 合同：未来真实输入到来时，状态机必须同时看到 live route execution、operator/dropoff acceptance、HIL pass、safe-to-control、same-task identity、terminal result record 等证据，才允许接受 delivery success。

## Context From Recent Closeouts

O5 仍是当前最低 Objective，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。

最近 closeout 已明确不能继续重复以下 support-only 路径：

- O5 CDN/TLS `4xx` probe。
- cloud production readiness packet / external review-decision。
- bounded route terminal-result bridge。
- terminal-result intake/export。
- mission bundle export。
- delivery state terminal reconciliation。
- O6/O7 readback、intake、export wrapper。

最新 sprint `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/` 已让 `DeliveryStateMachine` 对 `mock_route_execution_completed_not_live_delivery` fail closed，输出 `delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`。本轮的差异是补上"未来什么条件才可接受 success"的正向合同，而不是再次解释 mock terminal result。

## Direction Decision

- 方向判断：继续 O5，但调整抓手。
- 调整原因：O5 仍是最低 Objective；真实生产云、真实手机/browser、真实 live route execution、真实 HIL 和真实 operator/dropoff evidence 当前不可用，继续做外部证据 wrapper 会重复消费同类 blocker。
- 本轮抓手：Robot Software 单 owner，建立 `delivery_state_live_success_gate` 状态机合同。
- OKR 预期：本轮最多接受为 O5 software contract readiness；没有真实 live evidence 时主百分比保持 flat，KR 不归档。

## Scope

本轮计划的工程实现应让 `DeliveryStateMachine` 在 success path 上 fail closed：

- synthetic/current-live-shaped fixture 可以证明合同字段、验收断言和 negative cases 存在。
- synthetic fixture 必须输出 `live_success_gate_contract_ready=true`，但同时输出 `current_live_evidence_observed=false`、`delivery_success_claimed_by_this_run=false`、`real_world_delivery_proven=false`、`safe_to_control=false`、`hil_pass=false`。
- 只有 source 处于真实/live 模式，且完整证据同时满足，才允许 `delivery_success_accepted_for_state_machine=true`。
- 本轮不得声称真实 delivery、HIL、safe-to-control、production cloud、real phone/browser、route execution 或 WAVE ROVER control 已完成。

## Out Of Scope

- 不执行真实硬件控制。
- 不调用 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。
- 不采集真实手机/browser、真实云、真实 4G、真实 HIL 或真实 live route execution。
- 不修改 `OKR.md`、`docs/process/okr_progress_log.md` 或既有 sprint closeout。
- 不创建 `tech-done.md`、`side2side_check.md` 或 `final.md`，直到 Engineer 完成实现与验证。

## Owner And Routing

- 主责 Engineer：`Robot Software`
- 协作判断：单 owner epic。状态机、CLI、测试和产品文档同步都在 Robot Software 主链路内；Hardware、Algorithm、Full-stack 本轮不需要并行实现。
- 后续执行入口：主节点在计划验收后，按 AGENTS.md 把 `tech-plan.md` 中的文件范围和验收命令派给 `robot-software-engineer` 单线闭环。

## Risks And Evidence Gaps

- 真实 live route execution 未观察。
- operator/dropoff acceptance 未观察。
- HIL pass 未观察。
- `safe_to_control=true` 未证明。
- production cloud / 4G / real phone/browser 未证明。
- synthetic fixture 可能被误读为真实成功；因此 artifact 必须保留 `proof_boundary=software_proof_o5_delivery_state_live_success_gate_only` 和固定 false 字段。

## Required Sprint Documents

本计划阶段只创建：

- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/pre_start.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/prd.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/tech-plan.md`

Engineer 完成实现后再创建：

- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/tech-done.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/side2side_check.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/final.md`
