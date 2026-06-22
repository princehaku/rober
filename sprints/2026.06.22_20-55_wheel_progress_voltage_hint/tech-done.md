# 2026-06-22 20:55 Wheel Progress Voltage Hint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“本轮进度”的 `轮速记录` 项在 summary 有 `feedback_voltage_v` 时显示“反馈电压约 ...V”。
- `pc-tools/workstation/test/App.test.ts`：补充进度区电压提示断言，确认 L/R=0/0、T1001 帧数和电压会一起展示。
- `docs/product/pc_tools_workstation.md`：同步记录该电压只用于现场判断反馈在线和供电读数可见，不是 wheel raw L/R 非零、运动或 HIL 证明。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只把已读电压同步到进度摘要；真实 wheel raw L/R 非零仍需要现场运动窗口内观察到同一 T1001 帧 L/R 均非零。
- 当前真实上位机仍显示底盘反馈在线、电压约 12.43V，但 L/R 为 0/0。
