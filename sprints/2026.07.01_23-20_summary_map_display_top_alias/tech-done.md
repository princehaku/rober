# Summary 顶层地图大屏 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增地图易用性 alias：
  - `map_display_primary_url=/map`
  - `map_display_legacy_url=?view=map`
  - `map_display_default_zoom_percent=150%`
  - `map_display_max_zoom_percent=2400%`
  - `map_display_ros2_companion_required=false`
  - `map_display_ros2_companion_tools=[rviz2,foxglove]`
  - `map_display_companion_plain`
  - `map_display_sends_motion_when_clicked=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_rviz2=false`
  - `map_display_starts_foxglove=false`
  - `map_display_starts_nav2=false`
  - `map_display_starts_map_runtime=false`
- 这些字段与 `live_closure_summary` 同源，只是把“PC 地图太小该去哪里看、ROS2 配套是什么、是否会发车”放到最常用的 summary 顶层。
- 同步更新 shared contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `52020`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `map_display_primary_url=/map`
  - `map_display_legacy_url=?view=map`
  - `map_display_default_zoom_percent=150%`
  - `map_display_max_zoom_percent=2400%`
  - `map_display_ros2_companion_required=false`
  - `map_display_ros2_companion_tools=["rviz2","foxglove"]`
  - `map_display_sends_motion_when_clicked=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_rviz2=false`
  - `map_display_starts_foxglove=false`
  - `map_display_starts_nav2=false`
  - `map_display_starts_map_runtime=false`

## 剩余风险

- 本轮只修 summary 顶层脚本读数和地图入口可发现性，不改变地图坐标、路线、小车位置、雷达点贴图逻辑。
- ROS2/RViz2/Foxglove 仍只是工程观察配套，本轮不启动这些进程。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
