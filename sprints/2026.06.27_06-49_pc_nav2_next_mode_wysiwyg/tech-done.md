# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把上位机 `control_policy.nav2_base_command_mode` 纳入只读 key 白名单，并提升为 `readback_summary.nav2.next_execution_base_command_mode`。
- `pc-tools/workstation/src/shared/contracts.ts`：扩展 Nav2 summary contract，区分“最近一次执行模式”和“下一次执行模式”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏当前事实在旧 artifact 模式与下一次执行模式不一致时显示“下次将用 ros 复验”。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补服务端和 DOM 回归，覆盖旧 `pwm` 结果与下一次 `ros` 复验配置同时展示。
- `docs/product/pc_tools_workstation.md`：同步记录该 WYSIWYG 口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts`，`150 passed (150)`。
- 通过：`npm run build`；仍有既有 Vite chunk size warning，未影响构建产物生成。
- 通过：`npm run lint`。
- 通过：`npm test -- --run test/catalog.test.ts`，`113 passed (113)`。
- 通过：PC Node 已重启，PID `40415` 监听 `0.0.0.0:7001`；live summary 显示
  `goal_execution_base_command_mode=pwm`、`next_execution_base_command_mode=ros`，
  且 `read_endpoints.status.key_values.nav2_base_command_mode=ros`。

## 剩余风险

- 该改动只修复 PC 展示和摘要口径，不执行真实 Nav2 发车。
- 最近 live Nav2 artifact 仍是旧 `pwm` 执行记录；需要现场安全确认后重新执行，才能验证 `ros` 模式是否让同窗口 `T=1001.L/R` 非零。
