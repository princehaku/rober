# Final - O7 Consumer Inference Request

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_15-15_o7_consumer_inference_request/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Final status: accepted as bounded O7/O6 local/mock consumer inference request software proof
- Closed at: 2026-07-13 15:42 CST

## Actual Changes Accepted

Product accepts the implementation described in `tech-done.md`:

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_15-15_o7_consumer_inference_request/tech-done.md`

Product closeout added:

- `sprints/2026.07.13_15-15_o7_consumer_inference_request/side2side_check.md`
- `sprints/2026.07.13_15-15_o7_consumer_inference_request/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Product Acceptance Decision

Accepted as: O7/O6 local/mock consumer inference request software proof only.

Proof boundary: `software_proof_o7_o6_consumer_inference_request_only`.

Accepted facts:

- PC/O7 exposes `POST /api/o7/consumer-read/tasks/:taskId/inference/request`.
- The adapter forwards only fixed O6 `POST /api/o6/archive/inference`, and only for a local-loopback `baseUrl`.
- O7 receipt schema is `trashbot.pc_tools_workstation.o7_consumer_inference_request_result.v1`.
- Accepted local/mock request statuses include `local_mock_inference_written` and `local_mock_inference_updated`.
- Unsafe request fields, unsafe content, dangerous true claims, non-local base URLs, and schema-mismatched O6 responses fail closed.
- Fixed false fields are preserved: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `real_model_inference_success=false`, `real_floor_recognition_proven=false`, and `real_elevator_door_state_proven=false`.

Rejected as:

- real model inference
- true elevator door recognition
- true floor recognition
- production cloud, production DB/queue, OSS/CDN, 4G/SIM, or real phone/browser proof
- route execution, delivery/operator acceptance, HIL, or safe-to-control
- O5 external evidence
- `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART

## OKR And KR Result

- O5 remains about `85%`.
- O1 remains about `94%`.
- O6/O7 remain about `93%`.
- Main percentages: no adjustment.
- KR archival: `不归档`.
- Direction: continue, but treat this sprint as local/mock action/write software proof only. It is stronger than another read/query wrapper, but still below production/cloud, live route, delivery, HIL, or real model evidence.

## Verification Result

Engineer verification from `tech-done.md` passed:

- workstation `npm run test`: `Test Files 3 passed (3)`, `Tests 496 passed (496)`.
- workstation `npm run build`: passed with existing Vite large chunk warning.
- workstation `npm run lint`: passed.
- scoped `git diff --check`: passed.

Product light acceptance commands:

- `rg -n "2026-07-13 15|consumer inference|archive/inference|o7_consumer_inference_request_result|software_proof_o7_o6_consumer_inference_request_only|local_mock_inference_written|Tests 496 passed|safe_to_control=false|delivery_success=false|real_model_inference_success=false|不归档|O5.*85|O6/O7.*93" OKR.md docs/process/okr_progress_log.md sprints/2026.07.13_15-15_o7_consumer_inference_request/side2side_check.md sprints/2026.07.13_15-15_o7_consumer_inference_request/final.md`: passed after closeout.
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.13_15-15_o7_consumer_inference_request`: passed after closeout.

## Remaining Risk And Next Recommendation

Remaining risk: this proves only local/mock PC/O7 request construction, adapter guardrails, O6 local/mock `archive/inference` write receipt handling, and UI receipt rendering. It does not prove real model inference, true elevator/floor recognition, production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, route execution, delivery/operator acceptance, HIL, safe-to-control, or O5 external evidence.

Next recommendation: prioritize explicit operator-approved current live HIL/current route execution evidence, or stronger O5 production/cloud evidence. If those remain blocked, only take another O7/O6 slice when it consumes a new mission artifact or creates a non-repeating action/write path tied to `task_id`, `map.yaml`, `route.csv`, keyframe, rosbag, replay JSONL, or real/mock delivery result.
