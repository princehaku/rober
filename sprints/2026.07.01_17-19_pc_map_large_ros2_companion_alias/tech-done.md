# PC 大地图与操作入口 alias micro sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏和 `/map` 直达大屏默认地图缩放从 `300%` 提升到 `400%`，`适配` 仍回到 `100%` 全图，最高细节放大仍为 `2400%`。
- `pc-tools/workstation/src/styles.css`：提升 PC 大地图默认面板高度，让地图更像主工作区，而不是被状态卡片挤成小图。
- `pc-tools/workstation/src/server/robotControlSummary.ts` / `src/shared/contracts.ts`：`summary` 顶层新增 primary/trip/keyboard/free-move/mapping 的 start/stop/acceptance endpoint alias，并同步把地图显示 alias 改为 `400%`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`test/catalog.test.ts`、`test/App.test.ts`：补齐地图默认缩放和操作入口 alias 的合同断言。
- `docs/product/pc_tools_workstation.md`：记录当前有效地图方案：普通用户使用 PC `/map` 大地图；RViz2 和 Foxglove 只作为 ROS2 工程观察配套，不作为普通用户发车入口。

## 验证结果

- 通过：`git diff --check`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，`9 passed`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`，`1 passed | 180 skipped`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1|opens direct map view"`，`2 passed | 229 skipped`。第一轮发现旧 `300%/scale=3/1120px` DOM 和 CSS 断言未同步，已改为当前 `400%/scale=4/1320px` 后复跑通过。
- 通过：`cd pc-tools/workstation && npm test`，`421 passed`。第一轮失败于上述旧地图比例断言，修复后复跑通过。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：重启 `0.0.0.0:7001`，当前监听 PID `85196`，`GET /map` 返回 `200`。
- 通过：只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_default_zoom_percent=400%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、`map_display_starts_ros2=false`、`map_display_starts_nav2=false`，并返回 `primary_start_endpoint=/api/robot-control/nav2/goal/execute`、`keyboard_start_endpoint=/api/robot-control/base/manual`、`free_move_start_endpoint=/api/robot-control/free-roam/autonomy/start`、`mapping_start_endpoint=/api/robot-control/map/start`。

## 剩余风险

- 本轮只改 PC 显示、只读 summary alias 和文档，不发送运动命令，不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime。
- ROS2 配套建议沿用现有合同：RViz2 本地工程调试，Foxglove + `foxglove_bridge` 远程浏览器观察；普通用户主路径仍是 PC 工作站大地图。
