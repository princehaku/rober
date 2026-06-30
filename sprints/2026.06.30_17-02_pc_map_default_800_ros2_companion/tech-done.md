# PC Map Default 800 ROS2 Companion Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图默认缩放从 `600%` 提升到 `800%`，缩放档位最高提升到 `1200%`。
  - `?view=map` 直达地图大屏默认进入最高 `1200%`，继续保留路线、小车位置和雷达贴图同画布 WYSIWYG。
  - 地图说明明确普通用户优先使用 PC 大地图，RViz2 和 Foxglove 只作为 ROS2 配套观察工具。
- `pc-tools/workstation/test/App.test.ts`
  - 更新普通首屏和直达地图大屏的 DOM 合同断言，锁定默认 `800%`、直达 `1200%` 和不启动 ROS2/不发车边界。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步 PC 地图尺寸与 ROS2 配套分层：RViz2 / `nav2_rviz_plugins` 做本地工程调试，Foxglove / `foxglove_bridge` 做浏览器远程观察，普通用户仍使用简易 PC 工作站。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default|opens direct map view from URL without starting ROS2 or motion"`：通过，2 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、398 个测试全部通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-CAHePasd.js` 与 `dist/assets/index-BBcFFzNr.css`。
- `git diff --check`：通过。
- 7001 重启：旧 `node` PID `83274` 已停止，新监听进程为 `node` PID `95755`，地址 `TCP *:7001`。
- 只读 smoke：`GET http://127.0.0.1:7001/` 已引用新 bundle；bundle 内命中 `800%`、`1200%`、RViz2/Foxglove 和全宽可滚动地图 CSS；`GET /api/robot-control/summary` 返回当前 `live_status=needs_wysiwyg`，本轮未发送任何 motion POST。

## 剩余风险

- 本轮只改 PC Web 显示和只读 DOM 合同，不启动 RViz2、Foxglove 或 ROS2 runtime。
- 未做真实显示器人工目测验收；实际读图舒适度仍受浏览器窗口尺寸、地图图片分辨率和现场 DPI 影响。
