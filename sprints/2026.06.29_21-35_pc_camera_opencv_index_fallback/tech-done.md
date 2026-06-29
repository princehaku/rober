# PC Camera OpenCV Index Fallback

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`：OpenCV 打开 `/dev/videoN` 失败时会自动再试数字索引 `N`，并在 shared capture summary 中记录实际 `open_source`。这样部分板端 UVC 在 path/index 打开行为不一致时，仍有机会读到真实首帧；服务仍禁止黑帧、placeholder 或伪图像。
- `onboard/scripts/local_webrtc_camera_smoke.py`：首帧格式尝试结果新增 `open_source` 字段，PC/上位机日志能看到每次 MJPG/YUYV 尝试到底用的是 path 还是 index 打开方式。
- `onboard/tests/test_local_webrtc_camera_smoke.py`：新增 no-hardware 回归，覆盖 `/dev/video1` path 打不开但 `index:1` 可打开时复用同一个真实 capture，不新增第二条上游流。

## 验证结果

- 通过：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_first_frame_probe`，42 tests OK。
- 通过：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/camera_first_frame_probe.py`。
- 通过：`git diff --check`。
- 通过：`bash onboard/scripts/docker_humble_build.sh`，Docker/Humble `colcon build --symlink-install` 输出 `Summary: 6 packages finished [43.2s]`；构建过程仍有既有 amd64 ROS 镜像运行在 arm64 Docker Desktop 上的平台 warning。
- 通过：部署到真实上位机 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py` 并重启 8088 图传服务，最终监听 PID `402269`。
- 真实上位机只读/媒体验证：`curl http://127.0.0.1:8088/mjpeg` 仍返回 HTTP 503，`failure_reason=first_frame_total_timeout`，尝试 `MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@320x240@25` 均为 `capture_read_returned_false`。
- 真实上位机 PC relay 验证：`GET /api/camera/mjpeg` 通过共享 relay 返回 HTTP 502 包装上游 503，`exclusive_camera_claim=false`，PC 7001 `/api/robot-control/camera/mjpeg/status` 显示 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`source_usage_owner_count=0`。

## 剩余风险

- 当前 DV20 UVC 仍没有输出首帧；本轮证明不是页面独占，且 path 打开后读帧失败，因此还没有真实画面 WYSIWYG 成功证据。
- 内核日志仍可见 `uvcvideo ... Failed to resubmit video URB (-1)` 和 USB reset 记录；下一步需要检查 USB/供电/摄像头输入，或换 known-good UVC 复测。
- 本轮没有发送 manual、keyboard、free-roam、Nav2 goal、delivery、stop 或 `/cmd_vel`，不证明完整 Nav2 路线执行、wheel raw L/R 非零或 delivery success。
