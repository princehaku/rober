# 2026.07.01 09:17 PC 地图默认 300% 大细节

## sprint_type

micro

## 实际改动

- PC 普通首屏和 `/map` 直达地图大屏默认缩放从 `150%` 提升到 `300%`，继续保留 `适配=100%` 和 `细节放大=2400%`。
- `GET /api/robot-control/summary` 的 `live_closure_summary.map_display_default_zoom_percent` 同步改为 `300%`，共享 TypeScript contract 和测试 fixture 同步更新。
- 产品文档与 README 同步当前有效合同：普通用户优先使用 PC 大地图，ROS2 配套为 RViz2 / Foxglove 工程观察，不是发车入口。
- 该改动只改变 PC 显示和只读合同，不启动 ROS2/RViz2/Foxglove、Nav2、建图 runtime、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|renders Robot Control V1 by default"`，1 file passed，4 tests passed，227 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning；当前产物为 `dist/assets/index-BWkTdggq.js` 与 `dist/assets/index-7krFlZYN.css`。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`GET http://127.0.0.1:7001/map` 返回 `200 OK`。
- 通过：构建产物包含 `默认 300% 细节视图`、`data-default-map-zoom-percent`、`进入地图大屏`、`RViz2` 和 `Foxglove`。
- 通过：只读 `GET /api/robot-control/summary?robot_api_base_url=http://192.168.1.11:8787` 返回 `robot_api_connection=readable`、`map_display_default_zoom_percent=300%`、`map_current_visible=true`、`radar_map_points_visible=true`、`camera_current_visible=false`、`wheel_lr_nonzero=false`、`delivery_success=false`。

## 剩余风险

- 真实现场视觉大小仍需要在 PC 浏览器刷新 `http://<pc-ip>:7001/map` 后肉眼确认；如果 `300%` 仍觉得小，可以继续把默认档位提升到 `400%`。
- RViz2 / Foxglove 只是工程观察配套；本轮没有部署或启动 `foxglove_bridge`，也没有运行 ROS2 HIL。
