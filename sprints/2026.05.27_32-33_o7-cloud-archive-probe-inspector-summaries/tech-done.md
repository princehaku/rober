# O7 Cloud Archive Probe Inspector Summaries

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：为 `O7CloudArchiveTasksProbeResponse` 增加 `route_replay_summary`、`labeling_queue_summary`、`voice_asr_tts_summary`、`safe_command_summary` 四个只读摘要字段。
- `pc-tools/workstation/src/server/o7CloudArchiveTasksProbe.ts`：从远端 `safe_summaries` 和四个 inspector 白名单字段生成短摘要；默认 fail-closed 返回 blocked/not_loaded；危险 true 字段扫描仍会把 `probe_status` 置为 `fail_closed`。摘要显式保留 `playback_available=false`、`submit_enabled=false`、`tts_send_enabled=false`、`command_dispatch_enabled=false` 和 `robot_control_executed=false`。
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`：在 O7 Previews 的 `Cloud archive tasks probe` 区块展示四条 summary，不新增 playback/send/submit/export/control/keyboard/nav/stop/cancel/recovery 按钮。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖 fixture-backed archive response 的 KR3-KR6 摘要提取，并覆盖远端 `playback_available=true` 时仍 `fail_closed`。
- `pc-tools/workstation/test/App.test.ts`：覆盖 UI 展示新增 summary 和关键 false 字段。
- `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`：同步说明 PC probe 的 summary 字段、白名单来源、fail-closed 行为和真实能力边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`✓ built in 2.21s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 eslint 报错输出。
- `git diff --check -- pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/src/server/o7CloudArchiveTasksProbe.ts pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/catalog.test.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_32-33_o7-cloud-archive-probe-inspector-summaries`：通过，无 whitespace/error 输出。

## 剩余风险

- 本轮只打通 PC probe 消费 relay runtime fixture-backed response 的只读摘要，不打通真实云 archive、真实路线回放播放、真实标注提交、真实 ASR/TTS runtime、真实手控/寻路、机器人 ACK 或硬件 HIL。
- 仍需后续 O6/O7 真实后端、云存档、annotation/voice/command API、Robot/Hardware 安全验收材料后，才能把这些 summary 从 software proof 推进到真实能力证据。
