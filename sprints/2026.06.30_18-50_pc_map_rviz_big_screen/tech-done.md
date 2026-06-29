# PC 地图大屏与 RViz2 配套提示

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/styles.css`
  - 将 PC 工作站桌面外壳从 `min(1560px, calc(100% - 32px))` 放宽到 `min(1920px, calc(100% - 12px))`，并收紧顶部/底部边距，让地图在 PC 大屏上更接近全宽。
  - 将普通大地图高度提升到 `clamp(760px, calc(100vh - 180px), 1280px)`，全屏地图高度提升到 `calc(100vh - 120px)`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通地图卡加入 ROS2 配套调试提示，固定说明 RViz2 用于 `/map`、`/scan`、TF、Nav2 路线和定位观察。
  - DOM 暴露 `data-ros2-companion-tool=rviz2` 与 `data-rviz-launch-command="ros2 launch ros2_trashbot_bringup rviz.launch.py"`，方便现场脚本确认调试入口。
- `pc-tools/workstation/test/App.test.ts`
  - 固定大屏地图尺寸合同、RViz2 提示和 launch 命令。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录地图大屏策略和 ROS2/RViz2 配套边界。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - 结果：通过，`Test Files 1 passed (1)`，`Tests 1 passed | 218 skipped (219)`。
  - 先前误用不匹配的 test pattern 只产生 skipped，未作为通过证据。
- `npm run build`
  - 结果：通过，Vite 产物 `dist/assets/index-CZMHo-c5.css` 与 `dist/assets/index-84y0B8aN.js` 已生成。
- `npm test -- --run`
  - 结果：通过，`Test Files 2 passed (2)`，`Tests 389 passed (389)`。
- `git diff --check`
  - 结果：通过，无空白错误。
- PC Node 重启与 HTTP smoke
  - `npm run api -- --host 0.0.0.0 --port 7001` 已重新监听，`lsof` 显示 `node` 监听 `TCP *:7001`。
  - `GET http://127.0.0.1:7001/` 返回新 bundle：`index-CZMHo-c5.css`、`index-84y0B8aN.js`。
  - CSS bundle 已包含 `width:min(1920px,calc(100% - 12px))`、`clamp(760px,calc(100vh - 180px),1280px)` 和 `calc(100vh - 120px)`。
  - JS bundle 已包含 `plain-map-ros2-tool-note`、`ros2 launch ros2_trashbot_bringup rviz.launch.py` 和普通首屏文案 `规划轨迹`。

## 剩余风险

- 本轮只改 PC Web 显示与提示，不启动 RViz2、不启动 ROS2 runtime、不执行 Nav2、不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- RViz2 已有本地 launch：`onboard/src/ros2_trashbot_bringup/launch/rviz.launch.py`；真实显示效果仍依赖上车 ROS graph 是否正在发布 `/map`、`/scan`、TF 和 Nav2 path。
