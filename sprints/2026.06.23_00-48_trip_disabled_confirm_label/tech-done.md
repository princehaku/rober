# 2026-06-23 00:48 行程按钮确认前动作文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `行程操作` 的 `检查行程` 与 `执行行程` 按钮在未勾选行程前确认时显示 `先勾选确认`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：未连接小车时，两个按钮分别显示 `连接后检查行程` / `连接后执行行程`；pending 时显示 `检查中` / `执行中`。
- `pc-tools/workstation/test/App.test.ts`：更新默认首屏和行程操作回归，确认未勾选确认时按钮仍 disabled，勾选后恢复 `检查行程` / `执行行程`。
- `docs/product/pc_tools_workstation.md`：同步记录该文案不改变启用条件，不调用 preflight、不执行 Nav2，不发送 `/cmd_vel`、manual 或 delivery complete。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善完整 Nav2 路线执行入口的确认前提示；真实完整 Nav2 路线执行仍需要现场 operator 勾选确认并显式点击执行后，由上位机 `goal_succeeded` 证据证明。
- 本轮没有发送任何真实 Nav2 执行、运动控制、键盘 pulse 或送达确认请求。
