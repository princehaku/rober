# 2026-06-23 00:51 行程结果只读按钮文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 的最近结果按钮从 `读取行程结果` 调整为 `读取行程结果（只读）`。
- 已读到成功行程后，按钮从 `重新读取行程` 调整为 `重新读取行程（只读）`。
- `pc-tools/workstation/test/App.test.ts`：更新默认首屏、行程成功后和 delivery latest 预填三处按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只读最近 Nav2 execution latest，不执行 Nav2 goal，不发送 `/cmd_vel`、manual 或 delivery complete。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善完整 Nav2 路线执行证据读取入口的安全可读性；真实完整 Nav2 路线执行仍需要现场 operator 显式执行后，由上位机 `goal_succeeded` 证据证明。
- 本轮没有发送任何真实 Nav2 执行、运动控制、键盘 pulse 或送达确认请求。
