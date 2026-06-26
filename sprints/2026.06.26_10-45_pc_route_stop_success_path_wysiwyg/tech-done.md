# 2026-06-26 10:45 PC 路线停止成功折线 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/test/App.test.ts`
  - delayed stop success 用例不再依赖不存在的全局 stop fixture，改为显式返回 `command_forwarded` stop success 回包。
  - 锁定 stop 成功后地图终点 marker、整条路线折线、caption 和行程状态显示 `停止已发送`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 行程停止收口时，`null` 只表示本次没有拿到新 stop 回包，不能覆盖 `sendStop()` 已经记录的成功或失败结果。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 stop success route path 的 WYSIWYG 口径和安全边界。

## 验证结果

- `npm test -- -t "marks the visible route goal as executing while the plain trip request is pending|shows visible route stop failure on the whole route path"`：通过，2 passed / 191 skipped。
- `npm run lint`：通过。
- `npm run build`：通过，Vite production build 完成。
- `npm test`：通过，2 files / 193 tests passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 Node 监听 `TCP *:7001 (LISTEN)`。

## 剩余风险

- 本轮只做 PC 前端 mock/静态验证，不触发真实 Nav2 行程或真实底盘 stop，也不证明 HIL。
- `停止已发送` 只表示 PC stop proxy 返回 `command_forwarded`；真实 Nav2 action 是否取消、底盘是否已完全静止仍以后端 execution/latest、现场画面和真实 HIL 材料为准。
- Node 当前应继续监听 `0.0.0.0:7001`；本轮不修改 Clash、代理或系统网络配置。
