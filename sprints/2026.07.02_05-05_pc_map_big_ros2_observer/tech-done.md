# 2026-07-02 05:05 PC 大地图与 ROS2 观察入口

sprint_type: micro

## 实际改动

- PC 地图默认缩放调整为 `100%` 全图适配，最大细节缩放调整为 `800%`；`/map` 直达页继续保持只看地图大屏，不请求浏览器全屏权限，不发送任何运动命令。
- PC 首页和 `/map` 地图容器高度改为 viewport 友好的主视图，不再用 `8000%/9600%` 造成超宽滚动画布；按钮保留 `适配` 和 `细节放大` 两个普通用户动作。
- `GET /api/robot-control/summary` 和 DOM 新增地图画布合同：`map_display_direct_map_viewport_priority=fullscreen_map_canvas`、`map_display_direct_map_canvas_height_mode=viewport_dominant_full_height`，用于脚本确认地图不是普通小卡片。
- 地图工具行新增 `ROS2观察` 按钮，只展开 RViz2/Foxglove 说明和命令；按钮固定声明不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 文档同步更新 PC 当前有效口径：普通用户优先 PC 大地图或 `/map` 大屏；本地工程调试用 RViz2，远程浏览器观察用项目包装 Foxglove bridge。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- App.test.ts robotControlSummary.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 431 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提醒，不影响本轮地图合同。
- 通过：重启 PC Node 工作站到 `0.0.0.0:7001` 后，`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`。
- 通过：`GET /api/robot-control/summary` 返回 `map_display_default_zoom_percent=100%`、`map_display_max_zoom_percent=800%`、`map_display_direct_map_viewport_priority=fullscreen_map_canvas`、`map_display_direct_map_canvas_height_mode=viewport_dominant_full_height`，且不再包含旧 `特大/8000/9600` 口径。
- 通过：浏览器 smoke 打开 `http://127.0.0.1:7001/map`，`1280x720` viewport 下地图 panel 约 `1280x720`、layer 约 `1272x668`、frame 约 `1270x666`，DOM 显示 `data-map-zoom-percent=100%`、`data-map-state=地图可见`、`data-map-display-ros2-companion-tools=rviz2,foxglove`。

## 剩余风险

- 本轮只改 PC UI、summary 合同、测试和文档；没有真实 RViz2/Foxglove 图形会话截图，也没有真实机器人运动验证。
- RViz2/Foxglove 仍是工程观察配套，不替代 PC 简易界面；需要上车 ROS2 环境已安装对应包。
