# PC 行程执行后地图复核

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `行程执行包` 新增 `地图复核` 计划行。
  - `地图复核` 根据既有 `executionPostMapRefreshRequired`、`executionPostMapRefreshComplete`、执行后地图预览失败状态显示 `执行后验`、`执行后刷新`、`已刷新` 或 `刷新失败`。
  - 执行后地图刷新失败时，直接展示失败原因，并提示先刷新地图画面再准备送达材料。
- `pc-tools/workstation/test/App.test.ts`
  - 固定默认 `地图复核` 行存在，且说明执行完成后会自动刷新地图画面。
  - 固定执行后地图刷新失败时，`地图复核` 显示 `刷新失败`、`map_preview_timeout` 和送达前先刷新地图的下一步。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录完整 Nav2 行程执行后的地图所见即所得复核口径。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|shows post-trip map refresh failure after a visible route succeeds|uses managed Nav2 runtime"`：通过，1 个测试文件，2 个匹配用例通过。
- `npm test -- --run`：通过，2 个测试文件，391 个用例通过。
- `npm run lint`：通过，0 error；仍有 `RobotControlConsolePanel.vue` 既有 4 条 Vue warning，本轮未新增。
- `npm run build`：通过，产物为 `dist/assets/index-FV8MDkfP.js`、`dist/assets/index-C7tHGYa9.css`；仍有 Vite chunk > 500 kB 既有提示。
- `git diff --check`：通过。
- 7001 已重启为新 bundle，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node PID 27123，监听 `TCP *:7001`。
- live bundle 验证：`index-FV8MDkfP.js` 包含 `地图复核`、`执行完成后会自动刷新地图画面`、`执行后地图画面刷新失败`、`executionPostMapRefreshRequired`、`executionPostMapRefreshComplete`。
- live DOM 验证：`plain-trip-execution-plan-map_refresh` 存在，文本为“地图复核 执行后验 执行完成后会自动刷新地图画面；地图刷新完成前不把旧画面当作送达收口依据。”

## 剩余风险

- 本轮只改 PC 普通首屏的只读执行包、测试和文档；没有启动 ROS2、RViz2、Nav2、建图 runtime、manual/free-roam/keyboard/delivery 或 `/cmd_vel`。
- 完整 Nav2 路线执行仍需要真实现场安全确认和上车端执行窗口的 wheel raw L/R 非零证据；本轮只把执行后地图复核纳入普通用户可见闭环。
