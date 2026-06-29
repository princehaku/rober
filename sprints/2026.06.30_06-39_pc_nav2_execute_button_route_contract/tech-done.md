# PC Nav2 执行按钮完整路线合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `PlainTripDomEvidence` 新增路线完整度字段：`routePreviewComplete`、`routePreviewPartial`、`executionRoutePointCount`、`executesCurrentRouteGoal`。
  - `plain-trip-execute` 按钮新增按钮级 DOM 合同：图上显示点数、完整源路线点数、预览完整/部分、当前路线可见性、路线 WYSIWYG ready、执行路线点数、是否执行当前图上终点、固定 `/api/robot-control/nav2/goal/execute` 和同窗口 wheel raw L/R 非零要求。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖无路线时按钮 0 点且不执行。
  - 覆盖 summary 路线 `3/15` 点时按钮标记为部分预览、执行路线点数为 15，并绑定当前图上终点。
  - 覆盖 map preview 路线 `3/18` 点时按钮标记为部分预览、执行路线点数为 18，并绑定当前图上终点。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录完整路线执行按钮合同和 no-motion 边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary|shows a summary route on the initial map preview when route coordinates are available|draws the current route from map preview points when summary route coordinates are missing"`：通过，`3 passed | 216 skipped`。
- `npm test -- --run`：通过，`2 passed`，`389 passed`。
- `npm run build`：通过，生成 `dist/assets/index-CQwBRtm6.js` 与 `dist/assets/index-BmaNglvi.css`。
- `git diff --check`：通过，无空白错误。
- 7001 smoke：重启 PC 工作站后，`node` PID `60327` 监听 `*:7001`；`curl -fsS http://127.0.0.1:7001/` 返回当前 `index-CQwBRtm6.js` / `index-BmaNglvi.css`；dist 可检出 `route-preview-complete`、`route-preview-partial`、`execution-route-point-count`、`executes-current-route-goal` 和 `fixed-execute-proxy-endpoint`。

## 剩余风险

- 本轮只补 PC Web DOM 合同和测试，不执行真实 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实完整 Nav2 路线执行、wheel raw L/R 非零、执行后地图刷新和 delivery success 仍需要现场 HIL 验证。
