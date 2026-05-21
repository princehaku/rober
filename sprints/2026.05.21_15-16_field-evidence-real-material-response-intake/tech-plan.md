# Field Evidence Real Material Response Intake Tech Plan

Run time: 2026-05-21 15:16 CST

## Capability

- capability: `field_evidence_real_material_response_intake`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_intake_gate`
- sprint_type: epic
- planning owner: Product Manager / OKR Owner
- execution owner split:
  - Autonomy Algorithm Engineer for route/task and Nav2/fixed-route response classification.
  - Robot Platform Engineer for diagnostics-safe response-intake artifact and Robot/API boundary.
  - User Touchpoint Full-Stack Engineer for field-owner/mobile-facing response status and true phone/browser response semantics.
  - Hardware Infra Engineer for read-only vendor-source, elevator, human-assistance, LiDAR/ToF, WAVE ROVER/UART/HIL boundary consultation.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint does not target Objective 5 percentage movement because real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, and true phone/browser evidence are still missing. Per stop rule, adding another local O5 metadata wrapper would not be meaningful progress.
3. The next lowest Objective is Objective 1 at about 81%. This sprint does not target Objective 1 percentage movement because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, GitHub comment `3269642220` is only software-proof reply publication, and real vendor-sourced 2D LiDAR / ToF plus WAVE ROVER/UART/HIL materials remain missing.
4. Because O5 and O1 real materials are unavailable, this sprint targets the next actionable family: O2/O3/O4 field evidence response intake. The prior sprint dispatched nine real-material requests; this sprint plans the gate that classifies field-owner replies as `accepted`, `missing`, `rejected`, or `blocked` while preserving `not_proven` and false flags.

## Inputs To Read In Execution

Execution owners must read:

- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/final.md`
- the previous request dispatch artifact or fixture if present
- current Robot diagnostics safe summary contract
- current `mobile/web` field-material panels and fixtures
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/evidence_contracts.md`
- `docs/interfaces/ros_runtime_contracts.md`

Hardware read-only consultation must read `docs/vendor/VENDOR_INDEX.md` and cited local vendor files before making any statement about WAVE ROVER, UART, LiDAR, ToF, pins, voltage, baudrate, JSON commands, feedback protocol, or mechanical dimensions. This planning task does not authorize hardware configuration changes.

## Proposed Implementation Shape For Next Stage

Create a software-proof response-intake gate or artifact that:

1. Loads or cites the previous `field_evidence_real_material_request_dispatch` request state.
2. Requires `source=software_proof`, `status=not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
3. Requires one same safe `evidence_ref` across all returned material summaries.
4. Classifies each required material category as `accepted`, `missing`, `rejected`, or `blocked`.
5. Uses `accepted` only as "ready for later review", not as field pass or delivery success.
6. Fails closed when prior request state is missing, response schema is invalid, `evidence_ref` is missing or mixed, unsafe success claims appear, or raw sensitive details are present.
7. Produces phone-safe/operator-safe output only; no raw ROS topics, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, OSS secrets, local paths, tracebacks, checksums, or complete artifacts.
8. States that this is not real field rerun, not true phone/browser proof, not Nav2/fixed-route proof, not route/elevator field pass, not HIL, not WAVE ROVER/UART proof, not O5 external proof, not PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution, not delivery result, and not delivery success.

## Owner File Ranges For Execution

Suggested non-overlapping execution split:

- Autonomy Algorithm Engineer:
  - `pc-tools/evidence/field_evidence_real_material_response_intake.py`
  - `pc-tools/evidence/test_field_evidence_real_material_response_intake.py`
  - `docs/interfaces/evidence_contracts.md`
- Robot Platform Engineer:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_runtime_contracts.md`
- User Touchpoint Full-Stack Engineer:
  - `mobile/web/app.js`
  - `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_intake.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- Hardware Infra Engineer:
  - read-only consultation only by default
  - if later writing is approved: vendor-cited hardware boundary docs only, with source references from `docs/vendor/VENDOR_INDEX.md`
- Product Manager / OKR Owner:
  - `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/tech-done.md`
  - `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/side2side_check.md`
  - `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`

This planning task is limited to the three planning files in this sprint folder.

## Parallel Owner Launch Plan

The implementation stage should launch four parallel owners when execution begins:

- Autonomy: implement PC response-intake classification and route/task material status rules.
- Robot: expose diagnostics-safe alias/summary, preserving fail-closed metadata.
- Full-Stack: render read-only mobile response-intake status and keep primary actions disabled.
- Hardware read-only consultation: confirm vendor-source and hardware-adjacent no-claim boundaries before any hardware-sensitive wording lands.

The owners can run in parallel because their write scopes are disjoint except for docs. Docs edits must be coordinated by file ownership above to avoid overlapping writes.

## Interface Contract Requirements

Required response-intake fields:

- `schema=trashbot.field_evidence_real_material_response_intake.v1`
- `schema_version=1`
- `capability=field_evidence_real_material_response_intake`
- `evidence_boundary=software_proof_docker_field_evidence_real_material_response_intake_gate`
- `source=software_proof`
- `status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `response_statuses=[accepted, missing, rejected, blocked]`
- `required_materials=[task_record, nav2_fixed_route_runtime_log, route_completion_signal, elevator_door_floor_evidence, human_assistance_note, dropoff_cancel_completion, delivery_result, true_phone_browser_evidence, diagnostics_mobile_safe_summary]`
- `blocked_claims=[real_field_rerun, true_phone_browser_proof, nav2_fixed_route_proof, route_elevator_field_pass, hil_pass, wave_rover_uart_proof, o5_external_proof, pr5_thread_resolved, delivery_result, delivery_success]`

Classification rules:

- `accepted`: present, safe, same-`evidence_ref`, redacted, and ready for later review only.
- `missing`: required category absent from field-owner response.
- `rejected`: present but unsafe, stale, mixed-`evidence_ref`, success-claiming, raw, credential-bearing, hardware-claiming without source, or outside contract.
- `blocked`: field owner cannot capture the material because real hardware, field route, phone/browser, cloud, elevator, or operator dependency is unavailable.

## Validation Plan For Execution Stage

Each execution owner must use fenced validation only:

- Autonomy: `py_compile`, focused unittest, CLI/help or fixture drill, required `rg`, scoped `git diff --check`.
- Robot: `py_compile`, focused diagnostics unittest, required `rg`, scoped `git diff --check`.
- Full-Stack: `node --check mobile/web/app.js`, JSON fixture validation, focused mobile unittest, required `rg`, scoped `git diff --check`.
- Hardware consultation: source citation check against `docs/vendor/VENDOR_INDEX.md` and no-write confirmation unless explicitly expanded.
- Product closeout: file-existence checks, required evidence-boundary `rg`, scoped `git diff --check`, and only targeted integration checks returned by Engineers.

Do not add broad regression sweeps. Do not run full Docker/Humble build unless an implementation change touches ROS2 package integration or the execution owner identifies a concrete integration risk.

## Acceptance Commands For This Planning Task

```bash
test -f sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/pre_start.md
test -f sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/prd.md
test -f sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/tech-plan.md
rg -n "sprint_type: epic|field_evidence_real_material_response_intake|OKR 最低优先级核对|Objective 5|PRRT_kwDOSWB9286CJ3tX|3269642220|software_proof_docker_field_evidence_real_material_response_intake_gate|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_15-16_field-evidence-real-material-response-intake
git diff --check -- sprints/2026.05.21_15-16_field-evidence-real-material-response-intake
```

## Sprint Documentation To Create Or Update

Created in this planning task:

- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/pre_start.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/prd.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/tech-plan.md`

Required after execution:

- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/tech-done.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/side2side_check.md`
- `sprints/2026.05.21_15-16_field-evidence-real-material-response-intake/final.md`
- `OKR.md` only if closeout evidence warrants a conservative status update.
- Related `docs/` pages if product, interface, Robot diagnostics, or mobile semantics change.

## Risks And Blocks

- This sprint cannot improve Objective 5 without real external cloud, 4G/SIM, OSS/CDN, DB/queue, worker/cutover, production app/device, or true phone/browser proof.
- This sprint cannot improve Objective 1 without real vendor-sourced 2D LiDAR / ToF and WAVE ROVER/UART/HIL materials, plus PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution.
- This sprint cannot prove O2/O3/O4 field completion. It only plans response intake for the materials requested in the previous sprint.
- If execution receives no real field-owner response, the correct result is `missing` or `blocked`, not acceptance.
- If execution receives partial material, Product closeout must preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
