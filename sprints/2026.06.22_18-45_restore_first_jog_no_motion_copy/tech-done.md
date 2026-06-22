# 2026-06-22 18:45 Restore First-Jog No-Motion Copy

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏在送达草稿覆盖试动前确认时，所有“恢复试动确认”提示都明确标注“不会发车”。
- `pc-tools/workstation/test/App.test.ts`：更新恢复试动确认流程断言，确认首屏文案明确说明不发车，并继续保持恢复动作不调用 `/api/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录恢复试动确认只恢复 first-jog 前置现场材料，不调用底盘运动、Nav2、delivery complete 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低现场误解风险；真实 wheel raw L/R 非零仍需要现场安全确认后的 first-jog 运动窗口读到非零。
- 当前真实上位机 operator report 仍是 delivery draft，wheel_feedback 和 LiDAR delta 仍未证明。
