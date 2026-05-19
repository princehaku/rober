# Sprint 2026.05.19_09-10 Elevator Field Evidence Material Backfill Review Handoff - PRD

## 1. 用户价值和产品北极星

普通用户不需要理解 evidence gate，但现场团队必须知道跨楼层送垃圾为什么仍未完成、下一步谁补证据、补什么材料、如何安全 rerun。本轮产品目标是把上一轮材料回填复核决策转换为现场 owner handoff package：同一 safe `evidence_ref` 下，系统给出真实材料清单、owner handoff、safe rerun hints 和 phone-safe copy。

北极星仍是：低成本、手机友好、可解释的 ROS2 跨楼层送垃圾机器人。本轮不是宣布通过，而是把 `software_proof` / `not_proven` 的复核结果变成可执行交接，避免现场 owner 和手机端把 review decision 误读成 field pass。

## 2. OKR 映射

- Objective 2：为 elevator assisted delivery 的真实现场补证据建立 handoff package，支撑 KR5/KR6/KR7 的任务记录、失败解释、人工接管和电梯主链路边界。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal、field task record、dropoff/cancel/result 继续作为同一 safe `evidence_ref` 的下一步真实材料，不把 handoff ready 写成路线实跑。
- Objective 4：后续 mobile/web 只读展示 handoff package、owner next action 和 safe copy，不改变普通用户主操作 gating。
- Objective 1：不新增 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 真实材料，保持阻塞边界。
- Objective 5：不新增公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof，保持 stop-rule 边界。

## 3. KR 拆解或更新

本轮 planning 不更新 `OKR.md` 进度；后续 implementation 完成后，只能按验证结果保守记录 software-proof handoff 进展。

候选 KR 拆解：

1. KR-MBRH-1：PC gate 接收上一轮 `trashbot.elevator_field_evidence_trace_material_backfill_review_decision_summary.v1` 或 diagnostics safe alias，输出 `trashbot.elevator_field_evidence_trace_material_backfill_review_handoff_summary.v1`。
2. KR-MBRH-2：校验 review decision 的 schema、boundary、source、overall status、same safe `evidence_ref`、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven` 边界。
3. KR-MBRH-3：把 missing/rejected materials、next required evidence 和 decision reasons 转换为现场 owner handoff package。
4. KR-MBRH-4：生成 safe rerun hints，只允许描述“补齐同一 safe evidence_ref 后重跑 review handoff / review decision”，不得生成 motion command、ACK、cursor、raw artifact 或 success wording。
5. KR-MBRH-5：Robot diagnostics 新增 safe alias，禁止泄漏 raw material refs、本机路径、credentials、ROS topic、serial/UART/WAVE ROVER 细节或 success/control claim。
6. KR-MBRH-6：mobile/web 只读展示 owner handoff、真实材料缺口、safe rerun hints 和 phone-safe copy；Start Delivery、Confirm Dropoff、Cancel gating 不变。
7. KR-MBRH-7：产品文档同步说明这是 `software_proof` / `not_proven`，不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 4. 本轮核心抓手

抓手名称：`elevator_field_evidence_trace_material_backfill_review_handoff`。

输入来源：

- `elevator_field_evidence_trace_material_backfill_review_decision` artifact。
- `elevator_field_evidence_trace_material_backfill_review_decision_summary`。
- `robot_diagnostics_elevator_field_evidence_trace_material_backfill_review_decision_summary`。
- CLI 或 payload 提供的 safe `evidence_ref`。

输出判定：

- `blocked_missing_material_backfill_review_decision_not_proven`：缺上一轮 review decision summary 或 JSON 不可读。
- `blocked_unsupported_material_backfill_review_decision_not_proven`：schema、source、overall status、boundary、same-ref 布尔、`delivery_success=false` 或 `primary_actions_enabled=false` 不符合上一轮 contract。
- `blocked_evidence_ref_mismatch_not_proven`：review decision、diagnostics wrapper、CLI safe ref 不一致或缺 same-ref。
- `blocked_unsafe_material_review_handoff_not_proven`：raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、raw artifact、success/control claim 泄漏。
- `needs_field_owner_material_handoff_not_proven`：review decision 安全但真实材料仍缺，需要明确 owner handoff 和 safe rerun hints。
- `ready_for_field_owner_material_backfill_rerun_not_proven`：handoff package 安全齐全，可交给现场 owner 补同一 safe `evidence_ref` 的真实材料并重跑；仍不是 field pass。

## 5. 需要做什么

后续 implementation 应做三条互不重叠工作流：

1. Autonomy：新增 PC-only material backfill review handoff gate 和 unittest，负责 review decision contract、same-ref、owner handoff、safe rerun hints、unsafe copy、status mapping。
2. Robot：在 diagnostics 中新增 safe alias，只读消费 review handoff summary 并 fail closed。
3. Full-Stack：在 mobile/web 中新增只读 panel 和 fixture，显示现场 owner handoff 与 phone-safe copy，但不启用任何主动作。

Product closeout 在 implementation 后再做：

- 创建 `tech-done.md`、`side2side_check.md`、`final.md`。
- 根据真实验证结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 确保 `docs/interfaces/` 与 `docs/product/mobile_user_flow.md` 已同步更新。

## 6. 优先级和验收口径

P0：

- 必须消费上一轮 material backfill review decision summary。
- 必须验证 same safe `evidence_ref`。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须 fail closed：缺 review decision、unsupported schema/boundary、evidence_ref mismatch、unsafe copy、success/control claim、缺 owner handoff 都不能进入 ready。

P1：

- Robot diagnostics safe alias 可被 mobile/web 只读消费。
- mobile/web 展示 owner handoff、真实材料缺口和 safe rerun hints，文案中文优先，不暴露 raw JSON/ROS/hardware/internal path。
- interface/product docs 同步说明边界。

验收口径：

- Planning 阶段只验收三份文档存在和内容完整。
- Implementation 阶段必须由 Autonomy、Robot、Full-Stack 三个 worker 并行实现并运行 focused validation。
- 即使所有 focused validation 通过，也只能记为 Docker/local `software_proof`，不能写成真实 field pass。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：主责 PC evidence handoff gate。
- Robot Platform Engineer：主责 diagnostics safe alias。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读展示。
- Product Manager / OKR Owner：主责验收口径、OKR 进度边界和 sprint 留档收口。

## 8. 风险、阻塞和证据链

- O5 external proof 不在本轮范围内；缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser。
- O1 hardware proof 不在本轮范围内；缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log` 和 PR #5 2D LiDAR / ToF 真实材料。
- PR #4 route/elevator field pass 仍缺真实现场材料；本轮只是 handoff，不是 review 通过、现场通过或 delivery success。
- operator-provided material refs 只能以安全摘要进入下游；不得把本机路径、credential、raw artifact 或 checksum 暴露给 Robot/mobile。

## 9. 需要创建或更新的 sprint 文档

本轮 planning 必须创建：

- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/pre_start.md`
- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/prd.md`
- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/tech-plan.md`

后续 implementation 完成后再创建或更新：

- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/tech-done.md`
- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/side2side_check.md`
- `sprints/2026.05.19_09-10_elevator-field-evidence-material-backfill-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 相关 `docs/interfaces/` 与 `docs/product/mobile_user_flow.md`
