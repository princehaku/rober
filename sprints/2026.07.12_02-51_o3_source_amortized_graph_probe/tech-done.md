# Tech Done - O3 Source-Amortized Graph Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/`
- Owner: `robot-algorithm-engineer`
- Closeout time: `2026-07-12 03:08 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## 自主能力目标和本轮抓手

目标是修正 O3/O1 no-motion graph timeout root-cause probe 的测量口径。上一轮每条 root-cause probe 都通过 `run_ros()` 重新 source ROS/workspace；当 source 阶段约 5 秒、单条 probe timeout 只有 2 到 5 秒时，旧 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout` 可能被 source overhead 污染。

本轮抓手是新增 source-amortized batch：同一次 sourced shell 内批量执行 `ros2 node list`、`ros2 node list --no-daemon`、`ros2 daemon status`、`ros2 node list --help`、`ros2 topic list`、workspace env summary 和 rclpy graph stage stream，并让 root-cause classifier 优先使用 `source_amortized_batch`。

## 实际改动文件和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `source_amortized_graph_probe_batch_command()`、JSONL parser、batch-to-legacy probe 回填和 source-amortized classifier priority。
  - 修复 live 返工发现的 circular reference：final JSONL 自身不再进入 `events_observed`。
  - Artifact schema additive 新增 `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch`、`evidence_priority` 和 `evidence_boundary.source_amortized_batch_used`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 source-amortized partial stage timeout、final payload JSON serializable、daemon/DDS priority、CLI/plugin startup-stage gating 回归测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 说明旧 per-command probe timeout 会包含 source overhead，并明确 source-amortized 字段读取顺序。
- `docs/navigation/fixed_route_workflow.md`
  - 更新 fixed-route/no-motion closeout 顺序，优先读 `evidence_priority` 和 `probes.source_amortized_batch`。
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/local_o10_source_amortized_graph_probe.raw.json`
  - 本地 fail-closed dry-run artifact。
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`
  - 真板第一轮异常退出前拉回的 partial artifact，不作为完成证据。
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.stdout.log`
  - 真板第一轮异常退出 traceback。
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.incomplete.json`
  - live evidence 未完成的 fail-closed 摘要。

接口影响：无 CLI 运动入口新增；无 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或底盘配置改动。新增字段为 additive，旧 `probes.ros2_node_list`、`probes.workspace_environment`、`probes.rclpy_graph_segments` 仍保留，但由 batch 结果回填。

## 实现内容

- source-amortized batch 只 source 一次 ROS/workspace，然后在同一环境里分别给每条 ROS2 子命令设置自己的 timeout。
- rclpy graph probe 改成 stage stream，记录 `import_rclpy`、`rclpy_init`、`create_node`、`graph_wait` 的 started/completed 边界；外层 timeout 时也能用已 flush JSONL 还原 `last_started_stage` 和 `last_completed_stage`。
- classifier 现在显式输出 `evidence_priority=source_amortized_batch`。只有 batch 中 help 仍 timeout，且 rclpy stage stream 卡在 import/init/create_node 前段时，才继续主判 `ros2_cli_plugin_or_import_timeout`。
- 如果 batch 中 `ros2 node list --help` 成功，而 node/topic/daemon graph timeout，则优先判 `ros2_daemon_or_dds_graph_discovery_timeout` 或 managed lifecycle remaining candidate，不再把 `/tf_topic_missing` 提升成主因。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：退出码 `0`，无输出。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：

```text
Ran 91 tests in 2.249s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/local_o10_source_amortized_graph_probe.raw.json
```

结果：退出码 `2`，按 macOS 本地无 ROS 环境 fail-closed 写出 artifact。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_02-51_o3_source_amortized_graph_probe
```

结果：退出码 `0`，无 whitespace error。

## 本地 Artifact 关键字段

文件：`sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/local_o10_source_amortized_graph_probe.raw.json`

- `status=blocked_with_root_cause`
- `proof.artifact_closeout.artifact_kind=final`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_source_failed`
- source-amortized 字段位置：`proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch`
- 本地字段值：`boundary=skipped_without_sourced_ros2_cli_ready`、`executed=false`、`reason=board_source_preflight_source_failed`
- 本地 `evidence_priority=legacy_per_command_probes`，原因是 macOS 本机没有 `/opt/ros/humble/setup.bash`，source preflight 未到 `cli_ready=true`，batch 按设计跳过。

no-motion false fields：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generated=false`
- `path_generation_attempted=false`

## Live Evidence 状态

返工 bounded closeout 先检查远端第二轮 helper 状态，发现远端已经写出自然 final artifact；随后直接 scp 回本 sprint：

- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.stdout.log`

Live final 关键字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.artifact_closeout.artifact_kind=final`
- `proof.artifact_closeout.current_command=null`
- `proof.artifact_closeout.last_phase=final`
- `proof.ros2_graph_timeout_root_cause.classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.evidence_priority=source_amortized_batch`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.boundary=source_amortized_batch_completed`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.source_stage.elapsed_ms=5984`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list.boundary=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list_help.boundary=ros2_node_list_help_ok`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_topic_list.boundary=ros2_topic_list_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.rclpy_graph_stage_stream.boundary=rclpy_graph_nodes_observed`
- `proof.ros2_graph_timeout_root_cause.probes.source_amortized_batch.rclpy_graph_stage_stream.node_names` count = `21`

Live final remaining candidates:

- `managed_process_lifecycle_not_ready`: `process_started_but_lifecycle_or_expected_nodes_not_proven_ready`
- `tf_runtime_secondary_after_graph_blocked`: `/tf_topic_missing_recorded_as_secondary_readback_after_graph_blocked`

no-motion false fields in live final：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generated=false`
- `path_generation_attempted=false`

`live_o10_source_amortized_graph_probe.incomplete.json` 已更新为 `superseded_by_final_live_artifact`，仅保留前一轮异常退出的历史说明，不再作为本 sprint 主证据。

## 失败定位

已修复的失败：source-amortized batch parser 在 final JSONL 场景下形成循环引用，导致 partial writer `json.dumps(..., sort_keys=True)` 抛 `ValueError: Circular reference detected`。修复方式是把 `source_amortized_batch_final` 事件排除在 `events_observed` 之外，并新增 JSON serializable 回归测试。

返工后 live final 已确认。当前 live root cause 不再是旧的 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`；source-amortized batch 证明 help 和 rclpy graph stage stream 可完成，但 `ros2 node list`、`ros2 topic list` 等 graph command 在各自 command timeout 内仍 timeout，因此主因收敛为 `ros2_daemon_or_dds_graph_discovery_timeout` / `ros2_node_list_timeout`。

## 剩余风险和下一步

- Live final 仍是 no-motion runtime diagnostic，不证明 path generation、route execution、HIL、delivery/operator acceptance 或 production evidence。
- 下一轮应围绕 `ros2_daemon_or_dds_graph_discovery_timeout` 继续拆 daemon/DDS graph discovery 与 managed lifecycle visibility；不要回到 per-command source-overhead 污染的旧 reason。
- OKR 百分比不应调整；本轮是测量口径修复和本地/单元验证，不是 path generation、route execution、HIL、delivery/operator acceptance 或 production evidence。
