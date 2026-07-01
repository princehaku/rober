# PC 地图默认 300% 大图与 ROS2 观察边界

## sprint_type

micro

## 实际改动

- 将普通 PC 首屏和 `/map` 直达地图的默认缩放从 `150%` 提升到 `300%`，`适配` 仍回到 `100%` 全图，`细节放大` 仍到 `2400%`。
- 同步 `GET /api/robot-control/summary` / `live_closure_summary` 的 `map_display_default_zoom_percent=300%` 合同，确保现场脚本和 DOM 读到一致值。
- 保留 RViz2 / Foxglove 作为默认折叠的工程观察配套；PC 页面不自动启动 ROS2、RViz2、Foxglove、Nav2、建图 runtime，也不发送 manual/keyboard/free-roam/delivery/stop 或 `/cmd_vel`。
- 更新 `docs/product/pc_tools_workstation.md`，明确普通用户优先使用 PC `/map` 大地图，ROS2 配套只做观察。

## 验证结果

- `git diff --check`：通过。
- `npm test -- --run test/App.test.ts -t "map"`：通过，67 passed / 164 skipped。
- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，5 passed / 4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 passed / 180 skipped。
- `npm test`：通过，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；保留既有 Vite chunk size warning。
- 重启前只读 `GET /api/robot-control/summary` 仍返回旧进程的 `map_display_default_zoom_percent=150%`；已重启 PC Node。
- `lsof -nP -iTCP:7001 -sTCP:LISTEN`：新 Node PID `48533` 监听 `*:7001`。
- 只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：返回 `map_display_default_zoom_percent=300%`、`map_display_primary_url=/map`、`map_display_ros2_companion_tools=[rviz2,foxglove]`、`map_display_starts_ros2=false`、`map_display_sends_motion_when_clicked=false`。
- 只读 `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787`：返回同样的 `300%` 地图默认缩放和 ROS2 只观察边界。

## 剩余风险

- 本轮只修 PC 地图默认显示大小和合同同步；完整 Nav2 路线执行、PC 键盘连续控制、真实雷达贴图、相机画面和自由移动/建图仍需现场安全确认后继续 HIL 验证。
- 本轮未发送任何会让小车移动的请求，未验证真实运动闭环。
