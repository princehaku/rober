# PC MJPEG 画面状态所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlCameraMjpegStatusResponse` 新增 `preview_status`、`preview_plain_hint`、`preview_next_action`。
- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 只读派生共享预览状态：已有缓存帧为 `streaming`，相机源首帧失败为 `source_first_frame_failed`，无人观看为 `idle_not_started`，有客户端等待首帧为 `waiting_for_first_frame`。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐 MJPEG status 合同和 fixture，锁定 status 查询不会打开 `/api/camera/mjpeg` 上游。
- `docs/product/pc_tools_workstation.md`：同步说明 MJPEG status 顶层可读画面状态。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files  2 passed (2)`
  - `Tests  365 passed (365)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - 仍有既有 Vite chunk size warning：`dist/assets/index-*.js` 大于 500 kB；本轮未扩大处理范围。
- 通过：重启 7001 后读取 `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status`
  - `proxy_status=status_loaded`
  - `preview_status=source_first_frame_failed`
  - `preview_plain_hint=不是页面独占：USB Composite Device: DV20 USB  (usb-5310000.usb-1) 当前没人占用，但 UVC 设备没有输出视频帧；检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测。`
  - `preview_next_action=check_usb_camera_input_power_or_known_good_uvc`
  - `robot_control_executed=false`
  - `safe_to_control=false`
  - `primary_actions_enabled=false`
- 通过：读取 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `camera.status=source_first_frame_failed`
  - `camera.shared_failure=camera_source_first_frame_failed`
  - `camera.diag=uvc_no_frame_not_exclusive`
  - `map.path=18`
  - `map.robot_pose=map_pose_observed`
  - `keyboard.status=start_ready`

## 剩余风险

- 本轮只修正 PC 只读画面状态合同，不修复真实 DV20/UVC 无首帧；真实可见图传仍需现场检查 USB、摄像头输入/供电或换 known-good UVC 复测。
