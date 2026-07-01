# PC 地图标题大屏提示与 ROS2 配套回答

sprint_type: micro

## 实际改动

- 普通首屏地图标题旁新增 `plain-map-heading-proof` 只读状态标识，直接显示 `PC 大地图 <当前缩放> · /map 满屏`，让现场反馈地图太小时先看到 PC `/map` 大屏入口。
- 该标识同步暴露 `/map`、`pc_big_map`、`rviz2,foxglove` 和不发车边界；ROS2 配套仍只作为工程观察，不替代普通用户 PC 地图。
- 产品文档同步说明：普通用户先用 PC `/map` 大地图；RViz2 看 `/map`、`/scan`、TF、路径、定位和 costmap，Foxglove 用 bridge 后的浏览器观察。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map display|direct map|ROS2"`，1 file passed，3 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，420 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`；`HEAD http://127.0.0.1:7001/map` 返回 `200`，`GET /api/robot-control/live-summary` 返回 `map_display_primary_tool=pc_big_map`、`map_display_primary_url=/map`、`map_display_default_zoom_percent=600%`、`map_display_max_zoom_percent=2400%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、`map_display_direct_map_keeps_page_fullscreen_without_browser_api=true`、`map_current_visible=true`、`path_current_visible=true`、`free_move_start_ready=true`。

## 剩余风险

- 当前只读 live-summary 显示 `radar_overlay_status=not_current` 且 `radar_map_points_visible=false`；本轮没有自动刷新雷达 proof，因为用户反馈点是地图尺寸和 ROS2 配套说明，不应把验证扩大成传感器刷新。
- 本轮只改 PC 显示提示、测试和文档，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
