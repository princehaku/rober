# Camera Probe Backend Release Micro Sprint

## sprint_type

micro

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py`：OpenCV 首帧失败后，如果启用 backend smoke，先释放 `VideoCapture`，再运行 `v4l2-ctl` / `ffmpeg` 后端矩阵。
- `onboard/tests/test_camera_first_frame_probe.py`：新增断言，确保 backend smoke 执行时 capture 已释放。
- `docs/vision/board_camera_publisher.md`：记录本轮真实上车探针结论和证据边界。

## 验证结果

- `python3 -m unittest onboard.tests.test_camera_first_frame_probe`：通过，7 tests passed。
- 已同步 `camera_first_frame_probe.py` 到真实上位机 `root@192.168.1.11:37878`。
- 真实上位机执行：
  `python3 scripts/camera_first_frame_probe.py --device /dev/video1 --width 640 --height 480 --fps 30 --timeout-s 3 --read-call-timeout-s 1 --sample-path /tmp/rober_probe_latest.jpg --include-backend-smoke`
  返回 `status=first_frame_timeout`、`open_ok=true`、`read_ok=false`、`failure_reason=capture_read_call_timeout`。
- 同一结果中的 backend smoke 返回 `backend_no_frame_observed`：
  `v4l2_mjpg_mmap`、`v4l2_yuyv_mmap`、`ffmpeg_mjpg`、`ffmpeg_yuyv` 均结构化超时，`frame_observed=false`。
- 远端 camera service 已恢复：`local_webrtc_camera_smoke.py` 和 `upper_robot_api.py` 均在运行。

## 剩余风险

- 本轮修复的是诊断可信度，不是 `/dev/video1` 无帧根因。
- 当前证据说明 PC 共享预览、OpenCV、V4L2 和 ffmpeg 都没有读到真实帧；下一步仍需现场检查镜头、USB、采集卡输入、供电或替换 known-good UVC。
- 相机首帧未证明前，自动扫图/建图运动门禁仍必须保持 fail-closed。
