# PC 地图默认 150% 可读大图

## sprint_type

micro

## 实际改动

- 将 PC 普通首页和 `/map` 直达页的地图默认缩放从 `100%` 完整态势改为 `150%` 可读大图；`完整态势` 仍回到 `100%`，`细节放大` 仍到 `1200%`。
- 同步 `GET /api/robot-control/summary` / `live_closure_summary` 地图显示合同：`map_display_default_zoom_percent=150%`、`map_display_direct_map_default_zoom_percent=150%`、`map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=1200%`。
- 保留 ROS2 配套答案：普通用户继续用 PC 大地图和 `/map`；RViz2 用于本地工程观察，Foxglove bridge + Foxglove Web 用于远程浏览器观察，二者不替代普通简易控制台。
- 更新 PC workstation 和自由移动建图产品文档，明确 2026-07-04 02:35 CST 起当前有效地图口径。

## 验证结果

- 已通过：`npm test -- --run test/App.test.ts -t "direct map"`。
- 已通过：`npm test -- --run test/App.test.ts -t "map"`。
- 已通过：`npm test -- --run test/robotControlSummary.test.ts`。
- 已通过：`npm test`，结果 `3 passed (3)`、`447 passed (447)`。
- 已通过：`npm run build`；仅有既有 Vite chunk size warning。
- 已通过：`git diff --check`。
- 已部署本机 PC Node：`HOST=0.0.0.0 PORT=7001 npm run api`，`lsof` 显示 `TCP *:7001 (LISTEN)`。
- live summary 读回：`map_display_default_zoom_percent=150%`、`map_display_direct_map_default_zoom_percent=150%`、
  `map_current_visible=true`、`path_current_visible=true`、`route_target_visible=true`、
  `robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_map_points_visible=true`、
  `radar_overlay_current_point_count=27`。

## 剩余风险

- 该 sprint 只修改 PC 地图默认显示缩放和 ROS2 配套说明，不修复相机首帧、wheel raw L/R 仍为 `0/0` 或真实 Nav2 HIL 缺口。
- 浏览器截图仍依赖本机浏览器工具可用性；若截图工具不可用，以 Vitest DOM 合同和 live summary 读回作为本轮软件验证边界。
