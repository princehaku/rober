# onboard sensor current diagnostics

sprint_type: micro

## 实际改动

- 修正 `onboard/scripts/local_webrtc_camera_smoke.py` 的 `/health` 当前状态优先级：同一个视频源当前首帧失败时，历史 `last_successful_frame` 不再把 `source_observed` 置为 true，避免 PC 看到“当前失败但已观察首帧”的矛盾材料。
- 新增 `onboard/scripts/test_local_webrtc_camera_smoke_health.py`，覆盖 DV20 UVC 当前 `first_frame_total_timeout` 且无其他占用时，health 必须返回 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`。
- 扩展 `onboard/scripts/test_upper_robot_api_free_roam.py`，验证 LiDAR driver 诊断 JSON 的 nested `diagnosis.status` 会展平成 PC 可消费的 `diagnosis_status`，例如 `serial_open_but_no_bytes`。
- 更新 `docs/product/pc_tools_workstation.md`，同步本轮现场只读诊断结论：PC 地图普通用户用本页大地图和 `?view=map`，ROS2 配套建议 RViz2 / Foxglove；相机当前问题按 USB/UVC 无首帧处理，雷达按 WAVE ROVER/STC vendor 资料和 driver diagnostics 排查。
- 2026-06-30 19:42 CST 现场部署到上车端：备份旧文件到 `/root/rober/runtime/deploy_backups/sensor_diag_20260630_194247` 和 `/root/rober/runtime/deploy_backups/upper_api_sensor_diag_20260630_194532`；同步 `local_webrtc_camera_smoke.py`、`o1_lidar_lifecycle.sh`、`lidar_driver.py`、`upper_robot_api.py`；远端重建 `ros2_trashbot_hardware` 并重启 8088 相机服务、8787 upper API、LiDAR lifecycle。该部署未调用任何底盘 motion/control POST，LiDAR lifecycle 只使用 `/dev/ttyACM0`，明确不使用 `/dev/ttyS5` 或 `/cmd_vel`。

## 验证结果

- `python3 -m unittest onboard.scripts.test_local_webrtc_camera_smoke_health onboard.scripts.test_upper_robot_api_free_roam`：通过，6 tests。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/test_local_webrtc_camera_smoke_health.py onboard/scripts/test_upper_robot_api_free_roam.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs`：通过，16 tests。
- `npm test -- --run App.test.ts`（`pc-tools/workstation`）：通过，1 file / 225 tests。
- `git diff --check`：通过。
- 上车端 `python3 -m py_compile /root/rober/onboard/scripts/local_webrtc_camera_smoke.py /root/rober/onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`、`bash -n /root/rober/onboard/scripts/o1_lidar_lifecycle.sh`：通过；`colcon build --symlink-install --packages-select ros2_trashbot_hardware`：通过，1 package finished。
- 上车端相机 `/health`：`status=source_first_frame_failed`、`source_readiness=first_frame_failed`、`source_failure_reason=first_frame_total_timeout`、`source_diagnosis.status=uvc_no_frame_not_exclusive`、`not_exclusive=true`、`last_successful_frame=null`。
- 上车端 LiDAR driver diagnostics：`diagnosis.status=scan_published`，`bytes_read_total=314482`、`packet_count_total=9387`、`published_raw_packet_count=9387`、`published_scan_count=515`；`ros2 topic echo --once /lidar/raw_packet` 和 `/scan` 均成功返回。
- PC 7001 只读刷新：`POST /api/robot-control/radar/scan-proof/refresh` 观测到 `scan_once_observed=true`、`scan_hz_observed=true`、`raw_packet_once_observed=true`、`tf_observed=true`；`GET /api/robot-control/map/preview` 返回 `radar_overlay_status=loaded`、`radar_overlay_point_count=72`、`path_preview_status=path_preview_observed`、`robot_pose_status=map_pose_observed`。
- PC 7001 summary：`readback_summary.radar.status=radar_ready`、`driver_diagnostics_status=scan_published`、`readback_summary.map.radar_overlay_status=loaded`、`radar_overlay_point_count=72`；`live_closure_summary.side_blocker_ids` 已不再包含 `radar_map_points_wysiwyg`。

## 剩余风险

- 本轮没有发送任何 live 运动/control POST；Nav2 完整路线当前仍停在 `needs_wheel_rerun`，需要现场安全确认后重跑图上路线，并在同一个执行窗口复验 wheel L/R 非零。
- 相机不是页面独占，但仍未恢复真实首帧；需要现场检查 DV20 UVC 的 USB、摄像头输入或供电，必要时换 known-good UVC 复测。
- 雷达地图贴图已恢复为 WYSIWYG；但 `radar/scan-proof/refresh` 的汇总状态仍出现“观测项 true 但 status blocked”的字段兼容问题，当前 PC summary 和 map preview 已按 driver diagnostics + map overlay 正确展示，后续可单独修 proof collector 的 blocked reason 归并。
