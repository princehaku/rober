# Summary 顶层相机 WYSIWYG 恢复 Alias

## sprint_type

micro

## 实际改动

- 在 `GET /api/robot-control/summary` 顶层补齐相机 WYSIWYG 恢复 alias，包括：
  - `live_wysiwyg_camera_visible`
  - `camera_hardware_action_required`
  - `camera_hardware_action_label`
  - `camera_usb_full_speed_detected`
  - `camera_source_diagnosis_status`
  - `camera_source_diagnosis_not_exclusive`
  - `camera_recovery_next_action_plain`
  - `camera_recovery_sends_motion`
  - `fixed_camera_probe_endpoint`
  - `fixed_camera_mjpeg_status_endpoint`
  - `live_wysiwyg_camera_shared_preview_client_count`
  - `live_wysiwyg_camera_shared_preview_upstream_active`
  - `live_wysiwyg_camera_shared_preview_exclusive_camera_claim`
- 这些字段均与 `live_closure_summary` 同源，用于现场一条 `curl | jq` 判断“不是页面独占、是否 USB full-speed、是否需要换高速 USB 后复测”。
- 同步 TypeScript 合同、summary/catalog 测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run test/robotControlSummary.test.ts`：通过，9 passed。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 passed / 180 skipped。
- `npm test`：通过，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：新 Node PID `69773` 监听 `*:7001`。
- 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：顶层返回 `live_wysiwyg_camera_visible=false`、`camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`、`camera_usb_full_speed_detected=true`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`camera_recovery_sends_motion=false`、`fixed_camera_probe_endpoint=/api/robot-control/camera/first-frame/probe`、`fixed_camera_mjpeg_status_endpoint=/api/robot-control/camera/mjpeg/status`、`live_wysiwyg_camera_shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮只补只读 alias；不执行相机 probe、Nav2、键盘、自由移动、建图、送达或 stop，不验证真实画面恢复。
