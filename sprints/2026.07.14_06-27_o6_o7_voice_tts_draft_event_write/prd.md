# PRD - O6/O7 Voice TTS Draft Event Write

## Product Goal

Give the operator console a task-scoped voice action that can be validated without real audio hardware: an operator drafts a TTS message for a selected delivery task, the PC adapter writes a safe O6 archive event, and the response makes the disabled real-world boundary explicit.

## User Value

For assisted delivery, an operator eventually needs to ask for help, announce arrival, or explain a blocked task. This sprint creates the contract for that action while keeping the real TTS path disabled until hardware, voice runtime, and safety evidence are available.

## OKR Mapping

- O7 KR5: PC 端实时 ASR 监听 + TTS 发言操作. This sprint adds a task-scoped TTS draft request receipt, not real TTS playback.
- O6 KR2/KR6: Task/event archive and consumer API. This sprint writes a local/mock voice event through O6 archive semantics.
- O5 remains the lowest Objective, but this sprint does not target it because the next O5 scoring step requires real production/cloud or live delivery evidence not available in the current automation environment.

## Requirements

1. Add an O7 selected-task endpoint:
   - `POST /api/o7/consumer-read/tasks/:taskId/voice/tts-draft/request?baseUrl=<local-loopback-url>`
   - The endpoint must reject non-loopback URLs, credentials, query/hash injection, invalid task ids, unsafe text, and dangerous true claims.
2. The adapter must forward only a safe O6 event to `POST /api/o6/archive/events`.
3. O6 must explicitly allow the safe voice event type needed by this contract.
4. The O7 receipt must include:
   - schema `trashbot.pc_tools_workstation.o7_voice_tts_draft_request_result.v1`
   - selected `task_id`
   - remote O6 endpoint and HTTP status
   - local/mock write status
   - sanitized draft metadata and safe event id
   - fixed false fields for `tts_send_enabled`, `speaker_dispatch_enabled`, `real_voice_api_connected`, `real_asr_tts_runtime_connected`, `safe_to_control`, `delivery_success`, `robot_control_executed`, and `connects_cloud_production`
5. PC docs/UI/API surfaces must make clear that this is a draft/event write only.

## Acceptance

Product accepts this sprint only as local/mock O6/O7 voice TTS draft event write software proof. Product rejects any claim of real TTS playback, ASR stream, speaker dispatch, production cloud, live route execution, delivery, HIL, safe-to-control, or robot control.
