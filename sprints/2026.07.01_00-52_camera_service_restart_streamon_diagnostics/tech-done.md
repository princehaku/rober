# 2026.07.01 00:52 camera service restart 与 STREAMON diagnostics

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.sh`
  - 启动前检查监听同一 `PORT` 的旧进程。
  - 只清理命令行包含 `local_webrtc_camera_smoke.py` 的 stale listener，避免旧进程脱离 systemd 后继续占用 `0.0.0.0:8088`。
  - 若端口被其它服务占用，只输出错误，不抢占非相机服务。
- `onboard/scripts/camera_first_frame_probe.py`
  - `--include-backend-smoke` 新增 `streamon_io_error_observed`、`streamon_io_error_count`、`latest_streamon_io_error`。
  - OpenCV `open_failed` 时也继续运行 V4L2/ffmpeg backend smoke，避免 PC 只看到泛化 open 失败。
- `pc-tools/workstation/src/server/index.ts`
  - camera first-frame probe proxy 的 `probe_key_values` 透传 STREAMON I/O error 字段。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - camera summary readback 增加 `first_frame_probe_streamon_io_error_*` 字段。
- `pc-tools/workstation/src/shared/contracts.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 同步类型与 fixture。
- `docs/vision/board_camera_publisher.md`、`docs/product/pc_free_roam_mapping_design.md`
  - 记录 2026-07-01 上车验证结果和剩余摄像头硬件/USB blocker。

## 验证结果

- 本地：
  - `bash -n onboard/scripts/local_webrtc_camera_smoke.sh` 通过。
  - `python3 -m py_compile onboard/scripts/camera_first_frame_probe.py` 通过。
  - `python3 -m unittest onboard.scripts.test_local_webrtc_camera_smoke_health` 通过，`Ran 5 tests`。
  - `npm run build` 在 `pc-tools/workstation` 通过；仅保留既有 Vite bundle size warning。
  - `npx vitest run test/catalog.test.ts --testNamePattern "camera first-frame probe|backend smoke|source first-frame"` 通过，`6 passed | 171 skipped`。
- 上车 no-motion：
  - 已同步 `local_webrtc_camera_smoke.sh` 和 `camera_first_frame_probe.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/`。
  - 板端 `bash -n /root/rober/onboard/scripts/local_webrtc_camera_smoke.sh` 通过。
  - 连续两次 `systemctl restart trashbot-local-webrtc-camera.service` 后：
    - `systemctl is-active trashbot-local-webrtc-camera.service` 为 `active`。
    - `ss -ltnp` 显示 `0.0.0.0:8088` 由 systemd MainPID `python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py ...` 监听。
  - 共享 MJPEG 复测后 `GET http://127.0.0.1:8088/health` 返回：
    - `status=source_first_frame_failed`
    - `source_readiness=first_frame_failed`
    - `source_failure_reason=first_frame_total_timeout`
    - `source_usage.status=not_in_use`
    - `source_diagnosis.status=uvc_no_frame_not_exclusive`
  - `camera_first_frame_probe.py --include-backend-smoke` 返回：
    - `status=first_frame_timeout`
    - `backend_status=backend_no_frame_observed`
    - `streamon_io_error_observed=true`
    - `streamon_io_error_count=9`
    - `latest_streamon_io_error` 包含 `ioctl(VIDIOC_STREAMON): Input/output error` 和 `/dev/video1: Input/output error`
    - `sends_motion_commands=false`

## 剩余风险

- 摄像头仍未恢复真实画面；当前 blocker 是 DV20 `/dev/video1` 在 V4L2/ffmpeg STREAMON 阶段 I/O error。
- 需要现场检查 USB 线、接口、供电、DV20 输入，或换 known-good UVC 摄像头复测。
- 本轮未执行任何底盘运动、Nav2 goal、keyboard manual、free-roam、delivery 或 `/cmd_vel`。
