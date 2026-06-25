# 2026.06.26 07:55 PC 最近路线地图样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：路线折线增加 `data-state`，区分 `当前路线` 和 `最近路线`。
- `pc-tools/workstation/src/styles.css`：`最近路线` 折线改为黄系虚线，`最近路线起点/最近路线终点` 端点改为旧记录/待重新规划视觉态。
- `pc-tools/workstation/test/App.test.ts`：扩展最近路线地图用例，锁定折线 `data-state` 和最近路线折线/端点 CSS selector。
- `docs/product/pc_tools_workstation.md`：同步记录最近路线视觉态和安全边界。

## 验证结果

- `npm test -- -t "marks stale path preview points as a recent route instead of an executable route"`：通过，1 passed / 191 skipped。
- `npm test -- -t "draws the latest Nav2 goal on the real map when goal coordinates are available"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不执行真实 Nav2，不触发真实小车运动，也不覆盖 HIL 上车验证。
