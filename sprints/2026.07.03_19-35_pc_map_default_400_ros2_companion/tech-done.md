# PC Map Default 400% + ROS2 Companion Answer

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 普通首页和 `/map` 直达页默认地图缩放从 `200%` 提升到 `400%`，`适配` 仍回到 `45%`，`细节放大` 仍到 `1200%`；ROS2 配套入口仍是工程观察，不替代普通用户 PC 大地图。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 与 `pc-tools/workstation/src/shared/contracts.ts`：同步 summary / live closure / 类型合同为 `map_display_default_zoom_percent=400%`、`map_display_direct_map_default_zoom_percent=400%`。
- `pc-tools/workstation/src/styles.css`：同步地图 overlay 缩放注释，明确首页和 `/map` 默认 `400%`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：同步 DOM、summary 和缩放按钮断言，默认 scale 为 `4`，点一次放大到 `600%`，最高仍 `1200%`。
- `docs/product/pc_tools_workstation.md`：更新当前有效地图产品口径为默认 `400%` 细节视角；RViz2/Foxglove 仍为只读工程观察入口。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts test/catalog.test.ts test/App.test.ts -t "map"`，`3 passed`，`98 passed | 342 skipped`。
- 通过：`cd pc-tools/workstation && npm run build`，TypeScript + Vite + server 编译通过。
- 通过：本机 PC Node 已重启并监听 `0.0.0.0:7001`；`GET /api/health` 返回 `default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：`GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 返回 `map_display_default_zoom_percent=400%`、`map_display_direct_map_default_zoom_percent=400%`、`map_display_fit_zoom_percent=45%`、`map_display_max_zoom_percent=1200%`，并确认 `map_current_visible=true`、`path_current_visible=true`、`radar_map_points_visible=true`。

## 剩余风险

- 本轮只改 PC 地图观察默认缩放和 ROS2 配套说明，不修复相机首帧、wheel raw L/R 非零、delivery success 或真实 Nav2 复跑。
- RViz2/Foxglove 是工程观察配套，需要在 ROS2 环境部署/启动相应节点；普通用户仍应优先打开 `http://<PC-IP>:7001/map`。
