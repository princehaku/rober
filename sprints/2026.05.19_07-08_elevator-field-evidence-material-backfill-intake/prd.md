# Sprint 2026.05.19_07-08 Elevator Field Evidence Material Backfill Intake - PRD

## 1. 用户价值和产品北极星

普通用户不关心证据链名字，但现场交付团队必须知道为什么跨楼层送垃圾没有被判定为完成。本轮产品目标是给现场 owner 一个安全回填入口：用同一 safe `evidence_ref` 把真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime、task record、dropoff/cancel/result 等材料挂回上一轮 handoff，而不是让材料散落在聊天、截图或本机路径里。

北极星仍是：低成本、手机友好、可解释的 ROS2 跨楼层送垃圾机器人。本轮不追求“宣布通过”，而是让后续真实 field owner 的材料可以被系统性接收、复核和展示。

## 2. OKR 映射

- Objective 2：为 elevator assisted delivery 的真实现场材料回填建立入口，支撑 KR5/KR6/KR7 的可复盘任务记录和失败解释。
- Objective 3：把 Nav2/fixed-route runtime log、route completion signal 和 field task record 纳入同一 safe `evidence_ref` 的必需材料，不把 handoff summary 当成路线实跑。
- Objective 4：后续 mobile/web 只读展示材料回填状态、缺口和下一步，不改变普通用户主操作 gating。
- Objective 1：不新增 WAVE ROVER/UART/HIL 或 PR #5 2D LiDAR / ToF 真实材料，保持阻塞边界。
- Objective 5：不新增公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover external proof，保持阻塞边界。

## 3. KR 拆解或更新

本轮不更新 `OKR.md` 进度；后续 implementation 完成后，只能按验证结果保守记录 software-proof 进展。

候选 KR 拆解：

1. KR-MBI-1：PC gate 接收上一轮 handoff summary 和 operator material packet/file refs，输出 `trashbot.elevator_field_evidence_trace_material_backfill_intake_summary.v1`。
2. KR-MBI-2：校验 required materials 覆盖八类现场材料，并把缺失、占位、unsafe、same-ref mismatch 映射成 fail-closed 状态。
3. KR-MBI-3：Robot diagnostics 新增 safe alias，禁止泄漏 raw material refs、本机路径、credentials、ROS topic、serial/UART/WAVE ROVER 细节或 success/control claim。
4. KR-MBI-4：mobile/web 只读展示 backfill intake status、missing materials、accepted material refs、next required evidence 和 evidence boundary；Start Delivery、Confirm Dropoff、Cancel gating 不变。
5. KR-MBI-5：产品文档同步说明这是 `software_proof` / `not_proven`，不是真实 route/elevator field pass、HIL、真实手机/browser、Objective 5 external proof 或 delivery success。

## 4. 本轮核心抓手

抓手名称：`elevator_field_evidence_trace_material_backfill_intake`。

输入来源：

- `elevator_field_evidence_trace_callback_review_handoff` artifact。
- `elevator_field_evidence_trace_callback_review_handoff_summary`。
- `robot_diagnostics_elevator_field_evidence_trace_callback_review_handoff_summary`。
- operator-provided material packet / file refs 的安全摘要。
- CLI 或 payload 提供的 safe `evidence_ref`。

输出判定：

- `blocked_missing_handoff_not_proven`：缺上一轮 handoff summary 或 JSON 不可读。
- `blocked_unsupported_handoff_not_proven`：schema、source、overall status、boundary、same-ref 布尔、`delivery_success=false` 或 `primary_actions_enabled=false` 不符合上一轮 contract。
- `blocked_missing_material_packet_not_proven`：缺 operator material packet / file refs。
- `blocked_evidence_ref_mismatch_not_proven`：handoff、operator packet、CLI safe ref 不一致或缺 same-ref。
- `blocked_unsafe_material_ref_not_proven`：raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER、checksum、raw artifact、success/control claim 泄漏。
- `needs_required_material_backfill_not_proven`：材料包安全但 required materials 缺失或仅占位。
- `ready_for_material_review_not_proven`：required materials 的安全引用齐全，准备进入后续 review；仍不是 field pass。

## 5. 需要做什么

后续 implementation 应做三条互不重叠工作流：

1. Autonomy：新增 PC-only intake gate 和 unittest，负责 schema、same-ref、required material、unsafe copy、status mapping。
2. Robot：在 diagnostics 中新增 safe alias，只读消费 summary 并 fail closed。
3. Full-Stack：在 mobile/web 中新增只读 panel 和 fixture，显示材料回填状态但不启用任何主动作。

Product closeout 在 implementation 后再做：

- 创建 `tech-done.md`、`side2side_check.md`、`final.md`。
- 根据真实验证结果决定是否更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 确保 `docs/interfaces/` 与 `docs/product/mobile_user_flow.md` 已同步更新。

## 6. 优先级和验收口径

P0：

- 必须消费上一轮 handoff summary。
- 必须消费 operator-provided material packet/file refs 的安全摘要。
- 必须验证 same safe `evidence_ref`。
- 必须保留 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 必须 fail closed：缺材料、占位材料、evidence_ref mismatch、unsafe copy、success/control claim 都不能进入 ready。

P1：

- Robot diagnostics safe alias 可被 mobile/web 只读消费。
- mobile/web 展示缺口和下一步，文案中文优先，不暴露 raw JSON/ROS/hardware/internal path。
- interface/product docs 同步说明边界。

验收口径：

- Planning 阶段只验收三份文档存在和内容完整。
- Implementation 阶段必须由 Autonomy、Robot、Full-Stack 三个 worker 并行实现并运行 focused validation。
- 即使所有 focused validation 通过，也只能记为 Docker/local `software_proof`，不能写成真实 field pass。

## 7. 对应责任 Engineer

- Autonomy Algorithm Engineer：主责 PC evidence gate。
- Robot Platform Engineer：主责 diagnostics safe alias。
- User Touchpoint Full-Stack Engineer：主责 mobile/web 只读展示。
- Product Manager / OKR Owner：主责验收口径、OKR 进度边界和 sprint 留档收口。

## 8. 风险、阻塞和证据链

- O5 external proof 不在本轮范围内；缺公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover。
- O1 hardware proof 不在本轮范围内；缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log` 和 PR #5 2D LiDAR / ToF 真实材料。
- PR #4 route/elevator field pass 仍缺真实现场材料；本轮只是 intake 入口，不是 review 通过或 field pass。
- operator-provided material packet/file refs 只能以安全摘要进入下游；不得把本机路径、credential、raw artifact 或 checksum 暴露给 Robot/mobile。

## 9. 需要创建或更新的 sprint 文档

本轮 planning 必须创建：

- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/pre_start.md`
- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/prd.md`
- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/tech-plan.md`

后续 implementation 完成后再创建或更新：

- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/tech-done.md`
- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/side2side_check.md`
- `sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- 相关 `docs/interfaces/` 与 `docs/product/mobile_user_flow.md`
