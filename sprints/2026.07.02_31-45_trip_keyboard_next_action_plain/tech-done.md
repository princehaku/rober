# Trip And Keyboard Next Action Plain

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：为完整 Nav2 行程控制包和 PC 键盘连续手控控制包补齐 `*_next_action_plain`。
- `pc-tools/workstation/src/shared/contracts.ts`：补充 `current_trip_execution_pack_next_action_plain`、`current_keyboard_control_pack_next_action_plain` 类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-current-trip-execution-pack`、`plain-current-keyboard-control-pack` 同步暴露 `data-next-action-plain`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：覆盖 API 和 DOM 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录 Nav2/键盘下一步白话字段边界。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts test/App.test.ts`，`Test Files 2 passed (2)`，`Tests 247 passed (247)`。
- 通过：`npm run build`，TypeScript app/server 与 Vite build 均完成；仅保留既有 Vite chunk size warning。
- 通过：`git diff --check`。
- 通过：重启 `0.0.0.0:7001` 后 live 读取 `/api/health`，确认 `workstation_listen_address=http://0.0.0.0:7001`、`default_robot_api_base_url=http://192.168.1.11:8787`。
- 通过：live 读取 `/api/robot-control/summary`，确认 `current_trip_execution_pack_next_action_plain=勾现场安全确认后执行图上 Nav2 行程；执行后按地图、最近行程、轮速、送达和总览顺序只读复验。`。
- 通过：live 读取 `/api/robot-control/summary`，确认 `current_keyboard_control_pack_next_action_plain=勾现场安全确认后点击启用键盘；启用不发车，按住 W/A/S/D 或方向键才连续低速移动，松开后只读复验轮速和停止。`。

## 剩余风险

- 本轮只补 PC 端只读易用性字段，不发送真实 Nav2 或键盘运动命令。
- 真实 Nav2 wheel L/R 非零、delivery success、键盘按住轮速与松开停稳，仍需现场安全确认后 HIL 验证。
