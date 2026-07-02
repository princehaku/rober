# 2026.07.03 00:26 ROS cmd_vel 与地图终点读回

sprint_type: micro

## 实际改动

- 上车 `onboard/scripts/upper_robot_api.py` 的 ROS `/cmd_vel` 一次性发布默认超时从 `2s` 提到 `10s`，并显式设置 `RMW_FASTRTPS_USE_SHM=0`、`--wait-matching-subscriptions 0`、`--keep-alive 0.1`，避免 Orange Pi 现场 FastDDS SHM 历史锁文件让 `ros2 topic pub --once` 卡死。
- PC `GET /api/robot-control/map/preview` 新增 `target`、`route_target_state`、`route_target_visible`、`route_target_source`，从同一轮 map frame `path_preview_points` 的最后一个点派生路线终点。
- 同步更新 PC/API 单测、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md` 和 `docs/navigation/field_route_evidence_preflight.md`。硬件/协议说明采用 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`。

## 验证结果

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_ros_cmd_vel_publish_disables_fastrtps_shm_and_zero_wait onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_manual_control_default_motion_window_tracks_pulse_duration onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_manual_control_ros_persists_fresh_bridge_feedback_without_opening_uart`：3 tests OK。
- `cd pc-tools/workstation && npm test -- robotControlSummary.test.ts`：10 tests OK。
- `cd pc-tools/workstation && npm test -- catalog.test.ts`：184 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍有 chunk size warning。
- `cd pc-tools/workstation && npm test -- App.test.ts -t "draws the current route from map preview points when summary route coordinates are missing"`：1 test OK。
- 已部署到 `root@192.168.1.11 -p 7878`，车端备份 `/root/rober/runtime/deploy_backups/upper_api_ros_cmd_vel_inline_20260703_002513`，重启后 `GET /api/health` 返回 ready。
- 真实 ROS 手控验证：`POST http://192.168.1.11:8787/api/base/manual`，`command_mode=ros`、`duration_ms=300`，返回 `command_result.ok=true`、`stop_result.ok=true`、`manual_command_executed=true`、`auto_stop_executed=true`。
- PC 7001 已重启到 `0.0.0.0:7001`；`GET /api/robot-control/map/preview` 返回 `proxy_status=preview_forwarded`、`target={x:0.8,y:0.05,frame_id=map,source=path_preview_points,source_index=17}`、`path_preview_point_count=18`、`radar_overlay_status=loaded`、`radar_overlay_point_count=3`、`robot_pose_status=map_pose_observed`。

## 剩余风险

- 相机仍不可见，车端 `/api/camera/health` 诊断为 `uvc_full_speed_usb_not_exclusive`，`not_exclusive=true`，USB speed 为 `12M`，不是 PC 页面独占；下一步需要换高速 USB 口/线或带供电 Hub 后复测。
- Wheel raw L/R 仍未非零：ROS 手控后 bridge debug 读到 T1001，但 `wheel_feedback_lr_nonzero_proven=false`、latest L/R 为 `0/0`。这可能是 WAVE ROVER feedback 字段口径、底盘固件反馈或当前短脉冲窗口问题，尚未证明完整 Nav2 路线执行成功。
- `ros2 topic pub` stop 命令仍可能打印 FastDDS SHM 历史锁警告，但 returncode 为 `0`，不再阻塞 API；后续可评估清理 `/dev/shm/fastdds_*` 或切换 DDS 配置。
