# 2026-06-26 22:45 camera API alias shared preview

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 新增 `normalize_camera_service_path()`，让 8088 camera service 同时兼容历史根路径和 `/api/camera/*` 路径。
  - `GET /api/camera/health`、`/api/camera/devices`、`/api/camera/mjpeg` 现在分别等价于 `/health`、`/devices`、`/mjpeg`。
  - `POST /api/camera/offer`、`/api/camera/peers/{peer_id}/close` 现在分别等价于 `/offer`、`/peers/{peer_id}/close`。
  - 首帧失败或客户端提前断开时，已释放的 shared capture 会从 health 摘要移除，BrokenPipe 只记录短事件。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 新增 `/api/camera/*` 路径别名回归测试。
- `docs/vision/board_camera_publisher.md`
  - 记录 camera service 路径别名、释放行为和真实上车验证。
- `docs/product/pc_tools_workstation.md`
  - 同步 PC 共享预览合同，说明当前不可见仍是 `/dev/video1` 无帧输出，不是 PC 独占。

## 验证结果

- 本地：
  - `python3 -m unittest onboard/tests/test_local_webrtc_camera_smoke.py`
    - 20 tests OK。
  - `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py`
    - 通过。
- 上车部署：
  - 备份路径：`/root/rober/runtime/deploy_backups/camera_api_alias_cleanup_20260626_224247/`。
  - 已部署到 `/root/rober/onboard/scripts/local_webrtc_camera_smoke.py`。
  - 8088 干净重启后监听 PID：`152473`。
- 上车 live smoke：
  - `GET http://127.0.0.1:8088/api/camera/health`
    - HTTP 200，`schema=trashbot.local_webrtc_camera_smoke.v1`，`video_source=/dev/video1`。
  - `GET http://127.0.0.1:8088/api/camera/devices`
    - HTTP 200，`schema=trashbot.local_webrtc_camera_devices.v1`。
  - `GET http://127.0.0.1:8787/api/camera/health`
    - HTTP 200，`schema=trashbot.local_webrtc_camera_smoke.v1`。
  - `GET http://127.0.0.1:8787/api/camera/devices`
    - HTTP 200，`schema=trashbot.local_webrtc_camera_devices.v1`。
  - `GET /api/camera/mjpeg` 首帧仍失败；完整失败收尾后 health 显示
    `status=source_first_frame_failed`、`source_readiness=first_frame_failed`、
    `source_failure_reason=capture_read_returned_false`、`source_usage.status=not_in_use`、
    `owner_count=0`、`shared_captures={}`。
- PC 7001 live summary：
  - `console_status=loaded_fail_closed_summary`。
  - `readback_summary.camera.devices_status=loaded`。
  - `readback_summary.camera.shared_preview_exclusive_camera_claim=false`。

## 剩余风险

- 本轮修复的是 camera service API 合同和失败后资源释放，不证明画面已经可见。
- 真实上车 `/dev/video1` 仍能枚举、能被选中，但 MJPG/YUYV/default 均没有输出首帧；下一步需要现场查摄像头输入、USB 线/供电、采集卡，或替换 known-good UVC。
- 未触发 manual、keyboard、Nav2、delivery、free-roam start/stop、stop 或 `/cmd_vel`；所有 camera 响应仍保持 `safe_to_control=false`、`primary_actions_enabled=false`。
