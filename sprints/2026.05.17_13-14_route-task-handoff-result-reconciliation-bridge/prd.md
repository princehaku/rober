# Sprint 2026.05.17_13-14 Route Task Handoff Result Reconciliation Bridge - PRD

sprint_type: epic

## 1. 用户价值

现场复测材料链目前已经可以从 review-result handoff 进入 result-intake，但到 result reconciliation 时，用户触点和诊断面看到的是普通 reconciliation summary。支持人员无法一眼判断该复账是否来自 PR #4 review-result handoff 链路，后续真实材料回填时容易把来源追溯重新交给人工说明。

本轮目标是把来源谱系变成软件契约：从 `route_task_field_retest_review_result_handoff` 进入 `route_task_field_retest_result_intake` 后，再进入 `route_task_field_retest_result_reconciliation` 时，PC/Robot/mobile 都能只读看到安全 lineage metadata。

## 2. OKR 映射

- Objective 2：继续推进电梯 assisted delivery 的现场材料复核链，使真实门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result 将来能沿同一 `evidence_ref` 复账。
- Objective 3：继续推进 fixed-route/Nav2 result materials 的同一 `evidence_ref` 复账链，确保 runtime log、route completion signal 和 task record 不被上游 handoff 裁剪。
- Objective 5：本轮不推进。数值最低但缺真实外部材料，继续 O5 local metadata 会重复消费 blocker。

## 3. 验收口径

1. PC `route_task_field_retest_result_reconciliation` artifact / summary 增加 phone-safe lineage 字段，例如 `source_result_intake_schema`、`source_review_result_handoff_schema`、`source_review_result_handoff_status` 或等价安全字段。
2. Lineage 只能来自受支持的 result-intake source metadata，不能读取 raw handoff artifact 或把 raw paths/checksums/credentials/ROS topics/serial details 暴露到输出。
3. Robot diagnostics 能从 reconciliation artifact / summary 只读透传 lineage metadata，并保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
4. Mobile/web 能展示该 reconciliation 来自 handoff-derived result-intake，同时 copy/export 只包含白名单字段，控制按钮 gating 不变。
5. Product closeout 明确：本轮只证明 Docker/local software-proof lineage bridge，不证明真实 route/elevator field pass、真实手机/browser、HIL、真实投放或 Objective 5 external proof。

## 4. 非目标

- 不新增真实现场材料采集。
- 不新增 ROS action/topic/service、ACK、cursor 或 robot command。
- 不改变 Start Delivery / Confirm Dropoff / Cancel 授权。
- 不推进真实 O5 cloud/4G/OSS/CDN/DB/queue 证据。
