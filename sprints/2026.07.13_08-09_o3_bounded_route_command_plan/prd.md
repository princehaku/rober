# PRD - O3 Bounded Route Command Plan

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Proof boundary: `software_proof_o3_o1_no_motion_bounded_route_command_plan_only`

## 产品目标

把 07:07 accepted controlled route execution gate record 里的下一步缺口之一，收敛成可机器校验的 bounded route command plan with abort criteria。该计划只用于未来受控 live execution sprint 的输入准备，不触发机器人运动。

## 用户价值

北极星是让普通用户交付垃圾后，小车能安全沿固定路线送达。本轮不交付路线执行成功，但减少未来发车前的模糊性：同一 28-pose route packet 需要怎样的速度上限、段间距离、abort 条件、观测前置项和 false safety fields，必须在执行前被结构化记录和复核。

## 输入事实

权威输入：

- Gate record: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- Gate sprint closeout: `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/final.md`
- Source packet summary: `sprints/2026.07.13_05-02_o3_28_pose_same_task_replay_packet/artifacts/algorithm/same_task_replay_packet_summary.json`

必须保持：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `packet_jsonl_event_count=28`
- `path_structured_pose_count=28`

必须固定 false：

- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`

## 需求

1. 生成 `trashbot.o3.bounded_route_command_plan.v1` artifact，路径建议为 `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`。
2. 从 07:07 gate record 读取 source refs，复核 identity、28/28/28 counts、false safety fields 和 no-motion guards。
3. 基于 28 行 route CSV 生成段级计划 summary：segment count、total path distance、max segment distance、nominal linear/angular speed caps、estimated duration、per-segment abort checks。
4. 输出全局 abort criteria，至少覆盖 operator stop、localization stale、LiDAR stale/no sample、TF missing, controller result missing、route deviation、timeout、battery/IMU unknown、any control permission false。
5. 输出 `execution_plan_status=blocked_pending_live_safety_gate` 或更保守状态；不得输出 success-like execution status。
6. artifact 和测试必须包含 literal guard anchors：no `/cmd_vel`、no `/api/base/manual`、no NavigateToPose、no WAVE ROVER UART。
7. 同步更新 `docs/navigation/fixed_route_workflow.md`，说明 08:09 bounded plan 只是 no-motion execution-prep material。
8. 更新 `tech-done.md`，记录实际改动、验证输出、失败定位和剩余风险。

## 非目标

- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不调用 NavigateToPose、Nav2 controller/BT 或 ROS2 action execution。
- 不访问 WAVE ROVER UART。
- 不修改 hardware driver、launch、O6/O7 UI/API、production cloud 或 `OKR.md`。
- 不宣称 route execution、fixed-route movement、delivery/operator acceptance、HIL、safe-to-control 或 O5 production/external evidence。

## 验收口径

Product 只接受本轮为 O3/O1 no-motion bounded route command plan。若 artifact 证明 07:07 gate record 可被消费、28 pose 可生成受控执行前计划、abort criteria 清楚且所有 safety/control fields 仍 false，则本轮通过。OKR 主百分比预计不调整，KR `不归档`。
