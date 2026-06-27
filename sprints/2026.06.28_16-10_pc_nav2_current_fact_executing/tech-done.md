# 2026.06.28 16:10 PC Nav2 current fact executing

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的行程行在 Nav2 goal execution pending 时优先显示执行中状态。
  - 文案复用现有 `plainTripPendingRouteText()` 和 `plainTripStopOverlayState()`，与地图 marker、路线 polyline、行程卡片保持同一 pending 事实。
  - 该变更只影响可见状态，不新增 manual、free-roam、delivery、stop 或 `/cmd_vel` 调用，也不把 pending 当作到达成功。
- `pc-tools/workstation/test/App.test.ts`
  - 在图上路线执行 pending 测试中断言 `当前事实` 同步显示正在执行目标和路线点数。
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录 Nav2 执行中事实条的产品口径和安全边界。

## 验证结果

- `npm test -- --run test/App.test.ts -t "executing Nav2 route"`：未匹配测试名，1 个测试文件跳过，192 个测试跳过；不作为有效验证。
- `npm test -- --run test/App.test.ts -t "marks the visible route goal as executing while the plain trip request is pending"`：通过，1 个测试文件通过，1 个测试通过，191 个跳过。
- `npm test`：通过，2 个测试文件通过，339 个测试通过。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `git diff --check`：通过。

## 剩余风险

- 本轮只修正 PC 顶部事实条和 pending 状态一致性，不证明真实 Nav2 已能完成路线。
- 真实完整 Nav2 route execution、wheel raw L/R 同窗口非零和 delivery success 仍需要现场安全确认后继续验证。
