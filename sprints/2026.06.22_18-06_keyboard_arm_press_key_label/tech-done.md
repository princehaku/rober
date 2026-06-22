# 2026-06-22 18:06 Keyboard Arm Press Key Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘 gate 满足后，`启用键盘` 显示为 `启用键盘（按键才动）`。
- `pc-tools/workstation/test/App.test.ts`：更新键盘可用状态下的 arm 按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录点击启用只聚焦键盘面板，不发送 keyboard pulse、manual、stop、Nav2 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 PC 键盘连续手控入口被误解成“点击即动”的风险；真实连续手控仍需 wheel/LiDAR/现场材料满足后，在现场安全窗口按键 HIL 验证。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.44V，但 wheel raw L/R 为 0/0。
