# PC 行程复查可选化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `检查行程` 改为 `可选复查（不发车）`。
  - 行程状态提示改为“安全确认后可以准备图上路线，可选复查不会发车”，避免把 preflight 误读成发车前必点。
  - `本轮进度 -> 去行程` 在安全确认后优先聚焦 `准备行程（不发车）` 或 `执行图上路线`，不再优先聚焦可选复查。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通行程流断言，确认可选复查文案和跳转目标。
- `docs/product/pc_tools_workstation.md`
  - 同步记录普通首屏发车前最小确认口径。

## 验证结果

- 首次全量 `npm test` 发现默认首屏仍出现 `路线` 禁词，已修复为未确认时只显示“准备或执行行程”。
- 通过：`npm test -- --testNamePattern "renders Robot Control V1 by default|runs plain trip preflight and execution only after the safety checkbox is checked|keeps plain trip execution blocked until a visible route is confirmed while lidar is stopped"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 3 passed | 167 skipped (170)`。
- 通过：`npm run lint`
  - 结果：`eslint .` 无报错。
- 通过：`npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 170 passed (170)`。
- 通过：`npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过，Vite 输出 `✓ built`。
- 通过：`lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：`node ... TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只减少 PC 普通首屏的预检误导；真实完整 Nav2 路线、delivery success 和真车自由自动扫图仍需要继续用上车端/HIL 证据闭环。
- 高级诊断仍保留 Nav2 preflight 能力，用于排障，不作为普通发车主路径。
