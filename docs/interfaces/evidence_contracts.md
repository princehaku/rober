# Evidence Contracts

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
