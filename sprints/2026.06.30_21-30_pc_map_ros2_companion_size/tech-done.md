# PC Map ROS2 Companion Size Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图默认缩放从 `500%` 提升到 `600%`，缩放上限提升到 `800%`。
  - 地图默认高度模式从 `near-viewport` 更新为 `viewport-dominant`。
  - 将普通用户按钮文案从“观测模式 / 退出观测”改为“只看地图 / 退出只看”，并保留 RViz2 / Foxglove 作为 ROS2 工程配套信息。
- `pc-tools/workstation/src/styles.css`
  - PC 工作站外壳从 `min(2200px, calc(100% - 4px))` 放宽到 `min(2600px, calc(100% - 2px))`。
  - 默认大地图高度提升为 `clamp(1040px, calc(100vh - 12px), 2200px)`。
  - 全屏地图高度提升为 `calc(100vh - 8px)`，只看地图模式高度提升为 `calc(100vh - 42px)`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定默认 `600%`、最高 `800%`、只看地图按钮、近整屏高度和 ROS2 配套提示。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明 ROS2 配套：RViz2 / `nav2_rviz_plugins` 用于工程调试，Foxglove / `foxglove_bridge` 用于浏览器远程观察，普通用户仍使用 PC 简易工作站大地图。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、391 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-Cs3wSiB4.js` 与 `dist/assets/index-FPVvFXGa.css`。
- `git diff --check`：通过。
- 7001 重启：已停止旧 `node` PID `27123`，新监听进程为 `node` PID `40920`，地址 `TCP *:7001`。
- live bundle 检查：`http://127.0.0.1:7001/` 已引用 `index-Cs3wSiB4.js` 和 `index-FPVvFXGa.css`，资源内命中“只看地图”、`600%`、`800%`、`viewport-dominant`、`2600px`、`1040px`、`calc(100vh - 8px)` 等新合同。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同，不启动 RViz2、Foxglove 或 ROS2 runtime。
- 未做真实上位机 HIL 验证；地图实际可读性仍受浏览器窗口尺寸、当前地图图片分辨率和现场显示器 DPI 影响。
