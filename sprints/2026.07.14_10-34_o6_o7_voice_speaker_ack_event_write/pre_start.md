# Pre Start - O6/O7 Voice Speaker ACK Event Write

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.14_10-34_o6_o7_voice_speaker_ack_event_write/`
- Start time: 2026-07-14 10:34 CST
- Product owner: `product-okr-owner`
- Implementation owner: `full-stack-software-engineer`
- Target Objectives: O7 primary, O6 secondary
- Proof boundary: `software_proof_o6_o7_voice_speaker_ack_event_write_only`
- Planning status: plan only; do not create `tech-done.md`, `side2side_check.md`, or `final.md` in this planning task.

## User Value And North Star

The product north star is a phone/PC assisted trash-delivery robot that can explain task progress and ask for help without exposing unsafe robot control. Voice remains important because ordinary users may not watch a dashboard during a dropoff; the immediate value here is a task-scoped evidence trail that records whether a future speaker dispatch was acknowledged or failed.

This sprint is not audio playback. It creates a safe O6/O7 event-write contract so later real voice work has a place to report `voice.speaker_ack` and `voice.speaker_failure` outcomes.

## Previous Context

Latest closeout is `sprints/2026.07.14_09-33_o7_operator_dropoff_browser_artifact/`. Product accepted it as an O7 selected-task operator dropoff browser/DOM local software proof only. It reused the operator dropoff action capture path and did not prove real operator action, delivery success, live route execution, HIL, safe-to-control, production cloud, production DB/queue, OSS/CDN, 4G/SIM, true mobile browser evidence, or robot movement.

The 06:27 voice sprint `sprints/2026.07.14_06-27_o6_o7_voice_tts_draft_event_write/` accepted `voice.tts_draft` as a local/mock event-write contract and explicitly left real voice API, ASR/TTS runtime, media preflight, and speaker ACK/failure events unproven.

O5 remains about `85%`, but the missing evidence is success-class production/cloud evidence or explicit live route/HIL/operator evidence. Those materials are not available in this planning task.

## Direction Judgment

Decision: continue with a distinct O6/O7 selected-task action/write sprint, but keep OKR scoring flat unless implementation later proves a stronger class of evidence than local/mock software proof.

This sprint must not repeat:

- operator dropoff API/action/browser artifact work
- O5 operator gates
- terminal-result or delivery-state gates
- O6/O7 readback/export wrappers
- voice TTS draft packaging

The non-repeating product delta is the new speaker outcome event pair: `voice.speaker_ack` and `voice.speaker_failure`.

## Core Lever

Add a selected-task O7 endpoint:

- `POST /api/o7/consumer-read/tasks/:taskId/voice/speaker-ack/request?baseUrl=<local-loopback-url>`

The endpoint writes one safe local/mock O6 event to:

- `POST /api/o6/archive/events`

The O7 receipt schema is fixed as:

- `trashbot.pc_tools_workstation.o7_voice_speaker_ack_event_result.v1`

## Non-Goals

- Do not play audio.
- Do not connect a real voice API, ASR runtime, TTS runtime, RTC audio device, or speaker hardware.
- Do not prove real speaker ACK.
- Do not dispatch robot control, `/cmd_vel`, `/api/base/manual`, NavigateToPose, or WAVE ROVER UART.
- Do not claim delivery success, safe-to-control, HIL, production cloud, real phone/browser proof, or operator acceptance.

## Required False Fields

The receipt and relevant docs/tests must keep these fields false:

- `speaker_dispatch_enabled=false`
- `real_speaker_ack_proven=false`
- `tts_send_enabled=false`
- `real_voice_api_connected=false`
- `real_asr_tts_runtime_connected=false`
- `safe_to_control=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `connects_cloud_production=false`

## KR Handling

- Current KR archival decision for this planning sprint: no KR is complete; do not archive.
- `OKR.md` must not be modified in this task.
- If implementation later lands, closeout must state that O6/O7 remain local/mock unless real voice runtime, real speaker ACK, production cloud, live delivery, HIL, or safe-to-control evidence is added.

## Sprint Documents

Create now:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Create later only after implementation and validation:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
