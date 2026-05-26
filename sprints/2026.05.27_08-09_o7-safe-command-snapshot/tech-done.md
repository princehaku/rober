# O7 Safe Command Snapshot Micro Sprint

sprint_type: micro

## 实际改动

- 在 `cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py` 新增 `safe_command_snapshot`，schema 为 `trashbot.o7.safe_command_snapshot.v1`，固定 `source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`。
- 在 `pc-tools/workstation/src/shared/contracts.ts` 和 `pc-tools/workstation/src/server/o7OperatorConsole.ts` 同步 TypeScript contract 与 Node API 响应，展示 manual turn envelope、velocity/steering limits、navigate goal envelope、map goal slot、cloud command endpoint、idempotency key requirement、confirmation policy、robot ACK status、timeout/cancel/stop/recovery evidence gaps 和 next required evidence。
- 在 `pc-tools/workstation/src/components/O7OperatorConsolePanel.vue` 新增只读 Safe command snapshot 面板，不增加按钮、键盘绑定、地图点击下发或任何真实 dispatch 行为。
- 在 `pc-tools/workstation/test/App.test.ts` 和 `pc-tools/workstation/test/catalog.test.ts` 增加 fail-closed 断言，覆盖 KR6 固定 false 开关、future disabled endpoint、幂等键、确认策略、ACK 缺口和 recovery 缺口。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`，明确该 snapshot 只是 O7-KR6 契约槽位，不证明真实手控、速度控制、键盘控制、自动寻路、robot ACK、cancel/stop/recovery 或底盘安全。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 29 modules transformed.`、`✓ built in 1.95s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  16 passed (16)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：命令退出码为 0，无 lint 报错。
- 通过：`python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`
  - 关键输出：命令退出码为 0，无 Python 编译错误。
- 通过：`git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_08-09_o7-safe-command-snapshot`
  - 关键输出：命令退出码为 0，无 whitespace error。

## 剩余风险

- 当前证据边界仍为 `software_proof`，未连接真实云端 command API、真实 robot-side ACK、真实 cancel/stop/recovery、真实 HIL 或受控现场安全证据。
- 本轮按要求不修改 `OKR.md`，不提升 O7 百分比。
