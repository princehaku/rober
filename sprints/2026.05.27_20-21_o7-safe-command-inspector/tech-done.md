# 2026.05.27 20-21 O7 Safe Command Inspector

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/o7CloudArchiveTasks.ts` 为 selected task 新增 `safe_command_inspector`，只读读取 `command_session`、`commands[]`、`manual_turn_envelope`、`navigate_goal_envelope`、`velocity_limits`、`steering_limits`、`map_goal_slot`、`idempotency_key_requirement`、`confirmation_policy`、`robot_ack_status` / `command_ack` 等白名单字段。
- 在 `pc-tools/workstation/src/shared/contracts.ts` 新增 `O7SafeCommandInspector` 契约，并把 archive fixed false 字段补齐 KR6 的 command dispatch、manual、navigate、keyboard、robot ACK 开关。
- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 `O7 Previews > Cloud Archive Tasks` 增加 selected task 级 KR6 检查视图，只展示 command session、sample commands、envelope、limits、map goal slot、idempotency/confirmation、ACK blocked summary、evidence gaps 和 false fields，不新增任何动作按钮。
- 更新 `pc-tools/workstation/test/catalog.test.ts` 和 `pc-tools/workstation/test/App.test.ts`，覆盖 KR6 inspector 正常摘要、fail-closed 样本清空、UI 可见字段和动作按钮禁用边界。
- 更新 `docs/product/pc_tools_workstation.md` 和 `docs/interfaces/o7_cloud_archive_task_api.md`，同步 Cloud Archive Tasks 的 KR6 inspector 契约、fail-closed 规则和 UI 边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite 输出 `✓ built in 2.06s`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 32 passed (32)`。
- `cd pc-tools/workstation && npm run lint`：通过，无输出错误。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_20-21_o7-safe-command-inspector`：通过，无 whitespace error。

## 剩余风险

- 本轮仍是 PC-only/read-only software proof，不连接真实 cloud command API、robot ACK、Nav2、键盘控制、地图点击、底盘或 HIL。
- `safe_command_inspector` 只证明 archive fixture 的 KR6 数据形状能被检查；真实手控/自动寻路下发仍需要云端 command API、机器人 ACK、timeout/cancel/stop/recovery trace 和硬件安全证据。
