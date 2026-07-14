# Tech Done - O7 Voice Runtime Preflight

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_11-35_o7_voice_runtime_preflight/`
- Owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o7_voice_runtime_preflight_only`
- Result: implemented and locally verified.

## Actual Changes

- Added deterministic PC/Node voice runtime preflight builder:
  - `pc-tools/workstation/src/server/o7VoiceRuntimePreflight.ts`
  - `GET /api/o7/voice-runtime/preflight`
  - schema `trashbot.pc_tools_workstation.o7_voice_runtime_preflight_result.v1`
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

- Missing config or mode returns `blocked_missing_voice_runtime_config`.
- Safe local/offline mode or config returns `ready_for_configured_runtime_check_only`.
- Dangerous true claims return `fail_closed`.
- Fixed false fields remain explicit:
  - `real_voice_api_connected=false`
  - `real_asr_tts_runtime_connected=false`
  - `tts_send_enabled=false`
  - `speaker_dispatch_enabled=false`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `robot_control_executed=false`
  - `connects_cloud_production=false`
- The endpoint does not connect production cloud, open microphone or speaker, send TTS, play audio, write O6 archive events, call `/cmd_vel`, call `/api/base/manual`, or control the robot.

## Validation

```text
cd pc-tools/workstation && npm run test
Test Files  3 passed (3)
Tests  523 passed (523)
Duration  42.42s
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

## Failure / Repair Notes

- No validation failure occurred after implementation.
- No O6 archive event path was added or modified for this preflight. The existing voice/TTS draft and speaker ACK event-write paths remain separate.

## Remaining Risk

- This is software proof only. It does not prove a real ASR/TTS provider, microphone input, speaker playback, real speaker ACK, production cloud, delivery success, HIL, or safe-to-control.
- Next required evidence is an explicitly authorized real voice runtime smoke with microphone/speaker preflight and selected-task speaker ACK evidence.
