# PC camera MJPEG status source diagnosis

## Sprint Type

sprint_type: micro

## Actual Changes

- `pc-tools/workstation/src/server/index.ts`
  - `GET /api/robot-control/camera/mjpeg/status` now keeps the relay's latest MJPEG failure as the shared-preview failure reason while independently filling `source_diagnosis_*` from the read-only `/api/camera/health` check.
  - This prevents a stale relay HTTP 502/503 failure from hiding the real camera-source diagnosis, such as `uvc_no_frame_not_exclusive`.
- `pc-tools/workstation/test/catalog.test.ts`
  - Extended the MJPEG status regression to cover the live-shaped case: relay has a recent `camera_mjpeg_http_status_503` failure and health reports `uvc_no_frame_not_exclusive`.
- `docs/product/pc_tools_workstation.md`
  - Documented the status API merge contract and its no-motion/no-stream side effects boundary.

## Verification

- `npm test -- --run test/catalog.test.ts -t "camera MJPEG status"`: passed, 4 tests.
- `npm test -- --run`: passed, 2 files / 298 tests.
- `npm run build`: passed. Vite still reports the pre-existing chunk-size warning.
- `npm run lint`: passed.
- `git diff --check`: passed.
- 7001 live status smoke:
  - `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`
  - Returned `source_diagnosis_status=uvc_no_frame_not_exclusive`.
  - Returned `source_diagnosis_not_exclusive=true`.
  - Returned plain hint: `不是页面独占：USB Composite Device: DV20 USB ... 当前没人占用，但 UVC 设备没有输出视频帧...`
  - Returned `robot_control_executed=false`.
  - 7001 stayed bound to `0.0.0.0:7001` by node PID `26954`.

## Remaining Risks

- This sprint does not make the camera produce frames; it makes the status API accurately expose that the current blocker is UVC no-frame, not browser/page exclusivity.
- No real camera stream, WebRTC offer, Nav2 execution, manual control, free-roam start, stop, delivery, or `/cmd_vel` command was triggered.
- The historical dirty JSON artifacts under `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/` were not touched or staged.
