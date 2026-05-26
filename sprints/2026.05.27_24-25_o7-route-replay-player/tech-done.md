# O7 Route Replay Player Micro Sprint

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 `Cloud Archive Tasks` 区块新增 PC-only 本地 route replay player。
- player 基于已加载的 `route_replay_inspector.sample_frames` 展示当前 cursor、sample frame 总数、timestamp、pose、velocity、state 和 evidence ref。
- 新增 `Previous frame`、`Next frame`、`Reset cursor` 和 range cursor；这些控件只修改浏览器本地 state，不调用 API、不写后端、不发送机器人命令。
- fail-closed 条件覆盖 archive 未加载、selected task 缺失、sample frames 为空、inspector blocked，以及响应显式 `playback_available=false`。
- 更新 `pc-tools/workstation/test/App.test.ts`，验证本地 cursor navigation 不增加 fetch 调用。
- 同步更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md`，明确这是本地 fixture player，不是真实云 archive、真实地图叠加、真实机器人运动或真实控制。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ built in 1.07s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  35 passed (35)`。
- `cd pc-tools/workstation && npm run lint`：通过。`eslint .` 无错误输出。
- `git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_24-25_o7-route-replay-player`：通过，无 whitespace error 输出。

## 剩余风险

- 本轮只覆盖本地 archive fixture 的浏览器 cursor，不接真实 O6 archive store。
- 没有真实云历史路线回放、真实地图叠加、真实机器人运动、真实控制、真实 ROS2 `/tf` 或上车证据。
- 若后续 relay 或 O6 API 开始返回真实 `playback_available=true`，仍需要补 cloud frames 绑定、鉴权、延迟、审计和不触发机器人控制的独立验收。
