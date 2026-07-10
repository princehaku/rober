# Route Evidence Manifest Credit Gate

本页只记录 `onboard/scripts/field_route_evidence_manifest.py` 里 `same_task_mission_evidence_gate` 的 OKR credit 合同，不展开其他 artifact intake 细节。

## same-task mission gate credit 判定

`same_task_mission_evidence_gate` 除了原有 `mission_artifact_delta` 外，本轮还固定输出以下字段：

- `same_task_id_consumed`
- `live_or_field_command_executed`
- `support_only_reason`
- `okr_credit_allowed`

它们也会镜像出现在 `mission_artifact_delta` 内，便于 O6/O7 直接消费同一份合同。

## allow 条件

只有同时满足以下条件时，才允许 `okr_credit_allowed=true`：

1. `same_task_mission_gate_ready=true`
2. `same_task_id_consumed=true`
3. `live_or_field_command_executed=true`
4. `safe_to_control=false`
5. `delivery_success=false`
6. `primary_actions_enabled=false`
7. `robot_control_executed=false`

当前 `live_or_field_command_executed=true` 的保守判定只接受明确 live/field 运动材料：

- `motion_log_summary.live_motion_evidence_present=true`，或
- `motion_log_summary.live_nav2_log_present=true`，或
- `route_bag_or_live_nav2_log.source=live_motion_log`

这表示本轮确实消费了 live/field command 侧 mission artifact delta，而不只是同 task 的只读摘要闭合。

## deny 条件

以下输入一律保持 `okr_credit_allowed=false`，并给出 `support_only_reason`：

- `task_id` 不一致或缺失：`same_task_id_mismatch_or_missing`
- gate 自身未 ready：`same_task_mission_gate_not_ready`
- `probe` 类 same-task 材料：`probe_only_same_task_artifacts`
- `checklist` 类 same-task 材料：`checklist_only_same_task_artifacts`
- `readback` 类 same-task 材料：`readback_only_same_task_artifacts`
- `local/mock/unit/fixture` 类 same-task 材料：`local_or_mock_same_task_artifacts_only`
- 没有明确 live/field delta：`live_or_field_mission_artifact_delta_missing`

## 边界

即使 `okr_credit_allowed=true`，该 gate 仍然只证明“同一 `task_id` 且消费了 live/field mission artifact delta 的软件合同成立”，不证明：

- 真实 delivery success
- `safe_to_control=true`
- `primary_actions_enabled=true`
- `robot_control_executed=true`
- production cloud / production DB / queue / TLS / 4G 已完成

因此 `same_task_mission_gate_ready_not_success_proof` 仍然只是 ready-not-success proof。
