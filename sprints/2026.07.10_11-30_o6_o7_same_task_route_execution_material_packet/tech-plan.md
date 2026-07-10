# O6/O7 Same-Task Route Execution Material Packet Tech Plan

## 目标

新增 `same_task_route_execution_material_packet` 计划：在已有 `same_task_field_material_packet` 基础上，消费同一 `task_id` 的 route execution 相关材料，并形成 Algorithm producer -> O6 archive/readback -> O7 consumer/UI 的可验证软件证据链。

本阶段只产出 planning docs，不实现代码。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低 Objective：O5 约 `85%`；O1、O6、O7 约 `86%`。
2. 本 sprint 不直接针对绝对最低 O5，而是转向 O6/O7。
3. 不继续 O5 的理由：最近 final 已明确 O5 只能用真实 production cloud、production DB-queue external probe 或 live endpoint evidence 继续计 OKR；当前环境没有这些外部材料，继续 local/mock probe/readback 会违反 `same_task_mission_artifact_credit_gate` 的 support-only 不加分规则。
4. 不继续 O1 的理由：O1 下一步必须消费同一真实 run 的 `feedback_T1001.log`、motion command、operator report、HIL acceptance record；当前环境没有这些硬件/HIL 材料，继续软件 gate wrapper 不应计入主进度。
5. 选择 O6/O7 的理由：已有/准现场 same-task field materials 可进一步和 route execution result、pose progress、replay timeline 绑定，生成比 checklist/readback wrapper 更接近任务履约的 route execution material packet。

## Owner Split

### Robot Algorithm Engineer

- 负责 producer：`trashbot.same_task_route_execution_material_packet.v1`。
- 输入来源：已有 `same_task_field_material_packet`、route execution result JSON/JSONL、Nav2 goal/result、route bag / rosbag、pose progress replay、route replay JSONL。
- 输出位置：manifest 顶层，以及必要时嵌入 `field_motion_evidence_packet.same_task_route_execution_material_packet`。
- 验收重点：同一 `task_id` 校验、材料摘要、unsafe input fail-closed、固定 false flags。

### Robot Software Engineer / O6

- 负责 archive/readback 合同：`trashbot.o6.same_task_route_execution_material_packet.v1`。
- 支持写入、archive detail、field evidence、artifact bundle、consumer detail 顶层 alias 和 `include=same_task_route_execution_material_packet`。
- O6 是合同源；O7 readiness 只能信 O6 顶层 status。
- 验收重点：safe sanitizer、shape 对齐、task mismatch fail-closed、raw/base64/path/token/url 不回显。

### Full-Stack Software Engineer / O7

- 负责 consumer adapter、contract type、fixture 和 UI 摘要。
- UI 必须展示 packet 自身状态、present/missing route execution materials、blocked reasons、next required evidence、fixed false flags。
- Checklist 可以引用 packet，但不能把 checklist item 当作 packet 验收。
- 验收重点：兼容 O6 顶层 alias、default include 或显式 include、TS build/lint/test 全通过。

### Product / OKR Owner

- 当前阶段创建 planning docs。
- 实现完成后负责 `tech-done.md`、`side2side_check.md`、`final.md`、OKR 判断和历史归档建议。
- 本阶段禁止修改 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## Interface Field Draft

### Algorithm schema

Schema name：`trashbot.same_task_route_execution_material_packet.v1`

建议字段：

- `schema`
- `task_id`
- `run_id`
- `source`
- `source_schema`
- `status`: `route_execution_material_ready_not_delivery_proof` 或 `blocked_not_proven`
- `evidence_boundary`: `software_proof_same_task_route_execution_material_packet_only`
- `same_task_id_consumed`
- `same_task_field_material_packet_status`
- `route_execution_material_consumed`
- `route_execution_result_status`
- `nav2_goal_execution_status`
- `pose_progress_replay_status`
- `route_replay_jsonl_status`
- `route_bag_or_rosbag_status`
- `map_yaml_status`
- `route_csv_status`
- `keyframe_material_status`
- `material_summaries`
- `material_sample_refs`
- `blocked_reasons`
- `next_required_evidence`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `hil_pass=false` 如涉及硬件安全语义

### O6 schema

Schema name：`trashbot.o6.same_task_route_execution_material_packet.v1`

O6 可保留字段：

- `schema`
- `task_id`
- `status`
- `evidence_boundary`
- `same_task_id_consumed`
- `route_execution_material_consumed`
- `source_sections`
- `material_summaries`
- `material_sample_refs`
- `blocked_reasons`
- `next_required_evidence`
- fixed false flags

O6 必须丢弃或降级：

- raw ROS payload
- base64 blob
- absolute path
- credential-like URL
- token / secret / connection string
- traceback / response body
- dangerous true fields such as `safe_to_control=true`、`delivery_success=true`、`robot_control_executed=true`

### O7 consumer shape

O7 可展示：

- Packet title/status。
- Same-task identity。
- Present/missing materials。
- Route execution result summary。
- Pose progress/replay timeline summary。
- Blocked reasons。
- Next required evidence。
- Fixed false flags。

O7 不得派生：

- 不得从 child material ready 推导 top-level delivery success。
- 不得从 packet ready 推导 `safe_to_control=true`。
- 不得把 checklist complete 当成 route execution proof。

## Proposed File Scope For Implementation

### Algorithm

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/artifacts/algorithm_worker_report.md`

### O6

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/artifacts/o6_worker_report.md`

### O7

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/artifacts/o7_worker_report.md`

### Product closeout

- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/tech-done.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/side2side_check.md`
- `sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Acceptance Commands For Implementation

Algorithm worker:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
git diff --check -- onboard/scripts/field_route_evidence_manifest.py onboard/tests/test_field_route_evidence_manifest.py docs/navigation/field_route_evidence_manifest.md sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
```

O6 worker:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
```

O7 worker:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
```

Product / main acceptance after implementation:

```bash
rg -n "same_task_route_execution_material_packet|route_execution_material|route_execution|okr_credit_allowed|software_proof_same_task_route_execution_material_packet_only" OKR.md docs/process/okr_progress_log.md docs/interfaces docs/navigation docs/product pc-tools/workstation onboard sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
git diff --check
```

## Planning-Stage Validation Commands

本阶段只允许运行：

```bash
test -f sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/pre_start.md && test -f sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/prd.md && test -f sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|O6|O7|route_execution|same_task|software_proof" sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
git diff --check -- sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet
```

## Risk Boundary

- 本 sprint 的目标是 `software_proof_same_task_route_execution_material_packet_only`。
- 不证明真实 production cloud、production DB/queue、多实例一致性、HTTPS/TLS、4G/SIM、OSS/CDN live traffic。
- 不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success。
- 不证明 hardware safety、WAVE ROVER nonzero L/R、wheel direction、HIL pass。
- 若 implementation 阶段只能完成 producer 或 O6/O7 之一，必须在 `tech-done.md` 中标记 chain incomplete，不得调高 OKR。

## Next Sprint Docs

实现阶段完成后必须补齐：

- `tech-done.md`：实际改动、验证结果、偏差和剩余风险。
- `side2side_check.md`：对照本 PRD/tech-plan 的验收矩阵。
- `final.md`：OKR 方向判断、是否调进度、KR 是否归档、下一轮建议。
