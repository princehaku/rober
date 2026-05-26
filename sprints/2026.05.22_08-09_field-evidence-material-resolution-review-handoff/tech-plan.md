# Field Evidence Material Resolution Review Handoff Tech Plan

Run time: 2026-05-22 08:00 Asia/Shanghai

## Goal

Implement the next software-proof rung `field_evidence_material_resolution_review_handoff` after `field_evidence_material_resolution_review_decision`. The implementation must turn the previous review decision into an owner-executable handoff package while preserving `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and no OKR percentage lift.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1: Objective 5, about 68%.
2. This sprint targets Objective 5's blocker resolution chain because it is still the lowest Objective.
3. This sprint must not raise Objective 5 because `OKR.md` section 6 and the previous `final.md` require real external, terminal, field, phone, or HIL material before any completion lift. Current blockers remain: no real public HTTPS/TLS, no 4G/SIM, no OSS/CDN live traffic, no production DB/queue connectivity, no production worker/cutover, no true phone/browser evidence, no verified terminal delivery/dropoff/cancel result, no real hardware/HIL, and PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending.

## Evidence Inputs

- `OKR.md` 4.1 and section 6.
- Previous sprint final: `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/final.md`.
- Previous sprint done file: `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/tech-done.md`.
- Git chain:
  - `a384c84 Add field evidence resolution review decision`
  - `c629829 Add field evidence material resolution intake`
  - `c1f597b Add verified terminal result review decision gate`
- Repeated blockers: no real hardware, no real public cloud/4G/OSS/CDN/DB/queue, no real phone/browser, and PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / hardware_material_pending.

## File Structure For Next Execution

Autonomy Engineer:

- Modify/create PC evidence gate files under `pc-tools/evidence/`.
- Update the relevant evidence contract docs only if implementation changes contract shape.
- Do not touch Robot diagnostics or mobile/web files.

Robot Platform Engineer:

- Modify diagnostics safe alias code and tests under `onboard/src/ros2_trashbot_behavior/`.
- Update `docs/interfaces/` only for the safe summary contract.
- Do not touch PC evidence gate implementation or mobile/web files.

Full-Stack Engineer:

- Modify mobile/web read-only panel, fixture, and targeted tests under `mobile/web/`.
- Update `docs/product/mobile_user_flow.md` only for the read-only handoff panel boundary.
- Do not touch Robot diagnostics internals or PC evidence gate implementation.

Hardware Engineer:

- Read `docs/vendor/VENDOR_INDEX.md` and local vendor references only if the next implementation mentions WAVE ROVER, UART, 2D LiDAR, ToF, installation, wiring, power, calibration, or HIL.
- Keep the work read-only unless real hardware material appears and the sprint scope is explicitly expanded.

Product Owner:

- After implementation, create/update `tech-done.md`, `side2side_check.md`, and `final.md`.
- Do not update `OKR.md` unless real material changes the evidence state.

## Interface Contract

The next implementation should emit a safe handoff summary with these required semantics:

- `capability=field_evidence_material_resolution_review_handoff`
- `proof_boundary=software_proof_docker_field_evidence_material_resolution_review_handoff_gate`
- `source=software_proof`
- `not_proven=true`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- safe `evidence_ref`
- previous review decision reference
- accepted material refs, rejected material refs, and missing required materials
- owner handoff role and owner next action
- next required real evidence
- blocked categories for external cloud, terminal result, phone/browser, field route/elevator, hardware/HIL, and PR #5

The contract must fail closed when the previous review decision is missing, unsafe, success-claiming, or not tied to a safe `evidence_ref`.

## Owner Tasks

### Task A: PC Evidence Handoff Gate

Owner: `autonomy-engineer`

Build the `field_evidence_material_resolution_review_handoff` artifact/gate by consuming the previous review-decision output. The gate should create a sanitized owner handoff and reject or block any success claim, unsafe material ref, missing evidence ref, raw artifact exposure, or unsupported terminal/cloud/phone/HIL claim.

Acceptance commands should include targeted `py_compile`, targeted unittest for the new gate, CLI `--help`, required `rg`, and scoped `git diff --check`.

### Task B: Robot Diagnostics Safe Alias

Owner: `robot-software-engineer`

Expose `robot_diagnostics_field_evidence_material_resolution_review_handoff_summary` as a read-only safe alias. It must not enable commands, must not convert handoff status to readiness, and must preserve all fail-closed booleans.

Acceptance commands should include targeted `py_compile`, targeted diagnostics unittest, required `rg`, and scoped `git diff --check`.

### Task C: Mobile/Web Read-Only Handoff Panel

Owner: `full-stack-software-engineer`

Render the handoff summary as a first-screen or existing evidence-chain read-only panel. The panel should show owner, safe evidence ref, next required evidence, missing categories, blocked refs, evidence boundary, and fail-closed status. Start Delivery, Confirm Dropoff, and Cancel must remain disabled.

Acceptance commands should include `node --check mobile/web/app.js`, fixture JSON parse if a fixture is added, targeted `mobile.web.test_mobile_web_entrypoint`, required `rg`, and scoped `git diff --check`.

### Task D: Hardware Boundary Consultation

Owner: `robot-hardware-engineer`

Confirm whether the handoff references hardware or PR #5 material. If yes, read `docs/vendor/VENDOR_INDEX.md` and the pointed local vendor files before giving boundary text. The expected result is no hardware configuration change and no claim that PR #5 `PRRT_kwDOSWB9286CJ3tX` is resolved.

Acceptance commands should include `test -f docs/vendor/VENDOR_INDEX.md`, required `rg`, and scoped `git diff --check` over touched docs if any.

### Task E: Product Closeout

Owner: `product-okr-owner`

Collect worker evidence, update sprint closeout docs, and preserve OKR percentages unless real evidence arrives. The final wording must say whether docs under `docs/` were updated by implementation owners and whether any risks remain.

## Validation Plan For This Planning Pass

Run and record:

```bash
test -f sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/pre_start.md && test -f sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/prd.md && test -f sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|field_evidence_material_resolution_review_handoff|software_proof_docker_field_evidence_material_resolution_review_handoff_gate|PRRT_kwDOSWB9286CJ3tX|a384c84|c629829" sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff
```

```bash
git diff --check -- sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff
```

## Implementation Guardrails

- Do not claim real external cloud proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser proof, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery success, HIL, or PR #5 resolution.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch side effects, or robot command routes from the handoff.
- Do not expose raw artifacts, raw JSON, credentials, local paths, complete logs, checksums, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER parameters, or hardware vendor internals in phone-safe copy.
- Do not update OKR percentages in implementation unless real material appears and is recorded with evidence.

## Remaining Risks Before Execution

- The host still appears to be a Docker/local proof environment, so real hardware/HIL/cloud/phone validation is not expected.
- The handoff can improve owner actionability, but it will still be a local software-proof artifact.
- Repeating this ladder again without real owner materials would become another blocker wrapper; the next sprint after handoff should require actual owner response or escalate for real materials.
