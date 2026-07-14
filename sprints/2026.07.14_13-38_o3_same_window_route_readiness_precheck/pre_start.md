# Pre Start - O3 Same-Window Route Readiness Precheck

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/`
- Started at: 2026-07-14 13:38 CST
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_same_window_route_readiness_precheck_only`
- Target lane: O3/O1 strict no-motion route execution prerequisite, while O5 remains the lowest blocked Objective.

## 上轮未完成项和 Blocker

最近三轮 O7 voice runtime preflight、voice runtime offline smoke、voice speaker ACK/failure event-write 均已收口为 local/offline 或 local/mock software proof，且 O5 继续约 `85%`、O1 继续约 `94%`、O6/O7 继续约 `93%`。这些 sprint 明确下一步不能重复 voice preflight、offline smoke、TTS draft、speaker ACK/failure、operator/dropoff action/browser、terminal-result bridge/intake/export/reconciliation、delivery-state live-success、CDN/TLS 4xx、O6/O7 readback/export/action receipt 或其他附近 wrapper。

O5 仍是当前最低 Objective，但 success-class production/cloud evidence、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser proof、explicit same-window live route/HIL/delivery/operator evidence 和授权真实 voice runtime smoke 当前均不可得。继续做 O5 或 O7 wrapper 会重复消费同一 blocker。

O3/O1 route chain 已有 accepted material：07:07 fail-closed controlled route execution gate record、08:09 no-motion bounded route command plan、23:23 bounded route mock execution local software proof。它们仍不证明 live route execution、delivery、HIL 或 safe-to-control，但已经给出一个可被 Algorithm 单 owner 消费的下一层前置证据入口。

## 用户价值和产品北极星

北极星仍是普通用户把垃圾交给小车后，小车沿固定路线安全送达，并留下可复盘证据链。本轮不发车、不执行路线、不做交付；本轮价值是把已有 same-task route material 转成下一次现场 live route/HIL 前必须满足的 same-window readiness checklist，避免下一轮直接跳到控制命令或继续堆 wrapper。

## 本轮目标

创建 O3/O1 strict no-motion same-window route readiness precheck 计划，由 Algorithm owner 后续实现一个 artifact：

- 消费已接受的 bounded plan、controlled gate record、bounded mock execution summary/progress，必要时只读 stop/HIL mock gate。
- 输出同一 `packet_id` / `task_id` / `route_intent_id` 的 route-readiness precheck summary。
- 固定 false fields：`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。
- 明确 missing evidence：operator approval、current live stop/HIL、same-window `/scan`、AMCL/localization、dynamic TF、Nav2/controller result、delivery/operator acceptance。
- 保持 no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。

## Owner 和边界

- `robot-algorithm-engineer` 负责实现、验证、修复和 `tech-done.md`。
- 主节点只做计划、派单、验收和最终汇总。
- 不需要并行 owner；本轮不触碰 Full-stack/O7 voice、O5 cloud、Hardware UART 或 live control。
- 本轮不读取真实 WAVE ROVER UART，不发送 ROS2 motion command，不调用任何 robot control endpoint。

## 预期收口

本轮如果成功，只接受为 `software_proof_o3_o1_same_window_route_readiness_precheck_only`。O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%`，主百分比不调整，KR `不归档`。下一步只有在 explicit operator approval 和 same-window live readiness 真正可采集后，才允许进入受控 route execution evidence sprint。
