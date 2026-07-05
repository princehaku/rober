# PC map 800% ROS2 companion

sprint_type: micro

## 实际改动

- 将 PC 普通首页和 `/map` 默认地图缩放从 `300%` 调整为 `800%`，`完整态势` 保持回到 `100%`，`细节放大` 最高保持 `4800%`。
- 同步更新 `summary/live-summary` 合同、DOM data 属性、Vitest 断言和 catalog 断言，确保 `map_display_default_zoom_percent` 与 `map_display_direct_map_default_zoom_percent` 都返回 `800%`。
- 保持 ROS2 配套的产品分层：普通用户继续使用 PC 大地图和 `/map`；RViz2/Nav2 RViz 配置与 Foxglove bridge + Foxglove Web 只作为工程观察入口，不替代简易控制台，不发送运动命令。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md` 和 `OKR.md` 的当前地图显示口径。

## 验证结果

- `cd pc-tools/workstation && npm test -- test/robotControlSummary.test.ts --run`：通过，18 tests OK。
- `cd pc-tools/workstation && npm test -- test/App.test.ts --run`：通过，242 tests OK。
- `cd pc-tools/workstation && npm test -- test/catalog.test.ts --run`：通过，195 tests OK。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 chunk 超过 500 kB，这是既有打包体积警告，不影响本轮构建。
- 本机 PC Node 已重启并继续监听 `0.0.0.0:7001`；`GET /api/health` 返回 `workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 重启后 `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787` 返回 `status=ready_for_motion`、`map_display_default_zoom_percent=800%`、`map_display_direct_map_default_zoom_percent=800%`、`map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=4800%`、`map_display_ros2_companion_tools=[rviz2,foxglove]`。

## 剩余风险

- 本轮只调整 PC 地图显示比例和工程观察口径，不修复真实相机无帧、wheel raw `T=1001 L/R=0/0` 或完整路线长期 HIL。
- `800%` 默认会让小地图细节更大，但用户若需要全局态势仍应点击 `完整态势` 回到 `100%`。
