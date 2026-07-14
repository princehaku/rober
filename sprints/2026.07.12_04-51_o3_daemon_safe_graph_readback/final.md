# Final - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 06:05 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`
- Outcome: accepted as helper-preflight repair plus manual graph readback delta; localization and path gates remain blocked.

## 用户价值和产品北极星

用户价值是把现场调试从“graph timeout 可能还在 daemon 层”推进到“helper 当前卡在 source/CLI preflight，但手工 daemon-safe 命令已经恢复 graph 可见性，下一跳该回到 lifecycle/localization gate”。北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮只是进入 path generation、route execution 和 delivery 之前的 no-motion runtime diagnostic，不是送达闭环。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。本轮没有 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control、底盘反馈增量或真实控制执行。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 no-motion runtime recovery；`暂停` O5 support-only lane；`不归档` KR。

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

本轮核心抓手是把上一轮建议的 daemon-safe stop/start + 8s graph readback做成可验收的 same-run 事实，同时修掉 helper 的一个低风险超时边界误判。

Robot Software 实际改动已经在 `tech-done.md` 记录，Product 收口确认的关键结果是：

1. helper 修正把 `SOURCE_PREFLIGHT_TIMEOUT_S` 提到 `12.0`，并通过 targeted unittest `Ran 94 tests in 2.238s OK` 与 scoped `git diff --check`。
2. 修正后的 latest helper artifact 仍 fail-closed：`proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`，`proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`，`primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout`，`daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`，`daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`。
3. manual same-run strict no-motion 命令序列成功，且被接受为本轮 live readback delta：`ros2 daemon status/stop/start`、`timeout 8 ros2 node list`、`timeout 8 ros2 topic list` 均 `RC=0`，graph 中观测到 `/amcl`、`/planner_server`、`/scan`、`/map`、`/tf`、`/tf_static`。

Product closeout 实际改动：

- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/side2side_check.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot Software 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 94 tests in 2.238s OK`。
- true-board helper 复跑后 latest artifact 仍为 fail-closed blocked result。
- scoped `git diff --check` 通过。

Product closeout 验收命令：

```bash
rg -n "04-51|daemon_safe_graph_readback|manual_daemon_safe_graph_readback_recovered_graph_visibility|board_source_preflight_ros2_cli_which_timeout|workspace_source_or_env_mismatch|skipped_without_sourced_ros2_cli_ready|Ran 94|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback
```

## Live Artifact 结论

helper latest artifact：

- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_o10_daemon_safe_graph_readback.raw.json`

关键字段：

- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`
- `proof.board_source_preflight.source_stage_timeout_s=12.0`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout`
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`
- `daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`

manual accepted live delta：

- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_daemon_safe_graph_readback_manual.summary.json`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_daemon_safe_graph_readback_manual.stdout.log`

关键字段：

- `primary_conclusion=manual_daemon_safe_graph_readback_recovered_graph_visibility`
- `ros2 daemon status` `RC=0`
- `ros2 daemon stop` `RC=0`
- `ros2 daemon start` `RC=0`
- `timeout 8 ros2 node list` `RC=0`
- `timeout 8 ros2 topic list` `RC=0`
- observed nodes 包含 `/amcl`、`/planner_server`
- observed topics 包含 `/amcl_pose`、`/map`、`/scan`、`/tf`、`/tf_static`

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

本轮满足 acceptance gate，但结论必须保守：

- helper 仍没有结构化证明 daemon-safe graph readback 已恢复；它只证明旧 `board_source_preflight_source_timeout` 已被更窄的 `board_source_preflight_ros2_cli_which_timeout` 取代。
- manual same-run strict no-motion readback 已经证明现场 daemon-safe graph visibility 可以恢复，因此当前主问题不再是“graph 本身完全不可读”，而是 helper 的 source/CLI preflight 仍有时序或预算漂移。

因此本轮不是：

- path generation success
- planner route execution success
- delivery/operator acceptance
- current live HIL pass
- production cloud success
- safe-to-control success

## Blocker 重复消费判断

本轮不按与 `03-52` 完全同一 blocker 重复消费处理。理由：

1. `03-52` 的主因是 `daemon_status_timed_out_and_daemon_reset_not_confirmed`，下一条动作是 daemon-safe stop/start + 8s graph readback。
2. `04-51` 实际执行后，manual same-run graph readback 已成功，说明 graph visibility 不是旧层面的纯 daemon state timeout。
3. latest helper blocker 已移动到 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`，下一轮动作也已经变成 source + path lookup + CLI invocation 的同 shell amortization。

但下一轮如果不修 helper preflight，只继续包装 manual readback 或回到 O5 support-only，应视为接近同一 blocker 重复消费红线。

## 剩余风险

- helper 仍 blocked 在 source/CLI preflight，最新 artifact 还不是可消费的 structured graph recovery proof。
- manual readback 虽然成功，但还没有把同样的结果稳定落到 helper artifact 主路径。
- 本轮仍没有 `/map_server` active、`/amcl_pose` fresh sample、dynamic `map->odom`、same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence。
- `/cmd_vel` 只在 topic graph 中可见，不代表发布过运动命令；所有危险字段仍必须保持 false。

## 下一轮建议

下一轮继续 O3/O1 no-motion lane，由 `robot-software-engineer` 先修 helper source/CLI preflight：把 source、`command -v/which/type -a ros2` 与 `ros2 --help` 或目标 CLI invocation 放进同一个 amortized shell，消掉 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`。helper graph readback 稳定后，再回 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate；在此之前不得发送 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或打开 WAVE ROVER UART。
