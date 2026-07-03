# 2026.07.04 07:27 PC camera probe status + map answer

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 新增 PC 侧 `cameraFirstFrameProbeLastFailures` 缓存。
  - 当 `/api/robot-control/camera/first-frame/probe` 返回 `probe_total_timeout`、`probe_failed` 或无首帧材料时，把本次 probe 失败转成 MJPEG status 可消费的 `camera_source_first_frame_failed`。
  - 当真实 MJPEG relay 读到视频 chunk 时清除该 probe 失败，避免成功画面后继续显示旧故障。
  - `camera/mjpeg/status`、summary、live-summary 统一消费 source failure、probe failure 和 relay failure，保证相机服务重启后不会把刚复测出的无帧问题误显示成 `idle_not_started`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 将 `probe_total_timeout`、`probe_process_timeout`、`deadline_expired` 纳入首帧失败集合，保证 summary 诊断口径和 PC 代理一致。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增回归测试：相机服务重启后 health 回到 `source_selected_not_probed` 时，刚刚的 first-frame probe 失败仍会让 `/api/robot-control/camera/mjpeg/status` 显示 `source_first_frame_failed`、`probe_total_timeout`、`uvc_no_frame_not_exclusive` 和“检查摄像头输入/供电后复测”。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`、`OKR.md`、`docs/process/okr_progress_log.md`
  - 同步当前现场口径：普通用户嫌地图小优先用 PC 首页大地图或 `/map`，ROS2 配套是 RViz2 与 Foxglove 只读工程观察；相机当前是高速 USB 但 0 帧，不是 PC 页面独占；该缺口阻塞实时图传和建图视觉验收，不阻塞自由移动/WASD。

## 验证结果

- 代码测试：
  - `npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "keeps recent first-frame probe failure"` 通过，1 passed / 192 skipped。
  - `npm --prefix pc-tools/workstation test -- --run test/catalog.test.ts -t "camera MJPEG status|first-frame probe|USB recovery"` 通过，17 passed / 176 skipped。
  - `npm --prefix pc-tools/workstation run build` 通过，只有 Vite chunk size warning。
- 运行态复验：
  - PC Node 已重启到 `HOST=0.0.0.0 PORT=7001`，`lsof` 显示 `node` 监听 `*:7001`。
  - `GET /api/robot-control/map/preview` 返回地图可见，`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=149`。
  - `GET /api/robot-control/live-summary` 返回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`map_display_default_zoom_percent=800%`、ROS2 配套工具为 `rviz2,foxglove`。
  - `POST /api/robot-control/camera/first-frame/probe` 返回 `proxy_status=probe_failed`、`status=probe_total_timeout`、`frame_observed=false`、`camera_usb_speed=480M`、`camera_hardware_action_label=检查摄像头输入/供电后复测`。
  - probe 后 `GET /api/robot-control/camera/mjpeg/status` 返回 `status=source_first_frame_failed`、`preview_status=source_first_frame_failed`、`source_failure_reason=probe_total_timeout`、`source_diagnosis_status=uvc_no_frame_not_exclusive`，证明重启后 PC 状态不再误报 `idle_not_started`。

## 剩余风险

- DV20 `/dev/video1` 仍没有输出真实首帧。此前上位机 `v4l2-ctl`、ffmpeg、GStreamer、项目 USB recovery smoke 均显示 0 字节或 STREAMON 无帧；当前软件只保证状态表达准确，不能替代现场检查摄像头输入、线材、供电、接口或换 known-good UVC。
- `T=1001 L/R` wheel raw 仍为 `0/0`。PC/WASD 可证明 command raw、stop 和 IMU 动作信号，不可宣称 wheel raw 非零或完整自动驾驶/delivery success 闭环。
- `/map`、RViz2、Foxglove 都是观察入口。RViz2/Foxglove 只建议工程排障使用，不替代 PC 简易控制台，也不发送运动命令。
