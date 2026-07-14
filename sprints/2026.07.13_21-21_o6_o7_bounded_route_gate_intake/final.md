# Final - O6/O7 Bounded Route Gate Intake

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/`
- Closeout time: 2026-07-13 21:57 CST
- Product owner: `product-okr-owner`
- Implementation owners: `robot-software-engineer`, `full-stack-software-engineer`
- Final status: accepted, support-only, flat OKR
- Proof boundary: `software_proof_o6_o7_bounded_route_gate_material_intake_only`

## Product Closeout

Product accepts this sprint as O6/O7 bounded route gate material local/mock intake/readback software proof only.

The accepted increment is that the previously accepted 07:07 controlled route execution gate and 08:09 bounded route command plan can now be safely written into O6 field evidence and read back by O7 selected-task consumer detail.

Accepted facts:

- O6 section: `trashbot.o6.bounded_route_execution_gate_material.v1`
- O7 receipt: `trashbot.pc_tools_workstation.o7_bounded_route_gate_intake_result.v1`
- O7 endpoint: `POST /api/o7/consumer-read/tasks/:taskId/bounded-route-gate/intake?baseUrl=<local-loopback-url>`
- Ready status: `bounded_route_execution_gate_material_ready_not_route_execution_proof`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `path_structured_pose_count=28`
- `segment_count=27`
- `execution_plan_status=blocked_pending_live_safety_gate`

Rejected claims:

- route execution, fixed-route movement, NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART
- delivery/operator acceptance, real delivery success, current live HIL, safe-to-control
- production cloud, production DB/queue, OSS/CDN live traffic, 4G/SIM, O5 external evidence success

## Actual Changes

Robot Software delivered O6 archive/readback support in:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/product/cloud_4g_infrastructure.md`
- `docs/product/remote_4g_mvp.md`

Full-stack delivered O7 selected-task intake/receipt support in:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`

Product closeout updated:

- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/tech-done.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/side2side_check.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/final.md`
- `sprints/2026.07.13_21-21_o6_o7_bounded_route_gate_intake/artifacts/product_acceptance_bounded_route_gate_intake.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Verification Evidence

Implementation evidence:

- O6 py_compile passed.
- O6 unittest passed: `Ran 195 tests in 86.718s OK`.
- O6 anchor `rg` and scoped `git diff --check` passed.
- O7 `npm run test` passed: 3 files / 510 tests.
- O7 `npm run build` passed, with the existing Vite chunk size warning.
- O7 `npm run lint` passed.
- O7 anchor `rg` and scoped `git diff --check` passed.

Product acceptance evidence:

- Main-node anchor check confirmed `bounded_route_execution_gate_material_ready_not_route_execution_proof`, `software_proof_o6_o7_bounded_route_gate_material_intake_only`, `local_mock_bounded_route_gate_written`, and `bounded-route-gate/intake` are present.
- Main-node anchor check confirmed old O6 ready status `bounded_route_execution_gate_material_ready_not_control_proof` is confined to this sprint's failure-handling notes and no longer appears as the O6/O7 ready status.
- Scoped `git diff --check` passed for the sprint, O6, O7, and related docs.

## Failure Handling

Role-specific subagent startup failed in this runtime; generic `worker` fallback was used with full role prompts, file scopes, and acceptance commands.

One cross-owner contract drift was caught before closeout: O6 initially used `bounded_route_execution_gate_material_ready_not_control_proof`, while O7 expected `bounded_route_execution_gate_material_ready_not_route_execution_proof`. O6 was returned for a narrow repair and revalidated with `Ran 195 tests in 86.718s OK`.

## OKR Result

- O5: remains about `85%`. The latest O5 blocker is still `blocked_http_status_not_success_class`; this sprint did not repeat that blocker.
- O1: remains about `94%`. No live HIL, route execution, or safe-to-control evidence was collected.
- O6: remains about `93%`. A distinct bounded route gate material intake/readback path was added, but it is local/mock software proof only.
- O7: remains about `93%`. A selected-task O7 receipt path was added, but it is not real route execution or delivery.
- KR archival: `不归档`.
- Main percentages: unchanged.

## Remaining Risk And Next Step

Remaining risk:

- This sprint does not prove route execution, delivery/operator acceptance, current live HIL, safe-to-control, production cloud, production DB/queue, OSS/CDN, 4G/SIM, or O5 external evidence.
- The next live route step still needs explicit operator approval, current live HIL/stop path, same-window LiDAR/localization/TF readiness, Nav2/controller result, and delivery/operator acceptance.

Next recommendation:

Do not repeat O6/O7 readback wrappers. Next sprint should move only if it can collect explicit-operator-approved current live HIL/current route evidence, or if O5 gets stronger production evidence such as success-class public endpoint, production DB/queue, worker cutover, OSS/CDN live traffic, 4G/SIM, or real phone/browser production proof.
