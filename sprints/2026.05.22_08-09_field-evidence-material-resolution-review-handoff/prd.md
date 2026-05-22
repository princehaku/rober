# Field Evidence Material Resolution Review Handoff PRD

Run time: 2026-05-22 08:00 Asia/Shanghai

## User Value And Product North Star

User value: support and field owner need a safe, executable handoff after `field_evidence_material_resolution_review_decision`. The handoff should answer: who owns the next real material collection, which material is still missing, which accepted refs are safe to carry forward, which rejected refs must not be used, and what the next rerun or evidence request should be.

Product north star: the robot can only become useful when real delivery, route, elevator, phone, cloud, and hardware evidence are collected under a consistent safe `evidence_ref`. Until that exists, the product must make gaps visible and owner-actionable without enabling primary controls or describing local metadata as success.

## Product Problem

The previous sprint turned `field_evidence_material_resolution_intake` into a review decision. That decision is useful, but it still leaves execution ambiguous:

- `accepted_for_owner_review_not_proven` tells the owner review may proceed, but not exactly what to run next.
- Missing field/external/terminal materials can still be scattered across O5, O2/O3/O4, and O1 blocker language.
- A phone or diagnostics surface could accidentally over-read accepted review metadata as readiness unless the handoff repeats the fail-closed boundary.

This sprint defines the next product step as `field_evidence_material_resolution_review_handoff`: transform the previous decision into an owner-executable handoff package, not into an OKR lift.

## OKR Mapping

| Objective | Current status from `OKR.md` 4.1 | This sprint's relationship |
| --- | --- | --- |
| Objective 5: cloud relay + OSS/CDN data path | About 68%, still the lowest Objective. Missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, true phone/browser, and verified terminal delivery/dropoff/cancel result. | Primary planning target because it is lowest, but no percentage lift is allowed. The handoff only prepares owner action for real external/terminal/field material. |
| Objective 1: hardware protocol and trusted chassis | About 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` is unresolved / hardware_material_pending and no real 2D LiDAR / ToF or WAVE ROVER HIL materials are present. | Must stay explicitly blocked if the handoff references hardware material. No hardware claim may be made. |
| Objective 2/3/4 | About 99%. Still missing real task record, Nav2/fixed-route runtime, route/elevator field pass, true phone/browser proof, dropoff/cancel completion, and delivery success. | The handoff can request those real materials, but must not claim field pass, phone acceptance, or delivery success. |

Section 6 of `OKR.md` is the controlling priority rule: O5 remains lowest, but without real external material this sprint must not repeat generic O5 metadata depth or raise completion. Therefore this sprint advances the owner handoff needed to obtain real material later.

## KR Breakdown

- KR-A PC handoff gate: define a `field_evidence_material_resolution_review_handoff` CLI/artifact that consumes the previous review decision and emits a safe handoff summary with owner, next action, required real materials, blocked refs, accepted refs, evidence boundary, and fail-closed flags.
- KR-B Robot diagnostics summary: expose only a safe alias such as `robot_diagnostics_field_evidence_material_resolution_review_handoff_summary`, preserving `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- KR-C Mobile/web read-only panel: show the handoff as owner next steps and missing real material, without copy of raw artifacts and without enabling Start Delivery, Confirm Dropoff, or Cancel.
- KR-D Hardware boundary consultation: verify that PR #5 `PRRT_kwDOSWB9286CJ3tX` and real hardware material remain pending; do not change vendor docs or hardware configuration unless real source material appears.
- KR-E Product closeout: after implementation, update sprint `tech-done.md`, `side2side_check.md`, `final.md`, and only update `OKR.md` if real evidence justifies it. The current expectation is no OKR percentage increase.

## Core Product Requirements

The handoff package must include:

- Capability: `field_evidence_material_resolution_review_handoff`.
- Proof boundary: `software_proof_docker_field_evidence_material_resolution_review_handoff_gate`.
- Source and status fields: `source=software_proof`, `not_proven`.
- Control flags: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Input trace: previous decision evidence from `a384c84 Add field evidence resolution review decision` and intake chain from `c629829 Add field evidence material resolution intake`.
- Terminal-result context: previous terminal-result review decision chain from `c1f597b Add verified terminal result review decision gate`.
- PR/hardware blocker: PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending unless live GitHub evidence says otherwise.
- Owner execution fields: owner role, handoff status, safe `evidence_ref`, accepted refs, rejected refs, missing required materials, next required evidence, rerun or collection hint, and safety copy.

The handoff package must not include:

- Raw cloud credentials, local paths, complete internal logs, checksums, raw ROS topic dumps, `/cmd_vel`, UART devices, WAVE ROVER parameters, raw vendor material, or raw GitHub tokens.
- Any claim of real public cloud proof, production DB/queue proof, OSS/CDN live traffic, real phone/browser proof, route/elevator field pass, HIL, verified terminal result, dropoff/cancel completion, delivery success, PR #5 resolution, or OKR percentage lift.

## Priority And Owner Routing

P0:

- Autonomy Engineer owns the PC evidence artifact/gate because the previous decision gate lives in the field evidence tooling chain.
- Robot Platform Engineer owns the diagnostics safe alias and ROS/API contract surface.
- Full-Stack Engineer owns the read-only mobile/web handoff panel and fixture behavior.

P1:

- Hardware Engineer performs read-only consultation for PR #5 and vendor/hardware boundary language only.
- Product Owner performs closeout and OKR boundary review.

## Acceptance Criteria

- The next execution phase produces a handoff summary with `field_evidence_material_resolution_review_handoff` and `software_proof_docker_field_evidence_material_resolution_review_handoff_gate`.
- The handoff is owner-executable but fail-closed: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, and `not_proven`.
- Mobile/web and diagnostics surfaces are read-only and do not enable primary actions.
- The handoff references the real blockers precisely: no real hardware, no real public cloud/4G/OSS/CDN/DB/queue, no real phone/browser, and PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / hardware_material_pending.
- No OKR percentage is raised unless new real external, terminal, field, phone, or HIL material appears in the implementation phase.

## Risks And Non Goals

- Risk: another local metadata wrapper could be mistaken for progress. Mitigation: every artifact and UI copy must say this is software proof only and not delivery success.
- Risk: accepted review metadata could be over-read as terminal result verification. Mitigation: require explicit verified terminal delivery/dropoff/cancel result material before any success wording.
- Risk: hardware PR #5 wording could drift. Mitigation: Hardware consultation must keep `PRRT_kwDOSWB9286CJ3tX` unresolved / hardware_material_pending unless reviewer state changes.
- Non goal: this sprint does not implement real cloud ingress, OSS/CDN live traffic, production DB/queue, production worker/cutover, real phone/browser testing, Nav2/fixed-route field run, WAVE ROVER HIL, or delivery completion.
