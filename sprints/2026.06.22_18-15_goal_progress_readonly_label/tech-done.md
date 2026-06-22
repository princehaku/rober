# 2026-06-22 18:15 Goal Progress Readonly Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `本轮进度` 刷新按钮显示为 `刷新进度（只读）`，pending 时显示 `刷新中`。
- `pc-tools/workstation/test/App.test.ts`：锁定默认和点击前的只读文案，并继续验证刷新只调用 summary、base feedback samples、Nav2 latest 与 delivery readback。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮不执行行程、不确认送达、不发送 manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 `本轮进度` 刷新被误解成执行动作的风险；真实 wheel raw L/R 非零、delivery success 和 PC 键盘连续手控仍需现场 HIL 验证。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.44V，但 wheel raw L/R 为 0/0。
