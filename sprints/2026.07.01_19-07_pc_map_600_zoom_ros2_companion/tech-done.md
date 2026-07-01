# PC 地图 600% 默认大图与 ROS2 配套口径

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图和 `/map` 直达大屏默认缩放从 `400%` 提升到 `600%`。
  - 细节放大上限从 `2400%` 提升到 `3200%`，`适配` 仍固定回到 `100%` 全图。
  - 保持 ROS2 工程观察折叠入口：RViz2 看 `/map`、`/scan`、TF、路径、定位和 costmap；Foxglove 用于 bridge 后浏览器观察。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - 同步 summary 顶层 alias 和 live closure contract：`map_display_default_zoom_percent=600%`、`map_display_max_zoom_percent=3200%`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 更新 PC 地图 DOM、直达 `/map`、summary API、缩放按钮和 ROS2 配套合同断言。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步当前有效口径：普通用户优先 `/map` PC 大地图；ROS2 配套使用 RViz2 / Foxglove，但不作为普通用户发车入口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "map view|map display|direct map|plain map|Robot Control V1"`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，9 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 大 chunk warning 为既有提示，构建成功。
- 通过：`cd pc-tools/workstation && npm test -- --run`，3 files passed，421 tests passed。
- 通过：`git diff --check`。
- 通过：7001 重启后 `lsof` 显示 `node` PID `79604` 监听 `TCP *:7001`。
- 通过：`HEAD http://127.0.0.1:7001/` 与 `HEAD http://127.0.0.1:7001/map` 均返回 `200 OK`。
- 通过：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `map_display_default_zoom_percent=600%`、`map_display_max_zoom_percent=3200%`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`，且 `map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。
- 通过：静态 bundle `index-CH8aM4Uc.js` 包含 `600%`、`3200%`、`RViz2`、`Foxglove` 和 `进入地图大屏`。
- 注意：两次 catalog pattern 过窄导致 skipped，未作为通过证据；最终以全量 `npm test -- --run` 覆盖 catalog。

## 剩余风险

- 本轮只改变 PC 地图显示和 ROS2 配套说明，不启动 RViz2/Foxglove，不启动 ROS2/Nav2/建图 runtime，不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实现场视觉效果仍需要在 7001 页面和 `/map` 大屏上肉眼复核。
