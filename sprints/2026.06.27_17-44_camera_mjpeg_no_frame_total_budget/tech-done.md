# Camera MJPEG 无帧总预算

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py` 的首帧采集函数新增可选 `total_timeout_s`。
- 8088 共享 MJPEG 路径使用 `MJPEG_FIRST_FRAME_TOTAL_TIMEOUT_S=9.0`，无帧时不再等待完整 9 格式矩阵约 25-28 秒。
- WebRTC offer 不传总预算，仍保留完整格式矩阵，便于深度排障。
- `FIRST_FRAME_FAILURE_REASONS` 新增 `first_frame_total_timeout`，确保 health / PC summary 继续把该失败识别为首帧失败。
- 补充单元测试覆盖 MJPEG 总预算提前返回，不输出假图、不跑完整矩阵。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 `docs/vision/board_camera_publisher.md`。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`，25 tests OK。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`。
- 通过：部署到 `root@192.168.1.11:37878`；远端 py_compile 通过；`systemctl restart trashbot-local-webrtc-camera.service` 后服务为 `active (running)`，PID `261514`。
- 通过：8088 `/mjpeg` live smoke 使用 `curl --max-time 15`，约 `9.938s` 返回结构化 JSON，`status=error`、`failure_reason=first_frame_total_timeout`、`first_frame_timeout_s=3.0`、`first_frame_total_timeout_s=9.0`、`first_frame_elapsed_s=9.069`、`format_attempt_count=3`、`has_jpeg_soi=false`。
- 通过：等待后台读帧线程收尾后，8088 `/health` 显示 `source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`、`source_usage.status=not_in_use`、`shared_captures={}`。
- 通过：7001 Robot Control summary readback 显示 `camera.source_failure_reason=first_frame_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、普通诊断继续明确“不是页面独占，UVC 设备没有输出视频帧”。
- 通过：`git diff --check`。

## 剩余风险

- 当前 DV20 UVC 仍未输出真实视频帧；本轮只让失败更快、更所见即所得，不替代换线、供电或 known-good UVC 复测。
- 本轮不触发真实底盘运动、不执行 Nav2 goal、不确认 delivery success。
