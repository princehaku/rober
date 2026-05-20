# Evidence Contracts

## mobile_elevator_action_feedback

`TrashCollection.Feedback.current_step=elevator:<phase>` is the phone-safe,
read-only realtime feedback contract for elevator-assisted delivery display.
It reuses the existing ROS action feedback field and does not add a robot
command, ACK payload, delivery result, route result, or diagnostics artifact.

Allowed phase values are `waiting_elevator_open`, `entering_elevator`,
`requesting_floor_help`, `waiting_target_floor`, `exiting_elevator`, and
`resume_delivery`. Mobile and diagnostics consumers must fail closed for
missing fields, non-`elevator:` prefixes, or unknown phases. The existing
`operator_gateway` status payload exposes the field as `current_step`, while
`operator_gateway_http` may derive phone-safe `elevator_assist` copy from the
same known phase family.

Phone-safe copies for this contract must not expose raw ROS topics, artifact
paths, serial/UART identifiers, baudrate, WAVE ROVER parameters, credentials,
DB/queue URLs, raw JSON, complete artifacts, or checksums. They may expose only
the current phase, bounded Chinese help copy, and conservative support state.

This contract remains `source=software_proof` / `not_proven` and must preserve
`delivery_success=false` and `primary_actions_enabled=false`. It does not prove
real elevator operation, real phone-device/browser validation, real
Nav2/fixed-route execution, WAVE ROVER/UART/HIL, dropoff success, cancel
completion, or delivery success. Start Delivery, Confirm Dropoff, and Cancel
must stay governed by the existing command-safety gates and must not be enabled
by this feedback display.

## elevator_action_feedback_trace

Robot `task_record` now persists the realtime elevator action feedback chain as
`elevator_action_feedback_trace`. The trace schema is
`trashbot.elevator_action_feedback_trace.v1`; Robot diagnostics exposes the
phone-safe alias
`robot_diagnostics_elevator_action_feedback_trace_summary` with summary schema
`trashbot.robot_diagnostics_elevator_action_feedback_trace_summary.v1`.

The trace is derived only from existing elevator assist events and the known
feedback phase table behind `TrashCollection.Feedback.current_step=elevator:<phase>`.
It does not change the ROS action schema, add a topic/service, or alter robot
motion. Required fields are `schema`, `status`, `source=software_proof`,
`source_boundary`, `safe_evidence_ref`, `same_evidence_ref_required`, `phases`,
`current_step`, `message`, `percent`, `event`, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

Diagnostics may expose only metadata-safe values: phase names, `current_step`,
bounded message text, percent, event, source boundary, and safe `evidence_ref`.
It must fail closed as `blocked_missing_elevator_action_feedback_trace` when the
task record lacks a valid trace or has no safe `elevator:` phase entries.

This contract is software proof only. It does not prove real elevator
operation, real Nav2/fixed-route execution, real phone-device/browser
validation, WAVE ROVER/UART/HIL, dropoff completion, cancel completion, or
delivery success.

## pr5_review_thread_closeout

`pc-tools/evidence/pr5_review_thread_closeout_gate.py` generates the PC-only
review closeout gate for PR #5 unresolved review threads.

- Artifact schema: `trashbot.pr5_review_thread_closeout.v1`
- Summary schema: `trashbot.pr5_review_thread_closeout_summary.v1`
- Evidence boundary:
  `software_proof_docker_pr5_review_thread_closeout_gate`
- Source inputs: `docs/product/production_hardware_boundary.md`,
  `docs/vendor/VENDOR_INDEX.md`, `OKR.md`, and an optional safe PR #5 thread
  summary with schema `trashbot.pr5_review_thread_summary.v1`. The built-in
  thread summary contains only thread keys, severities, and topics; it does not
  copy raw GitHub review bodies or tokens.
- Decision values: `ready_to_close_on_mainline_docs`,
  `blocked_pending_real_materials`, and
  `still_open_missing_current_evidence`.
- CLI outputs: use `--output-dir <dir>` to write
  `pr5_review_thread_closeout.json` and
  `pr5_review_thread_closeout_summary.json` with the default names. Explicit
  `--output` and `--summary-output` paths still take precedence when supplied.

The gate maps the P1 hardware-boundary thread to
`ready_to_close_on_mainline_docs` only when the Default Hardware Set is separate
from the pending Navigation/Sensing target baseline and
`docs/vendor/VENDOR_INDEX.md` is cited as source boundary. It maps the P2 OKR
thread to `ready_to_close_on_mainline_docs` only when `OKR.md` 4.1 and the
priority narrative both identify Objective 5 as the lowest current objective.
It maps the mandatory sensor citation thread to
`blocked_pending_real_materials` when vendor/source citation exists but real
2D LiDAR / ToF SKU, receipt, installation, wiring, calibration, and HIL-entry
materials are still missing.

Missing source docs, unsupported thread summary schema, unsafe copy, raw local
paths, raw serial/UART paths, raw credentials, procurement/HIL/field success
claims, `delivery_success=true`, or `primary_actions_enabled=true` fail closed.
Every output must remain `source=software_proof`, `overall_status=not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

This contract is a docs/review closeout decision gate only. It does not prove
real hardware procurement, real 2D LiDAR, real ToF, real WAVE ROVER/UART/HIL,
real Nav2/fixed-route execution, real route/elevator field pass, real
phone/browser validation, Objective 5 external proof, or delivery success.

## route_task_field_retest_acceptance_review_decision

`pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py`
generates the PC-only review decision gate after
`route_task_field_retest_acceptance_brief.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_acceptance_brief.v1` and
  `trashbot.route_task_field_retest_acceptance_brief_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Decision values:
  `ready_for_controlled_field_retest_not_proven`,
  `needs_route_elevator_material_backfill_not_proven`,
  `needs_owner_handoff_not_proven`, `evidence_ref_mismatch_rerun_not_proven`,
  `blocked_acceptance_brief_not_ready`,
  `unsupported_acceptance_brief_schema_not_proven`, and
  `rejected_unsafe_acceptance_brief_claim_not_proven`.

The output always includes `review_decision`, `material_status`,
`owner_handoff`, `next_required_evidence`, `rerun_commands`, `safe_copy`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`,
`same_evidence_ref_required=true`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`.

Decision mapping is fail-closed. A supported, safe, ready acceptance brief with
matched evidence_ref, complete packet metadata, and owner handoff maps to
`ready_for_controlled_field_retest_not_proven`. Missing route/elevator packet
metadata maps to `needs_route_elevator_material_backfill_not_proven`. Missing
handoff maps to `needs_owner_handoff_not_proven`. Mismatched or weak
same-evidence-ref state maps to `evidence_ref_mismatch_rerun_not_proven`.
Unsupported schema, missing input, bad JSON, unsupported boundary, unsafe copy,
raw paths, credentials, ROS topics, serial/UART/WAVE ROVER text,
success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed.

This contract is software proof only. It does not prove a real route/elevator
field outcome, HIL pass, real Nav2/fixed-route execution, real delivery
success, real phone/browser validation, O5 external cloud proof, or any primary
robot action being enabled.

## route_task_field_retest_acceptance_execution_pack

`pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py`
generates the PC-only execution pack gate after
`route_task_field_retest_acceptance_review_decision.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_pack.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_acceptance_review_decision.v1` and
  `trashbot.route_task_field_retest_acceptance_review_decision_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
  CLI sources may also use `file:<path>` or `env:<VAR>` to locate the same JSON.
- Status values:
  `ready_for_field_retest_acceptance_execution_pack_not_proven`,
  `blocked_acceptance_review_decision_not_ready`,
  `evidence_ref_mismatch_rerun_not_proven`,
  `unsupported_acceptance_review_decision_schema_not_proven`, and
  `rejected_unsafe_acceptance_review_decision_claim_not_proven`.

The output always includes `execution_pack_status`,
`review_decision_source`, `owner_checklist`, `rerun_commands`,
`safe_evidence_bundle`, `required_route_elevator_materials`,
`handoff_owner`, `next_required_evidence`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`,
`same_evidence_ref_required=true`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`.

Execution-pack mapping is fail-closed. A supported, safe
`ready_for_controlled_field_retest_not_proven` review decision with matched
evidence_ref maps to
`ready_for_field_retest_acceptance_execution_pack_not_proven`. Non-ready review
decisions stay `blocked_acceptance_review_decision_not_ready`. Mismatched,
missing, or weak same-evidence-ref state maps to
`evidence_ref_mismatch_rerun_not_proven`. Unsupported schema, missing input, bad
JSON, unsupported boundary, unsafe copy, raw paths, credentials, ROS topics,
serial/UART/WAVE ROVER text, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` fail closed.

This contract is software proof only. It does not prove a real route/elevator
field outcome, HIL pass, real Nav2/fixed-route execution, real delivery
success, real dropoff/cancel completion, real phone/browser validation, O5
external cloud proof, or any primary robot action being enabled.

## route_task_field_retest_acceptance_execution_callback_intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py`
generates the PC-only callback intake gate after
`route_task_field_retest_acceptance_execution_pack.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_pack.v1` and
  `trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
  CLI sources may also use `file:<path>` or `env:<VAR>` to locate the same JSON.
- Allowed callback packet inputs:
  a safe callback packet with optional
  `trashbot.route_task_field_retest_acceptance_execution_callback_packet.v1`
  or `_summary.v1` schema. The packet must stay inside the whitelist:
  `safe_evidence_ref`, `same_evidence_ref_required`, `material_responses`,
  `received_materials`, `missing_materials`, `rejected_materials`,
  `owner_next_steps`, `next_required_evidence`, `safe_copy`,
  `delivery_success=false`, and `primary_actions_enabled=false`.
- Status values:
  `ready_for_field_retest_acceptance_execution_callback_intake_not_proven`,
  `blocked_missing_execution_pack_json`, `blocked_missing_callback_json`,
  `blocked_bad_json`, `blocked_unsupported_execution_pack_schema_or_boundary`,
  `blocked_unsupported_callback_packet_schema_or_fields`,
  `blocked_missing_evidence_ref`, `blocked_same_evidence_ref_mismatch`,
  `blocked_same_evidence_ref_not_required`, `blocked_unsafe_copy`,
  `blocked_weak_callback_fields`, `blocked_execution_pack_not_ready`,
  `blocked_rejected_callback_materials`, and
  `blocked_missing_callback_materials`.

The output always includes `callback_intake_status`,
`source_execution_pack`, `safe_callback_packet`, `evidence_ref_status`,
`required_route_elevator_materials`, `received_materials`,
`missing_materials`, `rejected_materials`, `owner_next_steps`,
`next_required_evidence`, `rerun_commands`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`,
`same_evidence_ref_required=true`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`.

Callback-intake mapping is fail-closed. A supported, safe
`ready_for_field_retest_acceptance_execution_pack_not_proven` source with
matched `evidence_ref` and a callback packet that marks every required
route/elevator material as received maps to
`ready_for_field_retest_acceptance_execution_callback_intake_not_proven`.
Missing materials stay `blocked_missing_callback_materials`. Rejected or
unknown callback material entries stay `blocked_rejected_callback_materials`.
Mismatched, missing, or weak same-evidence-ref state maps to a blocked
same-evidence-ref status. Unsupported schema, missing input, bad JSON,
unsupported boundary, weak callback field types, raw paths, credentials, ROS
topics, hardware transport details, checksum text, full raw artifact text,
success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed.

This contract is software proof only. It does not prove a real route/elevator
field outcome, HIL pass, real Nav2/fixed-route execution, real delivery
success, real dropoff/cancel completion, real phone/browser validation, O5
external cloud proof, or any primary robot action being enabled.

## route_task_field_retest_acceptance_execution_callback_review_decision

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py`
generates the PC-only review decision gate after
`route_task_field_retest_acceptance_execution_callback_intake.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1` and
  `trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Decision values:
  `ready_for_controlled_field_rerun`, `needs_material_backfill`,
  `evidence_ref_mismatch_rerun`, and fail-closed unsafe/unsupported states such
  as `rejected_unsafe_callback`.

The output always includes `review_decision`, `status_reasons`,
`source_callback_intake`, `field_rerun_readiness`, `owner_handoff`,
`next_required_evidence`, `rerun_commands`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`,
`same_evidence_ref_required=true`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`.

Decision mapping is fail-closed. A supported, safe
`ready_for_field_retest_acceptance_execution_callback_intake_not_proven` source
with matched evidence_ref, matched same-evidence-ref status, received callback
materials, and no missing or rejected materials maps to
`ready_for_controlled_field_rerun`. Missing, rejected, empty, unsupported, or
non-ready callback-intake material states map to `needs_material_backfill`.
Mismatched or weak same-evidence-ref state maps to
`evidence_ref_mismatch_rerun`. Missing input, bad JSON, unsupported schema,
unsupported boundary, unsafe copy, raw paths, credentials, ROS topics,
serial/UART/WAVE ROVER text, checksums, raw artifact text,
success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed.

This contract is software proof only. It does not prove a real route/elevator
field pass, real Nav2/fixed-route proof, task record/completion signal,
dropoff/cancel completion, delivery success, HIL pass, real phone/browser
validation, O5 external proof, or any primary robot action being enabled.

## route_task_field_retest_acceptance_execution_callback_review_handoff

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py`
generates the PC-only handoff gate after
`route_task_field_retest_acceptance_execution_callback_review_decision.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Handoff values:
  `ready_for_acceptance_execution_callback_review_handoff`,
  `needs_owner_follow_up`, `needs_acceptance_execution_callback_rerun`,
  `evidence_ref_mismatch_rerun`, and fail-closed unsafe states such as
  `blocked_unsafe_review_handoff`.

The Robot diagnostics consumer exposes only phone-safe metadata from the
artifact, summary, or compatible nested summary: handoff status, source review
decision/status, safe `evidence_ref`, owner handoff, next required evidence,
safe rerun hint, boundary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

This contract is software proof only. It does not prove real route/elevator
execution, Nav2/fixed-route proof, ACK, cursor persistence, dropoff/cancel
completion, delivery success, HIL pass, WAVE ROVER feedback, real phone/browser
validation, O5 external proof, or any primary robot action being enabled.

## route_task_field_retest_acceptance_execution_handoff_intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_handoff_intake.py`
generates the PC-only owner handoff intake gate after
`route_task_field_retest_acceptance_execution_callback_review_handoff.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1`
  under
  `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Optional owner intake input:
  phone-safe owner callback/intake JSON with the same safe `evidence_ref`.
- Handoff intake values:
  `ready_for_controlled_field_rerun_queue`, `needs_owner_ack`,
  `needs_acceptance_execution_handoff_backfill`,
  `evidence_ref_mismatch_rerun`, and fail-closed unsafe states such as
  `blocked_unsafe_handoff_intake`.

The Robot diagnostics consumer exposes only phone-safe metadata from the
artifact, summary, or compatible nested summary: handoff intake status, source
handoff status, safe `evidence_ref`, owner acknowledgement state, owner
handoff, next required evidence, safe rerun hint, boundary, `not_proven`,
`delivery_success=false`, and `primary_actions_enabled=false`.

This contract is software proof only. It does not prove real route/elevator
execution, Nav2/fixed-route proof, ACK, cursor persistence, dropoff/cancel
completion, delivery success, HIL pass, WAVE ROVER feedback, real phone/browser
validation, Objective 5 external proof, or any primary robot action being
enabled.

## route_task_field_retest_acceptance_execution_rerun_queue

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py`
generates the PC-only controlled rerun queue gate after
`route_task_field_retest_acceptance_execution_handoff_intake.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1`
  under
  `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Optional queue request input:
  owner-safe queue metadata with safe `evidence_ref`, owner acknowledgement,
  requested rerun reason, and next-required evidence.
- Rerun queue values:
  `queued_for_controlled_field_rerun_not_proven`,
  `needs_owner_ack_before_queue`,
  `needs_acceptance_execution_rerun_queue_backfill`,
  `evidence_ref_mismatch_rerun_queue`,
  `blocked_unsafe_rerun_queue`, and
  `blocked_unsupported_handoff_intake`.

The Robot diagnostics and mobile consumers should expose only phone-safe
metadata from the artifact, summary, or compatible nested summary: rerun queue
status, source handoff intake status, safe `evidence_ref`, owner
acknowledgement state, owner handoff, next required evidence, safe rerun hint,
boundary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

## route_task_field_retest_acceptance_execution_rerun_result_intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py`
generates the PC-only rerun result intake gate after
`route_task_field_retest_acceptance_execution_rerun_queue.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`
  under
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Optional rerun result packet input:
  owner-safe result metadata with safe `evidence_ref`, explicit ready/submitted
  packet state, result material categories, and an optional safe operator note.
- Rerun result intake values:
  `ready_for_acceptance_execution_rerun_result_review_not_proven`,
  `needs_acceptance_execution_rerun_result_backfill`,
  `evidence_ref_mismatch_rerun_result`,
  `blocked_unsafe_rerun_result`, and
  `blocked_unsupported_rerun_queue`.

The Robot diagnostics and mobile consumers should expose only phone-safe
metadata from the artifact, summary, or compatible nested summary: rerun result
intake status, source rerun queue status, safe `evidence_ref`, owner-safe rerun
result packet summary, owner handoff, next required evidence, safe review hint,
boundary, `not_proven`, `delivery_success=false`, and
`primary_actions_enabled=false`.

This gate does not read real field material directories, does not execute a
controlled rerun, does not access ROS graph, Nav2/fixed-route runtime,
serial/UART, WAVE ROVER, real phone/browser runtime, external cloud, OSS/CDN,
DB/queue, or 4G, and does not prove real route/elevator field pass, delivery
success, HIL, real phone/browser proof, or Objective 5 external proof. Unsafe
copy, raw artifact text, local paths, checksums, credentials, DB/queue URLs,
ROS topic names, `/cmd_vel`, serial/UART/baudrate or WAVE ROVER low-level
control detail, success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true` must map to `blocked_unsafe_rerun_result`.

This contract is software proof only. It does not prove a real controlled field
rerun, route/elevator execution, Nav2/fixed-route proof, ACK, cursor
persistence, dropoff/cancel completion, delivery success, HIL pass, WAVE ROVER
feedback, real phone/browser validation, Objective 5 external proof, or any
primary robot action being enabled.

## route_task_field_retest_acceptance_execution_rerun_result_review_decision

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`
generates the PC-only review decision gate after
`route_task_field_retest_acceptance_execution_rerun_result_intake.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1`
  under
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Decision status values:
  `ready_for_acceptance_execution_rerun_result_handoff`,
  `needs_acceptance_execution_rerun_result_backfill`,
  `evidence_ref_mismatch_rerun_result`,
  `blocked_unsafe_rerun_result`, and
  `blocked_unsupported_rerun_result_intake`.

The output always includes `source=software_proof`, `safe_evidence_ref`,
`same_evidence_ref_required=true`, source rerun result intake metadata,
provided and missing rerun result material categories,
`review_decision_package`, `owner_handoff`, `next_required_evidence`,
`rerun_commands`, `safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`.

Decision mapping is fail-closed. A supported ready intake with matching safe
evidence_ref and all required material categories maps to
`ready_for_acceptance_execution_rerun_result_handoff`. Missing route completion
signal, task record, Nav2/fixed-route runtime log, dropoff/cancel completion,
delivery result, elevator door state, target floor confirmation, or human
assistance record maps to
`needs_acceptance_execution_rerun_result_backfill`. Mismatched evidence_ref,
missing evidence_ref, or weak `same_evidence_ref_required` maps to
`evidence_ref_mismatch_rerun_result`. Missing JSON, bad JSON, unreadable JSON,
non-object JSON, unsupported schema, or unsupported boundary maps to
`blocked_unsupported_rerun_result_intake`. Unsafe copy, raw paths, checksum
text, credentials, DB/queue URLs, ROS topic names, `/cmd_vel`,
serial/UART/WAVE ROVER text, raw artifact text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`blocked_unsafe_rerun_result`.

This contract is software proof only. It does not prove a real route/elevator
field pass, real controlled rerun execution, Nav2/fixed-route proof, task
record/completion signal, dropoff/cancel completion, delivery success, HIL
pass, real phone/browser validation, Objective 5 external proof, or any
primary robot action being enabled.

## route_task_field_retest_acceptance_execution_rerun_result_review_handoff

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py`
generates the dependency-free PC owner handoff gate after
`route_task_field_retest_acceptance_execution_rerun_result_review_decision.py`.
It is the PR #4 real route/elevator field backfill preparation layer, not a
real field pass or delivery-success proof.

- Artifact schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1`
- Summary schema:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1`
  and
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1`
  under
  `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`
  only. Wrapper or nested JSON is allowed only through whitelisted
  `summary`, `artifact`, `safe_copy`, diagnostics, mobile, `payload`, or `data`
  keys.
- Handoff status values:
  `ready_for_acceptance_execution_rerun_result_owner_handoff`,
  `needs_acceptance_execution_rerun_result_material_backfill`,
  `evidence_ref_mismatch_rerun_result_handoff_blocked`,
  `blocked_unsafe_rerun_result_handoff_copy`, and
  `blocked_unsupported_rerun_result_review_decision`.

The output always includes `source=software_proof`, `safe_evidence_ref`,
`same_evidence_ref_required=true`, source review decision metadata,
`owner_role`, `owner_handoff`, `next_required_evidence`, `rerun_summary`,
`safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`.

Mapping is fail-closed. A supported source decision with
`ready_for_acceptance_execution_rerun_result_handoff`, matching safe
evidence_ref, `review_decision_package.ready=true`, and all required material
categories maps to `ready_for_acceptance_execution_rerun_result_owner_handoff`.
Missing elevator door state, target floor confirmation, human assistance
record, Nav2/fixed-route runtime log, task record, route completion signal,
dropoff/cancel completion, or delivery result maps to
`needs_acceptance_execution_rerun_result_material_backfill`. Mismatched
evidence_ref, missing evidence_ref, or weak `same_evidence_ref_required` maps
to `evidence_ref_mismatch_rerun_result_handoff_blocked`. Unsafe copy, raw
artifact text, local paths, checksum text, credentials, DB/queue URLs, ROS
topic names, `/cmd_vel`, serial/UART/WAVE ROVER text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`blocked_unsafe_rerun_result_handoff_copy`. Missing JSON, bad JSON, unreadable
JSON, non-object JSON, unsupported schema, unsupported boundary, or unsupported
source decision status maps to
`blocked_unsupported_rerun_result_review_decision`.

This contract is software proof only. It does not read material directories,
parse raw artifacts, access local paths/checksums/credentials/DB/queue URLs,
read ROS topics, touch serial/UART, trigger Nav2/fixed-route actions, prove a
real route/elevator field pass, prove PR #4 field backfill, prove HIL, prove a
real phone/browser run, prove O5/O1, or enable primary robot actions.

## field_evidence_rerun_material_dispatch

`pc-tools/evidence/field_evidence_rerun_material_dispatch.py` generates a
dependency-free PC material-dispatch gate after the route/elevator rerun review
handoff or real-material followup/status family. It packages what the field
owners must collect for a real rerun, not a real field pass or delivery result.

- Artifact schema:
  `trashbot.field_evidence_rerun_material_dispatch.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_material_dispatch_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_material_dispatch_gate`
- Allowed source inputs:
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1`,
  `trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1`,
  `trashbot.real_material_followup_escalation_status.v1`,
  `trashbot.real_material_followup_escalation_status_summary.v1`,
  `trashbot.real_material_evidence_intake.v1`,
  `trashbot.real_material_evidence_intake_summary.v1`,
  `trashbot.real_material_manifest_template.v1`, and
  `trashbot.real_material_manifest_template_summary.v1` under their matching
  software-proof boundaries only. Wrapper or nested JSON is allowed only through
  whitelisted `summary`, `artifact`, `safe_copy`, diagnostics, mobile,
  `payload`, or `data` keys.
- Dispatch status values:
  `ready_for_field_evidence_rerun_material_dispatch_not_proven`,
  `evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked`,
  `blocked_unsafe_field_evidence_rerun_material_dispatch_copy`, and
  `blocked_unsupported_field_evidence_rerun_material_dispatch_source`.

The output always includes `source=software_proof`, safe `evidence_ref`,
`same_evidence_ref_required=true`, source schema/boundary/status metadata,
required material groups, `owner_work_orders`, `rerun_commands`,
`callback_packet_requirements`, `safe_copy`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_material_dispatch_gate`.
Required material groups are `real route completion signal`, `real field task
record`, `real Nav2/fixed-route runtime log`, `real elevator door summary`,
`real target floor / floor arrival summary`, `real human-assistance summary`,
`real dropoff completion`, `real cancel completion`, `real delivery result`,
and `real phone/browser evidence`.

Mapping is fail-closed. A supported software-proof/not-proven source with a
matching safe evidence_ref maps to
`ready_for_field_evidence_rerun_material_dispatch_not_proven`. Mismatched
evidence_ref, missing evidence_ref, or weak `same_evidence_ref_required` maps
to `evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked`.
Unsafe copy, raw artifact text, local paths, checksum text, credentials,
DB/queue URLs, ROS topic names, `/cmd_vel`, serial/UART/WAVE ROVER text,
success/control claims, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` maps to
`blocked_unsafe_field_evidence_rerun_material_dispatch_copy`. Missing JSON, bad
JSON, unreadable JSON, non-object JSON, unsupported schema, unsupported
boundary, non-`software_proof` source, or missing `not_proven` maps to
`blocked_unsupported_field_evidence_rerun_material_dispatch_source`.

This contract is software proof only. It does not read material directories,
parse raw artifacts, access local paths/checksums/credentials/DB/queue URLs,
read ROS topics, touch serial/UART, trigger Nav2/fixed-route actions, prove a
real route/elevator field pass, prove dropoff/cancel completion, prove delivery
success, prove HIL, prove O5 external cloud/4G/OSS/CDN/DB/queue readiness,
resolve PR #5, prove a real phone/browser run, or enable primary robot actions.

## field_evidence_rerun_callback_intake

`pc-tools/evidence/field_evidence_rerun_callback_intake.py` generates a
dependency-free PC callback-intake gate after
`field_evidence_rerun_material_dispatch`. It consumes only the previous
dispatch artifact or summary plus a field-owner safe callback packet for the
same safe `evidence_ref`.

- Artifact schema:
  `trashbot.field_evidence_rerun_callback_intake.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_callback_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_callback_intake_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_material_dispatch.v1` and
  `trashbot.field_evidence_rerun_material_dispatch_summary.v1` under
  `software_proof_docker_field_evidence_rerun_material_dispatch_gate` only.
  Wrapper or nested JSON is allowed only through whitelisted `summary`,
  `artifact`, `safe_copy`, diagnostics, mobile, `payload`, or `data` keys.
- Callback input:
  an optional-schema `trashbot.field_evidence_rerun_callback_packet.v1` or
  `trashbot.field_evidence_rerun_callback_packet_summary.v1` style object with
  `source=software_proof`, `not_proven`, safe `evidence_ref`,
  `same_evidence_ref_required=true`, and material classifications.
- Callback intake status values:
  `ready_for_field_evidence_rerun_callback_intake_not_proven`,
  `blocked_field_evidence_rerun_callback_materials_not_ready`,
  `evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked`,
  `blocked_unsafe_field_evidence_rerun_callback_intake_copy`, and
  `blocked_unsupported_field_evidence_rerun_callback_intake_source`.

The output always includes `source=software_proof`, safe `evidence_ref`,
same-evidence-ref status, `accepted_materials`, `missing_materials`,
`rejected_materials`, `blocked_materials`, `material_counts`,
`next_required_evidence`, `safe_copy`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_callback_intake_gate`.
Required material classes are `real route completion signal`, `real field task
record`, `real Nav2/fixed-route runtime log`, `real elevator door summary`,
`real target floor / floor arrival summary`, `real human-assistance summary`,
`real dropoff completion`, `real cancel completion`, `real delivery result`,
and `real phone/browser evidence`. Each class must classify as `accepted`,
`missing`, `rejected`, or `blocked`; omitted classes default to `missing`.

Mapping is fail-closed. A supported dispatch and callback packet with matching
safe evidence_ref, safe copy, and all ten classes marked `accepted` maps to
`ready_for_field_evidence_rerun_callback_intake_not_proven`. Missing,
rejected, blocked, unknown, or invalid material classifications map to
`blocked_field_evidence_rerun_callback_materials_not_ready`. Mismatched
evidence_ref, missing evidence_ref, or weak `same_evidence_ref_required` maps
to `evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked`.
Unsafe copy, raw artifact text, local paths, checksum text, credentials,
DB/queue URLs, ROS topic names, `/cmd_vel`, serial/UART/WAVE ROVER text,
traceback text, success/control claims, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`blocked_unsafe_field_evidence_rerun_callback_intake_copy`. Missing JSON, bad
JSON, unreadable JSON, non-object JSON, unsupported dispatch schema/boundary,
unsupported callback schema/boundary, non-`software_proof` source, or missing
`not_proven` maps to
`blocked_unsupported_field_evidence_rerun_callback_intake_source`.

This contract is software proof only. It does not read material directories,
parse raw artifacts, access local paths/checksums/credentials/DB/queue URLs,
read ROS topics, touch serial/UART, trigger Nav2/fixed-route actions, prove a
real route/elevator field pass, prove dropoff/cancel completion, prove delivery
success, prove HIL, prove O5 external cloud/4G/OSS/CDN/DB/queue readiness,
resolve PR #5, prove a real phone/browser run, or enable primary robot actions.

## field_evidence_rerun_callback_review_decision

`pc-tools/evidence/field_evidence_rerun_callback_review_decision.py` generates
the PC-only review decision gate after `field_evidence_rerun_callback_intake`.
It consumes only the callback-intake summary or a wrapper/nested artifact that
contains that summary; it does not read field material directories or raw
materials.

- Artifact schema:
  `trashbot.field_evidence_rerun_callback_review_decision.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_callback_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_callback_review_decision_gate`
- Allowed inputs:
  `trashbot.field_evidence_rerun_callback_intake_summary.v1` under
  `software_proof_docker_field_evidence_rerun_callback_intake_gate`, or
  `trashbot.field_evidence_rerun_callback_intake.v1` only when wrapper/nested
  JSON exposes the same summary. Missing summary fails closed.
- Review decision values:
  `accepted`, `missing`, `rejected`, and `blocked`.

The output always includes `source=software_proof`, `review_decision`, safe
`evidence_ref`, `same_evidence_ref_status`, `owner_handoff`,
`next_required_evidence`, `rerun_guidance`, `blocker_summary`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`blocked_materials`, `safe_copy`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_callback_review_decision_gate`.
Required material classes are `real route completion signal`, `real field task
record`, `real Nav2/fixed-route runtime log`, `real elevator door summary`,
`real target floor / floor arrival summary`, `real human-assistance summary`,
`real dropoff completion`, `real cancel completion`, `real delivery result`,
and `real phone/browser evidence`.

Decision mapping is fail-closed. A supported, safe callback-intake summary with
matched safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, and
all ten required material classes in `accepted` maps to
`review_decision=accepted`. Any missing required class maps to `missing`;
rejected classes map to `rejected`; blocked classes, unsupported schema or
boundary, missing input, bad JSON, missing summary, evidence_ref mismatch,
unsafe copy, raw paths, credentials, ROS topic text, `/cmd_vel`,
serial/UART/WAVE ROVER text, checksum text, complete artifact text, traceback
text, success/control claims, `safe_to_control=true`,
`delivery_success=true`, or `primary_actions_enabled=true` map to
`review_decision=blocked`.

This contract is software proof only. It does not prove a real route/elevator
field pass, real Nav2/fixed-route execution, real field task record, real
elevator door or floor arrival evidence, real human assistance, real dropoff
completion, real cancel completion, real delivery result, real phone/browser
evidence, HIL pass, Objective 5 external proof, PR #5 resolution, or any
primary robot action being enabled.

## field_evidence_rerun_callback_review_handoff

`pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py` generates
the PC-only handoff gate after `field_evidence_rerun_callback_review_decision`.
It consumes only the review-decision artifact, summary, or wrapper/nested JSON;
it does not read field material directories, execute field reruns, or open raw
materials.

- Artifact schema:
  `trashbot.field_evidence_rerun_callback_review_handoff.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_callback_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`
- Allowed inputs:
  `trashbot.field_evidence_rerun_callback_review_decision.v1` and
  `trashbot.field_evidence_rerun_callback_review_decision_summary.v1` under
  `software_proof_docker_field_evidence_rerun_callback_review_decision_gate`.
  Wrapper, summary, artifact, robot diagnostics, mobile read-only, payload, and
  nested diagnostics JSON are allowed only through known safe wrapper keys.
- Handoff status values:
  `ready_for_field_evidence_rerun_callback_review_handoff`,
  `needs_owner_follow_up`,
  `needs_field_evidence_rerun_callback_rerun`,
  `evidence_ref_mismatch_rerun`, and `blocked_unsafe_review_handoff`.

The output always includes `source=software_proof`, `handoff_status`, source
`review_decision`, safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status`, `owner_handoff`, `handoff_package`,
`next_required_evidence`, `rerun_guidance`, `blocker_summary`, `safe_copy`,
`not_proven`, `safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`.
The summary mirrors the artifact and is the intended read-only consumer surface
for Robot diagnostics and mobile/web follow-through.

Handoff mapping is fail-closed. A supported, safe review-decision input with
`review_decision=accepted`, matched safe `evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_status=matched`,
`source=software_proof`, `not_proven`, and all action flags false maps to
`ready_for_field_evidence_rerun_callback_review_handoff`.
`review_decision=missing` or `review_decision=rejected` maps to
`needs_owner_follow_up`; `review_decision=blocked` maps to
`needs_field_evidence_rerun_callback_rerun`. Missing input, bad JSON,
unsupported schema or boundary, missing safe evidence_ref, mismatched evidence
refs, weak same-ref typing, unsupported review decision, unsafe copy, raw paths,
credentials, ROS topic text, `/cmd_vel`, serial/UART/WAVE ROVER text, checksum
text, complete artifact text, traceback text, success/control claims,
`safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed to a rerun, mismatch, or unsafe
handoff status.

This contract is software proof only. It does not prove a real route/elevator
field pass, real Nav2/fixed-route execution, real field task record, real
elevator door or floor arrival evidence, real human assistance, real dropoff
completion, real cancel completion, real delivery result, real phone/browser
evidence, HIL pass, Objective 5 external cloud/4G/OSS/CDN/DB/queue proof, PR #5
resolution, or any primary robot action being enabled.

## field_evidence_rerun_handoff_intake

`pc-tools/evidence/field_evidence_rerun_handoff_intake.py` generates the
PC-only owner handoff-intake gate after
`field_evidence_rerun_callback_review_handoff`. It consumes only the
callback-review-handoff artifact/summary/wrapper JSON and an owner-safe
handoff intake packet; it does not read field material directories, execute
field reruns, or open raw materials.

- Artifact schema:
  `trashbot.field_evidence_rerun_handoff_intake.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_handoff_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_handoff_intake_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_callback_review_handoff.v1` and
  `trashbot.field_evidence_rerun_callback_review_handoff_summary.v1` under
  `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`.
  Wrapper, summary, artifact, robot diagnostics, mobile read-only, payload, and
  nested diagnostics JSON are allowed only through known safe wrapper keys.
- Allowed packet inputs:
  a safe owner packet with optional
  `trashbot.field_evidence_rerun_handoff_intake_packet.v1` or `_summary.v1`
  schema. The packet must include `owner`, `handoff_received=true`,
  `intake_notes`, `next_required_evidence`, `source=software_proof`,
  `not_proven`, `safe_to_control=false`, `delivery_success=false`,
  `primary_actions_enabled=false`, `same_evidence_ref_required=true`, and the
  same safe `evidence_ref`.
- Intake status values:
  `ready_for_field_evidence_rerun_handoff_intake_not_proven`,
  `blocked_missing_field_evidence_rerun_handoff_intake_packet`,
  `blocked_unsupported_field_evidence_rerun_handoff_intake_source`,
  `blocked_field_evidence_rerun_review_handoff_not_ready`,
  `evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked`, and
  `blocked_unsafe_field_evidence_rerun_handoff_intake_copy`.

The output always includes `source=software_proof`, `intake_status`, source
`handoff_status`, safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status`, `owner_intake`, `next_required_evidence`,
`rerun_guidance`, `blocker_summary`, `safe_copy`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_handoff_intake_gate`.
The summary mirrors the artifact and is the intended read-only consumer surface
for Robot diagnostics and mobile/web follow-through.

Intake mapping is fail-closed. A supported, safe source handoff with
`handoff_status=ready_for_field_evidence_rerun_callback_review_handoff`,
matched safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, all
action flags false, and a supported owner-safe packet maps to
`ready_for_field_evidence_rerun_handoff_intake_not_proven`. Missing source
input, bad JSON, unsupported source schema or boundary, or missing
software-proof/not-proven fields fails closed to
`blocked_unsupported_field_evidence_rerun_handoff_intake_source`. Missing
packet input, unsupported packet schema/boundary, `handoff_received` not true,
or missing required owner packet fields fails closed to
`blocked_missing_field_evidence_rerun_handoff_intake_packet`. A non-ready
source handoff maps to `blocked_field_evidence_rerun_review_handoff_not_ready`.
Mismatched evidence refs, missing safe evidence_ref, weak same-ref typing, or
non-matched same-ref status maps to
`evidence_ref_mismatch_field_evidence_rerun_handoff_intake_blocked`. Unsafe
copy, raw paths, credentials, ROS topic text, `/cmd_vel`, serial/UART/WAVE
ROVER text, checksum text, complete artifact text, traceback text,
success/control claims, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed to
`blocked_unsafe_field_evidence_rerun_handoff_intake_copy`.

This contract is software proof only. It does not prove a real route/elevator
field pass, real Nav2/fixed-route execution, real field task record, real
elevator door or floor arrival evidence, real human assistance, real dropoff
completion, real cancel completion, real delivery result, real phone/browser
evidence, HIL pass, Objective 5 external cloud/4G/OSS/CDN/DB/queue proof, PR #5
resolution, or any primary robot action being enabled.

## field_evidence_rerun_queue

`pc-tools/evidence/field_evidence_rerun_queue.py` generates the PC-only
controlled rerun queue gate after `field_evidence_rerun_handoff_intake.py`.
It consumes only a supported handoff-intake artifact/summary/wrapper JSON and
an optional owner-safe queue request JSON; it does not read field material
directories, execute field reruns, or open raw materials.

- Artifact schema:
  `trashbot.field_evidence_rerun_queue.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_queue_summary.v1`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_queue_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_handoff_intake.v1` and
  `trashbot.field_evidence_rerun_handoff_intake_summary.v1` under
  `software_proof_docker_field_evidence_rerun_handoff_intake_gate`.
  Wrapper, summary, artifact, robot diagnostics, mobile read-only, payload, and
  nested diagnostics JSON are allowed only through known safe wrapper keys.
- Owner-safe queue request:
  optional CLI input, but required for `queued_for_controlled_field_rerun_not_proven`.
  Missing request still emits a blocked/not-proven summary. A supported request
  must carry the same safe `evidence_ref`, `source=software_proof`,
  `not_proven`, `same_evidence_ref_required=true`, acknowledged owner queue
  state, `safe_to_control=false`, `delivery_success=false`, and
  `primary_actions_enabled=false`.
- Queue status values:
  `queued_for_controlled_field_rerun_not_proven`,
  `needs_owner_safe_queue_request_before_rerun_queue`,
  `needs_field_evidence_rerun_queue_backfill`,
  `evidence_ref_mismatch_field_evidence_rerun_queue`,
  `blocked_unsafe_field_evidence_rerun_queue`, and
  `blocked_unsupported_field_evidence_rerun_handoff_intake`.

The output always includes `source=software_proof`, `queue_status`, source
handoff intake status, safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status`, owner-safe queue request, `blocker_summary`,
`next_required_evidence`, `owner_handoff`, `safe_rerun_hint` /
`rerun_guidance`, `safe_copy`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_queue_gate`.
The summary mirrors the artifact and is the intended read-only consumer surface
for Robot diagnostics and mobile/web follow-through.

Queue mapping is fail-closed. A supported, safe source handoff intake with
`intake_status=ready_for_field_evidence_rerun_handoff_intake_not_proven`,
matched safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, all
action flags false, and a supported owner-safe acknowledged request maps to
`queued_for_controlled_field_rerun_not_proven`. Missing source input, bad JSON,
unsupported source schema or boundary, or missing software-proof/not-proven
fields fails closed to `blocked_unsupported_field_evidence_rerun_handoff_intake`.
Missing owner-safe queue request, unsupported request, or missing owner queue
acknowledgement fails closed to
`needs_owner_safe_queue_request_before_rerun_queue`. A non-ready source intake
maps to `needs_field_evidence_rerun_queue_backfill`. Mismatched evidence refs,
missing safe evidence_ref, weak same-ref typing, or non-matched same-ref status
maps to `evidence_ref_mismatch_field_evidence_rerun_queue`. Unsafe copy, raw
paths, credentials, ROS topic text, `/cmd_vel`, serial/UART/WAVE ROVER text,
checksum text, complete/raw artifact text, traceback text, success/control
wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed to
`blocked_unsafe_field_evidence_rerun_queue`.

This contract is software proof only. It does not prove a real route/elevator
field pass, real controlled field rerun, real Nav2/fixed-route execution, real
field task record, real route completion signal, real dropoff or cancel
completion, real delivery result, real phone/browser evidence, HIL pass,
Objective 5 external cloud/4G/OSS/CDN/DB/queue proof, PR #5 resolution, or any
primary robot action being enabled.

## field_evidence_rerun_execution_pack

`pc-tools/evidence/field_evidence_rerun_execution_pack.py` generates the
PC-only field owner execution-pack gate after `field_evidence_rerun_queue.py`.
It consumes only a supported queue artifact/summary/wrapper JSON; it does not
read field material directories, execute field reruns, schedule robot actions,
or open raw materials.

- Artifact schema:
  `trashbot.field_evidence_rerun_execution_pack.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_execution_pack_summary.v1`
- Robot safe alias:
  `robot_diagnostics_field_evidence_rerun_execution_pack_summary`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_execution_pack_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_queue.v1` and
  `trashbot.field_evidence_rerun_queue_summary.v1` under
  `software_proof_docker_field_evidence_rerun_queue_gate`.
  Wrapper, summary, artifact, robot diagnostics, mobile read-only, payload, and
  nested diagnostics JSON are allowed only through known safe wrapper keys.
- Execution-pack status values:
  `ready_for_field_evidence_rerun_execution_pack_not_proven`,
  `needs_field_evidence_rerun_execution_pack_backfill`,
  `evidence_ref_mismatch_field_evidence_rerun_execution_pack`,
  `blocked_unsafe_field_evidence_rerun_execution_pack`, and
  `blocked_unsupported_field_evidence_rerun_queue`.

The output always includes `source=software_proof`, `execution_pack_status`,
`source_queue_schema`, `source_queue_status`, safe `evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_status`,
`execution_steps`, `material_templates`, `owner_handoff`, `fail_thresholds`,
`pass_thresholds`, `backfill_instructions`, `safe_copy`, `not_proven`,
`safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_execution_pack_gate`.
The summary mirrors the artifact and is the intended read-only consumer surface
for Robot diagnostics and mobile/web follow-through.

Execution-pack mapping is fail-closed. A supported, safe queue source with
`queue_status=queued_for_controlled_field_rerun_not_proven`, matched safe
`evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, and
all action flags false maps to
`ready_for_field_evidence_rerun_execution_pack_not_proven`. Missing source
input, bad JSON, unsupported source schema or boundary, or missing
software-proof/not-proven fields fails closed to
`blocked_unsupported_field_evidence_rerun_queue`. A non-queued source maps to
`needs_field_evidence_rerun_execution_pack_backfill`. Mismatched evidence refs,
missing safe evidence_ref, weak same-ref typing, or non-matched same-ref status
maps to `evidence_ref_mismatch_field_evidence_rerun_execution_pack`. Unsafe
copy, raw paths, credentials, ROS topic text, `/cmd_vel`, serial/UART/WAVE
ROVER text, checksum text, complete/raw artifact text, traceback text,
success/control wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed to
`blocked_unsafe_field_evidence_rerun_execution_pack`.

This contract is software proof only. It does not prove a real route/elevator
field pass, real controlled field rerun, real Nav2/fixed-route execution, real
field task record, real route completion signal, real elevator door/floor
material, real human assistance, real dropoff or cancel completion, real
delivery result, real phone/browser evidence, HIL pass, Objective 5 external
cloud/4G/OSS/CDN/DB/queue proof, PR #5 resolution, or any primary robot action
being enabled.

## field_evidence_rerun_execution_callback_intake

`pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py`
generates the PC-only execution callback intake gate after
`field_evidence_rerun_execution_pack.py`. It consumes only a supported
execution-pack artifact/summary/wrapper JSON and a field owner execution
callback packet; it does not read field material directories, execute field
reruns, schedule robot actions, or expose raw callback material.

- Artifact schema:
  `trashbot.field_evidence_rerun_execution_callback_intake.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_execution_callback_intake_summary.v1`
- Robot safe alias:
  `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_execution_pack.v1` and
  `trashbot.field_evidence_rerun_execution_pack_summary.v1` under
  `software_proof_docker_field_evidence_rerun_execution_pack_gate`.
- Allowed callback inputs:
  an optional-schema
  `trashbot.field_evidence_rerun_execution_callback_packet.v1` or
  `_summary.v1` object with `source=software_proof`, `not_proven`,
  same safe `evidence_ref`, and all action flags false.
- Callback intake status values:
  `ready_for_field_evidence_rerun_execution_callback_intake_not_proven`,
  `blocked_field_evidence_rerun_execution_callback_materials_not_ready`,
  `blocked_field_evidence_rerun_execution_pack_not_ready`,
  `evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked`,
  `blocked_unsafe_field_evidence_rerun_execution_callback_intake_copy`, and
  `blocked_unsupported_field_evidence_rerun_execution_callback_intake_source`.

The output always includes `source=software_proof`, `callback_intake_status`,
`source_execution_pack_schema`, `source_execution_pack_status`,
`callback_packet_schema`, `callback_packet_status`, safe `evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_status`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`blocked_materials`, `owner_handoff`, `next_required_evidence`, `safe_copy`,
`not_proven`, `safe_to_control=false`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`.
The required material categories are `task_record`,
`nav2_fixed_route_runtime_log`, `route_completion_signal`,
`elevator_door_state`, `target_floor_confirmation`,
`human_assistance_record`, `dropoff_completion`, `cancel_completion`,
`delivery_result`, and `phone_browser_evidence`.
The gate accepts the prior execution-pack template groups as coverage for
these categories, including combined elevator context and terminal completion
templates, but the callback packet itself must still classify the ten
categories explicitly.

Execution callback mapping is fail-closed. A supported, safe execution pack
with `execution_pack_status=ready_for_field_evidence_rerun_execution_pack_not_proven`,
matched safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, and
all action flags false can map to
`ready_for_field_evidence_rerun_execution_callback_intake_not_proven` only
when the callback packet marks all required categories as `accepted`. Missing,
rejected, blocked, unknown, or invalid material classifications map to
`blocked_field_evidence_rerun_execution_callback_materials_not_ready`.
Non-ready execution packs map to
`blocked_field_evidence_rerun_execution_pack_not_ready`. Mismatched evidence
refs, missing safe evidence_ref, weak same-ref typing, or non-matched same-ref
status maps to
`evidence_ref_mismatch_field_evidence_rerun_execution_callback_intake_blocked`.
Missing source or callback JSON, bad JSON, unsupported schema or boundary, or
missing software-proof/not-proven fields fails closed to
`blocked_unsupported_field_evidence_rerun_execution_callback_intake_source`.
Unsafe copy, raw paths, credentials, ROS topic text, `/cmd_vel`, serial/UART or
WAVE ROVER text, checksum text, complete/raw artifact text, traceback text,
success/control wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` fail closed to
`blocked_unsafe_field_evidence_rerun_execution_callback_intake_copy`.

This contract is software proof only. It does not prove a real field rerun,
real route/elevator field pass, real Nav2/fixed-route execution, real field
task record, real route completion signal, real elevator door/floor material,
real human assistance, real dropoff or cancel completion, real delivery
result, real phone/browser evidence, HIL pass, Objective 5 external
cloud/4G/OSS/CDN/DB/queue proof, PR #5 resolution, or any primary robot action
being enabled.

## field_evidence_rerun_execution_callback_review_decision

`pc-tools/evidence/field_evidence_rerun_execution_callback_review_decision.py`
generates the PC-only canonical review-decision gate after
`field_evidence_rerun_execution_callback_intake.py`. It consumes only a
supported callback-intake artifact/summary/wrapper JSON or Robot safe alias; it
does not read field material directories, execute field reruns, schedule robot
actions, or expose raw callback material.

- Artifact schema:
  `trashbot.field_evidence_rerun_execution_callback_review_decision.v1`
- Summary schema:
  `trashbot.field_evidence_rerun_execution_callback_review_decision_summary.v1`
- Robot safe alias:
  `robot_diagnostics_field_evidence_rerun_execution_callback_review_decision_summary`
- Evidence boundary:
  `software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate`
- Allowed source inputs:
  `trashbot.field_evidence_rerun_execution_callback_intake.v1` and
  `trashbot.field_evidence_rerun_execution_callback_intake_summary.v1` under
  `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`.
- Review decision values:
  `ready`, `missing`, `rejected`, `blocked`, `unsupported`, `unsafe`,
  `evidence_ref_mismatch`, and `source_not_ready`.

The output always includes `source=software_proof`, `review_decision`,
`decision_reasons`, `source_callback_intake_status`, safe `evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_status`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`blocked_materials`, `owner_handoff`, `next_required_evidence`,
`rerun_guidance`, `safe_copy`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_field_evidence_rerun_execution_callback_review_decision_gate`.
The required material categories remain `task_record`,
`nav2_fixed_route_runtime_log`, `route_completion_signal`,
`elevator_door_state`, `target_floor_confirmation`,
`human_assistance_record`, `dropoff_completion`, `cancel_completion`,
`delivery_result`, and `phone_browser_evidence`.

Review-decision mapping is fail-closed. A supported, safe callback-intake
source with
`callback_intake_status=ready_for_field_evidence_rerun_execution_callback_intake_not_proven`,
matched safe `evidence_ref`, `same_evidence_ref_required=true`,
`same_evidence_ref_status=matched`, `source=software_proof`, `not_proven`, and
all action flags false can map to `ready` only when every required category is
accepted. Missing categories map to `missing`; rejected categories map to
`rejected`; blocked categories map to `blocked`. Non-ready callback-intake
sources map to `source_not_ready`. Mismatched evidence refs, missing safe
evidence_ref, weak same-ref typing, or non-matched same-ref status map to
`evidence_ref_mismatch`. Missing input, bad JSON, unsupported schema or
boundary, missing software-proof/not-proven fields, unknown categories, or
category groups that conflict map to `unsupported`. Unsafe copy, raw paths,
credentials, ROS topic text, `/cmd_vel`, serial/UART or WAVE ROVER text,
checksum text, complete/raw artifact text, traceback text, success/control
wording, `safe_to_control=true`, `delivery_success=true`, or
`primary_actions_enabled=true` map to `unsafe`.

This contract is software proof only. It does not prove a real field rerun,
real route/elevator field pass, real Nav2/fixed-route execution, real field
task record, real route completion signal, real elevator door/floor material,
real human assistance, real dropoff or cancel completion, real delivery
result, real phone/browser evidence, HIL pass, Objective 5 external
cloud/4G/OSS/CDN/DB/queue proof, PR #5 resolution, or any primary robot action
being enabled.

## route_task_field_retest_result_backfill_review_decision

`pc-tools/evidence/route_task_field_retest_result_backfill_review_decision.py`
generates the PC-only review decision gate after
`route_task_field_retest_result_acceptance_backfill.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_backfill_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_backfill_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_acceptance_backfill.v1` and
  `trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Disallowed inputs:
  raw upstream artifacts, material directories, ROS2/Nav2 runtime state,
  hardware transport logs, external cloud evidence, real phone/browser evidence,
  or arbitrary JSON without the supported schema and boundary.

The output always includes `review_decision`, `material_status`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`owner_handoff`, `next_required_evidence`, `rerun_commands`, `safe_copy`,
`not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary`.

The gate fails closed on missing or bad JSON, unsupported schema or boundary,
acceptance backfill not ready, evidence_ref mismatch, weak
`same_evidence_ref_required`, unsafe copy, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.

## route_task_field_retest_result_callback_review_decision

`pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py`
generates the PC-only review-decision gate after
`route_task_field_retest_result_callback_intake.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_callback_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_callback_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_callback_intake.v1` and
  `trashbot.route_task_field_retest_result_callback_intake_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Decision values:
  `ready_for_result_review`, `needs_material_backfill`,
  `needs_callback_rerun`, `evidence_ref_mismatch_rerun`, and
  `rejected_unsafe_callback`.

The output always includes `safe_evidence_ref`, `source_callback_intake`,
`accepted_updates`, `missing_updates`, `rejected_updates`,
`result_review_readiness`, `next_required_evidence`, `owner_handoff`,
`rerun_commands`, `safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, `same_evidence_ref_required=true`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`.

Decision mapping is fail-closed. A source with accepted updates, no missing or
rejected updates, ready source status, and matched evidence_ref maps to
`ready_for_result_review`. Missing updates map to `needs_material_backfill`.
Rejected updates, unsupported source schema or boundary, bad JSON, missing JSON,
not-ready source status, or an empty accepted update set map to
`needs_callback_rerun`. Mismatched or missing same-evidence-ref state maps to
`evidence_ref_mismatch_rerun`. Unsafe copy, raw paths, checksum text,
credentials, ROS topics, serial/UART/WAVE ROVER text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` map to
`rejected_unsafe_callback`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.

## route_task_field_retest_result_callback_review_handoff

`pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py`
generates the PC-only handoff gate after
`route_task_field_retest_result_callback_review_decision.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_callback_review_handoff.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_callback_review_decision.v1` and
  `trashbot.route_task_field_retest_result_callback_review_decision_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Handoff status values:
  `ready_for_result_review_handoff`, `needs_owner_follow_up`,
  `needs_callback_rerun`, `evidence_ref_mismatch_rerun`, and
  `blocked_unsafe_review_handoff`.

The output always includes `safe_evidence_ref`,
`same_evidence_ref_required=true`, `owner_follow_up`,
`review_ready_package`, `rerun_package`, `next_required_evidence`,
`safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`.

Handoff mapping is fail-closed. `ready_for_result_review` maps to
`ready_for_result_review_handoff`. `needs_material_backfill` maps to
`needs_owner_follow_up`. `needs_callback_rerun` maps to
`needs_callback_rerun`. Evidence-ref mismatch or weak
`same_evidence_ref_required` maps to `evidence_ref_mismatch_rerun`.
Missing JSON, bad JSON, unsupported schema or boundary, missing decision, or an
unknown decision maps to `needs_callback_rerun`. Rejected or unsafe source
decision, unsafe copy, raw paths, checksum text, credentials, ROS topics,
serial/UART/WAVE ROVER text, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true` maps to
`blocked_unsafe_review_handoff`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.

## route_task_field_retest_result_review_intake

`pc-tools/evidence/route_task_field_retest_result_review_intake.py`
generates the PC-only result review intake gate after
`route_task_field_retest_result_callback_review_handoff.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_review_intake.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_review_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_review_intake_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_callback_review_handoff.v1` and
  `trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Intake status values:
  `ready_for_result_review_intake`, `needs_owner_follow_up`,
  `needs_handoff_rerun`, `evidence_ref_mismatch_rerun`, and
  `blocked_unsafe_review_intake`.

The output always includes `safe_evidence_ref`,
`same_evidence_ref_required=true`, `owner_follow_up`,
`result_review_intake_package`, `rerun_package`, `next_required_evidence`,
`safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_intake_gate`.

Intake mapping is fail-closed. `ready_for_result_review_handoff` maps to
`ready_for_result_review_intake`. `needs_owner_follow_up` stays
`needs_owner_follow_up`. `needs_callback_rerun` maps to
`needs_handoff_rerun`. Evidence-ref mismatch or weak
`same_evidence_ref_required` maps to `evidence_ref_mismatch_rerun`.
Missing JSON, bad JSON, unsupported schema or boundary, missing handoff status,
or an unknown handoff status maps to `needs_handoff_rerun`. Unsafe source
handoff, unsafe copy, raw paths, checksum text, credentials, ROS topics,
serial/UART/WAVE ROVER text, raw artifact text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`blocked_unsafe_review_intake`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.

## route_task_field_retest_result_review_decision

`pc-tools/evidence/route_task_field_retest_result_review_decision.py`
generates the PC-only result review decision gate after
`route_task_field_retest_result_review_intake.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_review_intake.v1` and
  `trashbot.route_task_field_retest_result_review_intake_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Decision status values:
  `ready_for_result_acceptance_backfill_not_proven`,
  `needs_route_elevator_material_backfill_not_proven`,
  `evidence_ref_mismatch_rerun_not_proven`,
  `blocked_missing_result_review_intake_not_proven`, and
  `unsupported_result_review_intake_schema_not_proven`.

The output always includes `safe_evidence_ref`,
`same_evidence_ref_required=true`, `source_result_review_intake`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`result_review_decision_package`, `owner_handoff`, `rerun_commands`,
`next_required_evidence`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_decision_gate`.

Decision mapping is fail-closed. A supported ready intake with matched
evidence_ref, `result_review_intake_package.ready=true`, and all required
route/elevator result material classes present maps to
`ready_for_result_acceptance_backfill_not_proven`. Missing result materials,
not-ready intake, rejected materials, or missing review-ready package maps to
`needs_route_elevator_material_backfill_not_proven`. Mismatched evidence_ref,
missing evidence_ref, weak `same_evidence_ref_required`, or non-matched
same-ref status maps to `evidence_ref_mismatch_rerun_not_proven`. Missing JSON,
bad JSON, unreadable JSON, or non-object JSON maps to
`blocked_missing_result_review_intake_not_proven`. Unsupported schema or
boundary, unsafe copy, raw paths, checksum text, credentials, ROS topics,
serial/UART/WAVE ROVER text, raw artifact text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`unsupported_result_review_intake_schema_not_proven`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real task record, real
dropoff/cancel completion, real delivery success, real phone/browser
validation, O5 external cloud proof, or any primary robot action being enabled.

## route_task_field_retest_result_review_handoff

`pc-tools/evidence/route_task_field_retest_result_review_handoff.py`
generates the PC-only owner handoff gate after
`route_task_field_retest_result_review_decision.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_review_handoff.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_review_handoff_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_review_handoff_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_review_decision.v1` and
  `trashbot.route_task_field_retest_result_review_decision_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Handoff status values:
  `ready_for_owner_result_callback_not_proven`,
  `needs_result_material_callback_not_proven`,
  `evidence_ref_mismatch_rerun_not_proven`,
  `blocked_missing_result_review_decision_not_proven`, and
  `unsupported_result_review_decision_schema_not_proven`.

The output always includes `safe_evidence_ref`,
`same_evidence_ref_required=true`, `same_evidence_ref_package`,
`owner_work_orders`, `accepted_reasons`, `blocked_reasons`, `rerun_reasons`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`next_material_callback_requirements`, `rerun_commands`,
`next_required_evidence`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_handoff_gate`.

Handoff mapping is fail-closed. A supported
`ready_for_result_acceptance_backfill_not_proven` decision with matched
evidence_ref, `result_review_decision_package.ready=true`, and all required
route/elevator result material classes present maps to
`ready_for_owner_result_callback_not_proven`. Missing result materials,
rejected materials, or a not-ready decision package maps to
`needs_result_material_callback_not_proven`. Mismatched evidence_ref, missing
evidence_ref, weak `same_evidence_ref_required`, or non-matched same-ref status
maps to `evidence_ref_mismatch_rerun_not_proven`. Missing JSON, bad JSON,
unreadable JSON, or non-object JSON maps to
`blocked_missing_result_review_decision_not_proven`. Unsupported schema or
boundary, unsafe copy, raw paths, checksum text, credentials, ROS topics,
serial/UART/WAVE ROVER text, raw artifact text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`unsupported_result_review_decision_schema_not_proven`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real task record, real
dropoff/cancel completion, real delivery success, real phone/browser
validation, O5 external cloud proof, or any primary robot action being enabled.

## route_task_field_retest_material_pack

`pc-tools/evidence/route_task_field_retest_material_pack.py`
generates the PC-only field retest material pack gate. It preserves the
historical `--material-dir` mode used by operator drill and result acceptance
backfill, and adds an explicit `--result-review-handoff-json` /
`--review-handoff-summary` compatibility mode after
`route_task_field_retest_result_review_handoff.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_material_pack.v1`
- Summary schema:
  `trashbot.route_task_field_retest_material_pack_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_material_pack_gate`
- Allowed material-dir input:
  `--material-dir` scans the eight legacy material classes through
  `MATERIAL_ALIASES`: `nav2_or_fixed_route_runtime_log`,
  `route_completion_signal`, `task_record`, `door_state`,
  `target_floor_confirmation`, `human_assistance_note`,
  `dropoff_or_cancel_completion`, and `delivery_result`.
- Allowed handoff inputs:
  `trashbot.route_task_field_retest_result_review_handoff.v1` and
  `trashbot.route_task_field_retest_result_review_handoff_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Material-dir verdict values include:
  `ready_for_field_retest_material_pack_not_proven`,
  `blocked_missing_material_dir`, `blocked_unsafe_material_copy`,
  `blocked_success_or_control_claim`, `blocked_same_evidence_ref_mismatch`,
  `blocked_missing_materials`, `blocked_placeholder_only_materials`, and
  `blocked_rejected_materials`.
- Handoff material pack status values:
  `ready_for_field_retest_material_collection_not_proven`,
  `needs_result_review_handoff_not_proven`,
  `evidence_ref_mismatch_rerun_not_proven`,
  `blocked_missing_result_review_handoff_not_proven`, and
  `unsupported_result_review_handoff_schema_not_proven`.

Material-dir output keeps the historical downstream fields:
`material_manifest`, `material_pack_summary`, `material_completeness`,
`missing_materials`, `rejected_materials`, `operator_next_steps`,
`safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_pack_gate`.
It also mirrors the verdict into `material_pack_status` for read-only
downstream compatibility. Handoff-mode output additionally includes
`source_schema`, `source_boundary`, `safe_evidence_ref`,
`same_evidence_ref_required=true`, `field_capture_checklist`,
`callback_payload_skeleton`, `owner_work_orders`, and `rerun_commands`.

Material-pack mapping is fail-closed. A supported
`ready_for_owner_result_callback_not_proven` handoff with matched evidence_ref
maps to `ready_for_field_retest_material_collection_not_proven`. A supported
but not-ready handoff such as `needs_result_material_callback_not_proven` maps
to `needs_result_review_handoff_not_proven`. Mismatched evidence_ref, missing
evidence_ref, weak `same_evidence_ref_required`, or non-matched same-ref status
maps to `evidence_ref_mismatch_rerun_not_proven`. Missing JSON, bad JSON,
unreadable JSON, or non-object JSON maps to
`blocked_missing_result_review_handoff_not_proven`. Unsupported schema or
boundary, unsafe copy, raw paths, checksum text, credentials, ROS topics,
serial/UART/WAVE ROVER text, raw artifact text, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true` maps to
`unsupported_result_review_handoff_schema_not_proven`.

This contract is software proof only. Material-dir mode reads only whitelisted
local JSON/text material files, and handoff mode reads only the handoff JSON
artifact/summary. Neither mode proves a real route/elevator field pass, HIL
pass, real Nav2/fixed-route execution, real task record, real dropoff/cancel
completion, real delivery success, real phone/browser validation, O5 external
cloud proof, or any primary robot action being enabled.

## route_task_field_retest_material_callback_packet

`pc-tools/evidence/route_task_field_retest_material_callback_packet.py`
generates the PC-only field material callback packet gate after
`route_task_field_retest_material_pack.py`. It converts the material pack
callback skeleton into a fillable, returnable, and reviewable metadata packet.

- Artifact schema:
  `trashbot.route_task_field_retest_material_callback_packet.v1`
- Summary schema:
  `trashbot.route_task_field_retest_material_callback_packet_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_material_callback_packet_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_material_pack.v1` and
  `trashbot.route_task_field_retest_material_pack_summary.v1` only. Wrapper,
  summary, artifact, robot diagnostics, mobile read-only, payload, and nested
  diagnostics JSON are allowed only through known safe wrapper keys.
- Disallowed inputs:
  unsupported schemas, wrong boundaries, weak or path-like evidence refs,
  mismatched evidence refs, weak `same_evidence_ref_required`, raw local paths,
  credentials, OSS/DB/queue/token material, ROS topics, serial/UART/WAVE ROVER
  text, success/control claims, `delivery_success=true`, or
  `primary_actions_enabled=true`.

The artifact always includes `callback_packet_status`, `safe_evidence_ref`,
`field_callback_items`, `accepted_materials`, `missing_materials`,
`rejected_materials`, `owner_acknowledgement`, `next_required_evidence`,
`rerun_commands`, `safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`.
The summary mirrors the same status and evidence ref, sets
`source_schema=trashbot.route_task_field_retest_material_callback_packet.v1`,
and exposes `material_callback_summary` plus `owner_next_steps` for read-only
Robot diagnostics and mobile/web consumers.

Callback packet status values include
`ready_for_field_material_callback_not_proven`,
`needs_material_pack_not_proven`,
`evidence_ref_mismatch_rerun_not_proven`,
`blocked_missing_callback_materials_not_proven`,
`unsupported_material_pack_schema_not_proven`, and
`unsafe_success_claim_rejected_not_proven`. A supported material pack with
matched safe evidence_ref, fixed
`evidence_boundary=software_proof_docker_route_task_field_retest_material_pack_gate`,
strict `same_evidence_ref_required=true`, and disabled action flags maps to
`ready_for_field_material_callback_not_proven`. Missing or not-ready material
pack input maps to `needs_material_pack_not_proven`. Mismatched or weak
evidence refs map to `evidence_ref_mismatch_rerun_not_proven`. Unsafe copy,
wrong schema, or wrong boundary maps fail-closed and must be regenerated before
Robot or mobile display.

This contract is software proof only. It does not prove a real route/elevator
field pass, Nav2 or fixed-route execution, task record or completion signal,
dropoff/cancel completion, delivery success, HIL, WAVE ROVER/UART feedback,
real phone/browser validation, Objective 5 external cloud/4G/OSS/CDN/DB/queue
proof, or any primary robot action being enabled.

## route_task_field_retest_material_callback_review_decision

`pc-tools/evidence/route_task_field_retest_material_callback_review_decision.py`
generates the PC-only review-decision gate after
`route_task_field_retest_material_callback_packet.py`. It converts a sanitized
material callback packet into a review decision artifact and summary that can be
read by Robot diagnostics and mobile/web without opening raw field material.

- Artifact schema:
  `trashbot.route_task_field_retest_material_callback_review_decision.v1`
- Summary schema:
  `trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_material_callback_packet.v1` and
  `trashbot.route_task_field_retest_material_callback_packet_summary.v1` only.
  Wrapper, summary, artifact, robot diagnostics, mobile read-only, payload, and
  nested diagnostics JSON are allowed only through known safe wrapper keys.
- Disallowed inputs:
  unsupported schemas, wrong boundaries, weak or path-like evidence refs,
  mismatched evidence refs, weak `same_evidence_ref_required`, raw local paths,
  credentials, OSS/DB/queue/token material, ROS topics, serial/UART/WAVE ROVER
  text, success/control claims, `delivery_success=true`, or
  `primary_actions_enabled=true`.

The artifact always includes `review_decision`, `safe_evidence_ref`,
`same_evidence_ref_required=true`, `accepted_materials`, `missing_materials`,
`rejected_materials`, `owner_acknowledgement`, `next_required_evidence`,
`rerun_commands`, `safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`.
It also records `source_schema=trashbot.route_task_field_retest_material_callback_packet.v1`
or `trashbot.route_task_field_retest_material_callback_packet_summary.v1` and
`source_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`.
The summary mirrors the same decision and evidence ref, sets
`source_schema=trashbot.route_task_field_retest_material_callback_review_decision.v1`,
and exposes `material_callback_review_summary`, `owner_next_steps`, and
`safe_copy` for read-only consumers.

Review decision values include
`ready_for_controlled_field_rerun_not_proven`,
`needs_material_callback_backfill_not_proven`,
`evidence_ref_mismatch_rerun_not_proven`,
`blocked_material_callback_review_not_proven`,
`unsupported_material_callback_packet_schema_not_proven`, and
`unsafe_success_claim_rejected_not_proven`. A supported packet with matched safe
evidence_ref, fixed
`evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_packet_gate`,
strict `same_evidence_ref_required=true`, source status
`ready_for_field_material_callback_not_proven`, no missing or rejected material
callbacks, and completed owner acknowledgement maps to
`ready_for_controlled_field_rerun_not_proven`. Missing/rejected material
callbacks or pending acknowledgement map to
`needs_material_callback_backfill_not_proven`. Mismatched or weak evidence refs
map to `evidence_ref_mismatch_rerun_not_proven`. Missing JSON, bad JSON,
unsafe copy, unsupported schema, or wrong boundary maps fail-closed and must be
regenerated before Robot or mobile display.

This contract is software proof only. It is not a real route/elevator field
pass, not Nav2/fixed-route proof, not a task record or completion signal, not
dropoff/cancel completion, not delivery success, not HIL, not WAVE ROVER/UART
feedback, not real phone/browser validation, not Objective 5 external
cloud/4G/OSS/CDN/DB/queue proof, and not any primary robot action being
enabled.

## route_task_field_retest_operator_drill

`pc-tools/evidence/route_task_field_retest_operator_drill.py`
generates the PC-only operator drill after the material callback review
decision or the legacy material pack. It keeps the historical material-pack
input path for compatibility, but when a wrapper, summary, artifact, robot
diagnostics, mobile read-only payload, or nested diagnostics object contains
both families, it prioritizes
`route_task_field_retest_material_callback_review_decision` over material pack.

- Artifact schema:
  `trashbot.route_task_field_retest_operator_drill.v1`
- Summary schema:
  `trashbot.route_task_field_retest_operator_drill_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_operator_drill_gate`
- Preferred inputs:
  `trashbot.route_task_field_retest_material_callback_review_decision.v1` and
  `trashbot.route_task_field_retest_material_callback_review_decision_summary.v1`
  with
  `evidence_boundary=software_proof_docker_route_task_field_retest_material_callback_review_decision_gate`.
- Legacy compatible inputs:
  `trashbot.route_task_field_retest_material_pack.v1` and
  `trashbot.route_task_field_retest_material_pack_summary.v1` with
  `evidence_boundary=software_proof_docker_route_task_field_retest_material_pack_gate`.

The output schema stays unchanged and always includes `source_family`,
`source_schema`, `source_boundary`, `command_chain`, `required_outputs`,
`missing_material_prompts`, `operator_callback_checklist`, `rerun_notes`,
`safe_copy`, `not_proven`, `delivery_success=false`,
`primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_operator_drill_gate`.
For review-decision inputs it also mirrors `source_review_decision` so
Robot/mobile readers can show that the operator drill is based on the reviewed
callback source rather than a material pack-only drill.

Operator drill status values include `ready_for_operator_drill_not_proven`,
`blocked_missing_material_pack`, `blocked_bad_json`,
`blocked_unsupported_schema`, `blocked_missing_evidence_ref`,
`blocked_same_evidence_ref_mismatch`,
`blocked_same_evidence_ref_not_required`, and
`blocked_unsafe_material_pack_copy`. The gate fails closed on missing or bad
JSON, unsupported schema or boundary, weak or mismatched evidence refs, weak
`same_evidence_ref_required`, unsafe copy, raw paths, credentials, ROS topics,
serial/UART/WAVE ROVER text, success/control claims, `delivery_success=true`,
or `primary_actions_enabled=true`.

This contract is software proof only. It does not prove a real route/elevator
field pass, Nav2 or fixed-route execution, task record or completion signal,
dropoff/cancel completion, delivery success, HIL, WAVE ROVER/UART feedback,
real phone/browser validation, Objective 5 external cloud/4G/OSS/CDN/DB/queue
proof, or any primary robot action being enabled.

## route_task_field_retest_result_review_dispatch

`pc-tools/evidence/route_task_field_retest_result_review_dispatch.py`
generates the PC-only dispatch gate after
`route_task_field_retest_result_backfill_review_decision.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_review_dispatch.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_review_dispatch_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_review_dispatch_gate`
- Allowed inputs:
  `trashbot.route_task_field_retest_result_backfill_review_decision.v1` and
  `trashbot.route_task_field_retest_result_backfill_review_decision_summary.v1`
  only. Wrapper or nested JSON is allowed when it contains one of those schemas.
- Disallowed inputs:
  raw upstream artifacts, material directories, ROS2/Nav2 runtime state,
  hardware transport logs, external cloud evidence, real phone/browser evidence,
  or arbitrary JSON without the supported schema and boundary.

The output always includes `source_review_decision`, `material_categories`,
`accepted_materials`, `missing_materials`, `rejected_materials`,
`owner_work_orders`, `callback_packet_requirements`, `rerun_commands`,
`same_evidence_ref_required=true`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_review_dispatch_gate`.

The gate fails closed on missing or bad JSON, unsupported schema or boundary,
review decision not ready, evidence_ref mismatch, weak
`same_evidence_ref_required`, unsafe copy, success/control claims,
`delivery_success=true`, or `primary_actions_enabled=true`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.

## route_task_field_retest_result_callback_intake

`pc-tools/evidence/route_task_field_retest_result_callback_intake.py`
generates the PC-only callback intake gate after
`route_task_field_retest_result_review_dispatch.py`.

- Artifact schema:
  `trashbot.route_task_field_retest_result_callback_intake.v1`
- Summary schema:
  `trashbot.route_task_field_retest_result_callback_intake_summary.v1`
- Evidence boundary:
  `software_proof_docker_route_task_field_retest_result_callback_intake_gate`
- Allowed dispatch inputs:
  `trashbot.route_task_field_retest_result_review_dispatch.v1` and
  `trashbot.route_task_field_retest_result_review_dispatch_summary.v1`
  only. Wrapper or nested JSON is allowed only through known safe wrapper keys.
- Allowed callback inputs:
  a safe callback packet fixture or sample with optional
  `trashbot.route_task_field_retest_result_callback_packet.v1` schema. The
  packet must carry `safe_evidence_ref` or `evidence_ref`, strict JSON
  `same_evidence_ref_required=true`, per-item `owner_work_orders` responses,
  and per-item `callback_packet_requirements` responses.
- Disallowed inputs:
  the older `route_task_field_retest_evidence_dispatch` source contract, raw
  upstream artifacts, material directories, ROS2/Nav2 runtime state, hardware
  transport logs, external cloud evidence, real phone/browser evidence, or
  arbitrary JSON without supported schema and boundary.

The output always includes `safe_evidence_ref`, `source_dispatch`,
`callback_packet`, `owner_work_orders`, `callback_packet_requirements`,
`accepted_updates`, `missing_updates`, `rejected_updates`, `owner_follow_up`,
`review_decision_handoff`, `rerun_commands`, `safe_copy`, `not_proven`,
`delivery_success=false`, `primary_actions_enabled=false`, and
`evidence_boundary=software_proof_docker_route_task_field_retest_result_callback_intake_gate`.

The gate fails closed on missing or bad JSON, unsupported schema or boundary,
dispatch not ready, evidence_ref mismatch, weak `same_evidence_ref_required`,
weak callback response types, missing or rejected callback updates, unsafe copy,
raw paths, checksum text, credentials, ROS topics, serial/UART/WAVE ROVER text,
success/control claims, `delivery_success=true`, or
`primary_actions_enabled=true`.

This contract is software proof only. It does not prove a real route/elevator
field pass, HIL pass, real Nav2/fixed-route execution, real delivery success,
real phone/browser validation, O5 external cloud proof, or any primary robot
action being enabled.
