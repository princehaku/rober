# PC Nav2 Managed Runtime Blocker Cleanup

## sprint_type

micro

## 实际改动

- 修正 `pc-tools/workstation/src/server/robotControlSummary.ts`：当图上路线已 ready，且执行端会托管启动自动驾驶 runtime 时，`nav2_lifecycle_not_running` 只保留在 Nav2 只读诊断里，不再混入 `safe_command_boundary.nav2_goal_blockers`。
- 扩展 `pc-tools/workstation/test/catalog.test.ts` 的 PWM 成功但 wheel L/R=0/0 用例，覆盖现场形态：Nav2 lifecycle stopped、路线 ready、下一次 ROS 重跑且执行时自动启动 runtime。
- 同步更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，记录发车 blocker 与只读诊断的边界。

## 验证结果

- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "rerun ROS Nav2"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "nested nav2 status proof"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "IMU motion material"`，1 passed。
- Pass: `npm --prefix pc-tools/workstation test`，2 files passed，379 tests passed。
- Pass: `npm --prefix pc-tools/workstation run build`，TypeScript 与 Vite build 通过；Vite 仍提示既有 chunk size warning。
- Pass: PC API 已重启到 `0.0.0.0:7001`，监听 PID 64224。
- Pass: 只读 curl `http://127.0.0.1:7001/api/robot-control/summary` 返回 `robot_api_connection.status=readable`、`loaded_count=15`、`failed_count=0`、`readback_summary.nav2.current_blocker_reasons=nav2_lifecycle_not_running`、`safe_command_boundary.nav2_goal_ready=true`、`safe_command_boundary.nav2_goal_blockers=[]`。
- Pass: 只读 7071 诊断仍返回 `robot_api_port_7071_mismatch_use_8787` 作为首位 blocker，并保持 `safe_to_control=false`、`primary_actions_enabled=false`。

## 剩余风险

- 真实发车仍属于危险动作，需要现场安全确认后由用户触发；本轮只做只读 summary 修正，不调用 manual、Nav2 执行、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 现场仍显示上次路线成功但 wheel L/R=0/0，下一步是勾选行程前安全确认后用 ROS 模式重跑，并在同窗口复验 wheel L/R 非零。
