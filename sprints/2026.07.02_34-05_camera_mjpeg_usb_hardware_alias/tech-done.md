# 相机 MJPEG USB 硬件动作短 alias

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/camera/mjpeg/status` 新增短 alias：
  - `usb_speed`
  - `usb_full_speed_detected`
  - `hardware_action_required`
  - `hardware_action_label`
- 这些字段与既有 `camera_usb_speed`、`camera_usb_full_speed_detected`、`camera_hardware_action_required`、`camera_hardware_action_label` 同源。
- 更新 catalog 测试和 PC 工作站产品文档，确保现场只查 direct camera status 时也能看到“USB 12M full-speed / 换高速USB后复测”。

## 验证结果

- 本轮修改前先读真实 `0.0.0.0:7001`：
  - summary 已显示 `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `camera_first_frame_failure_reason=first_frame_total_timeout`
  - direct `/camera/mjpeg/status` 已显示 `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`，但无前缀 `usb_full_speed_detected` / `hardware_action_label` 读到 `null`
- `npm test -- test/catalog.test.ts -t "workstation camera MJPEG status translates full-speed USB diagnosis"`：通过，`1 passed`。
- `npm test -- test/catalog.test.ts`：通过，`183 passed`。
- `npm run build`：通过，Vite 仅保留既有大 chunk 警告。
- `git diff --check`：通过。
- 已重启 PC 工作站到 `0.0.0.0:7001`。
- 修复后 live 读回 direct `/api/robot-control/camera/mjpeg/status`：
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `source_diagnosis_not_exclusive=true`
  - `camera_usb_speed=12M`
  - `camera_usb_full_speed_detected=true`
  - `camera_hardware_action_required=true`
  - `camera_hardware_action_label=换高速USB后复测`
  - `usb_speed=12M`
  - `usb_full_speed_detected=true`
  - `hardware_action_required=true`
  - `hardware_action_label=换高速USB后复测`
  - `first_frame_failure_reason=first_frame_total_timeout`
- 修复后 live summary 读回：
  - `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `current_camera_wysiwyg_pack_missing_evidence=["camera_first_frame"]`
  - `current_mapping_control_pack_status=blocked`
  - `current_mapping_control_pack_missing_evidence=["camera_first_frame"]`
  - `live_wysiwyg_missing_surface_ids=["camera"]`

## 剩余风险

- 该改动只修正直连 status 的只读 alias，不会让 USB 12M 摄像头本身出帧。
- 建图仍会被 `camera_first_frame` 阻塞，直到现场换高速 USB 口/线或带供电 USB Hub 后复测成功。
- 运动类目标仍需要现场安全确认后的 HIL 验证。
