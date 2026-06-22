# 2026-06-22 17:57 Wheel Trial Low Speed Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `轮速记录` first-jog 入口改为 `低速试动读轮速`，恢复材料后显示 `开始低速试动读轮速`，失败后显示 `重试低速试动读轮速`。
- `pc-tools/workstation/test/App.test.ts`：更新普通默认、恢复材料后、失败重试三种状态的按钮文案断言。
- `docs/product/pc_tools_workstation.md`：同步记录该文案只说明轮速非零需要低速试动窗口，不改变 gate 或自动发车。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低现场把静态读取误解为 wheel raw L/R 非零证明的风险；真实非零仍需要现场安全窗口完成低速试动，并读到同一 T1001 帧 L/R 均非零。
- 当前真实只读 `/api/base/status` 显示 T1001 在线、电压约 12.44V，但 wheel raw L/R 仍为 0/0。
- 当前真实 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false；PC 键盘连续手控仍需 wheel/LiDAR/现场材料补齐后 HIL 验证。
