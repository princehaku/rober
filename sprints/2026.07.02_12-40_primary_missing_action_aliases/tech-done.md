# 主缺口动作 alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增 `field_acceptance_primary_missing_action_*` 短 alias，覆盖 action label、start/stop endpoint、acceptance endpoints、是否发车、是否需要安全确认。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从当前 primary missing evidence 的 `action_id` 反查 `fieldAcceptanceSteps`，把对应动作的执行和验收合同抬到 summary 顶层。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补回归断言，确认当前 `same_window_wheel_lr_nonzero` 缺口直接指向 `/api/robot-control/nav2/goal/execute`，并保留执行后地图、Nav2 latest、wheel samples、delivery latest 和 summary 读回链路。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明这些字段只减少现场 `curl | jq` 取数路径，不自动勾安全确认、不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交送达、不发送 stop 或 `/cmd_vel`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 条测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `41830`。
- 真实只读 summary smoke：`status=needs_wheel_rerun`，`field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`，`field_acceptance_primary_missing_action_id=run_nav2_route`，`field_acceptance_primary_missing_action_start_endpoint=/api/robot-control/nav2/goal/execute`，`field_acceptance_primary_missing_action_stop_endpoint=/api/robot-control/base/stop`，`field_acceptance_primary_missing_action_acceptance_endpoints=[/api/robot-control/map/preview,/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/delivery/latest,/api/robot-control/summary]`，`field_acceptance_primary_missing_action_sends_motion=true`，`field_acceptance_primary_missing_action_requires_safety_confirm=true`，`field_acceptance_primary_readback_endpoint=/api/robot-control/base/feedback-samples`。
- 收尾 summary 一度显示 `radar_overlay_status=not_current`、`radar_overlay_wysiwyg_complete=false`；按 summary 声明的 no-motion primary action 执行 `/api/robot-control/radar/scan-proof/refresh -> /api/robot-control/radar/status -> /api/robot-control/map/preview -> /api/robot-control/summary` 后，真实 summary 恢复为 `live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`、`radar_map_points_visible=true`。该链路 `field_acceptance_primary_no_motion_readback_sends_motion=false`。

## 剩余风险

- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；仅在收尾使用 no-motion 雷达贴图复验链路恢复 WYSIWYG。
- `motion` 目标仍缺现场安全确认后的 Nav2 同窗口 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动 latest 运行读数。
- `wysiwyg` / `mapping` 仍只剩相机首帧硬件缺口；当前诊断仍指向 USB 12M full-speed，需要现场换高速 USB 口/线或带供电 Hub 后再复测。
