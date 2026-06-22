# 2026-06-22 17:19 Wheel Zero Next Action

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `轮速记录` 增加 `下一步` 提示；当 readback 或 first-jog 结果为 `L/R=0/0` 时，提示现场检查电机使能、供电、模式和现场空间后重试读取轮速。
- `pc-tools/workstation/test/App.test.ts`：补充 summary 读回、底盘反馈采样和 first-jog 失败三种 `L/R=0/0` 场景下的下一步提示断言，确认仍不调用 manual/operator report。
- `docs/product/pc_tools_workstation.md`：同步记录该提示不发送运动命令，也不把静态反馈、电压或 `0/0` 当作非零证明。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 wheel raw L/R 非零卡点的普通排障引导；真实非零仍需要现场运动窗口读到同一 T1001 帧 L/R 均非零。
- 真实上位机当前只读反馈仍显示 T1001 在线、电压约 12.43V，但 wheel raw L/R 为 0/0。
