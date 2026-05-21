# Field Evidence Real Material Request Dispatch Tech Plan

Run time: 2026-05-21 14:15 CST

## Capability

- capability: `field_evidence_real_material_request_dispatch`
- evidence boundary: `software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- sprint_type: epic
- planning owner: Product Manager / OKR Owner
- execution owner split:
  - Autonomy Algorithm Engineer for route/task evidence semantics.
  - Robot Platform Engineer for diagnostics-safe artifact/gate and Robot/API boundary.
  - User Touchpoint Full-Stack Engineer for field-owner/mobile-facing request copy and true phone/browser evidence semantics.
  - Hardware Infra Engineer for elevator/human-assistance evidence review and hardware-adjacent no-claim boundary.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint does not target Objective 5 percentage movement because current available evidence is only `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`. Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/migration/cutover, production app/device, and true phone/browser evidence are still missing.
3. The next lowest Objective is Objective 1 at about 81%. This sprint does not target Objective 1 percentage movement because PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved, comment `3269642220` is only software-proof reply publication, and real vendor-sourced 2D LiDAR / ToF plus WAVE ROVER/UART/HIL materials remain missing.
4. Because O5 and O1 real materials are unavailable, this sprint targets the next actionable family: O2/O3/O4 real field material request dispatch. It converts the previous acceptance backfill state into a field-owner request for same safe `evidence_ref` materials instead of repeating another backfill wrapper.

## Inputs To Read In Execution

The execution sprint must read:

- `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md`
- the previous acceptance backfill summary artifact or fixture if present
- current Robot diagnostics safe summary contract
- current `mobile/web` phone-safe evidence panels
- `docs/product/mobile_user_flow.md`
- `docs/interfaces/evidence_contracts.md`
- `docs/interfaces/ros_runtime_contracts.md`

If execution touches hardware assumptions, WAVE ROVER, UART, LiDAR, ToF, voltage, pins, mechanical dimensions, or serial details, Hardware Infra Engineer must first read `docs/vendor/VENDOR_INDEX.md` and cited local vendor files. This planning task does not authorize hardware configuration changes.

## Proposed Implementation Shape For Next Stage

Create a software-proof gate or artifact that:

1. Loads the previous acceptance backfill safe state.
2. Requires `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
3. Requires the field-owner request to use one same safe `evidence_ref`.
4. Emits a request checklist for:
   - `task_record`
   - `nav2_fixed_route_runtime_log`
   - `route_completion_signal`
   - `elevator_door_floor_evidence`
   - `human_assistance_note`
   - `dropoff_cancel_completion`
   - `delivery_result`
   - `true_phone_browser_evidence`
   - `diagnostics_mobile_safe_summary`
5. Fails closed when any mandatory prior safe-state field is missing, unsafe, stale, or mismatched.
6. Produces phone-safe/operator-safe output only; no raw ROS topics, `/cmd_vel`, serial devices, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, local paths, tracebacks, checksums, or complete artifacts.
7. States that this is not real field rerun, not true phone/browser proof, not Nav2/fixed-route proof, not route/elevator field pass, not HIL, not O5 external proof, not PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution, not delivery result, and not delivery success.

## Owner File Ranges For Execution

Suggested non-overlapping execution split:

- Autonomy Algorithm Engineer:
  - `pc-tools/evidence/field_evidence_real_material_request_dispatch.py`
  - `pc-tools/evidence/test_field_evidence_real_material_request_dispatch.py`
  - `docs/interfaces/evidence_contracts.md`
- Robot Platform Engineer:
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_runtime_contracts.md`
- User Touchpoint Full-Stack Engineer:
  - `mobile/web/app.js`
  - `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_request_dispatch.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- Hardware Infra Engineer:
  - read-only consultation by default unless execution expands hardware docs
  - if writing is approved later: `docs/vendor/`-cited hardware boundary notes only
- Product Manager / OKR Owner:
  - `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-done.md`
  - `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/side2side_check.md`
  - `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/final.md`
  - `OKR.md`
  - `docs/process/okr_progress_log.md`

This planning task is limited to the three planning files in this sprint folder.

## Interface Contract Requirements

Required request fields:

- `schema=trashbot.field_evidence_real_material_request_dispatch.v1`
- `schema_version=1`
- `capability=field_evidence_real_material_request_dispatch`
- `evidence_boundary=software_proof_docker_field_evidence_real_material_request_dispatch_gate`
- `source=software_proof`
- `status=not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`
- `required_materials=[task_record, nav2_fixed_route_runtime_log, route_completion_signal, elevator_door_floor_evidence, human_assistance_note, dropoff_cancel_completion, delivery_result, true_phone_browser_evidence, diagnostics_mobile_safe_summary]`
- `blocked_claims=[real_field_rerun, true_phone_browser_proof, nav2_fixed_route_proof, route_elevator_field_pass, hil_pass, o5_external_proof, pr5_thread_resolved, delivery_result, delivery_success]`

## Validation Plan For Execution Stage

Each execution owner must use fenced validation only:

- Autonomy: `py_compile`, focused unittest, CLI/help or fixture drill, required `rg`, scoped `git diff --check`.
- Robot: `py_compile`, focused diagnostics unittest, required `rg`, scoped `git diff --check`.
- Full-Stack: `node --check mobile/web/app.js`, JSON fixture validation, focused mobile unittest, required `rg`, scoped `git diff --check`.
- Product closeout: file-existence checks, required evidence-boundary `rg`, scoped `git diff --check`, and only targeted integration checks returned by Engineers.

## Acceptance Commands For This Planning Task

```bash
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/pre_start.md
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/prd.md
test -f sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_real_material_request_dispatch|software_proof_docker_field_evidence_real_material_request_dispatch_gate|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|not_proven" sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch
git diff --check -- sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch
```

## Sprint Documentation To Create Or Update

Created in this planning task:

- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/pre_start.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/prd.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-plan.md`

Required after execution:

- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/tech-done.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/side2side_check.md`
- `sprints/2026.05.21_14-15_field-evidence-real-material-request-dispatch/final.md`
- `OKR.md` only if closeout evidence warrants a conservative status update.
- Related `docs/` pages if product, interface, Robot diagnostics, or mobile semantics change.

## Risks And Blocks

- This sprint cannot itself improve Objective 5 because it does not produce real external cloud/4G/OSS/CDN/DB/queue/phone proof.
- This sprint cannot itself improve Objective 1 because it does not resolve PR #5 `PRRT_kwDOSWB9286CJ3tX` or provide real vendor/hardware/HIL materials.
- This sprint cannot itself prove O2/O3/O4 field completion. It only dispatches the material request needed before a future intake/review can accept real field evidence.
- If execution produces only another wrapper and no concrete field-owner request, it should be rejected at Product closeout.
