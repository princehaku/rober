# PC keyboard ROS command mode WYSIWYG

## sprint_type

micro

## 实际改动

- `RobotControlSummaryResponse.safe_command_boundary` 新增 `keyboard_manual_command_mode: "ros"`，把 PC 键盘连续手控默认走 ROS bridge 的事实结构化暴露出来。
- `lockedBoundary()` 输出 `keyboard_manual_command_mode=ros`，与 PC Node 实际转发 `/api/base/manual` 时写入的 `command_mode=ros` 对齐。
- 普通首屏键盘当前事实和键盘指南改为消费该 contract，显示“ROS 桥接低速入口”；高级诊断 `keyboard continuous control` 同步显示 `command_mode=ros`。
- 更新 catalog/App 测试断言，覆盖 summary contract、普通首屏文案和高级诊断字段。
- 更新 `docs/product/pc_tools_workstation.md`，记录该变化只暴露既有键盘连续手控合同，不自动启用键盘或发送任何运动命令。

## 验证结果

- `npm --prefix pc-tools/workstation test` 通过：2 个 test files、365 个 tests 全部通过。
- `npm --prefix pc-tools/workstation run build` 通过：`tsc -p tsconfig.app.json`、`vite build`、`tsc -p tsconfig.server.json` 全部完成；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提示。
- PC Node 已按 `HOST=0.0.0.0 PORT=7001 npm --prefix pc-tools/workstation run api` 重启，`lsof` 确认 PID `28804` 监听 `*:7001`。
- 只读复核 `GET http://127.0.0.1:7001/api/robot-control/summary`：`keyboard_control_mode=bounded_repeating_manual_pulse`、`keyboard_manual_command_mode=ros`、`keyboard_control_start_ready=true`、`nav2_goal_ready=true`、`nav2_goal_execution_mode_label=上次 pwm，下次 ros`、`robot_control_executed=false`。

## 剩余风险

- 该轮不发送真实键盘脉冲、不执行 Nav2、不验证 wheel raw L/R 非零；真实移动仍需要现场勾选安全确认后操作。
- live 自动驾驶仍显示上一轮执行 wheel raw L/R 为 `0/0`，需要后续现场安全确认后用 ROS 路线重跑复验。
