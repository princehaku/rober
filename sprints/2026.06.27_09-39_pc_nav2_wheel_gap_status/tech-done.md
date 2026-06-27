# PC Nav2 轮速缺口状态所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 当最近 Nav2 goal 已 `goal_succeeded/result_status=succeeded`，但同一执行结果里的 `base_feedback_summary.wheel_feedback_lr_nonzero_proven=false` 时，`readback_summary.nav2.status` 改为 `goal_succeeded_wheel_feedback_not_proven`。
  - 这个状态明确区分“Nav2 action 成功”和“完整路线执行还差 wheel raw L/R 非零闭环”，避免继续显示泛化 `blocked/not_proven`。
  - 逻辑只读取最近执行 artifact，不会重新执行 Nav2、manual、keyboard、delivery、free-roam 或 `/cmd_vel`。
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 live 形状回归测试，锁定 `goal_succeeded + wheel_feedback_lr_nonzero_proven=false` 的专用状态。
- `docs/product/pc_tools_workstation.md`
  - 同步记录该状态合同和安全边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- catalog.test.ts --testNamePattern "Robot Control summary.*Nav2|Nav2 latest execution"`
  - `Test Files 1 passed`
  - `Tests 8 passed | 113 skipped`
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite 仍提示单 chunk 超过 500 kB，这是既有打包体积 warning，不影响本轮功能。
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 2 passed`
  - `Tests 282 passed`
- 通过：`git diff --check`
- 通过：重启 PC Node 后确认 `0.0.0.0:7001` 仍监听。
  - `node ... TCP *:7001 (LISTEN)`
  - PC Node 由 `launchctl submit -l rober.pc.api.7001` 托管，避免当前 shell 退出时带走 7001。
- live 只读确认：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`
  - `goal_execution_status=goal_succeeded`
  - `goal_execution_result_status=succeeded`
  - `goal_execution_proven=false`
  - `goal_execution_base_command_mode=pwm`
  - `next_execution_base_command_mode=ros`
  - `goal_execution_base_command_nonzero_count=49`
  - `goal_execution_base_feedback_sample_count=239`
  - `goal_execution_base_feedback_lr_nonzero_proven=false`
  - `goal_execution_base_feedback_latest_left_speed=0`
  - `goal_execution_base_feedback_latest_right_speed=0`

## 剩余风险

- 本轮只修 summary 状态合同，不修复真实底盘 L/R 仍为 `0/0` 的根因。
- 真实“完整 Nav2 路线执行”仍需要在现场安全确认后重新执行，并看到同窗口 wheel raw L/R 非零。
