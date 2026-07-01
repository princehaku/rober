# sprint_type: micro

## 实际改动

- PC 普通页顶栏新增“地图大屏”主入口，固定打开 `/map`，让用户不必先在地图卡内部寻找入口。
- 顶栏入口声明只切换地图观察页面，不启动 ROS2、RViz2、Foxglove、Nav2、建图 runtime，也不发送任何运动命令。
- 更新地图大屏入口样式、前端 DOM 合同测试和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- 通过：`npm test -- --run App.test.ts robotControlSummary.test.ts catalog.test.ts`，3 个测试文件、428 个用例通过。
- 通过：`npm run lint`。
- 通过：`npm run build`。
- 通过：`git diff --check`。
- 通过：PC Node 输出 `pc-tools workstation API listening on http://0.0.0.0:7001`，`lsof` 确认 `TCP *:7001 (LISTEN)`。
- 通过：`curl -fsS http://127.0.0.1:7001/` 和 `curl -fsS http://127.0.0.1:7001/map` 均返回当前构建的前端资源。
- 通过：`curl -fsS http://127.0.0.1:7001/api/robot-control/summary` 读到 `map_display_primary_url=/map`、`map_display_default_zoom_percent=1600%`、`map_display_max_zoom_percent=4800%`，且 `map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_foxglove=false`、`map_display_starts_nav2=false`、`map_display_starts_map_runtime=false`。
- 通过：内置浏览器 DOM 检查首页 `topbar-map-direct-link` 文案为“地图大屏”、`href=/map`、`data-sends-motion-when-clicked=false`、`data-starts-ros2=false`、`data-starts-nav2=false`；`/map` 页面 `plain-map-panel` 为 `data-direct-map-view-requested=true`、`data-size=fullscreen`、`data-map-zoom-percent=1600%`、`data-direct-map-starts-radar-lifecycle-on-enter=false`。

## 剩余风险

- 本轮改动仅提升 PC 地图入口易用性；真实 Nav2 行程、键盘连续手控、相机首帧和自由移动实车闭环仍需继续按目标验收。
