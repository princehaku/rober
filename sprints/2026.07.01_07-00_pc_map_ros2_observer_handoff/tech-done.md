# PC 地图 ROS2 工程观察交接

## sprint_type

micro

## 实际改动

- 在 PC 普通地图卡的默认折叠“工程观察”里补齐 RViz2/Foxglove 的固定观察 topic 白名单：`/map`、`/scan`、`/tf`、`/plan`、`/local_plan`、`/amcl_pose`、`/global_costmap/costmap`、`/local_costmap/costmap`。
- `plain-map-panel`、`plain-map-display-proof`、`plain-map-ros2-tool-note`、`plain-live-closure-summary` 和 `plain-live-map-companion-summary` 同步暴露 `data-ros2-observe-*` 只读 DOM 证据。
- `live_closure_summary` 增加 `map_display_ros2_observe_topics`、`map_display_ros2_observe_motion_topics=false` 和 `map_display_ros2_observe_control_tools=false`，明确 ROS2 配套只观察，不提供 GoalTool，不观察或发送底盘移动 topic；普通控制台可见文案不泄漏 `/cmd_vel` 或“速度”。
- 更新 `docs/product/pc_tools_workstation.md`，把 ROS2 配套定位固定为工程观察入口，普通用户仍优先使用 `/map` 大地图。

## 验证结果

- 通过：`npm test -- --run test/robotControlSummary.test.ts`，6 tests passed。
- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 test passed / 229 skipped。
- 通过：`npm run build`，Vite 构建成功；保留既有 chunk size warning。
- 通过：`npm run lint`。
- 通过：`git diff --check`。
- 通过：重启 PC Node 到 `http://0.0.0.0:7001`，本地只读 `GET /api/health` 成功。
- 通过：本地只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_primary_tool=pc_big_map`、ROS2 观察 topic 白名单、`map_display_ros2_observe_motion_topics=false`、`map_display_ros2_observe_control_tools=false`、`map_display_starts_nav2=false`。

## 剩余风险

- 本轮只增强 PC 端地图/ROS2 工程观察交接和只读合同，不启动真实 RViz2/Foxglove，也不执行 HIL 发车验证。
- 完整目标仍未收口：真实小车运动、同窗口 wheel raw L/R 非零、delivery success、摄像头首帧和建图启动还需要后续现场安全确认与硬件验证。
