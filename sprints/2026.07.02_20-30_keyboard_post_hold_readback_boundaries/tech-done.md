# Keyboard Post Hold Readback Boundaries

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层新增 `keyboard_post_hold_readback_*` 只读边界，并同步 `current_keyboard_action_post_hold_readback_*`。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 类型，固定键盘 post-hold 读回链不发送运动/控制动作的合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-keyboard-hold-gate` DOM 暴露 post-hold readback 的只读 flags。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 API 与 DOM 的键盘 post-hold 只读边界。
- `docs/product/pc_tools_workstation.md`：同步产品合同，说明松开/停止后的复验链只读取 wheel feedback samples 和 summary，不再发送 manual、stop、Nav2、keyboard、free-roam、建图、delivery 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍保留既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不执行真实键盘按住移动，不发送 manual/Nav2/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实 wheel L/R 非零和松开后 stop 收口仍需现场勾安全确认后实车复验。
