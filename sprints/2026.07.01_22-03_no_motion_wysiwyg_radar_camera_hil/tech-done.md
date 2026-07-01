# No-motion WYSIWYG 雷达与相机复验

sprint_type: micro

## 实际改动

- 本轮未修改产品代码。
- 执行 PC `7001` no-motion 现场复验，确认雷达贴图可通过固定只读/非运动链路恢复到当前地图。
- 执行相机首帧 probe 与 MJPEG status 读回，确认画面缺口仍是上车相机首帧失败，诊断为 USB 12M full-speed，不是页面独占。

## 验证结果

- 当前 PC Node：`0.0.0.0:7001`，PID `22103`。
- 复验前 summary：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_wysiwyg_missing_surface_ids=[camera,radar_map_points]`。
  - `camera_current_visible=false`、`camera_usb_speed=12M`、`camera_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`。
  - `radar_overlay_status=not_current`、`radar_overlay_current_point_count=0`、`radar_overlay_source_point_count=174`、`radar_overlay_needs_refresh=true`。
  - `radar_overlay_blocks_wysiwyg=true`、`radar_overlay_blocks_free_move=false`。
  - `mapping_start_missing_reasons=[camera_first_frame]`、`free_move_start_ready=true`。
- 执行 no-motion 雷达贴图刷新：
  - `POST /api/robot-control/radar/scan-proof/refresh?baseUrl=http://192.168.1.11:8787`
  - 回包 `schema=trashbot.pc_tools_workstation.robot_control_proof_refresh_proxy.v1`。
  - 回包 `robot_control_executed=false`。
  - 回包 `scan_once=true`、`scan_hz=true`、`raw_packet=true`。
- 雷达刷新后地图预览：
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`
  - `radar_overlay_status=loaded`。
  - `radar_overlay_current_point_count=68`、`radar_overlay_source_point_count=81`。
  - `radar_overlay_needs_refresh=false`。
  - `radar_overlay_blocks_wysiwyg=false`、`radar_overlay_blocks_free_move=false`。
  - `radar_overlay_refresh_sends_motion=false`、`radar_overlay_refresh_starts_radar_lifecycle=false`。
- 相机 MJPEG status：
  - `GET /api/robot-control/camera/mjpeg/status?baseUrl=http://192.168.1.11:8787`
  - `status=idle_not_started`、`client_count=0`、`upstream_active=false`、`exclusive_camera_claim=false`。
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、`source_diagnosis_not_exclusive=true`。
  - `uvc_usb_topology_video_usb_speed=12M`。
  - `robot_control_executed=false`。
- 相机首帧 probe：
  - `POST /api/robot-control/camera/first-frame/probe?baseUrl=http://192.168.1.11:8787`
  - HTTP `502` from PC proxy，remote HTTP status `503`。
  - 远端状态 `first_frame_timeout`，`failure_reason=deadline_expired`。
  - `camera_first_frame_ready=false`、`frame_observed=false`。
  - `source_diagnosis_status=uvc_full_speed_usb_not_exclusive`。
  - `camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`。
  - `camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`。
  - `camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`。
  - `robot_control_executed=false`、`sends_motion_when_clicked=false`、`starts_map_runtime=false`。
- 复验后 summary：
  - `field_acceptance_wysiwyg_missing_surface_ids=[camera]`。
  - `radar_map_points_visible=true`。
  - `radar_overlay_status=loaded`、`radar_overlay_current_point_count=68`、`radar_overlay_source_point_count=81`。
  - `radar_overlay_needs_refresh=false`、`radar_overlay_blocks_wysiwyg=false`、`radar_overlay_blocks_free_move=false`。
  - `mapping_start_missing_reasons=[camera_first_frame]`。
  - `free_move_start_ready=true`。
  - `route_ready_on_map=true`、`nav2_goal_succeeded=true`、`wheel_lr_nonzero_proven=false`、`route_delivery_success=false`。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 已通过：`git diff --check`。

## 剩余风险

- 雷达地图标记 WYSIWYG 已通过 no-motion 链路恢复；后续如果雷达源更新再次 stale，需要重复固定 refresh → map preview 链路。
- 画面 WYSIWYG 仍未完成，当前明确是 USB 12M full-speed / 首帧超时，不是页面独占；需要现场换高速 USB 口/线或带供电 Hub 后复测。
- 完整 Nav2 路线执行仍缺同窗口 wheel L/R 非零和 delivery success。
- PC 键盘连续控制仍缺按住窗口 wheel L/R 非零和松开停稳读回。
- 自由移动仍缺启动后的 `free_roam_motion_ready` 运行读数。
