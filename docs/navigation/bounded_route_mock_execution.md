# Bounded Route Mock Execution

本文记录 `sprints/2026.07.13_23-23_o3_bounded_route_mock_execution/` 的 O3/O1 严格 no-motion 路线执行仿真材料。

## 目标

- 输入：`sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`。
- 输出：`bounded_route_mock_execution_summary.json` 与 `bounded_route_mock_execution_progress.jsonl`。
- 边界：`software_proof_o3_o1_bounded_route_mock_execution_only`。
- 状态：`mock_route_execution_completed_not_live_route_execution`。

该材料只证明 28-pose bounded route command plan 可以被离线消费，并生成 27 条 segment completion mock progress events。它不是 live route execution，不证明固定路线移动、controller/BT 执行、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART、HIL、delivery、safe-to-control 或 O5 production external evidence。

## 输入校验

CLI `onboard/scripts/o3_bounded_route_mock_execution.py` 在写出任何 artifact 前必须校验：

- source schema 为 `trashbot.o3.bounded_route_command_plan.v1`。
- `execution_plan_status=blocked_pending_live_safety_gate`。
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`。
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`。
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`。
- `route_csv_row_count=28` 且 `segment_count=27`，并逐段复核 `segment_index` 与 `from_order -> to_order` 连续。
- no-motion guards 同时包含 `no /cmd_vel`、`no /api/base/manual`、`no NavigateToPose`、`no WAVE ROVER UART`。
- 顶层与 `fixed_false_fields` 均保持 `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。

任一字段漂移时脚本返回非零，不写 summary 或 progress JSONL，并在 stderr 中继续输出 false 安全字段。

## 输出语义

`bounded_route_mock_execution_summary.json` 是本轮机器验收入口，包含 source identity、source counts、27 条 progress event 计数、mock 总距离、mock 总耗时和 rejected claims。

`bounded_route_mock_execution_progress.jsonl` 每行是一条 `mock_segment_completed_not_live_control` event，包含：

- `segment_index`、`from_order`、`to_order`。
- `distance_m`、`elapsed_s`、`cumulative_distance_m`、`cumulative_elapsed_s`。
- source `packet_id`、`task_id`、`route_intent_id`。
- 所有 live-control 和 success 字段继续为 false。

`elapsed_s` 是 `distance_m / planned_linear_speed_cap_mps` 计算出的 deterministic mock 值，不是墙钟时间，也不是 controller feedback。

## 验收边界

本轮可接受结论：

- bounded route command plan 的 identity/count/no-motion guard 可被离线复核。
- 28-pose route 被转成 27 条 mock segment completion progress events。
- summary 与 JSONL 均固定 false safety fields。

本轮不可接受结论：

- `route_execution_success=false` 不能改成 true。
- `safe_to_control=false` 不能改成 true。
- 不能声明 fixed-route movement、Nav2 controller result、delivery/operator acceptance、current live HIL、WAVE ROVER UART 或 O5 production evidence 已完成。

下一步只有在 explicit live safety gate、stop/HIL 材料、同窗口 `/scan`/localization/TF readiness、Nav2/controller result 和 operator acceptance 都可记录时，才可以进入 controlled route execution evidence。
