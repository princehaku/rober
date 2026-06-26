# 2026-06-26 10:30 PC 路线停止失败折线 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - 新增 visible-route stop failure 用例，模拟行程执行中 stop proxy 返回 `command_failed/status=blocked`。
  - 锁定停止失败时地图终点 marker、整条路线折线、caption 和 aria 都显示 `停止失败`。
  - 继续断言该失败态不触发 delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 行程执行中的 stop 结果独立留给路线 overlay，失败回包优先显示 `停止失败`，避免地图误停留在“停止已请求”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stop failure route path 的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "marks the visible route goal as executing while the plain trip request is pending|shows visible route stop failure on the whole route path"`：通过，2 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 完成。
- `npm test`：通过，2 files / 193 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实 Nav2 行程或真实底盘 stop，也不证明 HIL。
- `停止失败` 折线只表示 PC stop proxy 回包失败；真实路线最终状态仍以后端 execution result/latest、现场画面和 HIL 材料为准。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
