# PC 只剩相机 WYSIWYG 缺口范围

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 增强 `plain-field-acceptance-camera-proof`。
  - 当现场验收只剩 `camera` 缺口时，可见文案直接显示“唯一所见缺口是画面；阻塞建图首帧，不挡自由移动”。
  - DOM 新增 `data-camera-only-wysiwyg-gap` 和 `data-camera-scope-plain`。
- `pc-tools/workstation/test/App.test.ts`
  - 默认多缺口场景覆盖“当前所见缺口包含画面”。
  - camera-only + USB 12M 场景覆盖“唯一所见缺口是画面”、USB full-speed、换高速 USB 后复测、不挡自由移动、不启动任何 motion/control endpoint。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 camera-only WYSIWYG scope 合同。

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
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，新监听 PID `44733`。
- 已通过：只读 smoke `GET /` 和 `GET /map` 均返回 200。
- 已通过：只读 summary smoke `GET /api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `status=needs_wheel_rerun`。
  - `field_acceptance_wysiwyg_missing_surface_ids=[camera]`。
  - `camera_current_visible=false`、`camera_usb_speed=12M`、`camera_hardware_action_label=换高速USB后复测`。
  - `camera_blocks_mapping_start=true`、`camera_blocks_free_move=false`。
  - `radar_map_points_visible=true`、`radar_overlay_status=loaded`。
  - `mapping_start_missing_reasons=[camera_first_frame]`。
  - `free_move_start_ready=true`。

## 剩余风险

- 本轮只改 PC 现场验收卡的只读文案和 DOM 合同，没有执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- 画面 WYSIWYG 仍未完成，当前需要现场换高速 USB 口/线或带供电 Hub 后复测。
- 完整 Nav2 路线执行、键盘连续控制和自由移动运行读数仍需现场安全确认后实机复验。
