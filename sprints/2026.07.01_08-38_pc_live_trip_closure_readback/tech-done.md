# 2026.07.01 08:38 PC 当前卡点完整行程闭环读回

## sprint_type

micro

## 实际改动

- 在 PC 普通首屏当前卡点区新增 `plain-live-trip-closure-readback`，复用行程卡 `plainTripClosureReadbackSummary` 的完整行程闭环口径。
- 新行直接显示到点读回、同窗口 wheel L/R 非零、delivery success 三项事实，并提供 `plain-live-trip-closure-readback-refresh` 只读刷新按钮。
- 按钮仅刷新 `nav2/goal/execution/latest`、`base/feedback-samples`、`summary`、`delivery/latest` 四个验收端点，DOM 固定声明不启动 Nav2/manual/keyboard/free-roam/map runtime，不提交 delivery，不 stop，不发送 motion。
- 同步更新 PC 工作站产品边界文档，记录当前卡点区新增完整行程闭环读回条的用户可见合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，结果 `1 passed | 230 skipped`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，生成 `dist/assets/index-DLF-Y8KJ.js` 与既有 CSS；仅保留 Vite 大 chunk 提示。
- 通过：`cd pc-tools/workstation && npm test`，结果 `3 passed`、`417 passed`。
- 通过：`git diff --check`。
- 通过：重启 PC API 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，PID `59979`。
- 通过：`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：构建产物 `dist/assets/index-DLF-Y8KJ.js` 包含 `plain-live-trip-closure-readback`、`完整行程闭环`、`读回闭环`。
- 通过：只读 `GET /api/robot-control/summary` 当前读数为地图默认缩放 `150%`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero=false`、`delivery_success=false`、`camera_visible=false`、`radar_points=false`。

## 剩余风险

- 当前改动为 PC 前端只读 DOM/按钮合同，不触发真实小车运动；完整 Nav2 行程闭环仍需要现场在安全确认后重跑路线，并读到同窗口 wheel L/R 非零和 delivery success。
