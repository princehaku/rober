# 2026.07.02 27-25 Current Trip Execution Pack

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `current_trip_execution_pack_*` summary 合同，专门表达完整 Nav2 图上行程执行和验收读回。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从既有 `nav2_route_acceptance_packet` 生成当前完整行程包，压平路线 ready、Nav2 到点、同窗口 wheel L/R、送达确认、缺口、端点和安全边界。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏新增 `plain-current-trip-execution-pack`，让现场一眼看到完整行程当前能否复验、执行后读哪些端点、缺哪些证据。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 summary 字段和 DOM data 属性，锁定执行/读回边界。
- `docs/product/pc_tools_workstation.md`：同步说明 `current_trip_execution_pack_*` 的产品边界。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功；Vite 仍提示既有 chunk size warning。
- `npm run lint`：通过。
- `git diff --check`：通过。
- 重启 `0.0.0.0:7001` 后只读检查 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：通过，返回 `current_trip_execution_pack_status=ready_for_safety_confirm`、`current_trip_execution_pack_missing_evidence=same_window_wheel_lr_nonzero,delivery_success`、`current_trip_execution_pack_route_ready_on_map=true`、`current_trip_execution_pack_nav2_goal_succeeded=true`、`current_trip_execution_pack_same_window_wheel_lr_nonzero=false`、`current_trip_execution_pack_delivery_success=false`、`current_trip_execution_pack_sends_motion_when_executed=true`、`current_trip_execution_pack_starts_nav2_when_executed=true`、`current_trip_execution_pack_sends_motion_when_clicked=false`、`current_trip_execution_pack_readback_sends_motion=false`。

## 剩余风险

- 本轮只补完整行程执行验收包，不自动执行 Nav2 goal，不发送底盘命令，不提交送达确认。
- 真实同窗口轮速 L/R 非零和 delivery success 仍需要现场勾安全确认后重跑图上路线并复验。
