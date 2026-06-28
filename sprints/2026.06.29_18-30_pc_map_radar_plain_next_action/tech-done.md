# 2026-06-29 18:30 PC 地图雷达下一步白话化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 给地图雷达 overlay 合同新增 `next_action_plain` 与顶层 alias `radar_overlay_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `mapRadarOverlayExplanation()` 统一返回 token 与普通用户白话动作。
  - `GET /api/robot-control/summary` 与 `GET /api/robot-control/map/preview` 同步透出白话下一步，避免直连调试看到内部 token 后不知道该按哪个按钮。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图卡和雷达卡优先使用后端白话动作；旧 summary 没有新字段时补齐 `refresh_radar_scan_for_map_overlay`、`refresh_map_radar_overlay`、`start_or_refresh_radar` 等 token 的本地翻译。
- `pc-tools/workstation/test/catalog.test.ts`
  - 增加 summary 与 map preview alias 的白话 next action 断言。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 记录地图/雷达 WYSIWYG 下一步白话字段和安全边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "radar overlay"`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- 已重启：
  - `HOST=0.0.0.0 PORT=7001 npm run api`
- 已完成只读 live 验证：
  - `GET /api/robot-control/summary`
    - `robot_api_connection.status=readable`
    - `readback_summary.camera.status=source_first_frame_failed`
    - `readback_summary.camera.source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `readback_summary.map.radar_overlay_status=not_current`
    - `readback_summary.map.radar_overlay_next_action=start_radar_then_refresh_map_preview`
    - `readback_summary.map.radar_overlay_next_action_plain=先启动雷达，再刷新地图画面。`
    - `safe_command_boundary.free_roam_autonomy_start_ready=true`
    - `safe_command_boundary.free_roam_motion_start_ready=true`
    - `safe_command_boundary.nav2_goal_ready=true`
    - `safe_command_boundary.nav2_goal_next_action=上次路线 action 成功但 wheel raw L/R=0/0 未非零；已看到非零底盘命令和 IMU 姿态变化，主因不是雷达、相机或 controller；勾选行程前安全确认后用 ROS 重跑图上路线；执行时会自动启动自动驾驶 runtime`
  - `GET /api/robot-control/map/preview`
    - `proxy_status=preview_forwarded`
    - `radar_overlay_status=not_current`
    - `radar_overlay_next_action_plain=先启动雷达，再刷新地图画面。`
    - `radar_overlay.next_action_plain=先启动雷达，再刷新地图画面。`
    - `radar_overlay_count=0`
    - `radar_overlay_source_count=81`

## 剩余风险

- 本轮不调用真实雷达 start、Nav2 goal、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；真实“自动驾驶能动”和 wheel raw L/R 非零仍需现场安全确认后重跑验证。
- live 摄像头当前结论仍是 `uvc_no_frame_not_exclusive`：多人共享预览链路不是独占，但 UVC 源没有首帧，仍需要检查 USB/输入/供电或换 known-good UVC。
