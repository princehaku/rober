# O6/O7 Clean Baseline Nav2 Path Material Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低 Objective 是 O5（约 85%）；次低是 O1（约 86%）；O6/O7 约 89%。
2. 本 sprint 不直接针对最低 O5，也不直接针对次低 O1。
3. 理由：O5 当前需要真实 production cloud、production DB/queue、4G/TLS 或 live endpoint evidence；本轮环境变量检查未发现可安全消费的 production/cloud/DB/queue/OSS/CDN endpoint。O1 当前需要真实同一 run 的 WAVE ROVER nonzero L/R、轮速方向和 HIL acceptance；工作区没有新的真实 nonzero L/R 证据。为避免同一 blocker 连续消费，本轮转向 O6/O7，消费已有准现场 clean-baseline Nav2 no-motion path proof，并明确它只是 route execution preflight material。

## 接口设计

- Algorithm 新增 schema：`trashbot.clean_baseline_nav2_path_material.v1`。
- O6 新增 schema：`trashbot.o6.clean_baseline_nav2_path_material.v1`。
- O7 新增只读 consumer contract：`trashbot.pc_tools_workstation.o7_clean_baseline_nav2_path_material.v1`。
- 证明边界：`software_proof_clean_baseline_nav2_path_material_only`。

建议字段：

- `task_id`
- `source_schema`
- `status`
- `first_attempt_status`
- `retry_status`
- `path_generation_succeeded`
- `path_generated`
- `path_point_count`
- `planner_server_active`
- `managed_runtime_started`
- `managed_runtime_cleanup_ok`
- `initialpose_published`
- `amcl_pose_observed`
- `map_server_active`
- `amcl_active`
- `cleanup_readback_clean`
- `blocked_reasons`
- `next_required_evidence`
- `material_sample_refs`
- fixed false fields: `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`connects_cloud_production=false`

## 文件范围

Algorithm owner 可改：

- `onboard/scripts/field_route_evidence_manifest.py`
- `onboard/tests/test_field_route_evidence_manifest.py`
- `docs/navigation/field_route_evidence_manifest.md`
- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/algorithm_worker_report.md`

O6 owner 可改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o6_worker_report.md`

O7 owner 可改：

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/artifacts/o7_worker_report.md`

Product closeout 可改：

- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/tech-done.md`
- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/side2side_check.md`
- `sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

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
rg -n "clean_baseline_nav2_path_material|software_proof_clean_baseline_nav2_path_material_only|2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material" onboard docs pc-tools sprints/2026.07.10_14-22_o6_o7_clean_baseline_nav2_path_material OKR.md docs/process/okr_progress_log.md
```

## 证据边界

本轮消费的是已有真实上位机 clean-baseline no-motion Nav2 path proof。它不是 production cloud，不是真实 route execution，不是 NavigateToPose/FollowPath/controller 执行，不是 delivery record，不是 operator confirmation，不是 WAVE ROVER HIL，也不允许打开任何控制能力。
