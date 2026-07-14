# Tech Done - O7 Voice Runtime Offline Smoke

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke/`
- Owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_offline_smoke_only`
- Result: implemented and locally verified.

## Actual Changes

- Added deterministic PC/Node voice runtime offline smoke builder:
  - `pc-tools/workstation/src/server/o7VoiceRuntimeOfflineSmoke.ts`
  - `GET /api/o7/voice-runtime/offline-smoke`
  - schema `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1`
- Added shared/client/UI support:
  - `pc-tools/workstation/src/shared/contracts.ts`
  - `pc-tools/workstation/src/client/workstationApi.ts`
  - `pc-tools/workstation/src/server/catalog.ts`
  - `pc-tools/workstation/src/server/index.ts`
  - `pc-tools/workstation/src/components/O7FixturePreviewPanel.vue`
- Added/updated tests:
  - `pc-tools/workstation/test/catalog.test.ts`
  - `pc-tools/workstation/test/App.test.ts`
- Updated product documentation:
  - `docs/product/pc_tools_workstation.md`

## Contract Behavior

- Safe `mode=offline_stub|local_stub|disabled_local` or a local fixture with schema `trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_fixture.v1` produces `ready_for_offline_smoke_trace_only`.
- The result consumes preflight-derived status from `o7VoiceRuntimePreflight` and emits selected task identity plus four deterministic trace events:
  - `preflight_config_checked`
  - `offline_asr_stub_loaded`
  - `tts_draft_trace_prepared`
  - `speaker_ack_pending_not_real`
- Unsupported mode, task mismatch, unsafe URL/credential/audio/device/control text, bad fixture schema, and dangerous true claims return `fail_closed`.
- Fixed false fields remain explicit:
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

## Validation

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

```text
rg -n "software_proof_o7_voice_runtime_offline_smoke_only|voice runtime offline smoke|/api/o7/voice-runtime/offline-smoke|trashbot.pc_tools_workstation.o7_voice_runtime_offline_smoke_result.v1|real_voice_api_connected=false|real_asr_tts_runtime_connected=false|tts_send_enabled=false|speaker_dispatch_enabled=false|real_speaker_ack_proven=false|microphone_opened=false|speaker_playback_opened=false|safe_to_control=false|delivery_success=false" pc-tools/workstation docs/product/pc_tools_workstation.md sprints/2026.07.14_12-35_o7_voice_runtime_offline_smoke
matched the endpoint, schema, proof boundary, and required fixed false fields in workstation code, product docs, and sprint docs.
```

## Failure / Repair Notes

- No validation command failed after implementation.
- During self-review before final validation, the catalog test was tightened so `real_speaker_ack_proven=true` is actually carried by an unsafe local fixture and rejected as `fail_closed`.
- No O6 archive event path was added or modified.

## Remaining Risk

- This is `software_proof_o7_voice_runtime_offline_smoke_only`.
- It does not prove real ASR/TTS, a real voice API, microphone input, speaker playback, speaker dispatch, real speaker ACK, production cloud, route execution, delivery, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, or robot movement.
- Next required evidence is an explicitly authorized real voice runtime smoke with microphone/speaker readback and selected-task speaker ACK evidence.
