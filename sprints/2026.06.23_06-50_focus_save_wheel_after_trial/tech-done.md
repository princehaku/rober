# Focus Save Wheel After Trial

## sprint_type

micro

## 目标

- 继续推进 PC 端普通首屏易用性，减少 wheel raw L/R 已拿到但未保存的漏步。
- first-jog 返回非零 L/R 后，只把焦点移到 `保存轮速记录` 按钮，不自动保存。
- 不调用 subagent；不发送额外真实运动、Nav2 执行、delivery complete、operator report 或 keyboard/manual pulse。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 为 `plain-wheel-save` 按钮增加 ref。
  - `sendPlainFirstJog()` 在 first-jog 返回 `wheel_feedback_lr_nonzero_proven=true` 并完成只读刷新后，只滚动并聚焦保存按钮。
  - 保持保存 wheel operator report 必须由 operator 显式点击 `保存轮速记录`。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 first-jog 非零 L/R 场景，验证保存按钮可用、焦点动作发生，且点击保存前不会调用 operator report。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 06:50 起的 first-jog 成功后聚焦保存按钮行为。

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
- 真实上车仍需 operator 显式点击保存按钮，之后继续完成 Nav2、delivery 和键盘验证。
