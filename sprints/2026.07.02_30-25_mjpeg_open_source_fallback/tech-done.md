# MJPEG open source fallback

## sprint_type

micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - 新增共享 MJPEG 两段式首帧采集：先用低带宽格式矩阵在默认 path 上取帧，失败后再用剩余预算尝试 OpenCV index / CAP_V4L2 打开方式。
  - 新增 `open_source_fallbacks_only`，第二阶段跳过刚失败的 path/default，避免浪费短预算。
  - `/mjpeg` 默认入口改为调用 `acquire_mjpeg_first_frame_capture()`。
- `onboard/tests/test_local_webrtc_camera_smoke.py`
  - 新增无硬件单元测试，证明默认 MJPEG 预览会先试低带宽格式，再尝试 index/V4L2 fallback，并在 index 读到帧时保留共享 capture。
- `onboard/tests/test_upper_robot_api.py`
  - 修正现有 base status 兼容采样测试：`GET /api/base/status` 默认不抢 UART，只有显式设置 `ROBER_BASE_STATUS_DIRECT_FEEDBACK_ON_GET=1` 时才验证旧式 T=130 readback。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步记录共享 MJPEG 的两段式只读恢复口径。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_first_frame_probe`
  - 结果：通过，`Ran 51 tests`，`OK`。
- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_first_frame_probe onboard.tests.test_upper_robot_api`
  - 结果：通过，`Ran 142 tests`，`OK (skipped=1)`。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/camera_first_frame_probe.py onboard/scripts/upper_robot_api.py`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无空白错误。
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` live 读回：
  - `current_camera_wysiwyg_pack_status=needs_first_frame`
  - `current_camera_wysiwyg_pack_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `current_camera_wysiwyg_pack_usb_speed=12M`
  - `current_camera_wysiwyg_pack_blocks_mapping_start=true`
  - `current_camera_wysiwyg_pack_blocks_free_move=false`
  - `current_mapping_action_missing_evidence=["camera_first_frame"]`
  - `current_mapping_action_camera_ready=false`
  - `current_mapping_action_radar_ready=true`
  - `current_radar_map_wysiwyg_pack_status=loaded`
  - `live_wysiwyg_missing_surface_ids=["camera"]`

## 剩余风险

- 本轮没有直接在上位机真实 USB 摄像头上验证首帧恢复；它补的是 `/dev/video*` path 打开但无帧时的默认 MJPEG fallback。
- 当前 live 仍显示相机挂在 USB `12M` full-speed；如果底层 UVC 传输完全不可用，仍需现场换高速 USB 口/线或带供电 Hub 后复测。
- 运动目标仍需现场安全确认后继续验证 wheel raw L/R 非零、完整 Nav2 行程、delivery success、键盘连续手控和自由移动启动读回。
