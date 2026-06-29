# PC Nav2 Motion Closure Plain Diagnosis

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏行程操作区新增 `plain-trip-motion-closure` 只读诊断行。它把路线成功、底盘非零命令、IMU 姿态变化和轮速 L/R 未非零放在同一条普通话结论里，明确当前自动驾驶卡点不是相机或雷达阻塞。
- `pc-tools/workstation/test/App.test.ts`：补充旧 PWM 路线成功但 L/R=0/0、下一轮 ROS 复验的普通首屏断言，并确认不会触发 Nav2 execute、manual 或 `/cmd_vel`。
- `pc-tools/README.md`：同步记录行程卡点只读诊断口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，218 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`，client/server TypeScript 与 Vite build 成功；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `node` 监听 `*:7001`。
- 通过：live summary 确认当前 Nav2 形态为 `goal_succeeded_wheel_feedback_not_proven`、上次 `pwm`、下次 `ros`、非零底盘命令 `49`、IMU 姿态变化 `true`、轮速 L/R=`0/0` 且 `goal_execution_base_feedback_lr_nonzero_proven=false`。

## 剩余风险

- 本轮只增强 PC 普通首屏解释，不替代真实现场执行复验；完整 Nav2 路线仍需要用户现场勾安全确认后重跑，并在同窗口确认轮速 L/R 非零。
- 本轮不启动 Nav2、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
