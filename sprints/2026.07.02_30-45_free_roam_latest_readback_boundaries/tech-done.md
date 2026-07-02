# Free Roam Latest Readback Boundaries

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `RobotControlFreeRoamAutonomyLatestResponse` 增加直连只读边界字段，明确 latest 只读取状态，不发车、不启动建图或任何 runtime。
- `pc-tools/workstation/src/server/index.ts`：在 `/api/robot-control/free-roam/autonomy/latest` fallback 和正常响应里同源返回 `readback_only=true`、`free_roam_latest_readback_only=true` 以及完整 `starts_*` / `submits_delivery` / `stops_motion=false`。
- `pc-tools/workstation/test/catalog.test.ts`：补充 free-roam latest direct contract 断言，确保现场 `curl` 单看该接口也能确认只读边界。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录自由移动 latest 只读合同；地图太小继续按 PC `/map` 大屏优先，RViz2/Foxglove 只作为 ROS2 配套观察。

## 验证结果

- 通过：`npm test -- test/catalog.test.ts`，`Test Files 1 passed (1)`，`Tests 183 passed (183)`。
- 通过：`npm run build`，TypeScript app/server 和 Vite build 均完成；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001`，`/api/health` 返回 `workstation_listen_address=http://0.0.0.0:7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：读取 `GET /api/robot-control/free-roam/autonomy/latest`，返回 `proxy_status=latest_loaded`、`readback_only=true`、`free_roam_latest_readback_only=true`、`sends_motion_when_clicked=false`、`starts_camera_exclusive_capture=false`、`starts_radar_lifecycle=false`、`starts_nav2=false`、`starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`submits_delivery=false`、`stops_motion=false`。
- 通过：读取 `GET /api/robot-control/summary`，确认地图太小时下一步为打开 `/map`，ROS2 配套为本地 RViz2 和远程 Foxglove bridge，且 `map_display_companion_replaces_pc_ui=false`。

## 剩余风险

- 本轮不发送真实运动控制命令；`same_window_wheel_lr_nonzero`、`delivery_success`、真实自由移动启动后的 HIL 证据仍需现场安全确认后执行。
- 摄像头首帧仍受当前 USB full-speed / `first_frame_total_timeout` blocker 影响；该问题不阻塞低速自由移动，但阻塞建图启动验收。
