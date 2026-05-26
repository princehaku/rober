# O7 Voice ASR/TTS Inspector Micro Sprint

sprint_type: micro

## 实际改动

- 扩展 `trashbot.o7.cloud_archive_tasks.v1`：新增 `voice_asr_tts_inspector`，从 selected task 的本地 archive fixture 读取 `voice_session`、`asr_events[]`、`tts_drafts[]` / `tts_draft`、`voice_profile`、`speaker_ack`、`media_preflight`，生成只读 KR5 ASR/TTS 检查视图。
- 新增 ASR sample 限量、latest partial/final、TTS draft 安全文本摘要、speaker dispatch 缺口、media preflight dependency，以及固定 false 的 `asr_stream_connected`、`tts_send_enabled`、`speaker_dispatch_enabled`、`real_voice_api_connected`、`real_asr_tts_runtime_connected`。
- blocked / unsafe / success / control / real API claim 输入保持 fail-closed：样本清空、inspector blocked、所有真实连接和发送字段 false。
- PC `O7 Previews > Cloud Archive Tasks` 展示 voice inspector 的 ASR sample、latest slots、TTS draft summary、speaker dispatch summary、media preflight dependency 和 false fields，不增加真实语音或机器人动作入口。
- 同步更新 `docs/product/pc_tools_workstation.md`、`docs/interfaces/o7_cloud_archive_task_api.md`、`docs/interfaces/o7_realtime_operator_console.md`。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 31 modules transformed.`、`dist/assets/index-CGfPVnUm.js   135.09 kB`、`✓ built in 2.07s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  32 passed (32)`。
- `cd pc-tools/workstation && npm run lint`：通过，ESLint 无错误输出。
- `git diff --check -- pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_cloud_archive_task_api.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_19-20_o7-voice-asr-tts-inspector`：通过，无 whitespace error 输出。

## 剩余风险

- 当前只证明本地 archive fixture 可被压缩成 KR5 只读调试形状，不连接真实 ASR stream、TTS runtime、speaker ACK、RTC/audio device、O6 云归档或机器人端。
- 本轮不改变 `OKR.md` 完成度；O7-KR5 仍需真实语音 API、板端 media preflight 和上车 smoke 证据。

## 失败定位和修复

- 首轮 `npm run test` 失败于 `test/catalog.test.ts` 中 TTS 脱敏后 `text_length` 期望错误：实现按脱敏后安全文本计算长度为 34，测试误写为 28。
- 修复测试期望后，完整 build/test/lint/diff-check 均通过。
