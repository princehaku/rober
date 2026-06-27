# Camera Health Ready WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 收紧 camera health 顶层 `status`：只有同一 source 已经通过 `last_successful_frame` 读到真实首帧时才返回 `ready`。
  - 仅选中 `/dev/video1` 但还没有读到首帧时返回 `source_not_probed`，继续保留 `source_readiness=source_selected_not_probed`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 更新 health 选择设备但未读帧的断言，防止以后又把“设备存在”说成“画面 ready”。
- `docs/vision/board_camera_publisher.md`
  - 记录本轮真实上位机只读复核：`lsof` 无长期占用，`v4l2-ctl` MJPG/YUYV 输出 0 字节，OpenCV 多模式 `opened=false`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - PC summary 在固定首帧探针返回 `backend_no_frame_observed` 且 source usage 为空闲时，合成 `uvc_no_frame_not_exclusive` 诊断，避免高级字段仍停留在“还没读过首帧”。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 backend smoke 无帧后的 summary 诊断断言。

## 验证结果

- 已通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`，`Ran 23 tests ... OK`。
- 已通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "camera first-frame probe can request backend smoke"`，`Tests 1 passed | 125 skipped (126)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 291 passed (291)`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。
- 上车部署与 live 验证：
  - 已同步 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 并通过远端 `py_compile`。
  - 发现旧 camera 进程 PID `240460` 占用 `0.0.0.0:8088`，导致 systemd 新服务 `Address already in use`；已只清理该旧 camera 进程并由 `trashbot-local-webrtc-camera.service` 接管。
  - 当前 8088 由 systemd PID `254225` 监听，`trashbot-local-webrtc-camera.service=active`。
  - 重启后 `GET /api/camera/health` 返回 `status=source_not_probed`、`source_readiness=source_selected_not_probed`、`source_usage.status=not_in_use`，不再把仅选中 `/dev/video1` 说成 ready。
  - PC 7001 固定首帧探针返回 `probe_failed`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`open_ok=true`、`read_ok=false`、`backend_smoke_status=backend_no_frame_observed`、`backend_frame_observed=false`、`backend_attempts=4`。
  - 探针后 PC 7001 summary 返回 `status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_diagnosis_plain_hint=不是页面独占：USB Composite Device: DV20 USB 当前没人占用，但 OpenCV/V4L2 后端也没有取到视频帧。`。
  - 本机 PC Node 继续监听 `*:7001`。

## 剩余风险

- 本轮修的是 camera health 所见即所得口径，不修复 DV20 UVC 真实无帧。
- 真实多人实时预览仍依赖摄像头硬件能输出首帧；当前建议继续检查 USB、摄像头输入/供电或换 known-good UVC 复测。
