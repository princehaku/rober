# Camera Shared Preview Everyone Join Aliases

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/camera/mjpeg/status` 新增共享预览短字段：`shared_preview_everyone_can_join`、`shared_preview_current_frame_visible`、`shared_preview_gap_plain`、`shared_preview_readback_only`、`shared_preview_starts_camera_exclusive_capture`、`shared_preview_sends_motion`。
  - 字段只描述 PC Node 共享 MJPEG relay：同一小车地址单上游、多页面可加入、不独占摄像头、不发车；当前无帧时仍如实提示相机源未出帧。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary 顶层和 `live_closure_summary` 新增同源 `camera_shared_preview_*` / `live_wysiwyg_camera_shared_preview_*` 短字段。
  - 当前实机读到 USB 12M full-speed 且无首帧时，`camera_shared_preview_gap_plain` 明确“共享入口可加入但当前相机源未出首帧，请换高速USB后复测”。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-live-closure-summary` 和 `plain-live-camera-recovery-readback` 暴露新增 DOM 字段。
  - 画面复测短句改为直接消费 `live_wysiwyg_camera_shared_preview_gap_plain`，避免用户把共享入口误解为画面已经 WYSIWYG。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 summary、live closure 和 MJPEG status TypeScript 合同。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补 summary、catalog 和 DOM 回归，覆盖多页面可加入、当前帧是否可见、只读、非独占、不发车字段。
- `docs/product/pc_tools_workstation.md`
  - 同步共享相机预览短合同和 WYSIWYG 边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`
  - `Test Files 3 passed (3)`，`Tests 428 passed (428)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功，仅保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`git diff --check`
- 通过：PC `0.0.0.0:7001` live smoke
  - 服务 PID `4419` 监听 `*:7001`。
  - `GET /api/robot-control/summary` 返回 `camera_shared_preview_everyone_can_join=true`、`camera_shared_preview_current_frame_visible=false`、`camera_shared_preview_readback_only=true`、`camera_shared_preview_starts_camera_exclusive_capture=false`、`camera_shared_preview_sends_motion=false`。
  - `GET /api/robot-control/camera/mjpeg/status` 返回 `shared_preview_everyone_can_join=true`、`shared_preview_current_frame_visible=false`、`shared_preview_readback_only=true`、`shared_preview_starts_camera_exclusive_capture=false`、`shared_preview_sends_motion=false`、`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`camera_usb_speed=12M`。

## 剩余风险

- 当前只证明 PC 共享预览 relay 是单上游、多页面可加入、非独占、只读；没有证明真实相机已恢复出帧。
- live 当前仍显示 `objective_audit_missing_objective_ids=["motion","wysiwyg","mapping"]`，其中相机 `current_frame_visible=false` 继续阻塞 WYSIWYG 和建图启动。
- 真实恢复还需要现场换高速 USB 口/线或带供电 Hub 后复测首帧；本轮没有发送 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
