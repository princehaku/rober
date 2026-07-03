# 2026-07-03 15:23 PC Map / IMU Motion Signal

sprint_type: micro

## 实际改动

- 回答并落地“PC 地图太小 / ROS2 有没有配套”：普通首页地图卡从 `height: clamp(620px, calc(100vh - 96px), 860px)` 放大到 `height: clamp(760px, calc(100vh - 24px), 1280px)`，内层地图画布最小高度提升到 `clamp(620px, calc(100vh - 176px), 980px)`；`/map` 直达页和 RViz2/Foxglove 只读观察入口继续保留。
- 修复 PC 手控代理运动证据：`remote_motion_key_values` 现在透出上位机 `/api/base/manual` 的 `motion_signal_observed`、`motion_signal_source`、`imu_attitude_delta_observed`、`manual_imu_attitude_delta_observed`、`imu_roll_delta` 和 `imu_pitch_delta`。
- 调整 `motion_evidence_gaps`：同窗口 IMU/车身运动信号已观察到时，不再要求 LiDAR delta 才能清掉“运动迹象”缺口；但 `wheel_feedback_lr_nonzero_not_proven` 仍只由 vendor `T=1001 L/R` 非零清除。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md` 和 `docs/hardware/wave_rover_json_bridge.md`。硬件协议依据已复核 `docs/vendor/VENDOR_INDEX.md`，采用 WAVE ROVER `json_cmd.h`、`uart_ctrl.h`、`movtion_module.h` 和 `ugv_rpi/config.yaml` 的本地资料口径。

## 验证结果

- 通过：`npm test -- catalog.test.ts App.test.ts`，2 files / 425 tests passed。
- 通过：`npm test`，3 files / 438 tests passed。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm run lint`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`GET /api/health` 返回 `workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：真实 summary 读回 `normalized_base_url=http://192.168.1.11:8787`、`map_current_visible=true`、`path_current_visible=true`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`、`wheel_feedback_lr_nonzero_proven=false`、`nav2_goal_execution_proven=false`、`delivery_success=false`。
- 通过：真实 `GET /api/robot-control/map/preview` 返回 `path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=165`、`route_target_visible=true`、`target={x:0.8,y:0.05,frame_id:map,source:path_preview_points}`，且 `readback_only=true`、`sends_motion_when_clicked=false`。
- 通过：真实 `POST /api/robot-control/base/manual` 前进 `0.08m/s`、`800ms` 返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`feedback_during_motion_t1001_frame_count=80`、`wheel_feedback_latest_raw_left=0`、`wheel_feedback_latest_raw_right=0`、`imu_attitude_delta_observed=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`，`motion_evidence_gaps=["before_after_evidence_snapshot_incomplete","wheel_feedback_lr_nonzero_not_proven"]`，已不再包含 LiDAR delta 缺口。
- 通过：上位机 command debug 同窗口记录 `command_transport=http`、`http_write_returned=true`、`T=11,L/R=255` 和自动 stop `T=11,L/R=0`；feedback debug 后续仍为 `T=1001 L/R=0/0`。
- 通过：相机只读首帧 probe 返回 `probe_total_timeout`、`camera_usb_speed=480M`、`camera_usb_full_speed_detected=false`、`source_diagnosis_not_exclusive=true`；共享 MJPEG status 返回 `shared_capture=true`、`exclusive_camera_claim=false`。

## 剩余风险

- 本轮不把 IMU 姿态变化包装成 wheel raw L/R；现场 wheel raw `T=1001 L/R` 仍未证明非零。
- 摄像头仍是 480M 下的首帧 timeout/源头无帧问题，本轮未修复真实图传硬件链路。
- Nav2 目标曾返回 succeeded，但仍缺同窗口 wheel raw 非零和 delivery success；不能宣称完整自动驾驶闭环完成。
