# PC Nav2 下一次复验模式白话化

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/nav2/goal/execution/latest` 新增 `goal_execution_next_mode_plain` 和 `goal_execution_mode_rerun_plain`。
  - latest 只读响应会把“旧 PWM 轮速未闭合后切 ROS”“ROS 仍未闭合后切 SPEED”写成普通用户可读文案。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `readback_summary.nav2` 同步新增同名字段，普通首屏和脚本不用再手动拼 `goal_execution_base_command_mode`、`next_execution_base_command_mode` 和 wheel 状态。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通行程卡“执行模式”行直接展示模式切换复验原因。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 更新 PC API 合同类型。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 增加 PWM→ROS、ROS→SPEED 和首屏行程卡展示断言。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录只读合同、安全边界和 Objective 3 进展。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "Nav2|nav2|wheel|rerun|SPEED|ROS"`，35 passed / 133 skipped。
- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "stopped Nav2 stack"`，1 passed / 217 skipped。
- 通过：`npm --prefix pc-tools/workstation test`，2 个测试文件、386 个用例通过。
- 通过：`npm --prefix pc-tools/workstation run build`，TypeScript app/server 编译和 Vite build 通过；仅保留既有 chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，`lsof` 显示 `node` 监听 `*:7001`，`GET /api/health` 返回 `pc_only_readonly_workstation`。
- 通过：只读 `GET /api/robot-control/summary` live 返回 `next_execution_base_command_mode=ros`、
  `goal_execution_next_mode_plain=下次将用 ROS 模式重跑图上路线。`、
  `goal_execution_mode_rerun_plain=上次 PWM 模式路线返回成功但轮速 L/R 仍未非零，本次切到 ROS 模式复验控制链。`。

## 剩余风险

- 本轮只补只读 summary/latest/UI 展示和测试合同，不执行 Nav2、不启动 runtime、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实完整路线闭环仍需要现场勾选安全确认后按 PC 提示的模式重跑，并在同一执行窗口读到 wheel L/R 非零。
