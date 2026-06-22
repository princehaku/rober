# 2026-06-22 17:54 Keyboard Recheck No Motion Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `复查手控条件` 在键盘 gate 未满足时显示“还差 N 项，不发车”，减少现场误以为复查会触发手控。
- `pc-tools/workstation/test/App.test.ts`：更新默认缺三项和合同缺一项两种键盘 gate 的按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录该复查按钮只读刷新，不发送 keyboard pulse、manual、first-jog、stop、Nav2 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控入口的安全感和可读性；真正连续手控仍需 wheel raw L/R 非零、雷达移动记录和现场材料满足后，在现场安全窗口 HIL 验证。
- 当前真实只读状态显示 delivery 仍为 false，operator report 仍是送达草稿且基础安全/观察/送达 claim 未确认。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.42V，但 wheel raw L/R 为 0/0。
