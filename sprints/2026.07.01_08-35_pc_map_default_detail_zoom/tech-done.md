# PC 地图默认细节缩放

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏和 `/map` 直达地图大屏默认缩放从 `100%` 改为 `150%`，让现场打开即看到更大的地图细节。
  - `适配` 仍回到 `100%` 全图，`细节放大` 仍到 `2400%`，缩放继续作用在同一个 overlay frame，保证底图、路线、小车位置和雷达点同步放大。
  - 该改动只改变 PC 只读显示，不启动 ROS2/RViz2/Foxglove、Nav2、建图 runtime、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - `live_closure_summary.map_display_default_zoom_percent` 同步为 `150%`，普通用户文案说明可点“适配”回到 `100%` 看全图。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`
  - 锁定默认 `150%`、适配回 `100%`、最高 `2400%` 以及不发车边界。
- `docs/product/pc_tools_workstation.md`、`pc-tools/README.md`
  - 同步当前有效地图显示合同，清理顶部当前段落里 `100%` / `2400%` 默认值漂移。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，1 file passed，7 tests passed。
- 修复后通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|renders Robot Control V1 by default"`，1 file passed，4 tests passed，227 skipped。
- 通过：`cd pc-tools/workstation && npm test`，3 files passed，417 tests passed。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`，仅保留既有 Vite chunk size warning；当前产物为 `dist/assets/index-BhstVTls.js` 与 `dist/assets/index-7krFlZYN.css`。
- 通过：`git diff --check`。
- 通过：PC Node 已重启并监听 `0.0.0.0:7001`，`lsof` 返回 `node 43801 ... TCP *:7001 (LISTEN)`。
- 通过：`GET http://127.0.0.1:7001/map` 返回当前构建资源 `assets/index-BhstVTls.js`、`assets/index-7krFlZYN.css`。
- 通过：构建产物包含 `150%`、`细节视图`、`100% 看全图`、`2400%` 和 `data-default-map-zoom-percent`。
- 通过：只读 `GET /api/robot-control/summary` 返回 `live_closure_summary.map_display_default_zoom_percent=150%`、`map_display_max_zoom_percent=2400%`、`map_display_primary_url=/map`。

## 剩余风险

- 本轮只解决 PC 地图默认细节显示偏小的问题，不改变地图数据、雷达贴图坐标、Nav2 路线生成或现场运动能力。
- 真实浏览器视觉效果仍需在现场 PC 刷新 `http://<pc-ip>:7001/map` 后肉眼确认；若 150% 仍不够，可继续把默认档位提升到 `200%`。
