# 2026-06-23 00:55 键盘手控实时状态

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘手控面板新增实时状态行，显示未启用、等待按键、正在方向点动、已松开和已停止等普通话术。
- 该状态只读取前端已有 `keyboardControlArmed`、`keyboardHeldDirection` 和 `keyboardControlStatus`，不改变键盘 gate、不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`：补充键盘 ready 流程中的实时状态断言，覆盖启用后等待按键、按住前进、松开停止三态。
- `docs/product/pc_tools_workstation.md`：同步记录普通首屏键盘实时状态行。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控的现场可读性；没有发送真实键盘 pulse、manual 或 stop 请求。
- 真实 PC 键盘连续手控仍需要现场 operator 在材料 gate 全部满足后显式启用并按住方向键验证。
