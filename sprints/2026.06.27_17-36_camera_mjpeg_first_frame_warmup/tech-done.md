# Camera MJPEG 首帧 Warmup 对齐

sprint_type: micro

## 实际改动

- 上车端 `onboard/scripts/local_webrtc_camera_smoke.py` 将共享 MJPEG 首帧等待预算从独立 1 秒改为复用 WebRTC offer 的 3 秒预算。
- 保持安全边界：MJPEG 仍必须读到真实 OpenCV 帧才输出 multipart JPEG，失败继续结构化返回，不输出黑帧或 placeholder。
- 补充 `onboard/tests/test_local_webrtc_camera_smoke.py` 单元测试，锁定 MJPEG 与 WebRTC 共用同一首帧 warmup 预算。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 `docs/vision/board_camera_publisher.md`。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`，24 tests OK。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：部署到 `root@192.168.1.11:37878`；远端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 通过；`systemctl restart trashbot-local-webrtc-camera.service` 后服务为 `active (running)`，PID `260484`，命令行为 `python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 --video-source auto --width 640 --height 480 --fps 15`。
- 通过：8088 `/health` 重启后先返回 `status=source_not_probed`、`video_source=/dev/video1`、`active_peer_count=0`，说明旧失败状态已清空且系统服务接管 8088。
- 通过：8088 `/mjpeg` live smoke 使用 `curl --max-time 35`，返回结构化 JSON 失败而非挂死或伪造图：`status=error`、`error=first_frame_unreadable`、`failure_reason=capture_read_returned_false`、`first_frame_timeout_s=3.0`、`format_attempt_count=9`、`has_jpeg_soi=false`。
- 通过：7001 Robot Control summary readback 显示 `camera.status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`，普通诊断仍明确“不是页面独占，UVC 设备没有输出视频帧”。
- 通过：`git diff --check`。

## 剩余风险

- 该改动提高共享预览首帧 warmup 容错，但 live DV20 UVC 仍完全不输出视频帧，最终仍显示无帧诊断；需要换线、供电或 known-good UVC 继续 HIL 复核。
- 当前无帧时完整 9 格式矩阵约 25-28 秒返回结构化失败；后续可继续优化为总预算上限或后台探针，避免 PC 等待过久。
- 本轮不触发真实底盘运动、不执行 Nav2 goal、不确认 delivery success。
