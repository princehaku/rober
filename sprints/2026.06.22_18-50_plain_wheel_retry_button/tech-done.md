# 2026-06-22 18:50 Plain Wheel Retry Button

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏“轮速记录”小面板新增 `读取轮速 / 重试读取轮速` 按钮，直接复用现有 `sendPlainFirstJog` 和 first-jog gate。
- `pc-tools/workstation/test/App.test.ts`：补充默认按钮文案和 L/R=0/0 后重试按钮行为断言，确认重试只调用固定 `/api/robot-control/base/first-jog`，不走旧 manual 代理。
- `docs/product/pc_tools_workstation.md`：同步记录该按钮是 wheel 区域内的 first-jog 入口，不绕过 gate，不发布 `/cmd_vel`。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少现场重试 wheel L/R 采集的操作路径；真实 wheel raw L/R 非零仍需要现场安全确认后实际试动读到同帧非零 L/R。
- 当前真实上位机只读反馈仍显示 T1001 可读但 L/R=0/0。
