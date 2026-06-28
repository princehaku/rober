# 2026-06-29 18:50 PC 相机共享预览下一步白话化

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - 相机 summary 与 MJPEG status 合同新增 `preview_next_action_plain`、`source_diagnosis_next_action_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - Robot Control summary 为相机预览下一步和 source diagnosis 下一步生成普通用户白话。
  - live 的 `uvc_no_frame_not_exclusive` 会明确显示：检查 USB、摄像头输入或供电，必要时换 known-good UVC；共享预览不是页面独占。
- `pc-tools/workstation/src/server/index.ts`
  - `/api/robot-control/camera/mjpeg/status` 同步返回相同白话字段，方便后来进入页面或 curl 只读确认。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏共享预览 guidance 优先使用后端白话字段；旧响应缺字段时才本地翻译 token。
  - 高级诊断露出 `camera_source_diagnosis_next_action_plain` 便于现场对照。
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
  - 增加 summary、MJPEG status 和普通首屏白话下一步断言，防止内部 token 回到用户界面。
- `pc-tools/README.md`
- `docs/product/pc_free_roam_mapping_design.md`
  - 同步记录画面 WYSIWYG 字段和安全边界。

## 验证结果

- 已通过：
  - `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "camera"`
  - `npm --prefix pc-tools/workstation test -- App.test.ts -t "camera"`
  - `npm --prefix pc-tools/workstation test`
  - `npm --prefix pc-tools/workstation run build`
- 已重启：
  - `HOST=0.0.0.0 PORT=7001 npm run api`
- 已完成只读 live 验证：
  - `GET /api/robot-control/camera/mjpeg/status`
    - `proxy_status=status_loaded`
    - `preview_status=source_first_frame_failed`
    - `source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `source_diagnosis_next_action=check_usb_camera_input_power_or_known_good_uvc`
    - `source_diagnosis_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
    - `preview_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
    - `exclusive_camera_claim=false`
    - `robot_control_executed=false`
  - `GET /api/robot-control/summary`
    - `robot_api_connection.status=readable`
    - `readback_summary.camera.status=source_first_frame_failed`
    - `readback_summary.camera.source_diagnosis_status=uvc_no_frame_not_exclusive`
    - `readback_summary.camera.preview_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
    - `readback_summary.camera.source_diagnosis_next_action_plain=检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。`
    - `readback_summary.camera.shared_preview_exclusive_camera_claim=false`
    - `readback_summary.map.radar_overlay_next_action_plain=先启动雷达，再刷新地图画面。`
    - `safe_command_boundary.free_roam_autonomy_start_ready=true`
    - `safe_command_boundary.free_roam_motion_start_ready=true`
    - `safe_command_boundary.nav2_goal_ready=true`
    - `readback_summary.nav2.status=goal_succeeded_wheel_feedback_not_proven`

## 剩余风险

- 本轮只改善“画面当前状态和下一步”的只读解释，不修复真实 UVC 无首帧本身；live 恢复仍需要检查 USB、摄像头输入/供电或换 known-good UVC。
- 本轮不调用真实 Nav2 goal、manual、keyboard、free-roam、delivery、stop、雷达 start 或 `/cmd_vel`；完整 Nav2 路线执行、wheel raw L/R 非零和键盘连续手控仍需要现场安全确认后验证。
