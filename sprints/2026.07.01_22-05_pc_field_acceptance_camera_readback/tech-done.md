# 现场验收卡画面读回

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：在现场验收卡 `plain-field-acceptance-wysiwyg` 内新增 `plain-field-acceptance-camera-proof`。当当前所见缺口包含画面时，直接显示相机首帧/诊断/USB/共享预览/建图阻塞/自由移动不阻塞/固定复测端点。
- `pc-tools/workstation/test/App.test.ts`：补充默认画面缺口、USB 12M full-speed 和 camera-only 场景的 DOM 合同断言。
- `docs/product/pc_tools_workstation.md`：同步现场验收卡画面读回合同。

## 验证结果

- `npm --prefix pc-tools/workstation test -- --run test/App.test.ts`：通过，233 个用例通过。
- `npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`：通过，190 个用例通过。
- `git diff --check`：通过。
- `npm --prefix pc-tools/workstation run lint`：通过。
- `npm --prefix pc-tools/workstation run build`：通过；仅保留既有 Vite chunk size 警告。
- `npm --prefix pc-tools/workstation test -- --run`：通过，423 个用例通过。
- `GET /api/robot-control/camera/mjpeg/status` 只读 smoke：`status=waiting_for_first_frame`、`shared_preview_client_count=1`、`shared_preview_upstream_active=true`、`shared_preview_exclusive_camera_claim=false`、`camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`camera_recovery_sends_motion=false`、`camera_recovery_starts_map_runtime=false`、`robot_control_executed=false`。
- `GET /api/robot-control/summary` 只读 smoke：`field_acceptance_wysiwyg_missing_surface_ids=[camera]`、`camera_current_visible=false`、`camera_first_frame_ready=false`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`mapping_start_missing_reasons=[camera_first_frame]`、雷达贴图仍 `loaded` 且不阻塞 WYSIWYG。
- PC Node 已重启到 `0.0.0.0:7001`，监听 PID `74053`；`GET /` 返回 200，`GET /map` 返回 200。重启后 summary 仍读回 `field_acceptance_wysiwyg_missing_surface_ids=[camera]`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`、`camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`、`radar_overlay_status=loaded`。

## 剩余风险

- PC 端已经把画面缺口、USB 12M full-speed 和共享预览非独占状态放到现场验收卡顶层；但相机真实首帧仍未出现，需要现场换高速 USB 口/线或带供电 USB Hub 后再复测。完整 Nav2 同窗口 wheel L/R、delivery success、键盘按住轮速和自由移动 latest 仍需要现场安全确认后的真实运动验证。
