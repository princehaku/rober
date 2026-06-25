# PC 地图画面刷新失败 Caption

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `refreshMapPreview` fetch/解析异常时不再清空为 `null`，改为生成 `preview_failed` fallback。
  - 普通首屏 `地图画面` caption 在 map preview 失败或被阻止时显示 `地图画面：刷新失败：<failure_reason>`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增 map preview 失败用例，确认地图 caption 显示 `map_preview_timeout`，且不调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 map preview 失败的 WYSIWYG 口径和控制边界。

## 验证结果

- 已通过：
  - `npm test -- -t "shows map preview refresh failure reason on the plain map"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 185 skipped (186)`。
  - `npm run lint`
  - 结果：ESLint 通过。
  - `npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - `npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 186 passed (186)`。
  - `git diff --check`
  - 结果：通过，无 whitespace error。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：本机已有 `node` 监听 `*:7001`，未改 Clash 或系统代理配置。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有连接真实上位机触发真实 `/api/map/preview` timeout。
- 该改动只保留并展示 map preview 失败原因，不改变建图、保存、Nav2、manual、keyboard、delivery 或 stop 后端行为。
- 未触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`；未修改 Clash 或系统代理配置。
