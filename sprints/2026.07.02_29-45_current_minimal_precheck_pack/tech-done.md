# Current minimal precheck pack

## sprint_type

micro

## 实际改动

- `GET /api/robot-control/summary` 新增 `current_minimal_precheck_pack_*` 顶层字段，直接输出当前运动动作的发车前预检状态。
- 普通首屏新增 `plain-current-minimal-precheck-pack` DOM 读回，说明 Nav2 图上行程、键盘连续手控和自由自助移动只要求现场安全确认；相机、雷达、现场报告和路线 WYSIWYG 不作为额外发车前置。
- 共享 TypeScript contract、Vue fixture 和 summary 单测补齐该包的 action、precheck 和 no-motion 边界。
- `docs/product/pc_tools_workstation.md` 同步记录产品边界：相机和雷达 ready 仍只影响建图启动/验收，不阻塞自由移动或运动复验动作。

## 验证结果

- `npm test -- --run robotControlSummary.test.ts App.test.ts`
  - 结果：通过，`2 passed`，`247 passed`。
- `npm run build`
  - 结果：通过，产物包含 `dist/index.html`、`dist/assets/index-CV6yLOmZ.css`、`dist/assets/index-3y0z4rbN.js`。
  - 备注：Vite 仍提示单 chunk 大于 500 kB，这是既有体积警告，不影响本轮功能验证。
- `npm run lint`
  - 结果：通过。
- `git diff --check`
  - 结果：通过，无空白错误。
- `GET http://127.0.0.1:7001/map`
  - 结果：HTTP `200 OK`。
- `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 只读 live 读回：
  - `current_minimal_precheck_pack_status=safety_confirm_only`
  - `current_minimal_precheck_pack_action_ids=["run_nav2_route","hold_keyboard","start_free_move"]`
  - `current_minimal_precheck_pack_requires_safety_confirm=true`
  - `current_minimal_precheck_pack_minimal_precheck_safety_only=true`
  - `current_minimal_precheck_pack_camera_preflight_required=false`
  - `current_minimal_precheck_pack_radar_preflight_required=false`
  - `current_minimal_precheck_pack_operator_report_preflight_required=false`
  - `current_minimal_precheck_pack_route_wysiwyg_preflight_required=false`
  - `current_minimal_precheck_pack_camera_and_radar_display_only_for_motion=true`
  - `current_minimal_precheck_pack_mapping_still_requires_camera_and_radar_ready=true`
  - `current_minimal_precheck_pack_sends_motion_when_clicked=false`
  - `current_minimal_precheck_pack_starts_nav2_when_clicked=false`
  - `current_minimal_precheck_pack_starts_manual_when_clicked=false`
  - `current_minimal_precheck_pack_starts_keyboard_when_clicked=false`
  - `current_minimal_precheck_pack_starts_free_roam_when_clicked=false`
  - `current_minimal_precheck_pack_starts_map_runtime_when_clicked=false`
  - `current_minimal_precheck_pack_submits_delivery_when_clicked=false`
  - `current_minimal_precheck_pack_stops_motion_when_clicked=false`
- 同一 live 读回也确认地图/ROS2 配套口径：
  - `map_display_primary_url=/map`
  - `map_display_default_zoom_percent=3200%`
  - `map_display_max_zoom_percent=6400%`
  - `map_display_rviz_launch_command="ros2 launch ros2_trashbot_bringup rviz.launch.py"`
  - `map_display_foxglove_bridge_launch_command="ros2 launch ros2_trashbot_bringup foxglove_bridge.launch.py"`
  - `map_display_foxglove_websocket_url=ws://192.168.1.11:8765`

## 剩余风险

- 本包只证明 PC summary/DOM 的最小预检口径，不等于真实 HIL 已完成。
- wheel raw L/R 非零、完整 Nav2 路线执行、delivery success、相机首帧和建图 ready 仍需现场继续验证。
