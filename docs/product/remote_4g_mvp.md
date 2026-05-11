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

The Docker/local proof now has two control-plane surfaces:

- Local fallback: `operator_gateway` still embeds a mock cloud for local
  debugging and degraded operator workflows.
- Independent relay: `ros2_trashbot_behavior.remote_cloud_relay` is a separate
  HTTP service module with bearer auth, file-backed or SQLite-backed proof
  persistence, health/readiness checks, and phone-safe JSON errors. It can run
  in local Python or Docker without ROS2 runtime and without the
  `operator_gateway` process.

Both surfaces preserve `trashbot.remote.v1` command/status/ack semantics and do
not expose `/cmd_vel`, serial ports, baudrate, WAVE ROVER parameters, or raw
ROS2 topic names to ordinary phone users. The independent relay is still
`software_proof_docker_deploy`: it does not prove production cloud hosting,
HTTPS/TLS, public ingress, real 4G/SIM, OSS/CDN, Nav2/fixed-route, WAVE ROVER,
or HIL.

The independent relay also has a production preflight gate for deployment
readiness:

```text
GET /preflightz
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

The preflight output is machine-readable JSON with
`evidence_boundary=software_proof_docker_preflight_gate`, `production_ready`,
`overall_status`, `safe_summary`, `retry_hint`, and per-check status records.
It checks secret provisioning, HTTPS/public ingress, OSS/CDN configuration,
state store writability, and phone-safe redaction. Docker/local HTTP, missing
or placeholder secrets, missing TLS/public ingress, OSS/CDN placeholders,
file-backed store, missing production DB/queue, and unwritable state paths must
remain blocked or warning states. A blocked preflight is not a robot delivery
failure; it is an上线前配置 gate telling the phone/cloud team what to fix next.

When `TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite`, the same preflight uses
`evidence_boundary=software_proof_docker_sqlite_state_store`. That boundary
means the relay can prove single-node command/status/ack recovery across store
reopen or relay restart. It still must not claim production DB/queue,
multi-instance consistency, backup/restore, disaster recovery, real cloud, real
4G/SIM, OSS/CDN traffic, Nav2/fixed-route delivery, WAVE ROVER movement, or HIL.

Example local proof launch:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.json
```

Example SQLite state proof launch:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.sqlite \
  --state-backend sqlite
```

Example Docker deploy proof:

```bash
cp .env.example .env
# Set TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN to a local placeholder only.
docker compose -f docker-compose.remote-cloud-relay.yml build remote-cloud-relay
docker compose -f docker-compose.remote-cloud-relay.yml up -d remote-cloud-relay
curl -fsS http://127.0.0.1:8088/healthz
curl -fsS http://127.0.0.1:8088/readyz
curl -fsS http://127.0.0.1:8088/preflightz || true
```

For a fenced end-to-end Docker smoke:

```bash
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
scripts/remote_cloud_relay_docker_smoke.sh
```

## Bearer Auth Gate

The local/mock cloud API now has a bearer auth gate for software proof before a
real cloud account exists. When the gate is configured, protected remote
endpoints require `Authorization: Bearer <token>` before command, status, or ACK
payloads can be submitted or read. Missing or incorrect credentials return a
phone-safe auth failure instead of raw server details.

This gate proves only the local/mock or independent Docker relay control-plane
behavior. It does not prove production identity, provisioning, token rotation,
HTTPS/TLS, public ingress, or real 4G carrier connectivity.

Phone and diagnostics payloads must not expose bearer tokens, Authorization
headers, credential-bearing cloud URLs, serial devices, baudrate, WAVE ROVER
parameters, `/cmd_vel`, raw ROS topic names, or hardware configuration fields.

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

The local mock cloud and independent relay accept phone-created commands on
`POST /robots/{robot_id}/commands`, store the normalized `trashbot.remote.v1`
object, and return the same object for robot outbound polling on
`GET /robots/{robot_id}/commands/next`. Command `id` is the idempotency key;
duplicate submits return the existing command instead of creating a second
task. Expired commands remain in proof history but are not returned as the next
executable command.

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

Remote bridge failures are conservative around the same cursor contract. Cloud
unreachable, auth failed, malformed command/status/ACK response, or ACK post
failure must not advance `last_terminal_ack_id`, must not persist a terminal
cursor, and must not pretend the cloud accepted a terminal command state. A
malformed command response must not trigger a local action goal.

The independent relay stores commands/status/acks in either a single local JSON
state file or a single local SQLite file. JSON writes through a temporary file
plus atomic replace; SQLite uses a simple table-per-envelope proof schema while
preserving the same `trashbot.remote.v1` HTTP response shape. Both backends are
sufficient for Docker/local restart proof only. A production cloud still needs a
database or queue for concurrency, backups, multi-instance consistency, and
disaster recovery.

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

The phone-safe read endpoint is `GET /robots/{robot_id}/status`. In the
operator fallback, a missing robot status returns `state = "unknown"` with a
message that the robot has not posted status yet, rather than inventing a
successful or failed robot state. In the independent relay, a missing status
returns `status_missing`; a stale status returns `status_stale` with the last
safe status payload. A phone UI must treat both as degraded states and wait for
fresh robot status before implying that the task is healthy.

## Remote Readiness Contract

Phone-facing local/mock status includes `remote_readiness` so a formal phone UI
can render auth and degradation states without parsing raw exceptions or ROS
details.

| Field | Product meaning |
| --- | --- |
| `remote_ready` | `true` only means the current local/mock control-plane conditions allow the phone flow to continue; it is not real cloud, 4G, HIL, or delivery proof. |
| `cloud_reachable` | Whether the configured local/mock control-plane is reachable from the caller's point of view. |
| `auth_state` | Phone-safe auth state such as `mock_not_required`, `required`, `authorized`, or `auth_failed`. |
| `degradation_state` | Phone-safe degradation state such as `ok`, `status_stale`, `command_pending`, `auth_failed`, `cloud_unreachable`, or `malformed_response`. |
| `retry_hint` | Operator/phone action hint such as `ok`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, or `contact_support`. |
| `safe_phone_copy` | Plain-language UI copy that must not include raw JSON, ROS topic names, secrets, serial devices, or hardware parameters. |

`auth_state=authorized` means the local/mock request passed the configured bearer
gate. `degradation_state=ok` means the control-plane contract is healthy enough
for the next software step. Neither value proves the robot delivered trash,
reached a Nav2/fixed-route target, moved the WAVE ROVER base, or passed HIL.

The independent Docker relay also exposes process-level readiness:

```text
GET /healthz
GET /readyz
```

`/healthz` reports service liveness, protocol version, and
`software_proof_docker_deploy` evidence boundary. `/readyz` returns true only
when the protocol is the expected `trashbot.remote.v1`, the credential gate is
configured, the proof state store is writable, and the phone-safe failure
redaction self-check passes. These endpoints are for deployment and future phone
diagnostics; they must not expose bearer tokens, credential-bearing URLs, serial
devices, baudrate, WAVE ROVER parameters, ROS topic names, `/cmd_vel`, or raw
tracebacks.

`/preflightz` is stricter than `/readyz`: it is allowed and expected to fail in
Docker/local proof when production prerequisites are absent. A phone-safe
preflight failure should render as cloud setup blocked or not production-ready,
not as a trash delivery failure, navigation failure, 4G success, OSS upload
success, or hardware/HIL result. The JSON must not expose bearer tokens,
Authorization headers, OSS secrets, root passwords, serial devices, baudrate,
WAVE ROVER parameters, ROS topic names, or `/cmd_vel`.

SQLite path missing, unwritable, or initialization failures must also render as
phone-safe state-store readiness failures. The UI should show cloud setup
blocked and a retry hint, not raw filesystem paths, sqlite stack traces, bearer
tokens, ROS topics, serial devices, baudrate, WAVE ROVER parameters, or
`/cmd_vel`.

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
- The independent relay tests validate local HTTP, bearer auth, file persistence,
  health/readiness, Docker deploy startup, and phone-safe error behavior only.
- Bearer auth gate is covered by local/mock software proof only; production identity, provisioning, rotation, permissions, HTTPS/TLS, and public cloud ingress are not implemented.
- Remote bridge degradation/cursor safety is covered by local/mock software proof only; it does not prove weak-network recovery on a carrier 4G link.
- OSS/CDN upload, STS credentials, CDN read path, Nav2/fixed-route delivery,
  WAVE ROVER motion, and HIL remain unverified by this proof.
