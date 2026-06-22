# 2026-06-23 00:45 键盘入口全禁用态动作文案

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：新增 `plainKeyboardBlockedActionLabel`，让 `启用键盘` 与 `复查手控条件` 在所有常见禁用态都显示具体下一步动作。
- 动作文案覆盖：`先连接`、`先复查入口`、`先做检查`、`先记录画面`、`先补轮速`、`先补雷达`、`先复查材料`。
- `pc-tools/workstation/test/App.test.ts`：更新默认首屏和缺键盘合同两处断言，确认按钮从抽象数量变为 `先复查入口`。
- `docs/product/pc_tools_workstation.md`：同步记录该改动不改变键盘 gate，不 arm 键盘、不发送 keyboard pulse、manual、stop、Nav2、delivery complete 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控入口禁用态的可读性；真实 PC 键盘连续手控仍需要 wheel raw L/R 非零、LiDAR motion delta、移动前检查和后端 bounded pulse 合同全部满足后，再由 operator 显式启用并长按方向键验证。
- 本轮没有发送任何真实运动控制、键盘 pulse、Nav2 执行或送达确认请求。
