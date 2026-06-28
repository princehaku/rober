# PC Nav2 managed runtime 自动启动提示

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 中修正 Nav2 `nav2_goal_next_action` 的短文案解析：当后端 next_action 同时包含“用 ROS 重跑图上路线”和“执行时会自动启动 runtime”时，按钮/下一步继续优先展示重跑路线动作，不会误取末尾 runtime 说明。
- 同步修正自动驾驶诊断：当 `nav2_goal_ready=true` 且后端声明执行时会自动启动自动驾驶 runtime，普通界面不再把 lifecycle/controller 停止显示成额外发车前置任务，而是显示“执行时会自动启动自动驾驶 runtime”。
- 在 `pc-tools/workstation/test/App.test.ts` 新增 managed Nav2 runtime autostart 场景，覆盖当前现场形态：上次 PWM action 成功、IMU 有变化、wheel L/R=0/0、下次 ROS 重跑、执行时自动启动 runtime。

## 验证结果

- `npm --prefix pc-tools/workstation test -- -t "managed Nav2 runtime autostart|IMU-only route arrival"` 通过：2 tests passed。
- `npm --prefix pc-tools/workstation test` 通过：2 files passed, 368 tests passed。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留 Vite chunk size 既有警告。
- 只读查询 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 通过，现场为 `nav2_goal_ready=true`、`next_execution_base_command_mode=ros`、`goal_execution_mode_rerun_status=pending_ros_rerun_after_pwm`、`wheel L/R=0/0`、`IMU=true`，且 next_action 明确“执行时会自动启动自动驾驶 runtime”。

## 剩余风险

- 本轮没有现场安全确认，因此没有触发 `/api/nav2/goal/execute`、底盘手控、键盘手控、雷达启动或任何真实运动命令。
- 当前 Nav2 仍未最终完成验收：需要 CEO 现场勾选安全确认后用 ROS 重跑图上路线，并在同一执行窗口读到 wheel L/R 非零。
- 摄像头和雷达当前问题仍未通过真实硬件复测；本轮只推进自动驾驶普通界面的状态解释和最小预检口径。
