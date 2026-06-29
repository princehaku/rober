# PC base/Nav2 status 直连只读代理

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增固定只读 `GET /api/robot-control/base/status`，转发上车 `/api/base/status`，直出 `base_command_mode`、`nav2_base_command_mode`、`wheel_feedback_lr_nonzero_proven`、`motion_signal_observed` 和白话下一步。
  - 新增固定只读 `GET /api/robot-control/nav2/status`，转发上车 `/api/nav2/status`，直出 `path_generated`、`path_point_count`、`planner_server_active`、`controller_server_active` 和白话下一步。
  - 两个接口都固定 fail-closed：`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 新增 `RobotControlReadOnlyStatusResponse` 共享合同，约束两个直连状态代理的返回字段。
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录 PC base/Nav2 status 直连只读代理边界和现场用途。

## 验证结果

- `npm run build`：通过。
- `npm test -- App.test.ts`：通过，`218 passed`。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，监听进程为 Node。
- live `curl http://127.0.0.1:7001/api/robot-control/base/status`：
  - `proxy_status=status_loaded`
  - `base_command_mode=ros`
  - `nav2_base_command_mode=ros`
  - `wheel_feedback_lr_nonzero_proven=false`
  - `motion_signal_observed=false`
  - `sends_motion_commands=false`
- live `curl http://127.0.0.1:7001/api/robot-control/nav2/status`：
  - `proxy_status=status_loaded`
  - `base_command_mode=ros`
  - `nav2_base_command_mode=ros`
  - `nav2_goal_execute_default_base_command_mode=ros`
  - `lifecycle_running=false`
  - `lifecycle_state=stopped`
  - `planner_server_active=true`
  - `controller_server_active=false`
  - `path_generated=true`
  - `path_point_count=18`
  - `sends_motion_commands=false`

## 剩余风险

- 本轮只补 PC 直连诊断入口，未发送真实 manual、keyboard、free-roam 或 Nav2 goal。
- 当前 live 事实仍显示：摄像头无首帧、雷达未运行、Nav2 controller/lifecycle 未 active、wheel raw L/R 尚未非零。
- 真实“自动驾驶能动”仍需要现场安全确认后启动/恢复 Nav2 runtime 并重跑图上路线，读取同窗口 wheel raw L/R。
