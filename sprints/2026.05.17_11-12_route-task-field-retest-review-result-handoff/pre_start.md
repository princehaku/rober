# Sprint 2026.05.17_11-12 Route Task Field Retest Review Result Handoff - Pre Start

sprint_type: epic

## 1. 启动结论

本轮新建 Epic sprint：`route_task_field_retest_review_result_handoff`。目标是把上一轮 `route_task_field_retest_callback_review_decision` 的 review decision，安全翻译成 result-intake 执行前交接包，让 Autonomy、Robot、Full-stack 三个 owner 可以并行实现 PC gate、Robot diagnostics metadata-only consumer 和 mobile/web 只读交接面板。

本轮只做规划文档，不写产品代码；后续实现必须由对应 Engineer 子 agent 执行。证据边界必须继续保持：

- `software_proof_docker_route_task_field_retest_review_result_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. 背景证据

- 当前 `OKR.md` 4.1 显示 Objective 5 数字最低，约 68%。但 Objective 5 的下一步真实提升需要公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 证据；当前主机只有 Docker，继续堆本地 O5 metadata wrapper 不能形成真实进展。
- PR #5 评审暴露 `docs/product/production_hardware_boundary.md` 默认硬件集与 `monocular + 2D LiDAR + ToF` 必需基线矛盾，且新硬件假设缺 `docs/vendor/` 来源。近几轮硬件 source/config blocker 已多次消费，当前没有真实 SKU/source/receipt/install/wiring/calibration/HIL-entry 材料，不适合继续把硬件材料 blocker 包成新一轮主要结论。
- 最新 sprint `2026.05.17_10-11_route-task-field-retest-callback-review-decision` 已完成 `route_task_field_retest_callback_review_decision`，把 PR #4 route/elevator callback intake 推到 `ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema`、`blocked_unsafe_callback`、`blocked_success_claim` 等 review decision 层。

## 3. 本轮 rerank

当前可行动作不是继续推进 Objective 5 metadata wrapper，也不是重复消费 PR #5 硬件材料缺口，而是转向 Objective 2 / Objective 3 的 route/elevator evidence ladder：把 callback review decision 变成 result-intake 前的交接包，明确哪些材料可以进入结果入口，哪些必须 backfill、rerun 或 blocked。

本轮目标 Objective：

- Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环。
- Objective 3：建立可验证导航与固定路线能力。

不针对 Objective 5 的理由：

- Objective 5 数字最低，但当前缺真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser 材料。
- Docker-only 主机无法生成真实 external proof。
- 继续增加本地 O5 metadata wrapper 会重复消费同一外部环境 blocker，不会提升真实完成度。

## 4. 用户价值和产品北极星

产品北极星仍是：普通手机用户把垃圾交给小车后，小车可以沿固定路线或跨楼层 assisted delivery 完成送达，并且每次任务都有可复盘的 evidence chain。

本轮用户价值是降低现场复测结果入口的歧义：当回执审阅已经给出 `ready_for_result_intake`、backfill、mismatch 或 blocked 时，操作者、Robot diagnostics 和手机端看到同一份只读交接包，知道下一步该补什么、谁负责、哪些动作仍不可启用。

## 5. 上轮未完成项

- 真实 Nav2/fixed-route runtime log 仍缺。
- 真实 route completion signal 和 task record 仍缺。
- 真实 door_state、target_floor_confirmation、human_assistance_note 仍缺。
- 真实 dropoff_or_cancel_completion、delivery_result 和 same-`evidence_ref` 上车复账仍缺。
- PR #5 相关 2D LiDAR / ToF SKU、source、receipt、installation、wiring、power、calibration、HIL-entry 仍缺。
- Objective 5 external proof 仍缺。

## 6. Owner 和并行策略

本轮是跨 owner Epic sprint，后续实现必须并行派 3 个 owner：

- Autonomy Algorithm Engineer：负责 PC result-handoff gate 和 focused tests。
- Robot Platform Engineer：负责 diagnostics metadata-only result-handoff consumer。
- User Touchpoint Full-Stack Engineer：负责 mobile/web 只读 result-handoff panel 和 phone-safe copy。

Product Manager / OKR Owner 负责阶段验收、OKR 边界、sprint closeout、`OKR.md` 和相关 `docs/` 同步核对，不写产品代码。

## 7. 风险和阻塞

- 最大风险：result handoff 被误写成真实 field pass、真实投放、dropoff/cancel completion、delivery success 或 HIL。必须在 PC、Robot、mobile 和 closeout 中保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 证据风险：如果 callback review decision 的 source decision 是 backfill、mismatch 或 blocked，result handoff 必须 fail closed，不能生成可执行 result-intake。
- 协作风险：三个 owner 文件范围互不重叠，但字段 contract 强相关；tech-plan 必须给出相同 schema、边界字符串和验收命令。
- 文档风险：后续实现完成后必须更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和相关 `docs/`，本轮规划不替代交付。

## 8. 本轮需要创建或更新的 sprint 文档

本规划阶段创建：

- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/pre_start.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/prd.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/tech-plan.md`

后续实现完成后必须补齐：

- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/tech-done.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/side2side_check.md`
- `sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff/final.md`
