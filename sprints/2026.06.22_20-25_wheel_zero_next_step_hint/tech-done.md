# 2026-06-22 20:25 Wheel Zero Next Step Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“轮速记录”在只读 L/R 仍为 0/0 时，直接提示“若试动后仍为 0/0，检查电机使能、供电、模式和现场空间”。
- `pc-tools/workstation/test/App.test.ts`：更新普通首屏断言，确认 L/R=0/0 不再只提示“需要现场试动窗口”，而是给出现场排查方向。
- `docs/product/pc_tools_workstation.md`：同步记录该提示仍只消费 summary 或只读采样结果，不发送 `/api/base/manual`、first-jog、Nav2 或 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只提升 L/R=0/0 后的现场排查提示；真实 wheel raw L/R 非零仍需要现场运动窗口内观察到同一 T1001 帧 L/R 均非零。
- 当前真实上位机 `/api/base/status` 可读到 13 帧 T1001，但 L/R 仍为 0/0，不能作为 wheel raw L/R 非零完成证据。
