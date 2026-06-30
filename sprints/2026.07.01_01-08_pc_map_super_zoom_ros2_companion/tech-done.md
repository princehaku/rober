# PC Map Super Zoom ROS2 Companion Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图与 `/map` 直达地图大屏默认缩放从 `1600%` 提升到 `2400%`。
  - 保留“适配”回到 `100%` 的入口，防止现场需要看全图时被超大缩放卡住。
  - ROS2 配套说明继续分层：RViz2 / Nav2 RViz 插件用于本地工程调试，Foxglove bridge 用于浏览器远程观察；普通用户默认仍使用 PC 简易工作站超大地图。
- `pc-tools/workstation/test/App.test.ts`
  - 同步地图默认缩放、直达地图大屏、缩放按钮、display proof 和 ROS2 配套提示的 DOM 合同断言。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 更新当前 PC 地图显示合同为 `2400%` 默认/最高缩放，并明确不启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime、不发送运动命令。

## 验证结果

- `npm test -- App.test.ts`：通过，1 个测试文件、229 个测试通过。
- `npm test -- --run`：通过，3 个测试文件、412 个测试通过。
- `npm run lint`：通过，0 error；保留既有 4 个 `vue/multiline-html-element-content-newline` warning。
- `npm run build`：通过，生成 `dist/assets/index-BoR-EUKp.js` 与 `dist/assets/index-BMxcT92A.css`。
- `git diff --check`：通过。
- 7001 本机 smoke：`GET http://127.0.0.1:7001/` 返回新构建页面，bundle 中确认包含 `2400%`、`/map 超大地图`、`RViz2`、`Foxglove`。
- 7001 只读 summary smoke：`GET http://127.0.0.1:7001/api/robot-control/summary` 返回默认小车地址 `http://192.168.1.11:8787`、`safe_to_control=false`、`delivery_success=false`；本轮未发送 Nav2/manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 端口检查：PC 工作站监听 `TCP *:7001`；本轮未触碰 `7071`。

## 剩余风险

- 本轮只解决 PC 地图体感太小的问题，并说明 ROS2 配套工具分层；未部署 Foxglove bridge，未启动 RViz2，未执行真实 Nav2、建图或自由移动。
