# Evidence Contracts

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
