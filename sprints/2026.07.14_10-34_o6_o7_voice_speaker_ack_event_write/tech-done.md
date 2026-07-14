# Tech Done - O6/O7 Voice Speaker ACK Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/`
- Owner: `full-stack-software-engineer`
- Proof boundary: `software_proof_o6_o7_voice_speaker_ack_event_write_only`
- Implementation status: completed as local/mock software proof only.

## Actual Changes

- O6 archive events now allow `voice.speaker_ack` and `voice.speaker_failure`.
- O6 archive dangerous-true gate now rejects `real_speaker_ack_proven=true` in addition to existing voice, production, control, and delivery true claims.
- O7 workstation now exposes `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`.
- O7 adapter maps `ack_status=ack` to `voice.speaker_ack` and `ack_status=failure` to `voice.speaker_failure`.
- O7 receipt schema is `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`.
- Workstation UI adds selected-task speaker ACK/failure event-write controls and displays receipt status, O6 write status, proof boundary, evidence refs, and fixed false fields.
- Interface and product docs now describe the new endpoint, event types, receipt schema, false fields, and software-only boundary.

## Changed Files

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
- `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/tech-done.md`

## Verification

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`: passed.
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`: passed, `Ran 201 tests in 89.640s OK`.
- `cd pc-tools/workstation && npm run test`: passed, `Test Files 3 passed (3)`, `Tests 521 passed (521)`.
- `cd pc-tools/workstation && npm run build`: passed. Vite kept the existing large chunk warning for `dist/assets/index-*.js`.
- `cd pc-tools/workstation && npm run lint`: passed.

## First Failure And Repair

- First O6 unittest rerun failed because the new speaker ACK test was inserted before the previous TTS test's final `tts_send_body` assertion, leaving that assertion in the wrong method scope.
- Repair: moved the `tts_send_body` unsafe assertion back into the TTS draft test and reran the Python validation successfully.

## Interface Impact

- O6:
  - New safe event types: `voice.speaker_ack`, `voice.speaker_failure`.
  - Rejects dangerous true claims for `speaker_dispatch_enabled`, `real_speaker_ack_proven`, `tts_send_enabled`, `real_voice_api_connected`, `real_asr_tts_runtime_connected`, `safe_to_control`, `delivery_success`, `robot_control_executed`, and `connects_cloud_production`.
- O7:
  - New endpoint: `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`.
  - New receipt schema: `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`.
  - Success statuses distinguish ACK vs failure and created vs updated local/mock writes.

## User Journey Impact

- Operator can load a selected task, choose `ack` or `failure`, and write a bounded local/mock speaker ACK/failure event without leaving the workstation UI.
- The UI now shows whether the event write was accepted, which O6 event type was written, and why it remains not proven.
- This improves task evidence review and failure replay, but does not add real audio playback or real speaker ACK.

## Frontend / Backend / ROS2 Integration Result

- Frontend calls only the PC adapter endpoint and never O6 directly.
- Backend adapter is loopback-only and forwards only fixed safe `POST /api/o6/archive/events` bodies.
- ROS2 and hardware paths are not touched; this sprint has no `/cmd_vel`, `/api/base/manual`, NavigateToPose, UART, HIL, route execution, or real speaker runtime integration.

## Remaining Risks

- `speaker_dispatch_enabled=false`.
- `real_speaker_ack_proven=false`.
- `tts_send_enabled=false`.
- `real_voice_api_connected=false`.
- `real_asr_tts_runtime_connected=false`.
- `safe_to_control=false`.
- `delivery_success=false`.
- `robot_control_executed=false`.
- `connects_cloud_production=false`.
- This remains software proof only and must not be counted as audio playback, real speaker ACK, production cloud, route execution, delivery success, HIL, safe-to-control, or robot control.
