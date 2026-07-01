# PC 地图首屏优先级

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通用户首屏 `.simple-user-console` 上新增地图优先级 DOM 合同：
    - `data-first-screen-map-priority=map_before_status_summaries`
    - `data-first-screen-map-order=robot_console_grid_first`
    - `data-status-summaries-order=after_primary_map`
  - 该合同只改变 PC 页面视觉排序，不新增运动入口，不启动 RViz2/Foxglove/ROS2 runtime。
- `pc-tools/workstation/src/styles.css`
  - `.simple-user-console` 改成 grid 容器，并让 `robot-console-grid` 在视觉顺序上排到状态摘要前面。
  - 目的：普通 PC 页第一眼先看到大地图；当前事实、现在可以做什么、当前卡点等摘要仍保留在地图后面。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定普通首屏地图优先 DOM 合同和 CSS 选择器。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 2026-07-01 11:20 CST 起普通 PC 首页地图优先于状态摘要的显示契约。

## 验证结果

- `npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed | 230 skipped`。
- `npm run lint`：通过。
- `npm run build`：通过；仍有既有 Vite chunk size warning。
- `npm test`：通过，`3 passed / 417 tests passed`。
- `git diff --check`：通过。
- `GET http://127.0.0.1:7001/map`：通过，HTTP 200，返回当前构建资源 `index-Cj4H2zu9.js` / `index-DncBT-o2.css`。
- `GET http://127.0.0.1:7001/api/robot-control/summary` no-motion smoke：通过，地图主入口仍为 `/map`，默认缩放 `300%`，WYSIWYG overlay 为 `image,route,robot,radar`，ROS2 配套工具为 `rviz2,foxglove`。

## 剩余风险

- 本轮只解决 PC 普通页打开后地图被状态摘要挤到下方的问题。
- 真实车 wheel raw L/R 非零、delivery success、摄像头首帧、雷达当前点贴图和建图启动仍需现场或上车只读证据继续闭环。
