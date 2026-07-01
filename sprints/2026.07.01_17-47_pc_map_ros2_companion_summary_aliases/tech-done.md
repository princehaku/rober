# PC 地图 ROS2 配套顶层 alias

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `GET /api/robot-control/summary` 顶层补齐地图和 ROS2 工程观察 alias：普通用户入口 `/map`、主工具 `pc_big_map`、默认 `400%`、最高 `2400%`、WYSIWYG overlay、RViz2/Foxglove 启动命令、Foxglove WebSocket、观察 topic 白名单和所有 no-motion/no-runtime 标志。
  - 字段只从既有 `live_closure_summary` 同源透传；不启动 ROS2、RViz2、Foxglove、Nav2、建图 runtime，也不发送任何运动命令。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `RobotControlSummaryResponse` 顶层地图/ROS2 alias 类型，避免现场脚本读顶层字段时类型缺口。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 锁定 summary 顶层字段与 `live_closure_summary` 同源，覆盖 RViz2/Foxglove 命令和 no-motion 边界。
- `pc-tools/workstation/test/catalog.test.ts`
  - 锁定 live-summary 合同消费者可读到顶层 ROS2 配套 alias。
- `docs/product/pc_tools_workstation.md`
  - 更新 PC 地图易用性合同：普通用户默认 `/map` 大地图；ROS2 配套为 RViz2/Foxglove 工程观察，不作为发车入口。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，9 tests passed。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，1 file passed，1 passed / 180 skipped。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，421 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`，Vite/TS build 成功；仍有既有 bundle >500 kB 提示。
- 通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听 PID `35352`。
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `status=needs_wheel_rerun`、`map_display_primary_tool=pc_big_map`、`map_display_primary_url=/map`、`map_display_default_zoom_percent=400%`、`map_display_max_zoom_percent=2400%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、RViz2/Foxglove 启动命令、`map_display_foxglove_websocket_url=ws://192.168.1.11:8765`、观察 topic 白名单，且 `map_display_starts_ros2=false`、`map_display_starts_rviz2=false`、`map_display_starts_foxglove=false`、`map_display_starts_nav2=false`、`map_display_sends_motion_when_clicked=false`。

## 剩余风险

- 本轮不启动 RViz2/Foxglove，也不部署 `foxglove_bridge`；只把可用配套工具和命令暴露给 PC/API。
- 本轮不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；完整路线执行、轮速 L/R 非零和 delivery success 仍需现场勾安全确认后验证。
