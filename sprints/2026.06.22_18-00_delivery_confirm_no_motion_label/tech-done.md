# 2026-06-22 18:00 Delivery Confirm No Motion Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏送达最终确认在全部确认项满足后显示 `确认送达（不发车）`，缺项状态仍显示缺项数量。
- `pc-tools/workstation/test/App.test.ts`：更新最终确认 ready 状态断言，锁定可提交按钮文案和不自动提交边界。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只解释动作边界，不发送 Nav2、manual、first-jog、stop、keyboard pulse 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 delivery success 最终确认按钮被误解成发车动作的风险；真实 delivery success 仍需要现场确认后显式点击并通过上位机 gate。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.44V，但 wheel raw L/R 为 0/0；PC 键盘连续手控仍缺 wheel/LiDAR/现场材料 HIL 证明。
