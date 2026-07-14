# Tech Done - O6/O7 Voice TTS Draft Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/`
- Owner: `full-stack-software-engineer`
- Closeout time: 2026-07-14 06:51 CST
- Proof boundary: `software_proof_o6_o7_voice_tts_draft_event_write_only`

## 实际改动

- O6 archive events 允许安全事件类型 `voice.tts_draft`，并把 `tts_send_enabled`、`speaker_dispatch_enabled`、`real_voice_api_connected`、`real_asr_tts_runtime_connected` 的 true claim 纳入 fail-closed 检查；新增 O6 unittest 覆盖安全写入、list/detail readback 和危险 true 拒绝。
- O7 workstation 新增 selected-task endpoint `POST /api/o7/consumer-read/tasks/:taskId/voice/tts-draft/request?baseUrl=<local-loopback-url>`，只接受本机 loopback O6 baseUrl，校验 task/robot/event/evidence/draft/metadata，固定向 O6 `POST /api/o6/archive/events` 写入 `event_type=voice.tts_draft`。
- O7 receipt schema 为 `trashbot.pc_tools_workstation.o7_voice_tts_draft_request_result.v1`，成功/失败均固定展示 `tts_send_enabled=false`、`speaker_dispatch_enabled=false`、`real_voice_api_connected=false`、`real_asr_tts_runtime_connected=false`、`safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`connects_cloud_production=false`。
- Workstation client、shared contract、Express route、O7 preview selected-task UI 和 Vitest fixtures/tests 已接入该动作；UI 显示 schema、request status、event identity、draft/ref、write receipt、O6 receipt、proof boundary、false fields 和 not_proven。
- `docs/interfaces/o6_cloud_archive_api.md`、`docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md` 已同步写明 voice/TTS draft event-write 边界、禁止真实 voice API/音频/喇叭/控制/生产云/送达/HIL 声明。

## 改动文件

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/o6_cloud_archive_api.md`
- `docs/interfaces/o7_realtime_operator_console.md`
- `docs/product/pc_tools_workstation.md`
- `pc-tools/workstation/src/server/o7ConsumerReadAdapter.ts`
- `pc-tools/workstation/src/server/index.ts`
- `pc-tools/workstation/src/client/workstationApi.ts`
- `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- `pc-tools/workstation/src/shared/contracts.ts`
- `pc-tools/workstation/test/catalog.test.ts`
- `pc-tools/workstation/test/App.test.ts`
- `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/tech-done.md`

## 验证结果

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`：通过，无输出。
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`：通过，`Ran 199 tests in 88.854s`，`OK`。
- `cd pc-tools/workstation && npm run test`：第一次失败 1 项，原因是 UI 已收到 voice/TTS receipt 但未显式渲染 `tts_draft_event_written=true`；已补充 write receipt 展示后重跑通过，`Test Files 3 passed (3)`，`Tests 516 passed (516)`。
- `cd pc-tools/workstation && npm run build`：通过，`tsc` + `vite build` + server `tsc` 完成；仅保留 Vite chunk size warning。
- `cd pc-tools/workstation && npm run lint`：通过，`eslint .` 无报错。
- `rg -n "voice/tts-draft/request|o7_voice_tts_draft_request|software_proof_o6_o7_voice_tts_draft_event_write_only|voice.tts" ...`：通过，命中 O6/O7/code/test/docs/sprint markers。
- `git diff --check -- ...`：通过，无输出。

## 失败定位与修复

- 初次 `npm run test` 失败在 `test/App.test.ts > loads O7 fixture previews through PC-only read-only API clients`，断言缺少 `tts_draft_event_written=true`。
- 根因：O7 selected-task UI 只显示了 schema/status/event/proof boundary/false fields，没有把 receipt 的 `archive_event_written`、`tts_draft_event_written`、`write_status`、O6 schema/source 单独渲染。
- 修复：在 `O7FixturePreviewPanel.vue` 的 voice/TTS receipt `<dl>` 增加 `write receipt` 和 `O6 receipt` 行；重跑 `npm run test` 后全部通过。

## 剩余风险

- 本轮只证明 O6/O7 local/mock selected-task voice/TTS draft event-write 软件链路；不连接真实语音 API，不发送音频，不播放 TTS，不调度喇叭，不连接 production cloud。
- `safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`connects_cloud_production=false` 固定不变；本轮不提升 route execution、delivery、HIL 或 safe-to-control 证明。
- 后续若要进入真实语音能力，需要机器人侧补真实 ASR/TTS runtime、speaker ACK/failure event、media preflight 和独立安全验收。
