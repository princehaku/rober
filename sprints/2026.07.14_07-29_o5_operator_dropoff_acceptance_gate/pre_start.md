# Pre Start - O5 Operator Dropoff Acceptance Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/`
- Start time: 2026-07-14 07:29 CST
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned artifact schema: `trashbot.o5.operator_dropoff_acceptance_gate.v1`
- Planned proof boundary: `software_proof_o5_operator_dropoff_acceptance_gate_only`
- Planned current-run live claim: none

## User Value And Product North Star

用户价值是让普通手机用户或现场 operator 的"我已完成投放/取走垃圾"动作成为可审计的送达证据入口，但不会被单独误认为真实 delivery success。产品北极星仍是低成本 ROS2 垃圾投递机器人：用户放入垃圾，小车沿固定路线到达投放点，operator/user 完成 dropoff acceptance，手机和云端都能复盘同一任务的真实送达闭环。

本轮只做计划，不做代码或测试。本 sprint 要把 O5 的下一步从 terminal/result wrapper 转到更接近 Mission Objective 0 的 `operator_dropoff_acceptance` evidence intake/gate：它是用户动作证据收件门，不是送达成功声明。

## Context From Recent Closeouts

O5 仍是当前最低 Objective，约 `85%`。O1 约 `94%`，O6/O7 约 `93%`。

最近三个 O5/O6/O7 closeout 已明确禁止继续重复这些 support-only blocker：

- terminal-result bridge / reconciliation / live-success-gate。
- readiness packet、cloud external review-decision、CDN/TLS 4xx。
- O6/O7 readback、voice draft、export、intake wrapper。

最新 O5 live-success gate 已把 delivery success 的总条件写清，但它仍是 synthetic/current-live-shaped 合同证明，收口为 `blocked_missing_live_success_evidence`。本轮不再重复 live-success gate 本身，而是规划 operator/user-action 证据入口：后续 Engineer 只应实现一个 fail-closed `operator_dropoff_acceptance` intake/gate，让它能被 live-success gate 消费。

## Direction Decision

- 方向判断：继续 O5，但调整抓手。
- 调整原因：O5 仍是最低 Objective；真实生产云、真实手机/browser、真实 route execution、HIL pass 和 safe-to-control 当前不可用，重复做 terminal/result、readiness、CDN/TLS 或 O6/O7 wrapper 不会增加 Mission Objective 0。
- 本轮抓手：Robot Software 单 owner，设计 operator/user-action dropoff acceptance evidence gate。
- OKR 预期：计划阶段不调整百分比；后续实现若只使用 synthetic/mock fixture，也只能接受为 fail-closed software proof，O5 保持约 `85%`，KR 不归档。

## Scope

后续工程实现应提供一个 O5 operator dropoff acceptance gate，最小合同如下：

- 接收 `operator_dropoff_acceptance` 证据摘要，绑定同一 `task_id`、`robot_id`、terminal result identity 与 route/packet identity。
- 支持 `source_mode=live` 与 synthetic/mock fixture 的明确区分。
- synthetic/mock fixture 允许证明字段、脱敏、same-task 校验和 fail-closed 行为，但必须输出 `delivery_success=false`。
- 缺少 live route execution success、同 task terminal result recorded、HIL pass、safe_to_control 或 live source 时，必须输出 `acceptance_decision=blocked_missing_live_success_evidence` 或等价 fail-closed 状态。
- 只有 `source_mode=live`、同 task terminal result recorded、live route execution success、`operator_dropoff_acceptance`、HIL pass、safe_to_control 全齐时，才允许后续 live-success gate 接受 delivery success。

## Out Of Scope

- 不执行真实硬件控制。
- 不调用 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。
- 不采集真实 HIL、真实 route execution、真实 production cloud、真实 4G/SIM 或真实 phone/browser。
- 不修改 `OKR.md`、`docs/process/okr_progress_log.md`、产品代码、测试代码或历史 sprint。
- 不创建 `tech-done.md`、`side2side_check.md` 或 `final.md`，直到 Engineer 完成后续实现与验证。

## Owner And Routing

- 主责 Engineer：`robot-software-engineer`
- 协作判断：单 owner epic。状态机/证据 gate、CLI、测试和 docs/product 同步都属于 Robot Software 主链路；Hardware、Algorithm、Full-stack 本轮不并行实现。
- 后续执行入口：主节点在计划验收后，按 AGENTS.md 把 `tech-plan.md` 中的文件范围和验收命令派给 `robot-software-engineer` 单线闭环。

## Risks And Evidence Gaps

- operator/user 手动确认可能被误读为真实投放完成；因此必须和 route execution、terminal result、HIL、safe-to-control 同时校验。
- synthetic/mock fixture 可能被误读为现场用户动作；因此必须固定 `delivery_success=false`、`source_mode!=live` 和 `blocked_missing_live_success_evidence`。
- 本轮没有真实 production cloud、真实 4G/SIM、真实 route execution、真实 HIL、真实 safe-to-control 或真实 phone/browser 证据。

## Required Sprint Documents

本计划阶段只创建：

- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/pre_start.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/prd.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/tech-plan.md`

Engineer 完成实现后再创建：

- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/tech-done.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/side2side_check.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/final.md`
