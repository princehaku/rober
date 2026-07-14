# Tech Plan - O7 Consumer Inference Request

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 `85%`。
- 本 sprint 是否针对最低 Objective：不直接针对 O5。
- 理由：上一轮 `sprints/2026.07.13_13-13_o5_cdn_tls_external_evidence_probe/` 已关闭在 `blocked_http_status_not_success_class`。没有 success-class public CDN/TLS endpoint、OSS upload/origin fetch、production DB/queue、worker cutover、4G/SIM、real phone/browser 或更强 production evidence 时，继续 O5 只会重复 support-only wrapper。本轮改排 O7/O6 的非重复 action/write slice：PC consumer-read selected task 发起 local/mock inference request，写入 O6 `POST /api/o6/archive/inference` 并返回安全 receipt。

## Implementation Owner

- Primary owner: `full-stack-software-engineer`
- Runtime mode: one owner, single-line closure.
- Product owner: `product-okr-owner` only for planning, acceptance wording, closeout, and OKR boundary.

## Allowed Implementation File Scope

后续 full-stack implementation 只能修改：

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.13_15-15_o7_consumer_inference_request/tech-done.md`

禁止修改产品代码范围外文件、硬件/ROS2/nav 文件、`OKR.md`、`docs/process/okr_progress_log.md`、其他历史 sprint、任何 O5/O1/O3 artifact 或 closeout。

## Technical Design

### Current Contract Anchors

- O6 already exposes `POST /api/o6/archive/inference` for O6-KR5 local/mock model inference writes.
- O6 inference success response must use `schema=trashbot.o6.model_inference.v1`, `source=local_mock_inference`, `proof_status=not_proven`, `archive_event_written=true`, and fixed false fields including `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `real_model_inference_success=false`, `real_floor_recognition_proven=false`, and `real_elevator_door_state_proven=false`.
- O6 writes one `model_inference.*` event per `input + requested_output`, currently `model_inference.elevator_door_state` and `model_inference.floor_recognition`.
- Existing O7 consumer detail already includes `inference` as a read model; this sprint adds the missing local/mock request action, not a new readback-only wrapper.

### Planned PC API Shape

Add a fixed O7 PC endpoint similar to existing annotation submit/export action endpoints:

```text
POST /api/o7/consumer-read/tasks/<task_id>/inference/request?baseUrl=<local-loopback-url>
```

The PC endpoint should:

- Validate `baseUrl` as HTTP local-loopback only.
- Require path `task_id` and body `task_id` to match if body includes it.
- Accept only a small object body with safe fields needed to build O6 inference payload.
- Reject unknown fields, arrays where scalar is expected, oversized values, unsafe refs, credentials, raw/base64-like content, `/cmd_vel`, serial path, `baudrate`, traceback, token/password/secret/bearer strings, and any dangerous true claim.
- Generate or accept a safe `inference_id`; generated ids should be deterministic enough for tests but not include raw evidence content.
- Forward only normalized payload to O6 `POST /api/o6/archive/inference`.
- Accept O6 response only when schema, source, write status, result summary, not-proven fields, and fixed false fields match the local/mock contract.
- Return a PC receipt such as `trashbot.pc_tools_workstation.o7_consumer_inference_request_result.v1`.

### Planned Receipt Fields

The O7 receipt should include:

- `schema`
- `proof_status=not_proven`
- `request_status=local_mock_inference_written | local_mock_inference_updated | fail_closed`
- `task_id`
- `robot_id`
- `inference_id`
- `requested_outputs`
- `input_ids`
- `write_status`
- `duplicate`
- `created_count`
- `updated_count`
- `archive_event_written`
- `o6_schema`
- `o6_source=local_mock_inference`
- `result_summary`
- `not_proven`
- fixed false fields: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `real_model_inference_success=false`, `real_floor_recognition_proven=false`, `real_elevator_door_state_proven=false`

### UI Plan

In `O7FixturePreviewPanel.vue` under `O7 consumer read primary path`:

- Add a compact local/mock inference request control for the selected task.
- Reuse selected task context and allow operator to choose `requested_outputs` from `elevator_door_state` and `floor_recognition`.
- Let operator provide or select safe `evidence_ref`, `input_id`, `input_type`, and `captured_at_ms` from existing task summary where practical.
- Button text and receipt state must make this visibly local/mock and not a real model claim.
- Disabled/fail-closed states must appear when no selected task/detail exists, selected task mismatch occurs, unsafe input appears, or the adapter rejects O6 response.

## Test Plan

Full-stack owner should cover:

- Default UI disabled state before selected task.
- Successful local/mock request -> O6 inference write -> O7 receipt.
- Duplicate/update response from O6 keeps idempotent receipt semantics.
- Unsafe request body fails closed before O6 call.
- Unsafe or schema-mismatched O6 response fails closed.
- Docs/contract strings include `consumer inference`, `archive/inference`, `local/mock`, fixed false fields, and rejected proof claims.

## Acceptance Commands For Full-Stack Implementation

Run from `/Users/m1/apps/rober`:

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_15-15_o7_consumer_inference_request
```

## Product Planning Validation Commands

本 Product planning 阶段只运行轻量文档验收，不跑工程测试：

```bash
rg -n "sprint_type: epic|O5|85|consumer inference|archive/inference|local/mock|safe_to_control=false|delivery_success=false|不归档|OKR" sprints/2026.07.13_15-15_o7_consumer_inference_request
git diff --check -- sprints/2026.07.13_15-15_o7_consumer_inference_request
```

## Risk Boundary

- This sprint is O7/O6 `consumer inference` local/mock software proof only.
- It can prove request construction, PC adapter guardrails, O6 `archive/inference` write, receipt shape, and readback boundary.
- It must not prove or imply real model inference, true elevator door recognition, true floor recognition, production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, route execution, delivery, operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or O5 external evidence.
- Fixed safety/mission fields remain `safe_to_control=false`, `delivery_success=false`, `robot_control_executed=false`, `primary_actions_enabled=false`, and `connects_cloud_production=false`.
- OKR main percentages should stay flat unless later implementation produces evidence stronger than this plan. KR `不归档`.
