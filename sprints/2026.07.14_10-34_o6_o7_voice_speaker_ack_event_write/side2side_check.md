# Side2Side Check - O6/O7 Voice Speaker ACK Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/`
- Product acceptance time: 2026-07-14 10-34 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Acceptance decision: accepted as O6/O7 selected-task voice speaker ACK/failure event-write local/mock software proof only.
- Proof boundary: `software_proof_o6_o7_voice_speaker_ack_event_write_only`

## User Value And North Star

The user value is an auditable selected-task voice outcome trail: an operator can record whether a future speaker attempt was acknowledged or failed, and the evidence can be reviewed with the task. This supports the PC/phone assisted trash-delivery north star by improving task explainability without exposing unsafe robot control or overstating voice runtime readiness.

This sprint is deliberately not real speaker dispatch, real speaker ACK, audio playback, or real voice runtime. It records bounded local/mock speaker outcome events so a later real voice runtime can report into an already validated O6/O7 contract.

## Requirement Versus Evidence

| Requirement | Implementation evidence | Product result |
| --- | --- | --- |
| O6 allows safe speaker outcome events | `tech-done.md` states O6 now allows `voice.speaker_ack` and `voice.speaker_failure`. | Accepted. |
| O7 exposes selected-task request endpoint | `tech-done.md` states `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>` is implemented. | Accepted. |
| O7 maps request outcomes to O6 events | `ack_status=ack` writes `voice.speaker_ack`; `ack_status=failure` writes `voice.speaker_failure`. | Accepted. |
| O7 receipt schema is stable | Receipt schema is `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`; marker name is `voice_speaker_ack_event`. | Accepted. |
| Dangerous true claims fail closed | O6 rejects `real_speaker_ack_proven=true` and keeps the existing voice, production, control, and delivery true-claim guard. | Accepted. |
| Verification is complete after first failure repair | `py_compile`, O6 relay unittest, workstation test/build/lint, anchor checks, and scoped diff-check passed after the misplaced TTS assertion was moved back. | Accepted. |

## OKR Mapping And Direction Judgment

- O5 remains the lowest Objective at about `85%`, but this sprint does not raise O5 because it has no success-class production/cloud evidence and no explicit same-window live route/HIL/delivery/operator evidence.
- O6/O7 remain about `93%`; this is another local/mock selected-task action/write software proof, not a scoring event.
- Direction judgment: continue the O6/O7 voice evidence contract as a bounded support layer; do not archive KR and do not increase percentages.
- KR handling: `不归档`.

## Fixed False Fields

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

Product explicitly rejects claims of real speaker dispatch, real speaker ACK, audio playback, real voice runtime, TTS dispatch, real voice API connection, ASR/TTS runtime connection, production cloud, route execution, delivery success, HIL, safe-to-control, and robot control.

This sprint also does not prove real phone/browser evidence, `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, production DB/queue, OSS/CDN, 4G/SIM, or real robot movement.

## Verification Reviewed

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`: passed.
- `python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_cloud_relay`: passed, `Ran 201 tests in 89.640s OK`.
- `cd pc-tools/workstation && npm run test`: passed, `Test Files 3 passed (3)`, `Tests 521 passed (521)`.
- `cd pc-tools/workstation && npm run build`: passed; Vite kept the existing large chunk warning.
- `cd pc-tools/workstation && npm run lint`: passed.
- Implementation first failure: the new speaker ACK test displaced an existing TTS unsafe assertion into the wrong method scope; the assertion was moved back and the Python validation reran successfully.

## Next Run Recommendation

Do not repeat voice speaker ACK/failure local/mock event-write, voice TTS draft, operator/dropoff API/browser artifacts, terminal-result wrappers, readback/export wrappers, CDN/TLS 4xx, or O5 operator gates. The next scoring run needs success-class O5 production/cloud evidence or explicit same-window live route/HIL/delivery/operator evidence. If those are unavailable, choose a materially stronger same-task mission artifact or a real voice runtime preflight rather than another local/mock receipt wrapper.
