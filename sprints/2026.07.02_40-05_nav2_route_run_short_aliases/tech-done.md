# Nav2 Route Run Short Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- time: 2026-07-02 19:05 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `nav2_route_run_*` 顶层短字段，复用 `current_trip_execution_pack_*` 和 `nav2_route_acceptance_packet`，用于现场一眼读取完整 Nav2 图上行程的执行、复验和安全边界。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 的 `nav2_route_run_*` 可选字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC `plain-current-trip-execution-pack` 同步暴露 `data-nav2-route-run-*` DOM 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 summary 字段与 DOM 属性。
- `docs/product/pc_tools_workstation.md`：同步说明 Nav2 完整行程短别名、点击不发车、现场安全确认后执行，以及执行后只读复验顺序。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，1 个测试文件、10 个用例通过。
- 通过：`npm test -- test/App.test.ts`，1 个测试文件、237 个用例通过。
- 通过：`npm run build`，TypeScript 与 Vite build 成功；仅保留既有 Vite chunk size 警告。
- 通过：`git diff --check`，无空白错误。
- 通过：重启 PC workstation 到 `0.0.0.0:7001` 后只读调用 `GET /api/robot-control/summary`，读到
  `readback_only=true`、`robot_control_executed=false`、`nav2_route_run_status=ready_for_safety_confirm`、
  `nav2_route_run_requires_safety_confirm=true`、`nav2_route_run_sends_motion_when_clicked=false`、
  `nav2_route_run_sends_motion_when_executed=true`、`nav2_route_run_starts_nav2_when_clicked=false`、
  `nav2_route_run_starts_nav2_when_executed=true`。

## 剩余风险

- 当前改动只补 PC/API 可读合同与前端 DOM，不替代真实 Nav2 发车验收。
- 真车完整闭环仍需要现场勾安全确认后执行路线，并复验同窗口 wheel raw L/R 非零与 delivery success。
