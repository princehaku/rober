# Side2Side Check - O6/O7 Voice TTS Draft Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/`
- Check time: 2026-07-14 06:56 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o6_o7_voice_tts_draft_event_write_only`

## Product Acceptance Check

Accepted as O6/O7 local/mock selected-task voice/TTS draft event-write software proof only.

The accepted user-flow increment is:

- PC/O7 exposes selected-task `POST /api/o7/consumer-read/tasks/:taskId/voice/tts-draft/request?baseUrl=<local-loopback-url>`.
- The adapter validates task id, local-loopback base URL, draft body, metadata, event identity, evidence refs, and dangerous true claims.
- The adapter writes O6 `POST /api/o6/archive/events` with `event_type=voice.tts_draft`.
- The receipt schema is `trashbot.pc_tools_workstation.o7_voice_tts_draft_request_result.v1`.
- The UI renders the event/write/O6 receipt, including `tts_draft_event_written=true` for the local/mock success path.

## Boundary Check

Accepted false fields:

- `tts_send_enabled=false`
- `speaker_dispatch_enabled=false`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

Rejected claims:

- no real voice API
- no ASR/TTS runtime connection
- no audio playback or speaker dispatch
- no production cloud
- no route execution, delivery, HIL, safe-to-control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART

## Verification Review

Worker-reported validation is accepted:

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passed.
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` passed: `Ran 199 tests in 88.854s OK`.
- `cd pc-tools/workstation && npm run test` passed after one UI receipt rendering fix: `Test Files 3 passed (3)`, `Tests 516 passed (516)`.
- `cd pc-tools/workstation && npm run build` passed with the existing Vite large chunk warning.
- `cd pc-tools/workstation && npm run lint` passed.
- Required `rg` anchors and scoped `git diff --check` passed.

## OKR Check

- O5 remains about `85%`; this sprint deliberately did not repeat O5 support-only gates because success-class production/cloud or explicit live delivery evidence was unavailable.
- O1 remains about `94%`; no current live HIL, route execution, WAVE ROVER, or safe-to-control evidence was collected.
- O6 remains about `93%`; this adds a local/mock event-write contract, not production DB/queue/OSS or real robot data.
- O7 remains about `93%`; this adds a selected-task voice action-write receipt, not real ASR/TTS or speaker dispatch.
- KR archival: `不归档`.
