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
- Independent relay: `ros2_trashbot_cloud_relay.remote_cloud_relay` is a separate
  HTTP service module with bearer auth, file-backed or SQLite-backed proof
  persistence, health/readiness checks, and phone-safe JSON errors. It can run
  in local Python or Docker without ROS2 runtime and without the
  `operator_gateway` process. The cloud-relay entrypoint wraps the existing
  onboard relay implementation so command/status/ack semantics stay single-source.

Both surfaces preserve `trashbot.remote.v1` command/status/ack semantics and do
not expose `/cmd_vel`, serial ports, baudrate, WAVE ROVER parameters, or raw
ROS2 topic names to ordinary phone users. The independent relay is still
`software_proof_docker_deploy`: it does not prove production cloud hosting,
HTTPS/TLS, public ingress, real 4G/SIM, OSS/CDN, Nav2/fixed-route, WAVE ROVER,
or HIL.

The independent relay now also hosts the dependency-free `mobile/web/` PWA
shell on the same origin:

```text
GET /, /index.html, /app.js, /styles.css, /manifest.webmanifest,
GET /service-worker.js, /offline.html, /icon-192.svg, /icon-512.svg
```

This is a static phone shell only. `/api/*`, `/robots/*`, `/healthz`,
`/readyz`, `/preflightz`, command routes, and ACK routes are resolved before
static lookup, so opening the PWA cannot shadow the cloud control plane.
Static serving is restricted to the `mobile/web/` file set; missing assets and
path traversal return phone-safe 404 JSON without local absolute paths. The
evidence boundary is `software_proof_docker_cloud_hosted_mobile_web_gate`; it
does not prove production cloud, HTTPS/TLS public ingress, real 4G/SIM,
real phone browser/device validation, production app, PWA install prompt,
OSS/CDN live traffic, production DB/queue, Nav2/fixed-route, WAVE ROVER, HIL,
or delivery success.

The hosted shell also has a same-origin phone-safe adapter:

```text
GET /api/status
GET /api/diagnostics
```

These two static-phone APIs do not require bearer auth and do not change the
robot command/status/ACK contract. They select
`TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID` or `trashbot-001`, read the relay
store's latest `/robots/{robot_id}/status` when present, and return only a safe
copy. If no status exists, the response is still JSON 200 with
`overall_status=blocked` and `state=status_missing`, not a 404. The adapter is
always fail closed: `can_collect=false`, `can_confirm_dropoff=false`,
`can_cancel=false`, `phone_readiness.can_continue=false`, and
`command_safety.actions.*.enabled=false`. `/api/diagnostics` includes the same
summary, `cloud_hosted_mobile_web_gate`, `latest_status` when safe, and
`evidence_boundary=software_proof_docker_cloud_hosted_mobile_web_gate`.

The independent relay also has a production preflight gate for deployment
readiness:

```text
GET /preflightz
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

The preflight output is machine-readable JSON with
`evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate` for the current Docker-only deployment gate, `production_ready`,
`overall_status`, `safe_summary`, `retry_hint`, and per-check status records.
It checks secret provisioning, HTTPS/public ingress, OSS/CDN configuration,
state store writability, and phone-safe redaction. Docker/local HTTP, missing
or placeholder secrets, missing TLS/public ingress, OSS/CDN placeholders,
file-backed store, missing production DB/queue, and unwritable state paths must
remain blocked or warning states. A blocked preflight is not a robot delivery
failure; it is an上线前配置 gate telling the phone/cloud team what to fix next.

The current deployment-readiness gate extends that preflight with
`schema=trashbot.cloud_deployment_readiness`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_cloud_deployment_readiness_gate`. It
checks public base URL/TLS/public ingress, local healthcheck endpoints, bearer
credential placeholders, state backend type, production DB/queue gap, OSS/CDN
gap, 4G/SIM gap, and whether a deployment runbook or Docker smoke entry exists.
It is blocked-by-design on the Docker-only host: `production_ready=false`,
`overall_status=blocked`, `not_proven`, `safe_summary`, and `retry_hint` must
remain visible to the phone/cloud operator.

Generate the artifact locally:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-deployment-readiness-artifact /tmp/trashbot_cloud_deployment_readiness.json
```

Consume it in preflight:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DEPLOYMENT_READINESS_ARTIFACT=/tmp/trashbot_cloud_deployment_readiness.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

This proof does not establish real cloud hosting, real HTTPS/TLS, public
ingress, 4G/SIM connectivity, OSS/CDN traffic, production DB/queue,
Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success. The
artifact, preflight output, and phone-safe summaries must not expose bearer
tokens, Authorization headers, OSS secrets, AK/SK, root passwords, DB URLs,
queue URLs, credential-bearing URLs, raw state paths, serial ports, baudrate,
WAVE ROVER parameters, ROS topic names, `/cmd_vel`, or tracebacks.

The relay now also supports a cloud external probe bundle with
`schema=trashbot.cloud_external_probe_bundle`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_cloud_external_probe_bundle_gate`.
The CLI probes `/healthz`, `/readyz`, and `/preflightz` from a local or future
public base URL, but the artifact only stores endpoint paths, HTTP status, JSON
contract status, redaction status, safe summary, retry hint, and `not_proven`.
It never stores the base URL, Authorization headers, tokens, response bodies,
local paths, ROS topics, serial details, or hardware control names.

Generate the local proof artifact:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-external-probe-artifact /tmp/trashbot_cloud_external_probe.json \
  --cloud-external-probe-base-url http://127.0.0.1:8088
```

Consume it in preflight:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_PROBE_ARTIFACT=/tmp/trashbot_cloud_external_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

A valid bundle may set the preflight evidence boundary to
`software_proof_docker_cloud_external_probe_bundle_gate`, but it must keep
`production_ready=false` and `overall_status=blocked`. This gate proves only
Docker/local endpoint contract and artifact validation in the current sprint;
it is not proof of real HTTPS/TLS, public ingress, DNS, 4G/SIM, OSS/CDN live
traffic, production DB/queue, HIL, Nav2/fixed-route delivery, or real delivery.

The relay also exposes a public ingress/TLS/reverse-proxy configuration gate
with `schema=trashbot.cloud_public_ingress_tls_gate`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_cloud_public_ingress_tls_gate`.
It separates two blocked deployment-readiness states:

- `missing_public_ingress_tls_config`: no complete public ingress/TLS/reverse-proxy configuration package exists.
- `public_ingress_tls_config_present_not_externally_proven`: the configuration package shape exists, but there is still no real external HTTPS/TLS, public ingress, DNS, reverse-proxy routing, or firewall proof.

Generate the artifact locally:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PUBLIC_BASE_URL=https://relay.example.invalid \
TRASHBOT_REMOTE_CLOUD_TLS_MODE=reverse_proxy \
TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS=public_https \
TRASHBOT_REMOTE_CLOUD_REVERSE_PROXY_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_FIREWALL_CONFIG=present \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-public-ingress-tls-artifact /tmp/trashbot_cloud_public_ingress_tls.json
```

Consume it in preflight:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_PUBLIC_INGRESS_TLS_ARTIFACT=/tmp/trashbot_cloud_public_ingress_tls.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Both states must keep `production_ready=false` and `overall_status=blocked`.
This gate must not expose real URLs, credential-bearing URLs, Authorization
headers, bearer tokens, TLS private keys, private-key paths, root passwords,
OSS AK/SK, DB/queue URLs, local state paths, serial ports, WAVE ROVER
parameters, ROS topic names, `/cmd_vel`, or tracebacks.

The relay also exposes a cloud DB/queue config gate with
`schema=trashbot.cloud_db_queue_config_gate`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_cloud_db_queue_config_gate`. It
separates two blocked production-readiness states:

- `missing_cloud_db_queue_config`: no production DB/queue configuration package exists.
- `cloud_db_queue_config_present_not_externally_proven`: the configuration package shape exists, but there is still no real connectivity, multi-instance consistency, queue ordering, transaction isolation, backup, or disaster-recovery proof.

Generate the artifact locally:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_QUEUE_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_DB_MIGRATION_CONFIG=present \
TRASHBOT_REMOTE_CLOUD_QUEUE_WORKER_CONFIG=present \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-db-queue-config-artifact /tmp/trashbot_cloud_db_queue_config.json
```

Consume it in preflight:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_QUEUE_CONFIG_ARTIFACT=/tmp/trashbot_cloud_db_queue_config.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Both states must keep `production_ready=false` and `overall_status=blocked`.
This gate must not expose DB/queue endpoints, credential-bearing endpoints,
Authorization headers, bearer tokens, root passwords, local state paths, serial
ports, WAVE ROVER parameters, ROS topic names, `/cmd_vel`, or tracebacks.

The relay now adds a cloud DB/queue external probe bundle gate with
`schema=trashbot.cloud_db_queue_external_probe_bundle`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_cloud_db_queue_external_probe_gate`.
The bundle is the reusable entrypoint for future production DB/queue probes:
DB connectivity, queue connectivity, migration check, worker check,
multi-instance consistency, ordering, transaction isolation, and
backup/recovery. In the current Docker-only environment those statuses remain
`not_run` or `not_externally_proven`; a valid artifact still keeps
`production_ready=false`, `overall_status=blocked`, and
`external_probe_complete=false`.

Generate the artifact locally:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-cloud-db-queue-external-probe-artifact /tmp/trashbot_cloud_db_queue_external_probe.json
```

Consume it in preflight:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_DB_QUEUE_EXTERNAL_PROBE_ARTIFACT=/tmp/trashbot_cloud_db_queue_external_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

The preflight check may pass only as software proof: schema, checksum,
redaction, and preflight consumption are verified, while real DB/queue
connectivity, production queue ordering, transaction isolation,
multi-instance consistency, backup policy, disaster recovery, real cloud, real
4G/SIM, Nav2/fixed-route delivery, WAVE ROVER/HIL, and delivery success remain
`not_proven`. The bundle must not expose DB/queue endpoints,
credential-bearing endpoints, Authorization headers, bearer tokens, root
passwords, local state paths, serial ports, WAVE ROVER parameters, ROS topic
names, `/cmd_vel`, or tracebacks.

The relay now adds an external evidence intake gate with
`schema=trashbot.external_evidence_intake`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_external_evidence_intake_gate`. It is
the safe handoff surface for future real public ingress/TLS, OSS/CDN,
production DB/queue, and 4G/SIM evidence. In the current Docker-only
environment it stores only enum statuses, material time, fixed redacted
summaries, `safe_summary`, `retry_hint`, `not_proven`, `redaction_status`, and
checksum. It must keep `production_ready=false`, `overall_status=blocked`, and
`external_evidence_complete=false`.

Generate and consume the intake artifact:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-external-evidence-intake-artifact /tmp/trashbot_external_evidence_intake.json

PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_INTAKE_ARTIFACT=/tmp/trashbot_external_evidence_intake.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

The CLI also accepts `--external-evidence-intake-artifact` for preflight. A
valid intake artifact only proves schema, checksum, redaction, and preflight
consumption. It does not prove real cloud, HTTPS/TLS, public ingress, OSS
upload, CDN origin fetch, STS issuance, production DB/queue, queue ordering,
transaction isolation, real 4G/SIM, Nav2/fixed-route delivery, WAVE ROVER/HIL,
or delivery success. It must not expose URLs, credential-bearing endpoints,
Authorization headers, bearer tokens, OSS AK/SK, DB/queue URLs, local paths,
response bodies, tracebacks, serial ports, ROS topic names, or `/cmd_vel`.

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

The relay also supports an OSS/CDN live probe artifact with
`schema=trashbot.oss_cdn_live_probe` and
`evidence_boundary=software_proof_docker_oss_cdn_live_probe_gate`. It consumes
the existing manifest artifact as input, can issue safe HEAD probes, and writes
only endpoint paths, object key hashes, HTTP status, object count,
`redaction_status`, `safe_summary`, `retry_hint`, and `not_proven`. It never
writes complete CDN URLs, complete object keys, Authorization headers, bearer
tokens, OSS credentials, local paths, response bodies, ROS topics, serial data,
or `/cmd_vel`. In the Docker-only environment the artifact and preflight check
must keep `production_ready=false`, `overall_status=blocked`, and
`live_probe_complete=false` even if a local/mock HTTP probe observes 2xx.

Generate and consume the live probe artifact:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-oss-cdn-live-probe-artifact /tmp/trashbot_oss_cdn_live_probe.json \
  --oss-cdn-manifest-artifact /tmp/trashbot_oss_cdn_manifest.json

PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_LIVE_PROBE_ARTIFACT=/tmp/trashbot_oss_cdn_live_probe.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

Example local proof launch:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.json
```

Example SQLite state proof launch:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --host 127.0.0.1 \
  --port 8088 \
  --state-path /tmp/trashbot_remote_cloud_relay.sqlite \
  --state-backend sqlite
```

Example backup/restore drill:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_STATE_BACKEND=sqlite \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
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
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --network-recovery-drill \
  --state-backend sqlite \
  --state-path /tmp/trashbot_network_recovery.sqlite \
  --write-network-recovery-artifact /tmp/trashbot_network_recovery_drill.json
```

Preflight can consume the artifact:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_NETWORK_RECOVERY_ARTIFACT=/tmp/trashbot_network_recovery_drill.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
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
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-oss-cdn-manifest /tmp/trashbot_oss_cdn_manifest.json \
  --manifest-robot-id robot-local-proof \
  --manifest-task-id task-local-proof \
  --manifest-date 2026-05-12
```

Preflight can consume the artifact by environment variable or CLI parameter:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_OSS_CDN_MANIFEST_ARTIFACT=/tmp/trashbot_oss_cdn_manifest.json \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --preflight
```

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
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

## Command Expiry Safety Guard

The Robot bridge treats an expired cloud command as a terminal `ignored` ACK and
does not submit any local behavior action. It also reports a phone-safe
fail-closed status so operator status, phone readiness, and command safety do
not look green after the ignored ACK.

When this guard is active, status/readiness must include:

- `degradation_state=command_expired`
- `remote_ready=false`
- `expired_command_id=<safe command id or [redacted]>`
- `primary_actions_enabled=false`
- `safe_phone_copy=这条云端指令已经过期，机器人没有执行；请重新提交最新指令。`
- `retry_hint=resubmit_command`
- `proof_boundary=software_proof_docker_cloud_command_expiry_safety_guard`

`build_phone_readiness` and `trashbot.command_safety.v1` must block Start,
Confirm Dropoff, and Cancel for `command_expired`; Diagnostics remains available
so support can inspect the safe command id and proof boundary. This is a local
software proof only. It does not prove production DB/queue behavior, public
HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, real phone browser, Nav2 or fixed
route delivery, WAVE ROVER motion, HIL, or delivery success.

## Pending ACK Status Guard

The robot `remote_bridge` now exposes `cloud_pending_ack_status_guard` for the
specific case where a local command has already reached a terminal ACK state,
but replaying that terminal ACK to the cloud fails. This usually follows a
restart or temporary ACK outage after the earlier `cloud_ack_outage_replay_guard`
has persisted `pending_terminal_ack`.

When this guard is active, status/readiness must remain phone-safe and fail
closed:

- `degradation_state=command_pending`
- `remote_ready=false`
- `pending_terminal_ack_id=<safe command id or [redacted]>`
- `primary_actions_enabled=false`
- `safe_phone_copy=本地命令已完成终态，但云端 ACK 还没确认，暂不能拉取新命令。`
- `retry_hint=retry_cloud` or the cloud client's safer retry hint
- `proof_boundary=software_proof_docker_cloud_pending_ack_status_guard`

The robot must not advance `last_terminal_ack_id` until the pending terminal ACK
is accepted by the cloud. While `pending_terminal_ack` exists, the worker must
not pull a new command, must not execute Start Delivery, Confirm Dropoff, or
Cancel again, and must not treat any ACK response as delivery success. This
prevents a phone user from seeing green readiness while the cloud cursor still
cannot confirm the previous terminal command.

Both the persisted cursor file and the status payload use a safe subset. They
must not save or expose bearer tokens, Authorization headers, credential-bearing
cloud URLs, serial devices, baudrate, WAVE ROVER parameters, raw ROS topics,
`/cmd_vel`, tracebacks, production DB/queue credentials, 4G carrier details, or
any delivery success claim. The evidence boundary is only
`software_proof_docker_cloud_pending_ack_status_guard`; it does not prove real
4G/SIM, production cloud, public HTTPS/TLS, production DB/queue, real phone
browser, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

Example Docker deploy proof:

```bash
cd cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-placeholder \
  docker compose -f docker-compose.yml build remote-cloud-relay
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-placeholder \
  docker compose -f docker-compose.yml up -d remote-cloud-relay
curl -fsS http://127.0.0.1:8088/healthz
curl -fsS http://127.0.0.1:8088/readyz
curl -fsS http://127.0.0.1:8088/preflightz || true
```

For a fenced end-to-end Docker smoke:

```bash
TRASHBOT_REMOTE_CLOUD_PUBLISHED_PORT=18088 \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-smoke-token \
bash scripts/docker_smoke.sh
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
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
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
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
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
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
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

The transaction isolation drill adds the next Docker/local artifact for
interleaved command/status/ACK writes on one robot. Generate it with:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-transaction-isolation-artifact /tmp/trashbot_transaction_isolation_drill.json \
  --transaction-isolation-robot-id robot-local-proof
```

Then pass it to preflight with
`TRASHBOT_REMOTE_CLOUD_TRANSACTION_ISOLATION_ARTIFACT` or
`--transaction-isolation-artifact`. The resulting evidence boundary is
`software_proof_docker_transaction_isolation_gate`; phone consumption uses
`software_proof_docker_transaction_isolation_phone_consumption`.

The artifact fixes the local drill expectations for command A remaining
non-terminal, command B receiving a terminal ACK, status writes interleaving
with ACK writes, the ACK cursor staying before unfinished command A, and ACK not
becoming delivery success. It covers `ready|missing|invalid|stale|failed`
summaries for phone status and diagnostics. It is not real production
transaction isolation, a production DB/queue, multi-instance consistency, real
cloud, real 4G/SIM, Nav2/fixed-route delivery, WAVE ROVER/HIL, or delivery
success proof.

The production recovery gate adds the next Docker/local artifact for production
backup and disaster recovery readiness gaps. Generate it with:

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay \
  --write-production-recovery-artifact /tmp/trashbot_production_recovery_gate.json \
  --production-recovery-robot-id robot-local-proof
```

Then pass it to preflight with
`TRASHBOT_REMOTE_CLOUD_PRODUCTION_RECOVERY_ARTIFACT` or
`--production-recovery-artifact`. The resulting evidence boundary is
`software_proof_docker_production_recovery_gate`; phone consumption uses
`software_proof_docker_production_recovery_phone_consumption`.

The artifact fixes the local gate expectations for Docker/local
backup/restore input, schema/checksum invariants, production backup policy and
disaster recovery staying blocked, file/SQLite proof store boundaries,
production DB/queue absence, multi-instance consistency absence, retention
policy absence, RPO/RTO absence, and ACK as command accepted/processing
evidence only. It covers `ready|missing|invalid|stale|failed|blocked`
summaries for phone status and diagnostics. It is not real production DB/queue,
real production backup policy, real disaster recovery, multi-instance
consistency, real cloud, real 4G/SIM, OSS/CDN live traffic, Nav2/fixed-route
delivery, WAVE ROVER/HIL, or delivery success proof.

Phone and diagnostics payloads must not expose bearer tokens, Authorization
headers, credential-bearing cloud URLs, serial devices, baudrate, WAVE ROVER
parameters, `/cmd_vel`, raw ROS topic names, or hardware configuration fields.

The mobile operation-log gate adds a phone/support metadata layer with
`evidence_boundary=software_proof_docker_mobile_operation_log_gate`. Fields such
as `operation_log` or `phone_operation_log` may summarize recent user actions,
blocked reasons, pending ACK, offline/recovery states, manual takeover, and
support handoff copy. They are not part of the `trashbot.remote.v1`
command/status/ack envelope, and they must not be used by the robot bridge to
start `collect`, `confirm_dropoff`, or `cancel`, POST ACK, advance or persist a
cursor, or turn ACK wording into delivery success. ACK remains accepted or
processing evidence only; phones and support tools must continue reading status
and task records for actual progress, failure, cancellation, or handoff state.

Operation-log metadata must stay phone-safe. It must not expose bearer tokens,
Authorization headers, OSS secrets, AK/SK, root passwords, DB/queue URLs,
credential-bearing URLs, raw ROS topic names, `/cmd_vel`, serial devices,
baudrate, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums,
or complete artifacts. This gate does not prove a real phone device/browser,
production app, real cloud/4G, OSS/CDN live traffic, production DB/queue,
Nav2/fixed-route delivery, WAVE ROVER movement, HIL, or delivery success.

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
only `robot_id`, `last_terminal_ack_id`, optional redacted pending ACK,
protocol version, proof boundary, and update time. It must not store bearer
tokens, cloud URLs with credentials, serial devices, hardware parameters, raw
command payloads, raw ROS topics, `/cmd_vel`, WAVE ROVER details, tracebacks,
or delivery success claims.

On startup, a valid `cursor_state_path` takes precedence over the launch-time
`last_ack_id` fallback. After a terminal ACK (`acked`, `failed`, or `ignored`)
is successfully posted to the cloud, the bridge writes the new
`last_terminal_ack_id` atomically. If ACK posting fails, the cursor is not
advanced as a terminal cursor; only the pending ACK is persisted so the bridge
can retry without pretending that the cloud accepted the terminal state.

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
bridge persists a redacted `pending_terminal_ack`, leaves
`last_terminal_ack_id` unchanged, and records a degraded state. On worker
restart or the next polling cycle, the bridge posts the pending ACK before
requesting a new command. Once that replay succeeds, it advances and persists
`last_terminal_ack_id` and clears `pending_terminal_ack`; until then it must not
fetch another command or repeat local command execution.

### cloud_ack_outage_replay_guard

`cloud_ack_outage_replay_guard` is the Robot-side ACK outage guard for the
Docker/local remote bridge. Its evidence boundary is
`software_proof_docker_cloud_ack_outage_replay_guard`. It proves only that a
single local worker state file can preserve a terminal ACK after cloud ACK POST
outage or malformed ACK response, replay it after restart, and avoid duplicate
local backend execution before the cloud accepts that ACK.

The pending ACK state is a safe subset: command id, terminal ACK state/message,
safe result fields, `robot_id`, protocol version, `updated_at`, and
`evidence_boundary`. It is not a production DB/queue, worker/cutover, real 4G
or SIM, HTTPS/TLS public ingress, real phone/browser, Nav2/fixed-route, WAVE
ROVER/HIL, or delivery success proof. A successful replay means only that the
cloud ACK endpoint accepted the command-processing envelope.

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

For the cloud-hosted static shell only, `GET /api/status` and
`GET /api/diagnostics` wrap that store status into a blocked phone-safe summary
instead of surfacing the store's 404 to the browser. This adapter is a
Docker/local software proof convenience for same-origin phone rendering. It must
not leak Authorization headers, bearer tokens, DB/queue URLs, local paths, ROS
topics, `/cmd_vel`, serial devices, WAVE ROVER details, tracebacks, or complete
artifacts, and it must not open Start Delivery, Confirm Dropoff, or Cancel.

The local operator fallback also exposes `/api/status.phone_readiness` for the
phone-first readiness gate. This is a UI aggregation of local delivery status,
action permissions, local/mock remote readiness, optional preflight summaries,
optional backup/restore drill summaries, and optional OSS/CDN diagnostic
reference summaries. It also includes optional network recovery, credential
rotation, and provisioning audit summaries when their artifacts are configured.
It uses
`schema=trashbot.phone_readiness.v1`, `schema_version=1`, and
`evidence_boundary=software_proof_docker_local_phone_ui_readiness_gate`.

The `mobile/web/` entrypoint is a phone-side consumer of these phone-safe
status, diagnostics, readiness, command-safety, and offline/resume summaries.
Metadata such as `mobile_web_entrypoint`,
`mobile_web_entrypoint_readiness`, or `pwa_entrypoint` may describe the static
mobile shell or installability contract, but it is not part of the robot
`trashbot.remote.v1` command/status/ack envelope. A metadata-only response must
not trigger `/trashbot/collect_trash`, dropoff confirmation, cancel, ACK
posting, cursor advancement, cursor persistence, or wording that treats ACK as
delivery success. Deployment-readiness metadata such as
`deployment_readiness`, `cloud_deployment_readiness`, or `preflight` follows
the same robot-side rule: it is diagnostic cloud deployment evidence only, and
must not be interpreted as a robot command or cursor instruction.
Task-start confirmation fields such as `mobile_task_start_confirmation`,
`mobile_task_start_confirmation_readiness`, and
`task_start_confirmation_payload` are phone/API proof that the user selected a
destination and explicitly confirmed trash loading before Start Delivery. They
are not ROS2 action results, WAVE ROVER feedback, HIL, Nav2/fixed-route proof,
or delivery success. If those fields appear beside `command` in a cloud
response, the robot bridge ignores them; only a valid `trashbot.remote.v1`
`command.id`, `command.type`, and `command.payload` can produce a backend call
or terminal ACK.

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
- `cloud_db_queue_external_probe_bundle` is the phone-safe DB/queue external
  probe entrypoint. `ready` or `pass` means only that artifact schema,
  checksum, redaction, and preflight consumption are valid; it must still keep
  `production_ready=false`, `overall_status=blocked`, and real production
  DB/queue, ordering, transaction isolation, backup/recovery, real cloud,
  real 4G/SIM, WAVE ROVER/HIL, and delivery success as not proven.
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
