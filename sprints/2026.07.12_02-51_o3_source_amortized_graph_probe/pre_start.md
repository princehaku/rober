# Pre Start - O3 Source-Amortized Graph Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/`
- Start time: `2026-07-12 02:51 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Primary Objective: O3/O1 supporting no-motion runtime graph root-cause isolation.
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## Read Context

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/final.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/final.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json`
- Automation memory: `/Users/m1/.codex/automations/rober-okr/memory.md`

## Previous Sprint Facts

上一轮已把 generic `ros2_node_list_timeout` 下钻为：

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- `ros2_graph_timeout_root_cause.classification=ros2_cli_plugin_or_import_timeout`
- `primary_candidate.reason=ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`
- remaining candidates: `workspace_source_or_env_mismatch`、`managed_process_lifecycle_not_ready`、`tf_runtime_secondary_after_graph_blocked`

no-motion 字段继续固定：

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

## New Observation

本轮主节点只读验收上一轮 live artifact 时发现：root-cause probes 是逐条 `run_ros()` 执行，每条命令都会重新 `source /opt/ros/humble/setup.bash` 和 onboard workspace。上一轮 live artifact 里 `board_source_preflight.source_stage.elapsed_ms` 约 5 秒，而 `workspace_environment.timeout_s=2.0`、`ros2_node_list.timeout_s=2.5`、`ros2_topic_list.timeout_s=2.5`，这些 probe 很可能在 source 阶段就耗尽预算。

因此本轮不能继续把 `ros2_node_list_help_timeout` 原样作为新结论。必须先把 root-cause probes 改成 source-amortized：同一次 sourced shell 里批量执行 `ros2 node list`、`ros2 node list --help`、`ros2 topic list`、`ros2 daemon status`、workspace env summary 和 rclpy graph stage stream，再重新判断主因。

## OKR Mapping And Direction

- O5 当前仍是最低数值 Objective，约 `85%`，但继续 O5 需要真实 production/external evidence；没有公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external readback 时，继续 wrapper/readback/probe-only 不应计分。
- 本轮不继续 O5 support-only lane。
- 当前可推进的最低有效链路是 O3/O1 no-motion graph/lifecycle/localization gate，直接解锁后续 same-run path generation 和 route execution。
- 本轮默认不调整 OKR 百分比，不归档 KR；若只是 root-cause 诊断，保持 O5/O1/O6/O7 flat。

## Blocker Reuse Guard

本轮不允许仅重复以下结论：

- `ros2_node_list_timeout`
- `ros2_node_list_help_timeout`
- `rclpy_graph_segment_probe_timeout`
- `/tf_topic_missing`

必须新增 source-amortized evidence，说明上一轮 timeout 是否真实发生在 ROS2 subcommand / rclpy graph 内，还是被 per-command source overhead 污染。

## Owner And Scope

主责 Engineer：`robot-algorithm-engineer`

单 owner 闭环。文件范围集中在 Algorithm helper、Algorithm tests、导航文档和本 sprint artifacts，不需要并行拆分。

## Strict No-Motion Boundary

本 sprint 禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART
- 触发底盘运动

Artifact 必须继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generated=false`

## Evidence Needed

本轮完成时至少需要：

- source-amortized root-cause probe 字段进入 local artifact。
- targeted unittest 和 `py_compile` 通过。
- 如果真板可达，真实板 no-motion final artifact 自然返回。
- `tech-done.md` 写清实际改动、验证结果、失败定位、剩余风险。
- 导航文档说明 source-amortized probe 与上一轮 per-command timeout 的边界差异。

## Sprint Documents

本轮先创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 Algorithm 更新：

- `tech-done.md`
- `artifacts/`

阶段验收时 Product closeout 更新：

- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
