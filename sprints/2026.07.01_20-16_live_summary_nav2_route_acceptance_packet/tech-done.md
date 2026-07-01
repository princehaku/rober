# Live Summary Nav2 Route Acceptance Packet

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `RobotControlNav2RouteAcceptancePacket`，并挂到 `RobotControlSummaryResponse` 与 `RobotControlLiveSummaryResponse`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：复用 `live_closure_summary` 与 `run_nav2_route` runbook，生成 `nav2_route_acceptance_packet`，集中暴露完整 Nav2 行程执行、最小安全确认、同窗口 wheel L/R、delivery success 和只读读回边界。
- `pc-tools/workstation/src/server/index.ts`：`/api/robot-control/live-summary` 透出同源 `nav2_route_acceptance_packet`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`：锁定 summary/live-summary 同源字段、最小预检 safety-only、delivery success 缺口和 readback 不发车边界。
- `docs/product/pc_tools_workstation.md`：同步说明该包只读，不自动执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`，2 files / 190 tests。
- 通过：`npm --prefix pc-tools/workstation run lint`。
- 通过：`npm --prefix pc-tools/workstation run build`；Vite 仅提示既有 chunk size warning。
- 通过：`npm --prefix pc-tools/workstation test -- --run`，3 files / 422 tests。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，PID `13724`；`GET /` 和 `GET /map` 均返回 200。
- 通过：只读 `GET /api/robot-control/live-summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787` 返回 `nav2_route_acceptance_packet.action_id=run_nav2_route`、`start_endpoint=/api/robot-control/nav2/goal/execute`、`requires_safety_confirm=true`、`minimal_precheck_safety_only=true`、`camera_preflight_required=false`、`radar_preflight_required=false`、`route_wysiwyg_preflight_required=false`、`same_window_wheel_lr_nonzero=false`、`delivery_success=false`、`readback_sends_motion=false`、`readback_starts_nav2=false`、`readback_stops_motion=false`。

## 剩余风险

- 当前改动只补 PC/API 只读验收契约，不代表真实小车已经完成 Nav2 行程、同窗口 wheel L/R 非零或 delivery success。
- 本轮没有发送发车、Nav2 execute、manual、keyboard、free-roam、建图、delivery complete、stop 或 `/cmd_vel`；真实行程执行仍需现场安全确认后单独验收。
