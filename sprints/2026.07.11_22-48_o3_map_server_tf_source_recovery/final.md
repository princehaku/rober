# O3 Map Server TF Source Recovery Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: `2026-07-11`
- Outcome: `O3/O1 supporting no-motion diagnostic delta; board source preflight and managed runtime start recovered, but runtime wait graph / TF / path gate still blocked`

## 用户价值和产品北极星

本轮继续服务于“机器人沿固定路线稳定送垃圾”的主链路，但仍严格停在 no-motion supporting lane。对用户真正有价值的不是新的状态包装，而是把真实板 localization chain 从 `tf_source_probe_not_executed` 的模糊失败前移到更窄、可修复的 root cause。本轮做到的是：真实板已进入 `board_source_preflight_ready`、`cli_ready=true`、`runtime_ready=true`、`managed_runtime_started=true`；但还没有到 path generation attempt，更没有到 route execution、delivery/operator acceptance 或 HIL。

## OKR 映射和方向判断

- O5：保持约 `85%`。本轮没有真实 production / external evidence，不计 O5 增量。
- O1：保持约 `93%`。本轮只是 O3/O1 supporting no-motion 诊断前移，不是 current same-run path generation success、Nav2 route execution success 或 HIL pass。
- O6/O7：保持约 `93%`。本轮没有新的 route execution、delivery、operator acceptance 或 production readback material。
- 方向判断：`继续` O3/O1 supporting no-motion localization/path readiness；`暂停` O5 support-only；`不调整` 百分比；`不归档` KR。

## 实际改动

Algorithm owner 已在 `tech-done.md` 记录实现与验证；本次 Product closeout 新增与更新：

- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/side2side_check.md`
- `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- targeted unittest 最终 `Ran 74 tests in 2.239s OK`
- local helper exit `2`，按预期 fail-closed
- `scp` exit `0`
- live partial artifact pulled 成功
- artifact invariant check passed
- scoped `git diff --check` 通过

Product closeout 验收命令结果：

```bash
rg -n "22-48|partial_runtime_in_progress|partial_runtime_material|board_source_preflight_ready|cli_ready=true|runtime_ready=true|managed_runtime_started=true|managed_runtime_wait_timeout|rclpy_node_names_failed|/tf_topic_missing|librcl_action.so|path_generation_attempted=false|path_generated=false|safe_to_control=false|route_execution_success=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery
```

- 结果：命中 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md` 和既有 `tech-done.md` 中的 22-48 事实与边界字段。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery
```

- 结果：通过，无 whitespace / conflict 标记问题。

## Live Artifact 结论

最终 live artifact 只认：

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `board_source_preflight.classification=board_source_preflight_ready`
- `board_source_preflight.cli_ready=true`
- `board_source_preflight.runtime_ready=true`
- `managed_runtime_started=true`
- `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
- `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`

关键 readback：

- managed runtime 已真实启动，不再停留在 source-preflight 歧义层
- wait graph 多次落在 `rclpy_node_names_failed`
- `tf_source_root_cause_detail.amcl_param_probe_error` 命中 `librcl_action.so` / `_rclpy_pybind11` ImportError
- `/tf` source 仍未恢复，因此 `map_to_odom_dynamic.observed=false`

因此本轮唯一可计入 closeout 的新增 mission supporting artifact delta 是：

- blocker 从 `21-47` 的 `tf_source_probe_not_executed` / source-preflight ambiguity，前移到 `managed_runtime_wait_timeout`、`rclpy_node_names_failed`、`/tf_topic_missing` 与 AMCL rclpy import chain

但以下结论仍然不能写成已达成：

- `map_server_active=true`
- `amcl_active=true`
- `amcl_pose_observed=true`
- `map_to_odom_dynamic.observed=true`
- `path_generation_attempted=true`
- `path_generated=true`

## No-Motion 边界

最终 artifact 继续固定：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

因此本轮仍是 strict no-motion supporting sprint，不是 route execution、delivery 或 HIL 验收。

## Blocker 重复消费判断

本轮不按“与 21-47 完全同一根因重复消费”处理，理由是：

1. `21-47` 的主 blocker 仍包含 `tf_source_probe_not_executed` 与 source-preflight 歧义。
2. `22-48` 已把真实板前置条件推进到 `board_source_preflight_ready`、`cli_ready=true`、`runtime_ready=true` 和 `managed_runtime_started=true`。
3. 当前 blocker 进一步收口到 `managed_runtime_wait_timeout`、`rclpy_node_names_failed`、`/tf_topic_missing` 与 `librcl_action.so` / `_rclpy_pybind11` ImportError。

也就是说，本轮仍在同一 mission chain，但不是原样复述 21-47 的 blocker；已有新的 partial live artifact delta，因此不按相同 blocker 重复消费记账。

## KR 拆解、更新或历史归档

- 本轮 `不归档` 任何 KR。
- 本轮 `不调整` 任何 Objective 百分比。

原因：

- live artifact 仍是 `partial_runtime_material`，不是 final completed artifact
- 没有 current same-run `path_generated=true`
- 没有 route execution success
- 没有 delivery record / operator acceptance
- 没有 current live HIL pass
- 没有 production / external evidence

当前推进区继续保留：

- O1：current same-run path generation success / route execution / HIL acceptance 缺口
- O3 supporting lane：managed runtime wait graph、TF source 和 path gate 缺口
- O5：production external evidence 缺口

## 剩余风险

- `managed_runtime_wait_timeout` 说明 managed runtime 虽然启动，但 node graph / lifecycle 仍没稳定到可验收状态。
- `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed` 说明 board-side graph probe 还不可靠。
- `tf_source_root_cause_detail.amcl_param_probe_error` 命中 `librcl_action.so` / `_rclpy_pybind11` ImportError，AMCL rclpy inventory 仍不稳定。
- `map_server_active=false`、`amcl_active=false`、`amcl_pose_observed=false` 仍挡住 `path_generation_attempted=true`。
- 当前 live 证据是 partial，不是 final completed artifact。

## 下一轮建议

继续由 `robot-algorithm-engineer` 单线闭环，优先级如下：

1. 先修 board-side managed runtime wait graph probe 的 `rclpy_node_names_failed` timeout。
2. 再把 AMCL rclpy inventory 的 `librcl_action.so` / `_rclpy_pybind11` import failure 收紧到可复验单点。
3. 只有 `map_server_active=true`、`amcl_active=true`、`/tf` source 可见后，才允许继续看 planner-only `ComputePathToPose` attempt。
4. 不要回到 O5 support-only lane。

## Closeout 结论

本轮收口是有效的 supporting no-motion diagnostic delta，但不是 mission 完成 delta。产品上应把这轮记成“board source preflight 与 managed runtime start 已恢复，但 wait graph / TF / path gate 仍 blocked”，而不是“path generation 已尝试”或“route execution 已准备就绪”。OKR 百分比不变，KR 不归档。
