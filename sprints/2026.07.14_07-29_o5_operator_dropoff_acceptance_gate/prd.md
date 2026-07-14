# PRD - O5 Operator Dropoff Acceptance Gate

## Product Problem

当前 O5 已有 terminal result、delivery-state reconciliation 和 live-success gate 合同，但还缺一个独立的 operator/user-action evidence intake：现场 operator 确认"垃圾已投放/已取走"时，系统需要能记录这条动作证据，同时严格阻止它单独升级为真实 delivery success。

本轮 PRD 要求规划 `operator_dropoff_acceptance` gate。它是 live-success gate 的一个必要输入，不是充分条件。当前无真实硬件、真实云、真实手机/browser、真实 route execution 或 HIL 时，只允许 synthetic/mock fixture 证明 fail-closed 合同。

## User Value And North Star

用户价值：普通用户看到"已送达"时，背后必须同时有机器人到达、终态结果、现场 dropoff acceptance、HIL 和安全证据，而不是只靠一条 operator 文本或按钮点击。

产品北极星：rober 成为一台可验证地可靠投递垃圾的小车，送达成功语义由同一任务的 route execution、operator/user action、terminal result、HIL 和 safe-to-control 共同支撑。

## OKR Mapping And Direction

- Objective：O5。
- Current progress：约 `85%`，当前最低。
- Direction：继续 O5，但从 support-only terminal/result/readiness wrapper 转向 operator/user-action evidence gate。
- Why now：最近 closeout 已禁止继续重复 terminal-result bridge/reconciliation/live-success-gate、readiness packet、CDN/TLS 4xx、O6/O7 readback/voice draft wrapper。本轮应规划一个更接近 Mission Objective 0 的动作证据入口。
- Expected OKR effect：计划阶段不调整百分比；后续实现若无真实 live evidence，也只能算 `software_proof_o5_operator_dropoff_acceptance_gate_only`，不归档 KR。

## KR Handling

- 当前 KR 更新：本计划阶段不修改 `OKR.md`。
- 历史归档：本轮无已完成 KR，暂不归档。
- 证据位置：后续实现若完成，artifact 可放在 `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/artifacts/operator_dropoff_acceptance_gate_summary.json`。
- 剩余风险：真实 production cloud、真实 phone/browser、真实 live route execution、operator/dropoff live evidence、HIL 和 safe-to-control 仍需后续现场证据。

## Product Requirements

### P0 - Operator/User-Action Intake Contract

后续实现必须提供 `operator_dropoff_acceptance` evidence gate，输出 schema：

- `schema=trashbot.o5.operator_dropoff_acceptance_gate.v1`
- `proof_boundary=software_proof_o5_operator_dropoff_acceptance_gate_only`
- `operator_dropoff_acceptance_gate_ready=true`

该 gate 必须记录 operator/user action 的安全摘要，例如 acceptance id、同 task identity、source mode、occurred_at、safe evidence ref、operator action type、redaction status、missing evidence 和 next required evidence。

### P0 - Required Evidence For Accepting Delivery Success

只有以下证据全部同时满足时，未来 live-success gate 才允许接受 delivery success：

- `source_mode=live`。
- 同 task terminal result recorded。
- live route execution success recorded。
- `operator_dropoff_acceptance` recorded for the same `task_id`。
- HIL pass recorded in the same evidence window。
- `safe_to_control=true` backed by live safety evidence。
- same-task identity 通过：`task_id`、`robot_id`、route/packet identity、terminal result identity 不漂移。
- 无 dangerous true fields、stale evidence、cross-task evidence、mock/readback-only source 或 unsafe ref。

### P0 - Current Run Boundary

当前无真实硬件、真实云、真实手机/browser、真实 live route execution 或真实 operator action，因此 synthetic/mock artifact 必须固定：

- `source_mode=synthetic` 或 `source_mode=mock`，不得伪装成 live。
- `operator_dropoff_acceptance_recorded=false`，除非明确是 mock fixture。
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `delivery_success_accepted=false`
- `acceptance_decision=blocked_missing_live_success_evidence`

### P0 - Negative Fixtures

Robot Software 必须覆盖 fail-closed negative fixtures：

- 缺 live route execution success。
- 缺 same task terminal result recorded。
- 缺 `operator_dropoff_acceptance`。
- 缺 HIL pass。
- 缺 safe-to-control。
- source mode 是 synthetic/mock/readback-only 但携带 success-like 字段。
- task/robot/route/terminal result identity mismatch。
- stale/historical-only operator confirmation。
- unsafe evidence ref、raw URL/token/local path/traceback 或 dangerous true fields。

### P1 - Product Documentation Sync

实现完成时，Robot Software 必须同步更新：

- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `docs/product/mobile_user_flow.md`（若触及手机 confirm/dropoff copy 或按钮语义）

文档必须说明：operator dropoff acceptance 是必要证据入口，不等于真实 delivery success；缺任一 live success 条件时保持 `delivery_success=false`。

## Acceptance Criteria

计划验收：

- 三个计划文档存在，且仅限 `pre_start.md`、`prd.md`、`tech-plan.md`。
- `tech-plan.md` 包含 `OKR 最低优先级核对`。
- 文档中明确 owner 是 `robot-software-engineer`。
- 文档中出现 `operator_dropoff_acceptance`、`delivery_success=false`、`blocked_missing_live_success_evidence`。

工程验收：

- Gate 只把 operator/user action 作为必要输入，不单独接受 delivery success。
- synthetic/mock fixture 生成 summary，但 fail closed。
- summary 通过 JSON schema/field assertions。
- negative fixtures 全部 fail closed。
- docs/product 同步更新。

## Priority And Owner

- Priority：P0 for fail-closed operator/user-action evidence gate and tests; P1 for product docs sync.
- Responsible Engineer：`robot-software-engineer`
- Product acceptance：`product-okr-owner` 在后续 closeout 阶段只接受 software proof boundary，不允许把 synthetic/mock operator action 写成真实交付。

## Risks

- 最大风险是把 operator 点击或文本确认当成 delivery success；验收必须强制同 task route execution、terminal result、HIL 和 safe-to-control 全齐。
- 第二风险是把 synthetic/mock fixture 当作真实用户动作；artifact 必须固定 `source_mode!=live` 和 `delivery_success=false`。
- 第三风险是继续做 wrapper 而非动作证据入口；本 sprint 禁止扩展 terminal-result/readback/export/voice draft wrapper。

## Sprint Documents

本计划阶段创建或更新：

- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/pre_start.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/prd.md`
- `sprints/2026.07.14_07-29_o5_operator_dropoff_acceptance_gate/tech-plan.md`

后续实现阶段再创建 closeout 文档。
