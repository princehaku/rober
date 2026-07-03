# PC 大地图与 ROS2 配套 live 复核

## sprint_type

micro

## 实际改动

- 本轮不重复修改 PC 地图功能代码；当前代码已经包含普通用户大地图、`/map` 直达大屏、400% 默认细节视角、1200% 细节放大、45% 适配视角，以及 RViz2 / Foxglove 工程观察入口。
- `docs/process/okr_progress_log.md`：新增本轮 live 复核记录，明确 ROS2 配套工具推荐和当前地图图像/雷达点风险。
- `docs/product/pc_tools_workstation.md`：同步本轮现场口径，说明 PC 简易大地图是普通用户入口，RViz2/Foxglove 只作工程观察，不替代 PC 控制台。

## 验证结果

- `npm test -- test/App.test.ts -t "map display|direct map|ROS2|Foxglove|RViz2|plain map" --run`
  - 通过：1 个 test file，7 tests passed / 233 skipped。
- `npm test -- test/robotControlSummary.test.ts --run`
  - 通过：1 个 test file，15 tests passed。
- `npm run build`
  - 通过；仅保留既有 Vite chunk size warning。
- live 7001 smoke：
  - `GET http://127.0.0.1:7001/map` 返回 `HTTP 200`。
  - `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_default_zoom_percent=400%`、`map_display_primary_url=/map`、`map_display_max_zoom_percent=1200%`，并返回 RViz2 launch、Foxglove websocket `ws://192.168.1.11:8765`；`map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_nav2=false`。
  - summary `readback_summary.map` 返回 `map_current_visible=true`、`path_current_visible=true`、`route_target_visible=true`，路线目标为 `{x:0.8,y:0.05,frame_id:map,source:path_preview_points,source_index:17}`。
  - `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787` 返回 `proxy_status=preview_forwarded`、`width=261`、`height=113`、`robot_pose_status=map_pose_observed`、`path_preview_point_count=18`、`route_target_visible=true`，但 `has_png=false`、`status=loaded_fail_closed_summary`。

## 剩余风险

- 当前 PC UI 尺寸合同已生效，但本轮 live map preview 没拿到 PNG data URL；这不是“地图卡太小”的 UI 问题，而是上车 `/api/map/preview` 这次只返回 fail-closed summary。需要继续复查上车地图 PNG 生成/读取链路。
- 雷达 overlay 当前 `radar_overlay_status=not_current`，current 点数为 `0`，summary 说明旧来源点 `98` 个因 runtime scan stale 被抑制，需先刷新雷达扫描再刷新地图画面。
- ROS2 配套工具建议：本地工程调试用 RViz2 看 `/map`、`/scan`、TF、路径、定位和 costmap；远程浏览器观察用 Foxglove bridge + Foxglove Web。它们只观察，不替代普通 PC 简易控制台，也不发送底盘运动命令。
- 本轮没有执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
