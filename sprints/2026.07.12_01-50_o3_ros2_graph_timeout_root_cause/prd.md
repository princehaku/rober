# PRD - O3 ROS2 Graph Timeout Root Cause

## Product Goal

把真实板 O3/O1 no-motion runtime graph blocker 从上一轮的 final `ros2_node_list_timeout` 继续拆成可执行根因，帮助团队判断下一条工程命令应该修 ROS daemon/DDS discovery、CLI/import、workspace source、managed lifecycle，还是 TF/runtime 继发问题。

用户价值是缩短从“机器人不能生成路线”到“知道该修哪一层”的路径，为后续 fixed route、map/TF localization、planner-only path proof 和送达任务证据链恢复创造条件。

## North Star

北极星不变：普通手机用户不需要懂 SSH、ROS2 或串口，也能让小车稳定沿固定路线送垃圾。本轮是该能力的现场诊断前置，不是交付成功本身。

## Problem Statement

上一轮 final artifact 已证明：

- `ros2_node_list_timeout`
- `/tf_topic_missing`
- AMCL CLI params 可读
- graph wait fallback 未观察到节点
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`

这已经比 `23-49` 的 partial `current_command=ros2 node list` 更进一步，但还不能指导下一步修复。Algorithm 需要把 sourced `ros2 node list` timeout 拆成低层 root-cause 分类，并把证据写入 artifact，避免下一轮重复消费同一个 blocker。

## OKR Mapping And Direction

- O5：当前最低数值约 `85%`，但缺真实 production/external evidence。方向判断：`暂停 O5 support-only`，不再用 wrapper、readback、probe-only 或 readiness packet 计分。
- O1：约 `93%`，仍缺 current same-run path generation success、Nav2 route execution success、HIL pass、安全控制和真实路线执行。方向判断：`继续`，但本轮只做 no-motion supporting root-cause evidence。
- O3 supporting lane：继续推进 runtime graph / TF / localization gate。
- O6/O7：约 `93%`，本轮不消费新的 same-task delivery、operator acceptance 或 production readback material。

本轮不归档 KR，不更新 `OKR.md`。Product closeout 后续只有在有新的可计分 mission artifact delta 时才重新评估百分比。

## In Scope

- 在 no-motion helper 中增加 root-cause split，使 `ros2_node_list_timeout` 不再只是单一 blocker label。
- 记录 sourced shell 中 ROS/工作区环境摘要，避免误判 workspace source 问题。
- 对 ROS daemon/DDS graph discovery 与 `ros2` CLI plugin/import runtime 做可区分诊断。
- 对 managed runtime process lifecycle 做最小可复核记录，包括进程是否启动、节点是否应出现、lifecycle probe 是否被 graph timeout 阻断。
- 保留 `/tf_topic_missing`，但明确它是 graph blocker 后的 TF/runtime 继发事实，还是独立主因。
- 本地 dry-run 和真板 no-motion artifact 均必须 fail-closed。
- 同步更新导航文档与 sprint `tech-done.md`，由 Algorithm 后续执行。

## Out Of Scope

- 不做 route execution。
- 不发送 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不做 O5 production cloud / external evidence。
- 不把 PRD、计划、wrapper、readback 或 checklist 记为 OKR 进度。
- 不在 graph/lifecycle/localization gate 未 ready 时宣称 path generation、delivery 或 HIL success。

## Requirements

### R1 Root-Cause Classification

Artifact 必须增加或复用明确字段，说明 `ros2_node_list_timeout` 的下一层分类。建议输出：

- `ros2_graph_timeout_root_cause.classification`
- `ros2_graph_timeout_root_cause.primary_candidate`
- `ros2_graph_timeout_root_cause.excluded_candidates`
- `ros2_graph_timeout_root_cause.remaining_candidates`
- `ros2_graph_timeout_root_cause.probes`
- `ros2_graph_timeout_root_cause.evidence_boundary`

允许的分类至少覆盖：

- `ros2_daemon_or_dds_graph_discovery_timeout`
- `ros2_cli_plugin_or_import_timeout`
- `workspace_source_or_env_mismatch`
- `managed_process_lifecycle_not_ready`
- `tf_runtime_secondary_after_graph_blocked`
- `root_cause_unclassified_after_probe`

### R2 No-Motion Safety Fields

无论本地还是真板 artifact，都必须继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generated=false`，除非后续明确出现 planner gate ready 且仍不触发实际运动；本轮验收默认不要求 path success。

### R3 Final Artifact Behavior

helper 不能停在 partial `current_command=ros2 node list`。如果阻塞，artifact 必须自然返回：

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- root-cause split 字段完整
- validation commands 可复现

### R4 Documentation Sync

Algorithm 后续必须同步：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- sprint `tech-done.md`

文档必须写清本轮只是 no-motion diagnosis，不是 path generation、route execution、delivery、HIL 或 production cloud success。

## Acceptance Criteria

本轮 Product 验收时，至少满足：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 通过。
- 本地 helper fail-closed dry-run 产出新 sprint artifact。
- 若真板可达，按既有 SSH/SCP 模式产出 live no-motion final artifact。
- Artifact 明确提到 `ros2_node_list_timeout` 的下钻分类，而不是只重复上一轮 blocker。
- Artifact 继续包含 `/tf_topic_missing`，并解释其与 graph timeout 的主次关系。
- 安全字段继续保持 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`path_generated=false`。
- `git diff --check` 在指定范围内通过。

## Responsibility

- Product owner：`product-okr-owner`，负责本 PRD、范围边界、验收口径和后续 closeout 判断。
- Implementation owner：`robot-algorithm-engineer`，负责 helper、测试、导航文档、artifact 和 `tech-done.md`。

## Priority

P0：root-cause split artifact，先拆 `ros2_node_list_timeout`。

P1：真板 no-motion artifact；如果真板不可达，必须保留本地 fail-closed artifact 和无法执行 live 的原因。

P2：文档同步和 closeout 准备。

## Risks And Evidence Gaps

- 真板可能仍超时，导致只能得到 `root_cause_unclassified_after_probe`；可接受，但必须列出已排除与未排除项。
- ROS daemon/DDS discovery 与 managed lifecycle 可能同时异常，需要 artifact 明确主次，不要把 `/tf_topic_missing` 过早当主因。
- O5 约 `85%` 仍是最低 Objective，但没有真实 external production evidence，继续 O5 wrapper 不应计分。
- 本轮不会证明 route execution、delivery、operator acceptance、HIL、安全控制或 production cloud。

## KR History

本轮没有已完成 KR 需要归档。历史记录位置保持不变，后续 closeout 若仍是 no-motion diagnostic delta，应写入本 sprint `tech-done.md`、`side2side_check.md`、`final.md` 和进度日志，但不移动已完成 KR。

## Sprint Documents To Create Or Update

本轮已创建：

- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/pre_start.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/prd.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/tech-plan.md`

后续实现必须创建或更新：

- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/tech-done.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/`
- Epic closeout 时补 `side2side_check.md` 和 `final.md`
