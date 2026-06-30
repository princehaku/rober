# PC ROS2 Companion Tool Split Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏地图卡和 ROS2 配套提示新增 RViz2/Foxglove 工具分工 DOM 合同。
  - RViz2 明确为本机工程调试地图、雷达、TF、路径和定位；Foxglove 明确为部署 bridge 后的浏览器远程观察。
  - 文案保留普通用户口径：PC 默认继续使用近整屏大地图，独立观察屏使用 `?view=map`。
- `pc-tools/workstation/test/App.test.ts`
  - 锁定 `data-rviz-companion-purpose`、`data-foxglove-companion-purpose`、`data-foxglove-bridge-handoff`。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步“ROS2 配套工具分工，不代表已启动 runtime”的产品合同。

## 验证结果

- `npm test -- test/App.test.ts -t "renders Robot Control V1 by default"`：通过，1 个目标测试通过。
- `npm test -- --run`：通过，2 个测试文件、396 个测试全部通过。
- `npm run lint`：通过，0 个 error；保留既有 4 个 Vue warning。
- `npm run build`：通过，生成 `dist/assets/index-cloXKXCW.js` 与 `dist/assets/index-DCA8Xtd4.css`。
- `git diff --check`：通过。
- 7001 live 验证：
  - 已停止旧 `node` PID `42201`，新 `node` PID `54255` 监听 `*:7001`。
  - `curl http://127.0.0.1:7001/` 返回新资产 `/assets/index-cloXKXCW.js` 和 `/assets/index-DCA8Xtd4.css`。
  - 打包 JS 命中 `data-rviz-companion-purpose`、`local_engineering_debug_map_scan_tf_path_pose`、`data-foxglove-companion-purpose`、`browser_remote_observation_map_scan_tf_path_pose`、`data-foxglove-bridge-handoff`、`deploy_bridge_then_open_foxglove_studio`、`Foxglove Studio`。

## 剩余风险

- 本轮只补 PC Web 只读提示和 DOM 合同，不启动 RViz2、Foxglove、ROS2 runtime，不发送 manual、keyboard、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- Foxglove 仍需要现场部署 bridge 后才能作为浏览器远程观察工具，本轮不安装、不配置、不验证真实 Foxglove 连接。
