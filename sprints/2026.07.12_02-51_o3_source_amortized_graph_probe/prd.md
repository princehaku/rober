# PRD - O3 Source-Amortized Graph Probe

## Product Goal

把 O3/O1 no-motion runtime graph blocker 从上一轮的 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout` 继续拆清楚，判断 timeout 是否真实发生在 ROS2 subcommand / rclpy graph 层，还是因为每条 probe 反复 source ROS/workspace 导致低预算 probe 误判。

用户价值是让下一条工程命令更具体：修 ROS2 CLI/subcommand import，修 DDS/daemon discovery，修 workspace/source，修 managed lifecycle，还是恢复 TF/localization。

## North Star

北极星仍是普通手机用户可以一键让机器人沿固定路线送垃圾。本轮只是恢复路线能力前的 no-motion 现场诊断，不是送达成功，不是 HIL pass，也不是 production cloud success。

## Problem Statement

上一轮 live artifact 显示：

- `board_source_preflight_ready`
- top-level `ros2 --help` 可以在约 4.8 秒内完成
- `rclpy_import_ok=true`
- 但 root-cause probes 里的 `ros2 node list --help`、`ros2 node list`、`ros2 topic list`、`ros2 daemon status`、`workspace_environment` 和 `rclpy_graph_segments` 均 timeout

由于这些 probes 当前逐条运行 `run_ros()`，每条都会重新 source ROS/workspace，而 source 阶段本身约 5 秒，2 到 5 秒的 per-command timeout 可能不足以证明命令本身卡住。本轮要先修这个测量口径，否则会连续消费同一 blocker。

## OKR Mapping

- O5：约 `85%`，最低数值，但缺真实 production/external evidence；继续 support-only 不计 OKR 增量。
- O1：约 `93%`，仍缺 current same-run path generation、Nav2 route execution、HIL pass。O3 no-motion graph/lifecycle/localization 修复是解锁这些缺口的前置。
- O6/O7：约 `93%`，本轮不消费新的 route/delivery/operator/production material。

本轮预计是 diagnostic delta；默认不调整百分比、不归档 KR。

## In Scope

- 在 `o10_amcl_nav2_runtime_proof.py` 中新增或替换 root-cause probes，使 probe 在同一次 sourced shell 中批量执行。
- 单次 source 后记录 `source_stage`，再记录每条 subcommand 的真实 command timeout、returncode、stdout/stderr 摘要。
- 对 rclpy graph segment probe 增加 stage-stream 或 partial stdout 解析，确保 timeout 时也能知道已完成 import、init、create_node 还是卡在 graph wait。
- 在 artifact 中新增 source-amortized 字段，例如 `ros2_graph_timeout_root_cause.probes.source_amortized_batch` 或等价字段。
- 分类逻辑必须优先使用 source-amortized 结果，避免把 source overhead 误分类为 CLI/plugin timeout。
- 更新 `onboard/tests/test_nav2_runtime_proof_helper.py` 覆盖 source-amortized 分类和 rclpy stage-stream timeout。
- 更新 `docs/navigation/field_route_evidence_preflight.md` 与 `docs/navigation/fixed_route_workflow.md`。
- 更新本 sprint `tech-done.md` 和 artifacts。

## Out Of Scope

- 不做 route execution。
- 不发送 NavigateToPose goal。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不改 O5/O6/O7 cloud/workstation code。
- 不把 diagnostic artifact 记为 path generation、delivery、HIL 或 production evidence。

## Requirements

### R1 Source-Amortized Probe

Artifact 必须能看出：

- source 阶段是否成功、耗时多少。
- source 成功后，`ros2 node list --help` 是否仍 timeout。
- source 成功后，`ros2 node list`、`ros2 topic list`、`ros2 daemon status` 是否仍 timeout。
- workspace env summary 是否在同一次 sourced shell 内可读。
- rclpy graph stage-stream 卡在哪个阶段。

### R2 Classification Uses Correct Evidence

分类器必须满足：

- 如果 batched `ros2 node list --help` 成功，但 node/topic/daemon graph still timeout，则主分类应偏向 `ros2_daemon_or_dds_graph_discovery_timeout` 或 managed lifecycle，而不是 `ros2_cli_plugin_or_import_timeout`。
- 如果 batched subcommand help 仍 timeout，且 rclpy stage-stream 也在 import/init/create_node 前卡住，才允许继续归类为 `ros2_cli_plugin_or_import_timeout`。
- 如果 source stage 失败或 workspace env 缺 ROS/workspace 摘要，才能把 `workspace_source_or_env_mismatch` 提升为主因。
- `/tf_topic_missing` 在 graph blocked 时只能作为 secondary remaining candidate。

### R3 Final Artifact And Safety

helper 必须自然写出 final artifact：

- `status=blocked_with_root_cause` 或更具体 fail-closed status
- `artifact_kind=final`
- `current_command=null`
- `path_generation_attempted=false`
- `path_generated=false`
- no-motion booleans 全 false

不得留下 partial `current_command=ros2 node list` 作为唯一结论。

### R4 Documentation Sync

导航文档必须写清：

- 旧 per-command probe 的 timeout 会包含 source overhead。
- 新 source-amortized batch 的读取顺序。
- source-amortized evidence 仍是 no-motion diagnostic，不等于 path、route、delivery、HIL 或 production evidence。

## Acceptance Criteria

Algorithm owner 必须完成：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 通过。
- 本地 fail-closed dry-run 写入 `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/local_o10_source_amortized_graph_probe.raw.json`。
- 如果真板可达，写入 `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`。
- `git diff --check` scoped 范围通过。
- `tech-done.md` 包含实际改动、验证结果、失败定位、剩余风险。

Product closeout 只接受以下之一：

1. source-amortized evidence 证明 subcommand help 实际可完成，从而把主因从 CLI timeout 改到 daemon/DDS graph discovery 或 managed lifecycle。
2. source-amortized evidence 证明 subcommand help 和 rclpy stage-stream 在单次 source 后仍卡住，并给出具体 stage。
3. source-amortized evidence 仍无法唯一归因，但明确列出已排除和仍未排除候选，且不重复上一轮测量口径。

## Responsibility

- Product owner：`product-okr-owner`，负责范围边界、验收口径和 closeout 判断。
- Implementation owner：`robot-algorithm-engineer`，负责 helper、测试、导航文档、artifacts 和 `tech-done.md`。

## Risks

- 真板可能不可达；若不可达，只能保留本地 fail-closed artifact，OKR 百分比不调整。
- batched probe 可能发现上一轮 classification 受 source overhead 污染；这不是倒退，属于纠正测量口径。
- 即使 root cause 变成 daemon/DDS 或 managed lifecycle，本轮也仍不是 path generation 或 route execution。

## KR History

本轮没有计划归档 KR。若最终仍是 no-motion diagnostic delta，应只写入 sprint closeout 和 progress log，不上调 O5/O1/O6/O7。
