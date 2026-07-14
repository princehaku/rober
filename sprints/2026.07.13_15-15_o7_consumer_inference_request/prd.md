# PRD - O7 Consumer Inference Request

## Product Objective

在 O7 PC consumer-read primary path 上增加一个明确的 local/mock inference request action。operator 选中 O6/O7 consumer task 后，可以选择一个安全 `evidence_ref` / `input_id`，请求 `elevator_door_state` 和/或 `floor_recognition`，由 PC 后端调用 O6 `POST /api/o6/archive/inference`，并把 O6 返回的写入结果压成安全 receipt 展示。

这条链路的产品目标不是证明模型能力，而是补齐 O7 从“只读消费 O6 inference section”到“可以发起一次 O6-KR5 local/mock 模型推理写入”的非重复软件闭环。

## User Value

- Operator 可以围绕 selected task 直接触发一次本地/模拟推理请求，不需要手写 curl 或回到 O6 后端调试。
- O6 archive 的 `model_inference.*` events 成为同一 task 的 timeline 材料，后续 O7 detail/readback 可以继续从 `inference` section 读取。
- Receipt 清楚展示 request 是否写入、幂等命中、写入了哪些 `input_id/result_type`，同时持续提示 `not_proven` 和固定 false safety fields。

## OKR Mapping And Direction

- Primary mapping: Objective 7 KR3/KR4/KR5 shared PC consumer path, because PC workstation is the operator surface that consumes task detail and inference summaries.
- Secondary mapping: Objective 6 KR5, because actual write target is O6 `POST /api/o6/archive/inference`, which creates local/mock `model_inference.*` events.
- Direction judgment: continue O6/O7 software closure, but do not raise main OKR percentages in planning. Implementation can be accepted only as local/mock software proof.
- O5 remains the lowest Objective at about `85%`, but this sprint intentionally does not repeat O5 CDN/TLS while the last O5 closeout remains `blocked_http_status_not_success_class`.
- KR archival: `不归档`.

## In Scope

- Add a PC-side action in `O7 consumer read primary path` for selected task inference request.
- Support only O6 currently allowed `requested_outputs`: `elevator_door_state` and `floor_recognition`.
- Use selected task fields and safe UI inputs to produce O6 inference payload fields:
  - `robot_id`
  - `task_id`
  - `inference_id`
  - `model_family`
  - `requested_outputs[]`
  - `inputs[].input_id`
  - `inputs[].input_type`
  - `inputs[].evidence_ref`
  - `inputs[].captured_at_ms`
  - optional small `metadata`
- Return a PC receipt that includes O6 write status, duplicate semantics, result summary, and fixed false proof boundary.
- Add tests for success, duplicate/update, unsafe payload rejection, unknown/unauthorized task handling when mockable through fixture/server tests, and UI disabled/fail-closed states.
- Update O7 interface docs, PC product docs, and sprint `tech-done.md` during implementation.

## Out Of Scope

- No real GPU model, external model API, real elevator door recognition, real floor recognition, real camera/media fetch, production DB/queue, OSS/CDN, public cloud, 4G/SIM, real phone/browser proof, route execution, delivery, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or hardware work.
- No O5 CDN/TLS rerun.
- No O1/O3 route readiness, route command plan, stop path, or HIL wrapper.
- No generic query/readback-only O7 wrapper.

## Acceptance Criteria

1. O7 UI exposes a bounded local/mock `consumer inference` action only after a selected task is loaded or explicitly selected.
2. PC Node adapter exposes a fixed route for this action and only calls O6 `POST /api/o6/archive/inference` on local-loopback `baseUrl`.
3. Unknown fields, repeated/array query values where not expected, credentials, external URL, unsafe refs, raw/base64-like content, token/password/secret/bearer strings, `/cmd_vel`, serial path, `baudrate`, traceback, and dangerous true fields fail closed before O6 write.
4. O6 success response is accepted only when schema, source, proof fields, write status, and fixed false fields match the local/mock inference contract.
5. O7 receipt and UI display `safe_to_control=false`, `delivery_success=false`, `robot_control_executed=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `real_model_inference_success=false`, and `not_proven`.
6. Tests, build, lint, and scoped diff check pass in the workstation scope.
7. Docs record the local/mock proof boundary and explicitly reject real model, real elevator recognition, production cloud, route execution, delivery, HIL and safe-to-control claims.

## Priority And Owner

- Priority: P1 for this automation window because it is the lowest non-repeating O6/O7 software closure available while O5 and live route/HIL are blocked.
- Responsible engineer: `full-stack-software-engineer`.
- Product owner: `product-okr-owner` for scope, acceptance wording, OKR boundary, and closeout after implementation evidence exists.

## Evidence Required Before Closeout

- `tech-done.md` with actual changes, verification logs, failure positioning if any, remaining risks, and proof boundary.
- Workstation tests/build/lint logs.
- Scoped `git diff --check` result.
- Docs updated in `docs/interfaces/o7_realtime_operator_console.md` and `docs/product/pc_tools_workstation.md`.
- Product closeout docs must be created only after implementation/acceptance, not in this planning phase.

## Historical KR Record Position

No KR is completed or moved to historical records in this planning phase. If implementation passes, the evidence should be recorded under the current O6/O7 sections and the sprint closeout, with KR archival still `不归档` unless a later sprint adds production or real mission evidence.
