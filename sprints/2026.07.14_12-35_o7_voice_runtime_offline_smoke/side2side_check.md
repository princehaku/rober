# Side2Side Check - O7 Voice Runtime Offline Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/`
- Checked at: 2026-07-14 12-35 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Accepted proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`
- Product status: accepted, software proof only.

## Product Acceptance 结论

本轮接受为 O7 PC/Node voice runtime offline smoke deterministic local/offline trace。它把上一轮 preflight 从配置检查推进到同一 selected task 下的离线 runtime trace，可作为后续 explicit real voice runtime smoke 的输入输出对照。

本轮不接受为 real ASR/TTS、真实 voice API、真实麦克风、真实喇叭、speaker dispatch、real speaker ACK、production cloud、production DB/queue、OSS/CDN、4G/SIM、real phone/browser、route execution、delivery、HIL、safe-to-control、O5 external evidence、`/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART 或机器人控制。

## 对照检查

| Acceptance item | Product result |
| --- | --- |
| Endpoint | Accepted: `GET /api/o7/voice-runtime/offline-smoke` |
| Schema | Accepted: `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1` |
| Proof boundary | Accepted: `software_proof_o7_voice_runtime_offline_smoke_only` |
| Runtime status | Accepted: `ready_for_offline_smoke_trace_only` for safe local/offline fixture |
| Trace events | Accepted: `preflight_config_checked`, `offline_asr_stub_loaded`, `tts_draft_trace_prepared`, `speaker_ack_pending_not_real` |
| Fail-closed behavior | Accepted: unsafe fixture, task mismatch, unsupported mode and dangerous true claim return `fail_closed` |
| O6 archive event path | Accepted: no new or modified O6 archive event path |

## Fixed False Fields

Product acceptance requires these fields to stay false:

- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `real_speaker_ack_proven=false`
- `microphone_opened=false`
- `speaker_playback_opened=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`
- `route_execution_success=false`
- `hil_pass=false`

## 验证证据

Full-stack owner `tech-done.md` 已记录：

- `npm run test`: `Test Files 3 passed (3)`, `Tests 525 passed (525)`.
- `npm run build`: passed; only existing Vite chunk-size warning remains.
- `npm run lint`: passed.
- Required implementation `rg` matched endpoint, schema, proof boundary and fixed false fields.
- Scoped implementation `git diff --check` passed.

## OKR 判断

O5 仍是最低约 `85%`，但本轮没有 success-class production/cloud evidence。O1 继续约 `94%`，O6/O7 继续约 `93%`。主百分比不调整，KR `不归档`。

## 下一轮口径

下一轮不要重复 preflight/offline-smoke/TTS draft/speaker ACK wrappers。只有 success-class O5 production/cloud evidence、explicit same-window live route/HIL/delivery/operator evidence，或 explicitly authorized real voice runtime smoke，才进入计分口径。
