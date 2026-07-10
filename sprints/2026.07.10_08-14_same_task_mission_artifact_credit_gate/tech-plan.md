# Same-Task Mission Artifact Credit Gate Tech Plan

## 目标

把 recent retrospective 里的 mission artifact hard gate 变成可测试合同：同一 `task_id` 的 mission evidence 只有在消费 live/field mission artifact delta 时才能 `okr_credit_allowed=true`；否则必须写明 `support_only_reason`，后续不能用 local/mock wrapper、probe、checklist 或 readback-only 工作提高 O5/O6/O7 百分比。

## OKR 最低优先级核对

1. `OKR.md` 4.1 当前活跃 O1/O5/O6/O7 均约 85%，并列最低。
2. 本 sprint 针对 O5/O6/O7 的共同最低缺口：same-task mission artifact 消费和 OKR credit 误判。
3. 不直接推进 O1 的理由：本地可见旧硬件材料仍显示 WAVE ROVER `T=1001` 的 L/R 为 0，不能补齐 O1 当前主要缺口“轮速非零原始反馈”；真实硬件重新接入前，本轮不继续消费该 blocker。

## 分工

### Robot Algorithm Engineer

文件范围：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/route_evidence_manifest.md`（如不存在可创建，记录 contract）

任务：

- 扩展 same-task mission gate 的 `mission_artifact_delta`，输出结构化字段：
  - `same_task_id_consumed`
  - `cloud_terminal_result_source_consumed`
  - `route_execution_readiness_consumed`
  - `route_delivery_closure_consumed`
  - `nonzero_pose_progress_consumed`
  - `live_or_field_command_executed`
  - `support_only_reason`
  - `okr_credit_allowed`
- `okr_credit_allowed` 只能在同一 `task_id` 且至少一种 live/field mission artifact 被消费时为 true；readback-only、probe-only 或 checklist-only 必须 false。
- 保持 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。

验收命令：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check
```

### Robot Software Engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`

任务：

- O6 same-task mission gate summary 接受 Algorithm 的结构化 `mission_artifact_delta`。
- O6 readback 输出 `same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`。
- 缺字段、unsafe text、dangerous true、task mismatch 或 support-only 输入必须 `okr_credit_allowed=false`。
- consumer detail/include 必须能回读这些字段。

验收命令：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check
```

### Full-stack Software Engineer

文件范围：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/**/*same*mission*`（若已有相关测试/fixture，仅限 same-task mission gate 相关文件）
- `docs/interfaces/o7_realtime_operator_console.md`

任务：

- O7 consumer detail 读取 O6 credit fields。
- UI/fixture 显示 `okr_credit_allowed` 与 `support_only_reason`，并在 false 时保留 support-only/blocked 语义。
- 不新增真实控制按钮或 delivery success 状态。

验收命令：

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check
```

### Product OKR Owner

文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/tech-done.md`
- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/side2side_check.md`
- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md`

任务：

- 汇总各 owner 验证结果。
- 写清本轮 OKR credit 是否允许百分比变化；若本轮只是 gate 硬化，则不要虚增 O5/O6/O7。
- 更新 progress log，明确下一轮必须带真实/准现场 mission artifact 才能继续提升。

验收命令：

```bash
test -f sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/tech-done.md
test -f sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/side2side_check.md
test -f sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md
rg -n "okr_credit_allowed|support_only_reason|mission_artifact_delta|same_task_id_consumed" OKR.md docs/process/okr_progress_log.md sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate
git diff --check
```

## 接口影响

- Algorithm manifest 和 O6/O7 readback 新增只读字段；不删除旧字段。
- `delivery_success`、`safe_to_control`、`primary_actions_enabled`、`robot_control_executed` 继续固定 false。
- 不改变任何硬件参数、launch 默认值或控制 endpoint。

## 风险

- 本轮是 gate 硬化，不等于真实 delivery success。
- 若没有真实/准现场新材料，本轮通常不应提高 OKR 百分比。
- O6/O7 当前可能把 `mission_artifact_delta` 当字符串消费；实现需要兼容旧字符串和新结构化对象。
