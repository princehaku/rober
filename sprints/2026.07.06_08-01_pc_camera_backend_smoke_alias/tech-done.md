# PC camera backend smoke alias

sprint_type: micro

## 实际改动

- PC fixed first-frame probe 的诊断 alias 增加 `software_capture_exhausted`、`known_good_uvc_required` 和 `camera_input_signal_check_required`。
- 当显式 `backendSmoke=1` 的上车 backend smoke 返回 `backend_no_frame_observed` 且没有任何首帧证据时，PC probe 回包顶层直接暴露“软件采集矩阵已穷尽，需要检查输入/供电或换 known-good UVC”。
- `recordCameraFirstFrameProbeResult()` 同步保存这些 alias，后续 `camera/mjpeg/status` 和 summary 能继续继承本次深度检查事实。
- 更新 PC 合同类型、catalog 断言、`pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/catalog.test.ts -t "workstation camera first-frame probe can request backend smoke" --run`：通过，1 test OK。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts --run`：通过，195 tests OK。
- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run`：通过，18 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有体积警告。
- 本机 PC Node 已重启并继续监听 `0.0.0.0:7001`，`GET /api/health` 返回 `workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 真实 7001 deep probe：`POST /api/robot-control/camera/first-frame/probe?backendSmoke=1` 返回 `proxy_status=probe_failed`、`remote_http_status=503`、`status=first_frame_timeout`、`frame_observed=false`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`backend_smoke_status=backend_no_frame_observed`、`backend_attempts=11`、`backend_userptr_attempt_count=2`、`software_capture_exhausted=true`、`known_good_uvc_required=true`、`camera_input_signal_check_required=true`。
- 真实 7001 MJPEG status：`GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`、`shared_preview_everyone_can_join=true`、`shared_preview_exclusive_camera_claim=false`、`software_capture_exhausted=true`、`known_good_uvc_required=true`、`camera_input_signal_check_required=true`。
- 真实 7001 WASD 短脉冲复验：低速 `forward` 返回 `command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=164/164`；低速 `backward` 返回 `-164/-164`；两次 stop 均 `command_forwarded`。随后 live-summary 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_continuous_forwarded_pulses=2`、`keyboard_stop_settled_after_pulse=true`、`command_raw_lr_nonzero_proven=true`。

## 剩余风险

- 实时图传仍未恢复：DV20 `/dev/video1` 可枚举、USB 为 `480M`、无人占用，但 V4L2/ffmpeg/backend smoke 均未读到任何首帧。
- 本轮不生成占位图、不伪造相机 ready；图传缺口继续指向摄像头输入信号、供电、线材/接口、采集设备本体或 known-good UVC 复测。
- Wheel raw `T=1001 L/R` 仍未非零，本轮 WASD 只能证明 PC 到底盘命令 raw 非零与 stop 生效，不能替代 wheel raw 反馈闭环。
