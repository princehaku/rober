# Summary 顶层四项目标 Alias

## Sprint 类型

sprint_type: micro

## 实际改动

- `GET /api/robot-control/summary` 顶层新增四项目标总览 alias，全部与 `live_closure_summary` 同源：
  - WYSIWYG：`live_wysiwyg_ready`、`live_wysiwyg_missing_surface_ids`、`live_wysiwyg_primary_refresh_endpoint`、`live_wysiwyg_refresh_sends_motion=false`
  - 画面/雷达贴图：`camera_current_visible`、`radar_map_points_visible`、`radar_overlay_status`、`radar_overlay_current_point_count`、`radar_overlay_source_point_count`
  - 键盘连续控制：`keyboard_ready`、`keyboard_continuous_ready`、`keyboard_continuous_motion_verified`、`keyboard_enable_sends_motion=false`、`keyboard_manual_endpoint`、`keyboard_stop_endpoint`、`keyboard_feedback_readback_endpoint`
  - 自由移动：`free_move_start_ready`、`free_roam_ready`、`free_roam_motion_start_ready`、`free_roam_motion_ready`、`free_move_without_camera_allowed=true`、`free_roam_motion_without_radar_allowed=true`
  - 建图启动：`mapping_start_ready`、`mapping_start_missing_reasons`、`free_roam_mapping_start_ready`、`free_roam_mapping_start_missing_reasons`
- 同步更新 `RobotControlSummaryResponse` contract、`robotControlSummary.test.ts`、`catalog.test.ts` 和 `docs/product/pc_tools_workstation.md`。

## 验证结果

- `npm test -- --run test/robotControlSummary.test.ts -t "map"`：通过，1 个 test file，5 passed，4 skipped。
- `npm test -- --run test/catalog.test.ts -t "live-summary"`：通过，1 个 test file，1 passed，180 skipped。
- `npm test`：通过，3 个 test files，421 passed。
- `npm run lint`：通过。
- `npm run build`：通过；Vite 仍有既有 chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，当前监听 PID `66615`。
- 真实只读 `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787` 顶层读回：
  - `live_wysiwyg_ready=false`
  - `live_wysiwyg_missing_surface_ids=["camera","radar_map_points"]`
  - `live_wysiwyg_primary_refresh_endpoint=/api/robot-control/camera/first-frame/probe`
  - `live_wysiwyg_refresh_sends_motion=false`
  - `camera_current_visible=false`
  - `radar_map_points_visible=false`
  - `radar_overlay_status=not_current`
  - `radar_overlay_current_point_count=0`
  - `radar_overlay_source_point_count=181`
  - `keyboard_ready=true`
  - `keyboard_continuous_ready=true`
  - `keyboard_continuous_motion_verified=false`
  - `keyboard_enable_sends_motion=false`
  - `keyboard_manual_endpoint=/api/robot-control/base/manual`
  - `keyboard_stop_endpoint=/api/robot-control/base/stop`
  - `keyboard_feedback_readback_endpoint=/api/robot-control/base/feedback-samples`
  - `free_move_start_ready=true`
  - `free_roam_ready=true`
  - `free_roam_motion_start_ready=true`
  - `free_roam_motion_ready=false`
  - `free_move_without_camera_allowed=true`
  - `free_roam_motion_without_radar_allowed=true`
  - `mapping_start_ready=false`
  - `mapping_start_missing_reasons=["camera_first_frame"]`
  - `free_roam_mapping_start_ready=false`
  - `free_roam_mapping_start_missing_reasons=["camera_first_frame"]`

## 剩余风险

- 本轮只修 summary 顶层读数，不改变任何真实控制 gate。
- 当前真实 WYSIWYG 仍缺相机首帧和雷达当前贴图；需要现场硬件动作或 no-motion 刷新后复验。
- 本轮不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop，也不发布 `/cmd_vel`。
