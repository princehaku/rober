# PC Keyboard Stop Queue Button

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- status: done

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `canRequestKeyboardStop`。当方向 manual pulse 正在请求中且仍处于按住方向状态时，键盘/扫图停止按钮保持可点。
- 普通键盘停止、键盘方向盘中间停止、扫地式建图停止、扫图方向盘中间停止改用 `canRequestKeyboardStop`；全局普通 `停止` 仍沿用 `canSendStop`。
- 现有 `stopKeyboardControl()` 队列逻辑保持不变：点击停止时若 manual pulse 未返回，不并发发 stop，而是记录 reason，pulse 返回后补发固定 stop。
- `pc-tools/workstation/test/App.test.ts`：把 in-flight pulse 测试改为点击 `键盘停止（随时可点）`，验证按钮未禁用且 stop 在 pulse 返回后补发。
- `docs/product/pc_tools_workstation.md`：同步 2026-06-26 06:40 行为说明。

## 验证结果

- `npm test -- -t "queues release stop when the stop button is clicked during an in-flight keyboard pulse"`：通过，1 passed / 190 skipped。
- `npm test -- -t "keyboard|free-roam keyboard|stop|in-flight"`：通过，19 passed / 172 skipped。
- `npm run lint`：通过。
- `npm run build`：通过。
- `npm test`：通过，191 passed。
- `git diff --check`：通过。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：确认 `node` 监听 `*:7001`。

## 剩余风险

- 本轮只做 PC 前端 gate 和 mock/DOM 回归验证，没有触发真实底盘 manual/stop、Nav2、delivery 或 `/cmd_vel`；真实现场仍需在
  `0.0.0.0:7001` 工作台确认。
