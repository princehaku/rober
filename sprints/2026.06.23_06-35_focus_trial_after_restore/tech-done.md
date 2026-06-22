# Focus Trial After Restore

## sprint_type

micro

## 目标

- 继续推进 PC 端普通首屏易用性，让 first-jog 恢复确认后的下一步更直接。
- `恢复试动确认` 成功后，只把焦点移到 `开始低速试动读非零 L/R` 按钮，不自动发车。
- 不调用 subagent；不发送真实运动、Nav2 执行、delivery complete、operator report 之外的额外请求或 keyboard/manual pulse。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为 `plain-wheel-trial` 试动按钮增加 ref。
  - `restorePlainFirstJogMaterial()` 在恢复确认成功、刷新 summary 后，只滚动并聚焦试动按钮。
  - 保持 first-jog/manual 调用必须由 operator 显式点击试动按钮触发。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展恢复确认测试，验证恢复成功后发生焦点动作，且没有调用 first-jog/manual。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 06:35 起的恢复确认后聚焦试动按钮行为。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 剩余风险

- 本轮只改善 PC 首屏焦点引导，不证明真实车已完成 wheel raw L/R 非零、完整 Nav2 路线执行、送达成功或键盘连续手控。
- 真实上车仍需 operator 显式点击试动按钮，并在安全现场采集非零 L/R。
