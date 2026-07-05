# 2026.07.06 05:07｜pc_map_1600_ros2_companion｜PC 地图再放大与 ROS2 配套说明

## sprint_type

micro

## 本轮目标

响应现场反馈“PC 上地图太小，ROS2 有没有配套可以用”，把普通用户 PC 首页地图和 `/map` 默认可读视图继续放大，同时明确 ROS2 配套工具只用于工程观察：

- 普通用户默认用 PC 大地图和 `/map`，不需要先打开 RViz2 或 Foxglove。
- 本地工程调试用 RViz2/Nav2 RViz 配置观察 `/map`、`/scan`、TF、路径、定位和 costmap。
- 远程浏览器观察用 Foxglove bridge + Foxglove Web，连接 `ws://192.168.1.11:8765`。

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 首页和 `/map` 默认缩放从 `800%` 提升到 `1600%`。
  - `细节放大` 上限从 `3200%` 提升到 `4800%`，`完整态势` 仍回到 `100%`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - summary/live-summary 的地图显示口径同步为 `1600% / 4800%`。
  - 保持 ROS2 配套回答：RViz2/Foxglove 只观察，不替代 PC 简易控制台。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 同步 `map_display_default_zoom_percent=1600%`、`map_display_direct_map_default_zoom_percent=1600%`、`map_display_max_zoom_percent=4800%` 字面量合同。
- `pc-tools/workstation/test/App.test.ts`
- `pc-tools/workstation/test/robotControlSummary.test.ts`
- `pc-tools/workstation/test/catalog.test.ts`
  - 更新 PC 地图 DOM、summary 和 live-summary 的缩放断言。
- `pc-tools/README.md`
- `docs/product/pc_tools_workstation.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步当前有效默认值和 ROS2 配套分层说明。

## 验证结果

已通过：

```bash
cd pc-tools/workstation
npm test
npm run build
npm run lint
```

结果：

- `npm test` 通过：3 个测试文件、455 个测试用例通过。
- `npm run build` 通过：TypeScript app/server 编译和 Vite production build 通过；Vite 仅输出已有的大 bundle 警告。
- `npm run lint` 通过。

运行态复验：

```bash
HOST=0.0.0.0 PORT=7001 npm run api
curl -fsSI http://127.0.0.1:7001/map
curl -fsS 'http://127.0.0.1:7001/api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787'
curl -fsS http://127.0.0.1:7001/api/health
```

结果：

- Node 已重新监听 `*:7001`，`/map` 返回 HTTP 200。
- `/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- `live-summary` 返回 `status=ready_for_motion`、`map_current_visible=true`、`path_current_visible=true`。
- `live-summary` 返回 `map_display_default_zoom_percent=1600%`、`map_display_direct_map_default_zoom_percent=1600%`、`map_display_max_zoom_percent=4800%`。
- `live-summary` 返回 ROS2 配套口径：本地工程调试用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web，普通用户仍默认使用 PC 大地图和 `/map`。

## 剩余风险

- RViz2/Foxglove 是 ROS2 工程观察工具，本轮不自动启动 ROS2、RViz2、Foxglove、Nav2 或建图 runtime。
- 本轮仅改变地图显示和只读 API/DOM 合同，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 本次运行态只读复验中，`radar_map_points_visible=false` 且 `radar_overlay_current_point_count=0`，上车侧当前雷达/地图 proof 需要单独刷新或复验；不影响本轮 PC 地图缩放和 ROS2 配套口径交付。
