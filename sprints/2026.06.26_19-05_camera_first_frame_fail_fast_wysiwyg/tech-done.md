# 2026-06-26 19:05 Camera 首帧 fail-fast WYSIWYG

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 新增 `SharedCameraCapture.read_frame_with_timeout()`：OpenCV/V4L2 `capture.read()` 卡住时按服务超时快速 fail-closed，并释放共享 capture。
  - WebRTC offer 首帧检查改为超时读帧，不再让 HTTP 请求被 V4L2 select 卡住。
  - MJPEG fallback 在发送 HTTP 200 multipart 之前必须先读到真实首帧；读不到时返回结构化 503，而不是先开流再无画面。
  - `/health` 将 `capture_read_returned_false`、`capture_read_call_timeout`、`capture_read_no_result` 都提升为 `source_first_frame_failed/first_frame_failed`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏把 `capture_read_returned_false`、`capture_read_call_timeout` 也翻译为“相机没有出画面，检查摄像头/视频线”。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 新增 V4L2 read timeout 单测。
  - 更新 health 失败态测试，覆盖 `capture_read_returned_false`。
- `docs/vision/board_camera_publisher.md`
  - 记录当前 DV20 `/dev/video1` 首帧 fail-fast 状态，覆盖历史“MJPEG 可见”的旧现场状态。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 普通首屏当前画面失败态口径。

## 验证结果

- 本地测试
  - `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`
    - 通过：`Ran 15 tests`
  - `npm test`
    - 通过：`2 passed (2)，231 passed (231)`
  - `npm run build`
    - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`
- 上板部署
  - 已 scp `onboard/scripts/local_webrtc_camera_smoke.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`。
  - 已重启 8088 camera service，当前进程：
    `python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 30`
- Live 验证
  - `GET http://192.168.1.11:8787/api/camera/mjpeg`
    - 约 4 秒返回 HTTP 502，上游 8088 为 HTTP 503。
    - body preview 含 `error=first_frame_unreadable`、`failure_reason=capture_read_returned_false`。
  - `GET http://192.168.1.11:8787/api/camera/health`
    - `status=source_first_frame_failed`
    - `video_source=/dev/video1`
    - `fps=30`
    - `source_readiness=first_frame_failed`
    - `source_failure_reason=capture_read_returned_false`
  - `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
    - `camera.status=source_first_frame_failed`
    - `selected_path=/dev/video1`
    - `last_offer_failure_reason=capture_read_returned_false`
    - `free_roam_start_ready=true`

## 剩余风险

- 这轮让画面失败更快、更诚实，但没有修复 DV20 硬件/驱动不出帧本身。当前仍不能证明实时画面可见，也不能把摄像头作为建图 ready 证据。
- 下一步需要现场硬件动作：复位或更换 DV20、检查 USB 供电和视频输入源，或接入 known-good UVC 摄像头验证 `/dev/video1` 出帧链路。
- 未执行真实 Nav2 发车或底盘运动；本轮只改摄像头 WYSIWYG 失败态和只读验证。
