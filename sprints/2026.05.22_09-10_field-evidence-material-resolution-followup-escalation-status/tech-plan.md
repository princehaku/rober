# Field Evidence Material Resolution Followup Escalation Status Tech Plan

Run time: 2026-05-22 09:00 Asia/Shanghai

## Goal

Implement `field_evidence_material_resolution_followup_escalation_status` as the next software-proof rung after `field_evidence_material_resolution_review_handoff`. The work must convert “handoff sent, real owner response material still missing” into a traceable owner/CEO escalation status while preserving `software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate`, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and no OKR percentage lift.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. This sprint targets Objective 5's blocker resolution chain because it is still the lowest Objective.
3. Objective 1 is about 81%, and Objectives 2/3/4 are about 99%.
4. This sprint must not raise Objective 5 because the current host has no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, true phone/browser evidence, verified terminal delivery/dropoff/cancel result, route/elevator field pass, real hardware/HIL, real owner response material, or PR #5 reviewer resolution.
5. The previous final explicitly says the next useful step is owner response material or escalate for owner action. Therefore this sprint is valid only as `followup escalation status`, not as another local-only handoff wrapper and not as OKR movement.
6. `final.md` must re-check whether the status still lacks real material. If it does, closeout must keep percentages unchanged and name the owner/CEO action needed next.

## Evidence Inputs

- `AGENTS.md` and `docs/process/iteration_velocity.md` for Epic sprint, parallel owner split, repeated-blocker cap, and OKR lowest-priority rules.
- `OKR.md` 4.1 and section 6 for current completion and no-lift evidence boundaries.
- `sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/final.md`, especially: next useful step is real handoff response material or escalate for owner action; another local-only wrapper should not be counted as OKR movement.
- `docs/product/mobile_user_flow.md` for phone-safe read-only panel and disabled primary-action semantics.
- `docs/vendor/VENDOR_INDEX.md` for Hardware consultation source boundary if hardware facts are mentioned.
- Git chain:
  - `43a3f01 Add field evidence resolution handoff gate`
  - `a384c84 Add field evidence resolution review decision`
- GitHub PR #5 review thread evidence from the CEO prompt:
  - `PRRT_kwDOSWB9286CJ3tQ` resolved
  - `PRRT_kwDOSWB9286CJ3tU` resolved
  - `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`
  - comment `3269642220` is software-proof reply, not reviewer resolution

## File Structure For Next Execution

### A. Autonomy Engineer

Allowed files:

- `pc-tools/evidence/`
- Targeted tests under `pc-tools/evidence/`
- Relevant evidence contract docs only if the implementation changes contract shape

Disallowed:

- Robot diagnostics code
- `mobile/web/`
- Hardware configuration
- `OKR.md`

### B. Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/`
- Targeted diagnostics tests under `onboard/src/ros2_trashbot_behavior/`
- Relevant `docs/interfaces/` files only if the safe diagnostics contract changes

Disallowed:

- PC evidence gate implementation
- `mobile/web/`
- Hardware configuration
- `OKR.md`

### C. Full-Stack Engineer

Allowed files:

- `mobile/web/`
- `mobile/web/` fixtures/tests or existing mobile web test files
- `docs/product/mobile_user_flow.md` only if the read-only panel contract changes

Disallowed:

- PC evidence gate implementation
- Robot diagnostics internals
- Hardware configuration
- `OKR.md`

### D. Hardware Engineer

Allowed files:

- Read-only consultation against `docs/vendor/VENDOR_INDEX.md` and referenced local vendor files
- No file changes expected unless implementation explicitly needs boundary wording in an allowed docs file

Disallowed:

- Hardware config changes
- Launch parameter changes
- Vendor file edits
- Any claim that hardware/HIL, 2D LiDAR / ToF, WAVE ROVER/UART, or PR #5 resolution is proven

### E. Product Owner

Allowed closeout files after implementation:

- `sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/tech-done.md`
- `sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/final.md`
- `OKR.md` and `docs/process/okr_progress_log.md` only if real evidence or conservative closeout wording requires it

## Interface Contract

The implementation should emit a safe summary with these required semantics:

- `capability=field_evidence_material_resolution_followup_escalation_status`
- `proof_boundary=software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate`
- `source=software_proof`
- `not_proven=true`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- safe `evidence_ref`
- previous handoff reference, expected to trace to `43a3f01`
- previous review decision reference, expected to trace to `a384c84`
- `owner_response_material_status=missing` or equivalent unless real owner material is present
- `followup_status` such as `pending_owner_response_not_proven`, `overdue_owner_response_not_proven`, or `escalated_for_owner_action_not_proven`
- `due_status`, `blocked_reason`, `next_required_evidence`, `owner_action`, and `ceo_escalation_recommendation`
- PR #5 thread state: `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live evidence changes

The contract must fail closed when the previous handoff summary is missing, lacks a safe `evidence_ref`, contains success wording, enables primary actions, lacks proof boundary, or claims reviewer/material/field/cloud/hardware proof.

## Parallel Owner Tasks

### Task A: PC Evidence Followup Escalation Gate

Owner: `autonomy-engineer`

Build the `field_evidence_material_resolution_followup_escalation_status` CLI/gate under `pc-tools/evidence/`. It must consume the previous `field_evidence_material_resolution_review_handoff` summary, preserve the `43a3f01` and `a384c84` lineage, and emit a sanitized escalation status that names missing owner response material and next owner/CEO action.

Required behavior:

- Accept a previous review-handoff summary as input.
- Reject or block missing safe `evidence_ref`, missing proof boundary, success claims, unsafe raw artifacts, enabled primary actions, reviewer-resolution claims, or field/cloud/phone/HIL proof claims.
- Emit `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Include `owner response material` and `escalate` wording in safe status or operator next steps.

Acceptance commands:

```bash
python3 -m py_compile <new-or-touched-pc-evidence-files>
python3 -m unittest <targeted-pc-evidence-test-module>
python3 <new-cli-path> --help
rg -n "field_evidence_material_resolution_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate|owner response material|escalate|43a3f01|a384c84" pc-tools/evidence
git diff --check -- pc-tools/evidence <any-touched-evidence-docs>
```

### Task B: Robot Diagnostics Safe Alias

Owner: `robot-software-engineer`

Expose a read-only diagnostics alias under `onboard/src/ros2_trashbot_behavior/`, expected name `robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary`. It must consume the PC safe summary shape or compatible fallback and never turn escalation status into readiness.

Required behavior:

- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Redact raw artifacts, raw GitHub data, local paths, credentials, ROS topics, `/cmd_vel`, serial/UART details, and WAVE ROVER parameters.
- Keep status read-only for diagnostics and operator support.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/<touched-files>
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_followup_escalation_status_summary|field_evidence_material_resolution_followup_escalation_status|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior
git diff --check -- onboard/src/ros2_trashbot_behavior <any-touched-interface-docs>
```

### Task C: Mobile/Web Read-Only Escalation Panel

Owner: `full-stack-software-engineer`

Add a read-only escalation panel under `mobile/web/` that consumes the Robot/PC safe summary and displays owner followup status, due/escalation state, missing owner response material, next required evidence, evidence boundary, and not-proven flags.

Required behavior:

- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel must not fetch raw diagnostics by itself, mutate ACK/cursor state, send commands, expose raw artifacts, or show success copy.
- Missing summary fails closed with blocked/not-proven copy.
- Fixture/tests must prove `primary_actions_enabled=false` and no delivery success claim.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool <new-or-touched-mobile-fixture-json>
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_resolution_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate|owner response material|escalate|primary_actions_enabled=false|delivery_success=false" mobile/web
git diff --check -- mobile/web <any-touched-product-docs>
```

### Task D: Hardware Boundary Consultation

Owner: `robot-hardware-engineer`

Perform read-only consultation for vendor and PR #5 boundary language. If any implementation copy references WAVE ROVER, UART, 2D LiDAR, ToF, install, wiring, power, calibration, HIL, or PR #5 hardware material, consult `docs/vendor/VENDOR_INDEX.md` first and cite the local source boundary in the worker result.

Required behavior:

- Do not edit hardware config, launch defaults, vendor files, or hardware parameters.
- Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live GitHub review evidence changes.
- Confirm comment `3269642220` is software-proof reply only, not reviewer resolution.
- Confirm no real WAVE ROVER/UART/HIL or installed/procured/calibrated 2D LiDAR / ToF proof is present on this host.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|3269642220|hardware_material_pending|WAVE ROVER|UART|HIL|2D LiDAR|ToF" docs/vendor docs/product onboard/src/ros2_trashbot_behavior mobile/web pc-tools/evidence
git diff --check -- docs/vendor docs/product onboard/src/ros2_trashbot_behavior mobile/web pc-tools/evidence
```

### Task E: Product Closeout

Owner: `product-okr-owner`

After Tasks A-D return, collect validation evidence and update closeout docs. Product must verify that implementation owners updated relevant `docs/` files if contracts or product surfaces changed, and must preserve OKR percentages unless real evidence appears.

Required behavior:

- Create/update `tech-done.md`, `side2side_check.md`, and `final.md`.
- Record worker validation and any failed/retried commands.
- Confirm whether `OKR.md` and `docs/process/okr_progress_log.md` require conservative no-lift wording.
- State explicitly that `field_evidence_material_resolution_followup_escalation_status` is software proof only and not OKR movement if no real owner response material arrived.

Acceptance commands:

```bash
test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/tech-done.md && test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/side2side_check.md && test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/final.md
rg -n "field_evidence_material_resolution_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate|Objective 5|68%|owner response material|escalate|no OKR percentage" sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status OKR.md docs/process/okr_progress_log.md <any-docs-touched-by-implementation>
```

## Integration And Dispatch Notes

- This is a 4-owner parallel execution sprint plus Product closeout. Tasks A, B, C, and D have non-overlapping write scopes and should be dispatched in parallel.
- Hardware Task D is consultation-only and should not block software work unless it finds unsafe hardware wording.
- Product Task E starts after implementation owners return.
- Main session must not implement product code or tests directly; implementation and validation belong to the owner agents.

## Validation Plan For This Planning Pass

Run and record:

```bash
test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/pre_start.md && test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/prd.md && test -f sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_material_resolution_followup_escalation_status|software_proof_docker_field_evidence_material_resolution_followup_escalation_status_gate|PRRT_kwDOSWB9286CJ3tX|43a3f01|a384c84|owner response material|escalate" sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status
```

```bash
git diff --check -- sprints/2026.05.22_09-10_field-evidence-material-resolution-followup-escalation-status
```

## Implementation Guardrails

- Do not claim real external cloud proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery success, HIL, hardware readiness, owner response received, or PR #5 resolution.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Do not expose raw artifacts, raw JSON, credentials, local paths, complete logs, checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, raw vendor data, or hardware internals in phone-safe copy.
- Do not update OKR percentages unless real material appears and is recorded with evidence.
- If real owner response material arrives during execution, Product must pause percentage changes until it is reviewed and tied to the same safe `evidence_ref`.

## Remaining Risks Before Execution

- The host remains Docker-only, so real external, phone, field, hardware, and HIL validation are not expected.
- This sprint can make escalation traceable, but it still cannot create the missing real material.
- If no owner response material arrives after this sprint, the next useful action is CEO/owner escalation or actual material collection, not another local-only wrapper.
