# Final - O6/O7 Voice Speaker ACK Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/`
- Final status: accepted by Product.
- Product acceptance time: 2026-07-14 10-34 CST
- Implementation owner: `full-stack-software-engineer`
- Product owner: `product-okr-owner`
- Proof boundary: `software_proof_o6_o7_voice_speaker_ack_event_write_only`

## Acceptance Summary

Product accepts this sprint as O6/O7 selected-task voice speaker ACK/failure event-write local/mock software proof only. The implemented surface is the O7 endpoint `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`, which writes bounded O6 archive events `voice.speaker_ack` or `voice.speaker_failure` and returns receipt schema `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1` under the `voice_speaker_ack_event` marker.

This is useful because it gives future real voice work a task-scoped receipt path for speaker outcome evidence. It does not prove real speaker dispatch, real speaker ACK, real voice runtime, live audio, or robot behavior.

## OKR Result

- O5 remains about `85%`; this sprint does not add success-class production/cloud evidence or explicit same-window live route/HIL/delivery/operator evidence.
- O6/O7 remain about `93%`; this is local/mock action/write software proof and regression guard coverage, not a main OKR scoring event.
- Direction judgment: continue bounded O6/O7 voice evidence contracts, but pivot away from nearby wrapper work for the next run.
- KR decision: `不归档`.

## Verification Evidence

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`: passed.
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`: passed, `Ran 201 tests in 89.640s OK`.
- `cd pc-tools/workstation && npm run test`: passed, `Test Files 3 passed (3)`, `Tests 521 passed (521)`.
- `cd pc-tools/workstation && npm run build`: passed; existing Vite large chunk warning remains.
- `cd pc-tools/workstation && npm run lint`: passed.
- Product closeout anchor check passed after this final write.
- Product scoped `git diff --check` passed after this final write.

## First Failure And Repair

The first O6 unittest rerun failed because the new speaker ACK test was inserted before the previous TTS test's final `tts_send_body` unsafe assertion, leaving that assertion in the wrong method scope. The implementation owner moved the assertion back into the TTS draft test and reran Python validation successfully.

## Required False Fields

- `speaker_dispatch_enabled=false`
- `real_speaker_ack_proven=false`
- `tts_send_enabled=false`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## Rejected Claims

Product rejects real speaker dispatch, real speaker ACK, audio playback, real voice runtime, TTS dispatch, real voice API, ASR/TTS runtime, production cloud, route execution, delivery success, HIL, safe-to-control, robot control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, real phone/browser evidence, production DB/queue, OSS/CDN, 4G/SIM, and robot movement claims.

## Remaining Risk And Next Run

The remaining risk is not a bug in this sprint; it is the proof boundary. The system still lacks real speaker dispatch, real speaker ACK, real voice runtime preflight, success-class O5 production/cloud evidence, and same-window live route/HIL/delivery/operator evidence.

Next run should not repeat voice speaker ACK/failure local/mock event-write, voice TTS draft, operator/dropoff API/browser artifacts, terminal-result wrappers, readback/export wrappers, CDN/TLS 4xx, or O5 operator gates. Only success-class O5 production/cloud evidence or explicit same-window live route/HIL/delivery/operator evidence should score. If unavailable, pick a materially stronger same-task mission artifact or real voice runtime preflight.
