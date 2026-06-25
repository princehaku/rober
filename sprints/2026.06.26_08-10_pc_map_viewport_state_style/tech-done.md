# 2026.06.26 08:10 PC 地图视口状态样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`：地图视口按 `data-state` 呈现可见、处理中/待刷新、不可用三类视觉态，让地图框本身和状态 chip 一致。
- `pc-tools/workstation/test/App.test.ts`：扩展地图可见和地图处理中用例，锁定对应 CSS selector。
- `docs/product/pc_tools_workstation.md`：同步记录地图视口状态视觉契约和安全边界。

## 验证结果

- `npm test -- -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|blocks visible-route execution while the map preview is refreshing"`：通过，2 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不刷新真实地图、不执行真实 Nav2、不触发真实小车运动，也不覆盖 HIL 上车验证。
