# 2026.06.26 01:51 PC 自动扫图失败原因地图 WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `freeRoamAutonomyFailureText()`，把自动扫图 start/stop 失败的 `failure_reason/blocked_reasons` 翻译成普通首屏短原因。
  - 普通首屏地图 `plain-map-free-roam-action-marker` 在 `autonomy_failed` 时显示 `自动扫图启动失败：<短原因>` 或 `自动扫图停止失败：<短原因>`。
  - `扫图状态` 行复用同一短原因，避免地图 marker 和卡片文案不一致。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 `shows plain free-roam autonomy failure reason on the map`，覆盖自动扫图 start 被 safety gate 拒绝时，地图 marker、`data-state`、ARIA 和扫图状态均显示 `安全确认未通过`。
- `docs/product/pc_tools_workstation.md`
  - 同步自动扫图失败原因贴回普通首屏地图和状态行的产品口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "shows plain free-roam autonomy failure reason on the map"`
  - 结果：通过，`1 passed | 180 skipped (181)`。
- `cd pc-tools/workstation && npm run lint`
  - 结果：通过，`eslint .` 无报错。
- `cd pc-tools/workstation && npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `cd pc-tools/workstation && npm test`
  - 结果：通过，`2 passed (2)`，`181 passed (181)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node` 正在监听 `TCP *:7001 (LISTEN)`。

## 验证副作用处理

- 全量 Vitest 会刷新旧 DOM smoke artifact 的 `checked_at` 字段；本轮已将
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  和
  `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
  恢复到原始时间戳，避免旧证据被误记为本轮产物。

## 剩余风险

- 本轮只做 PC mock/DOM 验证，没有真实启动上车端自动扫图状态机。
- 失败原因短文案只服务普通首屏 WYSIWYG；真实根因仍以高级诊断和上位机日志为准。
