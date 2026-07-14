# Final - O3 Daemon/DDS Graph Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 04:11 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`
- Outcome: accepted as daemon/DDS graph split; graph/lifecycle/localization remain blocked.

## 用户价值和产品北极星

用户价值是让现场调试从泛化 graph timeout 进入可执行修复命令。北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮只是进入 path generation、route execution 和 delivery 之前的 no-motion runtime diagnostic，不是送达闭环。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。本轮没有公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或 WAVE ROVER feedback delta。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 no-motion daemon/DDS graph recovery；`暂停` O5 support-only lane；`不归档` KR。

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

本轮核心抓手是把上一轮 `ros2_daemon_or_dds_graph_discovery_timeout` 继续拆成 daemon、DDS/domain/env、managed lifecycle visibility、graph command budget 和 no-daemon capability 候选。Robot Software 新增 additive `daemon_dds_split` 合同，并在 true-board artifact 中留下 primary、excluded、remaining 和下一条 live command。

Robot Software 实际改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/tech-done.md`
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/`

Product closeout 实际改动：

- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/side2side_check.md`
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot Software 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 93 tests in 2.235s OK`。
- local helper fail-closed dry-run exit `2`，写出 `local_o10_daemon_dds_graph_split.raw.json`。
- true-board SSH、helper push、remote no-motion helper run、artifact pull 均完成；remote helper exit `2`，符合 fail-closed blocked artifact 语义。
- scoped `git diff --check` 通过。

Product closeout 验收命令：

```bash
rg -n "03-52|daemon_dds_split|ros2_daemon_state_timeout|daemon_status_timed_out_and_daemon_reset_not_confirmed|ros2_topic_list_ok|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_03-52_o3_daemon_dds_graph_split
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_03-52_o3_daemon_dds_graph_split
```

## Live Artifact 结论

最终 live artifact：

- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/live_o10_daemon_dds_graph_split.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.ros2_graph_timeout_root_cause.classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_timeout`
- `proof.ros2_graph_timeout_root_cause.daemon_dds_split.schema=trashbot.o10.daemon_dds_graph_split.v1`
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

本轮满足 acceptance gate。它没有只重复 `ros2_node_list_timeout`，而是把上一轮 graph blocker 细分为 `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout`，并给出 `daemon_status_timed_out_and_daemon_reset_not_confirmed`。同时，safe env summary 已把 workspace/source/env mismatch 排除：ROS Humble、`which_ros2=/opt/ros/humble/bin/ros2`，`AMENT_PREFIX_PATH`、`PYTHONPATH`、`LD_LIBRARY_PATH` 均包含 ROS 与 onboard workspace。

仍需保守的是：`ros2 topic list` 本轮可完成到 `ros2_topic_list_ok`，但 `ros2 daemon status`、`ros2 node list`、`ros2 node list --no-daemon` 和 `ros2 node list --help` 都在 bounded budget 内 timeout；daemon reset 因 `reset_skip_reason=ros2_node_list_help_not_ok` 被跳过。因此 primary 只是 daemon state timeout 的当前候选，不是 graph/lifecycle/localization ready。

本轮不是：

- path generation success
- planner route execution success
- delivery/operator acceptance
- current live HIL pass
- production cloud success
- safe-to-control success

## Blocker 重复消费判断

本轮不按与 `02-51` 完全同一 blocker 重复消费处理。理由：

1. `02-51` 的主因停在 `ros2_daemon_or_dds_graph_discovery_timeout` / `ros2_node_list_timeout`。
2. `03-52` 新增了 daemon/DDS split，给出 primary `ros2_daemon_state_timeout`、excluded `workspace_source_or_env_mismatch` 和 remaining candidate 列表。
3. artifact 还给出下一条 daemon-safe stop/start + 8s graph readback command。

但下一轮如果不执行 daemon-safe reset/readback，而只是继续改 wrapper 或重复 graph timeout 文案，应视为接近同一 blocker 重复消费红线。

## 剩余风险

- daemon reset 尚未实际执行，reset 后 graph 是否恢复仍未证明。
- `ros2 node list --help` 本轮 5s timeout，而上一轮可完成，说明 board CLI latency 或 graph command budget 仍不稳定。
- managed runtime 已启动，但 lifecycle visibility 仍被 graph timeout 遮蔽，`/map_server`、`/amcl`、`/planner_server` 未完成可见性证明。
- AMCL、TF、path gate 仍未 ready；本轮没有 `path_generation_attempted=true` 或 `path_generated=true`。
- `/cmd_vel` topic 出现在 topic list 不等于运动执行；helper 没有发布 `/cmd_vel`，安全字段继续 false。

## 下一轮建议

下一轮继续 O3/O1 no-motion lane，由 `robot-software-engineer` 优先执行 artifact 的 `next_live_command` 等价动作：

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; ros2 daemon status; ros2 daemon stop; ros2 daemon start; timeout 8 ros2 node list; timeout 8 ros2 topic list'
```

先拿 daemon-safe stop/start + 8s graph readback，再回 AMCL/TF/path gate。graph/lifecycle/localization ready 前不得进入 motion/path，不得发送 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或打开 WAVE ROVER UART。
