# PC camera selected device alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`：`GET /api/robot-control/camera/mjpeg/status` 新增 `selected_device` 与 `selected_device_label` 顶层 alias，和既有 `selected_path` / `selected_name` 同源，方便普通 PC 页面与现场脚本直接显示当前摄像头源。
- `pc-tools/workstation/src/shared/contracts.ts`：同步补充 `RobotControlCameraMjpegStatusResponse` 类型字段。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖 `source_first_frame_failed` 与 `source_selected_not_probed` 两类相机 status，确保 alias 不会再回退成空值。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：记录本轮只读相机状态增强和现场边界。

## 验证结果

- 现场地图只读刷新：`POST /api/robot-control/radar/scan-proof/refresh` 返回 `readback_only=true`、`no_motion_refresh=true`；随后 `GET /api/robot-control/map/preview` 返回 `path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=36`、`route_target_visible=true`、目标点 `(0.8,0.05,map)`。
- 现场图传诊断：`/dev/video0` 为 cedrus memory-to-memory，`/dev/video2` 为 UVC metadata，真实视频节点为 `/dev/video1` DV20；`camera/first-frame/probe` 返回 `probe_total_timeout`，`camera/mjpeg/status` 返回 `source_first_frame_failed`、`source_diagnosis_status=uvc_transport_error_not_exclusive`、`source_failure_reason=first_frame_total_timeout`、`source_usage_owner_count=0`、`exclusive_camera_claim=false`、`camera_hardware_action_required=true`。
- `npm test -- test/catalog.test.ts -t "camera MJPEG status" --run`：通过，9 tests OK / 179 skipped。
- `npm test -- test/App.test.ts -t "camera|map display|direct map|keyboard|WASD" --run`：通过，68 tests OK / 171 skipped。
- `npm run build`：通过，仅 Vite chunk size warning。
- 7001 已重启到 `HOST=0.0.0.0 PORT=7001 DEFAULT_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，新 PID `83058` 监听 `TCP *:7001`。
- live alias 读回：`selected_device=/dev/video1`、`selected_device_label=USB Composite Device: DV20 USB (usb-5310000.usb-1)`、`selected_path=/dev/video1`、`selected_name=USB Composite Device: DV20 USB (usb-5310000.usb-1)`。
- live PC 手控短脉冲：`forward` 与 `back` 均返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`；随后 `POST /api/robot-control/base/stop` 返回 `status=stopped`。

## 剩余风险

- 当前改动提升状态可读性，不等于实时图传已恢复。DV20 仍未输出可显示首帧，下一步仍是检查摄像头输入、线/接口/供电，或换 known-good UVC 复测。
- 本轮未重新执行 Nav2 完整路线或 delivery success；地图四层显示已经通过只读接口验证。
