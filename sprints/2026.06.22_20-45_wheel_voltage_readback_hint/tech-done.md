# 2026-06-22 20:45 Wheel Voltage Readback Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 WAVE ROVER T1001 反馈帧最后一个 `v` 提取 `feedback_voltage_v`，放入 `readback_summary.base`。
- `pc-tools/workstation/src/shared/contracts.ts`：补充 `readback_summary.base.feedback_voltage_v` 合同字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“轮速记录”在 L/R=0/0 且有电压读回时显示“反馈电压约 ...V”，帮助现场区分反馈在线/供电可见与轮速未非零。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：覆盖 summary 电压提取和首屏电压提示。
- `docs/product/pc_tools_workstation.md`：同步记录电压只用于供电排查展示，不是运动、HIL 或 wheel raw L/R 非零证明。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只增加只读电压辅助提示；真实 wheel raw L/R 非零仍需要现场运动窗口内观察到同一 T1001 帧 L/R 均非零。
- 当前真实上位机 `/api/base/status` 显示底盘反馈在线、电压约 12.43V，但 L/R 仍为 0/0，不能作为 wheel raw L/R 非零完成证据。
