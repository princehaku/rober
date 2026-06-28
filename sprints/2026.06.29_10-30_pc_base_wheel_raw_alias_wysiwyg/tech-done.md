# 2026.06.29 10:30 PC base wheel raw alias WYSIWYG

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `readback_summary.base` 增加短字段 `wheel_raw_left/right` 与 `wheel_left_speed/right_speed`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：用现有保守底盘反馈摘要同步填充短字段，保证它们与 `wheel_feedback_latest_raw_left/right`、`wheel_feedback_latest_left_speed/right_speed` 同口径。
- `pc-tools/workstation/test/catalog.test.ts`：补充 summary contract 断言，避免短字段缺失或误把 Nav2 execution artifact 当成当前 base raw L/R。
- `docs/product/pc_tools_workstation.md`：同步记录短字段语义和不触发运动控制的边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "wheel feedback|fresh base status"`，结果 `1 passed`、`153 skipped`。
- 通过：`npm --prefix pc-tools/workstation test`，结果 `2 passed`、`366 passed`。
- 通过：`npm --prefix pc-tools/workstation run build`，结果 `tsc` 和 `vite build` 成功；Vite 仅保留既有大 chunk warning。
- 通过：`git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/robotControlSummary.ts pc-tools/workstation/test/App.test.ts pc-tools/workstation/test/catalog.test.ts docs/product/pc_tools_workstation.md sprints/2026.06.29_10-30_pc_base_wheel_raw_alias_wysiwyg/tech-done.md`，无 whitespace 问题。
- 通过：重启 PC Node 到 `0.0.0.0:7001` 后只读请求 `GET /api/robot-control/summary`；返回 `readback_summary.base.wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_left_speed=0`、`wheel_right_speed=0`、`wheel_feedback_lr_nonzero_proven=false`、`safe_command_boundary.nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`、`robot_control_executed=false`。

## 剩余风险

- 本轮只修 PC summary 的 wheel raw L/R 一眼读法，不执行发车，也不证明当前轮速非零。
- 未获得本轮现场安全确认，因此不执行 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
