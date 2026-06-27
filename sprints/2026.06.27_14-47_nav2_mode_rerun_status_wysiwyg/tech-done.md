# 2026.06.27 14:47 Nav2 模式复验状态 WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `readback_summary.nav2` 中新增 `goal_execution_mode_rerun_status`。
  - 当最近一次执行模式与下一次上车配置模式不同，例如 `pwm -> ros`，返回 `pending_ros_rerun_after_pwm`；模式一致时返回 `not_required`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首屏自动驾驶诊断增加 `旧 PWM 结果，等待 ROS 复验`。
  - 继续保留“不是摄像头或雷达阻塞；已发到底盘但 wheel raw L/R 仍 0/0”的根因说明。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步扩展 summary 合同字段。
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `docs/product/pc_tools_workstation.md`
- `docs/navigation/fixed_route_workflow.md`

## 验证结果

- 已通过：`npm test -- --run catalog.test.ts -t "Robot Control summary tells the operator to rerun ROS Nav2"`
- 已通过：`npm test -- --run App.test.ts -t "keeps IMU-only route arrival visible while calling out zero wheel readback"`
- 已通过：`npm test`，291 个测试通过。
- 已通过：`npm run build`，Vite 仍有既有 chunk size 警告。
- 已通过：重启/确认 PC Node 继续监听 `*:7001`。
- 已通过：只读 `GET /api/robot-control/summary?robot_base_url=http://192.168.1.11:8787` 返回：
  - `readback_summary.nav2.goal_execution_mode_rerun_status=pending_ros_rerun_after_pwm`
  - `goal_execution_base_command_mode=pwm`
  - `next_execution_base_command_mode=ros`
  - `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`
- 已通过：`curl -fsS http://127.0.0.1:7001/` 返回首页 HTML。

## 剩余风险

- 本轮未触发真实 Nav2 重跑、manual、keyboard、free-roam 或 `/cmd_vel`。
- 当前 live 证据仍是旧 PWM Nav2 artifact：action succeeded、非零底盘命令已发、IMU 有姿态变化，但同窗口 T=1001 wheel raw L/R 仍为 `0/0`。
- 完整自动驾驶修好仍需要现场安全确认后用 ROS/T=13 重跑图上路线，并证明同窗口 wheel raw L/R 非零。
