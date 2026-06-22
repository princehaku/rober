# 2026-06-23 00:37 键盘手控雷达缺项提示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把键盘 gate 的轮速下一步判断扩展为 `plainKeyboardMotionProofNextStep`，在前置条件满足后区分 `wheel` 与 `lidar` 两类运动证据缺项。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当 wheel proof 已满足但 LiDAR motion delta 仍缺失时，普通首屏 `启用键盘` 显示 `启用键盘（先补雷达）`，`复查手控条件` 显示 `复查手控条件（先补雷达，不发车）`。
- `pc-tools/workstation/test/App.test.ts`：新增 wheel 已满足、LiDAR motion delta 缺失的键盘 gate 回归，确认按钮仍禁用且不会调用 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录该状态仍不 arm 键盘，复查按钮仍只读刷新。

## 验证结果

- `npm test`：通过，`2 passed (2)`，`126 passed (126)`。
- `npm run lint`：通过，无 ESLint 报错。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只改善 PC 键盘连续手控 gate 的 LiDAR 缺项提示；真实 PC 键盘连续手控仍需要 wheel raw L/R 非零、LiDAR motion delta、移动前检查和后端 bounded pulse 合同全部满足后，再由 operator 显式启用并长按方向键验证。
- 本轮没有发送任何真实运动控制、键盘 pulse、Nav2 执行或送达确认请求。
