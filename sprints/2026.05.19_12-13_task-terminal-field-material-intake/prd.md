# Sprint 2026.05.19_12-13 Task Terminal Field Material Intake - PRD

## 1. 用户价值和产品北极星

本轮产品目标是把 11-12 的 `task_terminal_completion_mainline` 从“只读终态主链路 summary”推进到 `task_terminal_field_material_intake`：Robot diagnostics 和 mobile/web 都能在同一 safe `evidence_ref` 下显示后续现场材料是否可回填、缺哪些材料、哪些 safe refs 已被接受、下一步证据要求是什么。

面向用户和现场 owner 的价值：

- 现场 owner 可以围绕同一 safe `evidence_ref` 提交 dropoff/cancel terminal materials、route/elevator field materials 和 real phone/browser evidence，不再靠聊天或零散文档传递材料。
- 手机端能明确显示“现场材料回填入口”当前仍是 `software_proof` / `not_proven`，防止普通用户把材料入口误解为真实投放完成或 delivery success。
- Robot diagnostics 能把 sanitized terminal summary/material-intake payload 暴露给后续复核链路，但不会触发 ACK、commands、Nav2、HIL 或控制动作。

产品北极星：普通手机用户最终能用低成本机器人完成送垃圾闭环。本轮只建立真实材料进入主链路前的 fail-closed 入口，不证明真实手机、真实电梯、真实 Nav2/fixed-route、HIL、O5 external proof 或 delivery success。

## 2. OKR 映射

| Objective | 映射 | 本轮是否提高真实完成度 |
| --- | --- | --- |
| Objective 5 | 当前约 68%，仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。 | 否。本轮不做 O5 metadata depth，不证明 external proof。 |
| Objective 1 | 当前约 81%，上一轮已完成硬件真实材料升级请求；仍缺 WAVE ROVER/UART/HIL、`feedback_T1001`、真实 `/odom` / `/imu` / `/battery` 和 PR #5 2D LiDAR / ToF 真实材料。 | 否。本轮不碰硬件材料，不提高 O1。 |
| Objective 2 | 当前约 99%，仍缺真实 dropoff/cancel completion、route/elevator field pass、delivery result 和真实现场 task record。 | 只推进 terminal field material intake 软件入口；不提高真实完成度。 |
| Objective 3 | 当前约 99%，仍缺真实 Nav2/fixed-route runtime、route completion signal 和现场复账。 | 只要求 intake fields 与 route/elevator/Nav2 evidence 不冲突；不证明真实路线。 |
| Objective 4 | 当前约 99%，手机端需要解释材料回填缺口和安全边界。 | 只新增只读可见性；不证明真实手机或 production app。 |

## 3. KR 拆解或更新

### KR-A：Robot diagnostics field material intake summary

作为 Robot Platform Engineer，我需要在 diagnostics 中暴露 `robot_diagnostics_task_terminal_field_material_intake_summary`，让后续真实材料能进入同一 safe `evidence_ref` 主链路。

必须包含：

- `schema`: `trashbot.task_terminal_field_material_intake.v1` 或 summary alias。
- `summary_alias`: `robot_diagnostics_task_terminal_field_material_intake_summary`。
- `source`: `software_proof`。
- `status`: `blocked_missing_field_materials` / `ready_for_field_owner_material_backfill_not_proven` / `blocked_unsafe_payload`。
- `safe_evidence_ref`：必须是 phone-safe / diagnostics-safe string。
- `accepted_safe_refs`：只列出已清洗的 refs，不列 raw artifact、local path、checksum 或 credentials。
- `missing_materials`：至少覆盖真实 task record、dropoff/cancel terminal material、route/elevator field material、real phone/browser evidence。
- `next_required_evidence`：下一步要 field owner 提供的真实材料。
- `evidence_boundary`：必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

验收口径：缺 sanitized payload、缺 safe evidence_ref、unsupported schema、raw artifact、success wording、completion claim、HIL claim、O5 external proof claim、control grant 都必须 fail closed。

### KR-B：mobile/web field material intake panel

作为 User Touchpoint Full-Stack Engineer，我需要 mobile/web 展示只读“现场材料回填入口”panel，并保持 Start Delivery、Confirm Dropoff、Cancel gating 不扩大。

必须展示：

- intake status。
- safe `evidence_ref`。
- missing materials。
- accepted safe refs。
- next required evidence。
- phone-safe material intake copy。
- `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。

验收口径：panel 不得触发 ACK、cursor、diagnostics fetch、Start Delivery、Confirm Dropoff、Cancel、handoff route、review route、Nav2、HIL 或 robot command。缺 summary 时展示 fail-closed 状态。

### KR-C：Product closeout and OKR evidence boundary

作为 Product OKR Owner，我需要实现后更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`，说明本轮只是 O2/O3/O4 主链路可回填性。

验收口径：最终必须明确 Objective 5 不提高、Objective 1 不提高，Objective 2/3/4 只记录 field material intake 的 software-proof 可回填性；不得把 PRD、diagnostics summary、mobile panel 或 accepted safe refs 写成真实投放、真实取消、真实电梯、真实手机、HIL、O5 external proof 或 delivery success。

### KR-D：Autonomy evidence field consultation

作为 Autonomy Algorithm Engineer，我需要只读确认 route/elevator/Nav2 evidence fields 与 Objective 3 不冲突。

必须确认：

- intake summary 不得使用 `route_passed`、`fixed_route_passed`、`nav2_passed`、`field_pass` 等真实通过语义。
- route/elevator fields 只能作为 missing/next-required evidence 列出。
- 真实 Nav2/fixed-route runtime log、route completion signal、真实 task record、door/floor/human-assist evidence 必须留给后续现场材料回填。

## 4. 本轮核心抓手

`task_terminal_field_material_intake` 是本轮唯一核心抓手。

它不是新的硬件 wrapper，不是 cloud probe，不是真实 field-run pass，不是手机真实验收。它要回答的问题是：当现场 owner 准备提交真实 terminal/route/elevator/phone/browser 材料时，Robot diagnostics 和手机端是否已有一个不会误触控制、不会误报成功、能清楚列出缺口和下一步证据的主链路入口。

## 5. 需要做什么

1. Robot：新增或暴露 `robot_diagnostics_task_terminal_field_material_intake_summary`，只消费 sanitized terminal summary/material-intake payload，更新 diagnostics tests 和 `docs/interfaces/operator_gateway_diagnostics.md`。
2. Full-Stack：在 mobile/web 增加只读“现场材料回填入口”panel，更新 fixtures/tests 和 `docs/product/mobile_user_flow.md`。
3. Product：实现后更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。
4. Autonomy：只读提供 route/elevator/Nav2 evidence fields 建议，避免与 Objective 3 语义冲突。

## 6. 优先级和验收口径

优先级：

1. P0：Robot diagnostics summary 必须 fail closed，不能产生 control grant、completion claim 或 delivery success claim。
2. P0：mobile/web panel 必须只读，不扩大 Start Delivery、Confirm Dropoff、Cancel gating。
3. P1：字段必须能承接后续真实材料回填：same safe `evidence_ref`、accepted safe refs、missing materials、next required evidence。
4. P1：Product closeout 必须保守记录 OKR，不提高 O5/O1 真实进度。

全局验收口径：

- 必须包含 `task_terminal_field_material_intake`。
- 必须包含 `robot_diagnostics_task_terminal_field_material_intake_summary`。
- 必须包含 `software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 必须显式提到 Objective 5、Objective 1、Objective 2、Objective 3、Objective 4、PR #4、PR #5。
- 必须由 `robot-software-engineer`、`full-stack-software-engineer`、`product-okr-owner` 三个 owner 并行负责；`autonomy-engineer` 只读咨询。

## 7. 风险、阻塞和证据链

- 当前主机只有 Docker，没有真实 WAVE ROVER、UART、2D LiDAR、ToF、真实电梯、真实 Nav2/fixed-route、真实手机、4G、OSS/CDN 或 production DB/queue。
- 本轮即使全部验证通过，也只能证明 repo 的 `software_proof` field material intake contract 和 UI/diagnostics 展示工作，不能证明真实 dropoff/cancel completion、route/elevator field pass、Nav2/fixed-route、真实手机、HIL、O5 external proof 或 delivery success。
- PR #4 真实 route/elevator materials 仍需现场 owner 后续提供：真实门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、真实 task record、route completion signal、dropoff/cancel completion 和 delivery result。
- PR #5 真实 2D LiDAR / ToF materials 仍需现场 owner 后续提供；本轮不得新增或猜测硬件事实。

## 8. 需要创建或更新的 sprint 文档

本阶段已创建 PRD。实现后必须更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

Product closeout 必须再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。任何 Robot、mobile/web 或接口契约变更必须同步更新对应 `docs/` 文档。
