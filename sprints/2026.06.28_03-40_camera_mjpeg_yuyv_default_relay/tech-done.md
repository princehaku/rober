# 2026.06.28 03:40 Camera MJPEG YUYV Default Relay

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py` 新增共享 MJPEG 专用首帧尝试顺序：
  `MJPG@640x480@15 -> YUYV@640x480@22 -> default@current`，再进入完整矩阵。
- WebRTC offer 保持原完整矩阵；只有短预算共享 MJPEG 先横跨 MJPG/YUYV/default，避免 live 9 秒窗口被多个 MJPG 模式耗尽。
- `onboard/scripts/upper_robot_api.py` 的共享 MJPEG relay 等待窗口从 8s 对齐到 12s，并保留 8088 JSON 503 的
  `last_error_payload`，让 PC 能看到真实首帧失败尝试矩阵。
- `pc-tools/workstation/src/server/index.ts` 和 `robotControlSummary.ts` 消费 relay `last_error_payload`，在 health 短超时或 devices 失败时仍能把
  `last_offer_format_attempts_summary` 显示成 MJPG/YUYV/default 的真实尝试结果。
- 同步更新 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_upper_robot_api` 通过，99 个测试通过。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/upper_robot_api.py onboard/tests/test_local_webrtc_camera_smoke.py onboard/tests/test_upper_robot_api.py` 通过。
- `npm test` 通过，335 个测试通过。
- `npm test -- test/catalog.test.ts -t 'workstation camera MJPEG status and summary remember the latest upstream failure'` 通过。
- `npm run lint` 通过。
- `npm run build` 通过。
- `git diff --check` 通过。
- live 部署后直连 8088 `/api/camera/mjpeg` 返回 `first_frame_total_timeout`，尝试矩阵包含
  `MJPG@640x480@15`、`YUYV@640x480@22`、`default@current`。
- live 部署后 8787 `/api/camera/mjpeg` 返回 502，但 `relay.last_error_payload.first_frame_format_attempts` 保留同一组三种尝试。
- live 重启 PC 7001 后，summary 的 `last_offer_format_attempts_summary` 显示
  `MJPG@640x480@15 无首帧；YUYV@640x480@22 无首帧；default@current 无首帧`。

## 剩余风险

- 当前 `/dev/video1` 仍没有输出真实首帧；这轮只修复“尝试顺序和证据透传”，没有证明摄像头画面已经可见。
- 没有现场安全确认，本轮没有发送 manual、keyboard、Nav2 goal、free-roam、stop 或 `/cmd_vel`。
