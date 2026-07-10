# O7 Worker Report

## 用户旅程变化

- O7 operator 现在可以在 consumer detail 中直接看到 `localization_path_material_readback` 只读摘要。
- 页面会同时显示 same-run localization/path 状态、TF/planner/path false 结论，以及 cross-run clean-baseline comparator 边界，避免把历史 clean-baseline path 误读成当前 run path success。
- 该区块继续固定 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`，不新增任何控制动作。

## 实际改动文件列表

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`

## 联调结果

- O7 adapter 已把 O6 `localization_path_material_readback` 归一为 `trashbot.pc_tools_workstation.o7_localization_path_material_readback.v1`。
- consumer detail 与 artifact bundle readiness 都能读取该只读材料摘要。
- hostile payload 会在 schema mismatch、task mismatch、unsafe text/list、proof scope mismatch、same-run path success claim 时 fail-closed。

## 验证命令输出结果

### 1. `cd pc-tools/workstation && npm run test`

- 结果：通过
- 关键输出：`Test Files  3 passed (3)`，`Tests  488 passed (488)`

### 2. `cd pc-tools/workstation && npm run build`

- 结果：通过
- 关键输出：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 备注：Vite 仍提示 chunk 大于 `500 kB` 的现有 warning，本轮未扩大处理范围。

### 3. `cd pc-tools/workstation && npm run lint`

- 结果：通过
- 关键输出：`eslint .`

### 4. `rg -n "localization_path_material_readback|software_proof_localization_path_material_readback_only|same_run_path" pc-tools/workstation/src pc-tools/workstation/test docs/product/pc_tools_workstation.md`

- 结果：通过
- 关键命中：adapter include、O7 contract、fixture preview 文案、catalog/App 测试、产品文档说明均已包含 `localization_path_material_readback` 与 same-run path false 字段。

### 5. `git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback`

- 结果：通过
- 关键输出：无 whitespace / conflict 标记错误

## 失败定位

- 首轮 `npm run test` 失败：`buildConsumerArtifactBundleReadiness` 调用点遗漏 `localizationPathMaterialReadback` 参数，导致 `ReferenceError`。
- 修复：补齐 readiness builder 签名与 fail-closed 调用链，同时更新 HTTP contract 测试的 `include` 预期列表。
- 修复后：`npm run test`、`npm run build`、`npm run lint` 全部通过。

## 剩余风险

- 当前证明边界仍是 `software_proof_localization_path_material_readback_only`；不证明真实 live Nav2 route execution、真实 delivery success、真实 safe-to-control、真实 production cloud 或 HIL。
- O7 目前只消费已有 O6 合同；若并行中的 O6 worker 最终字段名与当前 tech-plan 契约不同，还需要做一次对齐回归。
