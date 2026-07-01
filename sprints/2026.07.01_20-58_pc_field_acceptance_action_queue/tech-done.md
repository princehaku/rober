# PC 现场验收行动队列

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-action-queue`。
  - 行动队列直接显示 ready / blocked / completed 数量、可先验动作、暂不可做动作和当前安全确认状态。
  - 队列里的 ready 动作按钮只聚焦到目标卡片，不执行 Nav2、manual、keyboard、free-roam、建图、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 增加行动队列 DOM、ready 动作按钮和 no-motion 聚焦行为断言。
- `docs/product/pc_tools_workstation.md`
  - 记录行动队列合同。

## 当前现场事实

- `GET http://127.0.0.1:7001/api/robot-control/summary` 显示：
  - `field_acceptance_ready_step_ids=["run_nav2_route","hold_keyboard","start_free_move"]`
  - `field_acceptance_blocked_step_ids=["start_mapping_when_sensors_ready"]`
  - `field_acceptance_next_step_id=run_nav2_route`
  - `free_move_start_ready=true`
  - `mapping_start_missing_reasons=["camera_first_frame"]`
  - `live_wysiwyg_missing_surface_ids=["camera"]`
  - `radar_map_points_visible=true`
  - `camera_usb_speed=12M`
  - `camera_hardware_action_label=换高速USB后复测`

## 验证结果

- 已通过：`npm --prefix pc-tools/workstation test -- --run test/App.test.ts`
  - `Test Files 1 passed (1)`
  - `Tests 233 passed (233)`
- 已通过：`npm --prefix pc-tools/workstation test -- --run test/robotControlSummary.test.ts test/catalog.test.ts`
  - `Test Files 2 passed (2)`
  - `Tests 190 passed (190)`
- 已通过：`npm --prefix pc-tools/workstation run lint`
- 已通过：`npm --prefix pc-tools/workstation run build`
  - Vite 输出既有 chunk size warning；构建成功。
- 已通过：`npm --prefix pc-tools/workstation test -- --run`
  - `Test Files 3 passed (3)`
  - `Tests 423 passed (423)`
- 已通过：重启 `0.0.0.0:7001`
  - 当前监听：`node` PID `3552`，`TCP *:7001 (LISTEN)`
  - `GET http://127.0.0.1:7001/` -> `200`
  - `GET http://127.0.0.1:7001/map` -> `200`
  - `GET http://127.0.0.1:7001/api/robot-control/summary` 只读 smoke 读到：`field_acceptance_ready_step_ids=["run_nav2_route","hold_keyboard","start_free_move"]`、`field_acceptance_blocked_step_ids=["start_mapping_when_sensors_ready"]`、`field_acceptance_next_step_id=run_nav2_route`、`live_wysiwyg_missing_surface_ids=["camera"]`、`radar_map_points_visible=true`、`camera_usb_speed=12M`、`camera_hardware_action_label=换高速USB后复测`、`mapping_start_missing_reasons=["camera_first_frame"]`。

## 剩余风险

- 本轮仍未执行任何运动控制；完整行程、键盘连续手控和自由移动虽然 ready，但实车完成需要现场安全确认后另行执行并读回。
- 建图仍阻塞在相机首帧，当前诊断为 USB 12M full-speed，需要换高速 USB 后复测。
- 未触碰两份历史 dirty artifact：`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/camera_frame_quality_dom_smoke.json`、`sprints/2026.06.11_18-00_pc_simple_user_console_repair/artifacts/pc_plain_user_home_dom_smoke.json`。
