# 2026-06-22 18:09 Keyboard Stop Always Available Label

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘面板 stop 按钮显示为 `键盘停止（随时可点）`，并新增 `keyboard-control-stop` 测试定位。
- `pc-tools/workstation/test/App.test.ts`：锁定普通首屏键盘 stop 按钮文案。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮仍走既有固定 stop 代理，不放宽非 stop manual gate。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只提升 PC 键盘连续手控 fail-safe 入口可读性；真实连续手控仍需 wheel/LiDAR/现场材料满足后，在现场安全窗口按键 HIL 验证。
- 当前真实只读状态显示 Nav2 latest 已 `goal_succeeded`，delivery 仍为 false，operator report 仍是送达草稿。
- 当前真实 `/api/base/status` 仍只读到 T1001 在线、电压约 12.44V，但 wheel raw L/R 为 0/0。
