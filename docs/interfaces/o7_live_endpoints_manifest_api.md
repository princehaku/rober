# O7 Live Endpoints Manifest API

## Purpose

`GET /api/o7/live-endpoints/manifest` exposes a read-only readiness manifest for future O7 live APIs. It lets the PC workstation show which endpoint environment variables are configured, missing, or blocked without probing the network, connecting production cloud, sending commands, reading hardware, or exposing credentials.

This API is software proof only. It does not prove real RTC/video, realtime pose, elevator state, cloud archive, route replay, annotation submit, ASR/TTS, safe command dispatch, robot ACK, HIL, or delivery success.

## Environment Variables

| Capability | O7 KR | URL env | Token env |
| --- | --- | --- | --- |
| RTC/realtime pose/elevator | O7-KR1, O7-KR2 | `O7_RTC_REALTIME_URL` | `O7_RTC_REALTIME_TOKEN` |
| Cloud archive | O7-KR3 | `O7_CLOUD_ARCHIVE_URL` | `O7_CLOUD_ARCHIVE_TOKEN` |
| Route replay data source | O7-KR3 | `O7_ROUTE_REPLAY_URL` | `O7_ROUTE_REPLAY_TOKEN` |
| Annotation submit API | O7-KR4 | `O7_ANNOTATION_API_URL` | `O7_ANNOTATION_API_TOKEN` |
| Voice ASR/TTS API | O7-KR5 | `O7_VOICE_API_URL` | `O7_VOICE_API_TOKEN` |
| Safe command API | O7-KR6 | `O7_SAFE_COMMAND_API_URL` | `O7_SAFE_COMMAND_TOKEN` |

## Redaction Rules

- URL output only includes `protocol`, `host`, `path`, and `display_url=protocol://host/path`.
- URL query, hash, username, and password are never displayed.
- Token values are never displayed; only `present` or `absent` is returned.
- URL values with credentials, query, or hash are marked `blocked` and not adopted.
- Invalid URLs or unsupported protocols are marked `blocked`.
- Allowed URL protocols are `http`, `https`, `ws`, and `wss`.

## Fixed Safety Flags

The response always includes:

```json
{
  "env_only": true,
  "network_probe_executed": false,
  "sends_commands": false,
  "safe_to_control": false,
  "connects_cloud_production": false,
  "robot_control_executed": false,
  "reads_hardware": false,
  "token_values_exposed": false,
  "url_query_hash_credentials_exposed": false
}
```

Default with no env configured: all six capabilities return `status=not_configured` and `proof_status=not_proven`.

## Response Shape

```json
{
  "schema": "trashbot.o7.live_endpoints_manifest.v1",
  "schema_version": 1,
  "manifest_status": "readiness_manifest_ready",
  "endpoint": "/api/o7/live-endpoints/manifest",
  "source": "software_proof",
  "proof_status": "not_proven",
  "safe_to_control": false,
  "capabilities": [
    {
      "id": "rtc_realtime_pose_elevator",
      "kr_ids": ["O7-KR1", "O7-KR2"],
      "status": "not_configured",
      "proof_status": "not_proven",
      "url": {
        "configured": false,
        "display_url": "not_configured",
        "protocol": "",
        "host": "",
        "path": "",
        "unsafe_reason": ""
      },
      "token": {
        "env": "O7_RTC_REALTIME_TOKEN",
        "status": "absent"
      },
      "missing": ["url", "token"],
      "blocked_reasons": [],
      "required_live_evidence": ["rtc_signaling_trace"],
      "remaining_real_capability_gaps": ["real_rtc_video_connected"]
    }
  ],
  "summary": {
    "configured": 0,
    "not_configured": 6,
    "blocked": 0,
    "token_present": 0,
    "token_absent": 6
  }
}
```

## Status Semantics

- `configured`: URL env is present and safe to summarize. This does not mean the endpoint is reachable or authenticated.
- `not_configured`: URL env is absent. Token may still be `present` or `absent`, but the endpoint is not configured.
- `blocked`: URL env is present but unsafe or invalid. The PC workstation must not adopt that URL.

## UI Boundary

O7 Previews exposes this through a manual `Load live endpoints manifest` button. The UI must not add ping, connect, send, test command, speak, play, submit, stop, cancel, recovery, keyboard, or map-click controls based on this manifest.
