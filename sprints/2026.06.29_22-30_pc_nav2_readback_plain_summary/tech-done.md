# PC Nav2 readback plain summary

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 的 `readback_summary.nav2` 新增 `execution_status_plain` 和 `next_action_plain`。
- Nav2 只读区块现在可以直接解释完整路线执行证明到哪一步：
  - 已证明路线执行和轮速 L/R 时，提示继续送达确认。
  - 路线结果成功但执行窗口轮速 L/R 未非零时，提示下一步勾安全确认后按下次模式重跑图上路线，并同窗口确认轮速 L/R 非零。
  - 路线未准备时，提示先准备图上路线并刷新地图画面。
- 前端 fixture、合同测试、`pc-tools/README.md` 和 `docs/product/pc_free_roam_mapping_design.md` 已同步更新。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- catalog.test.ts -t "summary"`
  - `Test Files 1 passed (1)`
  - `Tests 44 passed | 114 skipped (158)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files 2 passed (2)`
  - `Tests 373 passed (373)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
  - Vite 仍有既有 chunk size warning，但 build 成功。
- 通过：本机 7001 只读 summary 验证。
  - 7001 监听为 workstation 的 `tsx src/server/index.ts` / `node` 进程，未触碰 Clash。
  - `curl http://127.0.0.1:7001/api/robot-control/summary` 返回：
    `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`、
    `execution_status_plain=上次路线结果成功，但执行窗口轮速 L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或控制服务。`、
    `next_action_plain=勾选行程前安全确认后用 ROS 模式重跑图上路线，并在同窗口确认轮速 L/R 非零。`、
    `goal_execution_status=goal_succeeded`、
    `goal_execution_proven=false`、
    `goal_execution_base_feedback_lr_nonzero_proven=false`、
    `next_execution_base_command_mode=ros`、
    `goal_execution_base_feedback_latest_raw_left=0`、
    `goal_execution_base_feedback_latest_raw_right=0`、
    `navigate_goal_enabled=false`、`robot_control_executed=false`、`safe_to_control=false`。

## 剩余风险

- 本轮只补只读 readback summary 文案，不执行 Nav2 goal、不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 未获得本轮现场安全确认前，不做真实 Nav2 重跑和 wheel raw L/R HIL 验证。
