# 2026-07-03 15:23 PC Map / IMU Motion Signal

sprint_type: micro

## 实际改动

- 回答并落地“PC 地图太小 / ROS2 有没有配套”：普通首页地图卡从 `height: clamp(620px, calc(100vh - 96px), 860px)` 放大到 `height: clamp(760px, calc(100vh - 24px), 1280px)`，内层地图画布最小高度提升到 `clamp(620px, calc(100vh - 176px), 980px)`；`/map` 直达页和 RViz2/Foxglove 只读观察入口继续保留。
- 修复 PC 手控代理运动证据：`remote_motion_key_values` 现在透出上位机 `/api/base/manual` 的 `motion_signal_observed`、`motion_signal_source`、`imu_attitude_delta_observed`、`manual_imu_attitude_delta_observed`、`imu_roll_delta` 和 `imu_pitch_delta`。
- 调整 `motion_evidence_gaps`：同窗口 IMU/车身运动信号已观察到时，不再要求 LiDAR delta 才能清掉“运动迹象”缺口；但 `wheel_feedback_lr_nonzero_not_proven` 仍只由 vendor `T=1001 L/R` 非零清除。
- 修复相机恢复脚本和上车相机 health 诊断：通过 `/sys/class/video4linux/videoX/device` 反查当前 USB kernel 地址，避免旧端口 UVC 错误和其他 Video interface 的 `12M` 速率污染当前 DV20 诊断；`camera_usb_recovery_smoke.py` 在当前设备为 `480M` 但仍 0 帧时提示检查 USB 线、接口、供电或换 known-good UVC。
- PC summary 增加底盘只读顶层别名：`base_motion_signal_observed`、`base_motion_signal_source`、`base_wheel_feedback_latest_raw_left/right`、`motion_signal_observed` 和 `wheel_feedback_lr_nonzero_proven`，方便普通页和现场脚本直接读取“IMU 有运动信号但 wheel raw 仍 0/0”。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md` 和 `docs/hardware/wave_rover_json_bridge.md`。硬件协议依据已复核 `docs/vendor/VENDOR_INDEX.md`，采用 WAVE ROVER `json_cmd.h`、`uart_ctrl.h`、`movtion_module.h` 和 `ugv_rpi/config.yaml` 的本地资料口径。

## 验证结果

- 通过：`npm test -- catalog.test.ts App.test.ts`，2 files / 425 tests passed。
- 通过：`npm test`，3 files / 438 tests passed。
- 通过：`npm run build`，仅保留既有 Vite chunk size warning。
- 通过：`npm run lint`。
- 通过：`python -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/camera_usb_recovery_smoke.py && python -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_camera_usb_recovery_smoke`，44 tests passed。
- 通过：`npm test -- --run test/robotControlSummary.test.ts`，13 tests passed；`npm run build` 继续通过，仅保留既有 Vite chunk size warning。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`GET /api/health` 返回 `workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：PC Node 重新启动在 `*:7001`，`GET /api/robot-control/summary` 返回 `normalized_base_url=http://192.168.1.11:8787`、`base_motion_signal_observed=true`、`base_motion_signal_source=imu_attitude_delta`、`base_wheel_feedback_lr_nonzero_proven=false`、`base_wheel_feedback_latest_raw_left=0`、`base_wheel_feedback_latest_raw_right=0`、`camera_usb_speed=480M`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`。
- 通过：真实 summary 读回 `normalized_base_url=http://192.168.1.11:8787`、`map_current_visible=true`、`path_current_visible=true`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`、`wheel_feedback_lr_nonzero_proven=false`、`nav2_goal_execution_proven=false`、`delivery_success=false`。
- 通过：真实 `GET /api/robot-control/map/preview` 返回 `path_preview_status=path_preview_observed`、`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=165`、`route_target_visible=true`、`target={x:0.8,y:0.05,frame_id:map,source:path_preview_points}`，且 `readback_only=true`、`sends_motion_when_clicked=false`。
- 通过：真实 `POST /api/robot-control/base/manual` 前进 `0.08m/s`、`800ms` 返回 `proxy_status=command_forwarded`、`remote_http_status=200`、`feedback_during_motion_t1001_frame_count=80`、`wheel_feedback_latest_raw_left=0`、`wheel_feedback_latest_raw_right=0`、`imu_attitude_delta_observed=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`，`motion_evidence_gaps=["before_after_evidence_snapshot_incomplete","wheel_feedback_lr_nonzero_not_proven"]`，已不再包含 LiDAR delta 缺口。
- 通过：上位机 command debug 同窗口记录 `command_transport=http`、`http_write_returned=true`、`T=11,L/R=255` 和自动 stop `T=11,L/R=0`；feedback debug 后续仍为 `T=1001 L/R=0/0`。
- 通过：相机只读首帧 probe 返回 `probe_total_timeout`、`camera_usb_speed=480M`、`camera_usb_full_speed_detected=false`、`source_diagnosis_not_exclusive=true`；共享 MJPEG status 返回 `shared_capture=true`、`exclusive_camera_claim=false`。
- 通过：上车 `/root/rober/onboard/scripts/camera_usb_recovery_smoke.py --device /dev/video1` 返回 `usb_device=3-1`、`usb_video_speed=480M`、`usb_high_speed_observed=true`、`status=streamon_failed`、`stream_failure_class=high_speed_zero_byte_no_frame`、`next_action=check_usb_cable_port_power_or_known_good_uvc`；服务随后恢复为 active。
- 通过：现场临时把 `/esp32_bridge command_mode` 从 `pwm` 切到 `ros`，PC 手控请求写出 vendor `T=13 X=0.08 Z=0.0` 与 stop `T=13 X=0 Z=0`，随后恢复 `command_mode=pwm`；`T=1001 L/R` 仍为 `0/0`，说明当前 blocker 不在 PC 是否能发命令，而在底盘执行/反馈语义。

## 剩余风险

- 本轮不把 IMU 姿态变化包装成 wheel raw L/R；现场 wheel raw `T=1001 L/R` 仍未证明非零。
- 摄像头仍是 480M 下的首帧 timeout/源头无帧问题，本轮未修复真实图传硬件链路。
- Nav2 目标曾返回 succeeded，但仍缺同窗口 wheel raw 非零和 delivery success；不能宣称完整自动驾驶闭环完成。
- 真实摄像头共享预览软件模型已是单上游多 viewer，`exclusive_camera_claim=false`；但 DV20 在高速 USB 下仍所有 STREAMON 0 字节，需要现场处理 USB 线、接口、供电或 known-good UVC。
