# O7 Board Realtime Status Contract

`o7_board_realtime_status` is the board-side readiness summary consumed by
cloud-relay and PC tooling for O7 realtime features. It is emitted by
`ros2_trashbot_behavior.operator_gateway_http.status_payload()` and mirrored by
`ros2_trashbot_behavior.operator_gateway_diagnostics_payload.build_diagnostics_payload()`.

This contract is software proof only. It must not start RTC, camera streaming,
ASR, TTS, manual control, Nav2 goals, audio playback, or chassis motion.

## Schema

```json
{
  "schema": "trashbot.o7_board_realtime_status.v1",
  "schema_version": 1,
  "evidence_boundary": "software_proof_o7_board_realtime_status_contract",
  "source": "operator_gateway_status_contract",
  "media_agent_state": "software_contract_ready",
  "video_source_state": "not_proven",
  "asr_stream_state": "not_proven",
  "tts_playback_state": "not_proven",
  "media_preflight": {
    "schema": "trashbot.o7_board_media_preflight.v1",
    "overall_state": "blocked",
    "safe_to_control": false,
    "primary_actions_enabled": false,
    "software_proof_only": true
  },
  "manual_control_policy": {
    "state": "blocked",
    "enabled": false,
    "safe_to_control": false,
    "reason": "manual control is disabled until HIL proves safe stop and timeout behavior",
    "accepted_commands": [],
    "not_proven": ["manual_control_hil", "nav_goal_hil"],
    "next_required_evidence": ["hil_with_safe_stop_and_timeout"]
  },
  "nav_goal_policy": {
    "state": "blocked",
    "enabled": false,
    "safe_to_control": false,
    "reason": "nav goal dispatch is disabled until HIL proves goal, cancel, and timeout behavior",
    "accepted_commands": [],
    "not_proven": ["manual_control_hil", "nav_goal_hil"],
    "next_required_evidence": ["hil_with_safe_stop_and_timeout"]
  },
  "not_proven": [
    "real_rtc_session",
    "real_camera_video_source",
    "real_asr_stream",
    "real_tts_playback",
    "manual_control_hil",
    "nav_goal_hil"
  ],
  "next_required_evidence": [
    "cloud_relay_consumes_o7_board_realtime_status",
    "pc_tools_consumes_o7_board_realtime_status",
    "real_rtc_offer_answer_and_media_trace",
    "camera_frame_evidence_with_timestamp",
    "asr_partial_and_final_transcript_trace",
    "tts_audio_playback_trace",
    "manual_control_hil_with_safe_stop",
    "nav_goal_hil_with_cancel_and_timeout"
  ],
  "ready_for_consumers": true,
  "primary_actions_enabled": false,
  "software_proof_only": true
}
```

## Producer

- `ros2_trashbot_behavior.operator_gateway_http.status_payload()` adds the
  object to `/api/status` and the operator status file.
- `ros2_trashbot_behavior.operator_gateway_diagnostics_payload.build_diagnostics_payload()`
  mirrors it into `/api/diagnostics` as both `o7_board_realtime_status` and the
  compatibility alias `board_realtime_status`.

## Consumer Contract

Consumers must treat `ready_for_consumers=true` as "the JSON contract exists",
not as media/control readiness. Realtime capability decisions must inspect the
individual state fields and `not_proven`.

`media_preflight` is produced by
`ros2_trashbot_behavior.operator_media_preflight` and follows
`docs/interfaces/o7_board_media_preflight.md`. It reports board media
preconditions only. It does not open cameras, microphones, speakers, RTC,
serial devices, Nav2, or chassis control.

`manual_control_policy.enabled` and `nav_goal_policy.enabled` remain `false`
until separate HIL evidence proves safe stop, timeout, cancel, and goal-result
semantics. External status files cannot enable those policies through this
helper.

## Evidence Boundary

Current evidence is `software_proof_o7_board_realtime_status_contract`.
The remaining gaps are listed in `not_proven` and `next_required_evidence`.
Hardware, Full-Stack, and PC work must add real evidence before claiming RTC,
video, ASR, TTS, manual control, or navigation-goal readiness.
