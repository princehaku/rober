# PC Nav2 Wheel Raw L/R Plain Summary

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：在 `readback_summary.nav2` 合同中新增 `goal_execution_wheel_raw_lr_status_plain` 与 `goal_execution_wheel_raw_lr_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：把完整路线执行的 wheel raw L/R 结论拆成独立白话字段。这样脚本不用从 `execution_status_plain` 长句中解析同窗口轮速是否非零。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：补齐默认夹具、fail-closed 摘要和 live-like Nav2 回归断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录只读 summary 合同变化。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Robot Control summary|wheel raw"`：通过，1 个文件，39 个测试通过。
- `npm --prefix pc-tools/workstation test`：通过，2 个文件，373 个测试通过。
- `npm --prefix pc-tools/workstation run build`：通过；Vite 保留既有 chunk size warning。
- 7001 本地 live 只读复验：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `goal_execution_wheel_raw_lr_status_plain=上次路线 action 成功，但执行窗口 wheel raw L/R=0/0 未非零；已看到 49 次非零底盘命令，IMU 姿态有变化。`，`goal_execution_wheel_raw_lr_next_action_plain=勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认 wheel raw L/R 非零。`，同时 `safe_to_control=false`、`robot_control_executed=false`。

## 剩余风险

- 本轮只新增 PC 只读字段，不发车、不重跑 Nav2、不证明现场 wheel raw L/R 非零。
- 当前 live 仍需要 operator 勾选现场安全确认后，显式用 ROS 模式重跑图上路线，并在同一执行窗口确认 wheel raw L/R 非零。
