# Final - O6/O7 Voice TTS Draft Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/`
- Closeout time: 2026-07-14 06:56 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Final status: accepted as local/mock software proof only, flat OKR
- Proof boundary: `software_proof_o6_o7_voice_tts_draft_event_write_only`

## Product Closeout

Product accepts this sprint as an O6/O7 selected-task voice/TTS draft event-write contract. The useful increment is that a PC operator can draft a task-scoped TTS message, O7 validates it fail-closed, and the adapter writes a safe O6 archive event `voice.tts_draft`.

Product does not accept this sprint as real voice capability, speaker dispatch, production cloud, robot control, delivery, HIL, or safe-to-control.

Accepted facts:

- O7 endpoint: `POST /api/o7/consumer-read/tasks/:taskId/voice/tts-draft/request?baseUrl=<local-loopback-url>`.
- O7 receipt schema: `trashbot.pc_tools_workstation.o7_voice_tts_draft_request_result.v1`.
- O6 event type: `voice.tts_draft`.
- Proof boundary: `software_proof_o6_o7_voice_tts_draft_event_write_only`.
- Success path writes a local/mock O6 event and renders `tts_draft_event_written=true`.
- Fixed false fields include `tts_send_enabled=false`, `speaker_dispatch_enabled=false`, `real_voice_api_connected=false`, `real_asr_tts_runtime_connected=false`, `safe_to_control=false`, `delivery_success=false`, `robot_control_executed=false`, and `connects_cloud_production=false`.

## Actual Changes

Full-stack delivered:

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

Product closeout delivered:

- `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/side2side_check.md`
- `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Verification Evidence

Worker verification:

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passed.
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay` passed: `Ran 199 tests in 88.854s OK`.
- `cd pc-tools/workstation && npm run test` first failed because the UI did not render `tts_draft_event_written=true`; the worker added explicit write/O6 receipt rows and reran successfully: `Test Files 3 passed (3)`, `Tests 516 passed (516)`.
- `cd pc-tools/workstation && npm run build` passed with only the existing Vite large chunk warning.
- `cd pc-tools/workstation && npm run lint` passed.
- Required `rg` anchor scan passed.
- Scoped `git diff --check` passed.

Main-node acceptance:

- Reviewed `tech-done.md`.
- Confirmed the endpoint, schema, `voice.tts_draft`, proof boundary, UI receipt marker, and fixed false fields are present across code, tests, docs, and sprint docs.
- Confirmed this sprint did not claim O5 production evidence, O1 HIL/control evidence, real voice runtime, delivery success, or safe-to-control.

## OKR Result

- O5 remains about `85%`; success-class production/cloud or explicit live delivery evidence is still missing.
- O1 remains about `94%`; no current live HIL, WAVE ROVER, route execution, or safe-to-control evidence was collected.
- O6 remains about `93%`; this is a local/mock archive event-write contract, not production DB/queue/OSS or real robot data.
- O7 remains about `93%`; this is a selected-task TTS draft event receipt, not real ASR/TTS, speaker dispatch, or RTC/video.
- KR archival: `不归档`.
- Main percentages: unchanged.

## Remaining Risk And Next Step

Remaining risk:

- Real voice API, ASR/TTS runtime, speaker ACK/failure events, media preflight, production cloud, and live robot evidence remain unproven.
- The project still lacks same-window live route execution success, operator/dropoff acceptance, HIL pass, safe-to-control, and production/cloud success evidence.

Next recommendation:

Do not repeat O5 terminal/result gates, O6/O7 readback wrappers, or local/mock voice draft packaging as OKR progress. The next scoring move should be success-class O5 production/cloud evidence or explicit-operator-approved same-window live route/HIL/delivery/operator evidence. If those remain unavailable, choose a distinct action/write path that consumes a stronger same-task mission artifact.
