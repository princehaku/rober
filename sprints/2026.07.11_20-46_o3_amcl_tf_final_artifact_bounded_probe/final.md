# O3 AMCL TF Final Artifact Bounded Probe Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: 2026-07-11
- Outcome: O3/O1 supporting no-motion bounded final artifact progress; localization/TF gate remains blocked

## 用户价值和产品北极星

本轮让真实板 no-motion 链路从上一轮 source/CLI partial material 推进到 AMCL、TF 和 path gate 的 final root-cause artifact。它服务于固定路线送垃圾的北极星：先证明同轮定位和 planner-only path readiness，再进入 route execution、delivery/operator acceptance 和 production evidence。

## OKR 映射和方向判断

- O5：保持约 `85%`。O5 仍是最低 Objective，但缺真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 和真实手机/browser 证据；本轮继续 O3/O1 的理由仍成立。
- O1：保持约 `93%`。本轮是 AMCL/TF/path readiness supporting evidence，不是 current same-run path generation success、Nav2 route execution success 或 current live HIL pass。
- O6/O7：保持约 `93%`。本轮没有新的 route execution、delivery record、operator confirmation 或 production readback material 可消费。
- 方向判断：`继续` O3/O1 no-motion localization/path readiness；`暂停` O5 support-only 包装；`不调整` 百分比；`不归档` KR。

## 实际改动

Algorithm owner 已完成并记录在 `tech-done.md`：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/tech-done.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/local_o10_amcl_tf_final_artifact_bounded_probe.raw.json`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json`

Product closeout 本轮新增或同步：

- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/side2side_check.md`
- `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` exit `0`，`Ran 69 tests in 2.210s OK`
- local helper exit `2`，按预期 fail-closed 并写 artifact
- `scp` exit `0`
- live helper SSH exit `255` / manual interrupt；拉回 final artifact exit `0`
- artifact invariant check exit `0`，输出 `artifact_invariants_ok`
- documentation `rg` 与 scoped `git diff --check` exit `0`

Product closeout 额外执行并记录在最终回复：

```bash
rg -n "20-46|amcl_readiness_summary|tf_readiness_summary|path_generation_gate|board_source_preflight_ready|ros2_cli_ok=true|rclpy_import_ok=true|amcl_lifecycle_not_active|map_to_odom_dynamic_source_missing|path_generated=false|safe_to_control=false|route_execution_success=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe
```

## Live Artifact 结论

`artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json` 已是 final root-cause artifact：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `board_source_preflight.classification=board_source_preflight_ready`
- `ros2_cli_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `map_server_active=false`
- `amcl_active=false`
- `amcl_readiness_summary.ready=false`
- `/amcl` lifecycle readback 为 `inactive [2]`
- `/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`
- `/amcl_pose` sample observed 但 stale，`age_ms=85437`
- `tf_readiness_summary.ready=false`
- `map_to_odom_dynamic.observed=false`
- `map_to_base_link.observed=false` 且 blocked by `map_to_odom`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`
- `planner_server_ready_for_path_generation=true`

Root causes：

- `map_lifecycle_proof_not_clean`
- `map_server_lifecycle_not_active_during_preflight`
- `amcl_lifecycle_not_active_during_preflight`
- `map_server_lifecycle_not_active`
- `amcl_lifecycle_not_active`
- `/scan_reliable_and_best_effort_timeout`
- `/map_once_not_observed`
- `cli_initialpose_publish_failed`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

Safety/no-motion invariants：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## Blocker 重复消费判断

19-46 已把旧 source/CLI blocker 修到 `board_source_preflight_ready`，并证明 `ros2_cli_ok=true`、`rclpy_import_ok=true`。20-46 live artifact 继续保持这些 ready 字段，同时把结论推进到 AMCL lifecycle inactive、stale `/amcl_pose`、dynamic `map->odom` missing 和 localization/TF gate not ready。因此本轮没有重复消费旧 source/CLI blocker，也不触发同一 blocker 第三轮升级。

## KR 拆解、更新或历史归档

本轮不归档任何 KR。原因是已经完成的是 bounded final artifact diagnosis，不是 KR 终态证据：

- 没有 current same-run `path_generated=true`
- 没有 Nav2 route execution success
- 没有 delivery record 或 operator acceptance
- 没有 current live HIL pass
- 没有 production cloud external evidence
- 没有 O6/O7 可消费的新 route/delivery/operator/production material

当前推进区继续保留 O1 path generation / route execution / HIL 缺口、O5 production external evidence 缺口、O6/O7 current live route/delivery/operator/production material 缺口。

## 剩余风险和下一轮建议

剩余风险：

- `/amcl` lifecycle inactive；
- `/scan` dual-QoS timeout；
- `/map_once_not_observed`；
- `cli_initialpose_publish_failed`；
- dynamic `map->odom` missing；
- remote SSH helper still needs natural-return cleanup。

下一轮建议继续由 `robot-algorithm-engineer` 单线闭环：先让 `/amcl` lifecycle clean active，并同时恢复 `/scan`、`/map` 与 `/amcl_pose` freshness；只有 localization/TF gate ready 后，再让 planner-only `ComputePathToPose` 进入 attempted/generated。继续保持 no-motion，不发布 `/cmd_vel`、不调用 `/api/base/manual`、不发送 NavigateToPose、不打开 WAVE ROVER UART。
