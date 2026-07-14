# Tech Done - O6/O7 Bounded Route Gate Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/`
- run_time: 2026-07-13 21:57 CST
- Product owner: `product-okr-owner`
- Primary implementation owner: `robot-software-engineer`
- Supporting implementation owner: `full-stack-software-engineer`
- Implementation status: accepted after one O6/O7 contract alignment repair
- Proof boundary: `software_proof_o6_o7_bounded_route_gate_material_intake_only`

## Actual Changes

### O6 Archive And Readback

`robot-software-engineer` implemented `bounded_route_execution_gate_material` as an additive O6 field-evidence/archive/consumer readback section.

Changed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

Delivered behavior:

- O6 accepts and reads back `trashbot.o6.bounded_route_execution_gate_material.v1`.
- Ready status is unified as `bounded_route_execution_gate_material_ready_not_route_execution_proof`.
- It validates the 07:07 gate plus 08:09 bounded plan lineage: `packet_o3_28_pose_same_task_replay_7d57826142b0c79c`, `task_o3_28_pose_fixed_route_consumer_20260713_0402`, `route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`, 28 route rows, 28 structured poses, 27 bounded segments, and `execution_plan_status=blocked_pending_live_safety_gate`.
- It preserves fixed false fields: `safe_to_control=false`, `delivery_success=false`, `route_execution_success=false`, `hil_pass=false`, `robot_control_executed=false`, `connects_cloud_production=false`.
- Hostile control/path/command inputs fail closed to `blocked_not_proven`.

### O7 Selected-Task Intake

`full-stack-software-engineer` implemented selected-task bounded route gate intake and receipt.

Changed files:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

Delivered behavior:

- New PC/O7 endpoint: `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-gate/intake?baseUrl=<local-loopback-url>`.
- The adapter only writes to local-loopback O6 `/api/o6/archive/field-evidence`.
- Receipt schema is `trashbot.pc_tools_workstation.o7_bounded_route_gate_intake_result.v1`.
- UI shows O6 write/readback, packet/task/route/count fields, `blocked_pending_live_safety_gate`, and fixed false fields.
- Non-loopback URL, task mismatch, raw path, raw command, `/cmd_vel`, `/api/base/manual`, NavigateToPose, serial/UART/WAVE ROVER, and route/delivery/HIL/control true claims fail closed.

## Verification Results

Robot Software owner:

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
passed
```

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay
Ran 195 tests in 86.718s
OK
```

```text
rg anchor check
passed; old ready status bounded_route_execution_gate_material_ready_not_control_proof no longer appears in O6/O7 implementation or interface docs, only in this sprint's failure-handling notes
```

```text
git diff --check -- O6 scoped files
passed
```

Full-stack owner:

```text
cd pc-tools/workstation && npm run test
3 files / 510 tests passed
```

```text
cd pc-tools/workstation && npm run build
passed; existing Vite chunk size warning remains
```

```text
cd pc-tools/workstation && npm run lint
passed
```

```text
rg anchor check and scoped git diff --check
passed
```

Product/main-node acceptance checks:

```text
rg -n "bounded_route_execution_gate_material_ready_not_route_execution_proof|bounded_route_execution_gate_material_ready_not_control_proof|software_proof_o6_o7_bounded_route_gate_material_intake_only|local_mock_bounded_route_gate_written|bounded-route-gate/intake" ...
passed; new ready status and endpoint/proof anchors found, old ready status confined to this sprint's historical failure-handling notes
```

```text
git diff --check -- sprint/O6/O7 scoped files
passed
```

## Failure Handling

- Role-specific subagent startup failed with `spawn_agent could not resolve the child model for service tier validation`;主节点按项目记忆中的稳定 fallback 改用 generic `worker` 并保留完整角色 prompt、文件范围和验收命令。
- O6 first pass used ready status `bounded_route_execution_gate_material_ready_not_control_proof`, while O7 and the sprint plan expected `bounded_route_execution_gate_material_ready_not_route_execution_proof`.主节点验收发现该跨 owner contract drift 后，把 O6 退回复修；复修后 O6 195 tests passed，旧 ready status 仅保留在本 sprint 的失败处理说明中。
- O7 first pass reported old UI/fail-reason assertions and duplicate false-field fixture fields; owner fixed them before final `npm test/build/lint` passed.

## Remaining Risk

- This is local/mock O6/O7 software proof only.
- It does not prove real route execution, fixed-route movement, NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, delivery/operator acceptance, current live HIL, safe-to-control, production cloud, production DB/queue, OSS/CDN, 4G/SIM, or O5 external evidence.
- Next live progress still requires explicit operator approval, current live HIL/stop path, same-window LiDAR/localization/TF readiness, Nav2/controller execution result, and delivery/operator acceptance.
