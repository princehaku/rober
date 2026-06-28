# Nav2 summary plain hint

- sprint_type: micro
- 时间：2026-06-29 06:48 CST
- Owner：User Touchpoint Full-Stack Engineer（主会话执行；本轮按用户要求不调用 subagent）

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.nav2` 新增 `plain_hint`，把 `execution_status_plain` 和 `next_action_plain` 合成一条可直接读取的自动驾驶事实。
  - fail-closed summary 也补齐同名字段，避免读取失败时字段缺失。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 `RobotControlSummaryResponse.readback_summary.nav2` 类型，显式声明 `plain_hint`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 补齐 Nav2 latest fallback 的 `plain_hint/latest_key_values`，保持本地 fallback 与代理合同一致。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖路线未准备、完整路线已证明、action 成功但 wheel raw L/R 未非零三种读回。
- `pc-tools/workstation/test/App.test.ts`
  - 同步默认 summary fixture 的 Nav2 `plain_hint`。
- `docs/product/pc_tools_workstation.md`
  - 记录 summary Nav2 `plain_hint` 的只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "Robot Control V1"`
  - 结果：1 个测试文件通过，1 个用例通过，214 个同文件用例按过滤跳过。
- 首轮失败后修正断言，再通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary"`
  - 初始失败原因：未准备路线场景的 `plain_hint` 会包含当前根因；测试原先只期待无根因短句。
  - 修正后结果：1 个测试文件通过，38 个用例通过，122 个同文件用例按过滤跳过。
- 通过：`npm --prefix pc-tools/workstation run build`
  - 结果：TypeScript 与 Vite build 通过；保留既有 Vite chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test`
  - 结果：2 个测试文件通过，375 个用例通过。
- 通过：重启 PC API 到 `0.0.0.0:7001`，实际监听 PID `9874`。
  - 只读 `GET /api/robot-control/summary` 结果：`readback_summary.nav2.plain_hint=上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零...下一步：勾选行程前安全确认后用 ROS 模式重跑图上路线...`，`next_execution_base_command_mode=ros`，`goal_execution_base_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮只补 Nav2 只读 summary 合成字段，不执行路线、不启动 runtime、不发送 manual/keyboard/free-roam/delivery/stop。
- live 完整 Nav2 仍需要 operator 勾选安全确认后显式重跑路线，并在同窗口读到 wheel raw L/R 非零才能闭环。
