# O3 AMCL Lifecycle Path Generation Repair Side-to-Side Check

## 验收结论

- 验收结果：`部分通过（按 no-motion supporting artifact 收口，通过；按 localization/path gate ready 收口，不通过）`
- 收口类型：`O3/O1 supporting no-motion delta`
- 结论摘要：本轮真实板最终 artifact 新增了 `/amcl` lifecycle `active [3]` 这一条 mission supporting fact，但 `map_server_active=false`、`amcl_pose_observed=false`、`tf_source_probe_not_executed`、`map_to_odom_dynamic.observed=false`、`path_generation_attempted=false` 仍成立，因此不能把本轮写成 managed runtime 成功、localization ready、path generation attempted 或 path generated。

## 计划 vs 实现

### 计划要求

- 继续 O3/O1 no-motion localization/path readiness，不做 O5 support-only 包装。
- 单 owner 为 `robot-algorithm-engineer`。
- 目标至少把 `/amcl` lifecycle、signal freshness、dynamic TF 或 path gate 向前推进一层。
- 严格保持 no-motion：
  - `safe_to_control=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `delivery_success=false`
  - `hil_pass=false`
  - `uses_base_uart=false`

### 实现结果

- Algorithm 已完成 helper、targeted tests、导航文档和 artifact 合同修复，并在 `tech-done.md` 留档。
- Product 本次收口只认最终 live artifact：
  - `artifacts/live_o10_amcl_lifecycle_path_generation_repair.raw.json`
- 与计划相比，确实把 blocker 从上一轮 `/amcl inactive [2]` 推进为本轮 `/amcl active [3]`，但没有推进到 localization ready 或 planner-only path attempt。

## 证据 vs 验收口径

### 通过项

1. `/amcl` lifecycle 已有新的真实板 supporting 事实：
   - `amcl_active=true`
   - `amcl_readiness_summary.amcl_lifecycle.result.stdout="active [3]\n"`
2. 最终 artifact 已明确 fail-closed root cause：
   - `status=blocked_with_root_cause`
   - `evidence_type=blocked_with_root_cause`
   - `root_causes` 包含：
     - `board_source_preflight_rclpy_import_timeout`
     - `map_server_lifecycle_not_active_during_preflight`
     - `localization_not_ready_for_path_generation`
3. 验证链完整：
   - `py_compile` exit `0`
   - targeted unittest 最终 `Ran 72 tests in 2.225s OK`
   - local helper exit `2` fail-closed
   - `scp` exit `0`
   - live helper artifacts 拉回
   - invariant check 输出 `artifact_invariants_ok`
   - scoped `git diff --check` 通过
4. no-motion 边界保持成立：
   - `safe_to_control=false`
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `robot_control_executed=false`
   - `route_execution_success=false`
   - `delivery_success=false`
   - `hil_pass=false`
   - `uses_base_uart=false`

### 未通过项

1. 没有达到 localization ready：
   - `map_server_active=false`
   - `amcl_pose_observed=false`
   - `tf_readiness_summary.blocked_reason=tf_source_probe_not_executed`
   - `map_to_odom_dynamic.observed=false`
   - `map_to_base_link.observed=false`
2. 没有达到 planner-only path attempt：
   - `path_generation_requested=true`
   - `path_generation_attempted=false`
   - `path_generated=false`
   - `planner_server_ready_for_path_generation=false`
   - `path_generation_gate.blocked_reason=path_generation_blocked_by_localization_not_ready`
3. 不接受的口头摘要已被排除：
   - worker 曾口头提过 `managed_runtime_started=true`
   - 但最终 artifact 明确是 `managed_runtime_started=false`
   - closeout 只能以最终 artifact 为准，不能把 `managed_runtime_started=true` 写成最终 live 证据

## 边界核对

- 本轮属于 O3/O1 supporting no-motion delta，不是 mission completion delta。
- 本轮不是：
  - same-run path generation success
  - route execution success
  - delivery success
  - current live HIL pass
  - O5 production / external evidence
- 因此：
  - O5 保持约 `85%`
  - O1/O6/O7 保持约 `93%`
  - 本轮 `不调整` 百分比
  - 本轮 `不归档` KR

## Product 验收判断

- 用户价值和产品北极星：继续为“真实板 fixed-route delivery 之前，先把 no-motion localization/path gate 推到可尝试 planner-only path”的链路服务。
- OKR 方向判断：`继续` O3/O1 supporting no-motion localization/path readiness；`暂停` O5 support-only；`不调整` 百分比；`不归档` KR。
- 下一轮核心抓手：先把 `map_server_active=false` 与 `tf_source_probe_not_executed` 分开修掉，再看 `/amcl_pose` freshness 和 dynamic `map->odom`；只有 localization/TF gate ready 后，才允许进入 planner-only `ComputePathToPose` attempt。
