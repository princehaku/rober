# O7 Worker Report

## 范围

- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/interfaces/o7_realtime_operator_console.md`

## 实际改动

1. 给 `same_task_route_execution_material_packet` 增加 O7 侧 credit-aware 字段消费：
   - `live_or_field_command_evidence_present`
   - `delivery_or_operator_material_consumed`
   - `route_execution_credit_candidate`
   - `credit_support_only_reason`
   - `credit_required_evidence`
2. 在 `o7ConsumerReadAdapter.ts` 中把上述字段纳入必填白名单和 fail-closed 校验：
   - 缺字段、unsafe text/list、schema mismatch、task mismatch、dangerous true、proof scope mismatch 均会阻断 detail。
   - `route_execution_credit_candidate=true` 不会推导 `delivery_success`、`safe_to_control` 或 primary action。
3. 在 `O7FixturePreviewPanel.vue` 中新增 credit material summary 展示，显式提示 support-only/blocked 语义。
4. 更新 Vitest fixture 和断言，覆盖新字段的消费与渲染。
5. 同步产品文档和接口文档，记录 O7 的 credit-aware 展示边界。

## 验证

- 已执行 `cd pc-tools/workstation && npm run test && npm run build && npm run lint`
  - `Tests 486 passed (486)`
  - `vite build` 通过；仅保留既有 chunk-size warning
  - `eslint .` 通过
- 已执行 scoped `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material`，结果通过

## 剩余风险

- 当前仍是 software proof；即使 credit candidate 为 true，也不代表真实 live Nav2、真实 delivery record、真实 operator confirmation 或真实 delivery success。
- O7 只是在 UI/consumer 层消费 O6 credit 字段，最终是否允许计主 OKR 仍以 O6/O7 联合验收口径为准。
