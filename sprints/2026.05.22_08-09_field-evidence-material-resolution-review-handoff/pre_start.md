# Field Evidence Material Resolution Review Handoff Pre Start

Run time: 2026-05-22 08:00 Asia/Shanghai

## Sprint Declaration

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/`
- Capability name: `field_evidence_material_resolution_review_handoff`
- Evidence boundary: `software_proof_docker_field_evidence_material_resolution_review_handoff_gate`
- Product owner: `product-okr-owner`
- Implementation owners for the next execution phase: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- Hardware consultation owner: `hardware-engineer`

## Evidence Read Before Start

- `OKR.md` 4.1 says Objective 5 is still the lowest Objective at about 68%. It also states the previous `field_evidence_material_resolution_review_decision` work is only local metadata proof and keeps `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- `OKR.md` section 6 says O5 should only move with real external material such as OSS/CDN live traffic, public HTTPS/TLS, 4G/SIM, production DB/queue, production worker/cutover, true phone/browser evidence, or verified terminal delivery/dropoff/cancel result. If those are unavailable, do not repeat generic local O5 metadata depth.
- `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/final.md` says `accepted_for_owner_review_not_proven` is only a sanitized resolution intake ready for owner review. It is not delivery success, HIL, field pass, real phone/browser proof, real public cloud proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, dropoff/cancel completion, verified terminal result, or OKR lift.
- `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/tech-done.md` records the previous gate as `software_proof_docker_field_evidence_material_resolution_review_decision_gate` and keeps Objective 5 at about 68%, Objective 1 at about 81%, and Objectives 2/3/4 at about 99%.
- Recent git log confirms the immediate chain: `a384c84 Add field evidence resolution review decision`, `c629829 Add field evidence material resolution intake`, and `c1f597b Add verified terminal result review decision gate`.

## Why This Sprint Exists

The previous sprint produced a review decision. That decision is still not actionable enough for the field owner unless it is converted into a handoff package with owner, required materials, safe rerun hints, blocked categories, and a copy-safe next step.

This sprint therefore creates the planning lane for `field_evidence_material_resolution_review_handoff`: the next implementation must package the previous `field_evidence_material_resolution_review_decision` result for owner execution while preserving the same conservative evidence boundary.

## Repeated Blocker Check

The repeated blocker is unchanged:

- No real hardware or HIL evidence.
- No real public cloud, 4G/SIM, OSS/CDN, production DB/queue, production worker/cutover, or terminal-result material.
- No real phone/browser or production app evidence.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware_material_pending.

This sprint is allowed only because it does not claim to resolve those blockers and does not raise OKR percentages. It changes the next-step handoff shape so a field owner can collect real material later.

## Scope Boundary

In this planning pass, only these files may be created:

- `sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/pre_start.md`
- `sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/prd.md`
- `sprints/2026.05.22_08-09_field-evidence-material-resolution-review-handoff/tech-plan.md`

No `OKR.md`, product docs, source code, tests, mobile fixtures, Robot diagnostics, hardware configuration, or vendor files are changed in this pass.

## Start Criteria

- The next execution phase must consume the previous review-decision contract, not invent a success state.
- The next execution phase must keep `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- The handoff package must be owner-executable but read-only: no robot command, no ACK/cursor mutation, no Start Delivery, no Confirm Dropoff, no Cancel, and no hidden remote control.
- The handoff must explicitly say what real material is missing before any OKR lift is possible.

## Exit Criteria For Planning

- `prd.md` defines user value, OKR mapping, KR breakdown, priority, owner routing, and acceptance.
- `tech-plan.md` defines file ranges for the next implementation phase, interface boundaries, verification commands, risks, and the required `OKR 最低优先级核对`.
- Planning validation passes with the required file-existence check, required `rg` scan, and scoped `git diff --check`.
