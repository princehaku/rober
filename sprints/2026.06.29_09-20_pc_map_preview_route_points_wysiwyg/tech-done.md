# PC 地图预览路线点所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：地图路线 overlay 优先消费同一轮 `GET /api/robot-control/map/preview` 的 `path_preview_points`；只有 map preview 没有路线点时才回退 summary `o3_proof_summary.path_preview_points`。
- `pc-tools/workstation/test/App.test.ts`：新增回归测试，覆盖 summary 缺路线坐标但 map preview 带路线点时，普通首屏仍绘制当前路线并在安全确认后允许执行这条图上路线。
- `docs/product/pc_tools_workstation.md`：同步说明地图路线画线的数据源优先级和只读边界。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts -t "draws the current route from map preview points when summary route coordinates are missing"`
  - `Test Files  1 passed (1)`
  - `Tests  1 passed | 211 skipped (212)`
- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files  2 passed (2)`
  - `Tests  366 passed (366)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - 仍有既有 Vite chunk size warning：`dist/assets/index-*.js` 大于 500 kB；本轮未扩大处理范围。
- 通过：7001 live 只读读取 `GET http://127.0.0.1:7001/api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `path_preview_points.length=18`
  - `path_preview_point_count=18`
  - `path_preview_frame_id=map`
  - `robot_pose={x:-0.0045,y:0.0091,yaw:0.0055,frame_id:map,source:/amcl_pose}`
  - `radar_overlay.overlay_status=not_current`
  - `radar_overlay.scan_preview_source_point_count=81`
  - `radar_overlay.plain_hint=已有雷达来源点 81 个，但雷达扫描已过期、雷达未运行，所以当前不贴到地图。`
- 通过：7001 live 只读读取 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `safe_command_boundary.nav2_goal_ready=true`
  - `safe_command_boundary.nav2_goal_wheel_feedback_status=goal_succeeded_but_wheel_lr_zero`
  - `readback_summary.nav2.path_preview_point_count=18`
  - `readback_summary.map.radar_overlay_robot_pose_status=map_pose_observed`
  - `readback_summary.map.radar_overlay_status=not_current`
  - `readback_summary.free_roam.status=start_ready`
  - `safe_command_boundary.keyboard_control_status=start_ready`
  - `readback_summary.base.wheel_feedback_latest_raw_left/right=0/0`

## 剩余风险

- 本轮只修 PC 地图路线画线的数据源，不发送 Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。真实完整 Nav2 路线执行、wheel raw L/R 非零、键盘连续手控 HIL 和 delivery success 仍需现场安全确认后单独验证。
