# 主缺口最小预检 alias

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlSummaryResponse` 新增 `field_acceptance_primary_missing_action_minimal_precheck_safety_only`、`field_acceptance_primary_missing_action_camera_preflight_required`、`field_acceptance_primary_missing_action_radar_preflight_required`、`field_acceptance_primary_missing_action_operator_report_preflight_required` 和 `field_acceptance_primary_missing_action_route_wysiwyg_preflight_required`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 primary missing evidence 对应的 `fieldAcceptanceSafetyConfirmReadyActions` 同源取最小预检字段，避免现场脚本需要再解析安全确认 action 列表。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：补回归断言，确认当前 `same_window_wheel_lr_nonzero` 的 Nav2 复验只要求现场安全确认，camera/radar/operator report/route WYSIWYG 都不是额外 preflight。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明这些 alias 只解释发车前置条件，不自动勾安全确认、不启动 Nav2/manual/keyboard/free-roam/建图/雷达 lifecycle，不提交送达、不发送 stop 或 `/cmd_vel`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 条测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `51734`。
- 真实只读 summary smoke：`status=needs_wheel_rerun`，`field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`，`field_acceptance_primary_missing_action_start_endpoint=/api/robot-control/nav2/goal/execute`，`field_acceptance_primary_missing_action_requires_safety_confirm=true`，`field_acceptance_primary_missing_action_minimal_precheck_safety_only=true`，`field_acceptance_primary_missing_action_camera_preflight_required=false`，`field_acceptance_primary_missing_action_radar_preflight_required=false`，`field_acceptance_primary_missing_action_operator_report_preflight_required=false`，`field_acceptance_primary_missing_action_route_wysiwyg_preflight_required=false`。收尾 summary 同时保持 `live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_wysiwyg_complete=true`。

## 剩余风险

- 本轮只读 summary smoke，没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `motion` 目标仍缺现场安全确认后的 Nav2 同窗口 wheel L/R 非零、delivery success、PC 键盘连续手控和自由移动 latest 运行读数。
- `wysiwyg` / `mapping` 仍只剩相机首帧硬件缺口；当前诊断仍指向 USB 12M full-speed，需要现场换高速 USB 口/线或带供电 Hub 后再复测。
