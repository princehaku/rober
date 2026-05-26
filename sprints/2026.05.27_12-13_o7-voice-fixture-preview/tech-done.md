# O7 Voice Fixture Preview Tech Done

## sprint_type

micro

## 实际改动

- 新增 `pc-tools/workstation/src/server/o7VoicePreview.ts`，提供 `GET /api/o7/voice-preview?fixtureJson=<local-json>` 背后的 PC-only 本地 JSON fixture adapter。
- 更新 `pc-tools/workstation/src/shared/contracts.ts`，新增 `trashbot.o7.voice_preview.v1` 输出契约和 ASR/TTS 摘要类型。
- 更新 `pc-tools/workstation/src/server/catalog.ts` 与 `pc-tools/workstation/src/server/index.ts`，导出并挂载 voice preview API。
- 更新 `pc-tools/workstation/test/catalog.test.ts`，覆盖安全 fixture 摘要和 missing/bad/unsupported/unsafe/success/control/ASR/TTS/speaker/real voice/ACK success claim 的 fail-closed 分支。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`，同步 O7-KR5 voice fixture preview API、输入输出 schema、禁止能力和 UI 边界。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`，`Tests 23 passed (23)`。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check -- pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_12-13_o7-voice-fixture-preview`：通过，无输出。

## 剩余风险

- 本轮只实现 PC-only 本地 fixture 安全摘要，不连接云端 voice API、ROS2、硬件、麦克风、喇叭或音频设备。
- `fixture_preview_ready` 只证明本地 JSON 可被压缩为安全摘要，不证明真实 ASR partial/final、真实 TTS send/playback、真实 speaker ACK/failure、真实 media preflight 或真实 delivery success。
- O7 百分比和 `OKR.md` 按要求未改动。
