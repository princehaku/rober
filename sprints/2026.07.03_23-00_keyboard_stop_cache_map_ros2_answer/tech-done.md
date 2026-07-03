# 2026.07.03 23:00 Keyboard Stop Cache / Map ROS2 Answer

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/index.ts`
  - 为固定 `/api/robot-control/base/manual` 与 `/api/robot-control/base/stop` 增加 120 秒内存键盘证据缓存，按规范化 Robot API 地址隔离。
  - summary/live-summary 合并浏览器 query 与 PC Node 最近代理证据；manual 只累计连续 pulse 与运动信号，stop 只确认松手 stop 已转发。
  - wheel raw L/R 非零单独缓存为 `wheel_feedback_lr_nonzero_proven`，不把 IMU 或 `motion_signal_observed` 当成 wheel proof。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 扩展 `RobotControlKeyboardLocalEvidence.wheel_feedback_lr_nonzero_proven`。
  - 顶层 `keyboard_wheel_lr_nonzero` 改为真正读取键盘卡 wheel evidence，不再跟 `keyboard_continuous_motion_verified` 混用。
- `pc-tools/workstation/test/catalog.test.ts`
  - 新增 HTTP 回归：不带 keyboard query 时，forward/back/stop 后 summary 能读到 `keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`，但 wheel raw 仍保持 false。
- `pc-tools/README.md`
  - 补充 23:00 CST 现场读回和地图/ROS2 配套口径。
- `docs/product/pc_tools_workstation.md`
  - 同步产品边界：PC 大地图是普通用户入口，RViz2/Foxglove 是工程观察；IMU 运动信号不能替代 WAVE ROVER wheel raw L/R 非零。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts -t "workstation summary reuses recent manual and stop evidence without keyboard query"`：通过，1 passed。
- `cd pc-tools/workstation && npm test -- --run test/robotControlSummary.test.ts`：通过，16 passed。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 均成功。
- `cd pc-tools/workstation && npm test -- --run test/catalog.test.ts`：通过，190 passed。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "opens direct map view from URL without starting ROS2 or motion"`：通过。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "keeps legacy query direct map URL compatible"`：通过。
- `cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "refreshes stale radar overlay proof on direct map entry without starting radar lifecycle"`：通过。
- PC Node 已重启为 `HOST=0.0.0.0 PORT=7001 npm run api`，监听 `*:7001`。
- 现场 `curl` 验证：
  - forward/back manual 均 `proxy_status=command_forwarded`、`base_command_mode=ros`、`feedback_mode=realtime`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`、`imu_attitude_delta_observed=true`。
  - stop 为 `proxy_status=command_forwarded`、`status=stopped`。
  - stop 后 summary：`keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`、`keyboard_wheel_lr_nonzero=false`。
  - 雷达只读刷新后 summary：`map_preview_status=loaded`、`path_preview_point_count=18`、`route_target_visible=true`、`robot_pose_status=map_pose_observed`、`radar_overlay_status=loaded`、`radar_overlay_current_point_count=40`。
  - 地图/ROS2 summary 合同：默认 `800%`、`/map` 默认 `800%`、最高 `1200%`、`适配` 为 `45%`；ROS2 配套答案为本地 RViz2、远程 Foxglove bridge + Foxglove Web，普通用户仍用 PC 大地图和 `/map`。

## 剩余风险

- 摄像头当前仍无真实首帧，`camera_input_signal_check_required=true`，需要检查输入信号、视频线、接口、供电或换 known-good UVC 后复测。
- WAVE ROVER wheel raw L/R 非零仍未证明，当前 manual 回包为 `wheel_feedback_latest_raw_left/right=0/0`。
- 内置浏览器插件两次未能 attach webview；本轮使用 API 合同、Vitest DOM 用例和现场 curl 验证地图大屏/ROS2 配套，未产出浏览器截图。
