# Algorithm Worker Report

## 自主能力目标和本轮抓手

- 目标：把同一 `task_id` 下的 route execution result、delivery result readiness 和 operator confirmation readiness 收束成一个 fail-closed 的 Algorithm 摘要，供 O6/O7 继续消费。
- 抓手：复用已有 `nav2_goal_execution_evidence`、`delivery_result_evidence`、`route_bag_pose_progress_replay` 与 `field_motion_evidence_packet.route_bag_or_live_nav2_log`，不新增原始输入合同。

## 改动文件和接口影响

- [`/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/scripts/field_route_evidence_manifest.py)
  - 新增 `trashbot.route_execution_result_delivery_readiness.v1` / `software_proof_route_execution_result_delivery_readiness_only`。
  - 新增 `build_route_execution_result_delivery_readiness()`，并把摘要同时写入 manifest 顶层和 `field_motion_evidence_packet.route_execution_result_delivery_readiness`。
- [`/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py`](/Users/m1/apps/rober/onboard/tests/test_field_route_evidence_manifest.py)
  - 新增 ready、missing、delivery claim conflict 三组单测。
- [`/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md`](/Users/m1/apps/rober/docs/navigation/field_route_evidence_manifest.md)
  - 补充 readiness 合同、状态门槛和 fail-closed 约束。

## 实现内容

- 统一输出字段：
  - `schema`, `proof_scope`, `status`, `source`, `task_id`, `task_id_source`
  - `route_execution_result_status`, `route_execution_source`, `route_execution_result_ready`, `route_execution_success=false`
  - `delivery_result_readiness_status`, `delivery_result_source`, `delivery_result_readiness_ready`
  - `operator_confirmation_readiness_status`, `operator_confirmation_source`, `operator_confirmation_readiness_ready`
  - `linked_nav2_goal_execution_proven`, `linked_delivery_result_claimed`, `linked_operator_confirmation_present`
  - `blocked_reasons`, `next_required_evidence`
- ready 条件保守收敛为：
  - Nav2 goal additive 已 ready 且 `nav2_goal_execution_proven=true`
  - pose progress additive 已 ready 且 `nonzero_pose_progress_observed=true`
  - delivery result additive 已 ready 且 `delivery_result_claimed=true`
  - operator confirmation 已 present
- 任何 linked schema mismatch、dangerous true、unsafe 计数、route bag/live log 缺失或 delivery/operator 状态冲突，都会保持 `status=blocked_not_proven`。
- 所有安全字段固定保持：
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`

## 测试、dry-run 或上车验证结果

- `python3 -m py_compile onboard/scripts/field_route_evidence_manifest.py`
  - 通过
- `python3 -m unittest onboard.tests.test_field_route_evidence_manifest`
  - 本轮新增用例通过，整体见主节点验收日志
- manifest smoke
  - `route_execution_result_delivery_readiness.status=route_execution_result_delivery_readiness_ready_not_delivery_proof`
  - `route_execution_result_ready=true`
  - `delivery_result_readiness_ready=true`
  - `operator_confirmation_readiness_ready=true`
  - `safe_to_control=false`
  - `delivery_success=false`

## 数据、样本或调试输出变化

- readiness 摘要现在可从 manifest 顶层直接读取，也可从 `field_motion_evidence_packet.route_execution_result_delivery_readiness` 读取。
- smoke 输出中的 `route_execution_source` 现在会保守显示 `nav2_goal_execution_evidence+route_bag_pose_progress_replay`，便于 O6/O7 追踪结果链来源。

## 剩余风险和下一步能力建设建议

- 当前 readiness 只证明同一 `task_id` 的软件侧结果链可读回，不证明真实 live Nav2、真实 delivery record、真实 operator confirmation 或真实送达成功。
- 下一步应由 O6/O7 保持同一合同继续 ingest/readback/UI 展示，不要自行扩展另一套结果链字段。
