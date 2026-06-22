# PC Keyboard Arm Gate

sprint_type: micro

## 实际改动

- PC 普通首屏键盘连续手控入口改为条件满足才可启用：`启用键盘` 按钮绑定现有 `canSendManualMotion` gate。
- 键盘面板新增“当前方向”普通状态，按住 W/A/S/D 或方向键时显示前进、后退、左转或右转，松开后回到未按键。
- 补齐 `已启用`、`未满足` 状态样式，避免普通首屏出现无样式状态 chip。
- 更新 Vue 测试，覆盖默认禁用态、条件满足后的启用态、按住 W 发送 240ms 脉冲、松开触发 stop，以及首屏方向提示。
- 本轮不修改后端 `/api/robot-control/base/manual` gate，不绕过 checklist/operator report，不声明真实 wheel raw L/R、完整 Nav2 或 delivery success 已完成。

## 验证结果

- 通过：`npm test`，Vitest `2 passed (2)`，`113 passed (113)`。
- 通过：`npm run lint`，ESLint 无报错。
- 通过：`npm run build`，`tsc` 与 Vite production build 通过。
- 通过：`git diff --check`，无 whitespace error。

## 剩余风险

- 这轮只提升 PC 键盘连续手控入口易用性；真实小车仍需要现场 operator/safety 确认后才能执行运动验证。
- 当前完整目标中的 wheel raw L/R 非零、完整 Nav2 路线执行和 delivery success 仍未由本轮证明。
