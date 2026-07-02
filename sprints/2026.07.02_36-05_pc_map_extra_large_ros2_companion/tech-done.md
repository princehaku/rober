# PC 特大地图与 ROS2 配套说明

## sprint_type

micro

## 实际改动

- 将 PC 普通地图和 `/map` 直达地图的默认缩放从 `3200%` 提升到 `4800%`，细节放大上限从 `6400%` 提升到 `9600%`；`适配` 仍回到 `100%` 全图。
- 普通地图标题从 `PC 大地图` 改为 `PC 特大地图`，短句改为 `普通看 PC 特大图；工程看 RViz2 / Foxglove`。
- `GET /api/robot-control/summary` 和 `live_closure_summary` 的地图显示 alias 同步更新为 `map_display_default_zoom_percent=4800%`、`map_display_max_zoom_percent=9600%`，并明确普通用户默认使用 PC 特大地图和 `/map`。
- ROS2 配套口径保持不变：RViz2 用于本地工程观察，Foxglove bridge + Foxglove Web 用于远程浏览器观察；这些入口只看 `/map`、`/scan`、TF、路径、定位和 costmap，不启动 Nav2/建图 runtime，也不发送 `/cmd_vel`。
- 同步更新 `docs/product/pc_tools_workstation.md` 和 PC 工作站测试断言。

## 验证结果

- `npm test -- test/App.test.ts`
  - 结果：通过，`237 passed`。
- `npm test -- test/robotControlSummary.test.ts`
  - 结果：通过，`10 passed`。
- `npm test -- test/catalog.test.ts`
  - 结果：通过，`183 passed`。
- `npm run build`
  - 结果：通过，Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告。
- `git diff --check`
  - 结果：通过，无空白错误。
- 7001 live 只读验证：
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 Node 监听 `*:7001`，PID `14785`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `map_display_default_zoom_percent=4800%`、`map_display_max_zoom_percent=9600%`、`map_display_primary_url=/map`、`map_display_sends_motion_when_clicked=false`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。
  - `curl -I http://127.0.0.1:7001/map` 返回 HTTP `200 OK`。

## 剩余风险

- 本轮只改 PC 地图显示和只读说明，不做真车运动验证，不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- RViz2/Foxglove 是工程观察配套，不替代普通用户 PC 简易界面；真实远程多人观察仍需要现场启动 `foxglove_bridge`。
