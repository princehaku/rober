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

The SQLite relay also supports a Docker/local backup/restore drill with
`evidence_boundary=software_proof_docker_backup_restore_drill`. The drill
generates a JSON artifact with schema/version/metadata/checksum, restores that
artifact into a fresh SQLite state path, and validates the restored
command/status/ack envelopes plus conservative ACK cursor behavior. This is a
software proof only: production backup policy, production DB/queue,
multi-instance consistency, real disaster recovery, real cloud, real 4G/SIM,
OSS/CDN traffic, formal phone UI, Nav2/fixed-route delivery, WAVE ROVER, and
HIL remain unproven.

The relay now has a Docker/local network recovery drill with
`evidence_boundary=software_proof_docker_network_recovery_drill`. The drill
simulates an equivalent local relay/cloud connection failure, proves that ACK
post failure is not delivery success and does not advance cursor semantics,
then verifies that command/status/ack envelopes can be reconciled after
recovery. It also forces a stale status and records that phones must show a
blocked/warning recovery state instead of green ready. The JSON artifact uses
`schema=trashbot.network_recovery_drill`, `schema_version=1`, `overall_status`,
`steps`, `cursor_invariant`, `safe_summary`, `retry_hint`, `not_proven`,
`updated_at`, and `checksum`. It must not include bearer tokens,
Authorization headers, OSS secrets, AK/SK, root passwords, raw state paths,
serial ports, baudrate, WAVE ROVER parameters, ROS topic names, `/cmd_vel`, or
tracebacks. This remains software proof only and does not prove real cloud,
real 4G/SIM, production incident recovery, delivery success, Nav2/fixed-route,
WAVE ROVER, or HIL.

The relay now also supports an OSS/CDN object reference manifest proof with
`evidence_boundary=software_proof_docker_oss_cdn_manifest`. The manifest is a
phone-safe JSON artifact for future diagnostic snapshots, logs, or task records:
it fixes the bucket `bytegallop`, region `oss-cn-hangzhou`, object prefix
`rober/<robot_id>/<date>/<task_id>/`, CDN base URL
`https://cdn.bytegallop.com/rober/`, object refs, `not_proven`, and checksum.
It proves only local schema/prefix/CDN URL/checksum shape. It does not prove
real OSS upload, STS issuance, CDN origin fetch, lifecycle policy, production
account, real cloud, real 4G/SIM, HTTPS/TLS public ingress, production DB/queue,
Nav2/fixed-route delivery, WAVE ROVER, or HIL.

The local operator/API can now consume that artifact as a smaller phone-safe
diagnostic reference summary with
`evidence_boundary=software_proof_docker_phone_manifest_consumption`. The
summary is exposed at `/api/status.phone_readiness.oss_cdn_manifest` and
`/api/diagnostics.oss_cdn_manifest`, and both surfaces share the same helper.
It reports only `state=ready|missing|invalid|stale`, schema/version,
`object_count`, the CDN URL rule, freshness, ordinary user copy, retry hint, and
`not_proven`. It must not expose the full artifact, object keys, checksums,
local paths, credentials, raw ROS topics, `/cmd_vel`, serial data, or hardware
configuration.

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

Example backup/restore drill:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --state-backend sqlite \
  --state-path /tmp/trashbot_remote_cloud_relay.sqlite \
  --backup-state-to /tmp/trashbot_remote_cloud_relay_backup.json \
  --restore-state-path /tmp/trashbot_remote_cloud_relay_restored.sqlite \
  --backup-restore-drill
```

The drill output is intended for future phone/operator diagnostics. It reports
`backup_status`, `restore_status`, `drill_status`, `safe_summary`,
`retry_hint`, `evidence_boundary`, and `not_proven`. It must not expose bearer
tokens, Authorization headers, OSS secrets, root passwords, raw state paths,
ROS topic names, serial ports, baudrate, WAVE ROVER parameters, `/cmd_vel`, or
tracebacks.

Example network recovery drill:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --network-recovery-drill \
  --state-backend sqlite \
  --state-path /tmp/trashbot_network_recovery.sqlite \
  --write-network-recovery-artifact /tmp/trashbot_network_recovery_drill.json
```

Preflight can consume the artifact:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=/tmp/trashbot_network_recovery_drill.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

Missing artifacts stay warning, and invalid, stale, or failed artifacts stay
blocked. A passed artifact sets `software_proof_ready=true` and may raise the
local evidence boundary to
`software_proof_docker_network_recovery_drill`, but `production_ready` remains
false until the real cloud, TLS/public ingress, 4G/SIM, production state store,
OSS/CDN and operational recovery evidence exist. Operator/API consumption only
returns `phone_readiness.network_recovery` and
`diagnostics.network_recovery_drill` summaries; it does not return full steps,
local paths, ports, tracebacks, credentials, ROS topics, hardware details or
checksums.

Example OSS/CDN manifest proof:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-oss-cdn-manifest /tmp/trashbot_oss_cdn_manifest.json \
  --manifest-robot-id robot-local-proof \
  --manifest-task-id task-local-proof \
  --manifest-date 2026-05-12
```

Preflight can consume the artifact by environment variable or CLI parameter:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT=/tmp/trashbot_oss_cdn_manifest.json \
python3 -m ros2_trashbot_behavior.remote_cloud_relay --preflight
```

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --preflight \
  --oss-cdn-manifest-artifact /tmp/trashbot_oss_cdn_manifest.json
```

A valid manifest adds a passed `oss_cdn_manifest` preflight check and raises the
local evidence boundary to `software_proof_docker_oss_cdn_manifest`, while
keeping `production_ready=false` until the real production checks are proven.
Missing manifest is a warning; invalid schema/version/prefix/CDN URL/checksum or
phone-safe failure is blocked. The artifact and preflight output must not expose
bearer tokens, Authorization headers, OSS secrets, AK/SK, root passwords, raw
state paths, serial ports, baudrate, WAVE ROVER parameters, ROS topic names,
`/cmd_vel`, or tracebacks.

Operator consumption has a stricter phone UX rule than preflight: `missing`,
`invalid`, or `stale` must keep the phone readiness gate out of a green ready
state and show copy such as "诊断对象引用缺失。", "诊断对象引用损坏。", or
"诊断对象引用已过期。" with a retry hint to refresh or regenerate references.
`ready` still proves only local software consumption of a manifest summary; it
does not prove real OSS upload, STS issuance, CDN origin fetch, real cloud, real
4G/SIM, production DB/queue, Nav2/fixed-route delivery, WAVE ROVER, HIL, or
delivery success.

The operator browser now exposes `phone_readiness.command_safety` as the
button-level gate for local/fallback phone control. Start Delivery, Confirm
Dropoff, and Cancel are enabled only when the legacy local action permission and
the command safety gate both allow the action. The gate blocks primary commands
for stale robot status, pending ACK, auth failure, cloud unreachable, malformed
remote response, missing/invalid/stale manifest summary, and manual takeover.
Diagnostics remains available with a phone-safe blocking explanation so support
can still reproduce the issue. ACK text must stay conservative: an ACK is only
command accepted/processing evidence and does not prove delivery success, real
4G/cloud, OSS/CDN traffic, WAVE ROVER motion, or HIL.

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

The provisioning audit gate adds a separate Docker/local artifact for robot
provisioning, STS issuance boundary, and audit log contract consumption. Generate
it with:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-provisioning-audit-artifact /tmp/trashbot_provisioning_audit_gate.json \
  --provisioning-audit-robot-id robot-local-proof
```

Then pass it to preflight with
`TRASHBOT_REMOTE_CLOUD_PROVISIONING_AUDIT_ARTIFACT` or
`--provisioning-audit-artifact`. The resulting evidence boundary is
`software_proof_docker_provisioning_audit_gate`; `production_ready=false`,
`overall_status=blocked`, and `not_proven` must remain. This is not real STS
issuance, real audit log, production account provisioning, real cloud, real 4G,
Nav2/fixed-route delivery, WAVE ROVER, HIL, or delivery success.

The production store/queue gate adds a Docker/local artifact for the production
DB/queue contract boundary. Generate it with:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-production-store-queue-artifact /tmp/trashbot_production_store_queue_gate.json \
  --production-store-queue-robot-id robot-local-proof
```

Then pass it to preflight with
`TRASHBOT_REMOTE_CLOUD_PRODUCTION_STORE_QUEUE_ARTIFACT` or
`--production-store-queue-artifact`. The resulting evidence boundary is
`software_proof_docker_production_store_queue_gate`; phone consumption uses
`software_proof_docker_production_store_queue_phone_consumption`.
`production_ready=false`, `overall_status=blocked`, and `not_proven` must remain.
This is not a real production DB/queue, multi-instance consistency, production
backup policy, disaster recovery, real cloud, real 4G, Nav2/fixed-route delivery,
WAVE ROVER, HIL, or delivery success.

The queue ordering drill adds a narrower Docker/local artifact for command
ordering invariants. Generate it with:

```bash
PYTHONPATH=src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-queue-ordering-drill-artifact /tmp/trashbot_queue_ordering_drill.json \
  --queue-ordering-drill-robot-id robot-local-proof
```

Then pass it to preflight with
`TRASHBOT_REMOTE_CLOUD_QUEUE_ORDERING_DRILL_ARTIFACT` or
`--queue-ordering-drill-artifact`. The resulting evidence boundary is
`software_proof_docker_queue_ordering_drill`; phone consumption uses
`software_proof_docker_queue_ordering_phone_consumption`.

The artifact fixes the local drill expectations for parallel submits,
adjacent command ids, `cmd-9` before `cmd-10`, cursor advancement only after a
terminal ACK, and ACK as command acceptance/processing evidence only. It covers
`ready|missing|invalid|stale|failed` summaries for phone status and diagnostics.
It is not a real production queue ordering, transaction isolation,
multi-instance consistency, production DB/queue, real cloud, real 4G/SIM,
Nav2/fixed-route delivery, WAVE ROVER/HIL, or delivery success proof.

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

For the network recovery drill compatibility fence, `remote_bridge` treats
status POST failures as a hard stop for that polling cycle: it records a
phone-safe degraded state and does not request a command. If the ACK response is
malformed or the ACK POST fails after local behavior accepted the command, the
bridge keeps the command result only in memory, leaves `last_ack_id` and
`cursor_state_path` unchanged, and retries the same command envelope on the next
poll. Only a successfully posted terminal ACK may advance and persist the
cursor. This is still local/Docker software proof and does not prove real 4G
network recovery, production cloud durability, Nav2/fixed-route delivery, WAVE
ROVER movement, or HIL.

The independent relay stores commands/status/acks in either a single local JSON
state file or a single local SQLite file. JSON writes through a temporary file
plus atomic replace; SQLite uses a simple table-per-envelope proof schema while
preserving the same `trashbot.remote.v1` HTTP response shape. Both backends are
sufficient for Docker/local restart proof only. A production cloud still needs a
database or queue for concurrency, backups, multi-instance consistency, and
disaster recovery.

SQLite backup artifacts store sanitized command/status/ack envelopes rather
than raw database pages. Restore rebuilds a fresh SQLite proof state from those
normalized envelopes and fails closed on schema, version, protocol, evidence
boundary, or checksum mismatch. A successful restore does not convert an ACK
into a trash delivery result; phones must still read status for delivery
progress and failure explanation.

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

The local operator fallback also exposes `/api/status.phone_readiness` for the
phone-first readiness gate. This is a UI aggregation of local delivery status,
action permissions, local/mock remote readiness, optional preflight summaries,
optional backup/restore drill summaries, and optional OSS/CDN diagnostic
reference summaries. It also includes optional network recovery, credential
rotation, and provisioning audit summaries when their artifacts are configured.
It uses
`schema=trashbot.phone_readiness.v1`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_local_phone_ui_readiness_gate`.

Important product boundary:

- `primary_state=ready` means the phone has a safe next software step; it does
  not mean trash delivery succeeded.
- `primary_state=waiting_for_command_ack` means the phone should wait for the
  bridge to process the command envelope; it must not resubmit blindly.
- `primary_state=login_required`, `remote_unreachable`, or
  `remote_response_invalid` explains cloud/control-plane recovery only, not a
  robot navigation failure.
- `cloud_preflight` and `backup_restore` are optional local/Docker proof
  summaries. Missing output remains `not_run` or `unknown`.
- `oss_cdn_manifest` is the phone-safe diagnostic reference summary. `ready`
  means software summary consumption only; `missing`, `invalid`, and `stale`
  block a green first-screen readiness state until references are refreshed or
  regenerated.
- `provisioning_audit` is the phone-safe production provisioning / STS / audit
  gate summary. `ready` means the Docker/local artifact is consumable only; it
  must still expose `production_ready=false`, `overall_status=blocked`, and
  `not_proven`.
- `queue_ordering_drill` is the phone-safe Docker/local queue ordering drill
  summary. It reports ordering, concurrency, cursor, and ACK invariants, but
  keeps `production_ready=false` and lists production queue ordering,
  transaction isolation, production DB/queue, multi-instance consistency, real
  cloud, real 4G/SIM, WAVE ROVER/HIL, and delivery success as not proven.
- `not_proven` must continue to include production phone app, real cloud,
  real 4G/SIM, OSS/CDN, Nav2/fixed-route delivery, WAVE ROVER motion, and HIL
  until those paths have separate evidence.

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
  health/readiness, Docker deploy startup, SQLite backup/restore drill, and
  phone-safe error behavior only.
- Bearer auth gate is covered by local/mock software proof only; production identity, provisioning, rotation, permissions, HTTPS/TLS, and public cloud ingress are not implemented.
- Remote bridge degradation/cursor safety is covered by local/mock software proof only; it does not prove weak-network recovery on a carrier 4G link.
- OSS/CDN upload, STS credentials, CDN read path, Nav2/fixed-route delivery,
  WAVE ROVER motion, and HIL remain unverified by this proof.
