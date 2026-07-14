# O7 Delivery Result Intake Tech Done

## Sprint Type

sprint_type: epic

## 实际改动

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
  - 新增 `buildO7ConsumerDeliveryResultIntake()`，只允许本机 HTTP 回环 `baseUrl`。
  - 新增 O7 `trashbot.pc_tools_workstation.o7_consumer_delivery_result_intake_result.v1` receipt，成功状态为 `local_mock_delivery_result_written` / `local_mock_delivery_result_updated`，失败为 `fail_closed`。
  - 将 selected-task body 转成最小 `trashbot.field_evidence_manifest.v1` gate + `trashbot.delivery_result_evidence.v1` additive section，并固定转发 O6 `POST /api/o6/archive/field-evidence`。
  - 校验 O6 回包必须为 `trashbot.o6.field_evidence_archive.v1`、`source=local_mock_field_evidence_archive`、`proof_status=not_proven`、`archive_status=local_mock_field_evidence_ready`、`field_evidence_written=true`、`write_status=created|updated`，且 task/robot/result identity 匹配。
  - 保持 `software_proof_o7_o6_consumer_delivery_result_intake_only` 边界；`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`connects_cloud_production=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`、`real_cloud_db_connected=false`、`real_oss_connected=false` 固定 false。
- `pc-tools/workstation/src/server/index.ts`
  - 新增 `POST /api/o7/consumer-read/tasks/:taskId/delivery-result/intake`，浏览器只调用 PC Node adapter，不直连 O6。
- `pc-tools/workstation/src/client/workstationApi.ts`
  - 新增 `postO7ConsumerDeliveryResultIntake()` 和固定 client suffix `/delivery-result/intake`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 delivery result intake request/receipt 类型、record status/dropoff confirmation 枚举类型。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
  - 在 O7 consumer selected-task flow 的 delivery result evidence 区块后新增 local/mock delivery result intake 表单与 receipt 展示。
  - 按钮只在 selected task detail 已加载、task_id/robot_id 可复核、ref/UTC/notes 安全时启用。
  - Receipt 展示 O6 schema/source、`field_evidence_written`、`delivery_result_evidence` readiness、proof scope、not proven 和固定 false fields。
- `pc-tools/workstation/test/catalog.test.ts`
  - 扩展本机 O6 mock server，新增 `/api/o6/archive/field-evidence` 捕获。
  - 覆盖 created / updated receipt、unsafe input fail-closed、bad O6 receipt fail-closed、Express route adapter。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 UI fixture receipt、fetch stub route、按钮点击和 receipt/proof-boundary 文案断言。
- `docs/interfaces/o7_realtime_operator_console.md`
  - 补充 O7 delivery result intake endpoint、O6 field-evidence 转发路径、receipt schema、成功/失败边界和固定 false 字段。
- `docs/product/pc_tools_workstation.md`
  - 补充用户旅程：operator 先加载 selected task detail，再提交同 `task_id` 的 local/mock delivery result evidence request，receipt 只说明 O6 field-evidence local/mock 写入。

## 接口影响和用户旅程变化

- 新增 PC API：
  - `POST /api/o7/consumer-read/tasks/<task_id>/delivery-result/intake?baseUrl=<local-loopback-url>`
  - 转发到 O6：`POST /api/o6/archive/field-evidence`
  - O7 receipt schema：`trashbot.pc_tools_workstation.o7_consumer_delivery_result_intake_result.v1`
- Operator 现在可以在同一个 selected-task consumer detail 页面里：
  1. 读取 O6 `delivery_result_evidence` 摘要；
  2. 填写 local/mock delivery result intake 字段；
  3. 写入同 `task_id` 的 O6 field-evidence local/mock store；
  4. 看到 O7 receipt、O6 schema/source、write status、`field_evidence_written`、blocked/not_proven 和固定 false fields。
- 该动作不触碰真实硬件、真实 `/cmd_vel`、`/api/base/manual`、NavigateToPose 或 WAVE ROVER UART。

## 验证结果

已运行：

```bash
cd pc-tools/workstation && npm run test
cd pc-tools/workstation && npm run build
cd pc-tools/workstation && npm run lint
git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/server/index.ts pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md sprints/2026.07.13_17-17_o7_delivery_result_intake
```

关键输出：

```text
npm run test
Test Files  3 passed (3)
Tests  501 passed (501)

npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
✓ built in 1.97s

npm run lint
eslint .

git diff --check -- <scoped files>
通过，无输出
```

说明：`npm run build` 保留 Vite 既有 large chunk warning，但 TypeScript 与 production build 均通过。

## 失败定位和修复过程

- 未遇到验证失败；本轮不需要触碰 O6 后端 Python，因此未运行 O6 额外 py_compile / unittest。

## 剩余风险

- 当前仍是 `software_proof_o7_o6_consumer_delivery_result_intake_only`，只证明 PC/O7 selected-task action-write 到 O6 local/mock field-evidence 合同；不证明真实送达成功、真实 Nav2 route execution、生产云写入、HIL 或硬件安全。
- O6 `delivery_result_evidence` readback 当前只保留白名单摘要；后续若需要真实送达闭环，仍需机器人侧提供真实 delivery result trace、operator confirmation trace 和 same-task route execution evidence。
