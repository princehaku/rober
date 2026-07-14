# Final - O7 Voice Runtime Offline Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/`
- Closed at: 2026-07-14 12-35 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`
- Final status: accepted, software proof only.

## Product Acceptance 结论

本轮接受为 O7 voice runtime offline smoke software proof only。Full-stack owner 已实现 `GET /api/o7/voice-runtime/offline-smoke`，返回 schema `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1`，在 safe local/offline mode 或 fixture 下输出 `ready_for_offline_smoke_trace_only`，并把 preflight-derived status、selected task identity 和四个 deterministic trace events 固化为可复验 trace。

四个 trace events 为 `preflight_config_checked`、`offline_asr_stub_loaded`、`tts_draft_trace_prepared`、`speaker_ack_pending_not_real`。Unsafe fixture、unsupported mode、task mismatch、URL/credential/audio/device/control text 和 dangerous true claim 均 fail-closed。Full-stack owner 已明确没有新增或修改 O6 archive event path。

本轮不证明 real ASR/TTS、真实 voice API、麦克风输入、喇叭播放、TTS send、speaker dispatch、real speaker ACK、production cloud、production DB/queue、OSS/CDN、4G/SIM、real phone/browser、route execution、delivery、HIL、safe-to-control、O5 external evidence 或机器人控制。

## 实际改动

Implementation owner 已完成并记录：

- `pc-tools/workstation/src/server/o7VoiceRuntimeOfflineSmoke.ts`
- `GET /api/o7/voice-runtime/offline-smoke`
- `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1`
- Workstation shared/client/UI/catalog/index/test changes
- `docs/product/pc_tools_workstation.md`
- `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/tech-done.md`

Product closeout 本轮新增或更新：

- `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/side2side_check.md`
- `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Full-stack 验证来自 `tech-done.md`：

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests  525 passed (525)
Duration  46.44s
```

```text
cd pc-tools/workstation && npm run build
tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json
built successfully; Vite reported only the existing chunk-size warning.
```

```text
cd pc-tools/workstation && npm run lint
eslint .
passed
```

Product closeout 验收命令已执行通过：

```bash
rg -n "2026-07-14 12-35|voice runtime offline smoke|software_proof_o7_voice_runtime_offline_smoke_only|/api/o7/voice-runtime/offline-smoke|trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1|ready_for_offline_smoke_trace_only|preflight_config_checked|offline_asr_stub_loaded|tts_draft_trace_prepared|speaker_ack_pending_not_real|real_voice_api_connected=false|real_asr_tts_runtime_connected=false|tts_send_enabled=false|speaker_dispatch_enabled=false|real_speaker_ack_proven=false|microphone_opened=false|speaker_playback_opened=false|safe_to_control=false|delivery_success=false|不归档|O5.*85|O6/O7.*93|O1.*94" OKR.md docs/process/okr_progress_log.md sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke
```

Result summary: required anchors were found across `OKR.md`, `docs/process/okr_progress_log.md`, and this sprint directory; scoped `git diff --check` produced no output.

## OKR 和 KR

- O5 继续约 `85%`，因为没有 success-class production/cloud evidence、4G/SIM、production DB/queue、OSS/CDN live traffic 或真实手机/browser。
- O1 继续约 `94%`，因为没有 current live HIL、route execution、delivery/operator acceptance 或 safe-to-control。
- O6/O7 继续约 `93%`，因为本轮是 bounded O7 offline smoke trace，不是 real voice runtime 或 live mission evidence。
- 主百分比不调整，本轮 KR `不归档`。

## 剩余风险

- 仍缺真实 voice provider / ASR/TTS runtime、麦克风输入、喇叭播放、speaker dispatch 和 real speaker ACK。
- 仍缺 production cloud、route execution、delivery/operator acceptance、HIL 和 safe-to-control。
- 下一轮不要重复 preflight/offline-smoke/TTS draft/speaker ACK wrappers；只有 success-class O5 production/cloud evidence、explicit same-window live route/HIL/delivery/operator evidence，或 explicitly authorized real voice runtime smoke，才可进入计分口径。
