# PRD - O7 Delivery Result Intake

## 用户价值

PC operator 在查看同一任务详情时，需要能把本轮 delivery result 材料作为结构化证据写入任务归档，而不是只依赖旁路日志或只读摘要。这个能力让后续 route replay、mission checklist、O6 archive 和 Product closeout 可以围绕同一个 `task_id` 审核送达结果。

## OKR 对齐

- 主要对齐 O7：PC 端运营调试与数据训练平台，补齐 selected-task delivery result evidence action-write。
- 次要对齐 O6：云中转/归档侧消费任务记录和感知/结果事件的本地软件合同。
- O5 仍是最低项但本轮不直接推进，因为当前缺真实 production success-class 外部证据。

## 需求

1. PC/O7 selected task 增加 `delivery result intake` request。
2. Request 至少包含 `robot_id`、`task_id`、`record_status`、`delivery_result_claimed`、`evidence_ref`、`dropoff_confirmation_type`、`completed_at_utc` 和 `notes`/`metadata` 中的安全子集。
3. PC Node adapter 固定转发到本机 O6 delivery result evidence intake 路径，优先复用现有 `/api/o6/archive/field-evidence` 与 consumer detail `delivery_result_evidence` 合同。
4. O7 receipt 使用新 schema，例如 `trashbot.pc_tools_workstation.o7_consumer_delivery_result_intake_result.v1`。
5. UI 展示 receipt 摘要，但不把 local/mock delivery result 说成真实送达成功。
6. 文档同步说明接口、proof boundary 和拒绝证明范围。

## 非目标

- 不做真实 delivery success 认定。
- 不接 production cloud、production DB/queue、OSS/CDN 或真实手机/browser。
- 不执行 Nav2、底盘控制、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或 HIL。
- 不重复 query filters、readback-only wrapper、mission event append 或 inference request。

## 验收

- 成功路径：local/mock O6 receipt 后，O7 返回 `local_mock_delivery_result_written` 或 `local_mock_delivery_result_updated`。
- 失败路径：unsafe baseUrl、task mismatch、unsafe evidence/text、dangerous true field、O6 bad schema/false-field mismatch 都 fail closed，且不显示写入成功。
- Workstation tests/build/lint 通过，相关 docs 更新。

## 风险

- 本轮仍是 local/mock software proof，不会提升 O5 生产外部证据。
- 若 O6 现有 field-evidence 合同不适合单项 delivery result intake，可能需要把 scope 收窄为 O7 adapter 到现有 O6 field-evidence fixture contract，而不是新增大 O6 能力。
