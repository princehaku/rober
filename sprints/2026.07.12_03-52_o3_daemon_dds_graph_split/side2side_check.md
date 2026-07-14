# Side2Side Check - O3 Daemon/DDS Graph Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 04:11 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`
- Outcome: accepted as no-motion daemon/DDS graph root-cause split; no OKR percentage change.

## 用户价值和产品北极星

北极星仍是普通手机用户一键发车完成固定路线送垃圾。本轮价值不是送达本身，而是在进入路径生成、路线执行或 HIL 前，把 ROS2 graph/daemon/DDS/lifecycle 的现场盲区拆成下一条可执行命令，降低后续现场调试误判。

## 验收对照

| PRD / tech-plan 要求 | 本轮证据 | Product 判断 |
|---|---|---|
| 不能只复述 `ros2_node_list_timeout` | live artifact 新增 `daemon_dds_split.schema=trashbot.o10.daemon_dds_graph_split.v1`，并给出 `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout` | 接受 |
| 给出 split primary reason | `daemon_status_timed_out_and_daemon_reset_not_confirmed`，daemon status timeout 且 reset 未确认 | 接受 |
| 排除或保留 daemon/DDS/env/lifecycle/budget 候选 | `workspace_source_or_env_mismatch` 被 excluded；`ros2_cli_no_daemon_unsupported`、`managed_process_lifecycle_visibility_blocked`、`graph_command_budget_insufficient`、`dds_discovery_or_domain_mismatch` 保留为 remaining | 接受 |
| 保留 no-motion false fields | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | 接受 |
| 产出下一条 live command | artifact `next_live_command` 指向 daemon-safe stop/start + 8s `ros2 node list` / `ros2 topic list` readback | 接受 |

## Artifact 核对

核对对象：`sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/live_o10_daemon_dds_graph_split.raw.json`

关键事实：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.ros2_graph_timeout_root_cause.classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_timeout`
- `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout`
- `daemon_dds_split.primary_candidate.reason=daemon_status_timed_out_and_daemon_reset_not_confirmed`
- `daemon_dds_split.excluded_candidates[0].candidate=workspace_source_or_env_mismatch`
- `daemon_dds_split.excluded_candidates[0].reason=safe_env_summary_contains_ros_and_onboard_workspace`
- `daemon_dds_split.graph_budget_summary.commands.ros2_topic_list.boundary=ros2_topic_list_ok`
- `daemon_dds_split.graph_budget_summary.commands.ros2_daemon_status.boundary=ros2_daemon_status_timeout`
- `daemon_dds_split.graph_budget_summary.commands.ros2_node_list.boundary=ros2_node_list_timeout`
- `daemon_dds_split.graph_budget_summary.commands.ros2_node_list_no_daemon.boundary=ros2_node_list_no_daemon_timeout`
- `daemon_dds_split.graph_budget_summary.commands.ros2_node_list_help.boundary=ros2_node_list_help_timeout`
- `daemon_dds_split.daemon_command_summaries.reset_skipped=true`
- `daemon_dds_split.daemon_command_summaries.reset_skip_reason=ros2_node_list_help_not_ok`

## OKR 方向判断

- O5：继续约 `85%`，`不调整`。本轮没有真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external readback。
- O1：继续约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL pass 或 safe-to-control。
- O6/O7：继续约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- KR：`不归档`。没有完成 path generation / route execution / delivery / HIL / production KR。

## Product 验收结论

本轮满足最低接受条件：它没有停留在上一轮 `ros2_node_list_timeout` 复述，而是把 root cause 拆到 `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout`，并说明 `workspace_source_or_env_mismatch` 已由 safe env summary 排除，同时保留 DDS/domain、managed lifecycle visibility、graph budget 和 no-daemon capability 为 remaining candidates。

但本轮仍只是 O3/O1 supporting diagnostic delta，不是 path generation、route execution、delivery/operator acceptance、HIL、safe-to-control 或 production cloud evidence。OKR 百分比不调整，KR 不归档。

## 下一轮建议

下一轮先执行 artifact 的 `next_live_command` 等价动作：daemon-safe `ros2 daemon status; ros2 daemon stop; ros2 daemon start`，随后用 8s budget 读回 `ros2 node list` 与 `ros2 topic list`。只有 graph/lifecycle/localization ready 后，才回到 AMCL、TF 和 planner path gate；在此之前不得进入 motion/path、不得发送 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或打开 WAVE ROVER UART。
