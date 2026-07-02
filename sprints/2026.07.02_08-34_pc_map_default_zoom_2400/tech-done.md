# PC Map Default Zoom 2400

## sprint_type

micro

## 实际改动

- 将 PC 普通地图和 `/map` 直达大屏的默认缩放从 `1600%` 提升到 `2400%`，最高细节放大继续保持 `4800%`，`适配` 仍回到 `100%` 全图。
- 同步更新 `GET /api/robot-control/summary` 顶层地图显示 alias 和 `live_closure_summary`，让现场脚本能直接读到 `map_display_default_zoom_percent=2400%`。
- 保持 ROS2 配套分层：普通用户默认使用 PC `/map` 大地图；本地工程观察用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web；这些入口只观察地图、雷达、TF、路径、定位和 costmap，不作为发车入口。
- 同步更新 PC DOM 测试、summary 测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`，2 个 test files、247 个测试通过。
- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts catalog.test.ts`，3 个 test files、428 个测试通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，PID `76143`；`lsof` 显示 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/api/robot-control/summary` 读回 `map_display_primary_url=/map`、`map_display_default_zoom_percent=2400%`、`map_display_max_zoom_percent=4800%`、`map_display_ros2_companion_tools=["rviz2","foxglove"]`、`map_display_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。
- 通过：`curl -fsSI http://127.0.0.1:7001/` 和 `curl -fsSI http://127.0.0.1:7001/map` 均返回 `200 text/html; charset=utf-8`。

## 剩余风险

- 本轮只改变 PC 显示默认缩放和只读说明，不启动 RViz2/Foxglove/ROS2 runtime，不执行 Nav2、建图 runtime、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实地图细节是否足够大还取决于现场屏幕分辨率和浏览器缩放；如果仍嫌小，可继续用 `+` 或 `细节放大` 到 `4800%`。
