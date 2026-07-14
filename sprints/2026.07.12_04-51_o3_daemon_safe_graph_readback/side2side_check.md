# Side2Side Check - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 06:05 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`
- Outcome: accepted as no-motion diagnostic delta only; helper remains blocked, manual same-run readback accepted.

## 用户价值和产品北极星

北极星仍是普通手机用户一键发车完成固定路线送垃圾。本轮用户价值不是证明送达，而是把 daemon-safe graph readback 的现场事实分成两层：helper 当前为什么还不能稳定结构化复现，手工 same-run 严格 no-motion 命令序列又已经恢复了哪些 graph 可见性。

## 验收对照

| PRD / tech-plan 要求 | 本轮证据 | Product 判断 |
|---|---|---|
| helper 修正后必须重新给出 live artifact 边界 | `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`，`proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`，`primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout` | 接受 |
| 不能把 helper blocked 包装成 graph 已结构化恢复 | `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`，`daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed` | 接受 |
| manual same-run daemon-safe readback 要单独保留为 live delta | `primary_conclusion=manual_daemon_safe_graph_readback_recovered_graph_visibility`，`ros2 daemon status/stop/start`、`timeout 8 ros2 node list`、`timeout 8 ros2 topic list` 均 `RC=0` | 接受 |
| targeted unittest 和 scoped diff 必须通过 | `Ran 94 tests in 2.238s OK`，`git diff --check` 通过 | 接受 |
| no-motion false fields 必须保持 | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | 接受 |

## Artifact 核对

核对对象：

- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_o10_daemon_safe_graph_readback.raw.json`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_daemon_safe_graph_readback_manual.summary.json`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_daemon_safe_graph_readback_manual.stdout.log`

helper 关键事实：

- `status=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`
- `proof.board_source_preflight.source_stage_timeout_s=12.0`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout`
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`
- `daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`

manual same-run 关键事实：

- `primary_conclusion=manual_daemon_safe_graph_readback_recovered_graph_visibility`
- `ros2 daemon status` `RC=0`
- `ros2 daemon stop` `RC=0`
- `ros2 daemon start` `RC=0`
- `timeout 8 ros2 node list` `RC=0`
- `timeout 8 ros2 topic list` `RC=0`
- observed nodes 包含 `/amcl`、`/planner_server`、`/scan` 相关运行链路
- observed topics 包含 `/amcl_pose`、`/map`、`/scan`、`/tf`、`/tf_static`

## OKR 方向判断

- O5：继续约 `85%`，`不调整`。本轮没有 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL pass、safe-to-control 或底盘控制执行。
- O6/O7：继续约 `93%`，`不调整`。本轮没有新的 route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- KR：`不归档`。本轮没有 path generation、route execution、delivery、HIL 或 production KR 完成。

## Product 验收结论

本轮满足 closeout 接受条件，但必须按双边界收口：

1. helper 修正 pass 只把 source stage timeout 从 `board_source_preflight_source_timeout` 推进到 `board_source_preflight_ros2_cli_which_timeout`，还没有把 daemon-safe graph readback 稳定结构化。
2. manual same-run strict no-motion 命令序列已经证明 daemon-safe graph visibility 可恢复，且 `/amcl`、`/planner_server`、`/scan`、`/map`、`/tf`、`/tf_static` 已可读回。

因此本轮是 O3/O1 supporting no-motion diagnostic delta，不是 path generation、route execution、delivery/operator acceptance、HIL、safe-to-control 或 production cloud evidence。OKR 百分比不调整，KR 不归档。

## 下一轮建议

下一轮继续由 `robot-software-engineer` 修 helper 的 source/CLI preflight，把 source、path lookup 和 CLI invocation 放进同一个 amortized shell，先消掉 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`。只有 helper graph readback 稳定结构化后，才回到 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate；在此之前不得进入 motion/path，不得发送 NavigateToPose、`/cmd_vel`、`/api/base/manual` 或打开 WAVE ROVER UART。
