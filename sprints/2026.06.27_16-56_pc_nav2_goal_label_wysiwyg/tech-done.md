# 2026.06.27 16:56 PC Nav2 ready 文案所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 `safe_command_boundary.nav2_goal_label` 在路线读数 ready 时从 `路线读数已准备，先看地图画面` 改为 `路线读数已准备，等待地图画面确认`。
  - 保持 `nav2_goal_next_action`、安全确认、ROS 重跑、wheel raw L/R 复验口径不变。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步更新 `nav2_goal_label` 字面量合同。
- `pc-tools/workstation/test/catalog.test.ts`
  - 同步更新 fail-closed summary 合同测试。
- `docs/product/pc_tools_workstation.md`
  - 记录 Nav2 ready 文案不再暗示额外手动步骤，地图和路线可见性仍由前端 WYSIWYG gate 判断。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "nav2|Nav2|goal"`：通过，19 passed。
- `npm test -- --run test/App.test.ts -t "visible map|radar readback|radar map"`：通过，4 passed。
- `npm test -- --run`：通过，2 files / 298 tests passed。
- `npm run build`：通过，前端 bundle 保持 `/assets/index-Cmlq3fJ_.js`。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 7001 live 只读验证：重启 PC Node 后，`GET /api/robot-control/summary` 返回 `nav2_goal_ready=true`、`nav2_goal_label=路线读数已准备，等待地图画面确认`，next action 仍为 `用 ROS 重跑图上路线` 并确认同窗口 `wheel raw L/R` 非零。

## 剩余风险

- 本轮只修正 Nav2 ready 的短文案，不执行真实 Nav2 路线、不证明 wheel raw L/R 已非零、不确认 delivery success。
- 真实自动驾驶仍需要现场安全确认后重跑 ROS/T=13 图上路线，并在同窗口证明 wheel raw L/R 非零。
