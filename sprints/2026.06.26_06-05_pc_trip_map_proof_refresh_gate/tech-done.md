# 2026-06-26 06:05 PC 行程执行等待地图 proof 刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 将行程执行的地图 WYSIWYG pending gate 从只看 `mapPreviewPending` 扩展为 `mapPreviewPending || mapRefreshPending`。
  - 地图 proof 或地图画面刷新中时，`执行图上路线` 统一显示 `等待地图刷新` 并禁用。
  - 行程状态、路线 WYSIWYG 提示、本轮进度下一步和验收卡点会区分 `地图画面刷新中` 与 `地图状态刷新中`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 visible-route 执行测试：延迟 `map/proof/refresh` 和 `map/preview`，验证旧路线仍可见但执行按钮禁用，并断言不会调用 Nav2 execute、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步地图 proof/preview 刷新中不能按旧图执行路线的产品口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "map preview is refreshing|visible-route"`，2 passed / 188 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 190 passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 PC node 监听 `*:7001`，未改 Clash/系统代理。

## 剩余风险

- 本轮只覆盖 PC 前端 route/map proof pending gate 和 mock 回归；没有在真实小车上执行 Nav2 路线或做 HIL。
