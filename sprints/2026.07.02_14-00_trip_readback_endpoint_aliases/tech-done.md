# Trip Readback Endpoint Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：给 summary 顶层增加 `trip_execution_readback_endpoints` 和 `wheel_rerun_readback_endpoint` 短 alias。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`trip_execution_readback_endpoints` 直接复用 `nav2_route_acceptance_packet.readback_endpoints`；`wheel_rerun_readback_endpoint` 固定复用 `live_closure_summary.fixed_wheel_readback_endpoint=/api/robot-control/base/feedback-samples`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-closure-summary` 和 `plain-field-acceptance-packet` DOM 同步暴露完整行程读回链路，现场脚本不必解析嵌套 `nav2_route_acceptance_packet`。
- 同步更新 `App.test.ts`、`robotControlSummary.test.ts`、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `98030`。
- 真实 summary 只读 smoke 返回 `status=needs_wheel_rerun`，`trip_execution_ready=true`，`trip_execution_missing_evidence=[same_window_wheel_lr_nonzero,delivery_success]`，`trip_execution_readback_endpoints=[/api/robot-control/map/preview,/api/robot-control/nav2/goal/execution/latest,/api/robot-control/base/feedback-samples,/api/robot-control/delivery/latest,/api/robot-control/summary]`，`wheel_rerun_readback_endpoint=/api/robot-control/base/feedback-samples`，`wheel_rerun_readback_endpoints` 同完整行程读回链路。
- 真实 summary 同时保持 `field_acceptance_primary_missing_action_minimal_precheck_safety_only=true`、`live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_wysiwyg_complete=true`、`mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮只做 GET-only 运行态 smoke，未发任何运动/control POST，未执行 Nav2、键盘连续手控、自由移动、建图或 delivery complete。
- 真实 motion 目标仍缺安全确认后的完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动运行读回。
- 当前 WYSIWYG 和建图启动仍只剩相机首帧硬件缺口。
