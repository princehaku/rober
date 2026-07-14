# Tech Done - O7 Consumer Inference Request

## Sprint Type

- sprint_type: epic
- owner: full-stack-software-engineer
- run_time: 2026-07-13 15:37:50 CST

## Actual Changes

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 `buildO7ConsumerInferenceRequest()`，提供 PC endpoint 背后的 O7 adapter。
  - 固定转发 O6 `POST /api/o6/archive/inference`，不接受浏览器传入远端 endpoint、token 或任意控制字段。
  - 新增 local-loopback、path/body task_id、unknown fields、body size、requested_outputs、inputs、metadata、unsafe refs、raw/base64-like 内容、credential、serial/control 字符串和 dangerous true claim 校验。
  - 只接受 O6 `trashbot.o6.model_inference.v1` / `source=local_mock_inference` / `proof_status=not_proven` / `archive_event_written=true` / `write_status=created|updated` 且固定 false fields 全部为 false 的响应。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/o7/consumer-read/tasks/:taskId/inference/request` route。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postO7ConsumerInferenceRequest()`，浏览器只调用 workstation PC adapter。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `O7ConsumerInferenceRequestBody` / `O7ConsumerInferenceRequestResult` 等类型。
  - `API_ROUTES` 增加 O7 consumer inference request endpoint。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 `O7 consumer read primary path` 增加 selected-task local/mock inference request 控件。
  - UI 默认从 consumer detail 的 task/trajectory/evidence 摘要派生 safe input，也允许 operator 填写安全字段。
  - 展示 receipt、O6 schema/source、created/updated counts、archive write 状态、not_proven 和固定 false fields。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 O7 inference request adapter 成功与 fail-closed 覆盖。
  - 扩展本机 O6 mock server 记录 `/api/o6/archive/inference` POST body。
- `pc-tools/workstation/test/App.test.ts`
  - 增加 UI fixture、fetch route 和点击 `请求 local/mock 推理` 的 smoke 覆盖。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 补充 PC O7 consumer inference adapter contract、校验规则、receipt 和 proof boundary。
- `docs/product/pc_tools_workstation.md`
  - 补充 workstation 后端 adapter、O6 model inference API 消费关系和 UI workflow。

## Verification Results

```bash
cd pc-tools/workstation && npm run test
```

- Result: PASS
- Key output: `Test Files 3 passed (3)` / `Tests 496 passed (496)`

```bash
cd pc-tools/workstation && npm run build
```

- Result: PASS
- Key output: `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- Note: Vite still reports the existing large chunk warning after build; no build failure.

```bash
cd pc-tools/workstation && npm run lint
```

- Result: PASS
- Key output: `eslint .`

```bash
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_15-15_o7_consumer_inference_request
```

- Result: PASS
- Key output: no whitespace errors.

## Remaining Risks And Boundaries

- This is O7/O6 local/mock consumer inference software proof only.
- It proves selected-task PC request construction, adapter guardrails, O6 local/mock `archive/inference` write receipt handling, UI request/receipt rendering, and fail-closed rejection behavior.
- It does not prove real model inference, real elevator door recognition, real floor recognition, production cloud, production DB/queue, OSS/CDN, 4G/SIM, real phone/browser, route execution, delivery, operator acceptance, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or O5 external evidence.
- Fixed false fields remain `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `connects_cloud_production=false`, `robot_control_executed=false`, `real_model_inference_success=false`, `real_floor_recognition_proven=false`, and `real_elevator_door_state_proven=false`.
- OKR main percentages should stay flat; KR should not be archived from this sprint alone.
