# 2026.07.02 23:05 安全确认动作 operator report 预检 alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：补齐安全确认 ready-action、primary safety action 和 current motion action 的 `operator_report_preflight_required` 顶层 alias 类型。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 `field_acceptance_packet.safety_confirm_ready_actions[]` 同源输出 operator report 预检字段，固定说明 ready motion 动作不要求额外现场报告预检。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在 `plain-field-acceptance-packet` 和 `plain-trip-current-motion-action` DOM 暴露对应 `data-*`，现场 smoke 可直接读到 `false`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：补 summary 与 DOM 断言。
- `docs/product/pc_tools_workstation.md`：同步最小预检合同，明确 ready action、primary action 和 current motion action 均需暴露 operator report 非前置字段。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed / 247 passed`。
- `git diff --check`：通过，无 whitespace error。
- `cd pc-tools/workstation && npm run build`：通过，Vite 保留既有 chunk size warning。
- `cd pc-tools/workstation && npm run lint`：通过。

## 剩余风险

- 本轮覆盖 PC summary/DOM/mock；真实运动仍需要现场安全确认后用真实上车 API 复核。
