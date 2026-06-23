# 2026.06.23 08:05 Focus Keyboard After Delivery Success

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `确认送达（不发车）` 通过上位机 delivery gate 后，普通首屏自动聚焦 `键盘手控` 面板。
  - 聚焦只改变页面焦点和滚动位置，不启用键盘、不发送 keyboard pulse、不调用 manual、stop、Nav2 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展最终送达提交成功回归：delivery complete 成功后焦点落到 `keyboard-control-panel`。
  - 确认键盘状态仍是 `未启用`，且未调用 `/api/robot-control/base/manual` 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 delivery success 后进入 PC 键盘连续手控验证的焦点引导和安全边界。
- `pc-tools/workstation/src/server/index.ts`
  - Node API 支持 `HOST` 环境变量覆盖监听地址，默认仍为 `127.0.0.1`。
- `pc-tools/workstation/package.json`
  - 新增 `npm run api:public`，固定以 `HOST=0.0.0.0 PORT=7071` 启动 PC 工作站 API，方便局域网访问。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - `dist/assets/index-CPydOL9j.js 403.40 kB`
- 通过：`git diff --check`
- 已恢复历史 smoke artifact 的 `checked_at` 测试副作用，未纳入本轮提交。
- 公开 Node API 验证：
  - `netstat -anv -p tcp | rg '.7071|7071'` 显示当前 `*.7071 LISTEN` 属于本机 Clash Verge `verge-mihomo` 进程（PID 2183）。
  - 因 7071 已被用户侧代理占用，本轮未强行杀进程；`npm run api:public` 脚本已就绪，释放 7071 后会按 `HOST=0.0.0.0 PORT=7071` 启动。

## 剩余风险

- 当前变更只把 delivery success 后的普通首屏引导接到键盘验证入口；真实 PC 键盘连续手控仍必须由现场人员显式启用并按住方向键/WASD，通过固定 manual proxy 产生连续脉冲证据。
- 本轮未执行真实运动、Nav2 或 delivery complete；真实 wheel raw L/R 非零、完整 Nav2 本轮复验和 delivery success 仍需现场证据。
