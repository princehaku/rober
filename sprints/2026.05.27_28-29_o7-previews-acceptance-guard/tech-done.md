# O7 Previews Acceptance Guard

sprint_type: micro

## 实际改动

- 新增 `GET /api/o7/previews/acceptance`，返回 `trashbot.o7.previews_acceptance.v1` 只读验收摘要。
- 覆盖 O7 Previews 已有 surface：`cloud_operator_console_probe`、`cloud_archive_tasks_probe`、`realtime_elevator_probe`、`route_replay_player`、`labeling_review_panel`、`voice_monitor_panel`、`safe_command_review_panel`。
- 在 O7 Previews tab 顶部新增手动加载的 acceptance guard 区域，展示 verdict、evidence boundary、covered surfaces、blocked/not_proven、software proof only 和安全不变量。
- 更新接口、产品和 README 文档，明确该 guard 不读取硬件、不发命令、不连生产云、不提升 O7 完成度。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm run build`
  - 关键日志：`✓ 31 modules transformed.`、`✓ built in 2.26s`
- 已通过：`cd pc-tools/workstation && npm run test`
  - 关键日志：`Test Files  2 passed (2)`、`Tests  36 passed (36)`
- 已通过：`cd pc-tools/workstation && npm run lint`
  - 关键日志：`eslint .` 退出码 0
- 已通过：`git diff --check -- pc-tools/workstation/src/server pc-tools/workstation/src/client/workstationApi.ts pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_28-29_o7-previews-acceptance-guard`
  - 关键日志：无 whitespace error，退出码 0

## 剩余风险

- 当前仅是 PC-only software proof / local HTTP contract readiness summary。
- 没有打通真实 RTC/视频，没有真实手控/寻路，没有机器人 ACK，没有硬件 HIL 或上车证据。
- O7 完成度不因本轮 guard 提升；后续仍需真实云归档、实时流、annotation/voice/command API、robot ACK 和 HIL 验收。
