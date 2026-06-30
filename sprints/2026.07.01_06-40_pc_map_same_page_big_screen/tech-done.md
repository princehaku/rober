# PC 地图同页大屏入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue` 将普通首屏地图主入口从“打开地图大屏”调整为“进入地图大屏”，同页进入 `/map`，并暴露 `data-opens-current-page=true`、`data-direct-map-view-default-observer=true`、`data-direct-map-view-map-only=true`。
- `/map` 直达页继续默认 `fullscreen + observer`，只保留地图、路线、小车位置和雷达 overlay 的 WYSIWYG 画布，不自动打开相机、不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，也不发送运动命令。
- `pc-tools/workstation/src/styles.css` 加强 `/map` 直达页地图层高度，确保进入后就是地图观察屏，而不是普通卡片尺寸。
- `pc-tools/workstation/src/server/robotControlSummary.ts` 同步 summary 合同，把地图入口描述为“进入 /map 使用 PC 大地图”，并暴露同页进入/只看地图字段。
- `docs/product/pc_tools_workstation.md` 同步最新 PC 地图大屏口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "direct map|map display|ROS2"`，3 tests passed, 227 skipped。
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`，6 tests passed。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC 端显示入口和合同，不执行任何真实 Nav2、manual、keyboard、free-roam、map start、radar start、delivery、stop 或 `/cmd_vel`。
- 上位机上一轮出现 8787/SSH 只读超时，真实现场 `/map` 数据刷新仍依赖上位机 API 恢复响应。
