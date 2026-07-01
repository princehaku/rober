# No-motion WYSIWYG Refresh Evidence

## sprint_type

micro

## 目标

- 按 PC summary 声明的 no-motion 当前所见刷新链路复验地图、雷达贴图和相机首帧。
- 在不发车、不启动 Nav2/manual/keyboard/free-roam/建图 runtime 的前提下，尽量推进 WYSIWYG 当前证据。

## 实际操作

- 执行 `POST /api/robot-control/radar/scan-proof/refresh`。
- 读取 `GET /api/robot-control/radar/status`。
- 读取 `GET /api/robot-control/map/preview`。
- 执行 `POST /api/robot-control/camera/first-frame/probe`。
- 读取 `GET /api/robot-control/camera/mjpeg/status`。
- 读取 `GET /api/robot-control/summary`。

## 验证结果

- 雷达 scan proof refresh 回包：
  - `readback_only=true`
  - `no_motion_refresh=true`
  - `sends_motion_when_clicked=false`
  - `starts_radar_lifecycle=false`
  - `starts_nav2=false`
  - `starts_manual=false`
  - `starts_keyboard=false`
  - `starts_free_roam=false`
  - `starts_map_runtime=false`
  - `submits_delivery=false`
  - `stops_motion=false`
- 雷达 status 回包：
  - `readback_only=true`
  - `radar_status_readback_only=true`
  - 所有 motion/control danger flags 均为 `false`。
- 地图预览回包：
  - `radar_overlay_status=loaded`
  - `radar_overlay_current_point_count=162`
  - `radar_overlay_source_point_count=188`
  - `robot_pose_status=map_pose_observed`
- 相机首帧 probe：
  - PC 代理返回 `502`。
- 相机 MJPEG status：
  - `status=source_first_frame_failed`
  - `shared_preview_client_count=0`
  - `shared_preview_upstream_active=false`
  - `shared_preview_exclusive_camera_claim=false`
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `source_diagnosis_not_exclusive=true`
- summary 复验：
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_overlay_status=loaded`
  - `radar_overlay_wysiwyg_complete=true`
  - `live_wysiwyg_radar_map_current_point_count=162`
  - `live_wysiwyg_radar_map_source_point_count=188`
  - `camera_current_visible=false`
  - `camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`
  - `mapping_start_ready=false`
  - `mapping_start_missing_reasons=["camera_first_frame"]`
  - `mapping_lidar_fresh_readback_ready=true`
  - `mapping_lidar_fresh_gate_status=ready`

## 剩余风险

- WYSIWYG 现在只剩相机画面缺口；现场仍需把摄像头换到高速 USB 口/线或带供电 Hub 后复测。
- 完整 Nav2 路线、键盘连续控制、自由移动和 delivery success 仍需要现场安全确认后的真实运动验证。
