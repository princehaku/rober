# Side To Side Check - O7 Consumer Inference Request

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_15-15_o7_consumer_inference_request/`
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Checked at: 2026-07-13 15:42 CST
- Product decision: accepted as O7/O6 local/mock consumer inference request software proof only
- Proof boundary: `software_proof_o7_o6_consumer_inference_request_only`

## User Value And Product North Star

用户价值：PC operator 可以在 selected task 上直接发起一次 local/mock consumer inference request，让安全输入进入 O6 `POST /api/o6/archive/inference`，并在 O7 receipt 中看到写入状态、created/updated 语义和固定 false safety fields。

产品北极星仍是普通用户送垃圾闭环。本轮只推进 PC 运营调试和数据训练平台的软件闭环：从只读 consumer detail 变成 selected-task local/mock inference write request，不证明真实送达、真实模型或真实生产链路。

## Side By Side Acceptance

| PRD / tech-plan requirement | Implementation evidence from `tech-done.md` | Product result |
|---|---|---|
| O7 selected task exposes bounded `consumer inference` action | `O7FixturePreviewPanel.vue` 增加 selected-task local/mock inference request 控件，UI 从 consumer detail 派生 safe input 并展示 receipt | Accepted |
| PC adapter uses fixed local-loopback O6 inference write path | `o7ConsumerReadAdapter.ts` 新增 `buildO7ConsumerInferenceRequest()`，只转发 O6 `POST /api/o6/archive/inference`，且 baseUrl 仅允许 local-loopback | Accepted |
| O7 route is fixed and not browser-controlled | `index.ts` 新增 `POST /api/o7/consumer-read/tasks/:taskId/inference/request`，浏览器只调用 workstation PC adapter | Accepted |
| Receipt schema is bounded and explicit | O7 result schema is `trashbot.pc_tools_workstation.o7_consumer_inference_request_result.v1` | Accepted |
| Accepted statuses are local/mock only | Accepted statuses include `local_mock_inference_written` and `local_mock_inference_updated`; unsafe or mismatched responses fail closed | Accepted |
| O6 response must stay local/mock and not proven | Adapter accepts only O6 `trashbot.o6.model_inference.v1`, `source=local_mock_inference`, `proof_status=not_proven`, archive write result, and fixed false fields | Accepted |
| Dangerous inputs and claims fail closed | Tests cover unknown fields, unsafe refs, raw/base64-like content, credentials, serial/control text, dangerous true claims, and schema-mismatched O6 responses | Accepted |
| Docs updated | `docs/interfaces/o7_realtime_operator_console.md` and `docs/product/pc_tools_workstation.md` were updated by the full-stack worker | Accepted |

## Verification Accepted

- `cd pc-tools/workstation && npm run test`: PASS, `Test Files 3 passed (3)`, `Tests 496 passed (496)`.
- `cd pc-tools/workstation && npm run build`: PASS, with existing Vite large chunk warning.
- `cd pc-tools/workstation && npm run lint`: PASS.
- Scoped implementation `git diff --check`: PASS.

## Rejected Claims

Product rejects this sprint as proof of real model inference, true elevator door recognition, true floor recognition, production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, route execution, delivery/operator acceptance, HIL, safe-to-control, O5 external evidence, `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART.

Fixed false fields remain: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `real_model_inference_success=false`, `real_floor_recognition_proven=false`, and `real_elevator_door_state_proven=false`.

## OKR And KR Check

- O5 remains about `85%`.
- O1 remains about `94%`.
- O6/O7 remain about `93%`.
- Main percentages: flat.
- KR archival: `不归档`.
- Direction judgment: continue O6/O7 only when the next slice consumes a new mission artifact or creates a non-repeating action/write path; do not count another query/readback or boundary wrapper as progress.

## Remaining Risk And Evidence Gap

The evidence chain is local/mock software proof only. It does not include production cloud, production persistence, real inference output, real camera/media, live robot data, real phone/browser, route execution, delivery/operator acceptance, HIL, or any control command execution.

Next preferred evidence: explicit operator-approved current live HIL/current route execution material, or stronger O5 production/cloud evidence. If those remain blocked, the next O7/O6 item should consume a new mission artifact such as `task_id`, `map.yaml`, `route.csv`, keyframe, rosbag, replay JSONL, or real/mock delivery result instead of repeating read/query wrappers.
