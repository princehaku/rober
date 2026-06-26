# Nav2 HIL False WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - Robot Control summary 新增 `readback_summary.nav2.goal_execution_hil_pass`。
  - 当上车端 Nav2 execution artifact 显式 `hil_pass=false` 时，即使 `NavigateToPose` action 返回 `goal_succeeded` 且有 feedback samples，PC 也把 `goal_execution_proven=false`，并且不再把 nav2 summary status 提升为 `goal_succeeded`。
- `pc-tools/workstation/src/server/index.ts`
  - Nav2 latest/execute 代理的 `goal_execution_key_values` 新增 `hil_pass`。
  - `hil_pass=false` 优先级高于旧的 `nav2_goal_execution_proven` 字段和 action success 推导，避免只读 latest 被误当作完整路线执行。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏完整路线判断消费 `hil_pass=false`。
  - 地图行程状态文案从 `执行未证明` 调整为 `真车未证明`，更贴近普通用户理解。
- `pc-tools/workstation/test/*`
  - 补齐 summary、latest proxy、普通首屏送达 gate 的 HIL false 回归测试。

## 验证结果

- `npm test -- catalog.test.ts --testNamePattern "Nav2|nav2|HIL|hil|summary"`
  - 33 passed / 76 skipped。
- `npm test -- App.test.ts --testNamePattern "Nav2|nav2|行程|hil_pass|路线执行"`
  - 14 passed / 128 skipped。
- `npm run build`
  - 通过；保留既有 Vite chunk size warning。
- live 7001 summary 复核：
  - `goal_execution_status=goal_succeeded`
  - `goal_execution_hil_pass=false`
  - `goal_execution_proven=false`
  - `readback_summary.nav2.status=not_proven`

## 剩余风险

- 本轮修正的是 PC WYSIWYG 口径和送达/完整路线 gate，不直接重跑真实 Nav2 goal。
- 当前现场证据说明：旧 Nav2 action artifact 成功，但真车路线执行未证明；底盘 wheel L/R 仍为 0/0。
- 下一轮仍需继续处理真实运动链路：先证明 PC 键盘/first-jog 能读到非零轮速，再推进完整 Nav2 路线执行。
