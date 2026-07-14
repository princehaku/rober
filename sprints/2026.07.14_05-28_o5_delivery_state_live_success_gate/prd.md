# PRD - O5 Delivery State Live Success Gate

## Product Problem

当前系统已经能把 mock terminal result 解释为 fail closed，但还缺少一个严格的 live success evidence gate。没有这个合同，未来接入真实 route execution、operator acceptance、HIL 或 cloud terminal result 时，状态机可能因为字段命名或来源混淆，把不完整证据误接受为 delivery success。

本轮 PRD 要求：`DeliveryStateMachine` 必须只有在完整 live evidence 同时满足时才接受 delivery success；在当前无硬件、无真实云、无真实手机/browser、无真实 route execution 的环境中，只能产出 synthetic/current-live-shaped 软件证明。

## User Value And North Star

用户价值：手机端看到的"已送达"必须代表真实机器人完成送达闭环，而不是 mock replay、readback、terminal-result wrapper 或人工填写的孤立成功字段。

产品北极星：低成本 ROS2 自主垃圾投递机器人具备可验证的送达成功语义，交付状态可被手机、云端和后续运营工具一致消费，并且错误证据默认拒绝。

## OKR Mapping And Direction

- Objective：O5。
- Current progress：约 `85%`。
- Direction：继续 O5，但从 support-only wrapper 转向状态机 live success gate 合同。
- Why now：最近 O5/O6/O7 已多次完成 wrapper、intake、export、reconciliation，但都没有真实 route execution、operator/dropoff acceptance、HIL pass 或 safe-to-control。本轮必须把下一个 O5 success 的准入条件固化到主状态机。
- Expected OKR effect：计划阶段不调整百分比；实现完成后也只有 software contract readiness，除非采到真实 live evidence，否则不归档 KR。

## KR Handling

- 当前 KR 更新：不在本计划阶段更新 `OKR.md`。
- 历史归档：本轮无已完成 KR，暂不归档。
- 证据位置：后续若完成实现，只能把 `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/artifacts/delivery_state_live_success_gate_summary.json` 作为 software proof artifact；不能作为真实 delivery 成功证据。
- 剩余风险：真实 production cloud、真实 phone/browser、真实 live route execution、operator acceptance、HIL 和 safe-to-control 仍需后续现场证据。

## Product Requirements

### P0 - Live Success Gate Contract

`DeliveryStateMachine` 必须提供 `delivery_state_live_success_gate` 或等价接口，输出 schema：

- `schema=trashbot.o5.delivery_state_live_success_gate.v1`
- `proof_boundary=software_proof_o5_delivery_state_live_success_gate_only`
- `live_success_gate_contract_ready=true`

### P0 - Required Evidence For Accepting Success

只有同时满足以下条件时，未来真实输入才可以使 `delivery_success_accepted_for_state_machine=true`：

- source mode 是真实/live，不是 synthetic、mock、local replay、historical-only、readback-only 或 wrapper-only。
- same-task identity 通过：`task_id`、`robot_id`、route/packet identity、terminal result identity 不漂移。
- live route execution 已完整记录并成功结束。
- operator/dropoff acceptance 已记录，且属于同一 task。
- HIL pass 已记录，且属于同一 task / same evidence window。
- `safe_to_control=true` 已由真实安全门证据支撑。
- terminal result record 存在，且 result source 与 state machine 输入一致。
- 无 dangerous true fields、stale evidence、cross-task evidence 或 unsafe source drift。

### P0 - Current Run Boundary

当前无真实硬件、真实云、真实手机/browser、真实 live route execution，因此本轮 synthetic/current-live-shaped artifact 必须固定：

- `current_live_evidence_observed=false`
- `delivery_success_claimed_by_this_run=false`
- `real_world_delivery_proven=false`
- `safe_to_control=false`
- `hil_pass=false`
- `delivery_success_accepted_for_state_machine=false`

### P0 - Negative Fixtures

Robot Software 必须覆盖 fail-closed negative fixtures：

- 缺 live route execution。
- 缺 operator/dropoff acceptance。
- 缺 HIL pass。
- 缺 safe-to-control。
- same-task identity mismatch。
- terminal result record missing。
- source mode 是 synthetic/mock/readback-only 但携带 success-like 字段。
- stale or historical evidence。
- dangerous true fields in unsafe source。

### P1 - Product Documentation Sync

实现完成时，Robot Software 必须同步更新：

- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

文档必须说明：本合同只定义 live success 准入门槛；当前 artifact 是 `software_proof_o5_delivery_state_live_success_gate_only`，不等于真实 delivery、HIL、safe-to-control、production cloud 或真实 phone/browser。

## Acceptance Criteria

计划验收：

- 三个计划文档存在，且仅限 `pre_start.md`、`prd.md`、`tech-plan.md`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`。
- 文档中明确 owner 是 `Robot Software`。
- 文档中出现 `delivery_state_live_success_gate` 和 `software_proof_o5_delivery_state_live_success_gate_only`。

工程验收：

- `DeliveryStateMachine` 只有在真实/live source 和完整证据同时满足时才接受 success。
- synthetic/current-live-shaped fixture 生成 summary，但不 claim delivery。
- summary 通过 JSON schema/field assertions。
- negative fixtures 全部 fail closed。
- docs/product 同步更新。

## Priority And Owner

- Priority：P0 for state-machine gate and fail-closed acceptance tests; P1 for product docs sync.
- Responsible Engineer：`Robot Software`
- Product acceptance：`product-okr-owner` 在后续 closeout 阶段只接受 software proof boundary，不允许把 synthetic fixture 写成真实交付。

## Risks

- 最大风险是 success-like synthetic fixture 被后续消费方误读。因此验收必须固定 `delivery_success_claimed_by_this_run=false` 和 `real_world_delivery_proven=false`。
- 第二风险是把状态机合同当 OKR 增量。没有真实/live evidence 时，O5 应保持约 `85%`。
- 第三风险是遗漏 docs/product 同步，导致手机/云端产品语义仍把 terminal result 与 real delivery 混在一起。

## Sprint Documents

本计划阶段创建或更新：

- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/pre_start.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/prd.md`
- `sprints/2026.07.14_05-28_o5_delivery_state_live_success_gate/tech-plan.md`

后续实现阶段再创建 closeout 文档。
