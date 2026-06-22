# 2026-06-22 20:35 Wheel Feedback Online Zero Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“轮速记录”在 L/R=0/0 时明确显示“已读到底盘反馈，但当前轮速是 L/R=0/0”，区分通信在线与轮速未非零。
- `pc-tools/workstation/test/App.test.ts`：更新普通首屏断言，确认 0/0 提示同时包含反馈在线和现场排查方向。
- `docs/product/pc_tools_workstation.md`：同步记录该提示仍只消费 summary 或只读采样结果，不发送 `/api/base/manual`、first-jog、Nav2 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少现场对 L/R=0/0 的误判；真实 wheel raw L/R 非零仍需要现场运动窗口内观察到同一 T1001 帧 L/R 均非零。
- 当前真实上位机 `/api/base/status` 显示底盘反馈在线、电压约 12.43V，但 L/R 仍为 0/0，不能作为 wheel raw L/R 非零完成证据。
