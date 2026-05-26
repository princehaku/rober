# O7 Safe Command Review Panel

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 Safe command inspector 区域新增 PC-only 本地 safe command review panel。
- panel 加载 archive 后默认聚焦第一条 `sample_commands`，提供 `Previous command`、`Next command`、`Reset command cursor`，这些按钮只改变浏览器本地 cursor，不调用 API、不写后端、不发送命令。
- panel 展示当前 command 的 `command_id`、`command_type`、`status`、`envelope_ref`、`idempotency_key_ref`、`evidence_ref`，并继续展示 manual turn envelope、navigate goal envelope、idempotency key requirement、confirmation policy、robot ACK blocked summary、evidence gaps 和关键 false 字段。
- 在 `pc-tools/workstation/test/App.test.ts` 补充两条 command sample，验证 Next/Reset command cursor 后 fetch 调用数量不增加，并验证 ACK blocker 和关键 false fields 仍可见。
- 同步更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`，明确该 panel 是本地 fixture 安全审核，不等于真实 command API、真实手控、真实寻路下发、真实 robot ACK、真实 stop/cancel/recovery 或硬件安全。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键日志：`✓ built in 2.36s`，server/app TypeScript 构建均退出 0。
- `cd pc-tools/workstation && npm run test`：通过。关键日志：`Test Files  2 passed (2)`、`Tests  35 passed (35)`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 退出 0。
- `git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_27-28_o7-safe-command-review-panel`：通过，无 whitespace error。

## 剩余风险

- 本轮仍是 PC-only、本地 fixture 审核体验，没有接入真实 command API、Nav2、键盘控制、地图点击、串口、WAVE ROVER、robot ACK、stop/cancel/recovery 或 HIL 安全验证。
- `manual_turn_envelope` 和 `navigate_goal_envelope` 的 limit 字段仍来自 fixture 摘要，不能外推为真实速度、转向或底盘安全边界。
