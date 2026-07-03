# PC Camera Readback Hardware Action

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：给 `readback_summary.camera` 同步派生 `camera_hardware_action_required`、`camera_hardware_action_label`、`camera_reprobe_after_hardware_action_required`。当共享 MJPEG / health 已证明 `uvc_no_frame_not_exclusive`、`uvc_transport_error_not_exclusive` 或 USB full-speed 且当前没有画面时，camera readback 层直接给出设备处理动作；画面已可见时仍回到“复测相机首帧”。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐上述 camera readback 字段合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：高级诊断显示 camera readback 的硬件动作字段，普通首屏文案不新增工程字段。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：覆盖 `uvc_no_frame_not_exclusive` 和 `uvc_full_speed_usb_not_exclusive` 两条 readback 硬件动作路径。
- `docs/product/pc_tools_workstation.md`：同步记录 summary camera readback 新字段和 no-motion 边界。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，13 passed。
- `npm test -- App.test.ts`：通过，239 passed。
- `npm test -- catalog.test.ts`：通过，188 passed。
- `npm run build`：通过，Vite 仍提示既有 bundle size warning。
- `git diff --check`：通过。
- PC 7001 重启：通过，新 PID `39186` 监听 `*:7001`。
- live summary smoke：通过，`readback_summary.camera.camera_hardware_action_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_reprobe_after_hardware_action_required=true`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_usage_owner_count=0`、`shared_preview_exclusive_camera_claim=false`、`free_move_without_camera_allowed=true`。

## 剩余风险

- 本轮只修 PC 端只读诊断合同，不会让当前 DV20 UVC 设备吐出真实首帧。最新现场证据仍是共享 MJPEG 可多人接入但返回 `502/first_frame_total_timeout`，`exclusive_camera_claim=false`、`owner_count=0`、USB `480M`，更像摄像头输入/供电/线缆或设备自身出帧问题。
- `wheel raw L/R` 非零和 `delivery_success` 仍未完成；自动驾驶路线曾有 `nav2_goal_succeeded=true`，但完整路线执行闭环还缺同窗口 wheel raw L/R 非零和送达确认。
