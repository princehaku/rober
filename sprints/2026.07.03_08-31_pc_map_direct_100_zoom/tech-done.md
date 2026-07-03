# PC 地图大屏直达 100% 细节

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`/map` 直达页默认进入 fullscreen 地图尺寸，并把默认缩放改为 `100%` 细节大屏；普通首页仍保持 `45%` 完整态势视角，`适配` 回到 `45%`。
- `pc-tools/workstation/src/styles.css`：只要 URL 是 `/map`，CSS 即强制按 fullscreen 画布高度计算，避免等待 observer 状态同步时短暂退回普通卡片尺寸。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`：summary/live-summary 新增 `map_display_direct_map_default_zoom_percent=100%` 和 `map_display_fit_zoom_percent=45%`，明确区分首页完整视角与直达大屏细节视角。
- `docs/navigation/fixed_route_workflow.md`：同步说明 ROS2 原生配套是 RViz2，远程浏览器观察可用 Foxglove bridge；二者只作工程观察，不替代 PC 普通用户页面。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：补齐 `/map` 默认 100%、fit 45%、RViz2/Foxglove 工程观察入口的断言。

## 验证结果

- `npm test -- App.test.ts robotControlSummary.test.ts catalog.test.ts`：通过，`3 passed / 434 passed`。
- `npm run build`：通过，Vite 仅保留既有 chunk size warning。
- 已重启 PC workstation：`0.0.0.0:7001` 正常监听。
- `GET http://127.0.0.1:7001/api/health`：返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车 API `http://192.168.1.11:8787`。
- `GET http://127.0.0.1:7001/map`：返回 `200 OK`。
- `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787`：返回 `map_display_direct_map_default_zoom_percent=100%`、`map_display_fit_zoom_percent=45%`、ROS2 配套工具 `rviz2,foxglove`。

## 剩余风险

- 本轮没有启动 RViz2 或 Foxglove bridge；它们仍是工程观察入口，需要在 ROS2 环境单独启动。
- 本轮只改 PC 地图显示口径，不改变 Nav2、WASD、相机或底盘控制链路。
