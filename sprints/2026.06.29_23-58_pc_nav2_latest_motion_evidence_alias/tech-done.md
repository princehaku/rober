# PC Nav2 Latest Motion Evidence Alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `RobotControlNavGoalExecutionLatestResponse` 中新增 latest 顶层白话和底盘命令/反馈证据 alias。
- `pc-tools/workstation/src/server/index.ts`：让只读 `GET /api/robot-control/nav2/goal/execution/latest` 顶层返回 `plain_hint`、上次/下次 command mode、非零命令计数、mode counts、wheel L/R 是否非零、IMU 姿态变化等字段；字段全部从既有 latest artifact 派生，不发起 NavigateToPose。
- `pc-tools/workstation/test/catalog.test.ts`：补 latest 已证明和 PWM 成功但 wheel raw L/R 未非零两种路径的断言。
- `docs/product/pc_tools_workstation.md`：同步记录 latest 顶层运动证据 alias。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2 latest execution proxy"`，4 个相关测试通过，156 个跳过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite 构建通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积提醒。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、375 个测试全部通过。
- 通过：重启本机 PC API 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/nav2/goal/execution/latest`，live 返回 `plain_hint=上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。`，`base_command_mode=pwm`，`next_execution_base_command_mode=ros`，`goal_execution_base_command_nonzero_count=49`，`goal_execution_base_feedback_lr_nonzero_proven=false`，`goal_execution_base_feedback_imu_attitude_delta_observed=true`，`goal_execution_base_feedback_latest_raw_left/right=0/0`。

## 剩余风险

- 本轮只增强 PC latest 只读证据字段；真实车体路线重跑仍需要现场人员勾选安全确认后操作，不在本轮自动执行。当前 live 结论指向“用 ROS 模式重跑并复验同窗口 wheel raw L/R”，不是雷达、相机或控制服务阻塞。
