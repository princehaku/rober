# 2026-06-23 00:11 Plain Wheel Readback Refresh Button

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“轮速记录”新增 `刷新当前轮速（只读）` 按钮，pending 时显示 `刷新中`，复用既有固定 `base/feedback-samples` 只读代理。
- `pc-tools/workstation/test/App.test.ts`：验证首屏显示该按钮，并确认点击只调用 `/api/robot-control/base/feedback-samples`，不会调用 manual、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只读取 T1001 L/R，不发送任何运动或送达确认接口。

## 验证结果

- `npm test`：通过，2 个 test files，124 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 wheel raw L/R 收口路径的普通首屏入口；真实 wheel raw L/R 非零仍需要现场低速试动窗口读到同帧 T1001 非零。
- 当前真实 `/api/base/status` 新鲜读回 T1001 在线但 L/R=0/0；只读刷新按钮不能替代 first-jog 运动窗口证据。
- Nav2 latest 已 `goal_succeeded`，delivery latest 仍为 `delivery_success=false`，PC 键盘连续手控仍缺 wheel/LiDAR/现场材料 gate。
