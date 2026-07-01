# PC 相机 USB 后复测按钮

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 新增 `plainFieldAcceptanceWysiwygRefreshButtonLabel`。
  - 当现场验收只剩 `camera` 缺口，且 summary 显示 USB full-speed/硬件动作时，`plain-field-acceptance-wysiwyg-refresh` 按钮显示“换USB后复测画面”。
  - pending 状态仍沿用原有刷新中提示，避免用户不知道正在复测。
- `pc-tools/workstation/test/App.test.ts`
  - camera-only + USB 12M 场景断言 field acceptance 复测按钮显示“换USB后复测画面”。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 camera-only/full-speed 时的按钮文案合同。

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`，`Tests 235 passed (235)`。
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`，`Tests 190 passed (190)`。
- 已通过：`git diff --check`。
- 已通过：`npm --prefix pc-tools/workstation run lint`。
- 已通过：`npm --prefix pc-tools/workstation run build`。
  - Vite 仍提示单 chunk 超过 500 kB 的既有 warning，构建成功。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`，`Tests 425 passed (425)`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，新监听 PID `54651`。
- 已通过：只读 smoke `GET /` 和 `GET /map` 均返回 200。
- 已通过：只读 summary smoke `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_wysiwyg_missing_surface_ids=[camera]`。
  - `camera_usb_speed=12M`、`camera_usb_full_speed_detected=true`。
  - `camera_hardware_action_required=true`、`camera_hardware_action_label=换高速USB后复测`。
  - `radar_overlay_status=loaded`。
  - `free_move_start_ready=true`。
  - `mapping_start_missing_reasons=[camera_first_frame]`。

## 剩余风险

- 本轮只改 PC 按钮文案和只读 DOM/UI 合同，没有执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 画面 WYSIWYG 仍需要现场换高速 USB 口/线或带供电 Hub 后复测。
- 完整 Nav2 路线执行、键盘连续控制和自由移动运行读数仍需现场安全确认后实机复验。
