# O3 AMCL Lifecycle Path Generation Repair Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: `2026-07-11`
- Outcome: `O3/O1 supporting no-motion delta; /amcl lifecycle advanced to active [3], but localization/path gate still blocked`

## 用户价值和产品北极星

本轮继续服务于固定路线送垃圾的主链路，但只在 no-motion 边界内推进。对用户真正有价值的不是再多一个 support-only 摘要，而是把真实板定位链从“requested 但未 attempt”逐步推进到可尝试 planner-only path generation。本轮确实新增了 `/amcl active [3]` 这一条 supporting 事实，但还没有达到 localization ready，更没有达到 path generation success。

## OKR 映射和方向判断

- O5：保持约 `85%`。本轮没有真实 production / external material，不能推进 O5。
- O1：保持约 `93%`。本轮新增的是 O3/O1 supporting no-motion delta，不是 current same-run path generation success、Nav2 route execution success 或 HIL pass。
- O6/O7：保持约 `93%`。本轮没有新的 route execution、delivery、operator acceptance 或 production readback material。
- 方向判断：`继续` O3/O1 supporting no-motion localization/path readiness；`暂停` O5 support-only；`不调整` 百分比；`不归档` KR。

## 实际改动

Algorithm owner 已在 `tech-done.md` 记录实现与验证，本次 Product closeout 新增与更新：

- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/side2side_check.md`
- `sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- targeted unittest 最终 `Ran 72 tests in 2.225s OK`
- local helper exit `2`，按预期 fail-closed
- `scp` exit `0`
- live helper artifacts 拉回成功
- artifact invariant check 输出 `artifact_invariants_ok`
- scoped `git diff --check` 通过

Product closeout 验收命令结果：

```bash
rg -n "21-47|amcl_active=true|active \[3\]|map_server_active=false|managed_runtime_started=false|tf_source_probe_not_executed|path_generation_attempted=false|path_generated=false|safe_to_control=false|route_execution_success=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair
```

- 结果：命中 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md` 和既有 `tech-done.md` 中的 21-47 事实与边界字段。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair
```

- 结果：通过，无 whitespace / conflict 标记问题。

## Live Artifact 结论

最终 live artifact 只认：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `amcl_active=true`
- `map_server_active=false`
- `amcl_pose_observed=false`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`
- `managed_runtime_started=false`

关键 readback：

- `amcl_readiness_summary.amcl_lifecycle.result.stdout="active [3]\n"`
- `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_inactive`
- `tf_readiness_summary.blocked_reason=tf_source_probe_not_executed`
- `map_to_odom_dynamic.observed=false`
- `map_to_base_link.observed=false`
- `path_generation_gate.blocked_reason=path_generation_blocked_by_localization_not_ready`
- `planner_server_ready_for_path_generation=false`

最终 root causes：

- `board_source_preflight_rclpy_import_timeout`
- `map_server_lifecycle_not_active_during_preflight`
- `localization_not_ready_for_path_generation`

因此本轮唯一可计入 closeout 的新增 mission supporting artifact delta 是：

- `/amcl` lifecycle 从上一轮 `inactive [2]` 推进为本轮 `active [3]`

但以下结论仍然不能写成已达成：

- `managed_runtime_started=true`
- `map_server_active=true`
- `amcl_pose_observed=true`
- `map_to_odom=true`
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

本轮不按“同一根因第三轮重复消费”处理，理由是：

1. `19-46` 的主 blocker 是 source / CLI readiness，已推进到 `board_source_preflight_ready`。
2. `20-46` 的主 blocker 是 `/amcl inactive [2]`、stale `/amcl_pose`、dynamic `map->odom` missing 和 localization/path gate not ready。
3. `21-47` 又把同一大类 blocker 往前推进了一层：最终 artifact 已确认 `/amcl active [3]`，但 blocker 进一步收口到 `map_server_lifecycle_not_active_during_preflight`、`tf_source_probe_not_executed` 和 `localization_not_ready_for_path_generation`。

也就是说，本轮仍是同一 mission chain，但不是原样复述上一轮 blocker；已有新的 live artifact delta，因此不触发第三轮纯重复消费升级。

## KR 拆解、更新或历史归档

- 本轮 `不归档` 任何 KR。
- 本轮 `不调整` 任何 Objective 百分比。

原因：

- 没有 current same-run `path_generated=true`
- 没有 route execution success
- 没有 delivery record / operator acceptance
- 没有 current live HIL pass
- 没有 production / external evidence

当前推进区继续保留：

- O1：current same-run path generation success / route execution / HIL acceptance 缺口
- O3 supporting lane：localization/TF/path gate 缺口
- O5：production external evidence 缺口

## 剩余风险

- `map_server_active=false` 仍是当前第一现场 blocker。
- `tf_source_probe_not_executed` 说明 TF source inventory 仍未 clean 跑出。
- `amcl_pose_observed=false`，当前还没有 fresh localization output。
- `path_generation_attempted=false`、`path_generated=false`，planner-only path gate 仍未真正进入 attempt。
- `board_source_preflight_rclpy_import_timeout` 仍会污染稳定性，虽然它不应再被写成最终主结论之外的“成功”。

## 下一轮建议

继续由 `robot-algorithm-engineer` 单线闭环，优先级如下：

1. 先把 `map_server_active=false` 与 `tf_source_probe_not_executed` 分开修掉。
2. 在 `/amcl active [3]` 已成立的前提下，恢复 `/amcl_pose` fresh sample。
3. 再确认 dynamic `map->odom` 与 `map->base_link`。
4. 只有 localization/TF gate ready 后，才允许进入 planner-only `ComputePathToPose` attempt。

## Closeout 结论

本轮收口是有效的 supporting no-motion delta，但不是 mission 完成 delta。产品上应把这轮记成“`/amcl` lifecycle 已推进到 `active [3]`，但 map_server / TF / path gate 仍 blocked”，而不是“managed runtime 成功”或“path generation 已尝试”。OKR 百分比不变，KR 不归档。
