# PC Nav2 Latest Plain Execution Contract

sprint_type: micro

## 实际改动

- `GET /api/robot-control/nav2/goal/execution/latest` 顶层新增普通用户可读的只读字段：
  - `route_execution_readiness_plain`
  - `route_execution_precheck_plain`
  - `goal_execution_wheel_raw_lr_status_plain`
  - `goal_execution_wheel_raw_lr_next_action_plain`
- 当最近 Nav2 action 已成功但同窗口 `wheel raw L/R` 仍未非零时，latest endpoint 会明确提示“可重跑复验”“只需勾选行程前安全确认”“用 ROS 模式重跑图上路线”。
- 当最近完整路线已被 wheel raw L/R 证明时，latest endpoint 会明确提示下一步是送达确认，避免把 proof 字段留给脚本自行拼接。
- 同步更新 PC tools README 和产品文档，说明该合同只消费只读 latest artifact，不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2 latest execution proxy"`，结果 `Test Files 1 passed (1)`，`Tests 4 passed | 154 skipped (158)`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `Test Files 2 passed (2)`，`Tests 373 passed (373)`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 TypeScript、Vite 和 server TypeScript build 全部通过；Vite 仅保留既有 chunk size warning。
- 通过：本机 PC API 已重启到 `0.0.0.0:7001`，监听进程为 `node` PID `1164`。
- 通过：只读检查 `GET http://127.0.0.1:7001/api/robot-control/nav2/goal/execution/latest` 返回 `proxy_status=latest_loaded`、`robot_control_executed=false`，并返回：
  - `route_execution_readiness_plain=图上路线可重跑复验；上次路线 action 成功，但同窗口 wheel raw L/R=0/0 未非零。`
  - `route_execution_precheck_plain=只需勾选行程前安全确认；相机、雷达和 operator report 不作为额外发车前置；执行会用 ROS 模式跑图上路线。`
  - `goal_execution_wheel_raw_lr_status_plain=上次路线 action 成功，但执行窗口 wheel raw L/R=0/0 未非零；已看到 49 次非零底盘命令，IMU 姿态有变化。`
  - `goal_execution_wheel_raw_lr_next_action_plain=勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认 wheel raw L/R 非零。`

## 剩余风险

- 本轮只补 PC 端 latest 只读合同，不触发真实 Nav2 goal；真实小车能否自动驾驶移动仍需要 CEO 现场确认安全后再执行发车接口验证。
- 当前 live latest 的结论仍是“action 成功但同窗口 wheel raw L/R 未非零”，所以自动驾驶移动还没有完成真实 HIL 证明。
