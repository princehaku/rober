# Goal Progress Focus Restore Button

## sprint_type

micro

## 目标

- 继续推进 PC 端普通首屏易用性，减少 first-jog 恢复确认卡点下的点击和寻找成本。
- 当送达草稿覆盖 first-jog 基础确认时，`本轮进度` 主按钮应直接指向 `恢复试动确认` 按钮。
- 不调用 subagent；不发送真实运动、Nav2 执行、delivery complete、operator report 或 keyboard/manual pulse。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为 `恢复试动确认` 按钮增加稳定 ref 和 `data-testid`。
  - 在 first-jog 恢复卡点下，把 `本轮进度` 主按钮文案改为 `去恢复确认`，轮速行按钮改为 `去恢复`。
  - `focusPlainGoalProgressTarget("wheel")` 在该状态下只滚动并聚焦恢复按钮，不触发任何接口。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 restore-first-jog 场景，验证主按钮/行按钮文案、焦点行为和不发送 manual。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 06:20 起的 `本轮进度 -> 恢复试动确认` 聚焦行为。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed (2)`
  - `Tests 135 passed (135)`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 通过：`git diff --check`

## 剩余风险

- 本轮只改善 PC 首屏导航，不证明真实车已完成 wheel raw L/R 非零、完整 Nav2 路线执行、送达成功或键盘连续手控。
- 真实上车仍需 operator 显式点击恢复试动确认并在安全现场低速试动。
