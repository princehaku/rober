# PC Runtime Map + WASD + Camera Check

## sprint_type

micro

## 实际改动

- `docs/product/pc_tools_workstation.md`：同步 2026-07-03 19:56 CST 现场运行证据，明确 PC 7001、上位机 8787/8088、地图大屏四层、WASD forward/back 短脉冲和相机无帧的当前状态。
- 本轮未改产品代码；重点是现场复核、no-motion 刷新雷达贴图、尝试相机恢复、验证 PC manual/WASD 底层链路。

## 验证结果

- 通过：PC Node `GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：上位机 `ssh root@192.168.1.11 -p 7878` 可连；`trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 均 active；`0.0.0.0:8787` 和 `0.0.0.0:8088` 均监听。
- 通过：雷达 no-motion 刷新后 `GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_current_point_count=191`、`path_preview_point_count=18`、`robot_pose.frame_id=map`、`route_target_visible=true`、目标点来自 path 末点 `(0.8,0.05,map)`。
- 通过：PC fixed manual 代理短脉冲验证 forward/back：两次 `/api/robot-control/base/manual` 均 `command_forwarded`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`；两次 `/api/robot-control/base/stop` 均 `command_forwarded`。
- 未通过但已定位：`GET http://192.168.1.11:8088/mjpeg` 返回 `503 first_frame_total_timeout`；`POST /api/robot-control/camera/usb-recovery` 返回 `streamon_failed/high_speed_zero_byte_no_frame`；PC summary 继续显示 `camera_current_visible=false`、`camera_hardware_action_required=true`、`camera_label=检查摄像头输入/供电后复测`。

## 剩余风险

- 实时图传仍无真实首帧；当前证据指向 DV20 摄像头输入、USB 线/接口/供电或设备本体，非 PC 页面独占。
- WAVE ROVER wheel raw `L/R` 仍为 `0/0`，只能证明 PC -> Robot API -> ROS/manual -> stop 链路和 IMU 运动信号，不能证明编码器轮速非零。
- delivery success 和完整 Nav2 真实复跑本轮未收口。
