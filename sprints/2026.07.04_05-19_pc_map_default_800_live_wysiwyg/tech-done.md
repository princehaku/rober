# PC 地图默认 800% 大图 micro sprint

## sprint_type

micro

## 实际改动

- 将 PC 普通首页和 `/map` 直达大屏的默认地图缩放从 `400%` 提升到 `800%`，把 `细节放大` 上限从 `1600%` 提升到 `3200%`。
- 同步更新前端 DOM 断言、summary/live-summary 合同、共享 TypeScript literal 类型和 CSS 注释，确保实际画布比例、读回字段和测试合同一致。
- 更新 `docs/product/pc_tools_workstation.md` 当前有效口径：普通用户继续使用 PC 大地图和 `/map`；RViz2/Foxglove 只作为工程观察入口，不替代简易控制台，不发送运动命令。

## 验证结果

- 通过：`npm test -- test/App.test.ts -t "map display|direct map|ROS2|Foxglove|RViz2|plain map" --run`
  - `7 passed / 234 skipped`
- 通过：`npm test -- test/catalog.test.ts -t "map display|map preview|direct map|ROS2|Foxglove|RViz2" --run`
  - `4 passed / 188 skipped`
- 通过：`npm test -- test/robotControlSummary.test.ts --run`
  - `16 passed`
- 通过：`npm run build`
  - Vite 仍有既有 large chunk warning，构建成功。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，`curl -fsSI http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：`GET /api/robot-control/live-summary` 读回：
  - `map_display_default_zoom_percent=800%`
  - `map_display_direct_map_default_zoom_percent=800%`
  - `map_display_max_zoom_percent=3200%`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `route_target_current_visible=true`
  - `radar_map_points_current_visible=true`
  - `keyboard_motion_verified=true`
  - `keyboard_continuous_motion_verified=true`
  - `keyboard_command_raw_lr_nonzero_proven=true`
  - `delivery_success=true`
- 通过：`GET /api/robot-control/map/preview` 读回底图 PNG、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=173`。

## 剩余风险

- 实时图传仍未完成：触发共享 MJPEG 后返回 `502/0 bytes`，`/api/robot-control/camera/mjpeg/status` 和 live-summary 读回 `source_first_frame_failed / uvc_no_frame_not_exclusive`、`first_frame_total_timeout`、`camera_hardware_action_required=true`、`camera_input_signal_check_required=true`。当前证据说明 PC 页面、共享预览和独占问题不是主因，剩余仍是 DV20/UVC 输入信号、线材、接口、供电或 known-good UVC 复测。
- `wheel_lr_nonzero_proven=false` 仍未消除；本轮 WASD 证据来自连续手控命令非零和运动信号，不能冒充 WAVE ROVER `T=1001 L/R` 非零。
