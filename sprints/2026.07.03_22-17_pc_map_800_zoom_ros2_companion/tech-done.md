# PC 地图默认 800% 与 ROS2 配套说明

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 首页和 `/map` 直达页默认地图缩放从 `400%` 提到 `800%`，保留 `适配=45%` 和 `细节放大=1200%`，继续固定 RViz2 / Foxglove 只是工程观察，不自动启动 ROS2 或发车。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`：summary 顶层、live closure 和类型合同同步改为 `map_display_default_zoom_percent=800%`、`map_display_direct_map_default_zoom_percent=800%`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：更新 DOM/API 合同断言，锁定默认 `800%`、最高 `1200%` 和 RViz2/Foxglove 只读边界。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步当前“地图太小/ROS2 配套”口径，普通用户默认用 PC 大地图或 `/map`，本机工程观察用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "opens direct map view|renders Robot Control V1 by default"`，2 passed / 238 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，15 passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "Robot Control summary proxies Robot API readback endpoints|workstation live-summary route exposes"`，2 passed / 186 skipped。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript/Vite 构建通过；仅保留 Vite 大 chunk 提示。
- 通过：重启本机 PC Node 后 `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `*:7001`，`curl -I http://127.0.0.1:7001/map` 返回 `HTTP/1.1 200 OK`。
- 通过：只读 live summary 回读 `map_display_default_zoom_percent=800%`、`map_display_direct_map_default_zoom_percent=800%`、`map_display_fit_zoom_percent=45%`、`map_display_max_zoom_percent=1200%`，并保留 `map_display_ros2_companion_tools=["rviz2","foxglove"]`、RViz2 launch、Foxglove bridge launch 和 `ws://192.168.1.11:8765`。
- 通过：执行既有 no-motion 雷达 proof 刷新后，`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 回读 `map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、`route_target_state=path_preview_goal_observed`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=75`、`keyboard_continuous_motion_verified=true`。

## 剩余风险

- 本轮只改 PC 地图显示比例和 ROS2 配套说明，不启动 RViz2/Foxglove，不验证真实 Nav2 运动、delivery success、wheel raw L/R 非零或相机首帧。
- `800%` 会更强调局部细节；需要看全局路线时必须点 `适配` 回到 `45%`。
