# Same-Window Route Readiness Precheck

本文记录 `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/` 的 O3/O1 严格 no-motion same-window route readiness precheck。

## 目标

- 输入：
  - `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
  - `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`
  - `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_summary.json`
  - `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/artifacts/algorithm/bounded_route_mock_execution_progress.jsonl`
- 输出：`same_window_route_readiness_precheck_summary.json`
- 边界：`software_proof_o3_o1_same_window_route_readiness_precheck_only`
- 状态：`blocked_missing_same_window_live_evidence`

该材料只把 07:07 controlled gate、08:09 bounded plan、23:23 bounded route mock execution 汇总成下一次 same-window live route/HIL capture 前的 blocker checklist。它不是 live route execution，不证明 fixed-route movement、Nav2 controller/BT execution、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、HIL、delivery、safe-to-control 或 O5 production/cloud evidence。

## 输入校验

CLI `onboard/scripts/o3_same_window_route_readiness_precheck.py` 在写出 summary 前必须校验：

- gate record schema 为 `trashbot.o3.controlled_route_execution_gate_record.v1`，且 `controlled_route_execution_gate_status=fail_closed_input_packet_validated`。
- bounded plan schema 为 `trashbot.o3.bounded_route_command_plan.v1`，且 `execution_plan_status=blocked_pending_live_safety_gate`。
- mock summary schema 为 `trashbot.o3.bounded_route_mock_execution.v1`，且 `mock_execution_status=mock_route_execution_completed_not_live_route_execution`。
- progress JSONL 正好 27 条 `mock_segment_completed_not_live_control` event。
- route identity 完全一致：`packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`、`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`。
- `route_csv_row_count=28` 且 `segment_count=27`。
- no-motion guards 同时包含 `no /cmd_vel`、`no /api/base/manual`、`no NavigateToPose`、`no WAVE ROVER UART`。
- 顶层、`fixed_false_fields` 和 progress events 均保持 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。

任一字段漂移时脚本返回非零，不写 success-shaped summary，并在 stderr 继续固定 false safety fields。

## 输出语义

`same_window_route_readiness_precheck_summary.json` 是下一轮 route/HIL capture 的机器可读前置门。核心字段：

- `schema=trashbot.o3.same_window_route_readiness_precheck.v1`
- `same_window_route_readiness_status=blocked_missing_same_window_live_evidence`
- `proof_boundary=software_proof_o3_o1_same_window_route_readiness_precheck_only`
- `next_live_capture_allowed=false`
- `missing_evidence` 必须包含：
  - `explicit_operator_approval`
  - `current_live_stop_hil`
  - `same_window_scan_readiness`
  - `same_window_amcl_pose_readiness`
  - `same_window_map_to_odom_tf_readiness`
  - `nav2_controller_result`
  - `delivery_or_operator_acceptance`

这些 missing evidence 是本轮的真实结论：已有 route material 可以被离线复核，但同窗口 live route/HIL 前置材料仍缺失，所以不能发车，也不能把 mock progress 转成 route execution success。

## 验收边界

本轮可接受结论：

- accepted route chain 的 `packet_id`、`task_id`、`route_intent_id`、28 行 route 与 27 段 mock progress 可被离线统一复核。
- same-window live blocker 被明确列出。
- summary 与 source progress 均固定 false safety fields。

本轮不可接受结论：

- `route_execution_success=false` 不能改成 true。
- `delivery_success=false` 不能改成 true。
- `hil_pass=false` 不能改成 true。
- `safe_to_control=false` 不能改成 true。
- 不能声明 `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、fixed-route movement、Nav2 controller result、delivery/operator acceptance、current live HIL 或 O5 production evidence 已完成。

下一步只有在 explicit operator approval、current live stop/HIL、同窗口 `/scan`、AMCL pose、dynamic `map_to_odom` TF、Nav2/controller result 和 delivery/operator acceptance 都可采集时，才可以进入 controlled route execution evidence sprint。
