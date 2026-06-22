# 2026-06-23 00:18 键盘复查轮速下一步提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：抽出 `plainKeyboardWheelProofIsNext`，让 `启用键盘` 与 `复查手控条件` 共用同一套“轮速是下一步”的判断。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当前置连接、键盘合同、移动前检查和现场画面已满足，但 wheel proof 仍缺失时，`复查手控条件` 显示 `复查手控条件（先补轮速，不发车）`。
- `pc-tools/workstation/test/App.test.ts`：扩展键盘轮速缺项回归，确认复查按钮文案指向轮速，且点击启用和键盘按键仍不调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只做只读刷新，不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`125 passed (125)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 普通首屏键盘 gate 的轮速下一步提示；真实 wheel raw L/R 非零、完整 Nav2 路线执行、delivery success 和真实 PC 键盘连续手控仍需要现场 operator 在安全确认后继续采集和确认。
- 本轮没有发送任何真实运动控制、Nav2 执行或送达确认请求。
