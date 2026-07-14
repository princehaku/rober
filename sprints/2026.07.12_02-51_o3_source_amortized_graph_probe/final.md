# Final - O3 Source-Amortized Graph Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout time: `2026-07-12 03:16 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`
- Outcome: accepted as measurement-layer correction; graph discovery remains blocked.

## 用户价值和产品北极星

用户价值是减少下一轮现场调试的误判：上一轮把 `ros2 node list --help` 和 rclpy graph segment timeout 当成 CLI/plugin/import 主因，但本轮证明 per-command source overhead 污染了旧结论。北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮只是进入 path/route 前的 no-motion runtime diagnostic，不是送达闭环。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。O5 仍缺真实 production/external evidence；本轮没有公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external readback。
- O1：保持约 `93%`，`不调整`。本轮只修正 O3/O1 no-motion graph measurement layer；没有 current same-run path generation success、Nav2 route execution success、current live HIL pass 或 safe-to-control。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 no-motion graph / daemon / DDS / lifecycle recovery；`暂停` O5 support-only lane；`不归档` KR。

## KR 拆解、更新或历史归档

本轮 `不归档` 任何 KR。

原因：

- `path_generation_attempted=false`
- `path_generated=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- 没有 production cloud / external evidence
- 没有新的 route/delivery/operator acceptance material

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据只作为 O3/O1 supporting diagnostic delta 记录在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` Key Results 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手和实际结果

本轮核心抓手是把 root-cause probes 改成 source-amortized batch：同一次 sourced shell 中批量执行 graph commands 和 rclpy stage stream，避免每条 probe 反复 source ROS/workspace 导致 timeout 误判。

Algorithm owner 实际改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/tech-done.md`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/`

Product closeout 实际改动：

- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/side2side_check.md`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 91 tests in 2.249s OK`。
- local helper fail-closed dry-run exit `2`，写出 `local_o10_source_amortized_graph_probe.raw.json`。
- scoped `git diff --check` 通过。

Product closeout 验收命令：

```bash
rg -n "02-51|source_amortized_batch|ros2_daemon_or_dds_graph_discovery_timeout|ros2_node_list_help_ok|rclpy_graph_nodes_observed|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_02-51_o3_source_amortized_graph_probe
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_02-51_o3_source_amortized_graph_probe
```

## Live Artifact 结论

最终 live artifact：

- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- `proof.ros2_graph_timeout_root_cause.classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.evidence_priority=source_amortized_batch`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.boundary=source_amortized_batch_completed`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.source_stage.elapsed_ms≈5984`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list_help.boundary=ros2_node_list_help_ok`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list.boundary=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_topic_list.boundary=ros2_topic_list_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.rclpy_graph_stage_stream.boundary=rclpy_graph_nodes_observed`
- rclpy graph node count: `21`

No-motion 字段继续固定：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## Product Judgment

本轮修正了上一轮测量层：旧 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout` 被 source-amortized evidence 取代。`ros2 node list --help` 已可完成，rclpy graph stage stream 已观察到 21 个 node，因此旧的 CLI/plugin/import 主因被 superseded。

新的主因是 `ros2_daemon_or_dds_graph_discovery_timeout` / `ros2_node_list_timeout`。managed lifecycle 和 TF 仍是 secondary remaining candidates，不能升级为 path generation 或 delivery 证据。

本轮不是：

- path generation success
- planner route execution success
- delivery/operator acceptance
- current live HIL pass
- production cloud success
- safe-to-control success

## Blocker 重复消费判断

本轮不按与 `01-50` 完全同一 blocker 重复消费处理。理由：

1. `01-50` 的主因是 `ros2_cli_plugin_or_import_timeout` / `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`。
2. `02-51` 已通过 source-amortized batch 证明 `ros2_node_list_help_ok` 和 `rclpy_graph_nodes_observed`，排除了旧测量口径。
3. 当前 blocker 已移动到 daemon/DDS graph discovery timeout 与 managed lifecycle/TF secondary。

但下一轮如果仍只重复 `ros2_node_list_timeout`，没有进一步拆出 daemon/DDS/lifecycle/env 的具体 root cause，也没有恢复 graph readback 或 localization gate，应视为接近同一 blocker 重复消费红线。

## 剩余风险

- true-board `ros2 node list` / `ros2 topic list` 仍 timeout，ROS2 graph readback 不稳定。
- managed process lifecycle readiness、map_server / AMCL 状态和 TF visibility 未恢复。
- `path_generation_attempted=false` 与 `path_generated=false` 表明 O1 current same-run path generation success 仍未发生。
- 没有 HIL、safe-to-control、delivery/operator acceptance 或 production cloud evidence。

## 下一轮建议

继续留在 O3/O1 no-motion lane。下一轮由 `robot-algorithm-engineer` 优先定位 `ros2_daemon_or_dds_graph_discovery_timeout`：区分 ROS2 daemon lifecycle、DDS discovery/domain/env mismatch、managed process lifecycle visibility 和 graph command budget。只有 graph/lifecycle/localization gate ready 后，才允许进入 planner-only path attempt；在此之前不得发送 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或打开 WAVE ROVER UART。
