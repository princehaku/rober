# Tech Plan - O6/O7 Bounded Route Terminal Result Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/`
- Product owner: `product-okr-owner`
- Implementation owners: `robot-software-engineer`, `full-stack-software-engineer`
- Planned proof boundary: `software_proof_o6_o7_bounded_route_terminal_result_intake_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节最低完成度 Objective 是 O5：云中转控制面产品化，约 `85%`。
2. 本 sprint 不直接推进 O5。
3. 切换理由：最近 O5 已连续消费本地 support-only gate/bridge，而真实 success-class public HTTPS/TLS、production DB/queue、worker cutover、OSS/CDN live traffic、4G/SIM 或 real phone/browser production evidence 仍不可得。继续 O5 会重复“无真实 production/external evidence”的同根 blocker。本轮改为消费 00:24 已接受 terminal-result bridge，推进次低 O6/O7 的 same-task readback 闭环。

## Owner Routing

并行派发：

- `robot-software-engineer`：O6 archive/readback section。
- `full-stack-software-engineer`：O7 selected-task endpoint、adapter、receipt、UI/API 和 workstation tests。

接口耦合点由本 tech-plan 固定：O6 section name、schema、ready status、proof boundary、required identity fields 和 fixed false fields。两个 owner 不共享产品代码文件；主节点最后汇总 `tech-done.md`、`side2side_check.md` 和 `final.md`。

## Technical Approach

新增 terminal-result material intake/readback：

- O6 additive section name: `bounded_route_terminal_result_material`
- O6 schema: `trashbot.o6.bounded_route_terminal_result_material.v1`
- O6 ready status: `bounded_route_terminal_result_material_ready_not_delivery_proof`
- O7 endpoint: `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-terminal-result/intake?baseUrl=<local-loopback-url>`
- O7 receipt schema: `trashbot.pc_tools_workstation.o7_bounded_route_terminal_result_intake_result.v1`
- Proof boundary: `software_proof_o6_o7_bounded_route_terminal_result_intake_only`

Source material:

`sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`

Required source identity:

- `source_schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`
- `source_proof_boundary=software_proof_o5_bounded_route_terminal_result_bridge_only`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `path_structured_pose_count=28`
- `segment_count=27`
- `terminal_result_state=terminal_result_recorded`
- `reconciliation_state=terminal_result_recorded`
- `result_code=mock_route_execution_completed_not_live_delivery`

## Interface Contract

O6 section shape:

```json
{
  "schema": "trashbot.o6.bounded_route_terminal_result_material.v1",
  "status": "bounded_route_terminal_result_material_ready_not_delivery_proof",
  "proof_scope": "software_proof_o6_o7_bounded_route_terminal_result_intake_only",
  "source_schema": "trashbot.o5.bounded_route_terminal_result_bridge.v1",
  "source_proof_boundary": "software_proof_o5_bounded_route_terminal_result_bridge_only",
  "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
  "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
  "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
  "result_code": "mock_route_execution_completed_not_live_delivery",
  "terminal_result_state": "terminal_result_recorded",
  "reconciliation_state": "terminal_result_recorded",
  "safe_evidence_ref": "o5_bounded_route_terminal_result_bridge_summary.json",
  "delivery_success": false,
  "route_execution_success": false,
  "safe_to_control": false,
  "hil_pass": false,
  "robot_control_executed": false,
  "connects_cloud_production": false
}
```

O7 receipt shape:

```json
{
  "schema": "trashbot.pc_tools_workstation.o7_bounded_route_terminal_result_intake_result.v1",
  "status": "local_mock_bounded_route_terminal_result_written",
  "proof_scope": "software_proof_o6_o7_bounded_route_terminal_result_intake_only",
  "same_task_id_consumed": true,
  "bounded_route_terminal_result_material_written": true,
  "bounded_route_terminal_result_material_readback": true,
  "result_code": "mock_route_execution_completed_not_live_delivery",
  "terminal_result_state": "terminal_result_recorded",
  "reconciliation_state": "terminal_result_recorded",
  "delivery_success": false,
  "route_execution_success": false,
  "safe_to_control": false,
  "hil_pass": false,
  "robot_control_executed": false,
  "connects_cloud_production": false
}
```

## File Scope

Robot Software owner may edit:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

Full-stack owner may edit:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

Main-node closeout may edit:

- `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/tech-done.md`
- `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/side2side_check.md`
- `sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Forbidden:

- Hardware/vendor files.
- WAVE ROVER, ESP32, Orange Pi, UART, baudrate, voltage, pin, firmware or mechanical configuration.
- ROS2 launch, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART.
- Historical source artifact edits.

## Acceptance Commands

Robot Software owner must run:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
rg -n "bounded_route_terminal_result_material|bounded_route_terminal_result_material_ready_not_delivery_proof|software_proof_o6_o7_bounded_route_terminal_result_intake_only|mock_route_execution_completed_not_live_delivery|delivery_success=false|route_execution_success=false|safe_to_control=false|hil_pass=false|robot_control_executed=false" onboard/src/ros2_trashbot_behavior docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/o6_cloud_archive_api.md docs/product/cloud_4g_infrastructure.md docs/product/remote_4g_mvp.md
```

Full-stack owner must run:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
rg -n "bounded-route-terminal-result/intake|o7_bounded_route_terminal_result_intake|bounded_route_terminal_result_material|software_proof_o6_o7_bounded_route_terminal_result_intake_only|mock_route_execution_completed_not_live_delivery|delivery_success=false|route_execution_success=false|safe_to_control=false|hil_pass=false|robot_control_executed=false" pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md
git diff --check -- pc-tools/workstation/src pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md
```

Product closeout validation:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|software_proof_o6_o7_bounded_route_terminal_result_intake_only|bounded_route_terminal_result_material_ready_not_delivery_proof|local_mock_bounded_route_terminal_result_written|delivery_success=false|route_execution_success=false|safe_to_control=false|hil_pass=false|robot_control_executed=false|不归档" sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.07.14_01-24_o6_o7_bounded_route_terminal_result_intake OKR.md docs/process/okr_progress_log.md
```

## Risks

- This is still local/mock software proof and likely flat OKR.
- If O6/O7 do not read back the same `task_id`, Product must reject.
- If any true field appears for delivery, route execution, HIL, safe-to-control, production cloud or robot control, the owner must repair and rerun verification.
- Real progress beyond support-only still needs explicit operator approval, current live HIL/stop path, same-window LiDAR/localization/TF readiness, Nav2/controller result, delivery/operator acceptance or success-class production evidence.
