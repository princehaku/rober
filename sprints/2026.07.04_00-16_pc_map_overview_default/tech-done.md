# PC 地图默认完整态势

sprint_type: micro

## 实际改动

- PC 首页和 `/map` 的地图默认缩放统一为 `100%` 完整态势，`细节放大` 保留为 `1200%` 局部排障入口，`完整态势` 回到全局视角。
- `GET /api/robot-control/summary` / `live_closure_summary` / 共享 contract 同步暴露 `map_display_default_zoom_percent=100%`、`map_display_direct_map_default_zoom_percent=100%`、`map_display_fit_zoom_percent=100%`。
- 普通用户口径保持 PC 大地图优先；ROS2 配套只作为工程观察：本地 RViz2，远程 Foxglove bridge + Foxglove Web，不替代简易控制台，也不发送 `/cmd_vel` 或 Nav2/manual/stop。
- 同步更新 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md` 和 `docs/product/pc_free_roam_mapping_design.md` 的当前有效口径。
- 因本轮未改 WAVE ROVER/ESP32/UART 控制逻辑，仅沿用硬件事实边界；硬件资料入口已按项目纪律核对 `docs/vendor/VENDOR_INDEX.md`。

## 验证结果

- `npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts`
  - 结果：通过，`Test Files 3 passed`，`Tests 447 passed`。
- `npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- PC Node 重启验证
  - 结果：`node` 监听 `*:7001`。
  - `/map` 返回 `HTTP/1.1 200 OK`。
- 现场只读 summary smoke：`GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`
  - `map_display_default_zoom_percent=100%`
  - `map_display_direct_map_default_zoom_percent=100%`
  - `map_display_fit_zoom_percent=100%`
  - `map_display_max_zoom_percent=1200%`
  - `map_preview_status=loaded`
  - `path_preview_point_count=18`
  - `radar_overlay_status=loaded`
  - `radar_overlay_current_point_count=192`
  - `robot_pose_status=map_pose_observed`
  - `route_target_visible=true`
  - `keyboard_continuous_motion_verified=true`

## 剩余风险

- 当前相机仍为 `source_first_frame_failed`，且 `camera_input_signal_check_required=true`；本轮地图完整态势修复不解决摄像头首帧硬件/输入信号问题。
- 本轮 live smoke 是只读 summary 与 `/map` HTTP 验证，没有执行 Nav2、manual、keyboard pulse、delivery complete 或 stop。
