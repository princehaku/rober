# O6/O7 Field Operator Confirmation Material PRD

## 用户价值和产品北极星

产品北极星仍是：机器人可以被普通用户用手机或运营界面触发，并可验证地完成垃圾送达。当前缺口不是再多一层状态面板，而是把现场或准现场 operator report / operator confirmation 从聊天、日志或零散 artifact，变成同一 `task_id` 下可存档、可回读、可展示、可 fail-closed 的材料。

本轮用户价值是让研发和运营知道：某次路线/送达相关任务是否已经有 operator 侧确认材料，确认材料覆盖了哪些环节，哪些证据仍不足以证明 delivery success 或 HIL pass。

## 目标用户

- 研发：需要把 operator report 与 route/material evidence 绑定到同一 `task_id`，定位下一条现场执行命令缺什么材料。
- 运营调试：需要在 O7 工作站看到 operator material 的来源、确认状态、阻塞原因和下一步证据要求。
- 产品验收：需要区分 operator material 已接入、operator confirmation 已准现场消费、真实 delivery success 已证明这三件事。

## OKR 映射和方向判断

- O5：继续但本轮暂停主进度推进。O5 仍约 `85%`，没有真实 production cloud / production DB-queue / 4G / TLS / live endpoint 材料时，local/mock probe 或 checklist 不能计入主进度。
- O1：继续但本轮暂停主进度推进。O1 仍约 `86%`，下一步必须是真实 same-run `feedback_T1001.log`、motion command、operator report 和 HIL acceptance，而不是另一个软件 gate。
- O6：继续。目标是新增 operator confirmation material 的 archive/readback additive section，补真实机器人数据和 delivery/operator 材料缺口中的一类。
- O7：继续。目标是在 workstation consumer 中默认回读并展示 operator confirmation material，让运营能看到材料是否可用和仍缺什么。

方向判断：本轮选择 O6/O7 的 `field_operator_confirmation_material`，不是因为 O5/O1 不重要，而是因为 O5/O1 当前缺外部真实材料；继续消费同一 blocker 会违反 OKR credit gate。O6/O7 可以通过新的准现场 operator material 产生独立 additive material 进展。

## KR 拆解、更新和历史归档

- 本轮不在计划阶段更新 `OKR.md`，不移动任何 KR 到历史区。
- 后续实现完成后，Product closeout 才能根据 `tech-done.md`、`side2side_check.md`、`final.md` 和 owner 验证结果判断是否调整 O6/O7 百分比。
- 已完成 KR 历史记录位置保持 `OKR.md` 现有历史区不变；本轮计划不归档 KR。

## 本轮核心抓手

核心抓手是 `field_operator_confirmation_material`：把 operator report / operator confirmation 材料归一成安全、同 task、只读、可回读的 additive material，而不是继续增加 wrapper、handoff、review decision 或 checklist-only surface。

建议 material 至少表达：

- `task_id`、`source_schema`、`proof_boundary`。
- `operator_report_id`、`operator_report_present`、`operator_confirmation_present`。
- `operator_confirmation_status`、`operator_confirmed_at`、`confirmation_source`。
- `linked_route_material_present`、`linked_delivery_material_present`、`same_task_id_consumed`。
- `blocked_reasons`、`next_required_evidence`、`support_only_reason`。
- 固定 false safety fields。

## 验收口径

- Algorithm 可以从安全输入生成 `trashbot.field_operator_confirmation_material.v1`，并拒绝 task mismatch、unsafe text、raw/base64/path/token/URL/traceback 等材料。
- O6 可以归档并通过 `include=field_operator_confirmation_material` 回读 `trashbot.o6.field_operator_confirmation_material.v1`，并对缺字段、危险 true、proof boundary mismatch、task mismatch section-local fail-closed。
- O7 默认 include 该材料，consumer/UI 展示 operator material summary，同时保持控制能力和成功字段为 false。
- 验收结果必须明确 `software_proof_field_operator_confirmation_material_only`，不得写成 production cloud、live route execution、robot motion、delivery success 或 HIL pass。

## 责任 Engineer

- `robot-algorithm-engineer`：Algorithm producer 和 manifest tests/docs。
- `robot-software-engineer`：O6 archive/readback/include 和 relay tests/docs。
- `full-stack-software-engineer`：O7 consumer/default include/UI summary 和 workstation tests/docs。

## 非目标

- 不创建 production cloud、production DB/queue、OSS/CDN、TLS/4G 或 real browser/mobile 验收。
- 不执行真实 Nav2 route、robot motion、manual base control、WAVE ROVER HIL 或 delivery action。
- 不把 operator report 的存在解释成 delivery success；只有后续同 run route execution、delivery record、operator confirmation 和 acceptance record 同时满足时，才可进入更强证明。

