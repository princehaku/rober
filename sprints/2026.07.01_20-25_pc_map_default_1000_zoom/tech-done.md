# PC 地图 1000% 默认大图

## sprint_type: micro

## 实际改动

- 将 PC 普通首屏地图和 `/map` 直达大屏默认缩放从 `600%` 提升到 `1000%`，保留 `适配=100%` 全图和 `细节放大=3200%`。
- 同步 `GET /api/robot-control/summary` / `live_closure_summary` 的地图显示 alias：`map_display_default_zoom_percent=1000%`、`map_display_max_zoom_percent=3200%`。
- 同步普通首屏 DOM、summary 合同测试和产品文档，明确 ROS2 配套仍为 RViz2/Foxglove 工程观察，不作为普通用户发车入口。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 190 passed (190)`
- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 232 passed (232)`
- 通过：`npm --prefix pc-tools/workstation run lint`
- 通过：`npm --prefix pc-tools/workstation run build`
  - Vite 仍有既有 chunk size warning，非本轮新增错误。
- 通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`
  - `Tests 422 passed (422)`
- 通过：重启 PC Node 到 `0.0.0.0:7001`，listener PID `29114`。
  - `GET http://127.0.0.1:7001/` 返回 `200`。
  - `GET http://127.0.0.1:7001/map` 返回 `200`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `source_base_url=http://192.168.1.11:8787`、`map_display_default_zoom_percent=1000%`、`map_display_max_zoom_percent=3200%`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。

## 剩余风险

- 本轮只改 PC 显示比例和只读合同，不启动 RViz2/Foxglove，不执行 Nav2/manual/keyboard/free-roam/delivery/stop，也不发 `/cmd_vel`。
