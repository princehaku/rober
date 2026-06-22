# Stale Nav2 Requires Rerun

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：把“读到成功证据”和“本轮行程已完成”拆开。超过 15 分钟的 Nav2 `goal_succeeded` 继续展示为历史证据，但不再让本轮进度、送达 checklist 或行程按钮视为完成。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当只读 latest/delivery 中存在旧 Nav2 成功记录时，普通首屏 `任务收口`、`本轮进度` 和 `验收卡点` 改为提示“重新执行本轮行程”。
- `pc-tools/workstation/test/App.test.ts`：更新 stale Nav2 与 delivery latest 草稿测试，确认旧路线会指向行程复验，不调用 Nav2 execute、delivery complete、manual 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步记录 stale Nav2 不再算本轮完成的产品边界。

## 验证结果

- 通过：`npm test`，结果 `2 passed (2)`、`130 passed (130)`。
- 通过：`npm run lint`。
- 通过：`npm run build`，结果 `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
- 通过：`git diff --check`。

## 剩余风险

- 本轮没有真实执行 Nav2，只收紧 PC 端对旧路线证据的验收口径。
- 真实上位机仍需要现场重新完成本轮 Nav2 行程、wheel raw L/R 非零、delivery success 和键盘连续手控验证。
