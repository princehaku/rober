# 2026-06-23 11:00 本轮进度轮速卡点直达

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 的轮速跳转不再只落到 `轮速记录` 面板，而是按当前状态聚焦真实下一手动作：`已检查轮速卡点`、`检查后重试读非零 L/R`、`恢复试动确认` 或 `试动一下`。该行为只滚动和聚焦，不自动点击、不发车、不调用 Nav2、delivery complete、manual、stop、keyboard pulse 或 `/cmd_vel`。
- `pc-tools/workstation/package.json`、`pc-tools/workstation/vite.config.ts`：保留本地默认开发入口，并新增 `npm run dev:public`；Vite dev server 支持 `HOST/PORT` 覆盖，可绑定 `0.0.0.0:7071` 方便局域网访问。既有 `npm run api:public` 仍用于 Node API 绑定 `0.0.0.0:7071`。
- `pc-tools/workstation/test/App.test.ts`：扩展 L/R=`0/0` 场景，验证点击 `本轮进度 -> 去轮速记录卡点` 会把焦点落到 `plain-wheel-zero-check`，点击本地检查后再聚焦 `plain-wheel-trial`，且不调用 manual。
- `docs/product/pc_tools_workstation.md`：同步 public dev/API 启动入口和轮速卡点直达规则。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 137 passed (137)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 生成 `dist/index.html`、CSS 和 JS bundle。
- 通过：`git diff --check`
- 未通过环境验证：`cd pc-tools/workstation && npm run api:public`
  - 期望绑定：`HOST=0.0.0.0 PORT=7071`
  - 实际失败：`EADDRINUSE 0.0.0.0:7071`
  - `netstat -anv` 显示 `*.7071 LISTEN` 属于 PID `2183`，进程为 `/Applications/Clash Verge.app/Contents/MacOS/verge-mihomo`。
  - 本轮只清理了失败启动残留的 `tsx src/server/index.ts` 进程；未擅自停止 Clash Verge。

## 剩余风险

- 本轮是 PC 端易用性与公开绑定入口改进，不证明真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 或真实 PC 键盘连续手控。
- 7071 当前被 Clash Verge 占用，PC 工作站 public API/dev 服务无法实际绑定该端口；需要 CEO 明确是否关闭/改端口 Clash，或改用其它 PC 工作站端口。7071 同一时间只能由 Node API 或 Vite dev server 其中一个进程占用；若需要 UI 与 API 同时对外访问，需要其中一个改用其它端口或使用反向代理。
