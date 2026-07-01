# Keyboard Readback Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `keyboard_readback_endpoints` 和 `keyboard_required_success_markers` 顶层 summary alias。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：`keyboard_readback_endpoints` 复用 `hold_keyboard` runbook 的 acceptance endpoints；`keyboard_required_success_markers` 复用该 runbook 的 missing evidence。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-closure-summary` DOM 暴露 `data-keyboard-readback-endpoints` 和 `data-keyboard-required-success-markers`。
- 同步更新 `App.test.ts`、`robotControlSummary.test.ts`、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run catalog.test.ts App.test.ts robotControlSummary.test.ts`：3 个测试文件通过，427 个用例通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；保留既有 Vite chunk size warning。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `8603`。
- 真实 summary 只读 smoke 返回 `keyboard_ready=true`、`keyboard_continuous_motion_verified=false`、`keyboard_readback_endpoints=[/api/robot-control/base/feedback-samples,/api/robot-control/summary]`、`keyboard_required_success_markers=[same_hold_window_wheel_lr_nonzero,stop_after_release]`、`keyboard_post_hold_readback_endpoints=[/api/robot-control/base/feedback-samples,/api/robot-control/summary]`。
- 同一 smoke 确认 `trip_execution_readback_endpoints` 和 `free_move_readback_endpoints` 仍可读，`live_wysiwyg_missing_surface_ids=[camera]`、`radar_overlay_wysiwyg_complete=true`、`mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮只做 GET-only 运行态 smoke，未发任何运动/control POST，未执行键盘按住、Nav2、自由移动、建图或 delivery complete。
- 真实 motion 目标仍缺安全确认后的完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、PC 键盘连续手控和自由移动运行读回。
- 当前 WYSIWYG 和建图启动仍只剩相机首帧硬件缺口。
