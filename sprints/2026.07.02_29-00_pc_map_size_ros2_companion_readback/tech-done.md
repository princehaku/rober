# PC 地图太小与 ROS2 配套读回

## sprint_type

micro

## 实际改动

- 本轮未修改产品代码。复核发现当前 `master` 已实现普通用户地图大屏方案：
  - PC 顶部提供 `地图大屏` 入口，直达 `/map`。
  - `/map` 直达页只保留地图、缩放、只读地图刷新、雷达贴图只读刷新和 `ROS2观察`。
  - 普通地图默认 `3200%`，最高 `6400%`，并保持 `PC 大地图 / /map 满屏` 的普通用户口径。
- 本轮新增此 sprint 留档，记录用户反馈“PC 地图太小 / ROS2 有什么配套”的现场核准结论。

## 验证结果

- `npm test -- --run App.test.ts robotControlSummary.test.ts`
  - 结果：通过，`2 passed`，`247 passed`。
- `npm run build`
  - 结果：通过，产物包含 `dist/index.html`、`dist/assets/index-CV6yLOmZ.css`、`dist/assets/index-DDIdGRr3.js`。
  - 备注：Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告，不影响本轮地图功能验证。
- `npm run lint`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无空白错误。
- `curl -I http://127.0.0.1:7001/map`
  - 结果：HTTP `200 OK`。
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读读回：
  - `map_display_primary_tool=pc_big_map`
  - `map_display_primary_url=/map`
  - `map_display_default_zoom_percent=3200%`
  - `map_display_max_zoom_percent=6400%`
  - `map_display_rviz_launch_command="ros2 launch ros2_trashbot_bringup rviz.launch.py"`
  - `map_display_foxglove_bridge_launch_command="ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py"`
  - `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`
  - `map_display_sends_motion_when_clicked=false`
  - `map_display_starts_ros2=false`
  - `map_display_starts_rviz2=false`
  - `map_display_starts_foxglove=false`
  - `map_display_starts_nav2=false`
  - `map_display_starts_map_runtime=false`

## ROS2 配套口径

- 普通用户：优先用 PC 工作站 `/map` 大地图，不需要先开 ROS2 工具。
- 工程本地观察：用 RViz2，命令为 `ros2 launch ros2_trashbot_bringup rviz.launch.py`，看 `/map`、`/scan`、TF、路径、定位和 costmap。
- 远程浏览器观察：用 Foxglove bridge，命令为 `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py`，浏览器连接 `ws://192.168.1.11:8765`。
- RViz2 / Foxglove 在本项目口径里只做观察配套，不作为普通发车入口，不启动 Nav2、建图 runtime 或运动控制。

## 剩余风险

- 本轮未做真实浏览器截图尺寸测量，只用单元测试、构建、lint、HTTP 200 和 summary 只读字段确认当前服务口径。
- 真车 Nav2 行程、wheel raw L/R 非零、delivery success、摄像头首帧仍属于现场 HIL 验证范围；本轮没有发送任何运动命令。
- 工作区仍保留既有未纳入本轮的 artifact dirty 文件：
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`
  - `sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`
