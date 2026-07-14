# O3 Runtime Wait AMCL CLI Closeout Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: `2026-07-12`
- Outcome: `O3/O1 supporting no-motion diagnostic delta; final runtime wait closeout succeeded, but graph/TF/path gate remains blocked`

## 用户价值和产品北极星

本轮继续服务于“机器人沿固定路线稳定送垃圾”的主链路。对用户真正有价值的不是再证明 fallback 已执行，而是让真实板 no-motion runtime gate 形成 final artifact，知道下一步该修哪里。本轮把 `23-49` 的 partial `current_command=ros2 node list` 收口为 final `ros2_node_list_timeout`，并证明 AMCL CLI params 可读但 `/tf`、`/tf_static` 仍不可见。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。O5 仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser；本轮没有 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮只推动 O3/O1 supporting no-motion runtime diagnosis，不是 current same-run path generation success、Nav2 route execution success 或 current live HIL pass。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 route execution、delivery、operator acceptance、production readback 或可消费的 same-task mission material。
- 方向判断：`继续` O3/O1 no-motion runtime graph / TF recovery；`暂停` O5 support-only；`不归档` KR。

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

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据只作为 O3/O1 supporting diagnostic delta 记录在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` Key Results 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手和实际结果

本轮核心抓手是把 true-board managed runtime wait 自然收口为 final artifact，并消费 AMCL CLI fallback closeout。

Algorithm owner 实际改动：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-done.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/`

Product closeout 实际改动：

- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/side2side_check.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` 通过
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 81 tests in 2.221s OK`
- local helper exit `2`，按预期 fail-closed
- true-board patched helper `ssh_returncode=2`、`elapsed_s=117.4`，自然返回 final artifact
- scoped `git diff --check` 通过

Product closeout 验收命令：

```bash
rg -n "00-49|ros2_node_list_timeout|cli_invocation_timeout_s=6.0|board_source_preflight_ready|managed_runtime_started=true|cli_amcl_inventory_observed_amcl_params|/tf_topic_missing|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

## Live Artifact 结论

最终 live artifact 只认：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `artifact_kind=final`
- `last_phase=final`
- `current_command=null`
- primary root cause: `layer=Managed runtime wait`、`reason=ros2_node_list_timeout`
- `board_source_preflight_ready`
- `cli_invocation_timeout_s=6.0`
- `ros2_cli_invocation_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `managed_runtime_wait_result.reason=ros2_node_list_timeout`
- `managed_runtime_wait_result.boundary=ros2_node_list_timeout`
- `graph_wait_summary.latest_ros2_node_list_boundary=ros2_node_list_timeout`
- `graph_wait_summary.latest_ros2_node_list_timed_out=true`
- `graph_wait_summary.fallback_used=true`
- `graph_wait_summary.fallback_observed=false`
- `graph_wait_summary.observed_node_names=[]`
- `tf_source_root_cause_detail.amcl_param_probe_boundary=cli_amcl_inventory_observed_amcl_params`
- `tf_source_root_cause_detail.amcl_param_probe_ok=true`
- `tf_source_root_cause_detail.reason=/tf_topic_missing`
- `tf_topics_observed./tf=false`
- `tf_topics_observed./tf_static=false`
- `commands.map_to_odom_tf.boundary=tf_probe_skipped_after_managed_runtime_graph_wait_blocked`
- `commands.scan_once.boundary=scan_probe_skipped_after_managed_runtime_graph_wait_blocked`
- `path_generation_attempted=false`
- `path_generated=false`

No-motion 字段继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## Product Judgment

本轮是有效的 O3/O1 supporting no-motion diagnostic delta：

- 旧 `board_source_preflight_ros2_cli_invocation_timeout` 已关闭。
- 旧 `partial current_command=ros2 node list` 已关闭。
- 新 root cause 是 final `ros2_node_list_timeout`。
- AMCL CLI fallback 已推进到 `cli_amcl_inventory_observed_amcl_params`，但 `/tf_topic_missing` 仍挡住 localization/path gate。

本轮不是：

- path generation success
- planner route execution success
- delivery/operator acceptance
- current live HIL pass
- production cloud success
- safe-to-control success

## Blocker 重复消费判断

本轮不按与 `23-49` 完全同一 blocker 重复消费处理。理由：

1. `23-49` 仍是 `partial_runtime_in_progress`，只证明 `ros2 node list` fallback 正在 true-board 执行链中。
2. `00-49` 已自然返回 final artifact，`current_command=null`，并写出 final `managed_runtime_wait_result.boundary=ros2_node_list_timeout`。
3. AMCL CLI fallback 不再只是代码和单测，live artifact 已出现 `cli_amcl_inventory_observed_amcl_params` 与 `amcl_param_probe_ok=true`。

但下一轮如果仍只重复 `ros2_node_list_timeout` 而没有进一步解释 sourced `ros2 node list` 为什么 timeout，或没有恢复 `/tf` / `/tf_static` visibility，应视为接近同一 blocker 重复消费红线。

## 剩余风险

- true-board sourced `ros2 node list` 在 managed runtime 后持续 timeout，graph 不可观测。
- `/tf` 与 `/tf_static` 仍未 observed，AMCL dynamic `map->odom` 与 `map->base_link` gate 未 ready。
- map_server / amcl lifecycle inactive、ROS package availability missing、scan/map probes skipped 可能是 graph timeout 继发问题，也可能是真实 install/lifecycle 缺口。
- `path_generation_attempted=false` 和 `path_generated=false` 表明 O1 current same-run path generation success 仍未发生。

## 下一轮建议

继续留在 O3/O1 no-motion lane，不回到 O5。下一轮由 `robot-algorithm-engineer` 优先定位为什么 sourced `ros2 node list` 在 managed runtime 后 timeout，尽管 `board_source_preflight_ready`、`cli_invocation_timeout_s=6.0`、`ros2_cli_invocation_ok=true`、`rclpy_import_ok=true`；随后恢复 `/tf` 与 `/tf_static` visibility。只有 dynamic `map->odom`、AMCL pose 和 lifecycle gate ready 后，才允许 planner-only `ComputePathToPose` attempt。
