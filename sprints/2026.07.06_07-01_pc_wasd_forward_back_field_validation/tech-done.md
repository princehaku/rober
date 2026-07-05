# PC WASD Forward Back Field Validation

## sprint_type

micro

## 实际改动

- 本轮不改产品代码；沿用已运行的 PC 工作站 `0.0.0.0:7001` 和默认上位机 `http://192.168.1.11:8787`。
- 通过 PC Node 固定代理现场复验 forward/back 低速短脉冲和 stop，确认 PC 手控入口可继续服务普通用户。
- 更新 `docs/product/pc_tools_workstation.md`，记录本轮 PC 手控、ROS bridge raw 命令、IMU 运动信号和 WAVE ROVER wheel raw 风险边界。

## 验证结果

- `GET http://127.0.0.1:7001/api/health` 返回 `host=0.0.0.0`、`port=7001`、`robot=http://192.168.1.11:8787`。
- 上位机 `trashbot-upper-robot-api.service` 和 `trashbot-local-webrtc-camera.service` 均为 `active`；`0.0.0.0:8787`、`0.0.0.0:8088` 监听正常；`/dev/video1` 无其他进程占用。
- `GET /api/robot-control/live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`map_display_default_zoom_percent=300%`、`map_display_max_zoom_percent=4800%`，并给出 `工程观察：RViz2 / Foxglove` 的 ROS2 配套入口说明。
- `POST /api/robot-control/base/manual` forward：`proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=164/164`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
- `POST /api/robot-control/base/manual` back：`proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`command_raw_lr_nonzero_proven=true`、`command_raw_latest_left/right=-164/-164`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
- `POST /api/robot-control/base/stop` 返回 `proxy_status=command_forwarded`、`status=stopped`。
- 带页面本地按住证据的 `GET /api/robot-control/live-summary` 返回 `keyboard_motion_verified=true`、`keyboard_continuous_motion_verified=true`、`keyboard_command_raw_motion_verified=true`、`keyboard_command_raw_lr_nonzero_proven=true`、`keyboard_continuous_forwarded_pulses=2`。

## 剩余风险

- WAVE ROVER `T=1001` wheel raw 反馈仍为 `0/0`，所以当前只证明 PC/WASD/ROS bridge/底盘命令 raw 和 IMU 运动信号，不声明 wheel raw L/R 非零闭环完成。
- 实时图传仍未恢复真实帧；当前诊断仍指向 `uvc_no_frame_not_exclusive` / `high_speed_zero_byte_no_frame`，需要检查 DV20 输入、线材/接口/供电或更换 known-good UVC 复测。
- ROS2 配套工具口径：普通用户继续用 PC 大地图和 `/map`；本地工程调试看 RViz2，远程浏览器大屏观察可接 Foxglove bridge + Foxglove Web。
