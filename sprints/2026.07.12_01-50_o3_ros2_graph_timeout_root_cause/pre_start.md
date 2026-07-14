# Pre Start - O3 ROS2 Graph Timeout Root Cause

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/`
- Start date: `2026-07-12`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Primary Objective: O3/O1 supporting no-motion runtime graph / TF root cause isolation.
- Current proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## Read Context

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/final.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-done.md`
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/final.md`

## User Value And North Star

产品北极星仍是让普通手机用户把垃圾交给小车后，小车沿固定路线稳定完成送达。当前对用户真正有价值的下一步不是继续堆叠 wrapper、readback 或状态面板，而是把真实板 no-motion runtime graph blocker 拆清楚，让后续路线建图、定位、路径生成和送达任务证据链可以继续推进。

本轮目标是把上一轮 final artifact 里的 `ros2_node_list_timeout` 拆成可执行的下一层根因，而不是再次证明 `ros2 node list` 会 timeout。

## Previous Sprint Facts

`23-49` 已证明 true-board child Python graph probe 后，第二层 `ros2 node list` fallback 已真实进入执行链，但 artifact 仍是 `partial_runtime_in_progress`，`current_command.command=ros2 node list`，没有 final `managed_runtime_wait_result`。

`00-49` 已把 partial current command 收口成 final artifact：

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- primary root cause: `Managed runtime wait` / `ros2_node_list_timeout`
- `board_source_preflight_ready`
- `ros2_cli_invocation_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `graph_wait_summary.latest_ros2_node_list_boundary=ros2_node_list_timeout`
- `graph_wait_summary.observed_node_names=[]`
- AMCL CLI fallback 已看到 `cli_amcl_inventory_observed_amcl_params`
- `/tf_topic_missing`
- `/tf` 与 `/tf_static` 均未 observed
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

## OKR Mapping And Direction Judgment

- O5 当前最低数值约 `85%`，但 O5 需要真实 production/external evidence；近期 support-only、readback、wrapper、probe-only 工作不再允许计分。
- 本轮不继续 O5 support-only lane，方向判断为 `暂停 O5 support-only`。
- 当前环境可推进的是 O3/O1 no-motion runtime graph / TF 链，因此方向判断为 `继续 O3/O1 supporting no-motion`。
- 本轮不计划调整 OKR 百分比，不计划归档 KR。只有当 Algorithm 产出新的 same-run path、route execution、delivery/operator acceptance、HIL 或 production external evidence 时，后续 closeout 才能重新评估。

## Blocker Reuse Guard

同一 blocker 不能连续重复消费。本轮不得把 `ros2_node_list_timeout` 原样复述为新进展，必须进一步拆分 sourced `ros2 node list` timeout 的原因，至少在 artifact 字段中说明以下候选根因的证据边界：

- ROS daemon / DDS graph discovery timeout
- `ros2` CLI plugin/import/runtime timeout
- workspace source 或环境变量不一致
- managed process lifecycle 未实际形成可发现 graph
- TF/runtime 继发问题，而不是 graph timeout 的主因

如果仍无法唯一归因，必须输出 fail-closed 的 `root_cause_unclassified_after_probe`，并列出已经排除和仍未排除的候选项。

## Core Lever

本轮核心抓手是让 `robot-algorithm-engineer` 在 strict no-motion helper 里增加低层 graph timeout root-cause probes，并把结果写入新 sprint artifact：

- 对 sourced shell 的 `ros2 node list` timeout 做分层诊断。
- 把 ROS daemon/DDS discovery、CLI/import、workspace source、managed lifecycle、TF/runtime secondary 五类候选拆开。
- 保持 final artifact 可自然返回，不留下 partial `current_command`。
- gate 未 ready 时继续固定 `path_generation_attempted=false` / `path_generated=false`。

## Owner And Scope

主责 Engineer：`robot-algorithm-engineer`

Product 本轮仅创建计划文档。Algorithm 后续允许改动范围应限制在：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/tech-done.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/`

## No-Motion Boundary

本 sprint 严格 no-motion：

- 不发布 `/cmd_vel`
- 不调用 `/api/base/manual`
- 不发送 NavigateToPose
- 不打开 WAVE ROVER UART
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `path_generated=false`，除非后续 closeout 明确证明 graph、lifecycle、AMCL/TF 和 planner gate 均 ready；本轮计划默认不以 path success 为验收目标。

## Evidence Needed

本轮完成时至少需要：

- 本地 fail-closed dry-run artifact。
- targeted unittest 和 `py_compile` 通过。
- 如果真板可达，真实板 no-motion helper artifact，且自然返回 final artifact。
- artifact 中出现 root-cause split 字段，能说明 `ros2_node_list_timeout` 更可能属于哪一层。
- 更新 `tech-done.md` 记录实际改动、验证输出、失败定位和剩余风险。

## Sprint Documents

本轮 Product 先创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 Algorithm 必须更新：

- `tech-done.md`
- `artifacts/`

阶段验收时 Product 再补：

- `side2side_check.md`
- `final.md`
