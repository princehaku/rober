# O7 Local TTS Draft Editor Tech Done

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue` 的 voice monitor / readonly TTS draft review 附近新增 `Local TTS draft editor`。
- editor 只消费当前 archive fixture 的 `voice_asr_tts_inspector.tts_draft`、`voice_session`、latest partial/final 和当前 ASR sample，维护浏览器内存草稿，不调用 API、不发送 TTS、不播放音频、不调度喇叭、不写云端。
- 新增本地校验状态：`blocked_not_proven`、`blocked_tts_text_empty`、`blocked_tts_text_too_long`、`blocked_voice_profile_empty`、`blocked_language_empty`、`local_tts_draft_valid`。
- 新增测试覆盖：editor 初始 blocked、加载 archive 后可编辑、空文本/超长/profile 空/language 空校验、archive path 切换清理本地覆盖值、`Reset TTS draft` 回到 fixture 默认值，且本地编辑不增加 `fetch` 次数。
- 同步更新 `docs/interfaces/o7_cloud_archive_task_api.md`、`docs/product/pc_tools_workstation.md` 和 `pc-tools/README.md` 的 O7-KR5 PC-only 边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`✓ built in 2.12s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  38 passed (38)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 lint 输出。
- `git diff --check -- pc-tools/workstation/src/components/O7FixturePreviewPanel.vue pc-tools/workstation/test/App.test.ts docs/interfaces/o7_cloud_archive_task_api.md docs/product/pc_tools_workstation.md pc-tools/README.md sprints/2026.05.27_35-36_o7-local-tts-draft-editor/tech-done.md`：通过，无输出。

## 剩余风险

- 本轮仍是 PC-only fixture/browser-memory software proof，不证明真实 voice API、真实 ASR/TTS runtime、真实 TTS send/playback、speaker ACK、音频设备、云写入或机器人喇叭调度。
- editor 的默认值来自当前 archive fixture 摘要；未接真实 O6/O7 voice runtime 前，不能作为真实发言能力验收。
