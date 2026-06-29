# PC Camera MJPEG Backend Attempts

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 共享 MJPEG 首帧读取新增 OpenCV 打开方式矩阵：`/dev/videoN`、显式 `CAP_V4L2` backend、数字索引 `N`。
  - 首帧失败时在 attempt 里记录 `open_source/open_backend`，并通过 `health.last_first_frame_format_attempts` 暴露给 PC。
  - 共享 capture 释放改为按对象清理，避免 fallback cache key 与原始设备路径不一致时残留旧句柄。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 新增 `last_first_frame_format_attempts_summary`，不用重新开流也能看到本轮尝试过哪些 OpenCV 打开方式。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary 的 `last_offer_format_attempts_summary` 兼容 health 的 `last_first_frame_error/last_first_frame_format_attempts`，并把打开方式写入短摘要。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步新增 camera MJPEG status 字段合同。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 新增 path/backend/index fallback、health attempt 暴露和释放行为相关测试。

## 验证结果

- 本地：`python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py` 通过。
- 本地：`python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_first_frame_probe`，45 tests OK。
- 本地：`npm test -- --run`，2 files / 386 tests OK。
- 本地：`npm run build` 通过。
- 真实上位机：已同步 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`，8088 监听 `0.0.0.0:8088`。
- 真实上位机：请求 `http://127.0.0.1:8088/mjpeg` 后，`/health` 返回 `source_first_frame_failed`、`source_failure_reason=first_frame_total_timeout`、`not_exclusive=true`、`source_usage=not_in_use`，attempts 包含：
  - `MJPG@640x480@30 /dev/video1 default` 无首帧；
  - `MJPG@640x480@30 /dev/video1 CAP_V4L2` 无首帧；
  - `MJPG@640x480@30 index:1 default` 无首帧。
- PC 端：已重启 Node 到 `0.0.0.0:7001`。
- PC 端：`GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`，`last_first_frame_format_attempts_summary=MJPG@640x480@30(/dev/video1) 无首帧；MJPG@640x480@30(/dev/video1/CAP_V4L2) 无首帧；MJPG@640x480@30(index:1) 无首帧`，并继续显示多人共享 relay 非独占。

## 剩余风险

- 当前仍看不到实时画面，结论不是页面独占，而是 DV20 UVC 源头没有输出首帧；下一步需要检查 USB、摄像头输入、供电，或换 known-good UVC 复测。
- 本轮没有发送 manual、keyboard、free-roam、Nav2 goal、delivery、stop 或 `/cmd_vel`。只读检查显示自由移动策略不硬依赖雷达；当前现场 artifact 仍是 `external_stop_requested=true`、`cmd_vel_publish_enabled=false`，需要现场重新勾选安全确认后由 start 入口清 stop 并解锁，才能验证真实移动。
- 当前 summary 仍显示 Nav2 历史阻塞含 `controller_server_active=false` 和定位 TF 旧材料；本轮没有在安全确认下执行完整路线，因此不声明自动驾驶已真实动起来。
