# ROS Contracts

## Hardware: `esp32_bridge`

Vendor sources:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

### Parameters

| Name | Type | Default | Contract |
| --- | --- | --- | --- |
| `serial_port` | string | `/dev/ttyUSB0` | Canonical UART device parameter. Confirm the Orange Pi device on hardware. |
| `serial_baudrate` | int | `115200` | Canonical UART baudrate parameter. Vendor examples use `115200`. |
| `port` | string | empty | Deprecated alias for `serial_port`. |
| `baudrate` | int | `0` | Deprecated alias for `serial_baudrate`; ignored when `0`. |
| `command_mode` | string | `speed` | `speed` maps `/cmd_vel` to vendor `T=1`; `ros` maps to vendor `T=13`. |
| `track_width_m` | double | `0.172` | Differential-drive width used by `speed` mode. Must be positive. Current default is project tuning and requires HIL confirmation before production use. |
| `max_wheel_speed_mps` | double | `1.3` | Normalization limit for project-side `T=1` left/right values. Must be positive. Vendor WAVE ROVER materials describe `-0.5` to `0.5` as the user-facing speed range, so the current scaling/clamp remains HIL-pending. |
| `feedback_interval_ms` | int | `100` | Sent to vendor `T=142`. Must be non-negative. |
| `odom_publish_hz` | double | `20.0` | ROS-side `/odom` publish rate. Must be positive. |

### Consumed Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | In `speed` mode, `linear.x` and `angular.z` are converted to normalized `T=1` `L`/`R`; positive `angular.z` makes left lower and right higher. In `ros` mode, the bridge sends `T=13` `X`/`Z`. |

### Produced Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/odom` | `nav_msgs/msg/Odometry` | Command-integrated odometry from last accepted `/cmd_vel`; not encoder-validated or fused localization. |
| `/imu/data` | `sensor_msgs/msg/Imu` | Yaw-only orientation derived from vendor `T=1001` field `y`. |
| `/battery` | `sensor_msgs/msg/BatteryState` | Voltage-only battery state from vendor `T=1001` field `v`. |

### Services

| Service | Type | Contract |
| --- | --- | --- |
| `/trashbot/stop` | `std_srvs/srv/Trigger` | Sends vendor `T=1` stop with `L=0`, `R=0`. |
| `/trashbot/reset_odom` | `std_srvs/srv/Trigger` | Resets ROS-side command-integrated odometry only; no ESP32 reset command is sent. |
| `/trashbot/beep` | `std_srvs/srv/Trigger` | Currently returns unsupported because the WAVE ROVER base JSON contract does not define a beep command. |

### UART Startup Contract

On startup the bridge sends:

1. `{"T":143,"cmd":0}` to disable UART echo.
2. `{"T":142,"cmd":feedback_interval_ms}` to set feedback interval.
3. `{"T":131,"cmd":1}` to enable streamed base feedback.

The ESP32 feedback frame used by this contract is vendor `T=1001` with at least `L`, `R`, `r`, `p`, `y`, and `v`.

## Behavior: `collect_trash`

### Action Server

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/collect_trash` | `ros2_trashbot_interfaces/action/TrashCollection` | Default product entry point is `task_orchestrator`; the legacy standalone server is installed as `legacy_trash_collection_server` only for compatibility and aborts goals with `legacy_server_quarantined` instead of reporting demo success. |

### Feedback Fields

| Field | Contract |
| --- | --- |
| `status` | Compatibility numeric status: `0` idle/failure, `1` navigating, `3` delivering/dropoff, `4` done. |
| `percent_complete` | Compatibility progress percentage from `0` to `100`. |
| `current_step` | Compatibility readable step name. During elevator assisted delivery dry-run and rehearsal-artifact playback, `task_orchestrator` publishes phone-safe `elevator:<phase>` values such as `elevator:waiting_elevator_open`, `elevator:requesting_floor_help`, and `elevator:resume_delivery` before the task record is written. |
| `state` | Delivery state machine state, such as `loaded`, `delivering`, `dropoff`, `returning`, `idle`, or `error`. |
| `event` | Latest state machine event, including `invalid_transition` for rejected public transitions. |
| `message` | Human-readable progress or failure detail. |
| `elapsed_sec` | Elapsed action time in seconds. |

### Delivery Parameters

| Parameter | Values | Contract |
| --- | --- | --- |
| `delivery_mode` | `dry_run`, `waypoint`, `fixed_route` | `dry_run` succeeds without Nav2. `waypoint` resolves `delivery_target`/goal frame in `waypoint_file` and uses Nav2. `fixed_route` only reads `fixed_route_status_file`; it does not control UART or hardware directly. |
| `navigation_timeout_sec` | float seconds | Maximum duration for a waypoint or fixed-route attempt. |
| `navigation_retry_limit` | integer | Additional retry attempts after the first navigation attempt. |
| `dropoff_mode` | `dry_run`, `manual_confirm` | `dry_run` confirms immediately. `manual_confirm` waits through `dropoff_timeout_sec` unless canceled. |
| `dropoff_timeout_sec` | float seconds | Manual dropoff confirmation window. |
| `return_target` | waypoint name or empty | Optional return waypoint. Empty means no return navigation. |
| `elevator_assist_enabled` | boolean, default `true` | Enables the elevator assisted delivery dry-run subflow by default as `software_proof_docker_elevator_assist_default_mainline_gate`. Setting it to `false` must produce `reason=disabled_by_operator`, recovery guidance, `delivery_success=false`, and `primary_actions_enabled=false`; it does not block a non-cross-floor dry-run task. |
| `elevator_assist_mode` | `dry_run` | Default and only software-only elevator assisted delivery mode. It records waiting for elevator open, entering, requesting floor help, waiting target floor, exiting, and resume-delivery phases without claiming a real elevator, real speaker/TTS, real Nav2/fixed-route, or HIL. |
| `elevator_assist_target_floor` | string | Target floor copied into elevator assisted delivery task records and prompt context. |
| `elevator_assist_dry_run_failure` | empty, `door_timeout`, `target_floor_unconfirmed`, `unsafe_to_exit` | Optional software proof failure injection. Failure records must include phase, failure reason, manual takeover reason, and not-proven boundary metadata. |
| `elevator_assist_evidence_file` | JSON file path or empty | Optional only when `elevator_assist_mode=dry_run`. Missing or empty files keep the default dry-run fallback. Non-empty files must use `schema=trashbot.elevator_assist_rehearsal_evidence.v1`, `evidence_boundary=software_proof_docker_elevator_evidence_driven_mainline_gate`, `source=software_proof`, safe `evidence_ref` matching `[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}`, JSON boolean `same_evidence_ref_required=true`, `delivery_success=false`, and `primary_actions_enabled=false`; invalid artifacts fail closed through `elevator_failed` and require manual takeover. |

### Task Record Evidence Boundary

`task_record.json` is a software evidence record for the behavior state machine.
For fixed-route rehearsal, `task_record.evidence_ref`,
`task_record.route_progress.evidence_ref`, and
`task_record.nav_results[-1].evidence.route_progress.evidence_ref` must resolve
to the same run-level anchor when that anchor exists. If older fixed-route
status payloads expose progress fields at the evidence top level, behavior
normalizes those fields into `route_progress` without changing the ROS2
action/topic/service contract.

The route/task rehearsal artifact gate
`software_proof_docker_route_task_rehearsal_artifact_gate` may consume
`route_progress`, `nav_results[-1].evidence.route_progress`, and
`evidence_ref` for local/Docker cross-checks. A `final_status=success` task
record only means the configured behavior state machine finished under its
current mode, such as `dry_run` or software fixed-route status rehearsal. It is
not delivery success, not real Nav2/fixed-route execution, not WAVE ROVER
motion, and not HIL evidence.

Elevator assisted delivery is now part of the default behavior dry-run mainline:
`elevator_assist_enabled=true` with `elevator_assist_mode=dry_run`. The
`task_record.elevator_assist` payload is metadata only and must include
`proof_gate=software_proof_docker_elevator_assist_default_mainline_gate`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`,
`safe_phone_copy`, and rerun guidance. A successful elevator dry-run only means
the state chain was recorded in local/Docker software proof; it is not real
elevator operation, not real speaker/TTS playback, not real Nav2/fixed-route
execution, not HIL, and 不证明真实电梯、真实喇叭、真实 Nav2、HIL 或送达成功.
If disabled by operator config, the payload must report
`reason=disabled_by_operator` and keep the same boundary fields while allowing a
non-cross-floor dry-run task to continue.

When `elevator_assist_evidence_file` points to a non-empty rehearsal artifact,
`task_orchestrator` consumes it only in `elevator_assist_mode=dry_run`. The
artifact drives the `elevator_phase` sequence for `waiting_elevator_open`,
`entering_elevator`, `requesting_floor_help`, `waiting_target_floor`, and
`exiting_elevator`, then the task record promotes the artifact `evidence_ref`
to top-level `task_record.evidence_ref` and `task_record.result_path`. Optional
artifact `failure.phase/reason/manual_takeover_reason` fails closed through
`elevator_failed`, sets `human_intervention_required=true`, and preserves
`delivery_success=false` plus `primary_actions_enabled=false`. This is the
`software_proof_docker_elevator_evidence_driven_mainline_gate`; it is not real
elevator operation, not real Nav2/fixed-route execution, not WAVE ROVER motion,
not HIL, and not delivery success.

The same dry-run and rehearsal-artifact paths also publish live
`TrashCollection.Feedback` updates for each elevator subphase. Feedback uses the
existing action fields only: `current_step=elevator:<phase>`, `state=delivering`,
`event=elevator_phase` for in-progress subphases or `event=elevator_completed`
for `elevator:resume_delivery`, non-success `status=3`, and
`percent_complete` bounded to the 30-55% delivery window. Feedback messages must
stay phone-safe and must not expose local artifact paths, serial/UART details,
ROS topic names, raw evidence payloads, or success/control claims. This feedback
does not change `/trashbot/collect_trash` result semantics and must keep
`delivery_success=false` plus `primary_actions_enabled=false` under both
`software_proof_docker_elevator_assist_default_mainline_gate` and
`software_proof_docker_elevator_evidence_driven_mainline_gate`.

Operator diagnostics may additionally expose `route_task_rehearsal` from a
configured route/task rehearsal artifact. The diagnostics summary uses
`evidence_boundary=software_proof_docker_route_task_rehearsal_diagnostics_gate`
and is read-only support metadata. It may include sanitized `evidence_ref`,
source schema/boundary, crosscheck pass/fail status, HIL alignment status, and
`not_proven`, but it must not expose local paths, credentials, serial details,
raw traceback, DB/queue URLs, or complete artifacts. A `crosscheck_status=pass`
in this summary is not delivery success, not a ROS action/topic/service, not
ACK/cursor/terminal ACK, not real Nav2/fixed-route execution, and not HIL; when
HIL is missing, blocked, or software-only, `hil_alignment_status` remains
`not_proven`.

Operator diagnostics may also expose `route_task_rehearsal_execution_bundle`
from an explicit bundle ref or `TRASHBOT_ROUTE_TASK_REHEARSAL_BUNDLE`. The
manifest must use `schema=trashbot.route_task_rehearsal_execution_bundle` and
`evidence_boundary=software_proof_docker_route_task_rehearsal_execution_bundle_gate`.
This field is metadata-only support material for the Docker/local execution
bundle: it may include sanitized `evidence_ref`, artifact ref, crosscheck
status, HIL alignment status, `not_proven`, safe phone copy, and next step. It
must keep `primary_actions_enabled=false`, must not POST ACKs, must not advance
cursor state, and must not enable Start Delivery, Confirm Dropoff, or Cancel.
Missing, unreadable, unsupported, or crosscheck-fail manifests remain blocked
or read_error summaries. A bundle pass is not delivery success, not a ROS
action/topic/service, not real Nav2/fixed-route execution, not dropoff/cancel
completion, not WAVE ROVER motion, and not HIL.

Operator diagnostics may also expose
`route_task_rehearsal_operator_review` from an explicit
`route_task_rehearsal_operator_review_ref` or
`TRASHBOT_ROUTE_TASK_REHEARSAL_OPERATOR_REVIEW`. The review package must use
`schema=trashbot.route_task_rehearsal_operator_review.v1` and
`evidence_boundary=software_proof_docker_route_task_rehearsal_operator_review_gate`.
This summary is phone/support-safe metadata only: it may expose sanitized
`overall_status`, `state`, `evidence_ref`, crosscheck status, HIL alignment
status, `mismatch_summary`, `next_rehearsal_decision`, `not_proven`,
`safe_copy`, and boundary fields. Missing, unreadable, unsupported-schema,
crosscheck-fail, or unsafe-copy packages must remain blocked/degraded and
must not enable Start Delivery, Confirm Dropoff, Cancel, ACK POST,
cursor/persistence updates, HIL pass, dropoff/cancel completion, or delivery
success. It does not change the command/status/ACK envelope or the
collect/dropoff/cancel behavior.

Operator diagnostics may also expose `pc_route_debug_console` from an explicit
`pc_route_debug_console_ref` or `TRASHBOT_PC_ROUTE_DEBUG_CONSOLE`. The source
JSON must use `schema=trashbot.pc_route_debug_console.v1` and
`evidence_boundary=software_proof_docker_pc_route_debug_console_gate`. This
summary is metadata-only support material for the PC route debug console: it may
include sanitized availability, route debug status, route progress,
keyframe_preflight, recent task summary, `not_proven`, and safe support copy.
It may also retain a sanitized nested `route_elevator_reconciliation` summary
for the PC console route/elevator view. That nested summary has its own
`evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`,
but the parent `pc_route_debug_console.evidence_boundary` remains
`software_proof_docker_pc_route_debug_console_gate`. The nested summary may
only expose availability, reconciliation status, elevator assist status, route
completion status, operator next steps, `not_proven`, safe copy, and explicit
fail-closed flags: `delivery_success=false`, `primary_actions_enabled=false`,
remote/terminal ACK disabled, cursor/persistence disabled, `nav2_triggered=false`,
`hil_pass=false`, and dropoff/cancel completion false.
Missing, unreadable, unsupported-schema, blocked, or unsafe-copy sources remain
blocked/not_proven. This field is not a command/status/ACK envelope field, not a
ROS action/topic/service, not Nav2 execution, not Start/Confirm/Cancel
enablement, not ACK POST, not cursor/persistence or terminal ACK, not real
fixed-route evidence, not HIL, and not delivery success.

Operator diagnostics may also expose `route_task_field_run_readiness` and the
alias `route_task_field_run_readiness_summary` from an explicit
`route_task_field_run_readiness_ref` or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_READINESS`. The source JSON must use
`schema=trashbot.route_task_field_run_readiness.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`.
This summary is metadata-only support material for the next route-task field
run handoff: it may include sanitized availability / overall status,
`evidence_ref`, `same_evidence_ref_required`, missing or required next evidence
materials, commands summary, `not_proven`, and safe support copy. Missing,
unreadable, unsupported-schema, boundary-mismatch, or unsafe-field sources
remain blocked/not_proven. The fields must keep `delivery_success=false` and
`primary_actions_enabled=false`; they do not trigger `/api/collect`, dropoff,
cancel, ACK POST, cursor/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, or
delivery success. They are not command/status/ACK robot contract fields and do
not prove real fixed-route execution, real HIL, delivery success, or Objective 5
external proof.

Operator diagnostics may also expose `route_task_field_run_intake` and the
alias `route_task_field_run_intake_summary` from an explicit
`route_task_field_run_intake_ref` or `TRASHBOT_ROUTE_TASK_FIELD_RUN_INTAKE`.
The source JSON must use
`schema=trashbot.route_task_field_run_intake_crosscheck.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_intake_crosscheck_gate`.
This summary is metadata-only support material for the route-task field-run
material intake/crosscheck gate: it may include sanitized availability /
overall status, `evidence_ref`, `same_evidence_ref_required`,
`missing_materials`, `mismatch_reasons`, `commands_to_rerun`, `not_proven`, and
safe support copy. Raw route-status, task-record, runtime-log,
robot-side-task-evidence, mobile-summary, credentials, local paths, UART/serial
details, raw ACK payloads, raw command envelopes, and traceback content must not
enter mobile copy or the diagnostics summary. Missing, unreadable,
unsupported-schema, boundary-mismatch, evidence mismatch, or unsafe-summary
sources remain blocked/not_proven. The fields must keep
`delivery_success=false` and `primary_actions_enabled=false`; they do not
trigger `/api/collect`, dropoff, cancel, ACK POST, cursor advance/persistence,
terminal ACK, Nav2, WAVE ROVER, HIL, dropoff/cancel completion, or delivery
success. They are not command/status/ACK robot contract fields and do not prove
real fixed-route execution, real HIL, delivery success, or Objective 5 external
proof.

Operator diagnostics may also expose `route_task_field_run_review` and the
alias `route_task_field_run_review_summary` from an explicit
`route_task_field_run_review_ref`, `TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE`,
or `TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW`. The source JSON must use
`schema=trashbot.route_task_field_run_review_console.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_review_console_gate`.
This summary is metadata-only support material for the route-task field-run
operator review console: it may include sanitized availability / overall
status, review decision, `evidence_ref`, `same_evidence_ref_required`,
`missing_materials`, `mismatch_reasons`, `commands_to_rerun`,
`operator_next_steps`, `not_proven`, and safe support copy. Raw review logs,
credentials, local paths, UART/serial details, raw ACK payloads, raw command
envelopes, production-readiness claims, and traceback content must not enter
mobile copy or the diagnostics summary. Missing, unreadable,
unsupported-schema, blocked/mismatch, or unsafe-summary sources remain
blocked/not_proven. The fields must keep `metadata_only=true`,
`delivery_success=false`, `primary_actions_enabled=false`,
`collect_triggered=false`, `dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `cursor_updates_allowed=false`,
`terminal_ack_allowed=false`, `hil_pass=false`, `production_ready=false`,
`dropoff_completion=false`, and `cancel_completion=false`; they do not trigger
`/api/collect`, dropoff, cancel, ACK POST, cursor advance/persistence, terminal
ACK, Nav2, WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or
delivery success. They are not command/status/ACK robot contract fields and do
not prove real fixed-route execution, real HIL, delivery success, or Objective
5 external proof.

Operator diagnostics may also expose `route_task_field_run_execution_pack` and
the alias `route_task_field_run_execution_pack_summary` from an explicit
`route_task_field_run_execution_pack_ref` or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_EXECUTION_PACK`. The source JSON must use
`schema=trashbot.route_task_field_run_execution_pack.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_execution_pack_gate`.
This summary is metadata-only support material for a route-task field-run
execution pack: it may expose sanitized status, safe evidence ref,
`same_evidence_ref_required`, materials status, command summary, `not_proven`,
safe copy, and evidence-boundary fields only. Raw route logs, task records,
mobile summary payloads, credentials, local paths, UART/serial details, raw ACK
payloads, raw command envelopes, production-readiness claims, and traceback
content must not enter the diagnostics summary. Missing, unreadable,
unsupported-schema, boundary-mismatch, or unsafe-summary sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, dropoff/cancel completion, or delivery success. They are
not command/status/ACK robot contract fields and do not prove real fixed-route
execution, real HIL, production readiness, dropoff/cancel completion, or
delivery success.

Operator diagnostics may also expose `route_task_field_retest_execution_pack`
and the alias `route_task_field_retest_execution_pack_summary` from an
explicit `route_task_field_retest_execution_pack_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_EXECUTION_PACK_SUMMARY`, top-level
`phone_readiness`, top-level status fields, or an already sanitized nested
`diagnostics.summary` / `diagnostics.diagnostics_summary` source. The source
JSON must use `schema=trashbot.route_task_field_retest_execution_pack.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_execution_pack_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_execution_pack.v1` and the same
evidence boundary. This summary is metadata-only support material for the next
route-task field retest execution pack: it may expose only summary schema,
execution status, safe `evidence_ref`, `same_evidence_ref_required`, required
field materials summary, rerun commands summary, operator handoff, field retest
checklist, boundary,
`software_proof_docker_route_task_field_retest_execution_pack_gate`,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
Missing, unreadable, unsupported-schema, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain blocked/not_proven. The fields do
not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, production readiness,
dropoff/cancel completion, or delivery success. They are not command/status/ACK
robot contract fields and do not prove real fixed-route execution, real HIL,
real phone/browser proof, production readiness, Objective 5 external proof, or
delivery success.

Operator diagnostics may also expose `route_task_field_retest_session_handoff`
and the alias `route_task_field_retest_session_handoff_summary` from an
explicit `route_task_field_retest_session_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_SESSION_HANDOFF_SUMMARY`, top-level status
fields, or an already sanitized nested `diagnostics.summary` /
`diagnostics.diagnostics_summary` source. The source JSON must use
`schema=trashbot.route_task_field_retest_session_handoff.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_session_handoff_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_session_handoff.v1` and the
same evidence boundary. This summary is metadata-only support material for
handing the next route-task field retest session to operators: it may expose
only summary schema, handoff status, safe `evidence_ref`,
`same_evidence_ref_required=true`, session owner, required field materials
summary, redacted material placeholders summary, rerun commands summary,
operator next steps, field callback checklist, Robot diagnostics summary,
mobile-readonly copy, boundary,
`software_proof_docker_route_task_field_retest_session_handoff_gate`,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
Missing, unreadable, unsupported-schema, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, weak or non-boolean
`same_evidence_ref_required`, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain blocked/not_proven. The fields
do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, production
readiness, dropoff/cancel completion, or delivery success. They must not expose
raw route logs, raw ROS topics, `/cmd_vel`, serial/UART details, credentials,
local paths, checksums, tracebacks, complete artifacts, or Objective 5 external
proof, and they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose `route_task_field_retest_result_intake`
and the alias `route_task_field_retest_result_intake_summary` from an explicit
`route_task_field_retest_result_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_INTAKE_SUMMARY`, top-level status
fields, or an already sanitized nested `diagnostics.summary` /
`diagnostics.diagnostics_summary` source. The source JSON must use
`schema=trashbot.route_task_field_retest_result_intake.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_intake_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_result_intake.v1` and the same
evidence boundary. This summary is metadata-only support material for retest
result intake after the route-task field session: it may expose only summary
schema, result status, safe `evidence_ref`, `same_evidence_ref_required=true`,
phone-safe `door_state`, `target_floor_confirmation`, `human_assistance_note`,
result materials summary, operator next steps, Robot diagnostics summary,
mobile-readonly copy, boundary,
`software_proof_docker_route_task_field_retest_result_intake_gate`,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
Missing, unreadable, unsupported-schema, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, weak or non-boolean
`same_evidence_ref_required`, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain blocked/not_proven. The fields
do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, production
readiness, dropoff/cancel completion, or delivery success. They must not expose
raw route logs, raw ROS topics, `/cmd_vel`, serial/UART details, credentials,
local paths, checksums, tracebacks, complete artifacts, or Objective 5 external
proof, and they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_reconciliation` and the alias
`route_task_field_retest_result_reconciliation_summary` from an explicit
`route_task_field_retest_result_reconciliation_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_RECONCILIATION_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_reconciliation.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_reconciliation_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_result_reconciliation.v1` and
the same evidence boundary. This summary is metadata-only support material for
reconciling the Task A retest result intake with same-`evidence_ref` field
materials: it may expose only summary schema, reconciliation status, safe
`evidence_ref`, `same_evidence_ref_required=true`, result intake summary,
result reconciliation summary, safe lineage metadata (`source_result_intake`,
`source_review_result_handoff`, and the fixed
`review_result_handoff -> result_intake -> result_reconciliation` chain),
operator next steps, Robot diagnostics summary, mobile-readonly copy, boundary,
`software_proof_docker_route_task_field_retest_result_reconciliation_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing, unreadable, unsupported-schema,
unsafe copy, missing `evidence_ref`, same-`evidence_ref` mismatch, weak or
non-boolean `same_evidence_ref_required`, missing/unsupported lineage schema,
lineage `evidence_ref` mismatch, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, dropoff/cancel completion, or delivery success. They
must not expose raw route logs, raw ROS topics, `/cmd_vel`, serial/UART
details, credentials, local paths, checksums, tracebacks, complete artifacts,
or Objective 5 external proof, and they are not command/status/ACK robot
contract fields.

Operator diagnostics may also expose `route_task_field_retest_material_pack`
the alias `route_task_field_retest_material_pack_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_material_pack_summary` from an
explicit `route_task_field_retest_material_pack_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_PACK_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_material_pack.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_pack_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_material_pack.v1` and the same
evidence boundary. This field is metadata-only Robot diagnostics support for
the route-task field retest material pack: it may expose only summary schema,
material status, safe `evidence_ref`, `same_evidence_ref_required=true`,
material completeness, missing/rejected material names, operator next steps,
Robot diagnostics summary, mobile-readonly copy, boundary,
`software_proof_docker_route_task_field_retest_material_pack_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, same-`evidence_ref`
mismatch, weak or non-boolean `same_evidence_ref_required`, success wording,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw route logs, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not command/status/ACK
robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_material_callback_packet`, the alias
`route_task_field_retest_material_callback_packet_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_material_callback_packet_summary`
from an explicit `route_task_field_retest_material_callback_packet_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_PACKET_SUMMARY`, top-level
status fields, a wrapper field, or an already sanitized nested diagnostics
summary source. The source JSON must use
`schema=trashbot.route_task_field_retest_material_callback_packet.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_material_callback_packet.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for the route-task field retest material callback packet: it may expose
only summary schema, packet status, safe `evidence_ref`,
`same_evidence_ref_required=true`, accepted/missing/rejected material names,
owner follow-up, review-decision handoff, Robot diagnostics summary,
mobile-readonly copy, boundary,
`software_proof_docker_route_task_field_retest_material_callback_packet_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe raw fields, unsafe copy, missing
`evidence_ref`, same-`evidence_ref` mismatch, weak or non-boolean
`same_evidence_ref_required`, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed and remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
field pass, production readiness, Start enablement, Confirm enablement, Cancel
enablement, dropoff/cancel completion, or delivery success. They must not
expose raw material files, raw route logs, raw artifacts, raw commands, raw ROS
topics, `/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are not
command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_material_callback_review_decision`, the alias
`route_task_field_retest_material_callback_review_decision_summary`, and the
Robot alias
`robot_diagnostics_route_task_field_retest_material_callback_review_decision_summary`
from an explicit `route_task_field_retest_material_callback_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_MATERIAL_CALLBACK_REVIEW_DECISION_SUMMARY`,
top-level status fields, a wrapper field, or an already sanitized nested
diagnostics summary source. The source JSON must use
`schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`
or
`schema=trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for the route-task field retest material callback review decision: it
may expose only summary schema, review decision, safe `evidence_ref`,
`same_evidence_ref_required=true`, material callback review summary,
accepted/missing/rejected material names, owner acknowledgement, owner next
steps, next required evidence, rerun command labels, Robot diagnostics summary,
boundary,
`software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe raw fields, unsafe copy, missing
`evidence_ref`, same-`evidence_ref` mismatch, weak or non-boolean
`same_evidence_ref_required`, success wording, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed and remain
blocked/not_proven. Expected decision values include
`ready_for_controlled_field_rerun_not_proven`,
`needs_material_callback_backfill_not_proven`,
`evidence_ref_mismatch_rerun_not_proven`,
`blocked_material_callback_review_not_proven`,
`unsupported_material_callback_packet_schema_not_proven`, and
`unsafe_success_claim_rejected_not_proven`. The fields do not trigger
`/api/collect`, dropoff, cancel, Start Delivery, Confirm Dropoff, Cancel
Delivery, remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE
ROVER, HIL, field pass, production readiness, dropoff/cancel completion, or
delivery success. They must not expose raw material files, raw route logs, raw
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose `route_task_field_retest_operator_drill`,
the alias `route_task_field_retest_operator_drill_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_operator_drill_summary` from an explicit
`route_task_field_retest_operator_drill_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_OPERATOR_DRILL_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_operator_drill.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_operator_drill_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_operator_drill.v1` and the same
evidence boundary. This field is metadata-only Robot diagnostics support for
the route-task field retest operator drill: it may expose only summary schema,
safe summary, safe `evidence_ref`, `same_evidence_ref_required=true`, drill
status, next command labels, missing material prompts, operator callback
checklist, Robot diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_operator_drill_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, same-`evidence_ref`
mismatch, weak or non-boolean `same_evidence_ref_required`, success wording,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw route logs, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, review-decision-derived raw command/artifact
fields, Start/Confirm/Cancel enablement, field-pass wording, or Objective 5
external proof, and they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose `route_task_field_retest_drill_console`
and the alias `route_task_field_retest_drill_console_summary` from an explicit
`route_task_field_retest_drill_console_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_DRILL_CONSOLE_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_drill_console.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_drill_console_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_drill_console.v1` and the same
evidence boundary. This field is metadata-only Robot diagnostics support for
the route-task field retest drill console: it may expose only summary schema,
safe summary, safe `evidence_ref`, `same_evidence_ref_required=true`, console
status, command labels, safe checklist, missing material prompts, operator
callback checklist, Robot-compatible diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_drill_console_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, same-`evidence_ref`
mismatch, weak or non-boolean `same_evidence_ref_required`, success phrasing,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw route logs, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_brief` and the alias
`route_task_field_retest_acceptance_brief_summary` from an explicit
`route_task_field_retest_acceptance_brief_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_BRIEF_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_acceptance_brief.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_brief_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_acceptance_brief.v1` and the
same evidence boundary. This field is metadata-only Robot diagnostics support
for the route-task field retest acceptance brief: it may expose only summary
schema, safe summary, safe `evidence_ref`, `same_evidence_ref_required=true`,
acceptance status, pass/fail criteria, required evidence packet, owner handoff,
Robot-compatible diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_acceptance_brief_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, same-`evidence_ref`
mismatch, weak or non-boolean `same_evidence_ref_required`, success phrasing,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw route logs, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_evidence_dispatch` and the alias
`route_task_field_retest_evidence_dispatch_summary` from an explicit
`route_task_field_retest_evidence_dispatch_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_EVIDENCE_DISPATCH_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_evidence_dispatch.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_evidence_dispatch_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_evidence_dispatch.v1` and the
same evidence boundary. This field is metadata-only Robot diagnostics support
for the route-task field retest evidence dispatch: it may expose only summary
schema, safe summary, safe `evidence_ref`, dispatch status, material owners,
recommended filenames, backfill order, callback checklist, fail-closed rerun
notes, Robot-compatible diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_evidence_dispatch_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, success phrasing,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw route logs, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_review_decision`, the alias
`route_task_field_retest_acceptance_review_decision_summary`, and the Robot
alias
`robot_diagnostics_route_task_field_retest_acceptance_review_decision_summary`
from an explicit `route_task_field_retest_acceptance_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_REVIEW_DECISION_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_review_decision.v1` or
`schema=trashbot.route_task_field_retest_acceptance_review_decision_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's
acceptance review decision summary: it may expose only decision status, source
acceptance brief status, review decision, material backfill status, safe
`evidence_ref`, missing materials, owner handoff, next required evidence, rerun
commands, `same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, weak or
false `same_evidence_ref_required`, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, Start
Delivery, Confirm Dropoff, Cancel, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, material backfill
completion, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw material files, raw route logs, raw
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_pack`, the alias
`route_task_field_retest_acceptance_execution_pack_summary`, and the Robot
alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_pack_summary`
from an explicit `route_task_field_retest_acceptance_execution_pack_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_PACK_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_pack.v1` or
`schema=trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's
acceptance execution pack summary: it may expose only execution pack status,
review decision source, owner checklist, rerun commands, safe evidence bundle,
required route/elevator materials, handoff owner, next required evidence,
`same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, weak or
false `same_evidence_ref_required`, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, Start
Delivery, Confirm Dropoff, Cancel, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, owner checklist
execution, rerun command execution, material collection, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
material files, raw route logs, raw artifacts, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_callback_intake`, the alias
`route_task_field_retest_acceptance_execution_callback_intake_summary`, and the
Robot alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_callback_intake_summary`
from an explicit
`route_task_field_retest_acceptance_execution_callback_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_INTAKE_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1`
or
`schema=trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution callback intake summary: it may expose only callback intake status,
source execution pack, safe callback packet, evidence-ref match status,
received/missing/rejected materials, owner next steps, next required evidence,
`same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, weak or
false `same_evidence_ref_required`, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, Start
Delivery, Confirm Dropoff, Cancel, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, owner next-step
completion, callback packet verification, material collection, production
readiness, dropoff/cancel completion, or delivery success. They must not expose
raw material files, raw route logs, raw callback artifacts, raw commands, raw
ROS topics, `/cmd_vel`, serial/UART details, credentials, local paths,
checksums, tracebacks, complete artifacts, or Objective 5 external proof, and
they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_callback_review_decision`, the
alias
`route_task_field_retest_acceptance_execution_callback_review_decision_summary`,
and the Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary`
from an explicit
`route_task_field_retest_acceptance_execution_callback_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_DECISION_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution callback review decision summary: it may expose only review decision,
source callback intake status, safe evidence ref, owner handoff, next required
evidence, rerun commands or rerun hint, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, success or
control claims, enabled actions, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed as blocked/not_proven. The
fields do not trigger `/api/collect`, Start Delivery, Confirm Dropoff, Cancel,
dropoff, cancel, ACK, remote ACK, cursor advance/persistence, terminal ACK,
Nav2, WAVE ROVER, HIL, callback review completion, owner handoff execution,
rerun command execution, production readiness, dropoff/cancel completion,
delivery success, real phone/browser proof, or Objective 5 external proof.
They must not expose raw material files, raw route logs, raw callback
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, or complete artifacts, and
they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_callback_review_handoff`, the
alias
`route_task_field_retest_acceptance_execution_callback_review_handoff_summary`,
and the Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary`
from an explicit
`route_task_field_retest_acceptance_execution_callback_review_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_CALLBACK_REVIEW_HANDOFF_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1`
or
`schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution callback review handoff summary: it may expose only handoff status,
source review decision/status, safe evidence ref, owner handoff, next required
evidence, safe rerun hint, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, success or
control claims, enabled actions, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed as blocked/not_proven. The
fields do not trigger `/api/collect`, Start Delivery, Confirm Dropoff, Cancel,
dropoff, cancel, ACK, remote ACK, cursor advance/persistence, terminal ACK,
Nav2, WAVE ROVER, HIL, callback review handoff execution, owner handoff
completion, rerun command execution, production readiness, dropoff/cancel
completion, delivery success, real phone/browser proof, or Objective 5 external
proof. They must not expose raw material files, raw route logs, raw callback
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, or complete artifacts, and
they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_handoff_intake`, the alias
`route_task_field_retest_acceptance_execution_handoff_intake_summary`, and the
Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary`
from an explicit
`route_task_field_retest_acceptance_execution_handoff_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_HANDOFF_INTAKE_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1`
or
`schema=trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution handoff intake summary: it may expose only handoff intake status,
source handoff status, safe evidence ref, owner acknowledgement state, owner
handoff, next required evidence, safe rerun hint, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, success or
control claims, enabled actions, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed as blocked/not_proven. The
fields do not trigger `/api/collect`, Start Delivery, Confirm Dropoff, Cancel,
dropoff, cancel, ACK, remote ACK, cursor advance/persistence, terminal ACK,
Nav2, WAVE ROVER, HIL, handoff intake execution, owner acknowledgement
completion, rerun command execution, production readiness, dropoff/cancel
completion, delivery success, real phone/browser proof, or Objective 5 external
proof. They must not expose raw material files, raw route logs, raw callback
artifacts, raw owner intake JSON, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, or
complete artifacts, and they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_rerun_queue`, the alias
`route_task_field_retest_acceptance_execution_rerun_queue_summary`, and the
Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_queue_summary`
from an explicit
`route_task_field_retest_acceptance_execution_rerun_queue_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_QUEUE_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1`
or
`schema=trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution rerun queue summary: it may expose only queue status, source handoff
intake status, safe evidence ref, owner handoff, next required evidence, safe
rerun hint, blocked reason, safe copy, boundary,
`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, missing required safe summary fields, success or
control claims, enabled actions, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed as blocked/not_proven. The
fields do not trigger `/api/collect`, Start Delivery, Confirm Dropoff, Cancel,
dropoff, cancel, ACK, remote ACK, cursor advance/persistence, terminal ACK,
Nav2, WAVE ROVER, serial/UART, HIL, rerun queue execution, rerun command
execution, production readiness, dropoff/cancel completion, delivery success,
real phone/browser proof, or Objective 5 external proof. They must not expose
raw material files, raw route logs, raw callback artifacts, raw owner intake
JSON, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, or complete artifacts, and
they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_rerun_result_intake`, the alias
`route_task_field_retest_acceptance_execution_rerun_result_intake_summary`, and
the Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_intake_summary`
from an explicit
`route_task_field_retest_acceptance_execution_rerun_result_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_INTAKE_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. Robot consumes only the sanitized summary, not the raw Autonomy artifact.
The summary must use
`schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1`,
point to
`source_schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1`,
and stay inside
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution rerun result intake summary: it may expose only schema, intake
status, safe `evidence_ref`, owner handoff, next required evidence, boundary
flags, safe copy,
`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing sanitized summary, unreadable input,
unsupported schema or boundary, unsafe copy, raw artifact consumption,
control-entrypoint enablement, missing `evidence_ref`, same-`evidence_ref`
mismatch, non-boolean `same_evidence_ref_required`, success/control claims,
enabled actions, `delivery_success=true`, or `primary_actions_enabled=true`
sources fail closed as blocked/not_proven. Expected decision statuses include
`ready_for_acceptance_execution_rerun_result_handoff`,
`needs_acceptance_execution_rerun_result_backfill`,
`evidence_ref_mismatch_rerun_result`, `blocked_unsafe_rerun_result`, and
`blocked_unsupported_rerun_result_intake`. The fields do not trigger
`/api/collect`, Start Delivery, Confirm Dropoff, Cancel, dropoff, cancel, ACK,
remote ACK, cursor advance/persistence, terminal ACK, Nav2/fixed-route runtime,
WAVE ROVER, serial/UART, HIL, route completion, dropoff/cancel completion,
delivery result, delivery success, real phone/browser proof, or Objective 5
external proof. They must not expose raw material files, raw route logs, raw
callback artifacts, raw owner intake JSON, raw commands, raw ROS topics,
`/cmd_vel`, serial/UART details, baudrate, credentials, local paths, checksums,
tracebacks, WAVE ROVER material, or complete artifacts, and they are not
command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_callback_intake` and the alias
`route_task_field_retest_callback_intake_summary` from an explicit
`route_task_field_retest_callback_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_INTAKE_SUMMARY`, top-level status
fields, or an already sanitized nested diagnostics summary source. The source
JSON must use `schema=trashbot.route_task_field_retest_callback_intake.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_callback_intake_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_callback_intake.v1` and the
same evidence boundary. This field is metadata-only Robot diagnostics support
for sanitized field callback intake: it may expose only safe summary, safe
`evidence_ref`, intake status, received filenames summary, missing materials,
same-evidence-ref match result, next backfill action, callback checklist
result, Robot-compatible diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_callback_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported-schema, unsafe copy, missing `evidence_ref`, same-`evidence_ref`
mismatch, weak or non-boolean `same_evidence_ref_required`, success phrasing,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw callback JSON, raw route logs, raw commands,
raw ROS topics, `/cmd_vel`, serial/UART details, credentials, local paths,
checksums, tracebacks, complete artifacts, or Objective 5 external proof, and
they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_callback_review_decision` and the alias
`route_task_field_retest_callback_review_decision_summary` from an explicit
`route_task_field_retest_callback_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_CALLBACK_REVIEW_DECISION_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_callback_review_decision.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_callback_review_decision_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_callback_review_decision.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for sanitized field callback review decisions: it may expose only safe
summary, safe `evidence_ref`, review decision, source intake status, blocked
reasons, next required evidence, result-intake readiness, owner handoff,
Robot-compatible diagnostics summary, boundary,
`software_proof_docker_route_task_field_retest_callback_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Expected decision values include
`ready_for_result_intake`, `needs_material_backfill`,
`evidence_ref_mismatch_rerun`, and `unsupported_callback_schema`; unsafe
callback copy must fail closed as `blocked_unsafe_callback`. Missing summary,
unreadable input, unsupported schema or boundary, unsafe copy, missing
`evidence_ref`, same-`evidence_ref` mismatch, success phrasing,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
and remain blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result intake completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
callback JSON, raw route logs, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not
command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_review_result_handoff` and the alias
`route_task_field_retest_review_result_handoff_summary` from an explicit
`route_task_field_retest_review_result_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_REVIEW_RESULT_HANDOFF_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_review_result_handoff.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_review_result_handoff_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_review_result_handoff.v1` and
the same evidence boundary. This field is metadata-only Robot diagnostics
support for sanitized review-result handoff: it may expose only safe summary,
safe `evidence_ref`, source review decision, handoff status,
result-intake readiness, required materials, owner handoff, blocked reasons,
boundary, control boundary,
`software_proof_docker_route_task_field_retest_review_result_handoff_gate`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`same_evidence_ref_required=true`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`,
same-`evidence_ref` mismatch, weak `same_evidence_ref_required`, success
phrasing, `delivery_success=true`, or `primary_actions_enabled=true` sources
fail closed as blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result intake completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
callback JSON, raw route logs, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not command/status/ACK
robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_acceptance_packet` and the alias
`route_task_field_retest_result_acceptance_packet_summary` from an explicit
`route_task_field_retest_result_acceptance_packet_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_PACKET_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_acceptance_packet.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_result_acceptance_packet.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for the result acceptance packet: it may expose only packet status,
safe `evidence_ref`, missing material summary, owner handoff, rerun commands
summary, pass/fail criteria summary, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, success/control
claims, `delivery_success=true`, or `primary_actions_enabled=true` sources
fail closed as blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result intake completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw route
logs, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_result_acceptance_backfill` and the alias
`route_task_field_retest_result_acceptance_backfill_summary` from an explicit
`route_task_field_retest_result_acceptance_backfill_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_ACCEPTANCE_BACKFILL_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_result_acceptance_backfill.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_result_acceptance_backfill.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for the acceptance backfill gate: it may expose only backfill status,
safe `evidence_ref`, material completeness summary, alignment status,
missing/rejected category summary, owner handoff, rerun command summary, safe
copy, boundary,
`software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, success/control
claims, `delivery_success=true`, or `primary_actions_enabled=true` sources
fail closed as blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result intake completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
material files, raw route logs, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not command/status/ACK
robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_backfill_review_decision` and the alias
`route_task_field_retest_result_backfill_review_decision_summary` from an
explicit `route_task_field_retest_result_backfill_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_BACKFILL_REVIEW_DECISION_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_result_backfill_review_decision.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_retest_result_backfill_review_decision.v1`
and the same evidence boundary. This field is metadata-only Robot diagnostics
support for the backfill review decision gate: it may expose only review
decision metadata, safe `evidence_ref`, material status, accepted materials,
missing materials, rejected materials, owner handoff, next required evidence,
rerun commands, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, success/control
claims, `delivery_success=true`, or `primary_actions_enabled=true` sources
fail closed as blocked/not_proven. The fields do not trigger `/api/collect`,
dropoff, cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result intake completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
material files, raw route logs, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not command/status/ACK
robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_review_dispatch` and the alias
`route_task_field_retest_result_review_dispatch_summary` from an explicit
`route_task_field_retest_result_review_dispatch_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DISPATCH_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_review_dispatch_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_dispatch_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's field
retest result review dispatch summary: it may expose only dispatch metadata,
safe `evidence_ref`, accepted materials, missing materials, rejected
materials, owner work orders, callback packet requirements, rerun commands,
`same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_review_dispatch_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, weak or false
`same_evidence_ref_required`, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` sources fail closed as blocked/not_proven.
The fields do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, result intake
completion, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw material files, raw route logs, raw
commands, raw ROS topics, `/cmd_vel`, serial/UART details, credentials, local
paths, checksums, tracebacks, complete artifacts, or Objective 5 external
proof, and they are not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_review_intake`, the alias
`route_task_field_retest_result_review_intake_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_result_review_intake_summary` from
an explicit `route_task_field_retest_result_review_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_INTAKE_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_review_intake.v1` or
`schema=trashbot.route_task_field_retest_result_review_intake_summary.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_intake_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's field
retest result review intake summary: it may expose only intake status, safe
`evidence_ref`, missing materials, owner follow-up, review-ready package,
rerun package, next required evidence, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_review_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields,
success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true` sources fail closed as blocked/not_proven. The
fields do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, result review
completion, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw material files, raw route logs, raw
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_rerun_result_review_decision`,
the alias
`route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary`,
and the Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary`
from an explicit
`route_task_field_retest_acceptance_execution_rerun_result_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_DECISION_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. Robot consumes only the sanitized Autonomy summary, not the raw
Autonomy artifact. The summary must use
`schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1`,
point to
`source_schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1`,
and stay inside
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution rerun result review decision summary: it may expose only schema,
decision status, review decision, safe `evidence_ref`, next required evidence,
owner handoff, boundary flags, safe copy,
`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing sanitized summary, unreadable input,
unsupported schema or boundary, unsafe copy, raw artifact consumption,
control-entrypoint enablement, missing `evidence_ref`, same-`evidence_ref`
mismatch, non-boolean `same_evidence_ref_required`, success/control claims,
enabled actions, `delivery_success=true`, or `primary_actions_enabled=true`
sources fail closed as blocked/not_proven. The fields do not trigger
`/api/collect`, Start Delivery, Confirm Dropoff, Cancel, dropoff, cancel, ACK,
remote ACK, cursor advance/persistence, terminal ACK, Nav2/fixed-route runtime,
completion, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw material files, raw route logs, raw
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_acceptance_execution_rerun_result_review_handoff`,
the alias
`route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary`,
and the Robot safe alias
`robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary`
from an explicit
`route_task_field_retest_acceptance_execution_rerun_result_review_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_ACCEPTANCE_EXECUTION_RERUN_RESULT_REVIEW_HANDOFF_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. Robot consumes only the sanitized Autonomy summary, not the raw
Autonomy artifact, and it must not open material directories. The summary must
use
`schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1`,
point to
`source_schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1`,
and stay inside
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's acceptance
execution rerun result review handoff summary: it may expose only schema,
handoff status, safe `evidence_ref`, owner role, owner handoff, next required
evidence, boundary flags, safe copy, `source=software_proof`,
`software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Supported status values include
`ready_for_acceptance_execution_rerun_result_owner_handoff`,
`needs_acceptance_execution_rerun_result_material_backfill`,
`evidence_ref_mismatch_rerun_result_handoff_blocked`,
`blocked_unsafe_rerun_result_handoff_copy`, and
`blocked_unsupported_rerun_result_review_decision`. Missing sanitized summary,
unreadable input, unsupported schema or boundary, unsafe copy, raw artifact
consumption, material-directory access, control-entrypoint enablement, same
`evidence_ref` mismatch, success/control claims, enabled actions,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, Start
Delivery, Confirm Dropoff, Cancel, dropoff, cancel, ACK, remote ACK, cursor
advance/persistence, terminal ACK, ROS runtime, Nav2/fixed-route runtime,
route completion, dropoff/cancel completion, delivery result, production
readiness, or delivery success. They must not expose raw material files, raw
route logs, raw artifacts, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not
command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_review_decision`, the alias
`route_task_field_retest_result_review_decision_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_result_review_decision_summary`
from an explicit `route_task_field_retest_result_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_DECISION_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_review_decision.v1` or
`schema=trashbot.route_task_field_retest_result_review_decision_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_decision_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's result
review decision summary: it may expose only decision status, source review
intake status, review decision, safe `evidence_ref`, missing materials, owner
handoff, next required evidence, rerun commands, review-ready package, rerun
package, `same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, weak or false
`same_evidence_ref_required`, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` sources fail closed as blocked/not_proven.
The fields do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, result acceptance
backfill completion, production readiness, dropoff/cancel completion, or
delivery success. They must not expose raw material files, raw route logs, raw
artifacts, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_result_review_handoff`, the alias
`route_task_field_retest_result_review_handoff_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_result_review_handoff_summary`
from an explicit `route_task_field_retest_result_review_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_REVIEW_HANDOFF_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_review_handoff.v1` or
`schema=trashbot.route_task_field_retest_result_review_handoff_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_handoff_gate`.
This field is metadata-only Robot diagnostics support for Autonomy's result
review handoff summary: it may expose only handoff status, source review
decision status, safe `evidence_ref`, owner work orders, accepted/blocked/rerun
reasons, same-evidence-ref package, next material callback requirements, next
required evidence, rerun commands, `same_evidence_ref_required=true`, safe
copy, boundary,
`software_proof_docker_route_task_field_retest_result_review_handoff_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, weak or false
`same_evidence_ref_required`, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` sources fail closed as blocked/not_proven.
The fields do not trigger `/api/collect`, dropoff, cancel, result routes,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
owner work-order completion, material callback completion, production
readiness, dropoff/cancel completion, or delivery success. They must not expose
raw material files, raw route logs, raw artifacts, raw commands, raw ROS
topics, `/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_callback_intake`, the alias
`route_task_field_retest_result_callback_intake_summary`, and the Robot alias
`robot_diagnostics_route_task_field_retest_result_callback_intake_summary`
from an explicit `route_task_field_retest_result_callback_intake_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_INTAKE_SUMMARY`, top-level
status fields, or an already sanitized nested diagnostics summary source. The
source JSON must use
`schema=trashbot.route_task_field_retest_result_callback_intake_summary.v1`
or `schema=trashbot.route_task_field_retest_result_callback_intake.v1` and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_intake_gate`.
This field is metadata-only Robot diagnostics support for the result callback
intake gate: it may expose only callback intake metadata, source schema/source
boundary, safe `evidence_ref`, accepted materials/accepted updates, missing
materials/missing updates, rejected materials/rejected updates, owner follow-up,
review decision handoff, rerun commands, `same_evidence_ref_required=true`,
safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_callback_intake_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, weak or false
`same_evidence_ref_required`, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` sources fail closed as blocked/not_proven.
The fields do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, review decision
execution, production readiness, dropoff/cancel completion, or delivery
success. They must not expose raw material files, raw route logs, raw callback
packets, raw commands, raw ROS topics, `/cmd_vel`, serial/UART details,
credentials, local paths, checksums, tracebacks, complete artifacts, or
Objective 5 external proof, and they are not command/status/ACK robot contract
fields.

Operator diagnostics may also expose
`route_task_field_retest_result_callback_review_decision`, the alias
`route_task_field_retest_result_callback_review_decision_summary`, and the
Robot alias
`robot_diagnostics_route_task_field_retest_result_callback_review_decision_summary`
from an explicit
`route_task_field_retest_result_callback_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_DECISION_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_result_callback_review_decision.v1`
or
`schema=trashbot.route_task_field_retest_result_callback_review_decision_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`.
This field is metadata-only Robot diagnostics support for the result callback
review-decision gate: it may expose only review status, source callback-intake
status, review decision, material status, accepted/missing/rejected materials,
owner handoff, next required evidence, rerun commands, safe `evidence_ref`,
`same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Expected decision values include
`ready_for_result_review`, `needs_material_backfill`, `needs_callback_rerun`,
`evidence_ref_mismatch_rerun`, and `rejected_unsafe_callback`. Missing summary,
unreadable input, unsupported schema or boundary, unsafe copy, missing
`evidence_ref`, same `evidence_ref` mismatch, missing required safe summary
fields, weak or false `same_evidence_ref_required`, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, dropoff,
cancel, remote ACK, cursor advance/persistence, terminal ACK, Nav2,
WAVE ROVER, HIL, result review completion, production readiness,
dropoff/cancel completion, or delivery success. They must not expose raw
material files, raw route logs, raw callback packets, raw commands, raw ROS
topics, `/cmd_vel`, serial/UART details, credentials, local paths, checksums,
tracebacks, complete artifacts, or Objective 5 external proof, and they are
not command/status/ACK robot contract fields.

Operator diagnostics may also expose
`route_task_field_retest_result_callback_review_handoff`, the alias
`route_task_field_retest_result_callback_review_handoff_summary`, and the
Robot alias
`robot_diagnostics_route_task_field_retest_result_callback_review_handoff_summary`
from an explicit
`route_task_field_retest_result_callback_review_handoff_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF`,
`TRASHBOT_ROUTE_TASK_FIELD_RETEST_RESULT_CALLBACK_REVIEW_HANDOFF_SUMMARY`,
top-level status fields, or an already sanitized nested diagnostics summary
source. The source JSON must use
`schema=trashbot.route_task_field_retest_result_callback_review_handoff.v1`
or
`schema=trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1`
and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`.
This field is metadata-only Robot diagnostics support for the result callback
review handoff gate: it may expose only handoff status, source review decision,
owner follow-up, review-ready package, rerun package, next required evidence,
safe `evidence_ref`, `same_evidence_ref_required=true`, safe copy, boundary,
`software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`,
`not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Expected handoff status values include
`ready_for_result_review_handoff`, `needs_owner_follow_up`,
`needs_callback_rerun`, `evidence_ref_mismatch_rerun`, and
`blocked_unsafe_review_handoff`. Missing summary, unreadable input,
unsupported schema or boundary, unsafe copy, missing `evidence_ref`, same
`evidence_ref` mismatch, missing required safe summary fields, weak or false
`same_evidence_ref_required`, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` sources fail closed as blocked/not_proven.
The fields do not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, result review
completion, owner follow-up completion, production readiness, dropoff/cancel
completion, or delivery success. They must not expose raw material files, raw
route logs, raw callback packets, raw commands, raw ROS topics, `/cmd_vel`,
serial/UART details, credentials, local paths, checksums, tracebacks, complete
artifacts, or Objective 5 external proof, and they are not
command/status/ACK robot contract fields.

Operator diagnostics may also expose `route_task_field_run_reconciliation` and
the alias `route_task_field_run_reconciliation_summary` from an explicit
`route_task_field_run_reconciliation_ref` or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_RECONCILIATION`. The source JSON must use
`schema=trashbot.route_task_field_run_reconciliation.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_reconciliation_gate`.
This summary is metadata-only support material for Task A route-task field-run
reconciliation: it may expose only the summary schema/evidence boundary, source
schema/evidence boundary, reconciliation verdict, safe evidence ref,
`same_evidence_ref_required`, materials status, operator next steps,
phone-safe summary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Raw route logs, task records, mobile summary
payloads, credentials, local paths, UART/serial details, raw ACK payloads, raw
command envelopes, production-readiness claims, and traceback content must not
enter the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, or unsafe-summary sources remain blocked/not_proven. The
fields do not trigger collect/dropoff/cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, production
readiness, dropoff/cancel completion, or delivery success. They are not
command/status/ACK robot contract fields and do not prove real fixed-route
execution, real HIL, production readiness, dropoff/cancel completion, or
delivery success.

Operator diagnostics may also expose `route_task_completion_signal` and the
alias `route_task_completion_signal_summary` from an explicit
`route_task_completion_signal_ref` or
`TRASHBOT_ROUTE_TASK_COMPLETION_SIGNAL`. The source JSON must use
`schema=trashbot.route_task_completion_signal.v1` and
`evidence_boundary=software_proof_docker_route_task_completion_signal_gate`.
This summary is metadata-only support material for route/task completion review:
it may expose only the summary schema/evidence boundary, source schema/evidence
boundary, completion verdict, safe evidence ref, `same_evidence_ref_required`,
fixed-route summary, task-record summary, state-transition summary,
dropoff/cancel completion metadata, failure/recovery reason, materials status,
operator next steps, phone-safe summary, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`. Raw route logs,
task records, mobile summary payloads, credentials, local paths, UART/serial
details, raw ACK payloads, raw command envelopes, production-readiness claims,
and traceback content must not enter the diagnostics summary. Missing,
unreadable, unsupported-schema, boundary-mismatch, unsafe-summary,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real dropoff/cancel completion, or delivery success. They
are not command/status/ACK robot contract fields and do not prove real
fixed-route execution, real HIL, production readiness, dropoff completion,
cancel completion, or delivery success.

Task records now also include `route_task_terminal_completion_rehearsal`, and
operator diagnostics may expose `route_task_terminal_completion_rehearsal` plus
the alias `route_task_terminal_completion_rehearsal_summary` from an explicit
`route_task_terminal_completion_rehearsal_ref`,
`TRASHBOT_ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL`, or
`TRASHBOT_ROUTE_TASK_TERMINAL_COMPLETION_REHEARSAL_SUMMARY`. The source JSON
must use `schema=trashbot.route_task_terminal_completion_rehearsal.v1` or
`schema=trashbot.route_task_terminal_completion_rehearsal_summary.v1` with
`evidence_boundary=software_proof_docker_route_task_terminal_completion_rehearsal_gate`.
This contract is metadata-only support for route/task terminal completion
rehearsal: it may expose only terminal verdict, final status/state,
dropoff-result metadata, cancel/failure/recovery reason, safe evidence ref,
route-progress presence, materials status, operator next steps,
phone-safe summary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing sources default to
`blocked_missing_route_task_terminal_completion_rehearsal`. Unsupported schema,
unsafe fields, `delivery_success=true`, `primary_actions_enabled=true`, or
same-`evidence_ref` mismatch remain blocked/not_proven. The fields do not
trigger collect/dropoff/cancel, remote ACK, cursor advance/persistence,
terminal ACK, Nav2, WAVE ROVER, HIL, production readiness, real dropoff
completion, real cancel completion, or delivery success.

Operator diagnostics may also expose `route_task_terminal_review_decision` and
the alias `route_task_terminal_review_decision_summary` from an explicit
`route_task_terminal_review_decision_ref`,
`TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION`,
`TRASHBOT_ROUTE_TASK_TERMINAL_REVIEW_DECISION_SUMMARY`, or an already
sanitized diagnostics nested source. The source JSON must use
`schema=trashbot.route_task_terminal_review_decision.v1` and
`evidence_boundary=software_proof_docker_route_task_terminal_review_decision_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_terminal_review_decision.v1` and the same
evidence boundary. This contract is metadata-only support for route-task
terminal review: it may expose only review decision, safe evidence ref,
`owner_handoff`, `next_required_evidence`, `field_retest_request_guidance`,
review summary, operator next steps, robot diagnostics summary,
phone-safe summary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing sources default to
`blocked_missing_route_task_terminal_review_decision`. Unsupported schema,
unsafe fields, `same_evidence_ref_required=false`, `delivery_success=true`,
`primary_actions_enabled=true`, or same-`evidence_ref` mismatch remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
ACK POST, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real dropoff/cancel completion, or delivery success.
They are not command/status/ACK robot contract fields and do not prove real
fixed-route execution, real HIL, production readiness, dropoff completion,
cancel completion, or delivery success.

Operator diagnostics may also expose `route_task_field_run_console` and the
alias `route_task_field_run_console_summary` from an explicit
`route_task_field_run_console_ref`, `TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE`, or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_CONSOLE_SUMMARY`. The source JSON must use
`schema=trashbot.route_task_field_run_console.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_console_gate`.
This summary is metadata-only support material for a PC/operator field-run
console: it may expose only the summary schema/evidence boundary, source
schema/evidence boundary, `console_verdict`, safe evidence ref,
`same_evidence_ref_required`, `field_run_plan`, `capture_checklist`,
dropoff/cancel completion metadata, `operator_next_steps`,
`robot_diagnostics_summary`, `mobile_readonly_summary`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`. Raw route logs,
task records, mobile summary payloads, credentials, local paths, UART/serial
details, raw ACK payloads, raw command envelopes, production-readiness claims,
and traceback content must not enter the diagnostics summary. Missing,
unreadable, unsupported-schema, boundary-mismatch, unsafe fields,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real dropoff/cancel completion, or delivery success. They
are not command/status/ACK robot contract fields and do not prove real
fixed-route execution, real HIL, production readiness, dropoff completion,
cancel completion, or delivery success.

Operator diagnostics may also expose `route_task_field_run_evidence_kit` and
the alias `route_task_field_run_evidence_kit_summary` from an explicit
`route_task_field_run_evidence_kit_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT`, or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_EVIDENCE_KIT_SUMMARY`. The source JSON must use
`schema=trashbot.route_task_field_run_evidence_kit.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_evidence_kit_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_run_evidence_kit.v1` and the same
evidence boundary. This summary is metadata-only support material for a
route-task field-run evidence kit: it may expose only the summary
schema/evidence boundary, source schema/evidence boundary, `kit_verdict`, safe
evidence ref, `same_evidence_ref_required=true`, materials status,
`field_run_plan`, `capture_checklist`, completion/reconciliation summaries,
`operator_next_steps`, `robot_diagnostics_summary`,
`mobile_readonly_summary`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Raw route logs, task records, mobile summary
payloads, credentials, local paths, UART/serial details, raw ACK payloads, raw
command envelopes, production-readiness claims, and traceback content must not
enter the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, unsafe fields, `same_evidence_ref_required=false`,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real dropoff/cancel completion, or delivery success. They
are not command/status/ACK robot contract fields and do not prove real
fixed-route execution, real HIL, production readiness, dropoff completion,
cancel completion, or delivery success.

Operator diagnostics may also expose `route_task_field_run_material_bundle`
and the alias `route_task_field_run_material_bundle_summary` from an explicit
`route_task_field_run_material_bundle_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE`, or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_BUNDLE_SUMMARY`. The source JSON must
use `schema=trashbot.route_task_field_run_material_bundle.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_material_bundle_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_run_material_bundle.v1` and the same
evidence boundary. This summary is metadata-only support material for a
route-task field-run material bundle: it may expose only the summary
schema/evidence boundary, source schema/evidence boundary, `bundle_verdict`,
safe evidence ref, `same_evidence_ref_required=true`, materials status,
material directory scaffold, bundle summary, `operator_next_steps`,
`robot_diagnostics_summary`, `mobile_readonly_summary`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`. Raw route logs,
task records, mobile summary payloads, credentials, local paths, UART/serial
details, raw ACK payloads, raw command envelopes, production-readiness claims,
and traceback content must not enter the diagnostics summary. Missing,
unreadable, unsupported-schema, boundary-mismatch, unsafe fields,
`same_evidence_ref_required=false`, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain blocked/not_proven. The fields do
not trigger `/api/collect`, dropoff, cancel, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL, production readiness,
real dropoff/cancel completion, or delivery success. They are not
command/status/ACK robot contract fields and do not prove real fixed-route
execution, real HIL, production readiness, dropoff completion, cancel
completion, or delivery success.

Operator diagnostics may also expose `route_task_field_run_material_validation`
and the alias `route_task_field_run_material_validation_summary` from an
explicit `route_task_field_run_material_validation_ref`,
`TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION`, or
`TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY`. The source JSON
must use `schema=trashbot.route_task_field_run_material_validation.v1` and
`evidence_boundary=software_proof_docker_route_task_field_run_material_validation_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.route_task_field_run_material_validation.v1` and the
same evidence boundary. This summary is metadata-only support material for
validating route-task field-run materials: it may expose only the summary
schema/evidence boundary, source schema/evidence boundary,
`validation_verdict`, safe evidence ref, `same_evidence_ref_required=true`,
materials status, validation summary, material validation checks,
`operator_next_steps`, `robot_diagnostics_summary`,
`mobile_readonly_summary`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Raw route logs, task records, mobile summary
payloads, credentials, local paths, UART/serial details, raw ACK payloads, raw
command envelopes, production-readiness claims, and traceback content must not
enter the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, unsafe fields, `same_evidence_ref_required=false`,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real dropoff/cancel completion, or delivery success.
They are not command/status/ACK robot contract fields and do not prove real
fixed-route execution, real HIL, production readiness, dropoff completion,
cancel completion, or delivery success.

Operator diagnostics may also expose `elevator_field_run_material_validation`
and the alias `elevator_field_run_material_validation_summary` from an
explicit `elevator_field_run_material_validation_ref`,
`TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION`, or
`TRASHBOT_ELEVATOR_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY`. The source JSON
must use `schema=trashbot.elevator_field_run_material_validation.v1` and
`evidence_boundary=software_proof_docker_elevator_field_material_validation_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.elevator_field_run_material_validation.v1` and the
same evidence boundary. This summary is metadata-only support material for
validating elevator field-run materials from Autonomy: it may expose only the
summary schema/evidence boundary, source schema/evidence boundary,
`validation_verdict`, safe evidence ref, `same_evidence_ref_required=true`,
materials status, validation summary, material validation checks,
`operator_next_steps`, `robot_diagnostics_summary`,
`mobile_readonly_summary`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Raw route logs, task records, mobile summary
payloads, credentials, local paths, UART/serial details, raw ACK payloads, raw
command envelopes, production-readiness claims, and traceback content must not
enter the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, unsafe fields, `same_evidence_ref_required=false`,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real elevator operation, real dropoff/cancel completion,
or delivery success. They are not command/status/ACK robot contract fields and
do not prove real elevator, real floor confirmation, real Nav2, real HIL,
production readiness, dropoff completion, cancel completion, or delivery
success.

Operator diagnostics may also expose `elevator_field_run_review` and the alias
`elevator_field_run_review_summary` from an explicit
`elevator_field_run_review_ref`, `TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW`, or
`TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY`. The source JSON must use
`schema=trashbot.elevator_field_run_review.v1` and
`evidence_boundary=software_proof_docker_elevator_field_review_decision_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.elevator_field_run_review.v1` and the same evidence
boundary. This summary is metadata-only support material for turning elevator
field-run material validation into an operator review decision: it may expose
only the summary schema/evidence boundary, source schema/evidence boundary,
`review_decision`, safe evidence ref, `same_evidence_ref_required=true`,
blocked categories, `operator_next_steps`, `commands_to_rerun`,
`capture_checklist`, `review_summary`, `robot_diagnostics_summary`,
`phone_safe_summary`, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`. Raw route logs, task records, mobile summary
payloads, credentials, local paths, UART/serial details, raw ACK payloads, raw
command envelopes, production-readiness claims, and traceback content must not
enter the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, unsafe fields, `same_evidence_ref_required=false`,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real elevator operation, real dropoff/cancel completion,
or delivery success. They are not command/status/ACK robot contract fields and
do not prove real elevator, real floor confirmation, real Nav2, real HIL,
production readiness, dropoff completion, cancel completion, or delivery
success.

Operator diagnostics may also expose `elevator_field_run_execution_pack` and
the alias `elevator_field_run_execution_pack_summary` from an explicit
`elevator_field_run_execution_pack_ref`,
`TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK`, or
`TRASHBOT_ELEVATOR_FIELD_RUN_EXECUTION_PACK_SUMMARY`. The source JSON must use
`schema=trashbot.elevator_field_run_execution_pack.v1` and
`evidence_boundary=software_proof_docker_elevator_field_rehearsal_execution_pack_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.elevator_field_run_execution_pack.v1` and the same
evidence boundary. This summary is metadata-only support material for turning
an elevator review decision into a controlled field-rehearsal execution pack:
it may expose only the summary schema/evidence boundary, source schema/evidence
boundary, `execution_pack_verdict`, safe evidence ref,
`same_evidence_ref_required=true`, `controlled_rehearsal_manifest`,
`required_material_templates`, `first_run_commands`, `rerun_commands`,
`operator_handoff`, `robot_diagnostics_summary`, `phone_safe_summary`,
`not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
Raw route logs, task records, mobile summary payloads, credentials, local
paths, UART/serial details, raw artifacts, raw ACK payloads, raw command
envelopes, production-readiness claims, and traceback content must not enter
the diagnostics summary. Missing, unreadable, unsupported-schema,
boundary-mismatch, unsafe fields, `same_evidence_ref_required=false`,
non-boolean `same_evidence_ref_required`, `delivery_success=true`, or
`primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger `/api/collect`, dropoff, cancel,
remote ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real elevator operation, real dropoff/cancel completion,
or delivery success. They are not command/status/ACK robot contract fields and
do not prove real elevator, real floor confirmation, real Nav2, real HIL,
production readiness, dropoff completion, cancel completion, or delivery
success.

Operator diagnostics may also expose `elevator_route_evidence_reconciliation`
and the alias `elevator_route_evidence_reconciliation_summary` from an explicit
`elevator_route_evidence_reconciliation_ref`,
`TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION`, or
`TRASHBOT_ELEVATOR_ROUTE_EVIDENCE_RECONCILIATION_SUMMARY`. The source JSON must
use `schema=trashbot.elevator_route_evidence_reconciliation.v1` and
`evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`.
If the source is already a summary wrapper, it must still point to
`source_schema=trashbot.elevator_route_evidence_reconciliation.v1` and the same
evidence boundary. This summary is metadata-only support material for
reconciling elevator rehearsal evidence and route completion signal material on
the same `evidence_ref`: it may expose only the summary schema/evidence
boundary, source schema/evidence boundary, `reconciliation_verdict`, safe
evidence ref, `same_evidence_ref_required=true`, source states, materials
status, missing materials, mismatch reasons, `operator_next_steps`,
`robot_diagnostics_summary`, `phone_safe_summary`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`. Raw route logs,
task records, mobile summary payloads, credentials, local paths, UART/serial
details, raw ACK payloads, raw command envelopes, production-readiness claims,
and traceback content must not enter the diagnostics summary. Missing,
unreadable, unsupported-schema, boundary-mismatch, unsafe fields,
`same_evidence_ref_required=false`, non-boolean `same_evidence_ref_required`,
`delivery_success=true`, or `primary_actions_enabled=true` sources remain
blocked/not_proven. The fields do not trigger collect/dropoff/cancel, remote
ACK, cursor advance/persistence, terminal ACK, Nav2, WAVE ROVER, HIL,
production readiness, real elevator operation, dropoff/cancel completion, or
delivery success. They are not command/status/ACK robot contract fields and do
not prove real elevator, real floor confirmation, real Nav2/fixed-route, real
HIL, production readiness, dropoff completion, cancel completion, or delivery
success.

Operator diagnostics may also expose `route_elevator_field_session_handoff`
and the alias `route_elevator_field_session_handoff_summary` from an explicit
`route_elevator_field_session_handoff_ref`,
`TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF`, or
`TRASHBOT_ROUTE_ELEVATOR_FIELD_SESSION_HANDOFF_SUMMARY`. The source JSON must
use `schema=trashbot.route_elevator_field_session_handoff.v1` or
`schema=trashbot.route_elevator_field_session_handoff_summary.v1` with
`evidence_boundary=software_proof_docker_route_elevator_field_session_handoff_gate`.
If the source is already a summary wrapper, it must still point to the same
source schema/evidence boundary. This summary is metadata-only support material
for explaining the next route/elevator field-session handoff: it may expose
only the summary schema/evidence boundary, source schema/evidence boundary,
`handoff_verdict`, safe evidence ref, `same_evidence_ref_required=true`,
whitelisted `source_summaries`, `field_session_manifest`,
`required_materials_summary`, `operator_next_steps`,
`robot_diagnostics_summary`, `mobile_readonly_summary`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`. It is not
control authorization and must not enable Start Delivery, Confirm Dropoff,
Cancel, ACK POST, cursor/persistence updates, terminal ACK, Nav2, route
execution, dropoff/cancel completion, HIL, WAVE ROVER motion, or delivery
success. Diagnostics consumers must treat the summary as fence-only metadata:
`metadata_only=true`, `collect_triggered=false`, `dropoff_triggered=false`,
`cancel_triggered=false`, `ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`,
`production_ready=false`, `dropoff_completion=false`, and
`cancel_completion=false` remain required even when the handoff verdict is
ready-for-field-session. Raw route logs, task records, mobile raw payloads,
credentials, local paths, checksum material, UART/serial details, raw ACK
payloads, raw command envelopes, production-readiness claims, success copy, and
traceback content must not enter the diagnostics summary. Missing, unreadable,
unsupported-schema, boundary-mismatch, unsafe fields,
`same_evidence_ref_required=false`, non-boolean `same_evidence_ref_required`,
`delivery_success=true`, `primary_actions_enabled=true`, or success wording
sources remain blocked/not_proven. The field does not change `/api/collect`,
ACK, cursor, Nav2, dropoff/cancel, route execution, or HIL behavior, and it
does not prove real field-session pass, real elevator, real floor
confirmation, real Nav2/fixed-route, real HIL, dropoff completion, cancel
completion, Objective 5 external proof, or delivery success.

Operator diagnostics may also expose
`mobile_route_elevator_field_device_precheck` and the alias
`mobile_route_elevator_field_device_precheck_summary` from an explicit
`mobile_route_elevator_field_device_precheck_ref`,
`TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK`, or
`TRASHBOT_MOBILE_ROUTE_ELEVATOR_FIELD_DEVICE_PRECHECK_SUMMARY`. The source JSON
must use `schema=trashbot.mobile_route_elevator_field_device_precheck.v1` or
`schema=trashbot.mobile_route_elevator_field_device_precheck_summary.v1` with
`evidence_boundary=software_proof_docker_mobile_route_elevator_field_device_precheck_gate`.
If the source is already a summary wrapper, it must still point to the same
source schema/evidence boundary. This field is metadata-only Robot diagnostics
support for mobile route/elevator field-device precheck review. It may expose
only the summary schema/evidence boundary, source schema/evidence boundary,
`precheck_status`, safe evidence ref, `device_precheck_summary`,
`route_elevator_precheck_summary`, `operator_next_steps`,
`mobile_readonly_summary`, `not_proven`, and the conservative false fields
`real_device_observed=false`, `pwa_install_prompt_observed=false`,
`route_elevator_field_pass=false`, `dropoff_completion=false`,
`cancel_completion=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 trigger, not HIL, not a dropoff/cancel completion
signal, and not delivery success. Diagnostics consumers must treat it as
fence-only metadata: `metadata_only=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false` remain required even when a precheck source is
present. Raw route logs, task records, mobile raw payloads, credentials, local
paths, checksum material, UART/serial details, raw ACK payloads, raw command
envelopes, production-readiness claims, success copy, and traceback content
must not enter the diagnostics summary. Missing, unreadable,
unsupported-schema, boundary-mismatch, unsafe fields,
`real_device_observed=true`, `pwa_install_prompt_observed=true`,
`route_elevator_field_pass=true`, `dropoff_completion=true`,
`cancel_completion=true`, `delivery_success=true`,
`primary_actions_enabled=true`, or success wording sources remain
blocked/not_proven. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL,
dropoff/cancel completion, or delivery-success behavior, and it 不证明真实手机、
真实 PWA install prompt、真实 route/elevator、真实 HIL、Objective 5 external
proof 或 delivery success。

Operator diagnostics may also expose `mobile_field_material_intake` and the
alias `mobile_field_material_intake_summary` from an explicit
`mobile_field_material_intake_ref`, `TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE`, or
`TRASHBOT_MOBILE_FIELD_MATERIAL_INTAKE_SUMMARY`. The source JSON must use
`schema=trashbot.mobile_field_material_intake.v1` or
`schema=trashbot.mobile_field_material_intake_summary.v1` with
`evidence_boundary=software_proof_docker_mobile_field_material_intake_gate`. If
the source is already a summary wrapper, it must still point to the same source
schema/evidence boundary. This field is metadata-only Robot diagnostics support
for mobile field-material intake after route/elevator device precheck. It may
expose only the summary schema/evidence boundary, source schema/evidence
boundary, `intake_status`, safe evidence ref, `device_observation_summary`,
`route_elevator_materials_summary`, `nav2_fixed_route_materials_summary`,
`task_record_materials_summary`, `completion_signal_summary`,
`dropoff_cancel_materials_summary`, `operator_next_steps`,
`mobile_readonly_summary`, `not_proven`, and conservative false fields including
`real_device_observed=false`, `route_elevator_field_pass=false`,
`nav2_fixed_route_run=false`, `task_record_completion=false`,
`completion_signal_received=false`, `dropoff_completion=false`,
`cancel_completion=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 trigger, not HIL, not a dropoff/cancel completion
signal, and not delivery success. Diagnostics consumers must treat it as
fence-only metadata: `metadata_only=true`, `same_evidence_ref_required=true`,
`collect_triggered=false`, `dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false` remain required even when an intake source is present.
Raw route logs, task records, mobile raw payloads, credentials, local paths,
checksum material, UART/serial details, raw ACK payloads, raw command envelopes,
production-readiness claims, success copy, and traceback content must not enter
the diagnostics summary. Missing, unreadable, bad JSON, unsupported-schema,
boundary-mismatch, non-boolean `same_evidence_ref_required`,
`real_device_observed=true`, `route_elevator_field_pass=true`,
`nav2_fixed_route_run=true`, `task_record_completion=true`,
`completion_signal_received=true`, `dropoff_completion=true`,
`cancel_completion=true`, `delivery_success=true`, `primary_actions_enabled=true`,
or success wording sources remain blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2 trigger,
HIL, dropoff/cancel completion, or delivery-success behavior, and it 不证明真实手机、
真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、
真实 HIL、Objective 5 external proof 或 delivery success。

Operator diagnostics may also expose `mobile_field_material_review_decision` and
the alias `mobile_field_material_review_decision_summary` from an explicit
`mobile_field_material_review_decision_ref`,
`TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION`,
`TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION_SUMMARY`, or an already
sanitized diagnostics source. The source JSON must use
`schema=trashbot.mobile_field_material_review_decision.v1` or
`schema=trashbot.mobile_field_material_review_decision_summary.v1` with
`evidence_boundary=software_proof_docker_mobile_field_material_review_decision_gate`.
If the source is already a summary wrapper, it must still point to the same
source schema/evidence boundary. This field is metadata-only Robot diagnostics
support for the mobile field-material review decision after intake. It may
expose only the summary schema/evidence boundary, source schema/evidence
boundary, `review_status`, `review_decision`, `blocker_classification`,
`next_required_evidence`, `owner_handoff`, safe evidence ref,
`same_evidence_ref_status`, `operator_next_steps`, `mobile_readonly_summary`,
`not_proven`, and conservative false fields including
`real_device_observed=false`, `route_elevator_field_pass=false`,
`nav2_fixed_route_run=false`, `task_record_completion=false`,
`completion_signal_received=false`, `dropoff_completion=false`,
`cancel_completion=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 or fixed-route trigger, not HIL, not a
dropoff/cancel completion signal, and not delivery success. Diagnostics
consumers must treat it as fence-only metadata: `metadata_only=true`,
`same_evidence_ref_required=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a review decision source is present. Raw route logs, task
records, mobile raw payloads, credentials, local paths, checksum material,
UART/serial details, raw ACK payloads, raw command envelopes,
production-readiness claims, success copy, and traceback content must not enter
the diagnostics summary. Missing, unreadable, bad JSON, unsupported-schema,
boundary-mismatch, non-boolean `same_evidence_ref_required`,
`real_device_observed=true`, `route_elevator_field_pass=true`,
`nav2_fixed_route_run=true`, `task_record_completion=true`,
`completion_signal_received=true`, `dropoff_completion=true`,
`cancel_completion=true`, `delivery_success=true`, `primary_actions_enabled=true`,
or success wording sources remain blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2 trigger,
HIL, dropoff/cancel completion, or delivery-success behavior, and it 不证明真实手机、
真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、
真实 HIL、Objective 5 external proof 或 delivery success。

Operator diagnostics may also expose `mobile_field_material_retest_request` and
the alias `mobile_field_material_retest_request_summary` from an explicit
`mobile_field_material_retest_request_ref`,
`TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST`,
`TRASHBOT_MOBILE_FIELD_MATERIAL_RETEST_REQUEST_SUMMARY`, or an already
sanitized diagnostics source. The source JSON must use
`schema=trashbot.mobile_field_material_retest_request.v1` or
`schema=trashbot.mobile_field_material_retest_request_summary.v1` with
`evidence_boundary=software_proof_docker_mobile_field_material_retest_request_gate`.
If the source is already a summary wrapper, it must still point to the same
source schema/evidence boundary. This field is metadata-only Robot diagnostics
support for turning a mobile field-material review decision into the next
route/elevator material retest request. It may expose only the summary
schema/evidence boundary, source schema/evidence boundary,
`retest_request_status`, `source_review_decision`, `blockers`,
`next_required_evidence`, `retest_request`,
`route_elevator_material_checklist`, `owner_handoff`, safe evidence ref,
`same_evidence_ref_status`, `operator_next_steps`,
`mobile_readonly_summary`, `not_proven`, and conservative false fields
including `real_device_observed=false`, `route_elevator_field_pass=false`,
`nav2_fixed_route_run=false`, `task_record_completion=false`,
`completion_signal_received=false`, `dropoff_completion=false`,
`cancel_completion=false`, `delivery_success=false`, and
`primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 or fixed-route trigger, not HIL, not a
dropoff/cancel completion signal, and not delivery success. Diagnostics
consumers must treat it as fence-only metadata: `metadata_only=true`,
`same_evidence_ref_required=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a retest request source is present. Raw route logs, task
records, mobile raw payloads, credentials, local paths, checksum material,
UART/serial details, raw ACK payloads, raw command envelopes,
production-readiness claims, success copy, and traceback content must not enter
the diagnostics summary. Missing, unreadable, bad JSON, unsupported-schema,
boundary-mismatch, non-boolean `same_evidence_ref_required`,
`real_device_observed=true`, `route_elevator_field_pass=true`,
`nav2_fixed_route_run=true`, `task_record_completion=true`,
`completion_signal_received=true`, `dropoff_completion=true`,
`cancel_completion=true`, `delivery_success=true`, `primary_actions_enabled=true`,
or success wording sources remain blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2 trigger,
HIL, dropoff/cancel completion, or delivery-success behavior, and it 不证明真实手机、
真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、
真实 HIL、Objective 5 external proof 或 delivery success。

Operator diagnostics may also expose `wave_rover_feedback_replay` and the alias
`wave_rover_feedback_replay_summary` from an explicit
`wave_rover_feedback_replay_ref`, `TRASHBOT_WAVE_ROVER_FEEDBACK_REPLAY`,
`TRASHBOT_WAVE_ROVER_FEEDBACK_REPLAY_SUMMARY`, `latest_status`, or an already
sanitized diagnostics source. The source JSON must use
`schema=trashbot.wave_rover_feedback_replay.v1` or
`schema=trashbot.wave_rover_feedback_replay_summary.v1` with
`evidence_boundary=software_proof_docker_wave_rover_feedback_replay_gate`. If
the source is already a Robot diagnostics summary wrapper, it must still point
to the same source schema/evidence boundary. This field is metadata-only Robot
diagnostics support for the WAVE ROVER feedback replay gate backed by
`docs/vendor/VENDOR_INDEX.md` WAVE ROVER UART/JSON references; it does not
touch real UART, request `T=130`/`T=131` feedback, publish control topics, or
claim HIL. It may expose only summary schema/evidence boundary, source
schema/evidence boundary, `feedback_replay_status`, safe `evidence_ref`,
`feedback_alignment`, `interval_alignment`, `topic_alignment`,
`next_required_evidence`, `not_proven`, and conservative boundary flags:
`metadata_only=true`, `real_hardware_observed=false`,
`real_wave_rover_feedback=false`, `real_serial_or_uart_feedback=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. It must also
keep `collect_triggered=false`, `dropoff_triggered=false`,
`cancel_triggered=false`, `ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false`. Missing, unreadable, bad JSON, missing schema,
unsupported schema or boundary, missing `not_proven`, raw local paths, raw
serial/UART path, baudrate, raw feedback, raw command/status/ACK payloads,
success copy, `delivery_success=true`, or `primary_actions_enabled=true`
sources fail closed as blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2
trigger, WAVE ROVER feedback flow, HIL, dropoff/cancel completion, or
delivery-success behavior.

Operator diagnostics may also expose `wave_rover_hil_packet_intake`,
`wave_rover_hil_packet_intake_summary`, and the Robot-compatible
`robot_diagnostics_wave_rover_hil_packet_intake_summary` alias from an explicit
`wave_rover_hil_packet_intake_ref`, `TRASHBOT_WAVE_ROVER_HIL_PACKET_INTAKE`,
`TRASHBOT_WAVE_ROVER_HIL_PACKET_INTAKE_SUMMARY`, `latest_status`, or an already
sanitized diagnostics source. The source JSON must use
`schema=trashbot.wave_rover_hil_packet_intake.v1` or
`schema=trashbot.wave_rover_hil_packet_intake_summary.v1` with
`evidence_boundary=software_proof_docker_wave_rover_hil_packet_intake_gate`. If
the source is already a Robot diagnostics summary wrapper, it must still point
to the same source schema/evidence boundary. This field is metadata-only Robot
diagnostics support for the PC HIL packet intake gate; it does not open serial,
read raw packet files, subscribe to `/odom`, `/imu/data`, or `/battery`, publish
control topics, claim WAVE ROVER pass, or claim HIL. It may expose only summary
schema/evidence boundary, source schema/evidence boundary, `overall_status`,
`packet_status`, safe `evidence_ref`, `required_files`, `missing_files`,
`operator_report_status`, `next_required_evidence`, `not_proven`, and
conservative boundary flags: `metadata_only=true`,
`real_hardware_observed=false`, `real_wave_rover=false`, `real_uart=false`,
`real_odom=false`, `real_imu=false`, `real_battery=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. It must also
keep `collect_triggered=false`, `dropoff_triggered=false`,
`cancel_triggered=false`, `ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false`. Missing, unreadable, bad JSON, missing schema,
unsupported schema or boundary, missing `overall_status=not_proven`, missing
`not_proven`, non-boolean or false `same_evidence_ref_required`,
`evidence_ref_match=false`, raw artifact/local paths, raw serial/UART path,
baudrate, checksum, credentials, traceback, raw packet/feedback payloads,
success copy, `delivery_success=true`, or `primary_actions_enabled=true`
sources fail closed as blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2
trigger, WAVE ROVER feedback flow, WAVE ROVER HIL result, dropoff/cancel
completion, or delivery-success behavior.

Operator diagnostics may also expose `wave_rover_hil_packet_review_decision`,
`wave_rover_hil_packet_review_decision_summary`, and the Robot-compatible
`robot_diagnostics_wave_rover_hil_packet_review_decision_summary` alias from an
explicit `wave_rover_hil_packet_review_decision_ref`,
`TRASHBOT_WAVE_ROVER_HIL_PACKET_REVIEW_DECISION`,
`TRASHBOT_WAVE_ROVER_HIL_PACKET_REVIEW_DECISION_SUMMARY`, `latest_status`, or
an already sanitized diagnostics source. The source JSON must use
`schema=trashbot.wave_rover_hil_packet_review_decision.v1` or
`schema=trashbot.wave_rover_hil_packet_review_decision_summary.v1` with
`evidence_boundary=software_proof_docker_wave_rover_hil_packet_review_decision_gate`.
If the source is already a Robot diagnostics summary wrapper, it must still
point to the same source schema/evidence boundary. This field is metadata-only
Robot diagnostics support for the PC HIL packet review-decision gate; it does
not open serial, read raw packet files, subscribe to `/odom`, `/imu/data`, or
`/battery`, publish control topics, claim WAVE ROVER pass, or claim HIL. It may
expose only summary schema/evidence boundary, source schema/evidence boundary,
`overall_status`, `review_status`, `review_decision`, safe `evidence_ref`,
`accepted_required_materials`, `missing_required_materials`,
`rejected_required_materials`, `next_required_evidence`, `owner_handoff`,
`rerun_commands`, `not_proven`, and conservative boundary flags:
`metadata_only=true`, `real_hardware_observed=false`, `real_wave_rover=false`,
`real_uart=false`, `real_odom=false`, `real_imu=false`, `real_battery=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. It must also keep
`collect_triggered=false`, `dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false`. Missing, unreadable, bad JSON, missing schema,
unsupported schema or boundary, missing `overall_status=not_proven`, missing
`not_proven`, non-boolean or false `same_evidence_ref_required`,
`evidence_ref_match=false`, raw artifact/local paths, raw serial/UART path,
baudrate, checksum, credentials, traceback, raw packet/feedback payloads,
success copy, `delivery_success=true`, or `primary_actions_enabled=true`
sources fail closed as blocked/not_proven. The field does not change
`/api/collect`, `POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK,
remote control, cursor updates, persistence updates, terminal ACK, Nav2
trigger, WAVE ROVER feedback flow, WAVE ROVER HIL result, dropoff/cancel
completion, or delivery-success behavior.

Operator diagnostics may also expose `wave_rover_hil_packet_execution_pack`,
`wave_rover_hil_packet_execution_pack_summary`, and the Robot-compatible
`robot_diagnostics_wave_rover_hil_packet_execution_pack_summary` alias from an
explicit `wave_rover_hil_packet_execution_pack_ref`,
`TRASHBOT_WAVE_ROVER_HIL_PACKET_EXECUTION_PACK`,
`TRASHBOT_WAVE_ROVER_HIL_PACKET_EXECUTION_PACK_SUMMARY`, `latest_status`, or
an already sanitized diagnostics source. The source JSON must use
`schema=trashbot.wave_rover_hil_packet_execution_pack.v1` or
`schema=trashbot.wave_rover_hil_packet_execution_pack_summary.v1` with
`evidence_boundary=software_proof_docker_wave_rover_hil_packet_execution_pack_gate`.
If the source is already a Robot diagnostics summary wrapper, it must still
point to the same source schema/evidence boundary. This field is metadata-only
Robot diagnostics support for the Hardware worker's sanitized WAVE ROVER HIL
packet execution-pack handoff. It does not open serial, read raw packet files,
subscribe to `/odom`, `/imu/data`, or `/battery`, publish control topics, claim
WAVE ROVER pass, or claim HIL. It may expose only summary schema/evidence
boundary, source schema/evidence boundary, `overall_status`,
`execution_pack_status`, safe `evidence_ref`, `required_material_templates`,
`collection_sequence`, `owner_handoff`, `rerun_commands`, `boundary_flags`,
`not_proven`, and conservative boundary flags: `metadata_only=true`,
`real_hardware_observed=false`, `real_wave_rover=false`, `real_uart=false`,
`real_feedback_T1001=false`, `real_odom=false`, `real_imu=false`,
`real_battery=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. It must also keep
`collect_triggered=false`, `dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false`. Missing, unreadable, bad JSON, unsupported schema or
boundary, raw artifact/local paths, raw serial/UART path, baudrate, checksum,
credentials, traceback, raw packet/feedback payloads, success copy,
`delivery_success=true`, or `primary_actions_enabled=true` sources fail closed
as blocked/not_proven. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, WAVE ROVER
feedback flow, WAVE ROVER HIL result, dropoff/cancel completion, or
delivery-success behavior.

Operator diagnostics may also expose `hardware_baseline_review` and the alias
`hardware_baseline_review_summary` from an explicit
`hardware_baseline_review_ref`, `TRASHBOT_HARDWARE_BASELINE_REVIEW`,
`TRASHBOT_HARDWARE_BASELINE_REVIEW_SUMMARY`, `latest_status`, or an already
sanitized diagnostics source. The source JSON must use
`schema=trashbot.hardware_baseline_review_gate.v1` or
`schema=trashbot.hardware_baseline_review_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_baseline_review_gate`. If the
source is already a Robot diagnostics summary wrapper, it may either be the PC
`--summary-output` handoff schema itself or point to the same source
schema/evidence boundary. This field is metadata-only Robot diagnostics support
for consuming an Autonomy/Hardware baseline-review artifact or summary. It may
expose only the summary schema/evidence boundary, source schema/evidence
boundary, `review_status`, `hardware_material_status=hardware_material_pending`,
`blockers`, `next_required_evidence`, `review_summary`, safe evidence ref,
`operator_next_steps`, `robot_diagnostics_summary`, `not_proven`, and
conservative false fields including `real_hardware_observed=false`,
`route_elevator_field_pass=false`, `nav2_fixed_route_run=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 or fixed-route trigger, not a hardware action, not
HIL, and not delivery success. Diagnostics consumers must treat it as fence-only
metadata: `metadata_only=true`, `review_status.verdict=not_proven`,
`review_status.evidence_source=software_proof`,
`hardware_material_pending=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a hardware baseline review source is present. Raw sensor
configuration, device paths, frame ids, thresholds, channel counts, local paths,
credentials, raw ACK payloads, raw command envelopes, success copy, and
traceback content must not enter the diagnostics summary. Missing, unreadable,
bad JSON, unsupported-schema, boundary-mismatch, `real_hardware_observed=true`,
`route_elevator_field_pass=true`, `nav2_fixed_route_run=true`,
`delivery_success=true`, `primary_actions_enabled=true`, or success wording
sources remain blocked/not_proven. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, or delivery-success behavior, and it 不证明真实硬件材料、真实传感器、真实
Nav2/fixed-route、真实 HIL 或 delivery success。

Operator diagnostics may also expose `hardware_baseline_source_alignment` and
the alias `hardware_baseline_source_alignment_summary` from an explicit
`hardware_baseline_source_alignment_ref`,
`TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT`,
`TRASHBOT_HARDWARE_BASELINE_SOURCE_ALIGNMENT_SUMMARY`, `latest_status`, or an
already sanitized diagnostics source. The source JSON must use
`schema=trashbot.hardware_baseline_source_alignment.v1` or
`schema=trashbot.hardware_baseline_source_alignment_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_baseline_source_alignment_gate`.
If the source is already a Robot diagnostics summary wrapper, it must point back
to the same source schema/evidence boundary; the Hardware gate `--summary-output`
shape is also accepted when it preserves
`source_schema=trashbot.hardware_baseline_source_alignment.v1` and the same
`evidence_boundary` even if it omits `source_evidence_boundary`. This field is metadata-only Robot
diagnostics support for consuming a Hardware-owned baseline/source-alignment
artifact or summary. It may expose only the summary schema/evidence boundary,
source schema/evidence boundary, `source_contract`, `alignment_status`,
`source_alignment_status`, `hardware_material_status=hardware_material_pending`,
`blockers`, `baseline_source_summary`, `default_hardware_set_summary`,
`target_sensor_baseline_summary`, `vendor_source_boundary`,
`missing_alignment_items`, `source_inventory_summary`, `unresolved_sources`,
safe evidence ref, `owner_handoff`,
`next_required_evidence`, `operator_next_steps`, `robot_diagnostics_summary`,
`not_proven`, and conservative false fields including
`source_alignment_reviewed=false`, `sensor_procurement_completed=false`,
`sensor_installed_on_robot=false`, `sensor_wiring_verified=false`,
`sensor_power_budget_verified=false`, `route_elevator_field_pass=false`,
`nav2_fixed_route_run=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. It is not a `trashbot.remote.v1`
command/status/ACK envelope, not an ACK POST, not remote control authorization,
not a cursor or persistence instruction, not a terminal ACK, not a Nav2 or
fixed-route trigger, not a hardware action, not HIL, and not delivery success.
Diagnostics consumers must treat it as fence-only metadata:
`metadata_only=true`, `alignment_status.verdict=not_proven`,
`alignment_status.evidence_source=software_proof`, `hardware_material_pending=true`,
`collect_triggered=false`, `dropoff_triggered=false`, `cancel_triggered=false`,
`ack_post_allowed=false`, `remote_ack_allowed=false`,
`cursor_updates_allowed=false`, `persistence_updates_allowed=false`,
`terminal_ack_allowed=false`, `nav2_triggered=false`, `hil_pass=false`, and
`production_ready=false` remain required even when a source-alignment artifact
is present. Raw paths, credentials, serial/UART/baud details, hardware detail,
raw ACK payloads, raw command/status envelopes, WAVE ROVER details, success
copy, control copy, field-pass wording, and traceback content must not enter the
diagnostics summary. Missing, unreadable, bad JSON, unsupported-schema,
boundary-mismatch, `delivery_success=true`, `primary_actions_enabled=true`,
hardware/control/HIL/field-pass claims, or success wording sources remain
blocked/not_proven. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, or delivery-success behavior, and it 不证明真实硬件材料来源、真实传感器、
真实接线/供电、真实 Nav2/fixed-route、真实 HIL 或 delivery success。

Operator diagnostics may also expose `hardware_sensor_procurement_intake` and
the alias `hardware_sensor_procurement_intake_summary` from an explicit
`hardware_sensor_procurement_intake_ref`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_INTAKE_SUMMARY`, `latest_status`, or an
already sanitized diagnostics source. The source JSON must use
`schema=trashbot.hardware_sensor_procurement_intake_gate.v1` or
`schema=trashbot.hardware_sensor_procurement_intake_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_sensor_procurement_intake_gate`.
If the source is already a Robot diagnostics summary wrapper, it may either be
the PC `--summary-output` handoff schema itself or point to the same source
schema/evidence boundary. This field is metadata-only Robot diagnostics support
for consuming a Hardware-owned sensor-procurement intake artifact or summary.
It may expose only the summary schema/evidence boundary, source schema/evidence
boundary, `intake_status`, `hardware_material_status=hardware_material_pending`,
`blockers`, `next_required_evidence`, `procurement_summary`,
whitelisted `sensor_responsibility_summary` rows, safe evidence ref,
`operator_next_steps`, `robot_diagnostics_summary`, `not_proven`, and
conservative false fields including `real_hardware_observed=false`,
`sensor_procurement_completed=false`, `sensor_installed_on_robot=false`,
`route_elevator_field_pass=false`, `nav2_fixed_route_run=false`,
`dropoff_completion=false`, `cancel_completion=false`,
`delivery_success=false`, and `primary_actions_enabled=false`.
It is not a `trashbot.remote.v1` command/status/ACK envelope, not an ACK POST,
not remote control authorization, not a cursor or persistence instruction, not
a terminal ACK, not a Nav2 or fixed-route trigger, not a hardware action, not
HIL, not dropoff/cancel completion, and not delivery success. Diagnostics
consumers must treat it as fence-only metadata: `metadata_only=true`,
`intake_status.verdict=not_proven`,
`intake_status.evidence_source=software_proof`,
`hardware_material_pending=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a hardware sensor procurement intake source is present. Raw
artifact payloads, raw JSON, raw ROS topics, serial/UART details, baudrate,
hardware paths, credentials, checksums, full vendor/source documents, raw ACK
payloads, raw command envelopes, success copy, and traceback content must not
enter the diagnostics summary. Missing, unreadable, bad JSON,
unsupported-schema, boundary-mismatch, `real_hardware_observed=true`,
`sensor_procurement_completed=true`, `sensor_installed_on_robot=true`,
`route_elevator_field_pass=true`, `nav2_fixed_route_run=true`,
`dropoff_completion=true`, `cancel_completion=true`, `delivery_success=true`,
`primary_actions_enabled=true`, or success/control wording sources remain
blocked/not_proven. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, dropoff/cancel completion, or delivery-success behavior, and it
不证明真实传感器采购、真实装机、真实 Nav2/fixed-route、真实 HIL 或 delivery success。

Operator diagnostics may also expose `hardware_sensor_procurement_review_decision`
and the alias `hardware_sensor_procurement_review_decision_summary` from an
explicit `hardware_sensor_procurement_review_decision_ref`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_REVIEW_DECISION_SUMMARY`,
`latest_status`, or an already sanitized diagnostics source. The source JSON
must use `schema=trashbot.hardware_sensor_procurement_review_decision.v1` or
`schema=trashbot.hardware_sensor_procurement_review_decision_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_sensor_procurement_review_decision_gate`.
If the source is already a Robot diagnostics summary wrapper, it may point back
to the same source schema/evidence boundary. This field is metadata-only Robot
diagnostics support for consuming a Hardware-owned sensor-procurement review
decision summary. It may expose only summary schema/evidence boundary, source
schema/evidence boundary, `review_decision_status`,
`hardware_material_status=hardware_material_pending`, `blockers`,
`next_required_evidence`, `review_decision_summary`, `owner_handoff`,
`rerun_commands`, safe evidence ref, `operator_next_steps`,
`robot_diagnostics_summary`, `not_proven`, and conservative false fields
including `real_hardware_observed=false`, `sensor_procurement_completed=false`,
`sensor_installed_on_robot=false`, `route_elevator_field_pass=false`,
`nav2_fixed_route_run=false`, `dropoff_completion=false`,
`cancel_completion=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing or unconfigured sources fail closed as
`blocked_missing_hardware_sensor_procurement_review_decision`; unreadable JSON
uses `read_error`, unsupported schema/boundary uses `unsupported_schema`, and
success/control claims use `unsafe_fields`. Diagnostics consumers must treat it
as fence-only metadata: `metadata_only=true`,
`review_decision_status.verdict=not_proven`,
`review_decision_status.evidence_source=software_proof`,
`hardware_material_pending=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a review decision source is present. Raw artifact payloads,
raw JSON, raw ROS topics, serial/UART details, baudrate, hardware paths,
credentials, checksums, full vendor/source documents, raw ACK payloads, raw
command envelopes, success copy, and traceback content must not enter the
diagnostics summary. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, dropoff/cancel completion, or delivery-success behavior, and it
不证明真实传感器采购、真实装机、真实 Nav2/fixed-route、真实 HIL 或 delivery success。

Operator diagnostics may also expose `hardware_sensor_procurement_execution_pack`
and the alias `hardware_sensor_procurement_execution_pack_summary` from an
explicit `hardware_sensor_procurement_execution_pack_ref`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_EXECUTION_PACK_SUMMARY`,
`latest_status`, or an already sanitized diagnostics source. The source JSON
must use `schema=trashbot.hardware_sensor_procurement_execution_pack.v1` or
`schema=trashbot.hardware_sensor_procurement_execution_pack_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_sensor_procurement_execution_pack_gate`.
If the source is already a Robot diagnostics summary wrapper, it may point back
to the same source schema/evidence boundary. This field is metadata-only Robot
diagnostics support for consuming a Hardware-owned sensor-procurement execution
pack. It may expose only summary schema/evidence boundary, source
schema/evidence boundary, `execution_pack_status`,
`hardware_material_status=hardware_material_pending`, `blockers`,
`material_templates`, `owner_handoff`, `rerun_commands`, `blocked_reason`,
`next_required_evidence`, safe evidence ref, `operator_next_steps`,
`robot_diagnostics_summary`, `not_proven`, and conservative false fields
including `real_hardware_observed=false`, `sensor_procurement_completed=false`,
`sensor_installed_on_robot=false`, `sensor_calibrated_on_robot=false`,
`route_elevator_field_pass=false`, `nav2_fixed_route_run=false`,
`dropoff_completion=false`, `cancel_completion=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. Missing or
unconfigured sources fail closed as
`blocked_missing_hardware_sensor_procurement_execution_pack`; unreadable JSON
uses `read_error`, unsupported schema/boundary uses `unsupported_schema`, and
success/control claims use `unsafe_fields`. Diagnostics consumers must treat it
as fence-only metadata: `metadata_only=true`,
`execution_pack_status.verdict=not_proven`,
`execution_pack_status.evidence_source=software_proof`,
`hardware_material_pending=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when an execution pack source is present. Raw artifact payloads,
raw JSON, raw ROS topics, serial/UART details, baudrate, hardware paths,
credentials, checksums, full vendor/source documents, raw ACK payloads, raw
command envelopes, success copy, and traceback content must not enter the
diagnostics summary. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, dropoff/cancel completion, or delivery-success behavior, and it
不证明真实传感器采购、真实装机、真实校准、真实 Nav2/fixed-route、真实 HIL 或 delivery success。

Operator diagnostics may also expose `hardware_sensor_procurement_receipt_intake`
and the alias `hardware_sensor_procurement_receipt_intake_summary` from an
explicit `hardware_sensor_procurement_receipt_intake_ref`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE`,
`TRASHBOT_HARDWARE_SENSOR_PROCUREMENT_RECEIPT_INTAKE_SUMMARY`,
`latest_status`, or an already sanitized diagnostics source. The source JSON
must use `schema=trashbot.hardware_sensor_procurement_receipt_intake.v1` or
`schema=trashbot.hardware_sensor_procurement_receipt_intake_summary.v1` with
`evidence_boundary=software_proof_docker_hardware_sensor_procurement_receipt_intake_gate`.
If the source is already a Robot diagnostics summary wrapper, it must point
back to the same source schema/evidence boundary. This field is metadata-only
Robot diagnostics support for consuming a Hardware-owned sensor-procurement
receipt intake gate. It may expose only summary schema/evidence boundary,
source schema/evidence boundary, `receipt_intake_status`,
`hardware_material_status=hardware_material_pending`, `material_status`,
`blockers`, `accepted_materials`, `missing_materials`, `rejected_materials`,
`owner_handoff`, `next_required_evidence`, safe evidence ref,
`operator_next_steps`, `robot_diagnostics_summary`, `not_proven`, and
conservative false fields including `real_hardware_observed=false`,
`sensor_receipt_verified=false`, `sensor_procurement_completed=false`,
`sensor_installed_on_robot=false`, `sensor_wiring_verified=false`,
`sensor_power_budget_verified=false`, `sensor_calibrated_on_robot=false`,
`route_elevator_field_pass=false`, `nav2_fixed_route_run=false`,
`dropoff_completion=false`, `cancel_completion=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. Missing,
unconfigured, unreadable, unsupported schema/boundary, unsafe copy, weak
contract, or success/control claims fail closed as
`blocked_missing_hardware_sensor_procurement_receipt_intake`. Diagnostics
consumers must treat it as fence-only metadata: `metadata_only=true`,
`receipt_intake_status.verdict=not_proven`,
`receipt_intake_status.evidence_source=software_proof`,
`hardware_material_pending=true`, `collect_triggered=false`,
`dropoff_triggered=false`, `cancel_triggered=false`, `ack_post_allowed=false`,
`remote_ack_allowed=false`, `cursor_updates_allowed=false`,
`persistence_updates_allowed=false`, `terminal_ack_allowed=false`,
`nav2_triggered=false`, `hil_pass=false`, and `production_ready=false` remain
required even when a receipt intake source is present. Raw artifact payloads,
raw JSON, raw ROS topics, serial/UART details, baudrate, hardware paths,
credentials, checksums, full vendor/source documents, raw ACK payloads, raw
command envelopes, success copy, and traceback content must not enter the
diagnostics summary. The field does not change `/api/collect`,
`POST /api/dropoff/confirm`, `POST /api/cancel`, command, ACK, remote control,
cursor updates, persistence updates, terminal ACK, Nav2 trigger, HIL, hardware
action, dropoff/cancel completion, or delivery-success behavior, and it
不证明真实采购、真实收货、真实装机、真实接线、真实电源预算、真实校准、真实 Nav2/fixed-route、真实 HIL 或 delivery success。

### Dropoff Confirmation Service

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/confirm_dropoff` | `std_srvs/srv/SetBool` | Valid only while a `manual_confirm` dropoff is pending. `request.data=true` confirms the user has removed or disposed of the load. `request.data=false` rejects the dropoff and the delivery action fails. `response.success=false` means no dropoff confirmation was pending. |

### Operator Gateway

The optional `operator_gateway` node exposes a local HTTP API for phone or browser control without requiring SSH or ROS2 CLI access.

| Endpoint | Method | Contract |
| --- | --- | --- |
| `/api/status` | GET | Returns `state`, `message`, `updated_at`, and the latest task metadata such as `task_record_path`, `error_message`, progress, or target when available. |
| `/api/diagnostics` | GET | Returns the minimum remote-support diagnostic package: software version, map/route versions, latest status, last task summary, terminal failure fields, route proof summary + mapped route proof state, log references, vision sample manifest reference, hardware proof summary, and operator status file path. |
| `/api/vision/review-queue` | GET | Returns review queue samples with `review_status` and `last_decision` summary, plus progress aggregates (`progress_summary`), decision distribution (`decision_distribution`), and `next_pending_sample` for quick operator focus. Queue/manifest errors are returned as structured fields instead of breaking the operator main flow. |
| `/api/vision/review-decisions` | POST | Stores a manual review decision for one sample. Required fields: `sample_id`, `decision` (`approved`, `rejected`, `needs_retry`). Optional: `comment`, `option`, `operator`. |
| `/api/collect` | POST | Starts `/trashbot/collect_trash`. Optional JSON body or query parameter `target` overrides the default delivery target. |
| `/api/dropoff/confirm` | POST | Calls `/trashbot/confirm_dropoff`; optional JSON `accepted=false` rejects a pending manual dropoff. |
| `/api/cancel` | POST | Cancels the active `collect_trash` action goal if one is running. |

Every status-style response generated by the gateway includes:

| Field | Contract |
| --- | --- |
| `phone_copy` | Plain-language phone UI copy for the current state; clients should display this instead of parsing ROS-oriented status text. |
| `speaker_prompt` | Short prompt suitable for a speaker, buzzer/voice layer, or phone text-to-speech. |
| `phone_readiness` | `/api/status` aggregation for phone-first readiness. It is derived from local delivery status, action permissions, local/mock `remote_readiness`, optional cloud preflight, and optional backup/restore drill summaries. Older clients may ignore it. |
| `phone_support_bundle` | Phone-safe support handoff package for failed, blocked, waiting-ACK, or human-takeover states. It reuses the same status/readiness/diagnostics summaries and filters credentials, raw ROS topics, motion-control internals, hardware parameters, local paths, tracebacks, checksums, and complete artifacts. |
| `operation_log` / `phone_operation_log` | Phone-safe operation/support event metadata for recent user actions, blocked reasons, pending ACK, offline/recovery, manual takeover, and support handoff. It is not a ROS2 action, service, topic, ACK, cursor, Nav2/fixed-route result, WAVE ROVER feedback, or delivery-success surface. |
| `mobile_action_confirmation` / `mobile_action_receipt` / `phone_action_feedback` | Phone-safe action confirmation and receipt metadata for Start/Confirm/Cancel UI feedback. These fields summarize accepted/processing state, blocked reasons, or recovery copy for the phone; they are not `trashbot.remote.v1` command/status/ACK envelope fields and must not trigger robot actions, ACK, cursor updates, or delivery-success claims. |
| `mobile_terminal_action_confirmation_gate` / `mobile_terminal_action_confirmation_summary` | Phone/support metadata for Confirm Dropoff / Cancel terminal-action two-step confirmation. These fields may include action, risk copy, ACK semantics, client reference, evidence boundary, `not_proven`, and safe phone copy; they are not robot commands, ACKs, cursor instructions, delivery success, dropoff success, cancel completion, production readiness, or HIL evidence. |
| `mobile_primary_journey_gate` / `mobile_primary_journey_summary` | Phone/support metadata for the mobile primary journey summary. It may include destination, load-confirmation requirement, command-safety summary, browser/device/cloud gates, operation-log/action-feedback summaries, and `not_proven` items, but it is not a robot command, ACK, cursor, delivery success, dropoff success, cancel completion, production-readiness proof, or HIL proof. |
| `mobile_recovery_decision_gate` / `mobile_recovery_decision_summary` | Phone/support metadata for the mobile recovery decision panel. It may include recovery state, next action, blocking reason, support entry, ACK semantics, evidence boundary, and `not_proven` items, but it is not a robot command, ACK, cursor, delivery success, dropoff success, cancel completion, production-readiness proof, or HIL proof. |
| `mobile_device_acceptance_readiness` / `phone_device_acceptance_readiness` / `mobile_browser_acceptance_readiness` | Phone/browser acceptance metadata for device/browser readiness panels. These fields are support metadata only: they are not `trashbot.remote.v1` command/status/ACK envelope fields, not ROS2 actions or services, and must not trigger `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, cursor updates, or delivery-success claims. |
| `mobile_browser_acceptance_bundle` / `phone_browser_acceptance_bundle` / `mobile_acceptance_evidence_bundle` | Phone/browser acceptance-bundle metadata for browser viewport, touch, PWA/offline, diagnostics, cloud/action gates, safe copy, and evidence-boundary summaries. These fields are consumed by mobile UI and diagnostics only; the robot control loop must ignore them and must not turn them into commands, status, ACK, cursor, hardware, HIL, or delivery-success evidence. |
| `mobile_web_browser_proof` / `phone_browser_proof` / `mobile_browser_proof_summary` | Phone/browser proof metadata for the `software_proof_docker_mobile_web_browser_proof_gate` evidence boundary. It may summarize local Chromium-family browser evidence, screenshots, safe copy, ACK semantics, and not-proven items, but it is not a `trashbot.remote.v1` command/status/ACK envelope, ROS action, HIL result, or delivery-success surface. |
| `mobile_current_pwa_browser_proof_refresh` / `mobile_current_pwa_browser_proof_refresh_summary` / `phone_current_pwa_browser_proof_refresh` | Phone/browser proof refresh metadata for the `software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate` evidence boundary. It may summarize current `mobile/web/` PWA viewport evidence, screenshot/JSON refs, safe copy, ACK semantics, and not-proven items, but it is not a `trashbot.remote.v1` command/status/ACK envelope, cursor input, ROS action, production-readiness result, HIL result, real phone/browser proof, Start/Confirm/Cancel enablement source, or delivery-success surface. |
| `mobile_current_pwa_retest_browser_proof` / `mobile_current_pwa_retest_browser_proof_summary` / `phone_current_pwa_retest_browser_proof` | Phone/browser retest proof metadata for the `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate` evidence boundary. It may summarize current `mobile/web/` PWA viewport evidence, retest-request panel visibility, screenshot/JSON refs, safe copy, ACK semantics, and not-proven items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real phone/browser proof, real device retest completion, Start/Confirm/Cancel enablement, dropoff/cancel completion, or delivery success. |
| `mobile_current_pwa_field_trial_browser_proof` / `mobile_current_pwa_field_trial_browser_proof_summary` / `mobile_current_pwa_field_trial_browser_proof_copy` | Phone/browser field-trial proof metadata for the `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate` evidence boundary. It may summarize current `mobile/web/` PWA field-trial viewport evidence, screenshot/JSON refs, safe copy, ACK semantics, and `not_proven` items, but it is `software_proof` metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, O5 external proof, HIL, real phone proof, Start/Confirm/Cancel enablement, dropoff/cancel completion, or delivery success. |
| `mobile_real_device_evidence_intake` / `mobile_real_device_evidence_intake_summary` / `mobile_real_device_evidence_package` | Phone/support metadata for the `software_proof_docker_mobile_real_device_evidence_intake_gate` boundary. It may summarize真实手机设备、browser、viewport、display mode、PWA install prompt/user choice、production app readiness, screenshot/URL summaries, redaction, and `not_proven` items, but it is metadata-only: not command, status, ACK, cursor, production readiness, HIL, real device proof, control enablement, or delivery success. |
| `mobile_real_device_acceptance_decision` / `mobile_real_device_acceptance_decision_summary` / `mobile_real_device_acceptance_decision_package` | Phone/support metadata for the `software_proof_docker_mobile_real_device_acceptance_decision_gate` boundary. It may summarize a real-device acceptance decision, reviewer outcome, evidence refs, safe copy, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_review_handoff` / `mobile_real_device_review_handoff_summary` / `mobile_real_device_review_handoff_package` | Phone/support/product review-handoff metadata for the `software_proof_docker_mobile_real_device_review_handoff_gate` boundary. It may summarize reviewer routing, evidence refs, safe copy, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_retest_request` / `mobile_real_device_retest_request_summary` / `mobile_real_device_retest_request_package` | Phone/support/product retest-request metadata for the `software_proof_docker_mobile_real_device_retest_request_gate` boundary. It may summarize missing evidence, owner, next action, blocked/rejected reason, redaction/source boundary, ACK-not-delivery copy, and `not_proven` items for the next real-device retest, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_acceptance_session` / `mobile_real_device_field_trial_acceptance_session_summary` / `mobile_real_device_field_trial_acceptance_session_copy` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate` boundary. It may summarize a field-trial acceptance session, observer notes, safe copy, ACK-not-delivery semantics, and `not_proven` items, but it is `software_proof` metadata-only: not command, status, ACK, ACK POST, terminal ACK, cursor, production readiness, O5 external proof, HIL, real phone proof, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_review` / `mobile_real_device_field_trial_review_summary` / `mobile_real_device_field_trial_review_copy` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_review_gate` boundary. It may summarize real-device field-trial material review, missing evidence, redaction status, safe copy, ACK-not-delivery semantics, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_runbook_execution` / `mobile_real_device_field_trial_runbook_execution_summary` / `mobile_real_device_field_trial_runbook_execution_copy` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate` boundary. It may summarize runbook step execution, operator observations, safe copy, ACK-not-delivery semantics, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_retest_execution` / `mobile_real_device_field_trial_retest_execution_summary` / `mobile_real_device_field_trial_retest_execution_copy` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_retest_execution_gate` boundary. It may summarize field-trial retest step execution, operator observations, safe copy, ACK-not-delivery semantics, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_evidence_record` / `mobile_real_device_field_trial_evidence_record_summary` / `mobile_real_device_field_trial_evidence_record_copy` / `mobile_real_device_field_trial_evidence_record_archive` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate` boundary. It may summarize real-device field-trial observations, production-app/PWA prompt notes, redaction state, safe copy/archive refs, ACK-not-delivery semantics, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_evidence_verdict` / `mobile_real_device_field_trial_evidence_verdict_summary` / `mobile_real_device_field_trial_evidence_verdict_copy` | Phone/support/product metadata for the `software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate` boundary. It may summarize field-trial evidence review verdicts, missing material, retest requests, safe copy, ACK-not-delivery semantics, and `not_proven` items, but it is metadata-only: not command, status, ACK, terminal ACK, cursor, production readiness, HIL, real robot proof, dropoff success, cancel completion, or delivery success. |
| `mobile_real_device_field_trial_acceptance_execution_callback_review_decision` / `mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary` | Robot diagnostics metadata-only consumer for `trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_decision.v1` / `trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_decision_summary.v1` under `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_decision_gate`. It may expose only source callback intake status, accepted/missing/rejected callback evidence, same safe evidence ref, review decision, decision reasons, owner handoff, next required evidence, rerun guidance, `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`; missing fields, schema or boundary mismatch, unsafe evidence ref, missing/rejected callback material, unsafe copy, raw artifacts, credentials, ROS topics, serial/UART details, `/cmd_vel`, success/control copy, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` fail closed as blocked/not_proven. It never triggers ACK, cursor updates, Start Delivery, Confirm Dropoff, Cancel, diagnostics fetch, robot command, ROS control, HIL, real phone/browser proof, Objective 5 external proof, route/elevator pass, dropoff/cancel completion, or delivery success. |
| `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff` / `mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary` / `robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary` | Robot diagnostics metadata-only consumer for `trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff.v1` / `trashbot.mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_summary.v1` under `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_review_handoff_gate`. It may expose only source callback review decision status, handoff status, owner handoff, next required evidence, rerun guidance, blocker summary, the same safe evidence ref, evidence boundary, `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`; missing source review decision, missing safe evidence ref, schema or boundary mismatch, unsafe copy, raw artifacts, cursor/ACK payloads, local paths, credentials, complete artifacts, checksums, success/pass/control copy, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` fail closed as blocked/not_proven. It never triggers ACK, cursor updates, Start Delivery, Confirm Dropoff, Cancel, diagnostics fetch, robot command, ROS control, HIL, real phone/browser proof, Objective 5 external proof, Objective 1 HIL/material closure, route/elevator field pass, dropoff/cancel completion, or delivery success. |
| `route_task_field_retest_acceptance_execution_callback_review_decision` / `route_task_field_retest_acceptance_execution_callback_review_decision_summary` / `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_decision_summary` | Robot diagnostics metadata-only consumer for `trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1` under `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`. It may summarize review decision, source callback intake status, safe evidence ref, owner handoff, next required evidence, rerun commands or hint, boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema or boundary, unsafe raw fields, evidence-ref mismatch, enabled actions, success claims, or control claims. It is not a command, ACK, cursor, ROS control, Nav2, HIL pass, Start/Confirm/Cancel enablement source, real phone/browser proof, Objective 5 external proof, dropoff/cancel completion, or delivery success. |
| `route_task_field_retest_acceptance_execution_callback_review_handoff` / `route_task_field_retest_acceptance_execution_callback_review_handoff_summary` / `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary` | Robot diagnostics metadata-only consumer for `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1` / `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1` under `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`. It may summarize handoff status, source review decision/status, safe evidence ref, owner handoff, next required evidence, safe rerun hint, boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema or boundary, unsafe raw fields, evidence-ref mismatch, enabled actions, success claims, or control claims. It is not a command, ACK, cursor, ROS control, Nav2, HIL pass, Start/Confirm/Cancel enablement source, real phone/browser proof, Objective 5 external proof, dropoff/cancel completion, or delivery success. |
| `route_task_field_retest_acceptance_execution_handoff_intake` / `route_task_field_retest_acceptance_execution_handoff_intake_summary` / `robot_diagnostics_route_task_field_retest_acceptance_execution_handoff_intake_summary` | Robot diagnostics metadata-only consumer for `trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1` / `trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1` under `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`. It may summarize handoff intake status, source handoff status, safe evidence ref, owner acknowledgement state, owner handoff, next required evidence, safe rerun hint, boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema or boundary, unsafe raw fields, evidence-ref mismatch, enabled actions, success claims, or control claims. It is not a command, ACK, cursor, ROS control, Nav2, HIL pass, Start/Confirm/Cancel enablement source, real phone/browser proof, Objective 5 external proof, dropoff/cancel completion, or delivery success. |
| `route_task_field_retest_acceptance_execution_rerun_result_review_handoff` / `route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary` / `robot_diagnostics_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary` | Robot diagnostics metadata-only consumer for `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1` under `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`. It may summarize handoff status, safe evidence ref, owner role, owner handoff, next required evidence, boundary flags, `source=software_proof`, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema or boundary, unsafe raw fields or copy, material-directory access, evidence-ref mismatch, enabled actions, success claims, or control claims. It is not a command, ACK, cursor, ROS runtime, ROS control, Nav2/fixed-route proof, route completion, dropoff/cancel completion, HIL pass, Start/Confirm/Cancel enablement source, real phone/browser proof, Objective 5 external proof, delivery result, or delivery success. |
| `hardware_sensor_hil_entry_config_precheck` / `hardware_sensor_hil_entry_config_precheck_summary` / `hardware_sensor_hil_entry_config_precheck_copy` | Robot diagnostics metadata-only consumer for `trashbot.hardware_sensor_hil_entry_config_precheck.v1` / `trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1` under `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`. It may summarize safe evidence ref, sensor config summary, missing config/material categories, next required evidence, owner handoff, safe copy, evidence boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema, unsafe raw fields, success claims, or weak evidence boundary. It is not a command, ACK, cursor, ROS control, raw artifact reader, HIL pass, real 2D LiDAR/ToF proof, Start/Confirm/Cancel enablement source, dropoff/cancel completion, or delivery success. |
| `hardware_sensor_hil_entry_readiness_review` / `hardware_sensor_hil_entry_readiness_review_summary` / `hardware_sensor_hil_entry_readiness_review_copy` | Robot diagnostics metadata-only consumer for `trashbot.hardware_sensor_hil_entry_readiness_review.v1` / `trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1` under `software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate`. It may summarize safe evidence ref, readiness review status, readiness gates, accepted/missing/rejected materials, next required evidence, owner handoff, rerun commands, safe copy, evidence boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, unsupported schema, unsafe raw fields, success claims, or weak evidence boundary. It is not a command, ACK, cursor, ROS control, raw artifact reader, HIL pass, real 2D LiDAR/ToF proof, Start/Confirm/Cancel enablement source, dropoff/cancel completion, or delivery success. |
| `hardware_sensor_hil_entry_execution_pack` / `hardware_sensor_hil_entry_execution_pack_summary` | Robot diagnostics metadata-only consumer for `trashbot.hardware_sensor_hil_entry_execution_pack.v1` / `trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1` under `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`. It may summarize status, safe `evidence_ref`, required/missing materials, `next_required_evidence`, `owner_handoff`, `rerun_commands`, boundary, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`, but it must fail closed on missing summary, `unsupported_schema`, bad boundary, weak evidence ref, unsafe success/control/HIL/field/procurement/install/wiring claims, raw artifact, full local paths, credentials, serial/UART raw paths, OSS/DB/queue/token material. It is metadata-only: not collect, dropoff, cancel, ACK, cursor, Nav2, HIL pass, real 2D LiDAR/ToF proof, Start/Confirm/Cancel enablement source, dropoff/cancel completion, or delivery success. |
| `pr5_review_thread_closeout` / `pr5_review_thread_closeout_summary` / `robot_diagnostics_pr5_review_thread_closeout_summary` | Robot diagnostics metadata-only consumer for Hardware gate output `trashbot.pr5_review_thread_closeout.v1` / `trashbot.pr5_review_thread_closeout_summary.v1` under `software_proof_docker_pr5_review_thread_closeout_gate`. It may expose only sanitized PR #5 review thread decision status, safe evidence ref, safe current evidence refs, missing real 2D LiDAR / ToF / install / wiring / power / calibration / HIL-entry materials, owner handoff, next required evidence, `software_proof`, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`. Missing sanitized summary, unsupported schema or boundary, unsafe copy/raw review body, success wording, `delivery_success=true`, or `primary_actions_enabled=true` must fail closed. It is not a command, ACK, cursor, ROS control, `/cmd_vel`, Start Delivery, Confirm Dropoff, Cancel, Nav2, WAVE ROVER, HIL pass, real sensor material proof, route/elevator field pass, Objective 5 external proof, dropoff/cancel completion, or delivery success. |
| `mobile_device_handoff_session` / `mobile_device_handoff_session_summary` / `mobile_device_handoff_package` | Phone/support handoff-session metadata for the `software_proof_docker_mobile_device_handoff_session_gate` evidence boundary. It may summarize a support handoff session, safe copy, client references, and package metadata, but it is not command, ACK, cursor, delivery result, production readiness, HIL, real device proof, or a Start/Confirm/Cancel enablement source. |
| `mobile_pwa_install_prompt_evidence` / `mobile_pwa_install_prompt_evidence_summary` / `mobile_pwa_install_prompt_evidence_package` | Phone/support metadata for the `software_proof_docker_mobile_pwa_install_prompt_evidence_gate` evidence boundary. It may summarize install-prompt capture status, user outcome, display mode, manifest/service-worker/offline-shell state, linked handoff/device evidence, safe copy, and `not_proven` items, but it is not command, ACK, cursor, delivery result, production readiness, HIL, real device proof, real PWA install prompt proof, or a Start/Confirm/Cancel enablement source. |
| `mobile_pwa_install_prompt_event_capture` / `mobile_pwa_install_prompt_event_capture_summary` / `mobile_pwa_install_prompt_event_capture_copy` | Phone/support metadata for the `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate` evidence boundary. It may summarize local PWA install-prompt event capture, browser event timing, user-choice copy, safe copy, and `not_proven` items, but it is `software_proof` metadata-only: not command, ACK, ACK POST, terminal ACK, cursor, production readiness, O5 external proof, HIL, real phone proof, dropoff/cancel completion, or delivery success. |
| `mobile_pwa_install_prompt_evidence_export` / `mobile_pwa_install_prompt_evidence_export_summary` / `mobile_pwa_install_prompt_evidence_export_copy` | Phone/support metadata for the `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate` evidence boundary. It may summarize PWA install-prompt evidence export/copy state, safe copy, redacted evidence refs, ACK-not-delivery semantics, and `not_proven` items, but it is `software_proof` metadata-only: not command, ACK, ACK POST, terminal ACK, cursor, production readiness, O5 external proof, HIL, real phone proof, dropoff/cancel completion, or delivery success. |
| `oss_cdn_live_probe` / `oss_cdn_live_probe_artifact` / `cdn_live_probe` | Phone/support metadata for OSS/CDN live probe readiness. These fields may summarize blocked probe status, redacted endpoint/object evidence, and recovery copy, but they are not `trashbot.remote.v1` command/status/ACK envelope fields and must not trigger `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, cursor updates, persisted `last_terminal_ack_id`, or delivery-success claims. |
| `voice_prompt_readiness` | Phone-safe prompt readiness package for the current `speaker_prompt`/elevator-assist prompt. It is exposed at top-level `/api/status`, nested as `phone_readiness.voice_prompt_readiness`, and mirrored in `/api/diagnostics.voice_prompt_readiness`. |
| `phone_offline_resume_readiness` | Phone-safe offline/resume package for reconnect, stale status, pending ACK, command safety, support handoff, offline shell behavior, and ACK semantics. It is exposed at top-level `/api/status`, nested as `phone_readiness.phone_offline_resume_readiness`, and mirrored in `/api/diagnostics.phone_offline_resume_readiness`. |

### Mobile Web Consumer

`mobile/web/` is the dependency-free phone PWA consumer for the operator/remote phone-safe contract. It is a consumer only and does not change ROS2 action, service, topic, or `trashbot.remote.v1` command/status/ack semantics.

Runtime files:

| File | Contract |
| --- | --- |
| `mobile/web/index.html` | Phone-first static entrypoint. It starts with primary actions disabled and waits for `/api/status`. |
| `mobile/web/app.js` | Reads `/api/status` and `/api/diagnostics`; renders `phone_readiness`, `command_safety`, `phone_offline_resume_readiness`, optional task-flow/support/voice summaries, and sanitized diagnostics fields. |
| `mobile/web/manifest.webmanifest` | PWA metadata for the static shell. `evidence_boundary=software_proof_docker_mobile_web_entrypoint_gate`. |
| `mobile/web/service-worker.js` | Caches only static shell files and bypasses dynamic control traffic. |
| `mobile/web/offline.html` | Offline recovery shell. Start Delivery, Confirm Dropoff, and Cancel remain disabled. |
| `mobile/fixtures/mobile_web_status.fixture.json` | Static smoke fixture only; must remain marked `fixture=true` and must not be treated as live robot state. |

Button enablement contract:

| Button | Required backend allowance |
| --- | --- |
| Start Delivery | `phone_readiness.command_safety.actions.start.enabled=true` and `action_permissions.can_collect=true` or top-level `can_collect=true`. |
| Confirm Dropoff | `phone_readiness.command_safety.actions.confirm_dropoff.enabled=true` and `action_permissions.can_confirm_dropoff=true` or top-level `can_confirm_dropoff=true`. |
| Cancel | `phone_readiness.command_safety.actions.cancel.enabled=true` and `action_permissions.can_cancel=true` or top-level `can_cancel=true`. |
| Diagnostics / Support Handoff | May stay accessible while primary actions are blocked; opening them must not trigger robot actions. |

Fail-closed rule: when `command_safety` is missing, stale, blocked, waiting for ACK, offline, or manual takeover is required, the mobile web entrypoint keeps Start Delivery, Confirm Dropoff, and Cancel disabled. ACK copy remains command accepted/processing evidence only and must not be rendered as delivery success.

Service-worker boundary:

| Traffic | Cache behavior |
| --- | --- |
| Static shell (`index.html`, CSS, JS, manifest, offline shell, icons) | May be cached. |
| `/api/*`, `/robots/*`, command routes, ACK routes, diagnostics, and every non-GET request | Must bypass cache with `no-store`. |

Evidence boundary: `software_proof_docker_mobile_web_entrypoint_gate`. It does not prove production app readiness, real phone-device/browser acceptance, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, or delivery success.

`phone_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_local_phone_ui_readiness_gate`; this is local/Docker software proof only. |
| `primary_state` | One of the current phone-first states: `ready`, `local_ready_remote_status_waiting`, `waiting_for_robot_status`, `waiting_for_command_ack`, `login_required`, `remote_unreachable`, `remote_response_invalid`, `manual_takeover_required`, or `monitoring`. |
| `can_continue` | Whether the current phone journey has a safe next step. It does not prove delivery success. |
| `next_action` | Machine-readable recovery/action hint: `continue_local_flow`, `continue_local_or_wait_remote_status`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, `contact_support`, `manual_takeover`, or `watch_progress`. |
| `safe_phone_copy` | User-facing readiness summary. Must not include raw JSON, credentials, ROS topic names, serial devices, baudrate, WAVE ROVER parameters, or `/cmd_vel`. |
| `recovery_hint` | User-facing next step. |
| `support_level` | Support classification for phone UI and operator support, such as `phone_ready`, `local_fallback`, `local_fallback_only`, `remote_blocked`, `remote_waiting_status`, `remote_waiting_ack`, `support_required`, or `human_takeover_required`. |
| `local_delivery` | Current local state plus `phone_copy` and `speaker_prompt`. |
| `action_permissions` | Copies `can_collect`, `can_confirm_dropoff`, and `can_cancel`. These remain the source for button enablement. |
| `remote_readiness` | Pass-through local/mock remote readiness. |
| `cloud_preflight` | Optional phone-safe preflight summary. Missing data maps to `not_run` or `unknown`; it is not a robot delivery failure. |
| `backup_restore` | Optional phone-safe backup/restore drill summary. Missing data maps to `not_run` or `unknown`; it is not disaster recovery proof. |
| `phone_support_bundle` | Same object exposed at top-level `/api/status.phone_support_bundle`; nested here so clients that only consume readiness can still show Support Handoff. Schema is `trashbot.phone_support_bundle.v1`, evidence boundary is `software_proof_docker_phone_support_bundle_gate`. |
| `voice_prompt_readiness` | Same object exposed at top-level `/api/status.voice_prompt_readiness`; nested here so clients that only consume readiness can show the current prompt, trigger, human-help requirement, playback boundary, ACK semantics, and not-proven list. Schema is `trashbot.voice_prompt_readiness.v1`, evidence boundary is `software_proof_docker_phone_voice_prompt_readiness_gate`. |
| `phone_offline_resume_readiness` | Same object exposed at top-level `/api/status.phone_offline_resume_readiness`; nested here so clients that only consume readiness can show reconnect/resume state, command safety result, support handoff availability, offline shell boundary, ACK semantics, and not-proven list. Schema is `trashbot.phone_offline_resume_readiness.v1`, evidence boundary is `software_proof_docker_phone_offline_resume_gate`. |
| `not_proven` | Explicit list of capabilities this local gate does not prove, including production phone app, real cloud/4G, OSS/CDN, Nav2/fixed-route delivery, WAVE ROVER motion, and HIL pass. |

ACK semantics remain separate from delivery result semantics. `remote_readiness.last_command_ack` or `degradation_state=ok` only says the command envelope was processed; phone clients must keep reading local or remote status for delivery progress, failure, cancellation, or human-takeover results.

`phone_support_bundle` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_support_bundle.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_support_bundle_gate`; this is local/Docker software proof only. |
| `bundle_id` | Local tracking id. It must not contain tokens, paths, hardware parameters, serial details, or full artifact identifiers. |
| `generated_at` | Local generation timestamp. |
| `support_level` | Handoff classification, for example `phone_ready`, `local_fallback`, `remote_waiting_ack`, `support_required`, or `human_takeover_required`. |
| `status_summary` | Plain-language current state summary from `phone_readiness` or local status. |
| `failure_summary` | Plain-language terminal failure or blocking summary. If no terminal failure exists, it must say so instead of inventing one. |
| `next_steps` | User next step and support next step. |
| `ack_semantics` | Must state that ACK is accepted/processing evidence only and is not delivery success. |
| `support_refs` | Sanitized short references such as software/map/route version, failure code, current step, support level, and command block reason. |
| `safe_copy` | Chinese-first text block safe for copy/paste to family, after-sales, or engineering support. |
| `not_proven` | Explicit non-claims including real phone device, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER, HIL, ACK-as-delivery-success, and delivery success. |

`phone_support_bundle` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, or complete artifacts. `/api/diagnostics.phone_support_bundle` uses the same builder as `/api/status`, but may add sanitized failure context from diagnostics. Opening Support Handoff or Diagnostics must not trigger robot actions.

`operation_log` / `phone_operation_log` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_operation_log.v1` or a compatible phone-support metadata schema. |
| `evidence_boundary` | `software_proof_docker_mobile_operation_log_gate` when produced by the local/Docker mobile operation-log gate. |
| `events` | Phone-safe recent event summaries such as user action, blocked reason, pending ACK, offline/recovering, manual takeover, or support handoff. |
| `safe_phone_copy` / `recovery_hint` | Chinese-first user copy and next step. These must not expose raw JSON, tokens, ROS topics, serial devices, baudrate, WAVE ROVER parameters, local paths, tracebacks, checksums, or complete artifacts. |
| `ack_semantics` | Must preserve that ACK is accepted/processing evidence only and is not delivery success. |
| `support_handoff` | Sanitized support entry metadata. Opening or rendering it must not trigger Start Delivery, Confirm Dropoff, Cancel, or any backend action. |
| `not_proven` | Must include the remaining non-claims: real phone device/browser, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER, HIL, and delivery success. |

If operation-log metadata appears beside a cloud `command` response or in any status/diagnostics payload, robot-side code must treat it as ignorable phone/support metadata. A metadata-only response with no valid `trashbot.remote.v1` command must not call `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, or cancel; must not POST ACK; and must not advance or persist `last_terminal_ack_id`.

`mobile_device_acceptance_readiness`, `phone_device_acceptance_readiness`, and `mobile_browser_acceptance_readiness` follow the same robot-side metadata-only rule. They may describe phone-device acceptance, browser acceptance, diagnostics availability, support handoff, and safe user copy, but they are not command, status, ACK, or cursor inputs. If any of these fields appear beside a valid `command`, the robot bridge must normalize and execute only that command envelope. If they appear without a valid command, the bridge must leave `/trashbot/collect_trash`, `/trashbot/confirm_dropoff`, cancel, ACK POSTs, `last_ack_id`, and persisted `last_terminal_ack_id` unchanged. ACK remains accepted/processing evidence only; it is never delivery success, phone-device acceptance proof, or browser acceptance proof.

`mobile_browser_acceptance_bundle`, `phone_browser_acceptance_bundle`, and
`mobile_acceptance_evidence_bundle` extend the same phone/support metadata
boundary for browser acceptance. They may summarize viewport, touch-target,
PWA install prompt, offline shell, diagnostics, cloud/action gates, client
timestamp, safe phone copy, redacted evidence refs, and `not_proven` items for
mobile UI or diagnostics. They are not `trashbot.remote.v1`
command/status/ACK envelope fields, ROS2 action/service inputs, backend action
results, cursor instructions, Nav2/fixed-route results, WAVE ROVER feedback,
HIL evidence, production-app readiness, real browser acceptance, or delivery
success proof. If they appear beside a valid `command`, robot-side
normalization must strip the bundle fields and execute only the valid command
envelope. If they appear without a valid command, the bridge must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, and must not
advance in-memory `last_ack_id` or persist `last_terminal_ack_id`.
`trigger_robot_action`, `next_action`, `cursor_override`,
`delivery_success`, raw ROS topics, `/cmd_vel`, serial devices, hardware
parameters, Authorization headers, credentials, local paths, tracebacks,
checksums, and complete artifacts must not be copied into robot status, ACK,
backend action result, or normalized command payload. ACK remains
accepted/processing evidence only; it is never delivery success or acceptance
completion.

`mobile_web_browser_proof`, `phone_browser_proof`, and
`mobile_browser_proof_summary` extend that metadata-only rule for the
`software_proof_docker_mobile_web_browser_proof_gate` boundary. They may record
local Chromium-family browser evidence, screenshot/summary refs,
ACK-semantics copy, and `not_proven` items for the phone/browser proof bundle,
but they are not `trashbot.remote.v1` command/status/ACK fields, ROS2 action or
service inputs, Nav2/fixed-route proof, WAVE ROVER feedback, HIL evidence,
real phone-device proof, production-app readiness, cursor instructions, or
delivery/dropoff/cancel completion. If they appear beside a valid `command`,
robot-side normalization must strip them and execute only the valid command
envelope. If they appear without a valid command, the bridge must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, and must not
advance in-memory `last_ack_id` or persist `last_terminal_ack_id`. ACK remains
accepted/processing evidence only; it is never browser proof, delivery
success, dropoff success, or cancel completion.

`mobile_current_pwa_field_trial_browser_proof`,
`mobile_current_pwa_field_trial_browser_proof_summary`, and
`mobile_current_pwa_field_trial_browser_proof_copy` follow the same
robot-side metadata-only rule for the current PWA field-trial browser proof.
They may summarize local Chromium-family viewport evidence, field-trial panel
visibility, screenshot/JSON refs, phone-safe copy, ACK semantics, and
`not_proven` items for the
`software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`
boundary, but they are `software_proof` metadata only: not
`trashbot.remote.v1` command/status/ACK fields, terminal ACKs, cursor
instructions, ROS2 action/service inputs, backend action results, production
readiness, O5 external proof, HIL evidence, real phone-device proof, dropoff
success, cancel completion, or delivery success. If they appear beside a valid
`command`, robot-side normalization must strip them and execute only that
command envelope; metadata must not alter action, target, idempotency, ACK
payload, or cursor persistence. If they appear without a valid `command`, the
bridge must not invoke `collect`, `confirm_dropoff`, or `cancel`, must not POST
ACK, and must not advance in-memory `last_ack_id` or persist
`last_terminal_ack_id`. `trigger_robot_action`, `next_action`,
`cursor_override`, `terminal_ack`, `delivery_success`, `dropoff_success`,
`cancel_completed`, production-readiness flags, HIL flags, raw ROS topics,
`/cmd_vel`, serial devices, Authorization headers, credentials, local paths,
tracebacks, checksums, and complete artifacts must not be copied into robot
status, ACK, backend action result, cursor state, or normalized command
payload. ACK remains accepted/processing evidence only; it is never terminal
ACK, field-trial browser proof, delivery success, dropoff success, cancel
completion, production readiness, O5 external proof, or HIL.

`mobile_real_device_acceptance_decision`,
`mobile_real_device_acceptance_decision_summary`, and
`mobile_real_device_acceptance_decision_package` extend the metadata-only rule
for the `software_proof_docker_mobile_real_device_acceptance_decision_gate`
boundary. They may carry reviewer decision metadata, safe copy, redacted
support refs, terminal-ACK semantics, and remaining `not_proven` claims for
phone/support review, but they are not `trashbot.remote.v1`
command/status/ACK fields, terminal ACKs, cursor instructions, ROS2
action/service inputs, backend action results, production readiness, HIL
evidence, dropoff success, cancel completion, or delivery success. If they
appear beside a valid `command`, robot-side normalization must strip them and
execute only that command envelope. If they appear without a valid `command`,
the bridge must not invoke `collect`, `confirm_dropoff`, or `cancel`, must not
POST ACK, and must not advance in-memory `last_ack_id` or persist
`last_terminal_ack_id`. `trigger_robot_action`, `next_action`,
`cursor_override`, `terminal_ack`, `delivery_success`, `dropoff_success`,
`cancel_completed`, production-readiness flags, HIL flags, raw ROS topics,
`/cmd_vel`, serial devices, Authorization headers, credentials, local paths,
tracebacks, checksums, and complete artifacts must not be copied into robot
status, ACK, backend action result, or normalized command payload. ACK remains
accepted/processing evidence only; it is never terminal ACK, delivery success,
dropoff success, cancel completion, real-device acceptance, production
readiness, or HIL.

`cloud_public_ingress_tls`, `public_ingress_tls`, `cloud_public_ingress_tls_gate`, and public-ingress/TLS details under `deployment_readiness` are deployment readiness metadata only. They may describe whether a public ingress, TLS config, reverse proxy config, or external probe artifact is present, but they are not robot commands and do not alter the `trashbot.remote.v1` command/status/ACK envelope. If those fields appear without a valid `command`, robot-side code must not call backend actions, must not POST ACK, must not advance or persist cursor state, and must not copy `delivery_success`, `cursor_override`, Authorization/token material, credential-bearing URLs, raw ROS topics, `/cmd_vel`, serial devices, or hardware parameters into status or ACK. ACK remains accepted/processing evidence only; it is never delivery success or proof of real HTTPS/TLS/public ingress.

`voice_prompt_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.voice_prompt_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_voice_prompt_readiness_gate`; this is local/Docker prompt-contract proof only. |
| `current_prompt` | Current prompt that the phone may display or a future speaker/TTS layer may play. Chinese is preferred when a Chinese prompt exists. |
| `prompt_language` | Prompt language tag such as `zh-CN` or `en-US`. |
| `trigger_state` | State that selected the prompt, for example `waiting_for_trash`, `requesting_floor_help`, `target_floor_unconfirmed`, `unsafe_to_exit`, `failed`, or `needs_human_help`. |
| `trigger_reason` | Phone-safe plain-language reason for the prompt. |
| `requires_human_help` | True when user, bystander, support, or operator intervention is required. |
| `playback_ready` | Must remain `false` for the local/Docker proof; this gate does not prove real speaker or TTS playback. |
| `safe_phone_copy` | Chinese-first copy for the first screen. It must state that ACK is accepted/processing evidence only and that prompt readiness is not actual playback proof. |
| `ack_semantics` | Must state that ACK is not delivery success and not proof that the prompt was played. |
| `support_refs` | Sanitized short references such as state, failure code, support level, and command block reason. |
| `not_proven` | Explicit non-claims including real speaker playback, TTS playback, microphone wake word, real phone device, production phone app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route delivery, WAVE ROVER motion, HIL, and delivery success. |

When elevator assisted delivery reaches `requesting_floor_help`, `current_prompt` must be:

```text
你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,
```

`voice_prompt_readiness` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, local filesystem paths, tracebacks, checksums, or complete artifacts. Opening Diagnostics or reading this summary must not trigger robot actions and must not alter `trashbot.remote.v1` command/status/ack envelope semantics.

`phone_offline_resume_readiness` contract:

| Field | Contract |
| --- | --- |
| `schema` | `trashbot.phone_offline_resume_readiness.v1`. |
| `schema_version` | Integer schema version, currently `1`. |
| `evidence_boundary` | `software_proof_docker_phone_offline_resume_gate`; this is local/Docker offline/resume proof only. |
| `connection_state` | Phone recovery state: `offline`, `status_stale`, `pending_ack`, `blocked`, `manual_takeover`, `recovering`, or `online`. |
| `can_resume` | True only when connection state is online and command safety allows at least one primary action. |
| `primary_actions_enabled` | Whether Start Delivery, Confirm Dropoff, or Cancel is currently enabled after command safety. |
| `support_entry_enabled` | Whether Diagnostics or Support Handoff can still be opened while primary actions are blocked. |
| `next_action` | Machine-readable recovery hint such as `wait_reconnect`, `wait_for_robot_status`, `wait_for_command_ack`, `retry_cloud`, `manual_takeover`, or `continue_local_flow`. |
| `safe_phone_copy` | Chinese-first user copy for the first-screen offline/resume panel. |
| `recovery_hint` | User-facing recovery step after reconnect, stale status, pending ACK, or manual takeover. |
| `ack_semantics` | Must state that ACK is accepted/processing evidence only and is not delivery success. |
| `support_handoff` | Sanitized support handoff availability and copy. |
| `voice_prompt` | Prompt readiness boundary summary; local/Docker proof does not prove real speaker/TTS playback. |
| `command_safety` | Compact summary of the final browser button gate, including `global_block_reason`, primary-action state, and diagnostics availability. |
| `offline_shell` | Confirms Start/Confirm/Cancel remain disabled and no control request cache is used in the offline shell. |
| `not_proven` | Explicit non-claims including real phone browser/device, production app, real cloud/4G, OSS/CDN live traffic, Nav2/fixed-route, WAVE ROVER motion, HIL, and delivery success. |

`phone_offline_resume_readiness` must not expose tokens, Authorization headers, OSS AK/SK, root passwords, DB or queue URLs, raw ROS topic names, `/cmd_vel`, serial devices, baudrate values, local filesystem paths, checksums, or complete artifacts. Opening Diagnostics, Support Handoff, or the offline shell must not trigger robot actions, must not cache control requests, and must not alter `trashbot.remote.v1` command/status/ack envelope semantics.

The same `/api/status` payload carries live location telemetry when available:

| Field | Contract |
| --- | --- |
| `robot_pose` | Latest `/amcl_pose` sample as `frame_id`, `x`, `y`, `yaw`, and `updated_at`. `null` until pose data arrives. |
| `robot_location` | Compatibility alias for `robot_pose`. |
| `robot_path` | Recent pose trail, capped at 200 points, for the browser trajectory view. |

| Parameter | Default | Contract |
| --- | --- | --- |
| `pose_topic` | `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` topic used for the local web location view. |
| `software_version` | installed package version or `0.1.0` fallback | Version reported in `/api/diagnostics`. |
| `map_version` | empty | Map version label reported in `/api/diagnostics`; route/map generation should set this when available. |
| `route_version` | empty | Route version label reported in `/api/diagnostics`; fixed-route tooling should set this when available. |
| `log_refs` | empty list | Operator-facing log references included in `/api/diagnostics`. |
| `vision_sample_manifest_ref` | `~/.ros/trashbot_vision_samples/manifest.json` | Optional deployment-supplied reference for future vision samples; the current MVP does not ship a default detector or manifest producer. |
| `review_decision_log_ref` | `~/.ros/trashbot_vision_samples/review_decisions.jsonl` | Local JSONL sink for manual review decisions. Missing/corrupt decision logs are reported through structured diagnostics fields. |
| `hardware_proof_ref` | empty | Optional software-proof artifact path consumed by `/api/diagnostics.hardware_proof`. Empty or unreadable paths must degrade to `read_error`; this evidence is software-only and is never equivalent to HIL pass. |

Launch entry mapping:

- `bringup.launch.py` and `autonomous.launch.py` expose `operator_hardware_proof_ref`.
- That launch argument maps 1:1 to operator gateway node parameter `hardware_proof_ref`.

`/api/diagnostics.vision_samples` keeps the legacy summary fields (`manifest_ref`, `exists`, `schema`, `sample_count`, latest sample fields, `event_counts`, `review_queue`, and `read_error`) and adds manifest integrity fields produced from `ros2_trashbot_vision.vision_sample_manifest.summarize_manifest()` when available:

| Field | Contract |
| --- | --- |
| `integrity_summary.status` | `ok`, `warning`, `error`, `not_configured`, `checker_unavailable`, or `checker_failed`; phone and support tools can use this as the high-level sample-chain health state. |
| `integrity_error_count` / `integrity_warning_count` | Counts of checker errors and warnings. Errors mean required manifest shape or required file references are not trustworthy; warnings mean optional evidence or schema expectations need review. |
| `integrity_errors` / `integrity_warnings` | Checker messages for remote support. These are diagnostic strings, not user-facing phone copy. |
| `missing_file_ref_count` / `missing_file_refs` | Count and detail list for manifest references that could not be resolved or found, including `sample_index`, field name, original value, and resolved path when available. |
| `context_field_coverage` | Per-context-field present/missing counts for `task_id`, `route_id`, `checkpoint_id`, `event_type`, and `anomaly_type`. |
| `file_counts` | Per-reference present/missing/empty counts for `sample_ref`, `json`, `raw_image`, and `annotated_image`. |

If the manifest is not configured or the vision checker cannot be imported, diagnostics still returns HTTP payloads with the legacy fields and a structured integrity fallback instead of failing the whole endpoint.

`/api/diagnostics.route_proof_summary` is consumed from navigation proof output only (pass-through/mapping on behavior side). Behavior/operator must not recalculate coverage logic from local samples:

| Field | Contract |
| --- | --- |
| `route_proof_summary.coverage_rate` | Nav proof source-of-truth ratio. Behavior side only reads and displays it. |
| `route_proof_summary.covered_checkpoints` | Nav proof source-of-truth covered count. |
| `route_proof_summary.total_checkpoints` | Nav proof source-of-truth route checkpoint count. |
| `route_proof_summary.missing_checkpoints` | Nav proof source-of-truth missing checkpoint IDs/names. |
| `route_proof_summary.gate_status` | Nav proof source-of-truth visual gate status. |
| `route_proof_summary.last_block_reason` | Nav proof source-of-truth block reason text. |

`/api/diagnostics.route_proof_status` is a behavior-side readable classification derived from the above fields only:

| Field | Contract |
| --- | --- |
| `route_proof_status.state` | One of `ready`, `waiting_visual_gate`, `insufficient_coverage`, `blocked`, `unknown`. |
| `route_proof_status.reason` | Human-readable mapped explanation for the current state. |
| `route_proof_status.blocking_reason` | Non-empty only when state is `blocked`; sourced from `route_proof_summary.last_block_reason`. |
| `route_proof_status.missing_fields` | Required fields that were missing in `route_proof_summary`; non-empty implies `state=unknown`. |
| `route_proof_status.source` | Where behavior consumed the proof (`latest_status`, `last_task`, or task record evidence). |

`route_proof_status.state` mapping rule (single behavior-side contract, no local recomputation):

| State | Mapping condition |
| --- | --- |
| `unknown` | `route_proof_summary` missing, required fields missing, `coverage_rate` is non-numeric, or unsupported `gate_status`. |
| `waiting_visual_gate` | `gate_status` in `{waiting_visual_gate, waiting, pending, blocked_by_visual_gate, waiting_camera_frame, missing_live_frame, keyframe_preflight_failed, missing_keyframe, no_live_descriptors, insufficient_matches}`. This check runs before generic `blocked` mapping to preserve nav visual-gate waiting semantics. |
| `blocked` | `last_block_reason` is non-empty and `gate_status` is not one of the waiting statuses above. |
| `insufficient_coverage` | `coverage_rate < 1.0` or `missing_checkpoints` still has values after field validation. |
| `ready` | `coverage_rate >= 1.0`, `missing_checkpoints` empty, and `gate_status` in `{passed, ready, ok}`. |

`review_queue` items include manual-review merge fields:

| Field | Contract |
| --- | --- |
| `review_status` | `pending` or `decided`; derived from decision-log merge, not from UI-local state. |
| `last_decision` | `null` or latest decision summary (`decision_id`, `decision`, `comment`, `option`, `operator`, `timestamp`). |

Review progress aggregates are exposed by both `/api/vision/review-queue` and `/api/diagnostics.vision_samples`:

| Field | Contract |
| --- | --- |
| `progress_summary.total` | Number of reviewable samples based on current manifest queue criteria. |
| `progress_summary.decided` | Number of reviewable samples that have a valid latest decision. Duplicate records for one sample use last-valid-decision semantics. |
| `progress_summary.pending` | `max(total - decided, 0)`. |
| `progress_summary.coverage_rate` | `decided / total` rounded to 4 decimals; returns `0.0` when `total=0`. |
| `decision_distribution.<decision>.count` | Final-decision count per decision type (`approved`, `rejected`, `needs_retry`) among decided samples. |
| `decision_distribution.<decision>.ratio` | `count / decided` rounded to 4 decimals; returns `0.0` when `decided=0`. |
| `next_pending_sample` | `null` when there is no pending sample; otherwise includes `sample_id`, `sample_ref`, `reason`, `event_type`, and `timestamp`. |

`/api/diagnostics.review_decision_log` and `/api/vision/review-queue.review_decision_log` expose decision-store health:

| Field | Contract |
| --- | --- |
| `status` | `ok`, `not_configured`, `missing`, or `read_error`. |
| `decision_log_ref` | Resolved decision JSONL path. |
| `exists` | Whether the decision log exists. |
| `decision_count` / `sample_count` | Valid decision rows and distinct sample IDs in the log. |
| `read_error` | Structured read/parsing error detail when unavailable or malformed. |

`/api/diagnostics.hardware_proof` summarizes an offline artifact produced by `ros2_trashbot_hardware.hardware_diagnostics_proof`. The artifact source remains hardware-owned and vendor-backed by `docs/vendor/VENDOR_INDEX.md`; the operator gateway only reads it and maps it into phone-safe support states. Software proof is not HIL pass, hardware pass, real UART validation, wheel-direction validation, speed-unit validation, feedback-frequency measurement, IMU validation, or battery validation.

| Field | Contract |
| --- | --- |
| `status` | One of `software_proof`, `needs_hil`, `invalid_config`, or `read_error`. Unknown, missing, malformed, or unreadable artifacts must map conservatively and must not make `/api/diagnostics` fail. |
| `artifact_ref` | Path or deployment reference used to read the artifact. Empty means no artifact is configured. |
| `source_status` | Raw artifact status, such as `software_proof_ready`, `invalid_config`, or `feedback_parse_failed`. |
| `exists` | Whether the artifact path existed and could be opened far enough for the summary attempt. |
| `read_error` | Structured read/config/parsing problem. This field is populated for missing files, bad JSON, non-object JSON, missing status, unsupported status, invalid config detail, or feedback-parse failure. |
| `summary` | Phone/support copy. It must remain conservative and must never claim hardware passed or HIL passed. |
| `next_step` | Recovery or validation action, such as rerunning software proof, fixing bridge config, or running WAVE ROVER HIL. |
| `vendor_sources` | Vendor source references copied from the artifact. The operator gateway must not invent new hardware facts here. |
| `risk_flags` | Risk flags copied from the artifact. `hil_required` or high-severity HIL risk maps `software_proof_ready` to `needs_hil`. |
| `hil_recipe` | HIL recipe copied from the artifact for support/engineering validation. |

Status mapping:

| Artifact condition | Product status |
| --- | --- |
| `status=software_proof_ready` with `hil_required` or high HIL risk | `needs_hil` |
| `status=software_proof_ready` without HIL risk | `software_proof`, with copy that still says software proof only |
| `status=invalid_config` | `invalid_config` |
| `status=feedback_parse_failed` | `needs_hil` or `read_error`; current gateway uses `needs_hil` with read-error detail |
| Missing path, missing file, unreadable file, bad JSON, non-object JSON, missing status, unsupported status | `read_error` |

### 4G Remote Bridge

The optional `remote_bridge` node is the formal 4G-oriented remote MVP path. It does not expose robot-local HTTP to the phone. Instead, the robot initiates outbound HTTP polling to a cloud or mock-cloud endpoint. It is disabled by default in launch files and is intended to be testable without a real cloud account.

| Parameter | Default | Contract |
| --- | --- | --- |
| `enabled` | `false` | Runtime guard; launch also keeps the node off by default. |
| `cloud_base_url` | empty | Base URL for a mock or future cloud service. |
| `robot_id` | `trashbot-001` | Robot identity included in status and ack payloads. |
| `auth_token` | empty | Optional bearer token. When configured, robot-originated cloud requests use bearer auth; token values must never appear in status, diagnostics, ACK messages, or cursor state. |
| `poll_interval_sec` | `2.0` | Periodic command polling interval. |
| `request_timeout_sec` | `5.0` | HTTP request timeout. |
| `cursor_state_path` | empty | Optional file for persisted `last_terminal_ack_id`. It stores cursor metadata only and must not store bearer tokens, command payloads, serial devices, hardware parameters, or ROS topic names. |
| `last_ack_id` | empty | Launch-time fallback cursor used only when no valid `cursor_state_path` state is loaded. Treated as an opaque cloud cursor, not a sortable command id. |

| Direction | Endpoint | Contract |
| --- | --- | --- |
| robot -> cloud | `POST /robots/{robot_id}/status` | Sends the latest `trashbot.remote.v1` robot state before polling. |
| robot -> cloud | `GET /robots/{robot_id}/commands/next?last_ack_id=<id>` | Pulls `{"command": null}` or one command object. |
| robot -> cloud | `POST /robots/{robot_id}/commands/{command_id}/ack` | Sends `acked`, `failed`, or `ignored` plus local operator result metadata. `ignored` is used for expired commands that were not executed. |

Cloud responses may include optional status, preflight, diagnostics, queue,
mobile-web-entrypoint, PWA-entrypoint, cloud-hosted PWA/static-shell,
mobile PWA installability/browser installability,
mobile PWA install-prompt evidence, mobile PWA install-prompt event capture,
mobile PWA install-prompt evidence export,
current PWA retest browser proof,
voice-prompt-readiness, production-recovery, transaction-isolation, cloud
external probe, cloud DB/queue external probe, OSS/CDN live probe, external
evidence intake, deployment-readiness, mobile task-start confirmation, mobile
action feedback, mobile terminal action confirmation, mobile primary journey,
operation-log, DB/queue config-gate, phone/mobile cloud-readiness summary, or
mobile/browser acceptance-bundle metadata, including mobile real-device
field-trial retest-execution and evidence-record metadata beside the
`trashbot.remote.v1` command/status/ACK envelope. Robot clients must treat
those fields as ignorable diagnostics for forward compatibility. A
metadata-only response with `command=null` or no command object must not start a
robot action, must not emit ACK, and must not advance in-memory `last_ack_id`
or persist `last_terminal_ack_id`.
Cloud external probe metadata, including `cloud_external_probe` and
`cloud_external_probe_bundle`, is diagnostic/deployment metadata for
`/healthz`, `/readyz`, and `/preflightz` probe summaries. It is not a robot
command, delivery result, HIL result, or WAVE ROVER feedback. It may report
`production_ready=false`, `overall_status=blocked`, endpoint summaries, retry
hints, or redacted safe summaries, but it must not trigger `collect`,
`confirm_dropoff`, or `cancel`, post ACK, advance cursor state, persist
`last_terminal_ack_id`, or turn ACK copy into delivery success.
Deployment-readiness metadata, including `deployment_readiness`,
`cloud_deployment_readiness`, and `preflight`, is also deployment diagnostics
only; it is safe for older robot clients to ignore and cannot change
`trashbot.remote.v1` command normalization.
Mobile web entrypoint metadata, including `mobile_web_entrypoint`,
`mobile_web_entrypoint_readiness`, and `pwa_entrypoint`, is a phone/UI consumer
contract only. It may describe the static shell, installability, readiness, or
offline behavior, but it must not alter allowed remote command types, invoke
`collect`, `confirm_dropoff`, or `cancel`, post ACK, advance cursor state, or
turn ACK copy into delivery success.
Voice prompt readiness metadata is phone/operator prompt contract evidence only:
it must not trigger `collect`, `confirm_dropoff`, or `cancel`, and it must not
turn ACK into delivery success or proof that a speaker/TTS prompt was played.
Transaction-isolation metadata is proof about the cloud/control-plane drill
only; it is not a delivery result and cannot override ACK semantics.
Production-recovery metadata is phone/operator support metadata only. It may
describe local Docker recovery gate state, `production_ready=false`, or
`overall_status=blocked`, but it is not part of the remote command envelope, is
safe for older robot clients to ignore, and must not trigger `collect`,
`confirm_dropoff`, `cancel`, ACK emission, or cursor advancement on its own.
DB/queue config-gate metadata, including `cloud_db_queue_config`,
`cloud_db_queue_config_gate`, and `db_queue_config`, is phone-safe/cloud
readiness metadata for cloud database and queue configuration proof. It may
describe `production_ready=false`, blocked readiness, redacted config checks, or
software-proof evidence boundaries, but it is not a robot command, ACK payload,
status-post extension, backend action result, cursor instruction, ROS2 action
result, WAVE ROVER feedback, HIL result, or delivery success proof. Robot-side
protocol normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. DB URLs, queue URLs, credentials, Authorization headers,
raw ROS topics, `/cmd_vel`, serial devices, hardware parameters,
`trigger_robot_action`, `cursor_override`, and `delivery_success` must not be
copied into robot status, ACK, backend action result, or normalized command
payload.
DB/queue external-probe metadata, including
`cloud_db_queue_external_probe`, `cloud_db_queue_external_probe_bundle`, and
`db_queue_external_probe`, is the follow-on readiness proof for externally
probing cloud database and queue dependencies. It may describe
`production_ready=false`, `overall_status=blocked`, redacted probe results,
retry hints, or the evidence boundary
`software_proof_docker_cloud_db_queue_external_probe_gate`, but it is not part
of the `trashbot.remote.v1` command/status/ACK envelope. It must not be treated
as a robot command, backend action result, ACK payload, cursor instruction,
ROS2 action result, WAVE ROVER feedback, HIL result, real production DB/queue
proof, or delivery success proof. Robot-side protocol normalization must strip
those fields from valid command objects, and metadata-only responses must not
invoke `collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, and must
not advance or persist `last_terminal_ack_id`. DB/queue URLs, credentials,
Authorization headers, raw ROS topics, `/cmd_vel`, serial devices, hardware
parameters, `trigger_robot_action`, `cursor_override`, and `delivery_success`
must not be copied into robot status, ACK, backend action result, or normalized
command payload. ACK remains accepted/processing evidence only and must not be
interpreted as delivery success or external DB/queue production readiness.
OSS/CDN live-probe metadata, including `oss_cdn_live_probe`,
`oss_cdn_live_probe_artifact`, and `cdn_live_probe`, is phone/support readiness
metadata for checking whether future OSS object and CDN endpoint probes have
safe, redacted evidence. It may describe `production_ready=false`,
`overall_status=blocked`, redacted endpoint paths, object-key hashes, retry
hints, or the evidence boundary
`software_proof_docker_oss_cdn_live_probe_gate`, but it is not part of the
`trashbot.remote.v1` command/status/ACK envelope. It must not be treated as a
robot command, backend action result, ACK payload, cursor instruction, ROS2
action result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result, real
OSS/CDN live traffic proof, or delivery success proof. Robot-side protocol
normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. Credential URLs, Authorization headers, OSS AK/SK,
raw ROS topics, `/cmd_vel`, serial devices, hardware parameters,
`trigger_robot_action`, `cursor_override`, and `delivery_success` must not be
copied into robot status, ACK, backend action result, or normalized command
payload. ACK remains accepted/processing evidence only and must not be
interpreted as delivery success or real OSS/CDN production readiness.
External evidence intake metadata, including `external_evidence_intake`,
`external_evidence_intake_artifact`, and `cloud_external_evidence`, is the
cloud-readiness proof intake for future public ingress/TLS, OSS/CDN,
production DB/queue, and 4G/SIM materials. It may describe
`production_ready=false`, `overall_status=blocked`,
`external_evidence_complete=false`, redacted material summaries, retry hints,
checksums, or the evidence boundary
`software_proof_docker_external_evidence_intake_gate`, but it is not part of
the `trashbot.remote.v1` command/status/ACK envelope. It must not be treated as
a robot command, backend action result, ACK payload, cursor instruction, ROS2
action result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result, real
cloud/4G proof, real OSS/CDN/DB/queue proof, or delivery success proof.
Robot-side protocol normalization must strip those fields from valid command
objects, and metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. Credential-bearing
URLs, Authorization headers, OSS AK/SK, DB or queue URLs, raw ROS topics,
`/cmd_vel`, serial devices, hardware parameters, `trigger_robot_action`,
`cursor_override`, and `delivery_success` must not be copied into robot status,
ACK, backend action result, or normalized command payload. ACK remains
accepted/processing evidence only and must not be interpreted as delivery
success or external evidence production readiness.
Cloud-readiness summary metadata, including
`phone_cloud_readiness_summary`, `mobile_cloud_readiness_summary`, and
`cloud_readiness_summary`, is phone-safe support/readiness summary for the
mobile surface to explain cloud DB/queue/config readiness. It may summarize
blocked readiness, `production_ready=false`, redacted support copy, or the
software-proof boundary, but it is not part of the `trashbot.remote.v1`
command/status/ACK envelope. It is not a robot command, ACK payload, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, real cloud/4G proof, or delivery success proof. Robot-side protocol
normalization must strip those fields from valid command objects, and
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. Production-ready claims, credential material,
credential-bearing cloud URLs, raw ROS topics, `trigger_robot_action`,
`cursor_override`, and `delivery_success` must not be copied into robot status,
ACK, backend action result, or normalized command payload. ACK remains
accepted/processing evidence only and must not be interpreted as delivery
success.
Mobile task-start confirmation metadata, including
`mobile_task_start_confirmation`,
`mobile_task_start_confirmation_readiness`, and
`task_start_confirmation_payload`, is the phone/UI API record that a user
selected a destination and confirmed the trash was loaded before pressing Start
Delivery. It is not a ROS2 action result, HIL result, WAVE ROVER feedback, or
delivery success proof. The robot bridge must ignore those fields outside the
`trashbot.remote.v1` command envelope; only a valid `command.id`,
`command.type`, and `command.payload` may drive `collect`, `confirm_dropoff`, or
`cancel`.
Mobile action feedback metadata, including `mobile_action_confirmation`,
`mobile_action_receipt`, and `phone_action_feedback`, is the phone/UI support
summary for Start/Confirm/Cancel submission feedback. It may describe
accepted/processing copy, blocked reasons, recovery hints, client references,
and the evidence boundary
`software_proof_docker_mobile_action_feedback_gate`. It is not a
`trashbot.remote.v1` command/status/ACK envelope, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result, cursor instruction,
or delivery success proof. The robot bridge must ignore those fields outside a
valid command object; protocol normalization must strip them before execution;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, and must not advance or persist
`last_terminal_ack_id`. ACK remains accepted/processing evidence only and must
not be rendered or interpreted as delivery success.
Mobile terminal action confirmation metadata, including
`mobile_terminal_action_confirmation_gate` and
`mobile_terminal_action_confirmation_summary`, is the phone/support summary for
the Confirm Dropoff / Cancel two-step terminal action confirmation UI. It may
include the action being confirmed, risk copy, ACK semantics, client reference,
evidence boundary
`software_proof_docker_mobile_terminal_action_confirmation_gate`, explicit
`not_proven` items, and safe phone copy. It must not contain or redefine a
command envelope, and it is not a robot command, ACK payload, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness proof, delivery success proof, dropoff
success proof, or cancel completion proof. Robot-side protocol normalization
must strip these fields from valid command objects; metadata-only responses
must not invoke `collect`, `confirm_dropoff`, or `cancel`, must not POST ACK,
must not advance in-memory `last_ack_id`, must not persist
`last_terminal_ack_id`, and must not write a cursor override. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, or `hil_pass` into robot status, ACK, backend action
result, normalized command payload, or cursor state. ACK remains
accepted/processing evidence only and must not be rendered or interpreted as
terminal action completion.
Mobile primary journey metadata, including `mobile_primary_journey_gate` and
`mobile_primary_journey_summary`, is the phone/support summary for the Start
Delivery primary path. It may summarize the selected trash station,
load-confirmation requirement, command-safety result, browser/device/cloud
gates, operation-log/action-feedback copy, and remaining `not_proven` items,
but it is not a robot command, ACK payload, cursor instruction, ROS2 action
result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result, production
readiness proof, delivery success proof, dropoff success proof, or cancel
completion proof. The metadata must not contain or redefine a command envelope.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, must not persist `last_terminal_ack_id`, and must not write a
cursor override. If these fields appear beside a valid `collect`,
`confirm_dropoff`, or `cancel` command, the robot bridge must execute only the
`trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, or `hil_pass` into
robot status, ACK, backend action result, normalized command payload, or cursor
state.
Mobile recovery decision metadata, including `mobile_recovery_decision_gate`
and `mobile_recovery_decision_summary`, is the phone/support summary for
blocked, offline, pending ACK, manual takeover, local submit failure, or missing
readiness situations after the mobile primary journey. It may summarize
recovery state, `next_action`, `blocking_reason`, `support_entry`,
`ack_semantics`, `evidence_boundary`, and `not_proven` items, but it is not a
robot command, ACK payload, cursor instruction, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result, production-readiness
proof, delivery success proof, dropoff success proof, or cancel completion
proof. The metadata must not contain or redefine a command envelope.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, must not persist `last_terminal_ack_id`, and must not write a
cursor override. If these fields appear beside a valid `collect`,
`confirm_dropoff`, or `cancel` command, the robot bridge must execute only the
`trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, or `hil_pass` into
robot status, ACK, backend action result, normalized command payload, or cursor
state.
Mobile/browser acceptance-bundle metadata, including
`mobile_browser_acceptance_bundle`, `phone_browser_acceptance_bundle`,
`mobile_acceptance_evidence_bundle`, `mobile_web_browser_proof`,
`phone_browser_proof`, `mobile_browser_proof_summary`,
`mobile_current_pwa_browser_proof_refresh`,
`mobile_current_pwa_browser_proof_refresh_summary`, and
`phone_current_pwa_browser_proof_refresh`,
`mobile_current_pwa_retest_browser_proof`,
`mobile_current_pwa_retest_browser_proof_summary`, and
`phone_current_pwa_retest_browser_proof`,
`mobile_current_pwa_field_trial_browser_proof`,
`mobile_current_pwa_field_trial_browser_proof_summary`, and
`mobile_current_pwa_field_trial_browser_proof_copy`, is the phone/UI and diagnostics
package for browser viewport, touch, PWA/offline, diagnostics, cloud/action
gates, client timestamp, safe copy, browser proof summaries, refresh evidence,
current-PWA retest evidence, retest-request panel visibility, current-PWA
field-trial browser proof evidence, and
evidence-boundary summaries. It may help a mobile client explain why controls
stay blocked, but it is not a `trashbot.remote.v1` command/status/ACK
envelope, terminal ACK, ROS2 action result, Nav2/fixed-route result, WAVE ROVER
feedback, HIL result, production app readiness proof, real phone-device proof,
real browser proof, real device retest completion, O5 external proof, cursor
instruction, Start/Confirm/Cancel enablement source, delivery success, dropoff
success, cancel completion, or real browser acceptance proof beyond the stated
local software boundary. Robot-side protocol normalization must strip these
fields from valid command objects; metadata-only responses must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, must not advance
in-memory `last_ack_id`, and must not persist `last_terminal_ack_id`. In mixed
valid-command responses the metadata must not alter action, target,
idempotency, ACK payload, or cursor persistence. `terminal_ack`,
`trigger_robot_action`, `next_action`, `cursor_override`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, `hil_pass`,
`ready_for_retest`, Authorization headers, raw ROS topics, `/cmd_vel`, serial
devices, credentials, local paths, tracebacks, checksums, and complete
artifacts must not be copied into robot status, ACK, backend action result,
normalized command payload, terminal result, or cursor state. ACK remains
accepted/processing evidence only and must not be rendered or interpreted as
browser proof refresh, current PWA retest completion, field-trial browser
proof, robot execution, HIL, O5 external proof, dropoff/cancel completion, or
delivery success.
Mobile real-device evidence intake metadata, including
`mobile_real_device_evidence_intake`,
`mobile_real_device_evidence_intake_summary`, and
`mobile_real_device_evidence_package`, is phone/support/acceptance metadata for
the `software_proof_docker_mobile_real_device_evidence_intake_gate` boundary.
It may summarize真实手机设备 material intake, iPhone/Android/browser family,
viewport, display mode, PWA install prompt/user choice, production app
readiness copy, screenshot/URL summaries, observer notes, redaction status,
safe phone copy, ACK semantics, client references, and `not_proven` items, but
it is metadata-only and is not a `trashbot.remote.v1` command/status/ACK
envelope, backend action result, cursor instruction, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result, production readiness,
real device proof, real browser proof, real PWA install prompt proof, Start
Delivery / Confirm Dropoff / Cancel enablement source, dropoff success, cancel
completion, or delivery success proof. Robot-side protocol normalization must
strip these fields from valid command objects; metadata-only responses must not
invoke `collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, must not
advance in-memory `last_ack_id`, and must not persist `last_terminal_ack_id`.
If these fields appear beside a valid `collect`, `confirm_dropoff`, or `cancel`
command, the robot bridge must execute only the `trashbot.remote.v1` command
envelope and must not copy `trigger_robot_action`, `next_action`,
`cursor_override`, `delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`, `real_device_proof`,
`pwa_install_prompt_proof`, credential-bearing URLs, Authorization headers, raw
ROS topics, `/cmd_vel`, serial devices, or hardware parameters into robot
status, ACK, backend action result, normalized command payload, or cursor
state. ACK remains accepted/processing evidence only and must not be rendered
or interpreted as production app readiness, PWA install prompt proof, real
phone-device proof, robot execution, delivery success, production readiness, or
HIL.
Mobile device evidence-capture metadata, including
`mobile_device_evidence_capture`, `mobile_device_evidence_capture_summary`, and
`mobile_device_evidence_package`, is phone/support metadata for a future
operator-captured photo/video/support package and its local/Docker evidence
boundary
`software_proof_docker_mobile_device_evidence_capture_gate`. It may describe
capture state, attachment references, safe phone copy, client references,
support handoff fields, and `not_proven` items, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, backend action result, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness proof, real phone-device proof, real browser
proof, real support-upload proof, or delivery success proof. Robot-side
protocol normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and must
not persist `last_terminal_ack_id`. If these fields appear beside a valid
`collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, `hil_pass`,
`real_device_proof`, `wave_rover_feedback`, credential-bearing URLs,
Authorization headers, raw ROS topics, `/cmd_vel`, serial devices, or hardware
parameters into robot status, ACK, backend action result, normalized command
payload, or cursor state. ACK remains accepted/processing evidence only and
must not be rendered or interpreted as device proof, robot execution, delivery
success, production readiness, HIL, or real WAVE ROVER proof.
Mobile device handoff-session metadata, including
`mobile_device_handoff_session`, `mobile_device_handoff_session_summary`, and
`mobile_device_handoff_package`, follows the same phone/support metadata-only
rule for the
`software_proof_docker_mobile_device_handoff_session_gate` boundary. It may
describe a local support handoff session, safe phone copy, session/package refs,
client references, operator/support routing, and `not_proven` items, but it is
not a `trashbot.remote.v1` command/status/ACK envelope, backend action result,
cursor instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER
feedback, HIL result, production-readiness proof, real phone-device proof, real
browser proof, real support-upload proof, dropoff/cancel completion, or delivery
success proof. Robot-side protocol normalization must strip these fields from
valid command objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`delivery_success`, `dropoff_success`, `cancel_completed`, `production_ready`,
`hil_pass`, `real_device_proof`, `wave_rover_feedback`, credential-bearing URLs,
Authorization headers, raw ROS topics, `/cmd_vel`, serial devices, or hardware
parameters into robot status, ACK, backend action result, normalized command
payload, or cursor state. These fields also must not enable Start Delivery,
Confirm Dropoff, or Cancel; button enablement remains governed by
`command_safety` and `action_permissions`. ACK remains accepted/processing
evidence only and must not be rendered or interpreted as handoff completion,
robot execution, delivery success, production readiness, HIL, or real device
proof.
Mobile PWA install-prompt evidence metadata, including
`mobile_pwa_install_prompt_evidence`,
`mobile_pwa_install_prompt_evidence_summary`, and
`mobile_pwa_install_prompt_evidence_package`, follows the same phone/support
metadata-only rule for the
`software_proof_docker_mobile_pwa_install_prompt_evidence_gate` boundary. It
may describe install-prompt capture status, user outcome, display mode,
manifest presence, service-worker status, offline-shell status, production-app
readiness copy, `safe_to_control`, linked handoff/device-evidence references,
safe phone copy, recovery hints, ACK semantics, evidence refs, and
`not_proven` items, but it is not a `trashbot.remote.v1`
command/status/ACK envelope, backend action result, cursor instruction, ROS2
action result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result,
production-readiness proof, real phone-device proof, real browser proof, real
PWA install prompt proof, dropoff/cancel completion, or delivery success proof.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`delivery_success`, `dropoff_success`, `cancel_completed`, `production_ready`,
`hil_pass`, `real_device_proof`, `pwa_install_prompt_proof`,
credential-bearing URLs, Authorization headers, raw ROS topics, `/cmd_vel`,
serial devices, or hardware parameters into robot status, ACK, backend action
result, normalized command payload, or cursor state. These fields also must
not enable Start Delivery, Confirm Dropoff, or Cancel; button enablement
remains governed by `command_safety` and `action_permissions`. ACK remains
accepted/processing evidence only and must not be rendered or interpreted as
install-prompt proof, robot execution, delivery success, production readiness,
HIL, or real device proof.
Mobile PWA install-prompt event-capture metadata, including
`mobile_pwa_install_prompt_event_capture`,
`mobile_pwa_install_prompt_event_capture_summary`, and
`mobile_pwa_install_prompt_event_capture_copy`, follows the same
phone/support metadata-only rule for the
`software_proof_docker_mobile_pwa_install_prompt_event_capture_gate` boundary.
It may describe local browser install-prompt events, capture timing,
user-choice copy, redacted evidence refs, safe phone copy, ACK-not-delivery
semantics, and `not_proven` items, but it is `software_proof` metadata only:
not a `trashbot.remote.v1` command/status/ACK envelope, ACK POST instruction,
terminal ACK, cursor instruction, ROS2 action result, Nav2/fixed-route result,
WAVE ROVER feedback, production-readiness result, O5 external proof, HIL
evidence, real phone-device proof, dropoff/cancel completion, or delivery
success. Robot-side protocol normalization must strip these fields from valid
command objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not let metadata alter action, target, idempotency, ACK payload, or cursor
persistence. These fields also must not copy `trigger_robot_action`,
`next_action`, `cursor_override`, `terminal_ack`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, `hil_pass`,
`real_device_proof`, `pwa_install_prompt_proof`, credential-bearing URLs,
Authorization headers, raw ROS topics, `/cmd_vel`, serial devices, or hardware
parameters into robot status, ACK, backend action result, normalized command
payload, or cursor state. ACK remains accepted/processing evidence only and
must not be rendered or interpreted as install-prompt proof, robot execution,
delivery success, production readiness, O5 external proof, HIL, or real phone
proof.
Mobile PWA install-prompt evidence-export metadata, including
`mobile_pwa_install_prompt_evidence_export`,
`mobile_pwa_install_prompt_evidence_export_summary`, and
`mobile_pwa_install_prompt_evidence_export_copy`, follows the same
phone/support metadata-only rule for the
`software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`
boundary. It may describe PWA install-prompt evidence export status,
copy/share state, redacted evidence refs, safe phone copy, ACK-not-delivery
semantics, and `not_proven` items, but it is `software_proof` metadata only:
not a `trashbot.remote.v1` command/status/ACK envelope, ACK POST instruction,
terminal ACK, cursor instruction, ROS2 action result, Nav2/fixed-route result,
WAVE ROVER feedback, production-readiness result, O5 external proof, HIL
evidence, real phone-device proof, dropoff/cancel completion, or delivery
success. Robot-side protocol normalization must strip these fields from valid
command objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not let metadata alter action, target, idempotency, ACK payload, or cursor
persistence. These fields also must not copy `trigger_robot_action`,
`next_action`, `cursor_override`, `terminal_ack`, `delivery_success`,
`dropoff_success`, `cancel_completed`, `production_ready`, `hil_pass`,
credential-bearing URLs, Authorization headers, raw ROS topics, `/cmd_vel`,
serial devices, or hardware parameters into robot status, ACK, backend action
result, normalized command payload, or cursor state. ACK remains
accepted/processing evidence only and must not be rendered or interpreted as
install-prompt export proof, robot execution, delivery success, production
readiness, O5 external proof, HIL, or real phone proof.
Mobile real-device review-handoff metadata, including
`mobile_real_device_review_handoff`,
`mobile_real_device_review_handoff_summary`, and
`mobile_real_device_review_handoff_package`, follows the phone/support/product
metadata-only rule for the
`software_proof_docker_mobile_real_device_review_handoff_gate` boundary. It
may describe reviewer routing, product/support handoff state, safe phone copy,
review evidence references, client references, ACK semantics, and `not_proven`
items for a human review handoff, but it is not a `trashbot.remote.v1`
command/status/ACK envelope, terminal ACK, backend action result, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness proof, real robot proof, dropoff success
proof, cancel completion proof, or delivery success proof. Robot-side protocol
normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and must
not persist `last_terminal_ack_id`. If these fields appear beside a valid
`collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`delivery_success`, `dropoff_success`, `cancel_completed`, `production_ready`,
`production_app_ready`, `hil_pass`, `real_device_review_complete`,
credential-bearing URLs, Authorization headers, raw ROS topics, `/cmd_vel`,
serial devices, or hardware parameters into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted/processing evidence only and must not be rendered or
interpreted as review-handoff completion, robot execution, delivery success,
production readiness, HIL, dropoff success, or cancel completion.
Mobile real-device review-execution metadata, including
`mobile_real_device_review_execution`,
`mobile_real_device_review_execution_summary`, and
`mobile_real_device_review_execution_package`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_review_execution_gate` boundary. It
may describe review execution checklist state, review result/status, evidence
items readiness, operator notes, reviewer notes, blocked reason, next evidence
request, redaction status, source boundary, ACK-not-delivery copy, and
`not_proven` items for human review execution, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, terminal ACK, backend action
result, cursor instruction, ROS2 action result, Nav2/fixed-route result, WAVE
ROVER feedback, HIL result, production-readiness proof, real robot proof,
dropoff success proof, cancel completion proof, or delivery success proof.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`real_device_review_executed`, credential-bearing URLs, Authorization headers,
raw ROS topics, `/cmd_vel`, serial devices, or hardware parameters into robot
status, ACK, backend action result, normalized command payload, terminal
result, or cursor state. These fields also must not enable Start Delivery,
Confirm Dropoff, or Cancel; button enablement remains governed by
`command_safety` and `action_permissions`. ACK remains accepted/processing
evidence only and must not be rendered or interpreted as review execution
completion, robot execution, delivery success, production readiness, HIL,
dropoff success, or cancel completion.
Mobile real-device retest-request metadata, including
`mobile_real_device_retest_request`,
`mobile_real_device_retest_request_summary`, and
`mobile_real_device_retest_request_package`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_retest_request_gate` boundary. It
may describe the next real-device retest checklist, missing evidence,
readiness/status per evidence item, owner/next action, blocked reason,
rejection reason, redaction status, source boundary, ACK-not-delivery copy,
operator/reviewer notes, and `not_proven` items for human retest preparation,
but it is not a `trashbot.remote.v1` command/status/ACK envelope, terminal
ACK, backend action result, cursor instruction, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result,
production-readiness proof, real robot proof, dropoff success proof, cancel
completion proof, or delivery success proof. Robot-side protocol
normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and
must not persist `last_terminal_ack_id`. If these fields appear beside a
valid `collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`, `ready_for_retest`,
credential-bearing URLs, Authorization headers, raw ROS topics, `/cmd_vel`,
serial devices, local paths, tracebacks, checksums, or complete artifacts into
robot status, ACK, backend action result, normalized command payload, terminal
result, or cursor state. These fields also must not enable Start Delivery,
Confirm Dropoff, or Cancel; button enablement remains governed by
`command_safety` and `action_permissions`. ACK remains accepted/processing
evidence only and must not be rendered or interpreted as retest completion,
robot execution, delivery success, production readiness, HIL, dropoff success,
or cancel completion.
Mobile real-device field-trial package metadata, including
`mobile_real_device_field_trial_package`,
`mobile_real_device_field_trial_package_summary`, and
`mobile_real_device_field_trial_package_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_package_gate` boundary.
It may describe field-trial handoff state, support/product checklist items,
safe phone copy, missing evidence, redaction status, source boundary,
ACK-not-delivery copy, operator notes, reviewer notes, support references, and
`not_proven` items for preparing a real-device field trial, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, terminal ACK, backend action
result, cursor instruction, ROS2 action result, Nav2/fixed-route result, WAVE
ROVER feedback, HIL result, production-readiness proof, real robot proof,
dropoff success proof, cancel completion proof, or delivery success proof.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`real_device_field_trial_ready`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, or complete artifacts into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted/processing evidence only and must not be rendered or
interpreted as field-trial completion, robot execution, delivery success,
production readiness, HIL, dropoff success, or cancel completion.
Mobile real-device field-trial acceptance-session metadata, including
`mobile_real_device_field_trial_acceptance_session`,
`mobile_real_device_field_trial_acceptance_session_summary`, and
`mobile_real_device_field_trial_acceptance_session_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`
boundary. It may describe a field-trial acceptance session, observer notes,
session state, safe phone copy, source boundary, ACK-not-delivery copy,
support references, and `not_proven` items for a future real-device
acceptance session, but it is `software_proof` metadata-only and is not a
`trashbot.remote.v1` command/status/ACK envelope, ACK POST, terminal ACK,
backend action result, cursor instruction, ROS2 action result,
Nav2/fixed-route result, WAVE ROVER feedback, HIL result,
production-readiness proof, O5 external proof, real phone proof, real robot
proof, dropoff success proof, cancel completion proof, or delivery success
proof. Robot-side protocol normalization must strip these fields from valid
command objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `ack_post`, `delivery_success`, `dropoff_success`,
`cancel_completed`, `production_ready`, `production_app_ready`, `hil_pass`,
`field_trial_acceptance_complete`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, or complete artifacts into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted/processing evidence only and must not be rendered or
interpreted as acceptance-session completion, robot execution, delivery
success, production readiness, O5 external proof, HIL, dropoff success, or
cancel completion.
Mobile real-device field-trial review metadata, including
`mobile_real_device_field_trial_review`,
`mobile_real_device_field_trial_review_summary`, and
`mobile_real_device_field_trial_review_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_review_gate` boundary.
It may describe field-trial material review status, missing evidence,
redaction status, source boundary, safe phone copy, ACK-not-delivery copy,
operator/reviewer notes, support references, and `not_proven` items for
reviewing a real-device field-trial package, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, terminal ACK, backend action
result, cursor instruction, ROS2 action result, Nav2/fixed-route result, WAVE
ROVER feedback, HIL result, production-readiness proof, real robot proof,
dropoff success proof, cancel completion proof, or delivery success proof.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`real_device_field_trial_reviewed`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, or complete artifacts into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted/processing evidence only and must not be rendered or
interpreted as field-trial review completion, robot execution, delivery
success, production readiness, HIL, dropoff success, or cancel completion.
Mobile real-device field-trial acceptance-review handoff metadata, including
`mobile_real_device_field_trial_acceptance_review_handoff`,
`mobile_real_device_field_trial_acceptance_review_handoff_summary`, and the
Robot diagnostics safe alias
`robot_diagnostics_mobile_real_device_field_trial_acceptance_review_handoff_summary`,
follows the same metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_acceptance_review_handoff_gate`
boundary. Robot diagnostics may consume only
`schema=trashbot.mobile_real_device_field_trial_acceptance_review_handoff.v1`
or
`schema=trashbot.mobile_real_device_field_trial_acceptance_review_handoff_summary.v1`
that resolves to
`source_schema=trashbot.mobile_real_device_field_trial_acceptance_review_handoff.v1`.
It may expose only safe `evidence_ref`, handoff status, owner handoff,
next required evidence, accepted/missing/rejected material summaries, rerun
command summaries, safe copy, evidence boundary, `not_proven`,
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unsupported schema or
boundary, unsafe raw fields, success claims, control claims, enabled actions,
`safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed as blocked/not_proven. It must
not expose raw artifacts, local paths, checksums, tracebacks, credentials,
raw ROS topics, `/cmd_vel`, serial/UART details, DB/queue URLs, OSS AK/SK, or
complete artifacts. The alias is not a command, ACK, cursor, ROS runtime,
motion command, task-orchestrator state transition, Start/Confirm/Cancel
enablement source, real phone/browser proof, HIL pass, route/elevator field
pass, dropoff/cancel completion, delivery result, or delivery success.
Mobile real-device field-trial acceptance-execution-pack metadata, including
`mobile_real_device_field_trial_acceptance_execution_pack`,
`mobile_real_device_field_trial_acceptance_execution_pack_summary`, and the
Robot diagnostics safe alias
`robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_pack_summary`,
follows the same metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_acceptance_execution_pack_gate`
boundary. Robot diagnostics may consume an explicit
`mobile_real_device_field_trial_acceptance_execution_pack_ref`, the matching
environment variables, a sanitized `latest_status` object, or a nested
`diagnostics` summary, but it may copy only whitelisted summary fields:
`source=software_proof`, safe `evidence_ref`, execution-pack status, source
review-handoff summary, owner handoff, next required evidence,
accepted/missing/rejected material summaries, execution-step summaries, rerun
command summaries, safe copy, evidence boundary, and `not_proven`. It must
always emit `safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, unsupported schema or
boundary, unsafe raw fields, success claims, control claims, enabled actions,
`safe_to_control=true`, `delivery_success=true`, `primary_actions_enabled=true`,
or non-`software_proof` source must fail closed as blocked/not_proven. The
alias must not expose raw artifacts, local paths, credentials, raw ROS topics,
`/cmd_vel`, serial/UART details, DB/queue URLs, OSS AK/SK, collect/dropoff/
cancel commands, ACK/terminal ACK/cursor state, Nav2/fixed-route execution,
HIL pass, real phone/browser proof, route/elevator field pass, dropoff/cancel
completion, delivery result, or delivery success.
Mobile real-device field-trial acceptance-execution-callback-intake metadata,
including `mobile_real_device_field_trial_acceptance_execution_callback_intake`,
`mobile_real_device_field_trial_acceptance_execution_callback_intake_summary`,
and the Robot diagnostics safe alias
`robot_diagnostics_mobile_real_device_field_trial_acceptance_execution_callback_intake_summary`,
follows the same metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_acceptance_execution_callback_intake_gate`
boundary. Robot diagnostics may consume an explicit
`mobile_real_device_field_trial_acceptance_execution_callback_intake_ref`, the
matching environment variables, a sanitized `latest_status` object, or a nested
`diagnostics` summary, but it may copy only whitelisted summary fields:
`source=software_proof`, safe `evidence_ref`, callback-intake status, source
execution-pack summary, owner handoff, next required evidence,
accepted/missing/rejected callback evidence, rerun guidance, safe copy,
evidence boundary, and `not_proven`. It must always emit
`safe_to_control=false`, `delivery_success=false`, and
`primary_actions_enabled=false`. Missing summary, schema mismatch, unsupported
boundary, unsafe `evidence_ref`, unsafe raw fields, rejected callback evidence,
missing callback material, success claims, control claims, enabled actions,
`safe_to_control=true`, `delivery_success=true`, `primary_actions_enabled=true`,
or non-`software_proof` source must fail closed as blocked/not_proven. The
alias must not expose raw artifacts, local paths, credentials, raw ROS topics,
`/cmd_vel`, serial/UART details, DB/queue URLs, OSS AK/SK, collect/dropoff/
cancel commands, ACK/terminal ACK/cursor state, Nav2/fixed-route execution,
HIL pass, real phone/browser proof, route/elevator field pass, dropoff/cancel
completion, delivery result, or delivery success.
Mobile real-device field-trial runbook-execution metadata, including
`mobile_real_device_field_trial_runbook_execution`,
`mobile_real_device_field_trial_runbook_execution_summary`, and
`mobile_real_device_field_trial_runbook_execution_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_runbook_execution_gate`
boundary. It may describe runbook step execution, operator observations,
missing evidence, redaction status, safe phone copy, source boundary,
ACK-not-delivery copy, support references, and `not_proven` items for a future
real-device field-trial runbook, but it is not a `trashbot.remote.v1`
command/status/ACK envelope, terminal ACK, backend action result, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness proof, real robot proof, dropoff success
proof, cancel completion proof, or delivery success proof. Robot-side
protocol normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and
must not persist `last_terminal_ack_id`. If these fields appear beside a
valid `collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`runbook_execution_recorded`, credential-bearing URLs, Authorization headers,
raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, or complete artifacts into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted_processing_only_not_delivery_success and must not be rendered
or interpreted as runbook execution completion, robot execution, delivery
success, production readiness, HIL, dropoff success, or cancel completion.
Mobile real-device field-trial retest-execution metadata, including
`mobile_real_device_field_trial_retest_execution`,
`mobile_real_device_field_trial_retest_execution_summary`, and
`mobile_real_device_field_trial_retest_execution_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`
boundary. It may describe retest step execution, operator observations,
missing evidence, redaction status, safe phone copy, source boundary,
ACK-not-delivery copy, support references, and `not_proven` items for a future
real-device field-trial retest, but it is not a `trashbot.remote.v1`
command/status/ACK envelope, terminal ACK, backend action result, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness proof, real robot proof, dropoff success
proof, cancel completion proof, or delivery success proof. Robot-side
protocol normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and
must not persist `last_terminal_ack_id`. If these fields appear beside a
valid `collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`field_trial_retest_executed`, credential-bearing URLs, Authorization headers,
raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, or complete artifacts into robot status, ACK, backend action
result, normalized command payload, terminal result, or cursor state. These
fields also must not enable Start Delivery, Confirm Dropoff, or Cancel; button
enablement remains governed by `command_safety` and `action_permissions`. ACK
remains accepted_processing_only_not_delivery_success and must not be rendered
or interpreted as retest execution completion, robot execution, delivery
success, production readiness, HIL, dropoff success, or cancel completion.
Mobile real-device field-trial evidence-record metadata, including
`mobile_real_device_field_trial_evidence_record`,
`mobile_real_device_field_trial_evidence_record_summary`,
`mobile_real_device_field_trial_evidence_record_copy`, and
`mobile_real_device_field_trial_evidence_record_archive`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`
boundary. It may describe real-device field-trial observations, device/browser
and production-app notes, PWA install prompt/user-choice notes, offline/touch
or visual observations, redaction/source boundary, safe copy/archive refs,
operator/support notes, ACK-not-delivery copy, and `not_proven` items for a
future real-device field trial, but it is not a `trashbot.remote.v1`
command/status/ACK envelope, terminal ACK, backend action result, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, production-readiness grant, real robot proof, dropoff success
proof, cancel completion proof, or delivery success proof. Robot-side protocol
normalization must strip these fields from valid command objects;
metadata-only responses must not invoke `collect`, `confirm_dropoff`, or
`cancel`, must not POST ACK, must not advance in-memory `last_ack_id`, and
must not persist `last_terminal_ack_id`. If these fields appear beside a
valid `collect`, `confirm_dropoff`, or `cancel` command, the robot bridge must
execute only the `trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`field_trial_evidence_recorded`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, raw intake JSON, or complete artifacts into robot status, ACK,
backend action result, normalized command payload, terminal result, or cursor
state. These fields also must not enable Start Delivery, Confirm Dropoff, or
Cancel; button enablement remains governed by `command_safety` and
`action_permissions`. ACK remains accepted_processing_only_not_delivery_success
and must not be rendered or interpreted as evidence-record completion, robot
execution, delivery success, production readiness, HIL, dropoff success, or
cancel completion.
Mobile real-device field-trial evidence-verdict metadata, including
`mobile_real_device_field_trial_evidence_verdict`,
`mobile_real_device_field_trial_evidence_verdict_summary`, and
`mobile_real_device_field_trial_evidence_verdict_copy`, follows the same
phone/support/product metadata-only rule for the
`software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`
boundary. It may describe evidence review verdicts, missing evidence, retest
requests, redaction/source boundary, safe copy refs, ACK-not-delivery copy,
and `not_proven` items for a future real-device field trial, but it is not a
`trashbot.remote.v1` command/status/ACK envelope, terminal ACK, backend action
result, cursor instruction, ROS2 action result, Nav2/fixed-route result, WAVE
ROVER feedback, HIL result, production-readiness grant, real robot proof,
dropoff success proof, cancel completion proof, or delivery success proof.
Robot-side protocol normalization must strip these fields from valid command
objects; metadata-only responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. If these fields
appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command, the
robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `delivery_success`, `dropoff_success`, `cancel_completed`,
`production_ready`, `production_app_ready`, `hil_pass`,
`field_trial_evidence_verdict`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, local paths, tracebacks,
checksums, raw verdict JSON, or complete artifacts into robot status, ACK,
backend action result, normalized command payload, terminal result, or cursor
state. These fields also must not enable Start Delivery, Confirm Dropoff, or
Cancel; button enablement remains governed by `command_safety` and
`action_permissions`. ACK remains accepted_processing_only_not_delivery_success
and must not be rendered or interpreted as evidence-verdict completion, robot
execution, delivery success, production readiness, HIL, dropoff success, or
cancel completion.
Cloud-hosted PWA/static-shell metadata, including `cloud_hosted_pwa`,
`static_shell_metadata`, `pwa_static_surface`, and
`cloud_hosted_mobile_web_gate`, is the phone/static surface contract for a
hosted PWA or static mobile shell. It may describe hosted URLs, manifest/start
URLs, cache boundary, safe phone copy, screenshot/evidence refs, and
software-proof status for the mobile surface, but it is not part of the
`trashbot.remote.v1` command/status/ACK envelope. Robot-side protocol
normalization must strip these fields from valid command objects; metadata-only
responses or static PWA GET responses must not invoke `collect`,
`confirm_dropoff`, or `cancel`, must not POST ACK, must not advance in-memory
`last_ack_id`, and must not persist `last_terminal_ack_id`. These metadata
fields must not be copied into robot status, ACK, backend action result, or
normalized command payload, and must not expand robot command payload shape
beyond the command envelope. ACK remains accepted/processing evidence only and
must not be rendered or interpreted as browser proof, static-shell proof, or
delivery success.
Mobile PWA installability metadata, including
`cloud_hosted_mobile_pwa_installability_gate`,
`pwa_installability_metadata`, and `browser_installability_bundle`, is the
phone/browser static-surface proof for manifest, service worker, start URL,
standalone display mode, cache boundary, and local/Docker installability
evidence. It is not a robot command, backend action result, ACK payload, cursor
instruction, ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback,
HIL result, real phone-device proof, real browser-install prompt proof, or
delivery success proof. Robot-side protocol normalization must strip these
fields from valid command objects; metadata-only responses must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, must not advance
in-memory `last_ack_id`, and must not persist `last_terminal_ack_id`. If those
fields appear beside a valid `collect`, `confirm_dropoff`, or `cancel`
command, the robot bridge must execute only the `trashbot.remote.v1` command
envelope and must not copy `trigger_robot_action`, `next_action`,
`cursor_override`, `delivery_success`, credential-bearing URLs, Authorization
headers, raw ROS topics, `/cmd_vel`, serial devices, or hardware parameters
into robot status, ACK, backend action result, normalized command payload, or
cursor state. ACK remains accepted/processing evidence only and must not be
rendered or interpreted as PWA installability proof, browser proof, or delivery
success.
Operation-log metadata, including `operation_log` and `phone_operation_log`, is
phone/support metadata for recent events, blocked reasons, pending ACK,
offline/recovery state, manual takeover, and support handoff copy. It is not a
robot command, ACK, cursor instruction, ROS2 action result, WAVE ROVER feedback,
Nav2/fixed-route result, HIL result, or delivery success proof. The robot bridge
must ignore those fields outside the `trashbot.remote.v1` command envelope, and
protocol normalization must strip them from any command object before execution.

Cloud worker migration rehearsal metadata, including
`cloud_worker_migration_rehearsal` and
`cloud_worker_migration_rehearsal_summary`, is a metadata-only diagnostics and
preflight summary for
`software_proof_docker_cloud_worker_migration_rehearsal_gate`. Robot diagnostics
may expose only safe summary, schema, boundary, migration rehearsal status,
worker rehearsal status, retry hint, `not_proven`, `production_ready=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. Missing
artifacts, unsupported schema/boundary, unsafe copy, credential-bearing fields,
success wording, `production_ready=true`, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed. These fields are not a
`trashbot.remote.v1` command/status/ACK envelope, backend action result, ACK
payload, terminal ACK, cursor instruction, ROS2 action result, Nav2 or
fixed-route result, WAVE ROVER feedback, HIL result, real worker/migration
evidence, or delivery success proof. Metadata-only responses must not invoke
`collect`, `confirm_dropoff`, or `cancel`, must not POST ACK, must not advance
in-memory `last_ack_id`, and must not persist `last_terminal_ack_id`. If these
fields appear beside a valid `collect`, `confirm_dropoff`, or `cancel` command,
the robot bridge must execute only the `trashbot.remote.v1` command envelope and
must not copy `trigger_robot_action`, `next_action`, `cursor_override`,
`terminal_ack`, `delivery_success`, `production_ready`,
`primary_actions_enabled`, credentials, DB/queue URLs, raw ROS topics,
`/cmd_vel`, serial devices, hardware parameters, or rehearsal internals into
robot status, ACK, backend action result, normalized command payload, or cursor
state. ACK remains accepted/processing evidence only and must not be interpreted
as cloud worker migration success, production readiness, or delivery success.

Cloud worker cutover drain metadata, including `cloud_worker_cutover_drain` and
`cloud_worker_cutover_drain_summary`, is a metadata-only diagnostics and
preflight summary for
`software_proof_docker_cloud_worker_cutover_drain_gate`. Robot diagnostics may
expose only safe summary, schema, boundary, drain status, cursor summary,
terminal ACK summary, retry hint, `not_proven`, `production_ready=false`,
`delivery_success=false`, and `primary_actions_enabled=false`. Missing
artifacts, unsupported schema/boundary, unsafe copy, credential-bearing fields,
success wording, `production_ready=true`, `delivery_success=true`, or
`primary_actions_enabled=true` must fail closed. The summary is not a
`trashbot.remote.v1` command/status/ACK envelope, command payload, backend
action result, delivery result, ACK completion, terminal ACK, cursor instruction,
ROS2 action result, Nav2/fixed-route result, WAVE ROVER feedback, HIL result,
real worker cutover evidence, or delivery success proof. Metadata-only
responses must not invoke `collect`, `confirm_dropoff`, or `cancel`, must not
POST ACK, must not advance in-memory `last_ack_id`, and must not persist
`last_terminal_ack_id`. If these fields appear beside a valid `collect`,
`confirm_dropoff`, or `cancel` command, the robot bridge must execute only the
`trashbot.remote.v1` command envelope and must not copy
`trigger_robot_action`, `next_action`, `cursor_override`, `terminal_ack`,
`terminal_ack_summary`, `delivery_success`, `production_ready`,
`primary_actions_enabled`, credentials, DB/queue URLs, raw ROS topics,
`/cmd_vel`, serial devices, hardware parameters, or drain internals into robot
status, ACK, backend action result, normalized command payload, delivery result,
or cursor state. ACK remains accepted/processing evidence only and must not be
interpreted as cloud worker cutover drain completion, production readiness, or
delivery success.

Allowed remote commands are `collect`, `confirm_dropoff`, and `cancel`. The bridge only calls behavior-layer ROS contracts and never exposes direct base velocity control.
For `collect`, `acked` means the command was accepted/submitted locally; final delivery success or failure is reported through later status payloads.

#### Remote readiness fields

`operator_gateway` local/mock cloud status and `remote_bridge` degraded status use
the same phone-safe readiness shape. These fields are a control-plane contract;
they are not hardware, Nav2, fixed-route, or delivery success evidence.

| Field | Contract |
| --- | --- |
| `remote_ready` | `true` only when the local/mock control-plane is healthy enough for the next phone step. It does not prove real cloud, 4G, HIL, or trash delivery. |
| `cloud_reachable` | Whether the configured cloud/mock endpoint is reachable for the current operation. |
| `auth_state` | One of the phone-safe auth states used by the current implementation, including `mock_not_required`, `required`, `authorized`, and `auth_failed`. |
| `degradation_state` | One of the phone-safe degradation states used by the current implementation, including `ok`, `status_stale`, `command_pending`, `auth_failed`, `cloud_unreachable`, and `malformed_response`. |
| `retry_hint` | Phone/operator recovery hint such as `ok`, `wait_for_robot_status`, `wait_for_command_ack`, `check_auth`, `retry_cloud`, or `contact_support`. |
| `safe_phone_copy` | Plain-language copy suitable for phone UI. It must not contain raw JSON, raw exceptions, bearer tokens, Authorization headers, `/cmd_vel`, ROS topic names, serial devices, baudrate, WAVE ROVER parameters, or cloud URLs with credentials. |

#### Failure and cursor contract

| Condition | Required behavior |
| --- | --- |
| Cloud unreachable while posting status or polling command | Publish or retain degraded status, do not execute a new local action from untrusted data, do not advance or persist terminal cursor. |
| HTTP 401/403 auth failure | Map to `auth_state=auth_failed`, `degradation_state=auth_failed`, and a phone-safe retry hint. Do not leak tokens or raw headers. |
| Malformed command/status/ACK response | Map to `degradation_state=malformed_response`; do not submit a local action goal, do not advance cursor, and do not fabricate successful ACK. |
| Terminal ACK post failure | Keep the local command result available for retry, but do not update `last_terminal_ack_id` in memory or in `cursor_state_path`. |
| Terminal ACK post success | Only then may the bridge advance `last_terminal_ack_id` and atomically persist cursor state. |

ACK remains a command-envelope processing state. It is never a delivery result
and must not be used to claim Nav2/fixed-route success, WAVE ROVER movement, or
HIL pass.

Real-material readiness board diagnostics may expose
`real_material_readiness_board`, `real_material_readiness_board_summary`, and
the Robot safe alias
`robot_diagnostics_real_material_readiness_board_summary` from an explicit
`real_material_readiness_board_ref`,
`TRASHBOT_REAL_MATERIAL_READINESS_BOARD`,
`TRASHBOT_REAL_MATERIAL_READINESS_BOARD_SUMMARY`, top-level status fields, or
an already sanitized nested diagnostics summary source. The source JSON must
use `schema=trashbot.real_material_readiness_board.v1` or
`schema=trashbot.real_material_readiness_board_summary.v1`; when an
`evidence_boundary` is present it must remain
`software_proof_docker_real_material_readiness_board_gate`. This field is
metadata-only and routing-only Robot diagnostics support for missing real
materials: it may expose only sanitized material groups, safe `evidence_ref`,
owner handoff, next required evidence, safe copy, `source=software_proof`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`safe_to_control=false`. Missing input, unreadable input, unsupported schema or
boundary, `source` other than `software_proof`, status other than
`not_proven`, unsafe copy, success/control claims, `delivery_success=true`,
`primary_actions_enabled=true`, or `safe_to_control=true` sources fail closed
as blocked/not_proven. The fields do not trigger `/api/collect`, Start
Delivery, Confirm Dropoff, Cancel, dropoff, cancel, ACK, remote ACK, cursor
advance/persistence, terminal ACK, Nav2, WAVE ROVER, serial/UART, HIL,
material collection, production readiness, Objective 5 external proof,
dropoff/cancel completion, or delivery success, and they are not
command/status/ACK robot contract fields.

| Type | Payload | Local action |
| --- | --- | --- |
| `collect` | Required `target`, optional `trash_type` | Starts `/trashbot/collect_trash`; malformed commands without a non-empty `target` are failed before any local action goal is sent. |
| `confirm_dropoff` | optional `accepted` | Calls `/trashbot/confirm_dropoff`. |
| `cancel` | empty object | Cancels the active collection goal when one exists. |

### Task Record

Every success, cancellation, missing target, navigation failure, dropoff failure, and unsupported-mode failure writes a JSON task record with `started_at`, `ended_at`, `delivery_mode`, `target`, `return_target`, `nav_attempts`, `nav_results`, `dropoff_result`, `detection_snapshot_refs`, `config`, `final_status`, and `error_message`. `dropoff_result` records `success`, `result_code`, `message`, `source`, and `elapsed_sec`; `manual_confirm_timeout` and `manual_rejected` are failures.

### Terminal Diagnostics

`TrashCollection.Result` exposes machine-readable terminal diagnostics:

| Field | Contract |
| --- | --- |
| `error_code` | Empty on success. On failure/cancel, set from the terminal state-machine event, such as `timed_out`, `navigation_failed`, `dropoff_failed`, `return_failed`, or `canceled`. |
| `final_state` | Final delivery state-machine state, such as `idle` or `error`. Operator and remote status payloads propagate this field so phone/cloud clients do not need to parse human text. |
