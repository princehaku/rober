# Field Evidence Material Resolution Owner Response Review Decision Tech Plan

Run time: 2026-05-22 14:03 Asia/Shanghai

## Goal

Implement `field_evidence_material_resolution_owner_response_review_decision` as the next software-proof rung after `field_evidence_material_resolution_owner_response_intake`. The work must classify owner response material into structured review decisions while preserving `software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and no OKR percentage lift without real reviewed evidence.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. This sprint targets Objective 5's blocker-resolution evidence chain because it is still the lowest Objective.
3. Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
4. Objective 5 still cannot rise because this Docker-only host has no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, true phone/browser evidence, verified terminal delivery/dropoff/cancel result, route/elevator field pass, real hardware/HIL, real reviewed owner response material, or delivery success.
5. Objective 1 PR #5 still cannot count as resolved because `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`, and comment `3269642220` is software-proof only rather than reviewer resolution.
6. This sprint is not a repeat of intake or escalation status. It consumes `field_evidence_material_resolution_owner_response_intake` and adds a decision layer: `accepted_for_material_review_not_proven`, `needs_more_evidence_not_proven`, `rejected_unsafe_material_response_not_proven`, or `blocked_missing_owner_response_intake_not_proven`.
7. `final.md` must re-check whether real owner response material arrived and whether it was only accepted for later material review. If no real reviewed material exists, closeout must keep percentages unchanged and name the owner/CEO action needed next.

## Evidence Inputs

- `AGENTS.md` for Epic sprint, fresh sprint folder, parallel owner split, repeated-blocker cap, and OKR lowest-priority rules.
- `OKR.md` 4.1 and section 6 for current completion and no-lift evidence boundaries.
- `sprints/2026.05.22_10-11_field-evidence-material-resolution-owner-response-intake/final.md`, especially: the predecessor completed only software-proof owner response intake and left real owner response material unreviewed or pending.
- `sprints/2026.05.22_12-13_verified-terminal-result-material-review-handoff/final.md`, especially: no real terminal delivery/dropoff/cancel result material was provided.
- `sprints/2026.05.22_13-14_wave-rover-hil-packet-collection-drill/final.md`, especially: no real WAVE ROVER/UART/HIL, 2D LiDAR/ToF material, operator report, or reviewer resolution was provided.
- `docs/product/mobile_user_flow.md` for phone-safe read-only panel and disabled primary-action semantics.
- `docs/product/cloud_4g_infrastructure.md` for O5 cloud proof boundaries.
- `docs/product/production_hardware_boundary.md` and `docs/vendor/VENDOR_INDEX.md` for Hardware consultation source boundaries.
- GitHub PR #5 review thread evidence from the CEO prompt: `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`, and comment `3269642220` is software-proof reply, not reviewer resolution.

## File Structure For Next Execution

### A. Autonomy Engineer

Allowed files:

- Create `pc-tools/evidence/field_evidence_material_resolution_owner_response_review_decision.py`
- Create targeted tests under `pc-tools/evidence/`, expected `pc-tools/evidence/test_field_evidence_material_resolution_owner_response_review_decision.py`
- Update evidence docs, expected `pc-tools/README.md` and `docs/interfaces/evidence_contracts.md`, only if the implementation changes contract shape

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

- `sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/tech-done.md`
- `sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/side2side_check.md`
- `sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/final.md`
- `OKR.md` and `docs/process/okr_progress_log.md` only if real evidence or conservative closeout wording requires it

## Interface Contract

The implementation should emit a safe summary with these required semantics:

- `capability=field_evidence_material_resolution_owner_response_review_decision`
- `proof_boundary=software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate`
- `source=software_proof`
- `not_proven=true`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- safe `evidence_ref`
- previous intake reference, expected to trace to `field_evidence_material_resolution_owner_response_intake`
- `owner response material` status from the intake summary
- `review_decision=accepted_for_material_review_not_proven`, `needs_more_evidence_not_proven`, `rejected_unsafe_material_response_not_proven`, or `blocked_missing_owner_response_intake_not_proven`
- `decision_reasons`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `next_required_evidence`, `owner_action`, `ceo_escalation_recommendation`, and `review_handoff_recommendation`
- PR #5 thread state: `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live reviewer evidence changes

The contract must fail closed when the previous intake summary is missing, lacks a safe `evidence_ref`, contains success wording, enables primary actions, lacks proof boundary, claims reviewer resolution, claims material review acceptance beyond `accepted_for_material_review_not_proven`, or claims field/cloud/phone/hardware/HIL proof.

## Parallel Owner Tasks

### Task A: PC Owner Response Review Decision Gate

Owner: `autonomy-engineer`

Build the `field_evidence_material_resolution_owner_response_review_decision` CLI/gate under `pc-tools/evidence/field_evidence_material_resolution_owner_response_review_decision.py`. It must consume the previous `field_evidence_material_resolution_owner_response_intake` safe summary, preserve the same safe `evidence_ref`, and emit one of the supported review decisions.

Required behavior:

- Accept a previous owner-response intake safe summary as input.
- Classify owner response material as accepted for later material review, needs more evidence, rejected unsafe, or blocked missing intake.
- Reject or block missing safe `evidence_ref`, evidence-ref mismatch, missing proof boundary, success claims, unsafe raw artifacts, enabled primary actions, reviewer-resolution claims, delivery-success claims, or field/cloud/phone/HIL proof claims.
- Emit `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Include `owner response material`, `accepted_materials`, `missing_materials`, `rejected_materials`, `unsafe_materials`, `decision_reasons`, and `next_required_evidence` in safe output.
- Update targeted evidence docs if the summary contract changes.

Acceptance commands:

```bash
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_owner_response_review_decision.py
python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_owner_response_review_decision
python3 pc-tools/evidence/field_evidence_material_resolution_owner_response_review_decision.py --help
rg -n "field_evidence_material_resolution_owner_response_review_decision|software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate|owner response material|accepted_for_material_review_not_proven|needs_more_evidence_not_proven|rejected_unsafe_material_response_not_proven|blocked_missing_owner_response_intake_not_proven|not_proven|primary_actions_enabled=false|delivery_success=false|safe_to_control=false" pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence pc-tools/README.md docs/interfaces/evidence_contracts.md
```

### Task B: Robot Diagnostics Safe Alias

Owner: `robot-software-engineer`

Expose a read-only diagnostics alias under `onboard/src/ros2_trashbot_behavior/`, expected name `robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary`. It must consume the PC safe summary shape or compatible fallback and never turn a review decision into readiness, command authorization, delivery success, owner-material acceptance, or reviewer resolution.

Required behavior:

- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Preserve decision, decision reasons, accepted/missing/rejected/unsafe material categories in phone-safe form.
- Redact raw artifacts, raw GitHub data, local paths, credentials, DB/queue URLs, OSS AK/SK, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, tracebacks, and checksums.
- Keep status read-only for diagnostics and operator support.
- Update interface docs if the diagnostics contract changes.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/<touched-files>
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
rg -n "robot_diagnostics_field_evidence_material_resolution_owner_response_review_decision_summary|field_evidence_material_resolution_owner_response_review_decision|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces
git diff --check -- onboard/src/ros2_trashbot_behavior docs/interfaces
```

### Task C: Mobile/Web Read-Only Owner Response Review Decision Panel

Owner: `full-stack-software-engineer`

Add a read-only owner-response review decision panel under `mobile/web/` that consumes the Robot/PC safe summary and displays review decision, decision reasons, accepted/missing/rejected/unsafe material categories, next required evidence, evidence boundary, and not-proven flags.

Required behavior:

- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel must not fetch raw diagnostics by itself, mutate ACK/cursor state, send commands, expose raw artifacts, or show success copy.
- Missing summary fails closed with `blocked_missing_owner_response_intake_not_proven` or compatible blocked/not-proven copy.
- Fixture/tests must prove `primary_actions_enabled=false`, `delivery_success=false`, `safe_to_control=false`, and no delivery success claim.
- Update `docs/product/mobile_user_flow.md` only if the mobile contract changes.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool <new-or-touched-mobile-fixture-json>
python3 -m unittest mobile.web.test_mobile_web_entrypoint
rg -n "field_evidence_material_resolution_owner_response_review_decision|software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate|owner response material|accepted_for_material_review_not_proven|needs_more_evidence_not_proven|rejected_unsafe_material_response_not_proven|blocked_missing_owner_response_intake_not_proven|primary_actions_enabled=false|delivery_success=false|safe_to_control=false|not_proven" mobile/web docs/product/mobile_user_flow.md
git diff --check -- mobile/web docs/product/mobile_user_flow.md
```

### Task D: Hardware Boundary Consultation

Owner: `rober-hardware-engineer`

Perform read-only consultation for vendor and PR #5 boundary language. If any implementation copy references WAVE ROVER, UART, 2D LiDAR, ToF, install, wiring, power, calibration, HIL, or PR #5 hardware material, consult `docs/vendor/VENDOR_INDEX.md` first and cite the local source boundary in the worker result.

Required behavior:

- Do not edit hardware config, launch defaults, vendor files, or hardware parameters.
- Confirm `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live GitHub review evidence changes.
- Confirm comment `3269642220` is software-proof reply only, not reviewer resolution.
- Confirm no real WAVE ROVER/UART/HIL or installed/procured/calibrated 2D LiDAR / ToF proof is present on this host.
- Confirm the owner-response review decision must not accept hardware success claims without real source/procurement/install/calibration/HIL-entry evidence.

Acceptance commands:

```bash
test -f docs/vendor/VENDOR_INDEX.md
rg -n "PRRT_kwDOSWB9286CJ3tX|3269642220|hardware_material_pending|WAVE ROVER|UART|HIL|2D LiDAR|ToF" docs/vendor docs/product onboard/src/ros2_trashbot_behavior mobile/web pc-tools/evidence
git diff --check -- docs/vendor docs/product onboard/src/ros2_trashbot_behavior mobile/web pc-tools/evidence
```

### Task E: Product Closeout

Owner: `product-okr-owner`

After Tasks A-D return, collect validation evidence and update closeout docs. Product must verify that implementation owners updated relevant `docs/` files if contracts or product surfaces changed, and must preserve OKR percentages unless real evidence appears and is reviewed.

Required behavior:

- Create/update `tech-done.md`, `side2side_check.md`, and `final.md`.
- Record worker validation and any failed/retried commands.
- Confirm whether `OKR.md` and `docs/process/okr_progress_log.md` require conservative no-lift wording.
- State explicitly that `field_evidence_material_resolution_owner_response_review_decision` is software proof only and not OKR movement if no real reviewed owner response material exists.
- If real owner response material did arrive, state that `accepted_for_material_review_not_proven` is only input to later material review unless review evidence exists.

Acceptance commands:

```bash
test -f sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/tech-done.md && test -f sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/side2side_check.md && test -f sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/final.md
rg -n "field_evidence_material_resolution_owner_response_review_decision|software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate|Objective 5|68%|owner response material|no OKR percentage|not_proven|primary_actions_enabled=false|delivery_success=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX" sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision OKR.md docs/process/okr_progress_log.md <any-docs-touched-by-implementation>
```

## Integration And Dispatch Notes

- This is a 4-owner parallel execution sprint plus Product closeout. Tasks A, B, C, and D have non-overlapping write scopes and should be dispatched in parallel.
- Hardware Task D is consultation-only and should not block software work unless it finds unsafe hardware wording.
- Product Task E starts after implementation owners return.
- Main session must not implement product code or tests directly; implementation and validation belong to the owner agents.

## Validation Plan For This Planning Pass

Run and record:

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_material_resolution_owner_response_review_decision|software_proof_docker_field_evidence_material_resolution_owner_response_review_decision_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|owner response material|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision
```

```bash
git diff --check -- sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision
```

## Implementation Guardrails

- Do not claim real external cloud proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery success, HIL, hardware readiness, owner response reviewed as real proof, or PR #5 resolution.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes.
- Do not expose raw artifacts, raw JSON, credentials, local paths, complete logs, checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, raw vendor data, DB/queue URLs, OSS AK/SK, bearer tokens, tracebacks, or hardware internals in phone-safe copy.
- Do not update OKR percentages unless real material appears, is tied to the same safe `evidence_ref`, and is reviewed.
- If real owner response material arrives during execution, Product must treat `accepted_for_material_review_not_proven` as review input only until a later material review or review-handoff sprint accepts or rejects it with evidence.

## Remaining Risks Before Execution

- The host remains Docker-only, so real external, phone, field, hardware, and HIL validation are not expected.
- This sprint can make owner response material reviewable, but it still cannot create the missing real material.
- If no owner response material arrives after this sprint, the next useful action is CEO/owner material collection or decision escalation, not another local-only status wrapper.
