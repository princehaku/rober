# 2026-06-26 10:15 PC 路线停止折线 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 图上路线执行 pending 期间，路线折线复用 `plainTripStopOverlayState()`。
  - 点击 `行程停止（随时可点）` 后，路线折线从 `执行中` 切到 `停止中`；stop 转发成功后切到 `停止已发送`。
  - route caption 和 aria 同步显示停止请求链路，不再只让终点 marker 表达停止状态。
- `pc-tools/workstation/src/styles.css`
  - 新增路线折线 `停止中/停止已请求/停止已发送/停止失败` 样式。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 visible-route pending 用例，锁定 stop pending 和 stop forwarded 后路线折线 `data-state`、aria、caption 和 CSS 选择器。
- `docs/product/pc_tools_workstation.md`
  - 同步记录路线停止折线的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "marks the visible route goal as executing while the plain trip request is pending"`：通过，`1 passed | 191 skipped (192)`。
- `npm run lint`：通过。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `npm test`：通过，`2 passed (2)`，`192 passed (192)`。
- `git diff --check`：通过，无空白错误。
- 全量测试会刷新 2026-06-11 两个旧 DOM smoke artifact 的 `checked_at`；本轮已恢复为基线时间戳，避免无关产物进入提交。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实 Nav2 行程或真实底盘 stop，也不证明 HIL。
- `停止中/停止已发送` 折线只表示 PC 已请求固定 base stop 兜底，不等于 Nav2 action cancel；真实路线最终状态仍以后端 execution result/latest、现场画面和 HIL 材料为准。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
