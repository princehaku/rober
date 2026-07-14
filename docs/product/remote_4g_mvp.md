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
POST /api/commands/collect
POST /api/commands/confirm-dropoff
POST /api/commands/cancel
GET  /api/commands/{command_id}/result?robot_id=<robot_id>
POST /robots/{robot_id}/commands
GET  /robots/{robot_id}/commands/next?last_ack_id=<id>
POST /robots/{robot_id}/status
GET  /robots/{robot_id}/status
POST /robots/{robot_id}/commands/{command_id}/ack
GET  /robots/{robot_id}/commands/{command_id}/ack
POST /robots/{robot_id}/commands/{command_id}/terminal-result
```

The phone-facing command API is bearer-gated and task-level only. Each
`POST /api/commands/*` body must include `robot_id`, may include
`command_id` or `idempotency_key`, and may carry a task `payload`. The relay
normalizes those requests into the existing `collect`, `confirm_dropoff`, or
`cancel` command store shape, then returns a phone-safe receipt with
`capability=cloud_phone_command_api`,
`evidence_boundary=software_proof_docker_cloud_phone_command_api_gate`,
`ack_semantics=queued_not_delivery_success`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`. Duplicate
idempotency keys return the existing command id and duplicate info; a successful
receipt still only means queued for robot polling, not delivery success.
If the underlying command store is unavailable, the phone route returns a
phone-safe `503 command_store_unavailable` error instead of a receipt, and the
response must not expose state paths, credentials, ROS topics, serial/UART
details, or WAVE ROVER fields.

The same-origin result reconciliation route is:

```text
GET /api/commands/{command_id}/result?robot_id=<robot_id>
```

It is bearer-gated like the phone command POST routes, but it is read-only. It
does not enqueue, replay, cancel, advance ACK cursors, mutate status, call ROS,
or bypass the robot outbound polling contract. The response schema is
`trashbot.cloud_command_result_reconciliation.v2`, capability is
`cloud_command_result_reconciliation`, and evidence boundary is
`software_proof_docker_cloud_command_result_reconciliation_gate`. It summarizes
only the existing command store, latest safe status, terminal ACK envelope, and
persisted robot/relay terminal result into `queued`, `processing`,
`terminal_result_pending`, `terminal_result_recorded`, `missing_or_expired`, or
`store_unavailable`.

Every result reconciliation response keeps `delivery_success=false`,
`safe_to_control=false`, and `primary_actions_enabled=false`. A terminal ACK is
reported as `terminal_result_pending` until the robot-facing terminal result
write path persists a result for the same `robot_id + command_id`; ACK alone is
not delivery success, not dropoff success, and not cancel success. The route returns `safe_copy` and
`next_required_evidence` for the phone UI and must not expose Authorization,
bearer token, raw state path, DB/queue URL, ROS topic, `/cmd_vel`, serial/UART,
WAVE ROVER details, full artifacts, checksums, or tracebacks.

The robot-facing terminal result write path is:

```text
POST /robots/{robot_id}/commands/{command_id}/terminal-result
```

It accepts `schema=trashbot.cloud_command_terminal_result.v1` and writes the
phone-safe terminal result into the same command store abstraction used by the
phone command API. The write must first find an existing command for the exact
`robot_id + command_id`; it cannot create an orphan result, and a mismatched
body is rejected. File-backed and SQLite-backed proof stores both persist the
result. Reposting the identical terminal result is idempotent; reposting a
different terminal result returns `terminal_result_conflict` and preserves the
first result. Querying the result route after a persisted write returns
`terminal_result_recorded` with `terminal_result_type`, `task_terminal_state`,
`result_code`, safe refs, `safe_copy`, and `next_required_evidence`.

This is still a software terminal result only. Every terminal result response
keeps `delivery_success=false`, `safe_to_control=false`,
`primary_actions_enabled=false`, and `real_world_delivery_proven=false`; it
does not prove field delivery, HIL, route execution, production cloud, or real
phone/browser proof.

O6/O7 now has a local/mock `phone_browser_terminal_material` intake/readback
section for the same `task_id`. Its boundary is fixed to
`software_proof_o6_o7_phone_browser_terminal_material_intake_only`; the relay
only stores safe material enums (`true_phone_browser_evidence`,
`diagnostics_mobile_safe_summary`, `terminal_result_summary`), a terminal result
type, a basename `safe_evidence_ref`, blocked reasons, and next evidence. It
must keep `safe_to_control=false`, `delivery_success=false`,
`route_execution_success=false`, `hil_pass=false`,
`connects_cloud_production=false`, and `robot_control_executed=false`. Raw URL,
cookie, Authorization, token, local path, screenshot body, DOM dump, traceback,
`/cmd_vel`, serial/UART, WAVE ROVER, or any dangerous true field fails closed to
`blocked_not_proven`. This section gives Full-stack a stable read model for
safe phone/browser terminal material summaries, but it is still not true
phone/browser proof, not production cloud, not 4G/SIM, not route execution, not
delivery success, and not HIL.

O6/O7 also has a local/mock `bounded_route_execution_gate_material`
intake/readback section for the same 07:07 controlled route execution gate and
08:09 bounded route command plan. Its boundary is fixed to
`software_proof_o6_o7_bounded_route_gate_material_intake_only`, and its ready
status is `bounded_route_execution_gate_material_ready_not_route_execution_proof`;
the relay only stores exact packet/task/route identity, `route_csv_row_count=28`,
`path_structured_pose_count=28`, `segment_count=27`,
`execution_plan_status=blocked_pending_live_safety_gate`, source boundaries,
blocked reasons, and next evidence. It must keep `safe_to_control=false`,
`delivery_success=false`, `route_execution_success=false`, `hil_pass=false`,
`robot_control_executed=false`, and `connects_cloud_production=false`. Raw local
path, raw command body, `/cmd_vel`, `/api/base/manual`, NavigateToPose,
serial/UART, WAVE ROVER, or any route/delivery/HIL/control true field fails
closed to `blocked_not_proven`. This section is O6/O7 bounded gate material
intake only, not route execution, not delivery success, not HIL, not
safe-to-control, not control capability, not production cloud, and not 4G/SIM
proof.

O6/O7 now also exposes `bounded_route_terminal_result_material` for the 00:24
O5 terminal-result bridge summary. Its O6 schema is
`trashbot.o6.bounded_route_terminal_result_material.v1`, source schema is
`trashbot.o5.bounded_route_terminal_result_bridge.v1`, and the proof boundary is
fixed to `software_proof_o6_o7_bounded_route_terminal_result_intake_only`. The
ready status is `bounded_route_terminal_result_material_ready_not_delivery_proof`;
the relay only stores exact `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`,
`packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`,
`route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`,
route/pose/segment counts, `result_code=mock_route_execution_completed_not_live_delivery`,
`terminal_result_state=terminal_result_recorded`, `reconciliation_state=terminal_result_recorded`,
safe basename refs, blocked reasons, and next evidence. It must keep
`delivery_success=false`, `route_execution_success=false`,
`safe_to_control=false`, `hil_pass=false`, `robot_control_executed=false`, and
`connects_cloud_production=false`. Raw local path, raw command body, URL/token,
`/cmd_vel`, `/api/base/manual`, NavigateToPose, serial/UART, WAVE ROVER, or any
route/delivery/HIL/control true field fails closed to `blocked_not_proven`. This
section is intake/readback only, not delivery proof, not route execution, not
safe-to-control, not production cloud, and not 4G/SIM proof.

O5 now has a local/mock `bounded_route_terminal_result_bridge` CLI for the same
bounded route chain. Its artifact schema is
`trashbot.o5.bounded_route_terminal_result_bridge.v1`, and its proof boundary is
`software_proof_o5_bounded_route_terminal_result_bridge_only`. The bridge
consumes the O3 `trashbot.o3.bounded_route_mock_execution.v1` summary by safe
basename and same-task identity, then uses only the existing relay HTTP routes:
`POST /api/commands/collect`,
`POST /robots/{robot_id}/commands/{command_id}/terminal-result`, and
`GET /api/commands/{command_id}/result?robot_id=...`. The terminal result code
is `mock_route_execution_completed_not_live_delivery`, and the required readback
state is `terminal_result_recorded` through
`cloud_command_result_reconciliation`. The summary must keep
`delivery_success=false`, `route_execution_success=false`,
`safe_to_control=false`, `hil_pass=false`, `robot_control_executed=false`,
`connects_cloud_production=false`, `uses_base_uart=false`,
`publishes_cmd_vel=false`, and `calls_base_manual=false`. This bridge is only
local relay command/result/reconciliation software proof, not production cloud,
not public HTTPS/TLS, not 4G/SIM, not production DB/queue, not OSS/CDN live
traffic, not route execution, not delivery/operator acceptance, not HIL, and not
safe-to-control proof.

O5 also has a `DeliveryStateMachine` offline terminal-result reconciliation for
that bridge output. The generated summary schema is
`trashbot.o5.delivery_state_terminal_reconciliation.v1`; it accepts only source
schema `trashbot.o5.bounded_route_terminal_result_bridge.v1`, proof boundary
`software_proof_o5_bounded_route_terminal_result_bridge_only`, result code
`mock_route_execution_completed_not_live_delivery`, complete same-task identity,
`terminal_result_state=terminal_result_recorded`,
`reconciliation_state=terminal_result_recorded`, and strict false safety fields.
Schema drift, missing identity, dangerous true fields, or unexpected live/success
states fail closed before writing an artifact. A valid mock terminal result is
still reconciled as `final_state=error` with
`terminal_result_accepted_for_delivery=false`, `delivery_success=false`,
`route_execution_success=false`, `safe_to_control=false`, and `hil_pass=false`.
It is a readable state-machine rejection of mock material, not delivery proof,
not dropoff success, not route execution, not operator acceptance, not HIL, not
safe-to-control proof, and not production cloud or 4G/SIM proof.

O5 now also has a `DeliveryStateMachine.delivery_state_live_success_gate`
contract for future true delivery success. Its artifact schema is
`trashbot.o5.delivery_state_live_success_gate.v1`, and its proof boundary is
`software_proof_o5_delivery_state_live_success_gate_only`. The gate accepts
success only when the source mode is real/live, task/robot/packet/route/terminal
result identity stays same-task, live route execution success is recorded,
operator/dropoff acceptance is recorded, HIL passes, `safe_to_control=true` is
backed by live safety evidence, terminal result record exists, and all evidence
is fresh in the same window. The current CLI only writes a
synthetic-current-live-shaped summary with `live_success_gate_contract_ready=true`,
`current_live_evidence_observed=false`,
`delivery_success_claimed_by_this_run=false`,
`real_world_delivery_proven=false`, `safe_to_control=false`, `hil_pass=false`,
and `delivery_success_accepted_for_state_machine=false`. This is a live success
admission contract only, not real delivery proof, not route execution proof, not
operator acceptance, not HIL, not safe-to-control proof, not production cloud,
not true phone/browser proof, and not 4G/SIM proof.

O5 now has an independent `operator_dropoff_acceptance` evidence gate for the
operator/user dropoff action. Its artifact schema is
`trashbot.o5.operator_dropoff_acceptance_gate.v1`, and its proof boundary is
`software_proof_o5_operator_dropoff_acceptance_gate_only`. This gate is a
necessary input for `delivery_state_live_success_gate`, not a sufficient delivery
success decision. Positive acceptance requires `source_mode=live`, same-task
terminal result recorded, live route execution success, same-task
`operator_dropoff_acceptance`, HIL pass, `safe_to_control=true`, and same-window
freshness. Missing evidence, identity mismatch, unsafe evidence refs, stale
evidence, or non-live sources carrying dangerous true values fail closed with
`acceptance_decision=blocked_missing_live_success_evidence`. The current
synthetic CLI artifact keeps `delivery_success=false`,
`route_execution_success=false`, `safe_to_control=false`, `hil_pass=false`, and
`operator_dropoff_acceptance_gate_accepted=false`; it is only an operator
acceptance intake contract, not true phone/browser proof, not production cloud,
not 4G/SIM, not route execution, not HIL, and not real delivery success.

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

The local `operator_gateway` mock cloud now verifies terminal-result-like ACK
fields by value instead of treating any non-empty value as a real result. Values
such as `delivery_result="pending"`, `terminal_result="accepted"`,
`dropoff_completion="processing"`, `cancel_completion="pending"`, and
`delivery_result="unknown"` are
canonicalized to `cloud_terminal_result_verification_guard` with
`degradation_state=terminal_result_pending` and
`evidence_boundary=software_proof_docker_cloud_terminal_result_verification_guard`.
This guard keeps `ack_semantics=accepted_processing_only_not_delivery_success`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`; it does not prove verified delivery result, dropoff or
cancel completion, route/elevator field pass, real phone/browser proof, PR #5
resolution, HIL, or delivery success.

The local Robot/API status and diagnostics surfaces now also expose a command
lifecycle audit/export summary for the same O5 proof boundary:

```text
cloud_command_lifecycle_audit_export
cloud_command_lifecycle_audit_export_summary
robot_diagnostics_cloud_command_lifecycle_audit_export_summary
```

The schema is `trashbot.cloud_command_lifecycle_audit_export_summary.v1` and
the evidence boundary is
`software_proof_docker_cloud_command_lifecycle_audit_export_gate`. The summary
binds one safe `command_id` to one safe `evidence_ref`, lists a phone-safe
`lifecycle_timeline`, reports `terminal_result_status`, provides
`next_required_evidence`, and includes backend-provided `copy_export_text`.
Missing or conflicting lifecycle state remains blocked/not_proven. It keeps
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`; it does not authorize Start/Confirm/Cancel, replay
commands, advance ACK cursors, prove real external cloud/4G/OSS/CDN/DB/queue,
prove a real phone/browser, prove HIL, resolve PR #5, or prove delivery
success.

The same Robot/API surfaces now derive a read-only support replay drill from
that audit/export summary only:

```text
cloud_command_lifecycle_replay_drill
cloud_command_lifecycle_replay_drill_summary
robot_diagnostics_cloud_command_lifecycle_replay_drill_summary
```

The schema is `trashbot.cloud_command_lifecycle_replay_drill_summary.v1` and
the evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_drill_gate`. The drill
preserves the safe `command_id`, safe `evidence_ref`, ordered
`replay_timeline`, `ack_semantics=accepted_processing_only_not_delivery_success`,
`terminal_result_status`, `next_required_evidence`, and sanitized
`support_drill_copy`.

This is a support drill artifact for reproducing the lifecycle explanation. It
does not replay or resubmit commands, post ACKs, mutate cursors or persistence,
trigger Nav2, touch WAVE ROVER, prove HIL, or authorize robot control. It keeps
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`; missing IDs, conflicting refs, unsafe text, raw paths,
credentials, secret URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE
ROVER details, tracebacks, complete artifacts, checksums, success wording, or
any true-state control flags remain blocked/not_proven.

The same Robot/API surfaces now derive a read-only acceptance packet from that
replay drill only:

```text
cloud_command_lifecycle_replay_acceptance_packet
cloud_command_lifecycle_replay_acceptance_packet_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary
```

The schema is
`trashbot.cloud_command_lifecycle_replay_acceptance_packet_summary.v1` and the
evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
The packet preserves the safe `command_id`, safe `evidence_ref`, ordered
`replay_timeline`, `ack_semantics=accepted_processing_only_not_delivery_success`,
`terminal_result_status`, `acceptance_packet_status`, `owner_handoff`,
`next_required_evidence`, and sanitized `support_acceptance_copy`.

This is a support / field-owner acceptance-review packet, not a replay or
review action. It does not replay or resubmit commands, post ACKs, mutate
cursors or persistence, upload materials, perform a GitHub action, trigger
Nav2, touch WAVE ROVER, use UART, prove HIL, prove PR #5 resolution, or
authorize robot control. It keeps `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`; missing safe IDs,
conflicting command/evidence refs, unsafe text, raw paths, credentials, secret
URLs, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
tracebacks, complete artifacts, checksums, ACK payloads, cursors, success copy,
or any true-state control flags remain blocked/not_proven.

The cloud-relay Docker smoke now has a focused
`cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof` section
for that same packet. It reuses the Robot/API acceptance-packet builder inside
the relay container and asserts
`cloud_command_lifecycle_replay_acceptance_packet`,
`cloud_command_lifecycle_replay_acceptance_packet_summary`,
`robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`,
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`,
`accepted_processing_only_not_delivery_success`, `terminal_result_pending`,
`owner_handoff`, `next_required_evidence`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. Its Docker-smoke boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`.
This is still not true phone/browser proof, not real external cloud proof, not
public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue,
not worker/cutover, not verified terminal result, not HIL, not PR #5
resolution, not delivery success, and no OKR percentage lift.

The independent cloud relay CLI can now export that same read-only acceptance
packet as a deterministic JSON artifact for support / field-owner review:

```bash
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay \
  --write-cloud-command-lifecycle-replay-acceptance-packet-cli-export /tmp/trashbot_cli_export.json
```

The export capability is
`cloud_command_lifecycle_replay_acceptance_packet_cli_export`, with evidence
boundary
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`.
It preserves the source packet marker
`cloud_command_lifecycle_replay_acceptance_packet`, the source packet boundary
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`,
`accepted_processing_only_not_delivery_success`, `terminal_result_pending`,
`owner_handoff`, `next_required_evidence`, and `not_proven`.
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false` remain mandatory.

This CLI export is not a user-visible control, not delivery success, not true
phone/browser proof, not real external cloud proof, not public HTTPS/TLS, not
4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover,
not verified terminal result, not HIL, not PR #5 resolution, and no OKR
percentage lift. It does not replay or resubmit commands, post ACKs, mutate
cursors or persistence, upload materials, perform a GitHub action, trigger
Nav2, touch WAVE ROVER, use UART, or authorize robot control.

2026-07-14 `sprints/2026.07.14_14-38_o5_command_lifecycle_cli_export_refresh/`
refreshes that same CLI path as a fresh O5 field-owner review artifact:
`artifacts/o5_command_lifecycle_cli_export.json`. The artifact remains
`cloud_command_lifecycle_replay_acceptance_packet_cli_export`, keeps
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`,
`export_ready_for_field_owner_review_not_proven`,
`accepted_processing_only_not_delivery_success`, `terminal_result_pending`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. O5 remains about `85%`; this refresh is support-only,
does not prove production cloud, true phone/browser, delivery, HIL, route
execution, safe-to-control, or robot control, and the KR remains `不归档`.

The independent relay HTTP server now exposes the same support / field-owner
review metadata through a read-only route:

```text
GET /api/support/cloud-command-lifecycle-replay-acceptance-packet-export
```

The HTTP export capability is
`cloud_command_lifecycle_replay_acceptance_packet_http_export`, with evidence
boundary
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_http_export_gate`.
It is built from the CLI export helper, so it preserves the CLI export boundary
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`,
the source packet boundary
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`,
`pending_same_safe_command_id`, `pending_same_safe_evidence_ref`,
`accepted_processing_only_not_delivery_success`, `terminal_result_pending`,
`owner_handoff`, `next_required_evidence`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`,
`safe_to_control=false`, and `redaction_status=passed`.

This route does not require bearer auth because it is a phone/support-safe GET
surface like `/api/status`. It is read-only: it does not replay or resubmit
commands, post ACKs, mutate cursors or persistence, upload materials, trigger
GitHub action, trigger Nav2, touch WAVE ROVER, use UART, write delivery
success, or enable controls. It is not delivery success, not true phone/browser
proof, not real external cloud proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified
terminal result, not HIL, not PR #5 resolution, and no OKR percentage lift.
The pending safe command/evidence identifiers are explicit placeholders for
the later same-ref owner material; they are not raw command IDs and do not prove
that owner material has arrived.

The same-origin `mobile/web` shell can now consume that HTTP export/support
packet through a read-only phone/support panel:

```text
cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel
cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_summary
```

The mobile panel evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_mobile_export_panel_gate`.
It prefers the Robot diagnostics mobile-export summary, falls back to the
mobile-export summary, the existing acceptance-packet safe summary, or HTTP
export compatible safe fields, and shows only safe command id, safe
`evidence_ref`, acceptance packet status,
`ack_semantics=accepted_processing_only_not_delivery_success`,
`terminal_result_status=terminal_result_pending`, owner handoff, next required
evidence, redaction status, evidence/source boundaries, and backend-provided
safe copy. It keeps `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

The panel is not a new cloud control surface. It does not fetch raw
diagnostics, raw materials, command routes, ACK/cursor routes, review routes,
material routes, GitHub mutation routes, replay/resubmit routes, or any control
path, and it does not enable Start Delivery, Confirm Dropoff, or Cancel. This
is not delivery success, not true phone/browser proof, not public HTTPS/TLS,
not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not
worker/cutover, not verified terminal result, not HIL, not WAVE ROVER/UART
proof, not PR #5 resolution, and no OKR percentage lift.

The same-origin `mobile/web` shell can now turn that mobile export panel into a
read-only support handoff bundle:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_summary
```

The support handoff bundle evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_bundle_gate`.
It preserves `accepted_processing_only_not_delivery_success`,
`terminal_result_pending`, `owner_handoff`, `next_required_evidence`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`,
`safe_to_control=false`, `not true phone/browser proof`, and
`no OKR percentage lift`. Copy/download is allowed only when the backend
provides `safe_copy / support_handoff_copy / sanitized support copy`; missing
or unsafe copy stays `blocked copy unavailable`, and the phone UI does not
synthesize handoff text from raw fields.

The bundle is read-only and redacted. It does not fetch raw diagnostics, raw
materials, command routes, ACK/cursor routes, review routes, material routes,
GitHub mutation routes, replay/resubmit routes, or any control path, and it
does not enable Start Delivery, Confirm Dropoff, or Cancel. It is not delivery
success, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified
terminal result, not HIL, not WAVE ROVER/UART proof, not PR #5 resolution, and
no OKR percentage lift.

Robot/API now exposes a status/diagnostics compatible owner-response-intake
alias for that same support handoff safe bundle:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_summary
```

The alias evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_intake_gate`.
It is derived from the HTTP export safe fields only, so it preserves
`pending_same_safe_command_id`, `pending_same_safe_evidence_ref`,
`safe_copy`, `support_handoff_copy`, `sanitized_support_copy`,
`owner_handoff`, `next_required_evidence`, `redaction_status=passed`,
`accepted_processing_only_not_delivery_success`, `terminal_result_pending`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

This alias is embedded in `/api/status` and `/api/diagnostics` as read-only
metadata for mobile/support compatibility. It does not add a new control route,
ACK/cursor mutation, replay/resubmit behavior, material upload, GitHub
mutation, or robot command route. It remains not verified terminal result, not
HIL, not PR #5 resolved, not delivery success, not true phone/browser proof,
not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production
DB/queue, not worker/cutover, and no OKR percentage lift.

Robot/API now also exposes the downstream owner-response review-decision
summary for that same safe intake:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_summary
```

The review-decision evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision_gate`.
It is derived only from the safe owner-response-intake fields, preserving the
safe command id, safe evidence ref, `review_decision=blocked_not_proven`,
review reasons, owner response status, next required evidence, proof boundary,
source boundary, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Unsupported, unsafe, or missing intake state must stay blocked/not_proven and
must keep `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. The summary does not replay commands, resubmit
commands, mutate ACK cursors, upload materials, fetch raw artifacts, trigger
Nav2, touch WAVE ROVER/UART, authorize robot control, prove PR #5 resolved,
prove delivery success, prove real cloud, provide not verified terminal result,
or provide not true phone/browser proof.

Robot/API additionally exposes the next owner-response review-handoff summary:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_summary
```

The review-handoff evidence boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`.
It is derived only from the safe owner-response review-decision fields. The
summary preserves safe command id, safe evidence ref, `review_decision`,
`handoff_owner`, `handoff_reason`, owner response status, next required
evidence, blocker summary, source boundary, proof boundary, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`.

Unsupported, unsafe, or missing review-decision state must stay blocked or
not_proven. The summary must not expose credentials, bearer tokens, signed URLs,
raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks,
complete artifacts, checksums, success wording, ACK cursor changes, or control
flags. It remains not verified terminal result, not true phone/browser proof,
not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production
DB/queue, not worker/cutover, not HIL, not PR #5 resolved, not route/elevator
field pass, not delivery success, and no OKR percentage lift.

Robot/API now exposes the downstream reviewer ACK intake summary for that same
safe owner-response review handoff:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_summary
```

The reviewer ACK intake proof boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake_gate`.
It is derived only from safe owner-response review-handoff fields. The summary
preserves one safe `command_id`, one safe `evidence_ref`,
`reviewer_ack_status=acknowledged_not_proven`, source handoff status,
owner/support/reviewer routing, ACK reasons, next required evidence, proof
boundary, source boundary, `delivery_success=false`,
`primary_actions_enabled=false`, and `safe_to_control=false`.

Unsupported, unsafe, or missing source handoff state must stay blocked or
not_proven. The summary must not expose credentials, bearer tokens, signed URLs,
raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks,
complete artifacts, checksums, success wording, ACK cursor changes, control
flags, raw ACK payloads, or material uploads. It remains not verified terminal
result, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not
OSS/CDN live traffic, not production DB/queue, not worker/cutover, not HIL, not
PR #5 resolved, not route/elevator field pass, not delivery success, and no OKR
percentage lift.

Robot/API now exposes the downstream reviewer ACK review-decision summary for
that same safe reviewer ACK intake:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_summary
```

The reviewer ACK review-decision proof boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`.
It is derived only from the safe
`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake`
fields. The summary preserves one safe `command_id`, one safe `evidence_ref`,
the source ACK intake status, reviewer ACK review decision, owner/support/reviewer
routing, decision reasons, next required evidence, proof boundary, source
boundary, PR #5 review thread `PRRT_kwDOSWB9286CJ3tX`, and
`pr5_material_status=hardware_material_pending`.

Supported reviewer ACK review decisions are
`reviewer_ack_accepted_for_support_review_not_proven`,
`reviewer_ack_needs_reassignment_not_proven`,
`reviewer_ack_missing_material_not_proven`,
`reviewer_ack_evidence_ref_mismatch_not_proven`,
`reviewer_ack_rejected_unsafe_not_proven`, and
`blocked_missing_reviewer_ack_intake_not_proven`. Every state remains
not_proven and keeps `delivery_success=false`, `primary_actions_enabled=false`,
and `safe_to_control=false`.

Unsupported, unsafe, or missing source ACK intake state must stay blocked or
not_proven. The summary must not expose credentials, bearer tokens, signed URLs,
raw paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks,
complete artifacts, checksums, success wording, ACK cursor changes, reviewer-ACK
mutation, GitHub mutation, or true-state control flags. It remains not verified
terminal result, not true phone/browser proof, not public HTTPS/TLS, not 4G/SIM,
not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not HIL,
not PR #5 resolved, not route/elevator field pass, not delivery success, and no
OKR percentage lift.

Robot/API now exposes the downstream reviewer ACK review-handoff summary for
that same safe reviewer ACK review-decision:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary
```

The reviewer ACK review-handoff schema is
`trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_summary.v1`.
Its proof boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff_gate`.
It is derived only from the safe
`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`
summary and preserves the same safe `command_id` and safe `evidence_ref`.

The summary exposes the source review decision, `review_handoff_status`,
`handoff_owner`, `support_route`, `reviewer_route`, `handoff_reason`,
`decision_reasons`, `next_required_evidence`, `blocker_status`,
`pr_thread_id=PRRT_kwDOSWB9286CJ3tX`,
`hardware_material_pending`, `delivery_success=false`,
`primary_actions_enabled=false`, `safe_to_control=false`,
`terminal_result_verified=false`, `phone_browser_proof=not true phone/browser proof`,
and `okr_progress_effect=no OKR percentage lift`.

Supported reviewer ACK review-handoff states are
`accepted_for_reviewer_ack_review_handoff_not_proven`,
`reviewer_ack_review_handoff_needs_reassignment_not_proven`,
`reviewer_ack_review_handoff_missing_material_not_proven`,
`reviewer_ack_review_handoff_rejected_unsafe_not_proven`,
`blocked_missing_source_reviewer_ack_review_decision_not_proven`, and
`reviewer_ack_review_handoff_evidence_ref_mismatch_not_proven`. Evidence-ref
mismatch must fail closed to
`reviewer_ack_review_handoff_evidence_ref_mismatch_not_proven`.

Unsupported, unsafe, or missing source review-decision state must stay blocked
or not_proven. The summary must not expose credentials, bearer tokens, signed
URLs, local paths, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details,
tracebacks, complete artifacts, checksums, success wording, raw artifacts,
review mutations, GitHub mutations, handoff mutations, or true-state control
flags. It remains not verified terminal result, not true phone/browser proof,
not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production
DB/queue, not worker/cutover, not HIL, not PR #5 resolved, not route/elevator
field pass, not delivery success, and no OKR percentage lift.

Robot/API now exposes the downstream reviewer ACK follow-up escalation status
summary for that same safe reviewer ACK review-handoff:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary
```

The reviewer ACK follow-up escalation status schema is
`trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_summary.v1`.
Its proof boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status_gate`.
It is derived only from the safe
`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_handoff`
summary or equivalent safe diagnostics/status alias. It preserves the same safe
`command_id` and safe `evidence_ref`; mismatches fail closed to
`reviewer_ack_followup_evidence_ref_mismatch_not_proven`.

The summary exposes `source_capability`,
`source_proof_boundary`, `source_review_handoff_status`, `followup_status`,
`due_status`, `followup_owner`, `support_route`, `reviewer_route`,
`escalation_route`, `escalation_reason`, `decision_reasons`,
`next_required_evidence`, `blocker_status`,
`pr_thread_id=PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`,
`delivery_success=false`, `primary_actions_enabled=false`,
`safe_to_control=false`, `terminal_result_verified=false`,
`phone_browser_proof=not true phone/browser proof`, and
`okr_progress_effect=no OKR percentage lift`.

Supported reviewer ACK follow-up escalation statuses are
`reviewer_ack_followup_pending_not_proven`,
`reviewer_ack_followup_overdue_not_proven`,
`reviewer_ack_followup_escalated_not_proven`,
`reviewer_ack_followup_blocked_missing_material_not_proven`,
`ready_for_reviewer_followup_not_proven`,
`blocked_missing_source_reviewer_ack_review_handoff_not_proven`,
`reviewer_ack_followup_evidence_ref_mismatch_not_proven`, and
`reviewer_ack_followup_rejected_unsafe_not_proven`.

Unsupported, unsafe, or missing source review-handoff state must stay blocked
or not_proven. The summary must not expose robot commands, ACK/cursor changes,
material uploads, owner-response submissions, reviewer-ACK submissions, raw
artifact fetches, diagnostics mutations, GitHub mutations, Nav2 triggers, ROS
topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete
artifacts, checksums, verified terminal result wording, success wording, or
true-state control flags. It remains not verified terminal result, not true
phone/browser proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic,
not production DB/queue, not worker/cutover, not HIL, not PR #5 resolved, not
route/elevator field pass, not delivery success, and no OKR percentage lift.

Robot/API now exposes the reviewer ACK owner-response intake bridge. This is a
read-only bridge from reviewer ACK follow-up escalation status back into the
owner-response intake mainline, not a new independent action wrapper:

```text
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge
cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary
robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary
```

The bridge schema is
`trashbot.cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_summary.v1`.
Its proof boundary is
`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_owner_response_intake_bridge_gate`.
It is derived only from the safe
`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_followup_escalation_status`
summary or an equivalent safe status/diagnostics alias. It preserves the same
safe `command_id` and safe `evidence_ref`; command or evidence mismatch fails
closed to
`owner_response_intake_bridge_evidence_ref_mismatch_not_proven`.

The bridge exposes `source_capability`, `source_proof_boundary`,
`source_followup_status`, `bridge_status`,
`owner_response_intake_readiness`, `accepted_materials`,
`missing_materials`, `rejected_materials`, `unsafe_materials`,
`blocked_materials`, `owner_route`, `support_route`, `reviewer_route`,
`next_required_evidence`, `blocker_status`,
`pr_thread_id=PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`,
`delivery_success=false`, `primary_actions_enabled=false`,
`safe_to_control=false`, `terminal_result_verified=false`,
`phone_browser_proof=not true phone/browser proof`, and
`okr_progress_effect=no OKR percentage lift`.

Supported bridge states are
`accepted_for_owner_response_intake_bridge_not_proven`,
`owner_response_intake_bridge_missing_owner_material_not_proven`,
`owner_response_intake_bridge_rejected_unsafe_not_proven`,
`owner_response_intake_bridge_blocked_hardware_material_pending_not_proven`,
`blocked_missing_source_reviewer_ack_followup_escalation_status_not_proven`,
`owner_response_intake_bridge_evidence_ref_mismatch_not_proven`, and
`owner_response_intake_bridge_source_not_ready_not_proven`.

The bridge-to-owner-response-intake semantics are intentionally narrow:
`accepted_for_owner_response_intake_bridge_not_proven` only means the safe
reviewer ACK follow-up summary can be copied into the owner-response intake
review path with the same safe `command_id` and `evidence_ref`. It does not
submit owner response material, read raw reviewer material, resolve PR #5, or
turn any owner-response classification into verified terminal result wording.

Unsupported, unsafe, or missing source follow-up state must stay blocked or
not_proven. The bridge must not expose raw command payloads, Authorization
headers, bearer tokens, signed URLs, local paths, tracebacks, checksums,
complete artifacts, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER
details, true-state flags, verified terminal result wording, success wording,
owner-response submission payloads, or raw reviewer material. It remains not
verified terminal result, not true phone/browser proof, not public HTTPS/TLS,
not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not
worker/cutover, not HIL, not PR #5 resolved, not route/elevator field pass,
not delivery success, and no OKR percentage lift.

Robot/API also exposes the PR #5 mandatory-sensor owner-response review handoff
as a phone-safe status/diagnostics alias when the backend has already provided
the sanitized summary:

```text
pr5_mandatory_sensor_material_owner_response_review_handoff
pr5_mandatory_sensor_material_owner_response_review_handoff_summary
robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary
```

The alias evidence boundary is
`software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate`.
It preserves `source=software_proof`, `hardware_material_pending`,
`not_proven`, `safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing, unsupported, or unsafe backend
summaries fail closed to a blocked summary; the relay does not synthesize a
handoff from raw artifacts, raw diagnostics, local paths, credentials,
checksums, serial/UART details, ACK/cursor mutation, review-thread update,
`/cmd_vel`, or other control endpoints.

This handoff alias is embedded in `/api/status`, `/api/diagnostics`, and
`phone_readiness` for read-only mobile/support compatibility. It does not prove
real LiDAR/ToF material, WAVE ROVER/UART/HIL, PR #5 resolution, O5 external
proof, route/elevator field pass, delivery result, or delivery success, and it
does not enable Start Delivery, Confirm Dropoff, Cancel, ACK, cursor,
review-thread update, or robot command side effects.

Robot/API also exposes the PR #5 mandatory-sensor owner-response reviewer ACK
intake as a phone-safe status/diagnostics alias when the backend has already
provided the sanitized summary:

```text
pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary
robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary
```

The alias evidence boundary is
`software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`.
It preserves `source=software_proof`, `hardware_material_pending`,
`not_proven`, `safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. The safe summary is intentionally narrow:
capability, proof boundary, PR thread `PRRT_kwDOSWB9286CJ3tX`,
`hardware_material_pending`, reviewer ACK/intake status, next required
evidence, safe copy, and false flags.

This reviewer ACK intake alias is embedded in `/api/status`, `/api/diagnostics`,
and `phone_readiness` for read-only mobile/support compatibility. It does not
expose raw artifacts, serial/UART details, credentials, `/cmd_vel`, ROS control
topics, GitHub write/resolve actions, ACK/cursor mutation, or robot command side
effects. Missing, unsupported, or unsafe summaries fail closed and do not enable
Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, review-thread update,
Nav2, HIL, dropoff/cancel completion, delivery result, or primary robot actions.

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
`evidence_boundary=software_proof_docker_cloud_hosted_mobile_web_gate`. When a
backend sanitized PR #5 review-handoff summary is present, both endpoints expose
the `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_review_handoff_summary`
alias with the same fail-closed action boundaries.

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
remote response, command ID conflict, command sequence regression,
cloud poll backoff, missing/invalid/stale manifest summary, and manual
takeover.
Diagnostics remains available with a phone-safe blocking explanation so support
can still reproduce the issue. ACK text must stay conservative: an ACK is only
command accepted/processing evidence and does not prove delivery success, real
4G/cloud, OSS/CDN traffic, WAVE ROVER motion, or HIL.

## Cloud Unreachable Malformed Response Guard

`cloud_unreachable_malformed_response_guard` covers two remote-control degraded
states that must stay phone-safe and fail closed: `cloud_unreachable` and
`malformed_response`. Both states use the same evidence boundary,
`software_proof_docker_cloud_unreachable_malformed_response_guard`, and must
preserve `source=software_proof`, `not_proven`, `remote_ready=false`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.

When `cloud_unreachable` is active, the phone copy is:

```text
云端暂时不可达；当前不能下发主操作，请刷新状态或联系支持。
```

When `malformed_response` is active, the phone copy is:

```text
云端响应格式异常；机器人没有确认执行，请刷新状态或联系支持。
```

The phone UI must keep Start Delivery, Confirm Dropoff, and Cancel disabled for
both states. Diagnostics and Support Handoff remain visible so an operator can
collect a sanitized support summary, but the phone must not add control
endpoints, ACK/cursor requests, retries, resubmits, raw diagnostics fetches, or
hidden robot commands. Payloads and UI text must not expose raw JSON,
credentials, bearer tokens, Authorization headers, DB/queue URLs, OSS AK/SK,
tracebacks, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details,
local paths, checksums, or complete artifacts.

## Cloud Poll Backoff Rate Limit Guard

`cloud_poll_backoff_rate_limit_guard` covers the Robot-side state where outbound
polling has hit repeated poll failure or consecutive empty-poll pressure and is
waiting for a bounded retry window. The canonical degraded state is
`cloud_poll_backoff` with evidence boundary
`software_proof_docker_cloud_poll_backoff_rate_limit_guard`.

The Robot status and diagnostics surface only safe fields:

- `degradation_state=cloud_poll_backoff`
- `remote_ready=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=wait_for_backoff_window`
- `proof_boundary=software_proof_docker_cloud_poll_backoff_rate_limit_guard`
- optional redacted `backoff_until` / `backoff_duration_sec`

The state must not override more specific O5 failures. `auth_failed`,
`media_degraded`, `cloud_unreachable`, `malformed_response`,
`command_expired`, `command_pending`, `command_duplicate_deduped`,
`command_id_conflict`, and `command_sequence_regression` keep their own
recovery paths and proof boundaries.

This guard is Docker/local software proof only. It is not real public
HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not
true phone/browser proof, not HIL, not route/elevator field pass, not delivery
success, and not PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution. Payloads
must not expose raw base URLs, tokens, Authorization headers, local state paths,
tracebacks, `/cmd_vel`, ROS topics, serial devices, WAVE ROVER details, or
`delivery_success=true`.

This guard is Docker/local software proof only. It does not prove public
HTTPS/TLS, real 4G/SIM, production DB/queue, OSS/CDN live traffic, true
phone/browser behavior, WAVE ROVER/UART, HIL, route/elevator field pass,
dropoff/cancel completion, delivery result, or delivery success.

## Cloud Cancel Pending Command Safety Guard

`cloud_cancel_pending_command_safety_guard` covers the Robot/API state where a
cloud `cancel` arrives while the collect goal is still pending acceptance. The
canonical degraded state is `cancel_pending_goal_acceptance`, not a generic
`busy`/`failed` state and not a cancel completion.

When this guard is active, status/readiness must include:

- `capability=cloud_cancel_pending_command_safety_guard`
- `degradation_state=cancel_pending_goal_acceptance`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=wait_for_goal_acceptance`
- `ack_semantics=cancel_pending_not_delivery_success`
- `safe_phone_copy=取消请求已收到，但收集任务仍在等待目标接受；请等待目标接受后再重试取消，若持续阻塞请联系支持。这不是送达成功。`
- `proof_boundary=software_proof_docker_cloud_cancel_pending_command_safety_guard`

`build_phone_readiness` and `trashbot.command_safety.v1` must block Start
Delivery, Confirm Dropoff, and Cancel for `cancel_pending_goal_acceptance`.
Diagnostics and Support Handoff remain visible with sanitized copy only. The
state must not expose raw JSON, credentials, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, tracebacks, or `delivery_success=true`.

This guard is Docker/local software proof only. It does not prove real goal
acceptance, cancel completion, public HTTPS/TLS, real 4G/SIM, production
DB/queue, OSS/CDN live traffic, true phone/browser behavior, WAVE ROVER/UART,
HIL, route/elevator field pass, delivery result, or delivery success.

## Cloud Manual Takeover Command Safety Guard

`cloud_manual_takeover_command_safety_guard` covers the Robot/API state where a
manual takeover or human-help outcome is required. It turns `needs_human_help`,
`failed`, or `degradation_state=manual_takeover_required` into one canonical
safe degraded state instead of leaving phones to infer support actions from raw
Robot messages.

When this guard is active, status/readiness must include:

- `capability=cloud_manual_takeover_command_safety_guard`
- `degradation_state=manual_takeover_required`
- `manual_takeover_required=true`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=contact_support`
- `ack_semantics=manual_takeover_not_delivery_success`
- `safe_phone_copy=需要人工接管；远程主操作已暂停，请按现场/支持指引处理。这不是送达成功。`
- `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`

`build_phone_readiness` and `trashbot.command_safety.v1` must block Start
Delivery, Confirm Dropoff, and Cancel for `manual_takeover_required`.
Diagnostics, Support Handoff, voice prompt readiness, and offline/resume
summaries remain available, but they must be redacted and must not expose raw
tokens, Authorization headers, ROS topics, `/cmd_vel`, serial/UART details,
WAVE ROVER details, local paths, tracebacks, or `delivery_success=true`.

This guard is Docker/local software proof only. It is not real external cloud
proof, true phone/browser proof, HIL, WAVE ROVER/UART proof,
route/elevator field pass, delivery result, or delivery success.

## Command Idempotency Visibility Guard

The Robot bridge treats `command.id` as the idempotency key. If the cloud sends
the same unexpired command id again after the robot already has a terminal ACK
cached in memory, the bridge must reuse that cached ACK and must not submit a
second local action. The operator status still has to become visible and
phone-safe, because an `acked` cached envelope is not delivery success.

When this guard is active, status/readiness must include:

- `degradation_state=command_duplicate_deduped`
- `remote_ready=false`
- `duplicate_command_id=<safe command id or [redacted]>`
- `cached_ack_state=<acked|failed|ignored>`
- `ack_semantics=duplicate_cached_ack_not_delivery_success`
- `primary_actions_enabled=false`
- `safe_phone_copy=重复云指令已去重，机器人没有重复执行；cached ACK 不是送达成功。`
- `retry_hint=refresh_status`
- `proof_boundary=software_proof_docker_cloud_command_idempotency_visibility_guard`

Priority order matters. A persisted pending terminal ACK still blocks command
pulling before the bridge can observe another command, and expired commands must
continue to report `command_expired` rather than being hidden by duplicate
visibility. `build_phone_readiness` and `trashbot.command_safety.v1` must block
Start Delivery, Confirm Dropoff, and Cancel for
`command_duplicate_deduped`; Diagnostics remains available so support can inspect
the safe command id, cached ACK state, ACK semantics, and proof boundary. This is
only `software_proof_docker_cloud_command_idempotency_visibility_guard`; it does
not prove production DB/queue behavior, public HTTPS/TLS, real 4G/SIM,
OSS/CDN live traffic, real phone browser, Nav2 or fixed route delivery,
WAVE ROVER motion, HIL, or delivery success.

## Command ID Conflict Visibility Guard

The Robot bridge now compares duplicate command identity with a canonical
`type/payload` rule instead of raw JSON text. The canonical comparison sorts
payload keys before comparing, so the same command content with a different JSON
field order remains a normal duplicate and follows the cached ACK dedupe path.
`expires_at`, `created_at`, and queue metadata are not part of command identity.

If the same `command.id` appears again with a different `type` or canonical
`payload`, the bridge must fail closed: do not call the operator backend, do not
reuse the cached ACK, and do not write the cached ACK as the current command
result. The rejected command may be ACKed as `ignored` only with a phone-safe
operator status that explains the conflict.

When this guard is active, status/readiness must include:

- `degradation_state=command_id_conflict`
- `remote_ready=false`
- `conflict_command_id=<safe command id or [redacted]>`
- `conflict_reason=duplicate_id_mismatched_type_or_payload`
- `conflict_fields=<type|payload|type,payload>`
- `ack_semantics=conflict_rejected_not_delivery_success`
- `primary_actions_enabled=false`
- `safe_phone_copy=命令 ID 冲突：同一 ID 的 type/payload 不一致，机器人已拒绝执行；这不是送达成功。`
- `retry_hint=contact_support`
- `proof_boundary=software_proof_docker_cloud_command_id_conflict_visibility_guard`

Priority order is explicit: persisted pending terminal ACK blocks new command
pulling first; expired commands still report `command_expired`; same-ID
different-content commands report `command_id_conflict`; only same-ID same
canonical `type/payload` commands report `command_duplicate_deduped`. Phone
readiness, command safety, and diagnostics must keep Start Delivery, Confirm
Dropoff, and Cancel disabled for `command_id_conflict`, while Diagnostics
remains available for support. This is only
`software_proof_docker_cloud_command_id_conflict_visibility_guard`; it does not
prove delivery success, production DB/queue behavior, public HTTPS/TLS, real
4G/SIM, OSS/CDN live traffic, real phone browser, Nav2 or fixed route delivery,
WAVE ROVER motion, or HIL.

## Command Sequence Regression Guard

The Robot bridge may receive an optional top-level `queue_sequence` on a cloud
command. This is safe metadata only: when it is missing, the bridge keeps the
existing opaque `last_ack_id` cursor behavior and does not infer ordering from
the command id string. When it is present, the bridge records the highest
terminal `queue_sequence` only after the terminal ACK POST is accepted by the
cloud. A local pending ACK, malformed cloud response, or failed ACK POST must
not advance the highest terminal sequence.

If a later different `command.id` carries a `queue_sequence` lower than or equal
to the highest terminal sequence already accepted by the cloud, the bridge must
fail closed before calling the operator backend. The command may be ACKed as
`ignored`, but the ACK/readiness status must say this is a sequence regression,
not delivery success.

When this guard is active, status/readiness must include:

- `degradation_state=command_sequence_regression`
- `remote_ready=false`
- `sequence_regression_command_id=<safe command id or [redacted]>`
- `queue_sequence=<incoming sequence>`
- `highest_terminal_queue_sequence=<highest accepted terminal sequence>`
- `ack_semantics=sequence_regression_not_delivery_success`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `safe_phone_copy=云端指令序号回退，机器人已拒绝执行；这不是送达成功或真实队列排序证明。`
- `retry_hint=contact_support`
- `proof_boundary=software_proof_docker_cloud_command_sequence_regression_guard`

Priority order is conservative: pending terminal ACK replay still blocks all new
command polling, expired commands still report `command_expired`, same-ID
conflicts still report `command_id_conflict`, and same-ID same-content repeats
still report `command_duplicate_deduped`. The sequence regression guard applies
to later different command ids before any backend action is executed. Phone
readiness and `trashbot.command_safety.v1` must disable Start Delivery, Confirm
Dropoff, and Cancel for `command_sequence_regression`; Diagnostics remains
available for support. This is only
`software_proof_docker_cloud_command_sequence_regression_guard`; it does not
prove real production queue ordering, production DB/queue behavior,
multi-instance consistency, public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic,
real phone browser, Nav2 or fixed route delivery, WAVE ROVER motion, HIL, or
delivery success.

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

## Cloud Status Stale Guard

The Robot/mock HTTP gateway exposes `cloud_status_stale_guard` when the last
robot status is missing, unknown, or older than the local freshness window. This
guard is read-only and fail-closed: it does not submit behavior actions, does
not infer delivery state from a previous status payload, and does not let stale
`delivery_success` or `primary_actions_enabled` fields keep phone controls
enabled.

When this guard is active, Robot status, HTTP `remote_readiness`, diagnostics,
and phone command-safety summaries must include:

- `degradation_state=status_stale`
- `remote_ready=false`
- `status_stale=true`
- `retry_hint=wait_for_robot_status`
- `ack_semantics=stale_status_not_delivery_success`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `proof_boundary=software_proof_docker_cloud_status_stale_guard`

This boundary is only `software_proof_docker_cloud_status_stale_guard`. It does
not prove public HTTPS/TLS, real 4G/SIM, production DB/queue freshness, real
phone/browser validation, Nav2 or fixed-route delivery, WAVE ROVER motion, HIL,
or delivery success.

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
| `degradation_state` | Phone-safe degradation state such as `ok`, `status_stale`, `command_pending`, `command_expired`, `command_duplicate_deduped`, `command_id_conflict`, `command_sequence_regression`, `auth_failed`, `media_degraded`, `cloud_poll_backoff`, `ack_lookup_pending`, `ack_accepted_result_pending`, `terminal_result_pending`, `cancel_pending_goal_acceptance`, `manual_takeover_required`, `cloud_unreachable`, or `malformed_response`. |
| `media_state` | Present only for `media_degraded`; values are `oss_write_failed` or `cdn_unavailable`. |
| `retry_hint` | Operator/phone action hint such as `ok`, `wait_for_robot_status`, `wait_for_command_ack`, `resubmit_command`, `refresh_status`, `check_auth`, `check_oss_write`, `check_cdn_reachability`, `wait_for_backoff_window`, `continue_polling_or_contact_support`, `wait_for_delivery_result_or_contact_support`, `wait_for_verified_terminal_result_or_contact_support`, `wait_for_goal_acceptance`, `retry_cloud`, or `contact_support`. |
| `safe_phone_copy` | Plain-language UI copy that must not include raw JSON, ROS topic names, secrets, serial devices, or hardware parameters. |
| `ack_semantics` | Explicit non-delivery wording for degraded ACK/status states; `stale_status_not_delivery_success` means stale robot status is not delivery success. |
| `primary_actions_enabled` | `false` for fail-closed degraded states, including `auth_failed`, so Start/Confirm/Cancel remain disabled. |
| `proof_boundary` | The exact software-proof boundary string for the degraded state, never a claim of real cloud, phone, HIL, or delivery proof. |

`auth_state=authorized` means the local/mock request passed the configured bearer
gate. `degradation_state=ok` means the control-plane contract is healthy enough
for the next software step. Neither value proves the robot delivered trash,
reached a Nav2/fixed-route target, moved the WAVE ROVER base, or passed HIL.

## Cloud Auth Failure Status Guard

The robot bridge and local/mock HTTP gateway expose
`cloud_auth_failure_status_guard` when the remote control path fails auth. This
state is intentionally fail-closed: it does not parse cloud commands, does not
advance the cursor, does not submit behavior actions, and does not turn a 401
or credential mismatch into delivery success.

When this guard is active, Robot status, HTTP `remote_readiness`, diagnostics,
and phone command-safety summaries must include:

- `degradation_state=auth_failed`
- `auth_state=auth_failed`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `retry_hint=check_auth`
- `ack_semantics=auth_failed_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_auth_failure_status_guard`

The safe output must not expose Authorization headers, Bearer values, tokens,
raw credential URLs, tracebacks, local paths, ROS topic names, `/cmd_vel`,
serial/UART details, or WAVE ROVER details. Diagnostics remains available for
support, but Start Delivery, Confirm Dropoff, and Cancel stay disabled. This is
Docker/local software proof only; it is not public HTTPS/TLS, 4G/SIM, OSS/CDN
live traffic, production DB/queue, real phone/browser validation, WAVE ROVER
motion, HIL, or delivery success.

## Cloud Media Degradation Status Guard

The robot bridge and local/mock HTTP gateway expose
`cloud_media_degradation_status_guard` when media evidence cannot be persisted
to OSS or fetched through CDN. This guard is intentionally read-only and
fail-closed: it does not create replay, resubmit, ACK success, cursor movement,
diagnostics fetch side effects, ROS commands, hardware interaction, or any
control endpoint.

All media degradation statuses must include:

- `degradation_state=media_degraded`
- `remote_ready=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `proof_boundary=software_proof_docker_cloud_media_degradation_status_guard`

For OSS write failure, the status must include:

- `media_state=oss_write_failed`
- `retry_hint=check_oss_write`
- `ack_semantics=media_not_persisted_not_delivery_success`

For CDN unavailable, the status must include:

- `media_state=cdn_unavailable`
- `retry_hint=check_cdn_reachability`
- `ack_semantics=media_not_fetchable_not_delivery_success`

Diagnostics and phone readiness must stay redacted. They must not expose
Authorization headers, bearer tokens, OSS AK/SK, signed URLs, bucket secrets,
tracebacks, local absolute paths, ROS topic names, `/cmd_vel`, serial/UART
details, or WAVE ROVER details. Start Delivery, Confirm Dropoff, and Cancel
stay disabled; Diagnostics remains available with the same
`software_proof_docker_cloud_media_degradation_status_guard` boundary. This is
Docker/local software proof only, not real OSS write, real CDN fetch,
OSS/CDN live traffic, public HTTPS/TLS, 4G/SIM, production DB/queue, real
phone/browser validation, WAVE ROVER motion, HIL, or delivery success.

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
`ack_not_found` error plus canonical `remote_readiness` so the UI can keep
polling or show that the robot has not processed the command yet.

Missing ACK lookup must render as the O5 software-proof state
`cloud_ack_lookup_pending_status_guard`:

- `capability=cloud_ack_lookup_pending_status_guard`
- `degradation_state=ack_lookup_pending`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=continue_polling_or_contact_support`
- `ack_semantics=ack_lookup_pending_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_ack_lookup_pending_status_guard`
- Phone-safe copy: `机器人尚未处理该命令，请继续等待或联系支持。`

This pending lookup state is read-only. It must not enqueue, replay, cancel,
confirm dropoff, advance an ACK cursor, infer delivery outcome, or expose raw
tokens, paths, ROS topics, serial details, tracebacks, or success wording.

Accepted/processing ACK without a real terminal result must render as the O5
software-proof state `cloud_ack_accepted_result_pending_guard`:

- `capability=cloud_ack_accepted_result_pending_guard`
- `degradation_state=ack_accepted_result_pending`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=wait_for_delivery_result_or_contact_support`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_ack_accepted_result_pending_guard`
- Phone-safe copy: command ACK has accepted/processing evidence only, and no
  real delivery, dropoff completion, or cancel completion exists yet.

This state is read-only. It must not enqueue, replay, cancel, confirm dropoff,
advance an ACK cursor, infer delivery outcome, or expose raw tokens, paths,
ROS topics, serial details, tracebacks, terminal-result wording, or success
wording.

ACK payloads with terminal-result-like fields that still carry non-terminal
values must render as the stricter O5 software-proof state
`cloud_terminal_result_verification_guard`:

- `capability=cloud_terminal_result_verification_guard`
- `degradation_state=terminal_result_pending`
- `remote_ready=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `retry_hint=wait_for_verified_terminal_result_or_contact_support`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `proof_boundary=software_proof_docker_cloud_terminal_result_verification_guard`

Values such as `delivery_result=pending`, `delivery_result=unknown`,
`terminal_result=accepted`, `dropoff_completion=processing`, or
`cancel_completion=pending` are not
verified delivery results. This state must not enable Start, Confirm Dropoff,
Cancel, ACK cursor changes, route/elevator field pass, PR #5 resolution, HIL,
dropoff completion, cancel completion, or delivery success.

Verified terminal-result material intake has a separate Robot diagnostics
safe alias:

- `robot_diagnostics_verified_terminal_result_material_intake_summary`
- `schema=trashbot.verified_terminal_result_material_intake_summary.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_intake_gate`
- `status=not_proven`
- `source=software_proof`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that a sanitized terminal-result material summary can be
read by Robot diagnostics. It can consume the canonical intake/summary, the
Robot alias, or compatible nested diagnostics/status summary, but it must strip
or block raw artifact fields, ACK/cursor mutation hints, replay/resubmit hints,
robot-control hints, credentials, paths, checksums, ROS topics, serial/UART
details, and success wording. It must not enable Start Delivery, Confirm
Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, robot
control, route/elevator field pass, HIL, dropoff completion, cancel completion,
or delivery success.

Verified terminal-result material review decision has a follow-on Robot
diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_review_decision_summary`
- `schema=trashbot.verified_terminal_result_material_review_decision_summary.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_decision_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that Robot diagnostics can surface a sanitized
review-decision summary. `accepted_for_review` is owner-review readiness, not
delivery success. It can consume the canonical review decision artifact,
canonical summary, Robot alias, or compatible nested diagnostics/status
summary, but it strips or blocks raw artifact fields, ACK/cursor mutation
hints, replay/resubmit hints, robot-control hints, credentials, paths,
checksums, ROS topics, serial/UART details, WAVE ROVER details, and success
wording. It must not enable Start Delivery, Confirm Dropoff, Cancel, ACK
mutation, cursor mutation, replay, resubmit, robot control, route/elevator
field pass, HIL, dropoff completion, cancel completion, or delivery success.

Verified terminal-result material review handoff adds the next Robot
diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_review_handoff_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_review_handoff_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_review_handoff.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that Robot diagnostics can surface a sanitized owner
handoff summary for verified terminal delivery/dropoff/cancel result materials.
It can consume the canonical handoff artifact, canonical handoff summary,
Robot alias, or compatible nested diagnostics/status summary. Handoff statuses
such as `ready_for_owner_handoff`, `needs_material_backfill`, `rejected`, and
`blocked` are read-only support states, not delivery success and not route,
dropoff, cancel, ACK, or control authorization.

Unsafe raw fields, raw diagnostics fetch fields, ACK/cursor mutation hints,
replay/resubmit hints, robot-control hints, credentials, paths, checksums, ROS
topics, serial/UART details, WAVE ROVER details, hardware raw details, and
success/control claims must fail closed. This alias must not enable Start
Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay,
resubmit, raw diagnostics fetch, robot control, route/elevator field pass, HIL,
dropoff completion, cancel completion, terminal delivery result, or delivery
success.

Verified terminal-result material follow-up escalation status adds the next
Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_followup_escalation_status_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_followup_escalation_status.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that Robot diagnostics can surface a sanitized terminal
result material follow-up escalation summary for field owner, support owner,
and reviewer routing. It can consume the canonical follow-up summary, Robot
alias, or compatible nested diagnostics/status summary; a raw artifact wrapper
is valid only when it contains the sanitized summary and the Robot output strips
raw sibling keys before exposing the safe alias.

Follow-up statuses such as
`escalated_for_terminal_result_material_followup_not_proven`,
`waiting_for_terminal_result_material_backfill_not_proven`,
`needs_support_owner_reassignment_not_proven`,
`rejected_unsafe_terminal_result_followup_not_proven`, and
`blocked_missing_terminal_result_review_handoff_not_proven` are read-only
support/material-routing states. They are not reviewer resolution, route
completion, dropoff completion, cancel completion, ACK/cursor mutation,
replay/resubmit authorization, HIL pass, terminal delivery result, or delivery
success.

Unsafe raw source fields, raw artifacts, complete JSON, credentials, paths,
checksums, ROS topics, serial/UART details, WAVE ROVER details, hardware raw
details, ACK/cursor mutation hints, replay/resubmit hints, reviewer-resolution
claims, and success/completion/control claims must fail closed. This alias must
not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor
mutation, replay, resubmit, raw diagnostics fetch, robot control, route/elevator
field pass, HIL, dropoff completion, cancel completion, terminal delivery
result, reviewer resolution, or delivery success.

Verified terminal-result material owner-response intake adds the next Robot
diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_intake_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_intake.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that Robot diagnostics can surface a sanitized owner
response intake summary for later terminal-result material review. Even when
owner response material is `accepted_for_later_review_not_proven`, the state is
only a queueing/review hint; it does not enable collect, dropoff, cancel,
ACK/cursor mutation, replay/resubmit, command control, or delivery success.

PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved /
`hardware_material_pending`; this Robot alias must keep
`pr5_PRRT_kwDOSWB9286CJ3tX_unresolved` in the not-proven boundary and must not
claim OKR percentage lift. Unsafe raw source fields, raw artifacts, complete
JSON, credentials, paths, checksums, ROS topics, serial/UART details, WAVE ROVER
details, hardware raw details, ACK/cursor mutation hints, collect/dropoff/cancel
hints, reviewer-resolution or PR-resolution claims, and
success/completion/control claims must fail closed.

Verified terminal-result material owner-response review decision adds the next
Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_review_decision.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The alias only proves that Robot diagnostics can surface a sanitized
owner-response review decision for the next handoff. Even when the review
decision is `accepted_for_next_handoff_not_proven`, the state remains a
handoff/readiness hint only; it does not enable collect, dropoff, cancel,
ACK/cursor mutation, replay/resubmit, command control, HIL, route/elevator
field pass, terminal delivery result, or delivery success.

Unsafe raw source fields, raw artifacts, complete JSON, credentials, paths,
checksums, ROS topics, serial/UART details, WAVE ROVER details, hardware raw
details, ACK/cursor mutation hints, collect/dropoff/cancel hints,
handoff-authorization claims, and success/completion/control claims must fail
closed.

Verified terminal-result material owner-response review handoff adds the next
Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_review_handoff.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved
- `hardware_material_pending=true`

The alias is read-only and can be derived from the sanitized
`verified_terminal_result_material_owner_response_review_decision` safe summary.
It preserves the upstream review decision status, safe `evidence_ref`, safe
`command_id`, owner/support/reviewer routing, next required evidence, and safe
copy. It is only a handoff packet for owner-response review follow-through; it
does not prove a real terminal result, O5 external proof, true phone/browser
proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue,
worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, PR #5
resolution, or delivery success.

Unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, tracebacks, complete artifacts,
checksums, success wording, true control flags, PR-resolution claims,
handoff-authorization claims, ACK/cursor mutation hints, and
collect/dropoff/cancel hints must fail closed.

Verified terminal-result material owner-response reviewer ACK intake adds the
next Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_intake_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_intake.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_intake_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved
- `hardware_material_pending=true`

The alias is read-only and consumes the sanitized reviewer ACK intake summary
first, then the compatible Robot-safe alias. It can fall back to a blocked state
derived from the sanitized owner-response review handoff summary. It preserves
source handoff status, safe `evidence_ref`, safe `command_id`, reviewer ACK
status, owner/support/reviewer routing, next required evidence, and safe copy.
It is only a reviewer ACK intake packet for unresolved material follow-through;
it does not prove PR #5 resolution, reviewer resolution, real terminal result,
O5 external proof, true phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN
live traffic, production DB/queue, worker/cutover, route/elevator field pass,
HIL, WAVE ROVER/UART proof, or delivery success.

Verified terminal-result material owner-response reviewer ACK review decision
adds the next Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_decision.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_decision_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved
- `hardware_material_pending=true`

The alias is read-only and consumes the sanitized reviewer ACK review-decision
summary first, then the compatible Robot-safe alias. It can fall back to a
blocked state derived from the sanitized reviewer ACK intake summary. It
preserves source reviewer ACK intake status, review decision, safe
`evidence_ref`, safe `command_id`, missing/rejected materials, reassignment
reason, next required evidence, owner/support/reviewer routing, and safe copy.
It is only a reviewer ACK review-decision packet for unresolved material
follow-through; it does not prove PR #5 resolution, reviewer resolution, real
terminal result, O5 external proof, true phone/browser proof, public
HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover,
route/elevator field pass, HIL, WAVE ROVER/UART proof, review authorization,
or delivery success.

Unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, tracebacks, complete artifacts,
checksums, success wording, HIL wording, true control flags, PR-resolution
claims, reviewer-resolution claims, review-authorization claims, ACK/cursor
mutation hints, and collect/dropoff/cancel hints must fail closed.

Verified terminal-result material owner-response reviewer ACK review handoff
adds the next Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_review_handoff.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_review_handoff_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved
- `hardware_material_pending=true`

The alias is read-only and consumes the sanitized reviewer ACK review-handoff
summary first, then the compatible Robot-safe alias. It can fall back to a
blocked state derived from the sanitized reviewer ACK review-decision summary.
It preserves source reviewer ACK review-decision status, handoff status, safe
`evidence_ref`, safe `command_id`, missing/rejected materials, reassignment
reason, handoff reasons, next required evidence, owner/support/reviewer
routing, and safe copy. It is only a reviewer ACK review-handoff packet for
unresolved material follow-through; it does not prove PR #5 resolution,
reviewer resolution, real terminal result, O5 external proof, true
phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production
DB/queue, worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART
proof, review authorization, handoff authorization, or delivery success.

Unsafe raw fields, credentials, local paths, ROS topics, `/cmd_vel`,
serial/UART details, WAVE ROVER details, tracebacks, complete artifacts,
checksums, success wording, HIL/pass wording, true phone/browser proof, true
control flags, PR-resolution claims, reviewer-resolution claims,
review-authorization claims, handoff-authorization claims, ACK/cursor mutation
hints, and collect/dropoff/cancel hints must fail closed. This diagnostics
alias does not change command safety, ACK/cursor, cloud bridge, task execution,
or control semantics.

Verified terminal-result material owner-response reviewer ACK follow-up
escalation status adds the next Robot diagnostics safe alias:

- `robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary`
- `schema=trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1`
- `source_schema=trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1`
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved
- `hardware_material_pending=true`
- `overdue` / `escalated` states are follow-up metadata only

The alias is read-only and consumes only the sanitized PC follow-up summary or
compatible Robot-safe alias. It can fall back to a blocked state derived from
the sanitized reviewer ACK review-handoff summary. It preserves source reviewer
ACK review-handoff status, due/overdue/escalated state, owner/support/reviewer
route, escalation reason, blocked reason, next required evidence, and safe
copy. It is only a software-proof escalation-status packet for unresolved
material follow-through; it does not prove PR #5 resolution, reviewer
resolution, real terminal result, O5 external proof, true phone/browser proof,
public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue,
worker/cutover, route/elevator field pass, HIL, WAVE ROVER/UART proof, review
authorization, handoff authorization, OKR percentage lift, or delivery success.

Unsafe raw artifacts, credentials, local paths, raw robot responses, ROS topics,
`/cmd_vel`, serial/UART details, ACK payloads, cursor values, diagnostics fetch
mutation hints, robot command hints, success wording, HIL/pass wording, field
pass wording, true control flags, PR-resolution claims, reviewer-resolution
claims, review-authorization claims, handoff-authorization claims, and
collect/dropoff/cancel hints must fail closed. This diagnostics alias does not
change command safety, ACK/cursor, cloud bridge, task execution, or control
semantics.

Field evidence rerun acceptance handoff owner-response reviewer ACK bridge adds
the next Robot diagnostics safe alias on the existing owner-response intake
surface:

- `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_intake_summary`
- `capability=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge`
- `source_bridge=field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`
- `evidence_boundary=software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_owner_response_intake_bridge_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

The bridge exposes only sanitized source follow-up status, the same safe
`evidence_ref`, owner route, reviewer/support route, next required field-owner
materials, false-state flags, and safe copy. It is not task record proof,
dropoff completion, cancel completion, Nav2 route completion, elevator proof,
phone/browser proof, HIL, or robot-control permission.

Raw artifacts, credentials, local paths, raw robot responses, ROS topics,
`/cmd_vel`, serial/UART details, ACK/cursor payloads, diagnostics fetch
mutation hints, GitHub mutation hints, robot command hints, and success/control
claims must fail closed.
Start Delivery, Confirm Dropoff, or Cancel semantics.

## Safety Rules

- The robot never exposes `/cmd_vel` over the remote bridge.
- The bridge calls only behavior-level ROS contracts.
- `command.id` is an idempotency key; duplicate IDs reuse the cached ack and
  expose `command_duplicate_deduped` with
  `ack_semantics=duplicate_cached_ack_not_delivery_success`.
- Optional `queue_sequence` is a fail-closed regression hint only; it is not
  proof of real production queue ordering.
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

## Cloud External Evidence Review Decision

`cloud_external_evidence_review_decision` is the read-only phone/support panel for the O5 external evidence review step after `trashbot.external_evidence_intake`. The executable local gate is `pc-tools/evidence/cloud_external_evidence_review_decision.py`, with artifact schema `trashbot.cloud_external_evidence_review_decision.v1` and summary schema `trashbot.cloud_external_evidence_review_decision_summary.v1`. The phone consumes only `robot_diagnostics_cloud_external_evidence_review_decision_summary` or the same safe summary fallback from status/readiness/diagnostics; it must not fetch raw diagnostics, raw artifacts, raw materials, response bodies, ACK/cursor routes, upload routes, review mutation routes, GitHub mutation routes, replay/resubmit routes, or robot control paths. The panel shows safe command/evidence refs, material-family statuses, review decision, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX` with `hardware_material_pending`, proof boundary, and false-state flags.

Supported review states are `accepted_external_evidence_not_proven`, `needs_external_evidence_backfill_not_proven`, `rejected_unsafe_external_evidence_not_proven`, `blocked_missing_external_evidence_intake_not_proven`, and `external_evidence_ref_mismatch_not_proven`. The evidence boundary is `software_proof_docker_cloud_external_evidence_review_decision_gate`; the source capability remains `trashbot.external_evidence_intake`. Preflight and the O5 cutover readiness packet consume the artifact through `TRASHBOT_REMOTE_CLOUD_EXTERNAL_EVIDENCE_REVIEW_DECISION_ARTIFACT` or `--cloud-external-evidence-review-decision-artifact`, but this only adds a support-safe `cloud_external_evidence_review_decision` source slot. Start Delivery、Confirm Dropoff、Cancel 继续 disabled, and every surface must keep `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`. This is not O5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified terminal result, not HIL, not PR #5 resolution, and not delivery success.

## Cloud External Evidence Review Handoff

`cloud_external_evidence_review_handoff` is the next read-only phone/support panel after `cloud_external_evidence_review_decision`. The phone consumes only `robot_diagnostics_cloud_external_evidence_review_handoff_summary` or the same safe summary fallback from status/readiness/diagnostics; it must not fetch raw diagnostics, raw artifacts, raw materials, response bodies, ACK/cursor routes, upload routes, handoff routes, review mutation routes, GitHub mutation routes, replay/resubmit routes, or robot control paths. The panel shows source decision, handoff status, safe command/evidence refs, owner/support/reviewer route, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX` with `hardware_material_pending`, proof boundary, and false-state flags.

Supported handoff states are `ready_for_owner_support_reviewer_handoff_not_proven`, `needs_external_evidence_backfill_handoff_not_proven`, `rejected_unsafe_external_evidence_handoff_not_proven`, `blocked_missing_external_evidence_handoff_not_proven`, and `external_evidence_ref_mismatch_handoff_not_proven`. The evidence boundary is `software_proof_docker_cloud_external_evidence_review_handoff_gate`; the source capability remains `cloud_external_evidence_review_decision`. Start Delivery、Confirm Dropoff、Cancel 继续 disabled, and every surface must keep `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`. This is not O5 external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified terminal result, not HIL, not PR #5 resolution, and not delivery success.

`cloud_external_evidence_review_handoff_followup_escalation_status` is the read-only phone/support panel after `cloud_external_evidence_review_handoff`. The phone consumes only `robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary` or the same safe summary fallback from status/readiness/diagnostics; it must not fetch raw diagnostics, raw artifacts, raw materials, response bodies, ACK/cursor routes, upload routes, handoff routes, review mutation routes, GitHub mutation routes, replay/resubmit routes, or robot control paths. The panel shows source handoff status, due status, blocked reason, owner action, support action, reviewer action, CEO escalation recommendation, next required evidence, PR #5 `PRRT_kwDOSWB9286CJ3tX` with `hardware_material_pending`, proof boundary, and false-state flags.

Supported follow-up states are `pending_followup_not_proven`, `due_followup_not_proven`, `overdue_followup_not_proven`, `escalated_hardware_material_pending_not_proven`, and `blocked_missing_external_evidence_review_handoff_not_proven`. The evidence boundary is `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`; the source capability remains `cloud_external_evidence_review_handoff`. Start Delivery、Confirm Dropoff、Cancel 继续 disabled, and every surface must keep `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`. This is Docker/local `software_proof`, not true phone/browser proof, not external proof, not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not verified terminal result, not HIL, not PR #5 resolution, not route/elevator field pass, and not delivery success.
