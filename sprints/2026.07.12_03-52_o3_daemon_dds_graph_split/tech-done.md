# Tech Done - O3 Daemon/DDS Graph Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/`
- Implementation owner: `robot-software-engineer`
- Completion time: `2026-07-12 04:08 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 在 source-amortized graph batch 中新增 daemon-safe retry 摘要合同 `trashbot.o10.daemon_safe_graph_retry.v1`。
  - 在 `proof.ros2_graph_timeout_root_cause` 下新增 additive `daemon_dds_split`，schema 为 `trashbot.o10.daemon_dds_graph_split.v1`。
  - split 候选固定为 `ros2_daemon_state_timeout`、`dds_discovery_or_domain_mismatch`、`workspace_source_or_env_mismatch`、`managed_process_lifecycle_visibility_blocked`、`graph_command_budget_insufficient`、`ros2_cli_no_daemon_unsupported`。
  - 新增 safe env/domain 摘要、daemon command summaries、graph budget summary、managed lifecycle visibility summary、`next_live_command` 和严格 no-motion evidence boundary。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 daemon/DDS split 回归测试，覆盖 daemon reset 未确认时 primary 为 daemon state timeout，以及 reset 成功但 graph retry 仍 timeout 时 primary 转向 DDS/domain。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 `daemon_dds_split` 的读取顺序、安全 env 摘要、daemon reset 解释方式和 no-motion 边界。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 fixed-route/no-motion closeout 中 daemon/DDS split 的读取顺序和剩余风险边界。
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/`
  - 写出 local fail-closed artifact：`local_o10_daemon_dds_graph_split.raw.json`。
  - 写出并拉回 true-board artifact：`live_o10_daemon_dds_graph_split.raw.json`。
  - 保存 true-board stdout：`live_o10_daemon_dds_graph_split.stdout.log`。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 93 tests in 2.235s OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/local_o10_daemon_dds_graph_split.raw.json
```

结果：本地 macOS 无 ROS2 环境，helper fail-closed exit `2`；artifact 写出 `status=blocked_with_root_cause`。本地 split primary 为 `workspace_source_or_env_mismatch`，reason 为 `board_source_preflight_cli_not_ready`，daemon reset 写明 `reset_skipped=true`、`reset_skip_reason=skipped_without_sourced_ros2_cli_ready`。

True-board no-motion helper：

- SSH 可达性：`ssh -p 37878 root@192.168.1.11 true` exit `0`。
- helper 推送：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`。
- 远端执行：`timeout 240s python3.10 scripts/o10_amcl_nav2_runtime_proof.py ... --output /root/rober/onboard/runtime/live_o10_daemon_dds_graph_split.raw.json` exit `2`。
- artifact 拉回：`scp -P 37878 root@192.168.1.11:/root/rober/onboard/runtime/live_o10_daemon_dds_graph_split.raw.json .../live_o10_daemon_dds_graph_split.raw.json` exit `0`。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_03-52_o3_daemon_dds_graph_split
```

结果：通过，无输出。

## Artifact 关键字段

True-board artifact：`sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/live_o10_daemon_dds_graph_split.raw.json`

- `proof.status=blocked_with_root_cause`
- `proof.ros2_graph_timeout_root_cause.classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.evidence_priority=source_amortized_batch`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.schema=trashbot.o10.daemon_dds_graph_split.v1`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.primary_candidate.candidate=ros2_daemon_state_timeout`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.primary_candidate.reason=daemon_status_timed_out_and_daemon_reset_not_confirmed`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.safe_environment_summary.ROS_DISTRO=humble`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.safe_environment_summary.ROS_DOMAIN_ID=null`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.safe_environment_summary.RMW_IMPLEMENTATION=null`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.safe_environment_summary.board_source_preflight.classification=board_source_preflight_ready`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.daemon_command_summaries.pre_reset_daemon_status.boundary=ros2_daemon_status_timeout`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.daemon_command_summaries.reset_skipped=true`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.daemon_command_summaries.reset_skip_reason=ros2_node_list_help_not_ok`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_topic_list.boundary=ros2_topic_list_ok`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list.boundary=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list_help.boundary=ros2_node_list_help_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.ros2_node_list_no_daemon.boundary=ros2_node_list_no_daemon_timeout`
- `proof.ros2_graph_timeout_root_cause.probes.rclpy_graph_segments.boundary=rclpy_graph_nodes_observed`

No-motion false fields confirmed in both local and live artifacts:

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

## 失败定位

本轮没有恢复 path generation；也没有 HIL、route execution、delivery 或 production evidence。

新的 root-cause split 比上一轮更窄：

- workspace/source/env 已由 safe summary 排除：ROS Humble、`which_ros2=/opt/ros/humble/bin/ros2`，`AMENT_PREFIX_PATH`、`PYTHONPATH`、`LD_LIBRARY_PATH` 都包含 ROS 与 onboard workspace。
- `ros2 topic list` 在同一 source-amortized batch 内完成，说明 graph 不是完全不可读。
- `ros2 daemon status` timeout，`ros2 node list` timeout，`ros2 node list --no-daemon` timeout，`ros2 node list --help` 在 5s bounded budget 内 timeout。
- daemon reset 被跳过不是遗漏：artifact 明确写 `reset_skip_reason=ros2_node_list_help_not_ok`。下一轮应先执行 `daemon_dds_split.next_live_command` 中的 daemon-safe stop/start + 8s node/topic/daemon readback，或提高 help/daemon status 预算复验。
- managed runtime 已启动，但 `managed_runtime_wait_result.reason=ros2_node_list_timeout`；lifecycle visibility 仍是 remaining candidate，不能把 skipped lifecycle 读成 inactive 强证明。

## 剩余风险

- 本轮仍是 no-motion runtime diagnostic，不是 OKR 可计分的 path generation、route execution、delivery/operator acceptance、HIL 或 production cloud evidence。
- `ros2 node list --help` 这次在 5s 内 timeout，上一轮同命令可完成；这说明 board CLI latency 仍抖动，`graph_command_budget_insufficient` 仍是 remaining candidate。
- daemon reset 尚未实际执行；primary candidate 是 `ros2_daemon_state_timeout`，但还没有 reset 后恢复或不恢复的实证。
- `/cmd_vel` topic 在 topic list 中可见，但本 helper 没有发布 `/cmd_vel`，artifact safety fields 保持 false；该 topic presence 不能被解释成运动执行。
- 仍需要 Product closeout 判断本轮是否只作为 O3/O1 supporting diagnostic delta 记录，OKR 百分比不应因本轮上调。

## 协同需求

- Product：需要按本 tech-done 做验收、OKR 判断、`side2side_check.md` / `final.md` 收口；建议不调整 O5/O1/O6/O7 百分比。
- Hardware：本轮未触碰 WAVE ROVER UART、底盘控制或硬件配置，暂不需要硬件介入。
- Autonomy：下一轮若 daemon-safe reset 后 graph 可读，应继续接回 AMCL/TF/path gate；若 reset 后仍 timeout，需要 Autonomy/Robot Software 共同判断 DDS/domain/RMW 参数。
- Full-Stack：无协同需求。
