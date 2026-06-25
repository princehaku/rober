# 2026.06.26 08:00 PC 扫地图草图运行态样式

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：扫地图草图 SVG 增加 `data-state`，区分 `只读计划` 和 `自动扫图运行中`。
- `pc-tools/workstation/src/styles.css`：自动扫图运行中的草图使用独立监看覆盖视觉态，避免和未启动的只读计划混淆。
- `pc-tools/workstation/test/App.test.ts`：扩展自动扫图 start 成功和普通扫图草图用例，锁定草图 `data-state` 与运行态 CSS selector。
- `docs/product/pc_tools_workstation.md`：同步记录扫地图草图运行态视觉契约和安全边界。

## 验证结果

- `npm test -- -t "starts free-roam autonomy through the fixed proxy only after ready readback and safety confirmation|draws radar pulse on the robot marker only after map-frame pose is observed"`：通过，2 passed / 190 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，2 files passed，192 tests passed。
- 全量测试产生的两个旧 smoke artifact `checked_at` 副作用已恢复到既有值。

## 剩余风险

- 本轮只做 PC 前端 mock 验证，不启动真实自动扫图、不执行真实 Nav2、不触发真实小车运动，也不覆盖 HIL 上车验证。
