# Current Mapping Camera Hardware Action

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 在 `current_mapping_action_*` 顶层 alias 中补充相机硬件诊断字段：是否需要硬件动作、动作 label、USB 是否 full-speed、USB 速度、相机诊断状态、是否已排除页面独占、相机恢复下一步。
  - 字段与既有 `camera_*` / `live_closure_summary.camera_*` 同源，只读展示，不新增发车、建图、Nav2、manual、keyboard、delivery、stop 或 `/cmd_vel` 调用。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏 `plain-current-mapping-action` 在“只差画面首帧”时直接显示相机硬件动作，例如 USB 12M full-speed、不是页面独占、换高速 USB/带供电 Hub 后复测。
  - DOM 同步暴露 `data-current-mapping-action-camera-*` 证据字段，方便现场 smoke 和脚本验收。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 扩展 `RobotControlSummaryResponse` 的 `current_mapping_action_camera_*` 可选字段。
- `docs/product/pc_tools_workstation.md`
  - 同步当前建图动作 alias 合同，明确相机硬件诊断只读展示边界。
- `pc-tools/workstation/test/App.test.ts`
  - 补普通首屏 DOM 断言，覆盖默认无硬件动作和 USB 12M full-speed 需要换高速 USB 后复测两种形态。
- `pc-tools/workstation/test/robotControlSummary.test.ts`
  - 补 summary alias 断言，确认当前建图动作继承相机 USB full-speed 诊断。
- `pc-tools/workstation/test/catalog.test.ts`
  - 补 catalog smoke 断言，确认 `current_mapping_action_camera_*` 与 summary 顶层 `camera_*` 同源。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run App.test.ts catalog.test.ts robotControlSummary.test.ts`
  - `Test Files 3 passed (3)`，`Tests 428 passed (428)`。
- 通过：`cd pc-tools/workstation && npm run build`
  - Vite build 成功，仅保留既有 chunk size warning。
- 通过：`cd pc-tools/workstation && npm run lint`
- 通过：`git diff --check`
- 通过：PC `0.0.0.0:7001` live smoke
  - 服务 PID `29247`，`/` 和 `/map` 均返回 `200 text/html; charset=utf-8`。
  - `GET /api/robot-control/summary` 返回 `current_mapping_action_missing_evidence=["camera_first_frame"]`、`current_mapping_action_only_camera_missing=true`、`current_mapping_action_radar_overlay_wysiwyg_complete=true`、`current_mapping_action_camera_hardware_action_required=true`、`current_mapping_action_camera_hardware_action_label=换高速USB后复测`、`current_mapping_action_camera_usb_speed=12M`、`current_mapping_action_camera_source_diagnosis_not_exclusive=true`、`current_mapping_action_blocks_free_move=false`。
  - `GET /api/robot-control/camera/mjpeg/status` 返回 `readback_only=true`、`sends_motion_when_clicked=false`、`source_usage_status=not_in_use`、`source_usage_owner_count=0`、`camera_usb_speed=12M`、`camera_hardware_action_required=true`。

## 当前实机读回

- PC summary 显示当前建图只剩 `camera_first_frame`。
- 相机状态为 `source_first_frame_failed`，已排除页面独占：`source_usage_status=not_in_use`、`source_usage_owner_count=0`、`source_diagnosis_not_exclusive=true`。
- 相机 USB 拓扑为 `12M` full-speed，诊断提示换高速 USB 口/线或带供电 USB Hub 后复测。
- 该缺口阻塞建图首帧，不阻塞自由移动。

## 剩余风险

- 当前软件已把诊断和下一步直接暴露到普通 PC 首屏，但真实画面恢复仍需要现场处理 USB 接口、线材、供电或摄像头设备本身。
- 本轮不改上车 camera service 捕获策略，不改变任何运动门禁。
