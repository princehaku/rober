# PC Nav2 命令与底盘反馈事实条

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `当前事实` 的行程行新增专用摘要：Nav2 `goal_succeeded` 但 wheel raw L/R 未证明时，显示非零底盘命令数量、底盘反馈样本数量、当前 L/R 和 `不是雷达阻塞`。
  - 如果上车端下次 Nav2 执行模式已切到 `ros`，同一事实行继续保留 `下次将用 ros 复验`。
  - 该文案只翻译已有 readback，不改变 Nav2 gate，不把 goal success 提升为完整路线执行。
- `pc-tools/workstation/test/App.test.ts`
  - 更新回归测试，锁定 `49 条非零底盘命令 + 239 次反馈 + L/R=0/0 + 不是雷达阻塞 + 下次 ros 复验` 出现在普通首屏 `当前事实`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自动驾驶未动的首屏解释边界：优先查电机使能、供电、底盘模式和控制模式，不再把这类形态归因给雷达。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "explicit unproven execution|nonzero base commands"`
  - `Test Files 1 passed (1)`
  - `Tests 2 passed | 151 skipped (153)`
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 153 passed (153)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - `eslint .`
- 通过：`cd pc-tools/workstation && npm run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 保留既有 chunk size warning，本轮无新增构建失败。
- 通过：重启 PC Node 到 `0.0.0.0:7001`
  - `lsof` 显示 `node` PID `2644` 监听 `TCP *:7001`。
  - `curl http://127.0.0.1:7001/api/health` 返回 `mode=pc_only_readonly_workstation`、`safe_to_control=false`、`pc_only=true`。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回 live Nav2 事实：`goal_status=goal_succeeded`、`goal_execution_base_command_nonzero_count=49`、`goal_execution_base_feedback_sample_count=239`、`goal_execution_base_feedback_lr_nonzero_proven=false`、`L/R=0/0`、`next_execution_base_command_mode=ros`。

## 剩余风险

- 本轮只修首屏 WYSIWYG 文案，不执行新的 Nav2/底盘运动，不证明 wheel raw L/R 非零。
- live 仍需现场修复底盘轮速闭环、电机使能/供电/底盘模式或控制模式后，重新执行完整 Nav2 路线。
