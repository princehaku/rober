# Camera First Frame Fix Short Aliases

- sprint_type: micro
- owner: User Touchpoint Full-Stack Engineer
- time: 2026-07-02 20:05 CST

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：新增 `camera_first_frame_fix_*` 顶层短字段，复用 `current_camera_wysiwyg_pack_*` 和 `live_wysiwyg_camera_recovery_*`，用于现场直接确认相机首帧恢复动作、USB full-speed 诊断、硬件处理标签、复测顺序和 no-motion 边界。
- `pc-tools/workstation/src/shared/contracts.ts`：补齐 `RobotControlSummaryResponse` 的 `camera_first_frame_fix_*` 可选字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC `plain-current-camera-wysiwyg-pack` 同步暴露 `data-camera-first-frame-fix-*` DOM 合同。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 summary 字段与 DOM 属性。
- `docs/product/pc_tools_workstation.md`：同步说明相机首帧恢复短别名、点击不打开独占采集、不发车、不启动任何运动/建图 runtime。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts`，1 个测试文件、10 个用例通过。
- 通过：`npm test -- test/App.test.ts`，1 个测试文件、237 个用例通过。
- 通过：`npm run build`，TypeScript 与 Vite build 成功；仅保留既有 Vite chunk size 警告。
- 通过：`git diff --check`，无空白错误。
- 通过：重启 PC workstation 到 `0.0.0.0:7001` 后只读调用 `GET /api/robot-control/summary`，读到
  `readback_only=true`、`robot_control_executed=false`、`camera_first_frame_fix_status=needs_first_frame`、
  `camera_first_frame_fix_first_frame_ready=false`、`camera_first_frame_fix_source_diagnosis_status=uvc_full_speed_usb_not_exclusive`、
  `camera_first_frame_fix_hardware_action_required=true`、`camera_first_frame_fix_hardware_action_label=换高速USB后复测`、
  `camera_first_frame_fix_usb_full_speed_detected=true`、`camera_first_frame_fix_usb_speed=12M`、
  `camera_first_frame_fix_blocks_mapping_start=true`、`camera_first_frame_fix_blocks_free_move=false`、
  `camera_first_frame_fix_sends_motion_when_clicked=false`、`camera_first_frame_fix_starts_camera_exclusive_capture=false`、
  `camera_first_frame_fix_starts_nav2=false`、`camera_first_frame_fix_starts_free_roam=false`、
  `camera_first_frame_fix_starts_map_runtime=false`。

## 剩余风险

- 当前改动只补 PC/API 可读合同与前端 DOM，不替代真实硬件处理。
- 真机画面首帧仍需要按现场提示更换高速 USB 口/线或带供电 Hub 后复测。
- 相机首帧缺口继续阻塞建图启动，但不阻塞自由移动。
