# PC Nav2 ROS rerun summary guidance

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `safe_command_boundary` 增加 Nav2 行程下一步短口径：`nav2_goal_wheel_feedback_status`、`nav2_goal_next_action`、`nav2_goal_execution_mode_label`。
  - 当最近 Nav2 action 成功但 wheel raw L/R 同窗口未非零，且上位机策略显示下一次会走 ROS 时，summary 会直接提示“勾选行程前安全确认后用 ROS 重跑图上路线”。
  - 完整路线已证明时，summary 会提示继续送达确认；路线未就绪时仍提示先生成路线和读到地图位姿。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 Robot Control summary 合同。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 补充合同和前端 fixture，覆盖 live 的 `pwm -> ros` 重跑口径。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 Nav2 重跑 summary 字段。

## 验证结果

- `npm test -- --run catalog.test.ts -t "Nav2 execution proof|rerun ROS Nav2|workstation fail-closed API contracts"`
  - 结果：通过，`125 passed`。
- `npm test`
  - 结果：通过，`2 passed`，`290 passed`。
- `npm run build`
  - 结果：通过，生成 `dist/`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮 summary 字段。
- `curl -sS 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787' | jq '{nav2_goal_ready:.safe_command_boundary.nav2_goal_ready, nav2_goal_label:.safe_command_boundary.nav2_goal_label, nav2_goal_wheel_feedback_status:.safe_command_boundary.nav2_goal_wheel_feedback_status, nav2_goal_next_action:.safe_command_boundary.nav2_goal_next_action, nav2_goal_execution_mode_label:.safe_command_boundary.nav2_goal_execution_mode_label, nav2_readback:.readback_summary.nav2}'`
  - 结果：通过；live 显示 `nav2_goal_ready=true`，`nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`，`nav2_goal_execution_mode_label=上次 pwm，下次 ros`，`nav2_goal_next_action=上次路线 action 成功但 wheel raw L/R=0/0 未非零；勾选行程前安全确认后用 ROS 重跑图上路线`。

## 剩余风险

- 本轮不执行 Nav2、不发送 `/cmd_vel`，只把下一次应如何重跑的只读 guidance 写入 summary。
- live 当前仍未完成 wheel raw L/R 同窗口非零复验；后续需要现场勾安全确认后执行 ROS 路线复验。
