# PC 开机 runtime 服务与 ROS2 地图配套收口

sprint_type: micro

## 实际改动

- 新增 `onboard/scripts/esp32_bridge_http.sh`：上位机开机后自动恢复 `/cmd_vel -> esp32_bridge -> WAVE ROVER HTTP` 链路，启动前清理脱管 `esp32_bridge`，避免 PC WASD 出现多个订阅者。
- 新增 `onboard/systemd/trashbot-esp32-bridge.service`：systemd 托管 PC WASD/Nav2 底盘桥接，默认 `/dev/ttyS5 @ 115200`、HTTP `http://192.168.1.3`、PWM164。
- 新增 `onboard/systemd/trashbot-lidar-lifecycle.service`：systemd 托管 LiDAR lifecycle，默认 `/dev/ttyACM0 @ 150000`，用于 PC 大地图当前雷达贴图。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/process/okr_progress_log.md` 和 `OKR.md`：记录开机自恢复、相机 CMA 复测结论、ROS2 地图配套口径和 O7 进度。

## 验证结果

- `bash -n onboard/scripts/esp32_bridge_http.sh onboard/scripts/o1_lidar_lifecycle.sh`：通过。
- 上位机部署：`systemctl enable/start/restart trashbot-esp32-bridge.service trashbot-lidar-lifecycle.service` 完成，两个服务均为 `enabled`、`active`。
- 上位机 ROS 图：`ros2 node list` 读到 `/esp32_bridge` 与 `/lidar_driver`；`ros2 topic info /cmd_vel -v` 显示 publisher 1、subscription 1，唯一订阅者为 `esp32_bridge`。
- 上位机雷达：`ros2 topic echo --once /scan --no-arr` 读到 `frame_id=laser_frame`、`ranges` 长度 155 的 LaserScan。
- PC live-summary：`status=ready_for_motion`，`map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`，地图默认 `800%`，ROS2 配套工具为 `rviz2,foxglove`。
- PC map preview：`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`route_target_visible=true`、`radar_overlay_status=loaded`、`radar_overlay_wysiwyg_complete=true`。
- PC 相机 status：`status=source_first_frame_failed`、`source_diagnosis_status=uvc_no_frame_not_exclusive`、`first_frame_failure_reason=first_frame_total_timeout`、`camera_usb_speed=480M`、`cma_memory_diagnostics_status=cma_available_no_recent_failure`、`camera_blocks_free_move=false`、`camera_blocks_mapping_start=true`。
- PC 前进/后退短脉冲：均返回 `proxy_status=command_forwarded`、`base_command_mode=ros`、`command_raw_lr_nonzero_proven=true`、`motion_signal_observed=true`、`motion_evidence_complete=true`；前进 command raw 为 `164/164`，后退 command raw 为 `-164/-164`。

## 剩余风险

- wheel feedback 仍为 vendor `T=1001 L/R=0/0`，本轮不能宣称 wheel raw 非零、HIL 闭环或 delivery success。
- 重启后 CMA 已恢复，但 DV20 仍没有真实首帧；下一步应检查上游视频输入、摄像头/采集卡、视频线、接口、供电，或换 known-good UVC。
- 本轮没有执行完整 Nav2 路线 HIL、delivery success、真实 RTC/视频、ASR/TTS、云端回放或标注数据流。
- ROS2 配套结论是：本地工程观察用 RViz2/Nav2 RViz 配置，远程浏览器观察用 Foxglove bridge + Foxglove Web；普通用户仍使用 PC 大地图和 `/map`，不把 RViz2/Foxglove 当发车入口。
