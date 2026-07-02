# Camera MJPEG YUYV Budget

- sprint_type: micro
- 时间：2026-07-02 15:20 CST
- Owner：Robot Software Engineer + User Touchpoint Full-Stack Engineer

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py` 将共享 MJPEG 单次首帧尝试从 `3.0s` 缩短为 `1.2s`，总窗口仍为 `9.0s`，让 `YUYV@320x240@25`、`YUYV@640x480@22`、`default@current` 和 open-source fallback 能进入真实尝试。
- `onboard/tests/test_local_webrtc_camera_smoke.py` 更新 MJPEG 预算合同，新增断言保证关键 5 个尝试能落在 primary 窗口内。
- 已部署到小车 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，重启 `trashbot-local-webrtc-camera.service` 后服务 active。

## 验证结果

- 已按硬件纪律读取 `docs/vendor/VENDOR_INDEX.md`；现场硬件事实通过只读 `lsusb -t` / `v4l2-ctl` 验证，当前 DV20 UVC 在 USB `12M` full-speed，支持 `MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@640x480@22`、`YUYV@320x240@25/20`。
- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke`：通过，39 tests。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，91 tests，1 skipped。
- `git diff --check`：通过。
- 现场触发 `GET /api/robot-control/camera/mjpeg?baseUrl=http://192.168.1.11:8787`：仍返回 `first_frame_total_timeout`，`robot_control_executed=false`，`safe_to_control=false`。
- 现场 `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`：尝试摘要已包含 `MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@320x240@25`、`YUYV@640x480@22`、`default@current`、`MJPG@640x480@30(/dev/video1/CAP_V4L2)`，均无首帧。
- 现场 `GET /api/robot-control/summary`：`readback_summary.camera.last_offer_format_attempts_summary` 同步显示完整尝试链，`source_diagnosis_status=uvc_full_speed_usb_not_exclusive`，`live_wysiwyg_missing_surface_ids=["camera"]`。

## 剩余风险

- 相机画面仍未可见；本轮已排除“只试 MJPG 模式导致误判”的软件盲区，剩余根因仍指向 USB `12M` full-speed / UVC 传输链路。
- 建图仍被 `camera_first_frame` 阻塞；自由移动不被相机阻塞。
- 本轮没有发送任何运动、Nav2、manual、keyboard、free-roam、建图、delivery 或 stop 请求。
