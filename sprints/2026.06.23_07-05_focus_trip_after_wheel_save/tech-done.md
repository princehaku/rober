# Focus Trip After Wheel Save

## sprint_type

micro

## 目标

- 继续推进 PC 端普通首屏易用性，让 wheel raw L/R 保存成功后自然进入完整 Nav2 行程步骤。
- `保存轮速记录` 成功后只把焦点移到 `行程操作` 面板，不自动执行 Nav2。
- 不调用 subagent；不发送额外真实运动、Nav2 执行、delivery complete 或 keyboard/manual pulse。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `savePlainWheelEvidence()` 在 operator report 写入成功、刷新 summary 后，只滚动并聚焦 `行程操作` 面板。
  - 保持 Nav2 preflight/execute 必须由 operator 显式勾选并点击。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展 first-jog 非零 L/R 保存场景，验证保存后焦点落到 `plain-trip-run`，且不调用 Nav2 execute。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-06-23 07:05 起的 wheel save 后聚焦行程面板行为。

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
- 真实上车仍需 operator 显式勾选并执行行程，再完成送达与键盘验证。
