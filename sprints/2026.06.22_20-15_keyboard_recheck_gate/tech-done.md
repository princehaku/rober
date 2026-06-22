# 2026-06-22 20:15 Keyboard Recheck Gate

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏键盘面板新增 `复查手控条件`，让 operator 在键盘区域直接刷新手控 gate。
- `pc-tools/workstation/test/App.test.ts`：补充按钮行为断言，确认它会触发只读 `/api/robot-control/base/feedback-samples` 复查，但不会触发 `/api/robot-control/base/manual`。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮只刷新 summary、底盘反馈和收口读回，不 arm 键盘、不发送 manual/stop、不调用 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只降低 PC 键盘连续手控 gate 复查摩擦；真实键盘连续手控仍需要现场材料 gate 满足后由 operator 显式启用并长按方向键产生真实 bounded manual pulse 证据。
- 当前真实 summary 仍显示 keyboard bounded pulse 合同存在，但 operator 三项、wheel raw L/R 非零和 LiDAR delta 材料未满足，键盘仍不能启用。
