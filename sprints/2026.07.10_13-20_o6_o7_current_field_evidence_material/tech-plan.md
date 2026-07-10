# O6/O7 Current Field Evidence Material Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 O5（约 85%）；次低是 O1（约 86%）；O6/O7 约 88%。
2. 本 sprint 不直接针对最低 O5。
3. 理由：O5 当前只能用真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence 推进；当前工作区没有这些材料，且最近多轮已经把 local/mock probe/readback 判定为不能继续计主 OKR 增量。O1 也缺真实同 run wheel raw L/R nonzero、operator/HIL 材料。为避免同一 blocker 连续消费，本轮转向 O6/O7 中仍可消费的准现场 current field evidence material。

## 接口设计

- Algorithm 新增 schema：`trashbot.current_field_evidence_material.v1`。
- O6 新增 schema：`trashbot.o6.current_field_evidence_material.v1`。
- O7 新增只读 consumer contract：`trashbot.pc_tools_workstation.o7_current_field_evidence_material.v1`。
- 证明边界：`software_proof_current_field_evidence_material_only`。

字段建议：

- `task_id`
- `source_schema`
- `status`
- `present_materials`
- `missing_materials`
- `camera_frame_observed`
- `radar_scan_observed`
- `map_material_observed`
- `nav2_no_motion_path_generated`
- `manual_gate_blocked_expected`
- `live_or_field_material_consumed`
- `current_field_evidence_ready_not_route_execution_proof`
- `blocked_reasons`
- `next_required_evidence`
- fixed false fields: `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`hil_pass=false`、`connects_cloud_production=false`

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/algorithm_worker_report.md`

O6 owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o6_worker_report.md`

O7 owner 可改：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/o7_worker_report.md`

Product closeout 可改：

- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/tech-done.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/side2side_check.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material/artifacts/product_worker_report.md`

## 验收命令

Algorithm:

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py
python3 -m unittest onboard.tests.test_field_route_evidence_manifest
```

O6:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
```

O7:

```bash
cd pc-tools/workstation && npm run test && npm run build && npm run lint
```

Final acceptance:

```bash
git diff --check
rg -n "current_field_evidence_material|software_proof_current_field_evidence_material_only" onboard docs pc-tools sprints/2026.07.10_13-20_o6_o7_current_field_evidence_material
```

## 证据边界

本轮消费的是已有真实上位机 current evidence smoke 的材料摘要。它不是 production cloud、不是真实 route execution、不是 delivery record、不是 operator confirmation、不是 WAVE ROVER HIL，也不允许打开任何控制能力。
