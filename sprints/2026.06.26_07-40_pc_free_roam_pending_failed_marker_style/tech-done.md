# 2026.06.26 07:40 PC 自由扫图停止中/失败地图样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：将自由扫图地图流程 marker 的 `stopping` 纳入等待/警示视觉态，将 `map_failed` 纳入失败视觉态。
- `pc-tools/workstation/test/App.test.ts`：在既有 stop pending 和 map lifecycle failure 用例中增加 CSS 选择器断言，防止状态存在但地图视觉态回落默认样式。
- `docs/product/pc_tools_workstation.md`：同步记录 `stopping` / `map_failed` 的地图视觉态测试契约。

## 验证结果

- `npm test -- -t "keeps failed free-roam map lifecycle visible on the map"`：通过，1 passed / 191 skipped。
- `npm test -- -t "shows free-roam keyboard release while stop is still pending"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实小车运动，也不覆盖 HIL 上车验证。
