# O3 Runtime Graph TF Probe Hardening Pre-Start

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Date: `2026-07-11`
- Related prior sprint:
  - `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`

## 上轮未完成项

上一轮 `22-48` 已把 no-motion supporting lane 从 `tf_source_probe_not_executed` / source-preflight 歧义继续推进到 partial runtime 级别的新 live artifact。当前已确认的新增事实是：

- `board_source_preflight_ready`
- `cli_ready=true`
- `runtime_ready=true`
- `managed_runtime_started=true`

但以下 blocker 仍未通过，且它们直接挡住 planner-only path attempt：

- `managed_runtime_wait_timeout`
- `rclpy_node_names_failed`
- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `/tf_topic_missing`
- `tf_source_root_cause_detail.amcl_param_probe_error` 命中 `librcl_action.so` / `_rclpy_pybind11`
- `path_generation_attempted=false`
- `path_generated=false`

因此本轮不再回头包装 `board_source_preflight_ready` 或 `managed_runtime_started=true`，而是继续拆解三条更靠前的 blocker：

1. board-side managed runtime wait graph probe 为什么停在 `managed_runtime_wait_timeout`
2. graph / node list probe 为什么停在 `rclpy_node_names_failed`
3. TF source probe 为什么最终仍落到 `/tf_topic_missing`，且 AMCL rclpy inventory 仍受 `librcl_action.so` / `_rclpy_pybind11` import chain 影响

## Blocker 重复消费判断

本轮不按“同一根因第三次重复消费”处理，理由如下：

1. `21-47` 的主 blocker 仍是 `tf_source_probe_not_executed` 与 source-preflight 歧义。
2. `22-48` 已把 live artifact 前移到 `managed_runtime_started=true`，并把主 blocker 收敛为 `managed_runtime_wait_timeout`、`rclpy_node_names_failed`、`/tf_topic_missing` 和 AMCL rclpy import chain。
3. 本轮目标是把 runtime graph、AMCL inventory runtime 和 TF source fallback 再拆到更窄、可直接实现的 repair 点，而不是原样复述 `22-48`。

若本轮结束后仍不能把上述 blocker 继续收窄成 runtime graph、inventory runtime 或 TF source fallback 的单点修复项，`final.md` 必须明确说明是否已接近重复消费红线，并给出下一轮是否需要升级 CEO 决策。

## 用户价值和产品北极星

普通手机用户真正关心的是“机器人能否沿固定路线稳定完成送垃圾任务”。本轮仍然不直接证明 route execution、delivery/operator acceptance 或 HIL；本轮的价值是把真实板 no-motion localization chain 从“runtime 已启动但 graph/TF 仍不可靠”推进到“gate ready 后允许 planner-only path attempt”的状态，为后续 same-run path generation、route execution 和 delivery evidence 铺路。

## 本轮 Owner 和协作边界

- 单线 owner：`robot-algorithm-engineer`
- Product 只负责计划、边界、验收口径和后续 closeout，不直接做实现。
- 本轮不拆给 O5/O6/O7/UI/cloud owner，避免 support-only 或 readback-only 工作再次侵占最低有效抓手。

## 本轮核心抓手

1. 先硬化 board-side managed runtime wait graph probe，明确 `managed_runtime_wait_timeout` 的 runtime graph 边界。
2. 单独修或替换 `rclpy_node_names_failed` 相关 node graph inventory 路径，避免 graph probe 自身把 runtime 状态误判成 lifecycle 未起。
3. 把 AMCL rclpy inventory runtime 的 `librcl_action.so` / `_rclpy_pybind11` import chain 收敛成可复验的 runtime 路径或 fallback。
4. 恢复 TF source probe fallback，让 `/tf_topic_missing` 变成有 inventory 结论的 blocked reason，而不是单纯缺失。
5. 只有 runtime graph、AMCL inventory 和 TF source gate ready 后，才允许 planner-only `ComputePathToPose` attempt。

## 验收口径

本轮计划阶段必须明确：

- O5 虽是最低 Objective，但当前继续 O5 support-only 不计 OKR 增量
- 单线 owner 为 `robot-algorithm-engineer`
- 文件范围、接口边界、验收命令和 no-motion 风险边界完整
- planner-only path attempt 的前置条件是 runtime graph、AMCL inventory 与 TF source gate ready

后续 implementation 阶段至少要争取以下之一：

- `managed_runtime_wait_timeout` 被替换为更窄的 graph blocker
- `rclpy_node_names_failed` 被替换为可修复的 inventory/runtime blocker
- TF source probe 不再停在 `/tf_topic_missing` 的无 inventory 状态
- `map_server_active=true` / `amcl_active=true` / `amcl_pose_observed=true`
- 若前置门槛 ready，则 `path_generation_attempted=true`

## No-Motion 安全边界

本轮及后续 implementation 必须继续 fail-closed：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

严格禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART

允许范围仅限：

- managed runtime / graph / map_server / AMCL / TF source / readiness / probe
- planner-only `ComputePathToPose` attempt
- 且前提是 runtime graph、AMCL inventory 与 TF source gate 已 ready
