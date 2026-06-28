# PC 键盘 start-ready 状态所见即所得

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`safe_command_boundary` 新增 `keyboard_control_status` 和 `keyboard_control_next_action`，用于明确键盘入口当前是 `start_ready`，而不是已经 armed/active。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 固定输出 `keyboard_control_status=start_ready` 和普通用户下一步说明；`keyboard_control_enabled=false` 仍保持 fail-closed，表示 summary 本身没有武装键盘、没有发 manual/stop。
- `pc-tools/workstation/test/catalog.test.ts`、`pc-tools/workstation/test/App.test.ts`：补齐合同断言和默认 fixture。
- `docs/product/pc_tools_workstation.md`：同步说明 `keyboard_control_enabled=false` 与 `keyboard_control_status=start_ready` 的差异。

## 验证结果

- 通过：`npm --prefix pc-tools/workstation test`
  - `Test Files  2 passed (2)`
  - `Tests  365 passed (365)`
- 通过：`npm --prefix pc-tools/workstation run build`
  - `tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - 仍有既有 Vite chunk size warning：`dist/assets/index-*.js` 大于 500 kB；本轮未扩大处理范围。
- 通过：重启 7001 后读取 `GET http://127.0.0.1:7001/api/robot-control/summary`
  - `safe_command_boundary.keyboard_control_status=start_ready`
  - `safe_command_boundary.keyboard_control_start_ready=true`
  - `safe_command_boundary.keyboard_control_enabled=false`
  - `safe_command_boundary.keyboard_control_mode=bounded_repeating_manual_pulse`
  - `safe_command_boundary.keyboard_manual_command_mode=ros`
  - `safe_command_boundary.keyboard_control_next_action=勾选现场安全确认后点击启用键盘；按住 W/A/S/D 或方向键才会连续低速移动，松开/失焦/切页会停`
  - `safe_to_control=false`
  - `primary_actions_enabled=false`
- 通过：只读 `GET http://127.0.0.1:7001/api/robot-control/map/preview`
  - `proxy_status=preview_forwarded`
  - `robot_control_executed=false`
  - `path_preview_point_count=18`
  - `robot_pose.frame_id=map`

## 剩余风险

- 本轮不发送键盘 pulse、不做真实连续手控 HIL；PC 键盘连续控制完成仍需要现场安全确认后按住方向键验证、读取 wheel raw L/R 非零并确认 stop 成功。
