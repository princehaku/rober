# PRD - O5 Delivery State Terminal Reconciliation

## 用户价值和产品北极星

普通用户只需要知道任务是否真实送达，而不是被一条 mock terminal result 误导。产品北极星仍是“可验证地可靠交付垃圾”：手机/云端/状态机必须能把本地 mock 路线终态、真实路线执行、人工送达确认、HIL 和 safe-to-control 清楚分开。

本轮价值是建立交付状态机的 fail-closed 解释层：当 O5 terminal-result bridge 记录 `mock_route_execution_completed_not_live_delivery` 时，状态机必须明确进入 error 或等价 fail-closed final state，而不是把它当作 `delivery_success` 或 dropoff success。

## OKR 映射和方向判断

- Objective: Objective 5 云中转控制面产品化。
- 当前进度：约 `85%`，仍为最低 Objective。
- 方向判断：继续 O5，但调整抓手。
- 调整原因：真实 production/external evidence unavailable，最近 O5 CDN/TLS 4xx probe、readiness packet consumption、cloud external review-decision、O5 bounded-route terminal-result bridge，以及 O6/O7 terminal-result intake/export 均为 support-only。继续做 wrapper 不应提升 OKR。
- 本轮抓手：转向 O5/O1/O3 交付状态机 fail-closed 主链路，让已有 terminal result 被状态机正确解释和拒绝升级。

## KR 拆解、更新或历史归档

本轮不归档 KR，也不预设 OKR 百分比上调。

计划拆解：

- O5：terminal result 到 delivery state reconciliation 的本地软件主链路可复验。
- O1：继续保留 `safe_to_control=false`、`hil_pass=false`，不引入运动控制。
- O3：继续保留 `route_execution_success=false`，不把 mock route execution 当 live route execution。

已完成 KR 历史记录位置：不适用，本轮是计划阶段，且目标是 fail-closed 主链路准备，不是 KR 完成或归档。

## 需求范围

必须实现：

- 新增离线 reconcile 脚本，默认消费：
  - `sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`
- 在 `DeliveryStateMachine` 中接入或暴露离线 terminal-result reconcile 能力。
- 生成 summary artifact：
  - schema: `trashbot.o5.delivery_state_terminal_reconciliation.v1`
  - source result: `mock_route_execution_completed_not_live_delivery`
  - `terminal_result_accepted_for_delivery=false`
  - `delivery_success=false`
  - `route_execution_success=false`
  - `safe_to_control=false`
  - `hil_pass=false`
  - `final_state=error` 或等价 fail-closed
- 状态机事件必须可读解释：mock terminal result 不能当真实路线执行、真实送达、dropoff success、HIL 或 safe-to-control。
- 单测必须覆盖 happy fail-closed path、dangerous true field、source schema drift、missing identity、unexpected live/success state 等拒绝路径。

不得实现：

- 不接真实 production cloud、production DB/queue、OSS/CDN、4G/SIM 或真实 phone/browser。
- 不触发 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或任何真实机器人控制。
- 不把 `mock_route_execution_completed_not_live_delivery` 映射为 `delivery_success=true`、dropoff success、route execution success、HIL 或 safe-to-control。
- 不新增 O6/O7 intake/export wrapper 或 UI surface。

## 优先级和验收口径

优先级：P0，本轮只接受 fail-closed 语义正确性，不接受“看起来完成”的 happy path 包装。

Product 接受条件：

- 生成 `trashbot.o5.delivery_state_terminal_reconciliation.v1` summary。
- Summary 明确 `terminal_result_accepted_for_delivery=false`。
- Summary 固定 `delivery_success=false`、`route_execution_success=false`、`safe_to_control=false`、`hil_pass=false`。
- Summary 的 `final_state=error` 或等价 fail-closed。
- 状态机事件可读解释 mock terminal result 不是真实路线执行/送达。
- 验收命令全部通过，且 `git diff --check` scoped 通过。

Product 拒绝条件：

- 任一危险字段为 true。
- Mock terminal result 被接受为真实 delivery。
- 只生成 wrapper summary，但没有经过 `DeliveryStateMachine` reconcile。
- 文档或测试把本轮描述成 production、HIL、route execution、dropoff success 或 safe-to-control。

## 对应责任 Engineer

Implementation owner：`robot-software-engineer` 单 owner 闭环。

Product owner 只负责本轮计划、后续验收和 OKR closeout；不得代写产品代码或测试代码。

## 风险、阻塞和证据链缺口

- 真实 production/external evidence 仍不可用，O5 production blocker 不因本轮解决。
- Source artifact 是 local/mock terminal result，不是 live route execution。
- 状态机若已有 dropoff success 事件语义，必须避免被 source `terminal_result_recorded` 误触发。
- 本轮不补 HIL、safe-to-control、operator acceptance 或真实机器人控制证据。

下一步证据链缺口仍是：success-class production/external evidence，或 explicit-operator-approved current live HIL/current route execution/delivery/operator acceptance。

## 需要创建或更新的 sprint 文档

本轮计划阶段创建：

- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/pre_start.md`
- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/prd.md`
- `sprints/2026.07.14_04-27_o5_delivery_state_terminal_reconciliation/tech-plan.md`

本轮不创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

上述三个文件必须等 `robot-software-engineer` 实现、验证并产出证据后再写。
