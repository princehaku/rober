# PRD - O6/O7 Voice Speaker ACK Event Write

## Product Goal

Give the PC operator console a task-scoped way to record speaker outcome events after a voice/TTS request: either a local/mock speaker acknowledgment or a local/mock speaker failure. The product result is an auditable event-write receipt, not audio playback and not a real ACK.

## User Value And North Star

For assisted trash delivery, users and operators need clear evidence of whether the robot attempted to communicate a message. A future real speaker path must be able to report "the speaker side acknowledged" or "speaker dispatch failed" without implying route execution or delivery success.

This PRD supports the north star by making voice task evidence structured and queryable while keeping unsafe or unproven runtime claims disabled.

## OKR Mapping And Direction

- O7 KR5: PC-side ASR/TTS and voice operation. This sprint adds speaker ACK/failure event receipt plumbing only.
- O6 KR2/KR6: Task/event archive and consumer API. This sprint writes local/mock events through O6 archive semantics.
- O5 remains the lowest Objective at about `85%`, but this sprint does not target O5 because O5 now requires success-class production/cloud evidence or explicit live route/HIL/operator evidence.
- Direction judgment: continue O6/O7 local/mock action-write only; do not raise OKR percentages and do not archive KR from planning output.

## Fixed Event Types

O6 archive events must explicitly allow only these new safe event types for this sprint:

- `voice.speaker_ack`
- `voice.speaker_failure`

The endpoint path stays singular as `voice/speaker-ack/request`; the request body chooses the event outcome. Valid outcome mapping:

- `ack_status=ack` writes `event_type=voice.speaker_ack`
- `ack_status=failure` writes `event_type=voice.speaker_failure`

## Requirements

1. Add an O7 selected-task endpoint:
   - `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`
   - Reject non-loopback URLs, credentials, query/hash injection, invalid task ids, mismatched task ids, unsafe text, unsafe evidence refs, unknown `ack_status`, and dangerous true claims.
2. The O7 adapter must forward only a safe O6 request to:
   - `POST /api/o6/archive/events`
3. O6 must explicitly allow `voice.speaker_ack` and `voice.speaker_failure`, while fail-closing any payload that claims real speaker dispatch, real speaker ACK, real voice runtime, real TTS send, production cloud, robot control, safe-to-control, or delivery success.
4. The O7 response must return receipt schema:
   - `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`
5. The receipt must include:
   - selected `task_id`
   - requested `ack_status`
   - written O6 `event_type`
   - local/mock write status
   - O6 HTTP status and sanitized event id
   - proof boundary `software_proof_o6_o7_voice_speaker_ack_event_write_only`
   - fixed false fields listed below
6. The PC UI/API docs should expose the result as `voice_speaker_ack_event` so the action is discoverable and testable without implying real audio.

## Fixed False Fields

The receipt must always include and render:

- `speaker_dispatch_enabled=false`
- `real_speaker_ack_proven=false`
- `tts_send_enabled=false`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## Acceptance Criteria

Product accepts implementation only if:

- O7 exposes `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`.
- The success path writes one O6 archive event with `event_type=voice.speaker_ack` or `event_type=voice.speaker_failure`.
- The O7 receipt uses `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`.
- The proof boundary is `software_proof_o6_o7_voice_speaker_ack_event_write_only`.
- The implementation proves dangerous true fields fail closed.
- Docs and sprint closeout state this is local/mock event-write only.

Product rejects any claim that this proves audio playback, real speaker ACK, real ASR/TTS runtime, production cloud, robot control, route execution, delivery success, HIL, safe-to-control, or true operator/phone evidence.

## Priority And Owner

- Priority: P1 after latest O7 operator artifact closeout, because it consumes the speaker ACK/failure gap left by the 06:27 voice sprint without repeating TTS draft packaging.
- Responsible engineer: `full-stack-software-engineer`.
- Product acceptance owner: `product-okr-owner`.

## Evidence Chain Still Missing

- Real speaker dispatch and hardware/media preflight.
- Real voice API and ASR/TTS runtime connectivity.
- Same-window live route execution, delivery/operator acceptance, HIL pass, and `safe_to_control=true`.
- O5 success-class production/cloud evidence.
