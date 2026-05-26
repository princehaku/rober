# O7 Voice Monitor Panel Micro Sprint

## sprint_type

micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 Cloud Archive Tasks / Voice ASR/TTS inspector 区域新增 PC-only 本地 voice ASR/TTS monitor panel。
- 新增浏览器本地 `voiceAsrEventCursor`、blocked reason/helper、current ASR event 聚焦摘要，以及 `Previous ASR event`、`Next ASR event`、`Reset ASR cursor`。
- 加载 archive 后默认重置 ASR cursor 到第一条 `sample_asr_events`；所有 ASR navigation 只改变浏览器内存，不调用 API、不写后端、不连接真实 ASR stream、不发送 TTS、不播放音频、不调度喇叭。
- 在同一区块展示当前 ASR event 的 `event_type`、`timestamp_ms`、`transcript`、`confidence`、`evidence_ref`，并展示 `latest_partial`/`latest_final` 对比和 `tts_draft.confirmation_required=true` 的只读 TTS draft 审核摘要。
- 更新 `pc-tools/workstation/test/App.test.ts`，覆盖 ASR cursor Next/Reset 不增加 fetch 调用，并继续验证关键语音 false fields 与 TTS draft 审核文本可见。
- 同步更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md` 的本地 fixture voice monitor panel 边界说明。

## 验证结果

- 通过：`cd pc-tools/workstation && npm run build`
  - 关键输出：`✓ 31 modules transformed.`、`✓ built in 2.13s`
- 通过：`cd pc-tools/workstation && npm run test`
  - 关键输出：`Test Files  2 passed (2)`、`Tests  35 passed (35)`
- 通过：`cd pc-tools/workstation && npm run lint`
  - 关键输出：命令退出码 0，无 eslint 报错
- 通过：`git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/src/shared/contracts.ts pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_26-27_o7-voice-monitor-panel`
  - 关键输出：命令退出码 0，无 whitespace error

## 剩余风险

- 本轮仍是 PC-only 本地 fixture 调试体验，不证明真实 ASR stream、真实 TTS send/playback、speaker ACK、音频设备、云端 voice API 或机器人侧 O7-KR5 完成。
- 未连接真实语音 API、未播放音频、未发送 TTS、未调度喇叭；后续真实链路需要机器人侧和云端 voice runtime 提供独立 contract 与 HIL/音频设备验证。
