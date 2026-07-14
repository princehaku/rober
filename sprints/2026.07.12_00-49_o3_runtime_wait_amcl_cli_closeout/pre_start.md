# O3 Runtime Wait AMCL CLI Closeout Pre-Start

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `robot-algorithm-engineer`
- Date: `2026-07-12`
- Related prior sprints:
  - `sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
  - `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`

## 上轮未完成项

`22-48` 已把 no-motion supporting lane 推进到更清晰的 partial runtime 层：

- `board_source_preflight_ready`
- `cli_ready=true`
- `runtime_ready=true`
- `managed_runtime_started=true`
- `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
- `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`

`23-49` 继续证明 true-board child Python graph probe 失败后，第二层 `ros2 node list` fallback 已真实进入执行链：

- `status=partial_runtime_in_progress`
- `evidence_type=partial_runtime_material`
- `last_phase=managed_runtime_started`
- `current_command.command=ros2 node list`
- `artifact_closeout.current_command.command=ros2 node list`
- `recent_commands[*].command` 同时包含 child Python graph probe 与 `ros2 node list`
- `recent_commands[*].error.type=TimeoutExpired`
- `path_generation_attempted=false`
- `path_generated=false`

但 `23-49` 仍未收口以下核心缺口：

- 没有 final `managed_runtime_wait_result`
- 没有 AMCL CLI fallback live closeout
- 没有证明 `map_server_active=true`
- 没有证明 `amcl_active=true`
- 没有证明 `/tf`、`/tf_static`、`/amcl` inventory 已能形成可验收结论
- 没有 `path_generation_attempted=true`
- 没有 `path_generated=true`

因此本轮不能再把“`ros2 node list` fallback 已执行”包装成新进展；必须把 true-board graph wait 自然收口为 final `managed_runtime_wait_result`，并消费 AMCL CLI fallback 的现场 closeout。

## Blocker 重复消费判断

本轮不回到 O5 support-only blocker。O5 当前最低但缺口是公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 这些真实 external evidence；最近 O5 已固定 `okr_credit_allowed=false`，没有新 external material 时继续做 support-only 只会重复消费同一 blocker。

本轮也不能重复消费 O3 的旧 blocker。`23-49` 已经把 graph fallback 执行事实打到 `ros2 node list`，所以本轮若只再次证明 `partial_runtime_in_progress`、`ros2 node list` 和 `TimeoutExpired`，应判定为无新增 artifact delta。有效前进必须至少满足以下之一：

- 写出 final `managed_runtime_wait_result`，并明确最终 graph wait root cause
- 消费 AMCL CLI fallback live closeout，给出 `/tf`、`/tf_static`、`/amcl` inventory 的现场结论
- 证明 gate ready 后才进入 planner-only `ComputePathToPose` attempt
- 若仍 blocked，blocked reason 必须比 `23-49` 更窄，而不是复述 fallback 已执行

## 用户价值和产品北极星

产品北极星不变：普通手机用户把垃圾交给机器人后，机器人能沿固定路线稳定完成送达。本轮仍不是 route execution、delivery/operator acceptance 或 HIL；本轮的用户价值是把真实板 no-motion localization/runtime gate 从“runtime 启动但 graph wait 卡住”推进到“可判断是否允许 planner-only path generation”的状态，补齐后续 same-run path、route execution 和 delivery evidence 的前置门槛。

## 本轮 Owner 和协作边界

- 单线 owner：`robot-algorithm-engineer`
- Product 负责目标、边界、验收口径和初始三文档，不直接做实现。
- 本轮不派 O5/O6/O7/UI/cloud owner，避免 support-only、readback-only 或 surface 工作继续占用最低有效抓手。
- 若 implementation 阶段发现问题属于硬件串口、WAVE ROVER UART 或真实运动控制，不在本轮修，必须 fail-closed 记录为后续 hardware/HIL 风险。

## 本轮核心抓手

1. 让 true-board managed runtime wait 自然结束并写出 final `managed_runtime_wait_result`，不能只保留 partial current command。
2. 消费 `23-49` 已实现的 AMCL CLI fallback，让 `/tf`、`/tf_static`、`/amcl` inventory 在 live artifact 中形成 closeout。
3. 继续保持 strict no-motion；gate 未 ready 前必须保持 `path_generation_attempted=false` 和 `path_generated=false`。
4. 只有 final wait、AMCL/TF gate、map lifecycle 和 localization gate 都 ready 后，才允许 planner-only `ComputePathToPose` attempt。

## 优先级和验收口径

优先级 P0：

- final `managed_runtime_wait_result` 必须出现；若仍 blocked，必须明确最终是 `ros2_node_list_timeout`、`ros2_node_list_empty_after_wait`、graph visible 但 lifecycle inactive，还是其他更窄 root cause。
- AMCL CLI fallback live closeout 必须出现；至少给出 `/tf`、`/tf_static`、`/amcl` topic/node/param inventory 的执行结果或可解释 blocked reason。
- `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false` 必须保持。

优先级 P1：

- 若 `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`、`map_to_odom_dynamic.observed=true` 全部成立，再允许 planner-only `ComputePathToPose` attempt。
- 如果进入 planner-only attempt，必须明确 `path_generation_attempted=true` 是否伴随 `path_generated=true`；失败也要给出 planner-only root cause。

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
- 任何真实底盘运动或手动控制

允许范围仅限：

- managed runtime wait graph closeout
- `ros2 node list` / node graph 只读诊断
- AMCL CLI fallback inventory
- `/tf`、`/tf_static`、`/amcl` 只读诊断
- gate ready 后的 planner-only `ComputePathToPose` attempt

## 需要创建或更新的 sprint 文档

本轮初始阶段创建：

- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/pre_start.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/prd.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-plan.md`

implementation 后续必须补齐：

- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/tech-done.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/side2side_check.md`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/final.md`
