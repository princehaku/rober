# PC 地图默认可读大图与 ROS2 观察入口

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首页和 `/map` 默认地图缩放从 `100%` 完整态势改为 `300%` 可读大图。
  - `完整态势` 按钮继续回到 `100%` 全局视角，`细节放大` 继续到 `4800%`。
  - 保持 RViz2/Foxglove 为默认折叠的工程观察入口，不自动启动 ROS2/RViz2/Foxglove/Nav2/建图 runtime，不发送 manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`、`pc-tools/workstation/src/shared/contracts.ts`
  - summary/live-summary 地图合同同步为 `map_display_default_zoom_percent=300%`、`map_display_direct_map_default_zoom_percent=300%`、`map_display_fit_zoom_percent=100%`、`map_display_max_zoom_percent=4800%`。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/catalog.test.ts`
  - 更新地图默认缩放、直达 `/map`、live closure 和 catalog 合同断言。
- `docs/product/pc_tools_workstation.md`
  - 追加当前有效口径：默认 `300%` 可读大图，`100%` 是完整态势，ROS2 配套仍仅作只读观察。

## 验证结果

- `npm test`：通过，3 个 test files，455 个 tests passed。
- `npm run build`：通过；Vite 仍有既有 chunk 大小警告。
- 本机 PC Node 已重启：
  - `node` PID `71579` 监听 `TCP *:7001 (LISTEN)`。
  - `/api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 真实 7001 读回：
  - `live-summary.status=ready_for_motion`
  - `map_current_visible=true`
  - `path_current_visible=true`
  - `radar_map_points_visible=true`
  - `keyboard_ready=true`
  - `keyboard_motion_verified=true`
  - `keyboard_continuous_motion_verified=true`
  - `delivery_success=true`
  - `map_display_default_zoom_percent=300%`
  - `map_display_direct_map_default_zoom_percent=300%`
  - `map_display_fit_zoom_percent=100%`
  - `map_display_max_zoom_percent=4800%`
  - `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`
- `/map` HTTP smoke：HTTP HTML 返回，当前 bundle 为 `index-yKcAgvuy.js` / `index-D97t3wRS.css`。
- 上位机 ROS2 配套验证：
  - SSH `root@192.168.1.11 -p 7878` 可用。
  - `ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py --show-args` 返回默认 `address=0.0.0.0`、`port=8765`、`use_sim_time=false`、`sysinfo=true`。

## 剩余风险

- 实时图传仍未恢复：当前 7001 `live-summary.camera_current_visible=false`，已知缺口仍集中在 DV20 上游输入、线材/接口/供电、采集卡/摄像头本体或 known-good UVC 复测。
- 本轮没有启动 Foxglove bridge 常驻服务，只验证 ROS2 launch 参数和 PC 页面入口；普通用户默认仍使用 7001 `/map`。
- 本轮没有重新执行真实 Nav2 路线或 WASD 运动，只读复核当前 live-summary 里已有运动/键盘状态。
