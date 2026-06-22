# 2026-06-22 17:41 Wheel Save Button Wait Nonzero

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `保存轮速记录` 按钮在未拿到同帧非零 L/R 前显示“保存轮速记录（等非零 L/R）”，拿到可保存条件后恢复“保存轮速记录”。
- `pc-tools/workstation/test/App.test.ts`：补充默认、first-jog 成功、first-jog 仍为 0/0 三种状态下的保存按钮文案和禁用状态断言。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮不自动保存、不发送运动或手控命令。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 wheel raw L/R 非零卡点的保存入口可读性；真实非零仍需要现场运动窗口读到同一 T1001 帧 L/R 均非零。
- 当前真实上位机只读反馈显示 T1001 在线、电压约 12.43V，但 wheel raw L/R 为 0/0。
