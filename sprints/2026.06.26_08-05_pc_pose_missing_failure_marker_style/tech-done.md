# 2026.06.26 08:05 PC 地图定位失败标记样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图位置缺位 marker 增加 `data-state`，区分 `位置未读到` 和 `定位失败`。
- `pc-tools/workstation/src/styles.css`：`定位失败` marker 使用失败视觉态，避免和普通未读到位置混淆。
- `pc-tools/workstation/test/App.test.ts`：扩展 localization reset 失败用例，锁定 marker `data-state` 和 CSS selector。
- `docs/product/pc_tools_workstation.md`：同步记录定位失败 marker 视觉态和安全边界。

## 验证结果

- `npm test -- -t "shows localization reset failure on the plain map pose marker"`：通过，1 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不触发真实重新定位、不执行真实 Nav2、不触发真实小车运动，也不覆盖 HIL 上车验证。
