# O3 Map Server TF Source Recovery Side-to-Side Check

## 对照范围

- 本轮 sprint：`sprints/2026.07.11_22-48_o3_map_server_tf_source_recovery/`
- 上一轮对照：`sprints/2026.07.11_21-47_o3_amcl_lifecycle_path_generation_repair/`
- 对照对象：`pre_start.md`、`prd.md`、`tech-plan.md`、`tech-done.md`、local/live artifacts、上一轮 `final.md`

## 用户价值和产品北极星

用户真正需要的是机器人沿固定路线稳定送垃圾。本轮仍处于 strict no-motion supporting lane，价值不是宣称已能生成路径，而是把真实板 no-motion localization chain 从 `tf_source_probe_not_executed` / source-preflight 歧义，继续前移到更窄的 managed runtime wait graph、`/tf` 缺失和 AMCL rclpy import root cause，为下一轮真正恢复 localization/path attempt 铺路。

## 计划对照

- `pre_start.md` 设定的本轮抓手是拆开 `map_server_active=false` 与 `tf_source_probe_not_executed`。
- `prd.md` 要求本轮只计 O3/O1 no-motion supporting delta，`不调整` O5/O1/O6/O7 百分比，`不归档` KR。
- `tech-plan.md` 要求：若没有 `path_generation_attempted=true`，也必须把 blocker 比 `21-47` 再缩窄一层。

对照结论：本轮满足计划口径。虽然 `path_generation_attempted=false`、`path_generated=false` 仍未变化，但 blocker 没有停留在 `21-47` 的 `tf_source_probe_not_executed`；live artifact 已前移到 managed runtime wait graph probe timeout、`rclpy_node_names_failed`、`/tf_topic_missing` 与 `librcl_action.so` / `_rclpy_pybind11` import chain。

## 与 21-47 的事实对照

### 已前移的事实

- 上一轮 `21-47`：
  - `tf_readiness_summary.blocked_reason=tf_source_probe_not_executed`
  - `managed_runtime_started=false`
  - `board_source_preflight_rclpy_import_timeout`
- 本轮 `22-48` live artifact：
  - `status=partial_runtime_in_progress`
  - `evidence_type=partial_runtime_material`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `managed_runtime_started=true`
  - `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
  - `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
  - `tf_readiness_summary.blocked_reason=/tf_topic_missing`
  - `tf_source_root_cause_detail.amcl_param_probe_error` 命中 `librcl_action.so` / `_rclpy_pybind11` ImportError

### 仍未通过的门槛

- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
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
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` 输出 `Ran 74 tests in 2.239s OK`
- local helper exit `2`，按预期 fail-closed
- `scp` exit `0`
- live partial artifact pulled 成功
- artifact invariant check passed
- scoped `git diff --check` passed

## Product 验收判断

1. 本轮是有效的 O3/O1 supporting no-motion diagnostic delta。
2. 本轮不是 path generation success，不是 route execution，不是 delivery/operator acceptance，不是 HIL，也不是 production external evidence。
3. 本轮不触发“与 21-47 完全同一 blocker 的重复消费”，因为 blocker 已从 `tf_source_probe_not_executed` / source-preflight 歧义前移到 `managed_runtime_wait_timeout`、`rclpy_node_names_failed`、`/tf_topic_missing` 和 AMCL rclpy import chain。
4. 但 path/lifecycle 仍 blocked，下一轮必须继续 O3，不能回到 O5 support-only。

## 收口建议

- `final.md` 应明确把 live artifact 定义为 `partial_runtime_in_progress` / `partial_runtime_material`，不是 completed/final artifact。
- `OKR.md` 与 `docs/process/okr_progress_log.md` 只记录 supporting delta，不上调 O5/O1/O6/O7 百分比，不归档 KR。
- 下一轮继续由 `robot-algorithm-engineer` 单线闭环，优先修：
  1. board-side managed-runtime wait graph probe 的 `rclpy_node_names_failed`
  2. AMCL rclpy inventory import/runtime 的 `librcl_action.so` / `_rclpy_pybind11` 导入链
