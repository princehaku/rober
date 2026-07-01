# 2026-07-02 05:05 PC 地图大屏与 ROS2 观察入口

sprint_type: micro

## 实际改动

- PC 地图默认缩放从 `1000%` 提升到 `1600%`，最大细节缩放从 `3200%` 提升到 `4800%`；`/map` 直达页继续保持只看地图大屏，不请求浏览器全屏权限，不发送任何运动命令。
- `GET /api/robot-control/summary` 和 DOM 新增地图画布合同：`map_display_direct_map_viewport_priority=fullscreen_map_canvas`、`map_display_direct_map_canvas_height_mode=viewport_dominant_full_height`，用于脚本确认地图不是普通小卡片。
- 地图工具行新增 `ROS2观察` 按钮，只展开 RViz2/Foxglove 说明和命令；按钮固定声明不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 文档同步更新 PC 当前有效口径：普通用户优先 `/map` 大屏；本地工程调试用 RViz2，远程浏览器观察用项目包装 Foxglove bridge。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`，结果 `Test Files 3 passed`，`Tests 426 passed`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积提醒，不影响本轮地图合同。
- 通过：重启 PC Node 工作站到 `0.0.0.0:7001` 后，`GET /api/robot-control/summary` 返回 `map_display_default_zoom_percent=1600%`、`map_display_max_zoom_percent=4800%`、`map_display_direct_map_viewport_priority=fullscreen_map_canvas`、`map_display_direct_map_canvas_height_mode=viewport_dominant_full_height`。

## 剩余风险

- 本轮只改 PC UI、summary 合同、测试和文档；没有真实 RViz2/Foxglove 图形会话截图，也没有真实机器人运动验证。
- RViz2/Foxglove 仍是工程观察配套，不替代 PC 简易界面；需要上车 ROS2 环境已安装对应包。
