# 2026.07.03 05:30 PC 大地图 400% 与 ROS2 配套口径

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 地图默认缩放从 `300%` 提升到 `400%`，最高细节放大从 `800%` 提升到 `1200%`；`ROS2观察` 继续只展开 RViz2 / Foxglove 观察说明，不启动 ROS2 runtime 或任何运动入口。
- `pc-tools/workstation/src/styles.css`：普通首页驾驶台继续把地图作为主屏，地图列从 `4fr` 提升到 `5fr`，右侧图传/WASD 收紧到 `0.62fr` / `280px`；首页地图卡高度提升到 `clamp(860px, 100vh, 1600px)`，卡内地图画布提升到 `clamp(820px, calc(100vh - 60px), 1500px)`。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 与 `contracts.ts`：summary 顶层和 live closure map display 合同同步返回默认 `400%`、最高 `1200%`，继续暴露 RViz2 launch、Foxglove bridge launch 和 `ws://192.168.1.11:8765`。
- `pc-tools/workstation/test/*`、`pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步当前地图显示和 ROS2 配套合同。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|地图|ROS2|RViz|Foxglove|plain-map"`，结果 `1 file / 4 tests passed / 233 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`，结果 `2 files / 195 tests passed`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts`，结果 `1 file / 237 tests passed`。
- 通过：`cd pc-tools/workstation && npm run build`，`tsc`、`vite build` 和 server `tsc` 成功；仍有既有 Vite large chunk warning。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，新 PID `63986`；`GET /` 和 `GET /map` 均返回 `200 OK`。
- 通过：live `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_primary_url=/map`、`map_display_default_zoom_percent=400%`、`map_display_max_zoom_percent=1200%`、`map_display_engineering_tools_action_label=工程观察：RViz2 / Foxglove`、RViz2/Foxglove 命令齐全，且 `map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_foxglove=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。
- 通过：live `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、地图 `261x113`、`robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`、`target={x:0.8,y:0.05,frame_id=map}`、`radar_overlay_status=loaded`、`radar_overlay_point_count=98`。

## 剩余风险

- 本轮只解决 PC 地图显示面积和 ROS2 配套入口口径；没有启动真实 RViz2 GUI，也没有启动 Foxglove bridge 做浏览器远程观察。
- 真实地图源图仍是上车端 preview 的低分辨率图像，本轮通过更大的 PC 画布和缩放改善可视性，不改变 ROS2 地图质量。
- 仓库里既有两个 2026.06.11 artifact 脏文件，本轮未修改也不纳入提交。
