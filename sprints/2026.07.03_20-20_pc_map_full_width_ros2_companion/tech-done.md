# PC 地图全宽首行与 ROS2 配套说明 micro sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 普通 PC 首页 `visual-first` 布局从“地图左侧 + 图传/WASD 右侧”改为“地图独占首行，图传和 WASD 在第二行并排”。
  - 保留 `/map` 直达大屏、缩放、只读刷新和工程观察入口，且不改变任何运动、Nav2、建图或雷达 lifecycle gate。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图说明改为“PC 首页现在让地图独占首行”，继续明确 ROS2 配套为 RViz2/Foxglove，只作工程观察。
  - 顶部短提示改为“普通看大地图；工程看 RViz2 / Foxglove”。
- `pc-tools/workstation/src/App.vue`
  - 顶栏入口从“地图大屏 /map”改为普通用户更直观的“打开大地图”。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 同步 summary 中地图太小的处理口径，避免 API/DOM 与界面说明不一致。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图全宽首行、ROS2 配套和顶栏按钮文案断言。

## 验证结果

- `npm test -- test/App.test.ts -t "map display|direct map|ROS2|Foxglove|RViz2|plain map" --run`
  - 1 个 test file 通过；7 tests passed / 232 skipped。
- `npm test -- test/robotControlSummary.test.ts --run`
  - 1 个 test file 通过；14 tests passed。
- `npm run build`
  - 通过；Vite 仅保留既有 chunk size warning。
- 7001 本机 smoke：
  - 已重启 `PORT=7001 HOST=0.0.0.0 npm run api`。
  - `GET http://127.0.0.1:7001/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、默认小车地址 `http://192.168.1.11:8787`。
  - `GET http://127.0.0.1:7001/map` 返回 HTTP 200。
  - 当前构建产物可搜到 `打开大地图`、`地图独占首行`、`grid-template-areas:"map map" "camera drive"`。

## 剩余风险

- 本轮只调整 PC 界面布局和只读说明，不执行 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- ROS2 配套工具结论保持：本地工程调试用 RViz2，远程浏览器观察用 Foxglove bridge + Foxglove Web；它们不替代普通 PC 简易控制台，也不是发车前置。
