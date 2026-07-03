# PC 地图高度优先大屏与 ROS2 配套回答

## sprint_type

micro

## 实际改动

- 修复 PC 真实地图 PNG 的显示实现：`.plain-map-layer.has-real-map .plain-map-overlay-frame` 从实际生效的宽度优先改为高度优先，按画布高度撑满地图，宽图横向滚动，避免 `261x113` 这类宽地图只占大画布上半截。
- 同步 PC 地图文案、summary 合同和 Vitest 夹具：`map_display_too_small_next_action_plain`、`map_display_companion_plain` 明确“高度优先、宽图横向滚动、默认 100% 完整态势、最高 1200% 局部排障”。
- 同步文档：`pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`、`docs/navigation/fixed_route_workflow.md`。ROS2 配套口径保持：普通用户先用 PC 大地图和 `/map`，本地工程调试用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web；这些工具只观察地图、雷达、TF、路线、定位和 costmap，不替代 PC 简易控制台，不发送底盘运动命令。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- App.test.ts -t "map display|direct map|ROS2|Foxglove|RViz2|plain map" --run`，7 passed。
- 通过：`npm --prefix pc-tools/workstation test -- robotControlSummary.test.ts -t "map display|closure|summary|WYSIWYG|camera|keyboard" --run`，8 passed。
- 通过：`npm --prefix pc-tools/workstation test -- --run`，3 个测试文件 447 passed。
- 通过：`npm --prefix pc-tools/workstation run build`，仅保留 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：PC Node 已用当前代码重启到 `0.0.0.0:7001`，`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
- 通过：`GET /map` HTTP 200；Chrome headless 生成 `/tmp/rober_map_height_first.png`，截图尺寸 `1600x1000`，可见地图画布已吃满 `/map` viewport，高度优先显示路线、雷达点和小车位置。
- 通过：live `GET /api/robot-control/map/preview` 返回地图 `261x113`、`image_data_url_present=true`、`map_png_data_url_present=true`、`robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`radar_overlay_status=loaded`、当前雷达点 `66`。
- 通过：live summary 返回 `map.status=loaded`、`map_current_visible=true`、`path_current_visible=true`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`map_display_default_zoom_percent=100%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`，且新文案包含“真实地图按画布高度优先放大，宽图横向滚动”。
- 通过：短 forward/back/stop 复验 PC 手控链路：forward/back 均 `proxy_status=command_forwarded` 且 `motion_signal_observed=true`，两次 stop 均 `proxy_status=command_forwarded`；最终 summary 为 `keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_wheel_lr_nonzero=false`。
- 通过：上位机 `trashbot-local-webrtc-camera.service` 与 `trashbot-upper-robot-api.service` 均 active；`/dev/video1` 无 owner。固定相机首帧 probe 仍只读失败，summary 回到 `camera_status=source_first_frame_failed`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_input_signal_check_required=true`。
- 续跑通过：PC 页面真实 Chrome/CDP 打开 `http://127.0.0.1:7001/` 后，`data-open-page-live-map-refresh=true`、`data-open-page-live-camera-preview=true`、`data-open-page-keyboard-auto-ready=true`；页面自动触发一次 `POST /api/robot-control/camera/usb-recovery`，DOM 读回 `data-auto-usb-recovery-attempted=true`、`data-auto-usb-recovery-status=streamon_failed`、`data-auto-usb-recovery-frame-observed=false`、`data-auto-usb-recovery-stream-failure-class=high_speed_zero_byte_no_frame`、`data-camera-usb-speed=480M`，证明 PC 已自动做完不发车的软件恢复，但 DV20 仍无首帧。
- 续跑通过：Chrome/CDP 地图 DOM 读回 `plain-map-wysiwyg-view data-state=地图可见`、`data-size=large`、视口盒子约 `1548x862`，`plain-map-preview-image` 存在，`plain-map-route-path data-state=当前路线`，目标点 `plain-map-route-goal-marker data-state=行程未通过`，`plain-map-robot-marker` 存在，雷达 marker 数量 `1`，缩放 `100%`，标题为 `PC 大地图 100% · /map 满屏 · 普通看大地图；工程看 RViz2 / Foxglove`。
- 续跑通过：PC summary 当前读回 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`、`keyboard_ready=true`、`keyboard_continuous_motion_verified=true`，`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_usb_speed=480M`、`camera_hardware_action_required=true`。上位机 8088/8787 均 active，`/api/camera/health` HTTP 200。
- 续跑通过：用 PC 固定代理跑短 `forward/forward/back/back/stop`，四次 manual 均 `proxy_status=command_forwarded` 且 `command_raw_lr_nonzero_proven=true`；summary 保持 `keyboard_continuous_motion_verified=true`、`base_status.motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
- 续跑未通过：同一轮覆盖运动窗口的 `feedback-samples` 仍返回 `wheel_feedback_lr_nonzero_proven=false`、`wheel_feedback_nonzero_observed=false`、`wheel_feedback_latest_raw_left/right=0/0`，不能宣称 WAVE ROVER `T=1001` wheel raw L/R 非零。

## 剩余风险

- 本轮只修 PC 地图显示和 ROS2 配套口径，不改变上车地图源分辨率 `261x113`。
- 实时图传仍未恢复：板端直接 OpenCV/V4L2/GStreamer 矩阵、PC 首帧 probe 都没有拿到 DV20 有效帧；当前结论仍是检查摄像头输入/视频线/接口/供电，或换 known-good UVC 复测，不是页面独占。
- WAVE ROVER `T=1001` wheel raw 仍为 `0/0`；PC 手控有 command raw L/R 非零和 IMU motion signal 证据，但不能声明 wheel raw L/R 非零。
- 完整 Nav2 路线执行和 `delivery_success` 仍未在本轮完成。
