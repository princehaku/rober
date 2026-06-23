# 2026-06-23 15:15 雷达启动成功门控与 Node 默认公网端口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `启动雷达` 只有在 radar lifecycle 响应 `command_result.ok=true` 时，才提示 `雷达启动已返回，请点刷新雷达确认状态` 并聚焦 `刷新雷达`。
  - 若 radar start 返回 `command_not_configured`、blocked、failed 或其它未成功结果，则普通首屏显示 `雷达启动没有成功...`，焦点留在 `启动雷达`。
  - 该逻辑只消费固定 radar start proxy 响应，不自动重试、不自动刷新、不触发 first-jog/manual/keyboard pulse/stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新默认 dry-run 未配置分支，要求失败时焦点留在 `plain-radar-start`。
  - 新增 `command_result.ok=true` 成功分支，要求成功时焦点进入 `plain-radar-refresh`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 radar start 成功 gate。
  - 同步记录 `npm run api` 默认监听 `0.0.0.0:7071`，以及端口冲突兜底命令。
- `pc-tools/workstation/src/server/index.ts`
  - Node/Express 工作站默认监听从 `127.0.0.1:8787` 改为 `0.0.0.0:7071`，仍保留 `HOST/PORT` 启动前覆盖。
  - 端口占用提示从 `npm run api:public` 调整为默认入口 `npm run api`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增默认监听地址断言，锁定 `workstationListenAddress() = http://0.0.0.0:7071`。
  - 更新端口占用提示断言。
- `pc-tools/README.md`
  - 运行说明同步为构建后 `npm run api` 默认提供局域网可访问的 `0.0.0.0:7071`。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "plain radar start|radar start reports ok"`，结果 `1 passed`，`2 passed | 50 skipped`。
- 通过：`npm test -- test/catalog.test.ts -t "public operator port|public API port conflict"`，结果 `1 passed`，`2 passed | 86 skipped`。
- 通过：`npm test`，结果 `2 passed`，`140 passed`。
- 通过：`npm run lint`。
- 通过：`npm run build`，完成 app/server TypeScript 与 Vite production build。
- 通过：`git diff --check`。
- 真实上位机只读状态：
  - `/api/radar/status`: `lifecycle_running=false`, `lifecycle_status=lifecycle_not_running`
  - `/api/base/status`: `T=1001` 可读，最新 `L=0/R=0`，反馈电压约 `12.43V`
  - `/api/nav2/goal/execution/latest`: `status=not_proven`
  - `/api/delivery/latest`: `delivery_success=false`
  - `/api/operator/report`: latest 是 `delivery-draft-smoke-1782102952`，基础安全三项为 false

## 剩余风险

- 本轮没有执行真实雷达启动、first-jog、Nav2 或 delivery complete。
- `wheel raw L/R 非零`、`完整 Nav2 路线执行`、`delivery success`、`PC 键盘连续手控` 仍需现场安全确认后继续拿真实证据。
