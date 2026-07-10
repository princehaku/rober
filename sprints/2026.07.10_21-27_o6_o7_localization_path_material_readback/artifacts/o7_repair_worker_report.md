# O7 Repair Worker Report

## 实际改动文件

- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback/artifacts/o7_repair_worker_report.md`

## 修复内容

- O7 localization readback adapter 现在同时接受：
  - `status=localization_path_material_readback_ready_not_route_execution_proof`
  - `status=localization_path_material_ready_not_route_execution_proof`
- O7 同时接受 O6 旧 TF aliases：
  - `same_run_tf_map_to_odom_observed`
  - `same_run_tf_map_to_base_link_observed`
  以及最终字段：
  - `same_run_localization_tf_map_to_odom`
  - `same_run_localization_tf_map_to_base_link`
- 当 `localization_path_material_bridge_present` 缺失，但 payload 处于 ready status 且 `same_run_localization_material_present=true` 时，O7 兼容视其为 `true`，避免缺失 alias 触发误降级。
- UI 文案和产品文档同步记录该兼容行为。
- 新增 catalog/UI 回归测试，覆盖 O6 实际初版 payload 形状与 same-run path success fail-closed。

## 验证命令输出

### 1. `cd pc-tools/workstation && npm run test`

- 结果：通过
- 关键输出：`Test Files  3 passed (3)`，`Tests  489 passed (489)`

### 2. `cd pc-tools/workstation && npm run build`

- 结果：通过
- 关键输出：`vite v7.3.3 building client environment for production...`
- 备注：保留既有 Vite chunk size warning，未扩大本轮范围处理。

### 3. `cd pc-tools/workstation && npm run lint`

- 结果：通过
- 关键输出：`eslint .`

### 4. `rg -n "localization_path_material_readback_ready_not_route_execution_proof|same_run_tf_map_to_odom_observed|same_run_localization_tf_map_to_odom|localization_path_material_bridge_present" pc-tools/workstation/src pc-tools/workstation/test docs/product/pc_tools_workstation.md`

- 结果：通过
- 关键命中：
  - adapter 中已存在双 status 兼容、旧 TF alias 兼容、bridge alias 兼容逻辑；
  - `catalog.test.ts` 新增 actual O6 payload 回归；
  - `App.test.ts` 明确断言 UI 渲染 `material_status=localization_path_material_readback_ready_not_route_execution_proof`；
  - 产品文档已记录这轮返工兼容口径。

### 5. `git diff --check -- pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/product/pc_tools_workstation.md sprints/2026.07.10_21-27_o6_o7_localization_path_material_readback`

- 结果：通过
- 关键输出：无 whitespace / conflict 标记错误

## 失败定位

- 主会话验收指出：O6 初版 payload 使用 `_readback` ready status，且仍可能只带旧 TF aliases 或缺失 bridge 布尔位。
- 原因：O7 adapter 的缺字段检查和 ready 判定只识别最终字段名，导致真实 O6 payload 会被错误降级为 `derived_blocked_not_proven` 或直接 fail-closed。
- 首轮 `npm run test` 新回归失败点：compat 用例把 `loaded_fail_closed_summary` 的 `fail_closed_reason` 断言成空串。
- 修复：对齐既有 O7 contract，改为断言 `fail_closed_reason=none`；修复后 `npm run test` 重新通过。

## 剩余风险

- 当前兼容逻辑只覆盖这轮主会话已确认的 status / TF / bridge 命名漂移；若 O6 还有其他未暴露的别名，需要再补回归样例。
- 证明边界仍是 `software_proof_localization_path_material_readback_only`，不代表真实 Nav2 route execution、delivery success、safe_to_control 或 HIL 成功。
