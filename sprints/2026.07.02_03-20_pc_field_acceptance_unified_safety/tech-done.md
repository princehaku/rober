# PC 现场验收统一安全确认

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在 `plain-field-acceptance-packet` 顶部新增 `plain-field-acceptance-safety-gate`。
  - 该 checkbox 直接复用既有 `plainUnifiedSafetyConfirmed`，勾一次同步行程、键盘和自由移动的安全确认状态。
  - `plain-field-acceptance-next` 与 `plain-field-acceptance-primary` 文案会随勾选状态从“先勾现场安全确认”切换为“安全确认已勾”。
  - 勾选本身只更新本地确认状态，不发送任何控制请求。
- `pc-tools/workstation/src/styles.css`
  - 为验收卡内统一安全确认补充轻量样式。
- `pc-tools/workstation/test/App.test.ts`
  - 覆盖验收卡安全确认 DOM 合同、勾选不触发 fetch、同步全局安全确认、文案联动和 no-motion 边界。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 `plain-field-acceptance-safety-gate` 合同。

## 验证结果

- 已通过：`git diff --check`。
- 已通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。Vite 仍提示单 bundle 超过 500 kB，这是既有体积警告，不影响本轮验收。
- 已通过：`cd pc-tools/workstation && npm test`，3 files / 421 tests passed。
- 已通过：重启 PC workstation 到 `0.0.0.0:7001`，新 listener PID `52195`。
- 已通过：只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `status=needs_wheel_rerun`、`field_acceptance_packet.next_step_id=run_nav2_route`、`next_step_requires_safety_confirm=true`、`minimal_precheck_safety_only=true`、`ready_step_ids=[run_nav2_route,hold_keyboard,start_free_move]`、`blocked_step_ids=[start_mapping_when_sensors_ready]`、`field_acceptance_packet.sends_motion_when_clicked=false`。
- 已通过：只读检查 `http://127.0.0.1:7001/assets/index-DbCC5SWi.js`，bundle 包含 `plain-field-acceptance-safety-gate`、`plain-field-acceptance-safety-confirm` 和 `勾一次，行程、键盘和自由移动都生效`。

## 剩余风险

- 本轮只把“勾一次即可”的确认入口前置到现场验收卡，没有执行真实运动命令。
- 完整目标仍缺现场实测证据：Nav2 路线同窗口轮速 L/R 非零、键盘按住窗口轮速、自由移动 latest 运行读数、相机首帧 ready 后建图。
