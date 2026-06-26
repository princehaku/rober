# 2026-06-26 10:00 PC 路线执行折线 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏点击 `执行图上路线` 后，本次 Nav2 execute pending 期间地图路线折线从 `当前路线` 切到 `执行中`。
  - route caption 同步显示 `图上路线执行中 N/M 个点`，aria 显示正在执行的图上路线点数。
  - 后端返回后仍按既有成功、失败、旧路线或最近路线逻辑显示，不伪造完成。
- `pc-tools/workstation/src/styles.css`
  - 新增 `.plain-map-route-path[data-state="执行中"] polyline` 绿色虚线样式。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 visible-route pending 用例，锁定路线折线 `data-state="执行中"`、aria、caption 和 CSS 选择器。
- `docs/product/pc_tools_workstation.md`
  - 同步记录路线执行折线的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "marks the visible route goal as executing while the plain trip request is pending|draws no-motion route start and end markers when no executed goal is available"`：通过，`2 passed | 190 skipped (192)`。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `npm test`：通过，`2 passed (2)`，`192 passed (192)`。
- `git diff --check`：通过，无空白错误。
- 全量测试会刷新 2026-06-11 两个旧 DOM smoke artifact 的 `checked_at`；本轮已恢复为基线时间戳，避免无关产物进入提交。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实 Nav2 行程，也不证明 HIL。
- `执行中` 折线只表示本机已经显式发送 Nav2 execute 且响应还没返回；真实路线执行结果仍以后端 execution result/latest、现场画面和 HIL 材料为准。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
