# O7 Safe Command Fixture Preview

sprint_type: micro

## 实际改动

- 新增 PC-only 只读 API：`GET /api/o7/safe-command-preview?fixtureJson=<local-json>`，输入 schema 为 `trashbot.o7.safe_command_fixture.v1`，输出 schema 为 `trashbot.o7.safe_command_preview.v1`。
- 新增 `pc-tools/workstation/src/server/o7SafeCommandPreview.ts`，只读取用户显式指定的本地 JSON fixture，并输出手控/寻路安全摘要：command session、manual turn envelope、navigate goal envelope、velocity/steering limit summaries、map goal slot、idempotency key、confirmation policy、robot ACK blocked summary、evidence gaps 和 audit/evidence refs。
- 更新共享契约、catalog export、Express route、API route 列表和 Vitest，固定 `source=software_proof`、`proof_status=not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`pc_only=true`、`command_dispatch_enabled=false`、`manual_control_enabled=false`、`navigate_goal_enabled=false`、`keyboard_control_enabled=false`、`real_command_api_connected=false`、`real_robot_ack_connected=false`、`robot_control_executed=false`。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 和 `docs/product/pc_tools_workstation.md`，明确该 preview 不连接云端、ROS2、Nav2、硬件、WAVE ROVER 或串口，不发送命令，不提供方向键、地图点击、stop/cancel/recovery 按钮，也不把 fixture limits 解释为 HIL 或真实安全限制。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 完成，Vite 输出 `✓ built in 1.99s`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 25 passed (25)`。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无错误输出。
- `git diff --check -- pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_13-14_o7-safe-command-fixture-preview`：通过，无 whitespace error 输出。

## 剩余风险

- 本轮只完成后端契约 preview 和文档，不修改 UI；PC 端后续展示仍需单独接入该 API。
- 该结果是 software proof，不证明真实 command API、真实 robot ACK、真实 timeout/cancel/stop/recovery、真实 Nav2 goal dispatch、真实键盘控制、真实手控、真实 HIL/硬件安全或真实 delivery success。
- 本轮未修改 `OKR.md`，不提升 O7 百分比。
