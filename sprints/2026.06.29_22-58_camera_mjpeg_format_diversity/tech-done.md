# Camera MJPEG 首屏格式优先级修正

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 共享 MJPEG `/api/camera/mjpeg` 首帧短预算不再启用 path/index/backend fallback 作为每个格式的内层循环。
  - 短预算优先跨格式尝试 `MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@320x240@25` 等低带宽/不同像素格式，避免 9 秒预算全花在同一个 `MJPG@640x480@30`。
  - WebRTC offer、高级首帧探针和通用 OpenCV fallback 能力不变，仍可用于继续排查 path/index/backend 差异。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 新增回归测试，证明 MJPEG 短预算下前三次 attempts 先跨格式，而不是同一格式的不同打开方式。
- `docs/product/pc_tools_workstation.md`
  - 记录 8088 共享预览新策略和 live 验证结论。
- `docs/process/okr_progress_log.md`
  - 追加 Objective 3/5 的画面 WYSIWYG 进展。

## 验证结果

- 本地：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke -v` 通过，33 tests OK。
- 本地：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py` 通过。
- 上车部署：`scp` 更新 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，远端 `python3 -m py_compile` 通过，`systemctl restart trashbot-local-webrtc-camera.service` 后服务 `active`，PID `413184`。
- 上车 live：请求 `http://192.168.1.11:8088/api/camera/mjpeg` 返回 HTTP 503，结构化 attempts 已覆盖：
  - `MJPG@640x480@30(/dev/video1)` 无首帧
  - `MJPG@480x320@30(/dev/video1)` 无首帧
  - `YUYV@320x240@25(/dev/video1)` 无首帧
- PC 7001 只读 summary 已同步显示 `last_offer_format_attempts_summary` 和 `first_frame_probe_fallback_attempts_summary` 为上述三种格式。

## 剩余风险

- 真实画面仍未出现；当前证据更明确指向 UVC 没输出视频帧、摄像头输入/供电或硬件问题，仍需现场检查或换 known-good UVC 复测。
- 本轮没有发送任何底盘、Nav2、free-roam、keyboard、delivery、stop 或 `/cmd_vel` 命令。
