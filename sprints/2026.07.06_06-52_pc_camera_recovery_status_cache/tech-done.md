# PC 相机 Recovery 诊断缓存

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 将 `high_speed_zero_byte_no_frame`、`streamon_success_zero_byte_no_frame`、`zero_byte_no_frame` 和 `select_timeout` 纳入相机首帧失败原因集合。
  - 新增最近一次 USB recovery 失败缓存；当 recovery 已证明高速 USB、STREAMON 成功但 0 字节无帧时，后续 `/api/robot-control/camera/mjpeg/status` 和 summary 不再退回泛化 `probe_total_timeout/not_loaded`。
  - recovery 若真实观察到 frame，会清理旧的 recovery/probe/MJPEG 失败缓存，避免硬件恢复后继续显示旧 blocker。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补充 USB recovery 后读取 MJPEG status 的回归测试，确认 status 保留 `known_good_uvc_required=true`、`camera_input_signal_check_required=true`、`source_failure_reason=high_speed_zero_byte_no_frame`，且不打开 `/api/camera/mjpeg` 流。
- `docs/product/pc_tools_workstation.md`
  - 记录 2026-07-06 06:52 CST 当前相机现场证据和产品口径：不是页面独占，当前缺口指向 DV20/采集输入、视频线、USB/供电或 known-good UVC。

## 验证结果

- 现场上位机 `ssh -p 7878 root@192.168.1.11` 复核：
  - `trashbot-local-webrtc-camera.service` active，`0.0.0.0:8088` listening。
  - `/dev/video1` 最终 `lsof` 无 owner，DV20 UVC 仍在 USB `480M`。
  - PC 首帧 probe 返回 `status=probe_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - USB recovery 返回 `status=streamon_success_zero_byte_no_frame`、`stream_failure_class=high_speed_zero_byte_no_frame`、YUYV/MJPG 均 STREAMON 成功但 0 字节。
- 已通过：
  - `npm test -- --run test/catalog.test.ts -t "camera USB recovery"`
  - `npm test`，3 个测试文件全部通过，`455 passed`。
  - `npm run build`，TypeScript app/server 与 Vite build 通过；仅保留既有 chunk size warning。
- 重启 PC Node 后已通过 7001 真实运行验证：
  - `/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
  - `POST /api/robot-control/camera/usb-recovery?baseUrl=http://192.168.1.11:8787` 返回 `status=streamon_success_zero_byte_no_frame`、`stream_failure_class=high_speed_zero_byte_no_frame`、`software_capture_exhausted=true`、`known_good_uvc_required=true`。
  - `GET /api/robot-control/camera/mjpeg/status` 返回 `source_failure_reason=high_speed_zero_byte_no_frame`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - `GET /api/robot-control/live-summary` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_ready=true`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`。

## 剩余风险

- 实时图传仍未恢复真实画面；远程软件恢复、首帧 probe、`v4l2-ctl` 和 ffmpeg 长窗口直采均未读到视频 buffer。
- 当前无法用代码把无视频 buffer 变成真实图传；下一步需要检查 DV20 输入信号、视频线、接口/供电，或换 known-good UVC 后再复测。
- PC 地图和 WASD 自动准备链路未被本轮改动；既有测试已覆盖页面加载后无需点击启用按钮即可按住 W/A/S/D 走固定手控代理。
