# PC 大屏地图与 ROS2 配套入口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图默认缩放从 `150%` 提升到 `200%`，缩放档位改为 `100% / 150% / 200% / 300% / 400%`。
  - 地图卡本体新增 ROS2 配套 DOM 合同：`data-ros2-companion-tool=rviz2`、`data-ros2-remote-companion-tool=foxglove`、`data-rviz-launch-command="ros2 launch ros2_trashbot_bringup rviz.launch.py"`。
- `pc-tools/workstation/src/styles.css`
  - 桌面大地图高度提升到 `clamp(900px, calc(100vh - 96px), 1500px)`。
  - 全屏地图高度提升到 `calc(100vh - 72px)`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏地图默认缩放、缩放按钮和 ROS2 配套入口断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录：普通用户继续使用 PC 大地图；ROS2 工程调试用 RViz2，浏览器远程观察可接 Foxglove。

## 验证结果

- `npm test -- test/App.test.ts -t "shows the simplified first-screen console with visual-first map and camera proof"`：未命中用例名，0 个测试执行；已改用准确用例名重跑。
- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`：通过，`1 passed | 218 skipped`。
- `npm test -- --run`：通过，`2 passed`，`389 passed`。
- `npm run build`：通过，生成 `dist/assets/index-KhNg9bm4.js` 与 `dist/assets/index-BmaNglvi.css`。
- `git diff --check`：通过，无空白错误。
- 7001 smoke：重启 PC 工作站后，`node` PID `30532` 监听 `*:7001`；`curl -fsS http://127.0.0.1:7001/` 返回当前 `index-KhNg9bm4.js` / `index-BmaNglvi.css`；dist 可检出 `default-map-zoom-percent`、`200%`、`Foxglove`、`ros2-companion-tool`、`ros2-remote-companion-tool`、`rviz.launch.py`、`height:clamp(900px` 和 `100vh - 72px`。

## 剩余风险

- 本轮只改 PC Web 只读显示尺寸和 DOM/文档合同，没有启动 RViz2、Foxglove、ROS2 runtime、Nav2，也没有发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 地图真实内容质量、Nav2 路线完整执行、真实雷达贴图和真实小车运动仍需要现场 HIL 验证。
