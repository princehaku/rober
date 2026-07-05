# PC camera deep probe userptr

sprint_type: micro

## 实际改动

- `onboard/scripts/camera_first_frame_probe.py`：backend smoke 增加设备自报低负载模式的 V4L2 `--stream-user=3` userptr 尝试，并输出 `userptr_attempt_count` / `userptr_frame_observed`。
- `onboard/scripts/upper_robot_api.py`：显式 `include_backend_smoke` 深度探针预算放宽，避免新增矩阵被上位机代理提前截断；普通 quick probe 预算不变。
- `pc-tools/workstation/src/server/index.ts`、`robotControlSummary.ts`、`contracts.ts`：PC 相机 first-frame probe 支持 query/body 两种方式触发深度 backend smoke，深度超时放宽到 `85000ms`，并把 userptr 证据透传到 probe key-values、compact payload 和 summary overlay。
- 单测同步覆盖 PC 深度 probe 超时、userptr 字段、summary 透传；文档同步更新 PC、扫图/自由移动和上车 README。

## 验证结果

- `python3 -m unittest onboard.tests.test_camera_first_frame_probe`：13 tests OK。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：104 tests OK，skipped 1。
- `npm run build`（`pc-tools/workstation`）：通过，Vite 仅提示既有 chunk size warning。
- `npm test`（`pc-tools/workstation`）：3 files / 455 tests passed。
- 已部署 `camera_first_frame_probe.py` 与 `upper_robot_api.py` 到上位机 `root@192.168.1.11 -p 7878`；`trashbot-upper-robot-api.service`、`trashbot-local-webrtc-camera.service` 均 active，8787/8088 监听正常。
- 真实 7001 深度 probe：`proxy_status=probe_failed`、`remote_http_status=503`、`status=first_frame_timeout`、`failure_reason=capture_read_call_timeout`、`backend_smoke_status=backend_no_frame_observed`、`backend_attempts=11`、`backend_userptr_attempt_count=2`、`backend_userptr_frame_observed=false`。
- 真实 7001 live-summary：`status=ready_for_motion`、`map_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、`keyboard_motion_verified=true`。

## 剩余风险

- 实时图传仍未恢复：DV20 `/dev/video1` 在 USB `480M`、无页面独占、mmap/userptr/ffmpeg/OpenCV 多模式均无 kernel frame。下一步必须处理 DV20 上游输入信号、线材/接口/供电、采集设备/摄像头本体，或换 known-good UVC 后复测。
- wheel feedback `T=1001 L/R` 仍是独立未闭环风险；本轮未宣称完整 Nav2/wheel raw 闭环完成。
