# Summary 顶层完整 Nav2 路线 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增完整 Nav2 路线闭环 alias，全部与 `live_closure_summary` 同源：
  - `primary_action_id`
  - `route_ready_on_map`
  - `nav2_route_ready`
  - `nav2_goal_succeeded`
  - `nav2_goal_execution_proven`
  - `wheel_lr_nonzero_proven`
  - `needs_same_window_wheel_rerun`
  - `route_delivery_success`
  - `delivery_success_required`
  - `delivery_next_action_plain`
  - `fixed_delivery_latest_endpoint`
  - `fixed_delivery_complete_endpoint`
  - `delivery_latest_readback_only=true`
  - `delivery_complete_sends_motion=false`
  - `wheel_rerun_ready_for_safety_confirm`
  - `wheel_rerun_start_endpoint=/api/robot-control/nav2/goal/execute`
  - `wheel_rerun_start_sends_motion=true`
  - `wheel_rerun_requires_safety_confirm`
  - `wheel_rerun_readback_endpoints`
  - `wheel_rerun_required_success_markers`
  - `wheel_rerun_current_gap_plain`
  - `wheel_rerun_no_extra_precheck_plain`
- 保留 `summary.delivery_success` 作为全局 fail-closed `ProofFlags` 字段；路线送达闭环使用 `route_delivery_success`，避免脚本把只读软件证明误读为真实送达完成。
- 同步更新 `RobotControlSummaryResponse` contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `86609`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `primary_action_id=run_nav2_route`
  - `route_ready_on_map=true`
  - `nav2_route_ready=true`
  - `nav2_goal_succeeded=true`
  - `nav2_goal_execution_proven=true`
  - `wheel_lr_nonzero_proven=false`
  - `needs_same_window_wheel_rerun=true`
  - `route_delivery_success=false`
  - `delivery_success_required=true`
  - `delivery_latest_readback_only=true`
  - `delivery_complete_sends_motion=false`
  - `wheel_rerun_ready_for_safety_confirm=true`
  - `wheel_rerun_start_endpoint=/api/robot-control/nav2/goal/execute`
  - `wheel_rerun_start_sends_motion=true`
  - `wheel_rerun_requires_safety_confirm=true`
  - `wheel_rerun_readback_endpoints=[map/preview, nav2 latest, base feedback, delivery latest, summary]`
  - `wheel_rerun_required_success_markers=[map_route_visible, nav2_goal_succeeded, same_window_wheel_lr_nonzero, delivery_success]`

## 剩余风险

- 本轮只修 summary 顶层读数，不执行路线重跑。
- `wheel_rerun_start_sends_motion=true` 明确表示执行 endpoint 会发车，仍必须先由现场 operator 勾安全确认。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
