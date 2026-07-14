# O3 Runtime Graph TF Probe Hardening Side-to-Side Check

## 对照范围

- 本轮 sprint：`sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`
- 上一轮对照：`sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- 对照对象：`pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、live artifact、上一轮 `final.md`

## 用户价值和产品北极星

用户真正要的是机器人沿固定路线稳定送垃圾。本轮仍严格停在 no-motion supporting lane，价值不是把 partial artifact 包装成 completed，而是把 true-board runtime graph probe 从“只有 child Python graph probe 失败”前移到“第二层 `ros2 node list` fallback 已真实执行且仍 timeout”，为下一轮拿到 final `managed_runtime_wait_result` 和 AMCL CLI fallback 铺路。

## 计划对照

- `pre_start.md` 要求继续拆窄 `managed_runtime_wait_timeout`、`rclpy_node_names_failed` 和 TF source / AMCL inventory runtime blocker。
- `prd.md` 要求本轮只计 O3/O1 no-motion supporting delta，`不调整` O5/O1/O6/O7 百分比，`不归档` KR。
- `tech-plan.md` 要求：即使 `path_generation_attempted=false`，也必须把 runtime graph / inventory blocker 比 `22-48` 再缩窄一层。

对照结论：本轮满足计划口径。`path_generation_attempted=false`、`path_generated=false` 仍未变化，但 live artifact 已从 `22-48` 的 `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`，前移到 true-board partial 中 `current_command.command=ros2 node list`、`recent_commands[*].command` 包含 child Python graph probe 与 `ros2 node list`、`recent_commands[*].error.type=TimeoutExpired` 的更窄 graph wait blocker。

## 与 22-48 的事实对照

### 已前移的事实

- 上一轮 `22-48` final readback：
  - `status=partial_runtime_in_progress`
  - `evidence_type=partial_runtime_material`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `managed_runtime_started=true`
  - `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
  - `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
  - `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- 本轮 `23-49` live artifact：
  - `status=partial_runtime_in_progress`
  - `evidence_type=partial_runtime_material`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `managed_runtime_started=true`
  - `last_phase=managed_runtime_started`
  - `current_command.command=ros2 node list`
  - `artifact_closeout.current_command.command=ros2 node list`
  - `recent_commands[*].command` 包含 child Python graph probe 和 `ros2 node list`
  - `recent_commands[*].error.type=TimeoutExpired`

### 仍未通过的门槛

- 还没有 final `managed_runtime_wait_result`
- `map_server_active` 未证明为 true
- `amcl_active` 未证明为 true
- AMCL CLI fallback 还未跑到 live closeout 阶段
- `path_generation_attempted=false`
- `path_generated=false`

### 安全边界保持不变

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## 验证对照

Algorithm 验证与 `tech-done.md` 一致：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 77 tests in 2.220s OK`
- local helper exit `2`，按预期 fail-closed
- scoped `git diff --check` passed

## Product 验收判断

1. 本轮是有效的 O3/O1 supporting no-motion diagnostic delta。
2. 本轮不是 final completed artifact，不是 path generation success，不是 route execution，不是 delivery/operator acceptance，不是 HIL，也不是 production external evidence。
3. 本轮不按“与 22-48 完全同一 blocker 的重复消费”处理，因为 fallback 已从计划里的第二层 probe 进入 true-board 执行链，最新 blocker 已前移到 graph wait 时间窗口本身。
4. 但 current live artifact 仍停在 `partial_runtime_in_progress`，下一轮必须先拿到 true-board final `managed_runtime_wait_result`，再继续消费 AMCL CLI fallback。

## 收口建议

- `final.md` 必须明确：本轮 live artifact 只认 `status=partial_runtime_in_progress`、`evidence_type=partial_runtime_material`，不是 completed artifact。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 只记录 supporting delta，O5 保持约 `~85%`，O1/O6/O7 保持约 `~93%`，`不调整` 百分比，`不归档` KR。
- 下一轮继续由 `robot-algorithm-engineer` 单线闭环，优先修：
  1. true-board graph wait 到 final `managed_runtime_wait_result`
  2. AMCL CLI fallback 的现场 closeout
