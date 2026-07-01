# 2026.07.01 23:58 PC 大地图 Foxglove Web 观察入口

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary` 和 summary 顶层新增 `map_display_foxglove_web_app_url=https://studio.foxglove.dev`。
  - 地图 companion 文案明确：普通用户优先 `/map` 大屏；ROS2 配套只作工程观察，启动 `foxglove_bridge` 后用 Foxglove Web 连接 `ws://192.168.1.11:8765`。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐 `map_display_foxglove_web_app_url` 类型合同。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - PC 大地图“工程观察”折叠区新增 `打开 Foxglove Web` 链接。
  - 链接显式标注 `data-sends-motion-when-clicked=false`、`data-starts-nav2=false`、`data-starts-map-runtime=false`，只作为远程观察入口。
- `pc-tools/workstation/src/styles.css`
  - 给 Foxglove Web 观察链接增加轻量样式，避免普通主界面变成工程台。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 覆盖 summary 和 live closure 新字段。
- `pc-tools/workstation/test/catalog.test.ts`
  - 覆盖 live-summary 顶层 Foxglove Web URL。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖 DOM 中 Foxglove Web 入口、WebSocket URL 和只读/不发车属性。
- `docs/product/pc_tools_workstation.md`
  - 同步说明 `/map` 是普通用户大地图，Foxglove/RViz2 是 ROS2 配套观察工具，不作为发车或建图前置。

## 验证结果

- 通过：`git diff --check`
- 通过：`cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`
  - `Test Files 1 passed (1)`，`Tests 9 passed (9)`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "live-summary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 180 skipped (181)`。
- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`
  - `Test Files 1 passed (1)`，`Tests 1 passed | 230 skipped (231)`。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`cd pc-tools/workstation && npm run build`
- 通过：`cd pc-tools/workstation && npm test`
  - `Test Files 3 passed (3)`，`Tests 421 passed (421)`。
- 通过：重启 PC API 到 `0.0.0.0:7001`，新监听 PID 为 `92397`。
- 通过：只读请求 `http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A8787`。
  - `map_display_primary_url=/map`。
  - `map_display_default_zoom_percent=400%`。
  - `map_display_foxglove_web_app_url=https://studio.foxglove.dev`。
  - `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`。
  - `map_display_foxglove_bridge_launch_command=ros2 launch foxglove_bridge foxglove_bridge_launch.xml`。
  - `map_display_sends_motion_when_clicked=false`、`map_display_starts_nav2=false`。
  - 当前真实状态仍是 `status=needs_wheel_rerun`；WYSIWYG 只缺 `camera`，`radar_map_points_visible=true`，`camera_usb_speed=12M`。

## 剩余风险

- 本轮没有启动真实 `foxglove_bridge`，也没有证明 Foxglove Web 已连接到机器人；只完成 PC/API 侧观察入口和合同。
- 完整目标仍未闭环：完整 Nav2 路线同窗口 wheel raw L/R 非零、delivery success、键盘连续手控 wheel L/R 非零和自由移动真实启动读回仍需要现场安全确认后复验。
- 摄像头仍依赖硬件侧恢复首帧；当前 PC 只能继续显示“不是页面独占，而是 UVC/USB 无帧”的只读诊断。
