# PC 地图主画布与 ROS2 配套工具口径

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图默认缩放从 300% 提升到 400%，缩放上限提升到 500%。
  - 地图卡新增 `data-ros2-companion-tools=rviz2,foxglove`，明确 ROS2 配套观察工具为 RViz2 和 Foxglove。
  - `plain-keyboard-hold-gate` 暴露当前方向、方向文案、轮速 L/R、stop 收口状态，方便首屏直接验 PC 键盘连续手控。
- `pc-tools/workstation/src/styles.css`
  - PC 工作站外壳放宽到 `min(2200px, calc(100% - 4px))`，减少左右留白。
  - 地图大图高度提升到 `clamp(960px, calc(100vh - 54px), 1800px)`，全屏高度提升到 `calc(100vh - 40px)`，观测模式高度提升到 `calc(100vh - 58px)`。
- `pc-tools/workstation/test/App.test.ts`
  - 更新地图默认缩放、ROS2 工具 DOM 合同、地图尺寸 CSS 合同和键盘入口实时字段断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步普通 PC 地图主画布、RViz2/Foxglove 配套工具、键盘首屏证据字段的产品口径。

## 验证结果

- 通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default"`，1 passed / 218 skipped。
- 通过：`npm test -- --run test/App.test.ts -t "enables non-stop motion only after complete operator material and still uses the fixed workstation proxy"`，1 passed / 218 skipped。
- 通过：`npm test -- --run`，2 files passed，389 tests passed。
- 通过：`npm run lint`，0 errors，4 个既有 Vue multiline warning。
- 通过：`npm run build`，TypeScript 与 Vite build 通过；Vite 仍提示单 chunk 大于 500 kB 的既有 warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同，不启动 RViz2/Foxglove，不启动 ROS2 runtime，不执行 Nav2，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 真实现场地图是否足够大还需要在 PC 浏览器 7001 页面肉眼复核；当前验证以 DOM/CSS/构建为准。
