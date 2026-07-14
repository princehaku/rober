# Tech Plan - O6/O7 Bounded Route Gate Intake

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低完成度 Objective 是 O5，约 `85%`。
2. 本 sprint 不直接推进 O5。
3. 切换理由：最近两轮 O5 已 blocked 在 `blocked_http_status_not_success_class`，且 19:19 已消费 readiness packet。当前没有 success-class public endpoint、production DB/queue、worker cutover、OSS/CDN origin fetch/upload、4G/SIM 或 real phone/browser production evidence；继续 O5 会重复 CDN/TLS probe、readiness packet 或 support-only wrapper。

## Owner Routing

主责 owner：`robot-software-engineer`。

协作 owner：`full-stack-software-engineer`。

路由理由：O6 archive/readback 是材料事实源，O7 selected-task action/UI/receipt 是用户触点主路径。两个 owner 文件范围互不重叠，进入 implementation 时应并行派发。

## Technical Approach

新增 O6/O7 bounded route gate material intake：

- O6 增加 `bounded_route_execution_gate_material` consumer detail section，或等价 alias。
- O7 增加 `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-gate/intake?baseUrl=<local-loopback-url>`。
- O7 adapter 将 selected task 的安全 bounded route gate 摘要写入 O6，并立即读取/返回 safe receipt。
- Proof boundary 固定为 `software_proof_o6_o7_bounded_route_gate_material_intake_only`。
- 所有成功和失败输出都固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`、`connects_cloud_production=false`。

## Source Materials

本 sprint 只消费以下已接受材料的安全摘要：

- `sprints/2026.07.13_07-07_o3_controlled_route_execution_gate_record/artifacts/algorithm/controlled_route_execution_gate_record.json`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/artifacts/algorithm/bounded_route_command_plan.json`

关键字段：

- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `path_structured_pose_count=28`
- `segment_count=27`
- `execution_plan_status=blocked_pending_live_safety_gate`

## File Scope

Robot Software owner 允许改：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/tech-done.md`

Full-stack owner 允许改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/tech-done.md`

Sprint closeout 允许主节点改：

- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/side2side_check.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

禁止改：

- 硬件/vendor 文件。
- WAVE ROVER、ESP32、Orange Pi、UART、串口、波特率、引脚、电压或机械配置。
- ROS2 launch、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART。
- O5 CDN/TLS probe、O5 readiness packet consumption、历史 sprint 文件。

## Interface Contract

O6 section suggested shape:

```json
{
  "schema": "trashbot.o6.bounded_route_execution_gate_material.v1",
  "status": "bounded_route_execution_gate_material_ready_not_route_execution_proof",
  "proof_scope": "software_proof_o6_o7_bounded_route_gate_material_intake_only",
  "task_id": "<same task>",
  "packet_id": "<packet id>",
  "route_intent_id": "<route intent id>",
  "execution_plan_status": "blocked_pending_live_safety_gate",
  "route_csv_row_count": 28,
  "path_structured_pose_count": 28,
  "segment_count": 27,
  "global_abort_criteria_count": 11,
  "safe_refs": ["controlled_route_execution_gate_record.json", "bounded_route_command_plan.json"],
  "safe_to_control": false,
  "delivery_success": false,
  "route_execution_success": false,
  "hil_pass": false,
  "robot_control_executed": false
}
```

O7 receipt suggested shape:

```json
{
  "schema": "trashbot.pc_tools_workstation.o7_bounded_route_gate_intake_result.v1",
  "status": "local_mock_bounded_route_gate_written",
  "proof_scope": "software_proof_o6_o7_bounded_route_gate_material_intake_only",
  "same_task_id_consumed": true,
  "bounded_route_execution_gate_material_written": true,
  "bounded_route_execution_gate_material_readback": true,
  "execution_plan_status": "blocked_pending_live_safety_gate",
  "segment_count": 27,
  "safe_to_control": false,
  "delivery_success": false,
  "route_execution_success": false,
  "hil_pass": false,
  "robot_control_executed": false
}
```

## Acceptance Commands

Robot Software owner 必须运行并记录：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
rg -n "bounded_route_execution_gate_material|blocked_pending_live_safety_gate|software_proof_o6_o7_bounded_route_gate_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false|robot_control_executed=false" onboard/src/ros2_trashbot_behavior docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/tech-done.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake
```

Full-stack owner 必须运行并记录：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "bounded-route-gate/intake|o7_bounded_route_gate_intake|bounded_route_execution_gate_material|software_proof_o6_o7_bounded_route_gate_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false|robot_control_executed=false" pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/tech-done.md
git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake
```

Product closeout validation:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|blocked_http_status_not_success_class|software_proof_o6_o7_bounded_route_gate_material_intake_only|safe_to_control=false|delivery_success=false|route_execution_success=false|hil_pass=false|robot_control_executed=false|不归档" sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake OKR.md docs/process/okr_progress_log.md
```

## Risks

- 该路径仍可能只是 local/mock software proof，不会提升 O5/O6/O7 主百分比。
- 如果 O6/O7 只写 receipt 而没有同一 `task_id` readback，Product 不应接受。
- 如果 receipt 接受 raw local path、raw command、`/cmd_vel`、`/api/base/manual`、NavigateToPose、UART、WAVE ROVER 或任何 control/HIL/delivery true 字段，必须 fail closed 并返工。
- 真实 route execution 需要 explicit operator approval、current live HIL/stop path、同窗口 LiDAR/localization/TF readiness、Nav2/controller execution result 和 delivery/operator acceptance，不在本计划阶段证明。
