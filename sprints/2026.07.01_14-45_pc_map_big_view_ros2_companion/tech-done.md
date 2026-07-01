# PC 地图大视图与 ROS2 配套口径

sprint_type: micro

## 实际改动

- PC 普通首屏和 `/map` 直达地图的默认细节缩放从 `400%` 提升到 `600%`，仍保留“适配”回到 `100%` 和“细节放大”到 `2400%`。
- 地图画布默认高度、只看地图模式和 `/map` 直达页高度进一步放大，避免地图在 PC 上退回小卡片。
- `live_closure_summary`、普通首屏 DOM 测试和产品文档同步更新当前地图合同：普通用户优先用 PC 大地图，ROS2 配套只作为工程观察，RViz2 看本机 `/map`、`/scan`、TF、路线、定位和 costmap，Foxglove 用于 bridge 部署后的浏览器观察。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|map display|ROS2"`，1 file passed，3 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts -t "map display|live closure"`，1 file passed，1 test passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，418 tests passed。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `0.0.0.0:7001`；`HEAD http://127.0.0.1:7001/map` 返回 `200`，`GET /api/robot-control/live-summary` 返回 `map_display_default_zoom_percent=600%`、`map_display_max_zoom_percent=2400%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`。

## 剩余风险

- 本轮只改变 PC 地图显示和 ROS2 配套说明，不启动 RViz2/Foxglove，不执行 Nav2，不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 真实地图是否足够清晰仍取决于上车端 `/api/map/preview` 返回的 PGM/YAML 分辨率；若源图本身太低，PC 只能放大显示，不能补出更多地图细节。
