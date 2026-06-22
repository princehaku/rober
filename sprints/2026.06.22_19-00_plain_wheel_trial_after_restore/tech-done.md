# 2026-06-22 19:00 Plain Wheel Trial After Restore

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`恢复试动确认` 成功后，轮速记录面板按钮从 `读取轮速` 变为 `开始试动读轮速`，明确下一步才会进入 first-jog 试动窗口。
- `pc-tools/workstation/test/App.test.ts`：补充恢复确认后的按钮文案和启用状态断言，同时继续确认恢复动作本身不调用 first-jog 或 manual。
- `docs/product/pc_tools_workstation.md`：同步记录恢复确认不发车，按钮文案只提示下一步试动。

## 验证结果

- `npm test`：通过，2 个 test files，123 个 tests。
- `npm run lint`：通过。
- `npm run build`：通过，包含 app/server TypeScript 与 Vite build。
- `git diff --check`：通过，无 whitespace error。

## 剩余风险

- 本轮只减少恢复试动确认后的操作歧义；真实 wheel raw L/R 非零仍必须由现场 first-jog 试动窗口读到。
- 当前真实上位机 operator report 仍是 delivery draft，wheel raw L/R 仍未证明非零。
