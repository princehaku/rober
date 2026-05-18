# Sprint 2026.05.19_04-05 Elevator Field Evidence Trace Callback Intake - PRD

## 1. 用户价值和产品北极星

现场 owner 需要一个可判定的回填入口：当真实电梯/路线现场材料稍后到达时，系统能按同一 safe `evidence_ref` 判断 callback packet 是否与现有 `elevator_action_feedback_trace`、diagnostics/mobile summary、route/elevator required materials 对齐。

产品北极星：让普通用户的送垃圾任务从“能看见阶段”进一步走向“现场材料可复盘、可回填、可拒绝伪证”。本轮不是实机通过，也不是 delivery success。

## 2. OKR 映射

| Objective | 当前判断 | 本 sprint 关系 |
| --- | --- | --- |
| Objective 5 | 约 68%，数字最低 | 需要真实 HTTPS/TLS、4G/SIM、OSS/CDN、DB/queue、production worker/cutover 或真实 phone/browser external proof；Docker-only 本轮不推进。 |
| Objective 1 | 约 81% | PR #5 closeout gate 已完成文档可判定性；真实 WAVE ROVER/UART/HIL 和 2D LiDAR / ToF 材料仍不可用，本轮不消费 O1 blocker。 |
| Objective 2 | 约 99% | 主目标。补 PR #4 elevator-assisted delivery 现场回填链路的 intake 判定。 |
| Objective 3 | 约 99% | 共同目标。把 Nav2/fixed-route runtime、route completion signal、现场 task record 纳入 required materials，但保持 `not_proven`。 |
| Objective 4 | 约 99% | 支撑目标。mobile/web 只读展示 intake summary，不开放控制动作。 |

## 3. KR 拆解或更新

- Objective 2 KR5：每次任务产出可复盘记录。本 sprint 后续实现应把 callback packet 与 `elevator_action_feedback_trace`、task record、diagnostics/mobile summary 统一到同一 `evidence_ref`。
- Objective 2 KR6/KR7：电梯 assisted delivery 状态链已进入主链；本 sprint 后续实现应把门状态、目标楼层确认、人工协助、失败/超时/人工接管材料纳入 required materials。
- Objective 3 KR3/KR4/KR5：fixed route / Nav2 仍缺真实 runtime；本 sprint 后续实现应把 route runtime log、route completion signal、现场 task record 列为缺失项，避免 trace 被误写成 route pass。
- Objective 4 KR6/KR7：手机端只读展示 `elevator_field_evidence_trace_callback_intake` 结果，不暴露 raw JSON、ROS topic、串口、凭证、本机路径或控制授权。

## 4. 本轮核心抓手

核心抓手：`elevator_field_evidence_trace_callback_intake`。

输入：

1. safe callback packet，来自未来现场 owner 回填。
2. `elevator_action_feedback_trace` summary。
3. diagnostics/mobile summary，如 `robot_diagnostics_elevator_action_feedback_trace_summary`。
4. route/elevator required materials 清单。

输出：

1. `intake_status`：`blocked_missing_callback_packet_not_proven`、`blocked_evidence_ref_mismatch_not_proven`、`needs_route_elevator_material_backfill_not_proven`、`callback_packet_intake_ready_for_review_not_proven`。
2. `accepted_callback_materials`：只列 schema、safe `evidence_ref`、redaction status、owner acknowledgement 等元数据项。
3. `missing_required_materials`：列出真实 route/elevator field materials。
4. `owner_handoff`：给 Autonomy、Robot、现场 owner、Full-Stack 的下一步。
5. `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 5. 需要做什么

本轮只做 Epic planning 三文档，不实现代码。

实现阶段按 3 个并行 owner 拆分：

- Autonomy Algorithm Engineer 负责 PC evidence gate：读取 callback packet、trace summary、required materials，输出 intake artifact 和 summary。
- Robot Platform Engineer 负责 diagnostics safe alias：只读消费 summary 并 fail closed。
- User Touchpoint Full-Stack Engineer 负责 mobile/web 只读 panel：展示 intake status、missing materials、owner handoff，不改变按钮 gating。
- Product Manager / OKR Owner 负责实现完成后的 closeout、OKR 边界和 sprint 文档链。

## 6. 优先级和验收口径

### P0 必须满足

- 同一 safe `evidence_ref` 是 intake 判定主键；缺失、不安全或不一致时必须 blocked。
- `source` 必须是 `software_proof`。
- `overall_status` 必须是 `not_proven` 或等价 not-proven blocked state。
- `delivery_success=false` 和 `primary_actions_enabled=false` 必须保持 false。
- 不得把 callback intake 写成真实电梯、真实路线、真实投放、HIL、真实手机/browser 或 O5 external proof。

### P1 必须满足

- callback packet 缺少 owner、material type、redaction status、trace summary ref、required materials acknowledgement 时 fail closed。
- Robot diagnostics 只暴露 summary alias，不读取 raw artifact。
- mobile/web 只读展示，不启用 Start Delivery、Confirm Dropoff、Cancel。
- 文档必须写明本轮 evidence boundary。

### P2 可后续增强

- 后续可把 accepted/missing/rejected material state 接到下一轮 review decision；本 sprint 不做 review decision 和 OKR 百分比上调。

## 7. 对应责任 Engineer

| Owner | 责任 |
| --- | --- |
| Autonomy Algorithm Engineer | PC evidence gate、callback packet parsing、safe `evidence_ref` 判定、focused tests、schema docs。 |
| Robot Platform Engineer | diagnostics safe alias、fail-closed summary 读取、Robot test fence、Robot docs。 |
| User Touchpoint Full-Stack Engineer | mobile/web 只读 panel、fixtures、targeted tests、mobile user flow docs。 |
| Product Manager / OKR Owner | PRD/tech-plan、实现后验收、OKR closeout、progress log 和 final。 |

## 8. 风险、阻塞和需要补齐的证据链

- 真实 route/elevator field materials 仍不存在：真实门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、route completion signal、现场 task record、dropoff/cancel completion、delivery result。
- 真实 WAVE ROVER/UART/HIL 仍不存在。
- PR #5 真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 仍不存在。
- O5 external proof 仍不存在。
- 如果后续实现把 callback packet 默认 accepted 或把 missing materials 隐藏成成功文案，应视为验收失败。

## 9. 需要创建或更新的 sprint 文档

本规划阶段创建：

- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/pre_start.md`
- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/prd.md`
- `sprints/2026.05.19_04-05_elevator-field-evidence-trace-callback-intake/tech-plan.md`

实现后再创建：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

实现后按真实结果决定是否更新 `OKR.md`、`docs/process/okr_progress_log.md` 和相关 `docs/`。
