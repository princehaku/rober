# O3 Runtime Graph TF Probe Hardening Final

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: `2026-07-12`
- Outcome: `O3/O1 supporting no-motion diagnostic delta; true-board graph fallback reached ros2 node list, but runtime wait final closeout and AMCL CLI fallback are still pending`

## 用户价值和产品北极星

本轮继续服务于“机器人沿固定路线稳定送垃圾”的主链路，但仍严格停在 no-motion supporting lane。对用户真正有价值的不是更多 summary，而是把真实板 runtime graph/TF gate 从 `22-48` 的 `rclpy_node_names_failed` 单层失败，推进到“child Python graph probe 失败后，`ros2 node list` fallback 已真实进入执行链”的更窄 blocker，为后续拿到 final `managed_runtime_wait_result`、AMCL CLI fallback 和 planner-only path gate 铺路。

## OKR 映射和方向判断

- O5：保持约 `85%`。本轮没有真实 production / external evidence，不计 O5 增量。
- O1：保持约 `93%`。本轮只是 O3/O1 supporting no-motion 诊断前移，不是 current same-run path generation success、Nav2 route execution success 或 HIL pass。
- O6/O7：保持约 `93%`。本轮没有新的 route execution、delivery、operator acceptance 或 production readback material。
- 方向判断：`继续` O3/O1 supporting no-motion runtime graph / TF gate lane；`暂停` O5 support-only；`不调整` 百分比；`不归档` KR。

## 实际改动

Algorithm owner 已在 `tech-done.md` 记录实现与验证；本次 Product closeout 新增与更新：

- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/side2side_check.md`
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Algorithm 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- targeted unittest 最终 `Ran 77 tests in 2.220s OK`
- local helper exit `2`，按预期 fail-closed
- scoped `git diff --check` 通过

Product closeout 验收命令结果：

```bash
rg -n "23-49|partial_runtime_in_progress|partial_runtime_material|ros2 node list|TimeoutExpired|board_source_preflight_ready|cli_ready=true|runtime_ready=true|managed_runtime_started=true|path_generation_attempted=false|path_generated=false|safe_to_control=false|route_execution_success=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

- 结果：命中 `OKR.md`、`docs/process/okr_progress_log.md`、`side2side_check.md`、`final.md` 和既有 `tech-done.md` 中的 23-49 事实与边界字段。

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

- 结果：通过，无 whitespace / conflict 标记问题。

## Live Artifact 结论

最终 live artifact 只认：

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.board_source_preflight.cli_ready=true`
- `proof.board_source_preflight.runtime_ready=true`
- `proof.managed_runtime_started=true`
- `proof.last_phase=managed_runtime_started`
- `proof.current_command.command=ros2 node list`
- `proof.artifact_closeout.current_command.command=ros2 node list`
- `proof.recent_commands[*].command` 包含 child Python graph probe 与 `ros2 node list`
- `proof.recent_commands[*].error.type=TimeoutExpired`
- `path_generation_attempted=false`
- `path_generated=false`

关键 readback：

- `ros2 node list` fallback 已真实执行，不再停留在“fallback 没跑到”的假设层。
- 当前仍没有 final `managed_runtime_wait_result`，因此不能把本轮写成 graph wait 已完成收口。
- live partial 还没有跑到 AMCL CLI fallback closeout 阶段，因此也不能把 `probe_mode=ros2_cli_fallback` 写成已在现场证明。

因此本轮唯一可计入 closeout 的新增 mission supporting artifact delta 是：

- blocker 从 `22-48` 的 `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`，前移到 true-board graph fallback 已执行、但 child Python graph probe 与 `ros2 node list` 都在 wait 窗口中 `TimeoutExpired` 的更窄 runtime graph blocker。

但以下结论仍然不能写成已达成：

- final `managed_runtime_wait_result` 已写出
- `map_server_active=true`
- `amcl_active=true`
- AMCL CLI fallback 已完成现场 closeout
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

本轮不按“与 22-48 完全同一根因重复消费”处理，理由是：

1. `22-48` 的最终 live readback 还停在 `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`，看不到第二层 graph fallback 是否真的执行。
2. `23-49` 已把 helper 的两层 fallback 真正写进 true-board partial：child Python graph probe 失败后，`ros2 node list` 已被执行。
3. 当前 blocker 因此进一步收口到 graph wait 时间窗口，而不是原样复述 `22-48` 的边界。

也就是说，本轮仍在同一 mission chain，但不是原样复述 22-48 的 blocker；已有新的 partial live artifact delta，因此不按相同 blocker 重复消费记账。

## KR 拆解、更新或历史归档

- 本轮 `不归档` 任何 KR。
- 本轮 `不调整` 任何 Objective 百分比。

原因：

- live artifact 仍是 `partial_runtime_material`，不是 final completed artifact
- 没有 final `managed_runtime_wait_result`
- 没有现场 AMCL CLI fallback closeout
- 没有 current same-run `path_generated=true`
- 没有 route execution success
- 没有 delivery record / operator acceptance
- 没有 current live HIL pass
- 没有 production / external evidence

当前推进区继续保留：

- O1：current same-run path generation success / route execution / HIL acceptance 缺口
- O3 supporting lane：true-board runtime graph wait、AMCL CLI fallback 和 path gate 缺口
- O5：production external evidence 缺口

## 剩余风险

- 当前 partial artifact 还没有 final `managed_runtime_wait_result`，因此 graph wait 最终 root cause 字段尚未写死。
- `map_server_active` / `amcl_active` 还没有在本轮 final closeout 中被重新证明为 true。
- AMCL CLI fallback 虽已实现并通过单测，但本轮现场还没跑到该阶段。
- `path_generation_attempted=false` 继续说明 planner-only gate 仍未 ready。

## 下一轮建议

继续由 `robot-algorithm-engineer` 单线闭环，优先级如下：

1. 先把 true-board graph wait 自然收口到 final `managed_runtime_wait_result`。
2. 再消费 AMCL CLI fallback，确认 `/tf`、`/tf_static`、`/amcl` inventory 是否能把 root cause 从泛化 `/tf_topic_missing` 继续收紧。
3. 只有 graph wait 和 AMCL/TF gate ready 后，才允许继续看 planner-only `ComputePathToPose` attempt。
4. 不要回到 O5 support-only lane。

## Closeout 结论

本轮收口是有效的 supporting no-motion diagnostic delta，但不是 mission 完成 delta。产品上应把这轮记成“true-board graph fallback 已到 `ros2 node list`，但 runtime wait final closeout 和 AMCL CLI fallback 仍 pending”，而不是“runtime graph 已收口完成”或“path generation 已准备就绪”。OKR 百分比不变，KR 不归档。
