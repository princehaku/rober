# O7 Board Media Preflight Contract

`operator_media_preflight` emits the board-side media preflight summary for O7.
It is a fail-closed software contract, not a WebRTC/media runtime.

Hardware source boundary follows `docs/vendor/VENDOR_INDEX.md` and
`docs/interfaces/o7_realtime_hardware_sources.md`: Waveshare vendor material
only proves a Raspberry Pi reference app has WebRTC/video/audio examples. It
does not prove rober Orange Pi Zero 3 camera, audio, RTC, ASR, TTS, cloud
signaling, STUN/TURN, CPU encoding, or on-robot smoke.

## Producer

- Module: `ros2_trashbot_behavior.operator_media_preflight`
- CLI:

```bash
python3 -m ros2_trashbot_behavior.operator_media_preflight
```

The default CLI does not open camera, microphone, speaker, RTC, serial, chassis
UART, Nav2, or `/cmd_vel`. It only checks Python module availability,
explicitly passed paths, and explicit environment variables.

## Schema

```json
{
  "schema": "trashbot.o7_board_media_preflight.v1",
  "schema_version": 1,
  "evidence_boundary": "software_proof_o7_board_media_preflight_contract",
  "source": "operator_media_preflight",
  "overall_state": "blocked",
  "safe_to_control": false,
  "primary_actions_enabled": false,
  "device_probe_allowed": false,
  "device_probe_attempted": false,
  "capabilities": {
    "rtc": {
      "state": "blocked",
      "import_available": {"aiortc": false},
      "configured_env": {
        "TRASHBOT_RTC_SIGNALING_URL": false,
        "TRASHBOT_RTC_STUN_URLS": false,
        "TRASHBOT_RTC_TURN_URLS": false
      },
      "blocked_reasons": ["python_import_missing", "configuration_missing"],
      "not_proven": ["real_rtc_runtime", "orange_pi_rtc_device_or_service"]
    }
  },
  "path_checks": [
    {"name": "camera_path", "configured": false, "state": "not_configured"}
  ],
  "blocked": ["rtc"],
  "not_proven": [
    "real_rtc_session",
    "real_camera_video_source",
    "real_audio_capture",
    "real_audio_playback",
    "real_asr_stream",
    "real_tts_playback",
    "orange_pi_media_runtime",
    "on_robot_media_smoke"
  ],
  "next_required_evidence": [
    "resolve_blocked_preflight_items",
    "orange_pi_camera_device_enumeration",
    "orange_pi_audio_input_output_enumeration",
    "rtc_signaling_stun_turn_trace",
    "camera_frame_evidence_with_timestamp",
    "asr_partial_and_final_transcript_trace",
    "tts_audio_playback_trace",
    "cpu_encoding_budget_trace",
    "on_robot_media_smoke_with_no_chassis_motion"
  ],
  "software_proof_only": true
}
```

## Optional Probe

`--allow-device-probe` is default-off. When enabled, it performs shallow
`stat/access` checks only. It still must not open `/dev/video*`, microphone,
speaker, RTC sockets, serial devices, WAVE ROVER UART, Nav2 goals, or chassis
control paths. A successful shallow path check remains `not_proven`, never HIL
or RTC pass.

Unsafe path-like inputs such as `/cmd_vel`, `/dev/ttyUSB*`, bearer tokens, or
secrets are redacted and marked `blocked`.

## Realtime Status Integration

`o7_board_realtime_status.media_preflight` embeds this summary. Its
`not_proven` and `next_required_evidence` are also merged into
`o7_board_realtime_status` so cloud/PC consumers can see board media gaps
without enabling manual control or nav goals.

If an external status source provides `o7_board_media_preflight` or nested
`media_preflight`, the realtime status builder recursively redacts unsafe text
before exposing it. Raw `/cmd_vel`, `/dev/ttyUSB*`, authorization/bearer/token,
secret, or password strings must not appear in the emitted JSON; the summary is
downgraded to `blocked` with `unsafe_media_preflight_source_redacted`.

Consumers must keep primary actions disabled unless separate HIL and media
runtime evidence proves the full path.
