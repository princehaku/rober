# 4G Remote MVP

The real 4G product path is not phone-to-robot WiFi. A 4G robot should initiate outbound traffic to a cloud endpoint, because carrier NAT usually prevents stable inbound access to the robot.

## Roles

- Phone app/web: talks to cloud.
- Cloud API: stores commands, status, and acknowledgements.
- Robot `remote_bridge`: polls cloud over outbound HTTP.
- Robot behavior layer: executes `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, and cancel.
- Local `operator_gateway`: local debugging and fallback only; it is not the formal 4G phone channel.

## MVP Cloud API

```text
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
```

The first implementation uses HTTP polling so it is testable without a real 4G SIM or cloud account. A future MQTT or WebSocket transport must preserve the same command/status/ack semantics.

The Docker-only local mock cloud is implemented inside the operator HTTP gateway
as an in-memory control-plane store. It is a phone-safe entry for submit command,
read current status, and read command ACK during local development. It does not
expose `/cmd_vel`, serial ports, baudrate, WAVE ROVER parameters, or raw ROS2
topic names to ordinary phone users.

## Command Contract

```json
{
  "protocol_version": "trashbot.remote.v1",
  "id": "cmd-0001",
  "type": "collect",
  "expires_at": 1778256300.0,
  "payload": {
    "target": "trash_station",
    "trash_type": 0
  }
}
```

Allowed command types:

- `collect` with a non-empty `target`
- `confirm_dropoff`
- `cancel`

Unknown command types, missing `id`, non-object payloads, and expired commands must not execute.

The local mock cloud accepts phone-created commands on
`POST /robots/{robot_id}/commands`, stores the normalized
`trashbot.remote.v1` object, and returns the same object for robot outbound
polling on `GET /robots/{robot_id}/commands/next`. Command `id` is the
idempotency key; duplicate submits return the existing command instead of
creating a second task.

## Cursor And Restart Boundary

`remote_bridge` polls with `last_ack_id` and can optionally persist the last
terminal ACK cursor through `cursor_state_path`. The cursor state file stores
only `robot_id`, `last_terminal_ack_id`, protocol version, and update time. It
must not store bearer tokens, cloud URLs with credentials, serial devices,
hardware parameters, or raw command payloads.

On startup, a valid `cursor_state_path` takes precedence over the launch-time
`last_ack_id` fallback. After a terminal ACK (`acked`, `failed`, or `ignored`)
is successfully posted to the cloud, the bridge writes the new
`last_terminal_ack_id` atomically. If ACK posting fails, the cursor is not
advanced or persisted, so the bridge can retry the same command without
pretending that the cloud accepted the terminal state.

Unknown cursor behavior belongs to the cloud queue contract, not to robot-side
string ordering. The bridge sends the restored `last_ack_id` exactly as an
opaque cursor and never compares command IDs lexicographically. The current
local mock cloud looks for an exact command-id match; if the cursor is unknown,
it falls back to scanning from the beginning and returns the first unacked,
unexpired command. A production cloud may use database offsets or ACK tables,
but it must preserve the same opaque-cursor rule.

## Status Contract

Robot status is posted by the robot and should be enough for a phone UI to render current state:

```json
{
  "protocol_version": "trashbot.remote.v1",
  "robot_id": "trashbot-001",
  "state": "delivering",
  "message": "remote collect command accepted",
  "updated_at": 1778256012.0
}
```

The phone-safe read endpoint is `GET /robots/{robot_id}/status`. A missing robot
status returns `state = "unknown"` with a message that the robot has not posted
status yet, rather than inventing a successful or failed robot state.

## Ack Contract

```json
{
  "protocol_version": "trashbot.remote.v1",
  "robot_id": "trashbot-001",
  "command_id": "cmd-0001",
  "state": "acked",
  "message": "collect command submitted",
  "updated_at": 1778256013.0,
  "result": {}
}
```

Allowed ack states:

- `acked`
- `failed`
- `ignored`

`acked` means the robot-side bridge accepted or submitted the command to the local behavior interface. It is not a final delivery result; the cloud UI must keep reading robot status for later `completed`, `needs_human_help`, or failure states.

`failed` and `ignored` are also terminal ACK states for the remote command
envelope. They explain why the bridge will not keep trying that command, but
they still do not prove the physical robot delivered trash or reached a
hardware-safe final pose. Phone-facing UX must treat ACK as command-processing
state and status as the continuing delivery/result surface.

The phone-safe read endpoint is
`GET /robots/{robot_id}/commands/{command_id}/ack`. A missing ACK returns an
`ack_not_found` error so the UI can keep polling or show that the robot has not
processed the command yet.

## Safety Rules

- The robot never exposes `/cmd_vel` over the remote bridge.
- The bridge calls only behavior-level ROS contracts.
- `command.id` is an idempotency key; duplicate IDs reuse the cached ack.
- Expired commands are ignored.
- Malformed `collect` commands without a non-empty `target` fail before any local action goal is sent.
- New `collect` commands are ignored while a task is already active.
- Cloud outages do not automatically stop an already running local task.
- Hardware movement still depends on local navigation and base safety layers.

## Current Limits

- No real cloud account is configured.
- No SIM or carrier network test has been run.
- The local mock-cloud tests validate protocol behavior only.
- Authentication is represented by a bearer token field, but production identity, provisioning, rotation, and permissions are not implemented.
