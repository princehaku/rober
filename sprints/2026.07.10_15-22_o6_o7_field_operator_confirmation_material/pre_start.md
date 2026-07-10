# O6/O7 Field Operator Confirmation Material Pre-start

## sprint_type: epic

本轮是跨 Algorithm、O6 archive/readback、O7 consumer/UI 的 epic sprint。计划阶段只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，不改代码、不改 `OKR.md`、不创建 `tech-done.md`、`side2side_check.md` 或 `final.md`。

## 背景

本轮已按项目纪律读取 `AGENTS.md`、`OKR.md`、最近相关 sprint 收口和自动化记忆。当前 OKR 快照中 O5 约 `85%`，是最低 Objective；O1 约 `86%`；O6/O7 约 `90%`。

O5 的主要缺口仍是真实 production cloud、production DB/queue、4G/TLS、OSS/CDN live traffic、真实手机/browser 验收和 live endpoint 材料。`same_task_mission_artifact_credit_gate` 已经把 local/mock probe、readback-only、checklist-only 和 support-only surface 固化为 `okr_credit_allowed=false`，因此本轮不能再用 O5 本地探针或只读回读包装提升主进度。

O1 上一轮刚完成 `wave_rover_nonzero_feedback_hil_gate` 软件 gate。下一步有效增长必须消费同一真实 run 的 `feedback_T1001.log`、motion command、operator report 和 HIL acceptance。当前没有新的真实 WAVE ROVER nonzero L/R 或 HIL acceptance 材料，继续做同类软件 gate 会重复消费同一 blocker。

O6/O7 虽然约 `90%`，但仍存在真实或准现场 delivery/operator 材料缺口。当前可推进的新增材料类别是 `field_operator_confirmation_material`：把真实上位机或准现场 operator report / operator confirmation 类材料，以只读 additive material 进入 Algorithm -> O6 -> O7 证据链，避免继续做同层 wrapper。

## 本轮目标

- Algorithm 侧新增 `trashbot.field_operator_confirmation_material.v1` 生产入口，消费同一 `task_id` 的 operator report / operator confirmation material，输出安全摘要。
- O6 archive/readback 新增 `trashbot.o6.field_operator_confirmation_material.v1` additive section，支持 archive detail、field evidence、artifact bundle、consumer detail 和 `include=field_operator_confirmation_material` 回读。
- O7 consumer/UI 新增 `trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1` 默认 include 和只读 summary，帮助运营确认哪些 operator 材料已接入、哪些仍阻塞。
- 全链路固定 proof boundary：`software_proof_field_operator_confirmation_material_only`。

## Proof Boundary

本轮只证明 field operator report / operator confirmation material 可以被 Algorithm、O6、O7 安全消费、归档、回读和展示。

本轮不证明：

- production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic 或 production worker/cutover。
- live Nav2 execution、NavigateToPose/FollowPath/controller/BT 执行或 route execution success。
- robot motion、WAVE ROVER nonzero L/R、safe-to-control、HIL pass 或 hardware safety。
- delivery success、真实到达、真实投放完成或长期路线验收。

所有 schema 与 UI 都必须保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`。

## Owner

- Product / OKR owner：`product-okr-owner` 负责本轮计划、范围边界和后续验收口径。
- Algorithm owner：`robot-algorithm-engineer`。
- O6 backend owner：`robot-software-engineer`。
- O7 consumer/UI owner：`full-stack-software-engineer`。

## 风险与阻塞

- 如果输入 operator report 只包含人工口头结论，没有同一 `task_id`、时间戳、命令上下文或材料来源，本轮只能 fail-closed 为 not proven。
- 如果后续 worker 没有拿到真实或准现场 operator material，可先用 fixture 覆盖 schema 与 fail-closed 逻辑，但不能声明 operator confirmation 已真实完成。
- 该 sprint 不能作为 O5 production cloud 或 O1 HIL 的替代证明，只能作为 O6/O7 的 additive material 进展。

