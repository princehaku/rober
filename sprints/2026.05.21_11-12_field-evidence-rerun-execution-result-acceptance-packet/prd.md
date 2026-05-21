# Field Evidence Rerun Execution Result Acceptance Packet PRD

## Product Summary

Create the next field-evidence ladder rung: `field_evidence_rerun_execution_result_acceptance_packet`.

The product need is not another internal review state. The field owner now needs one packet shape that says whether a route/elevator execution result is acceptance-reviewable, which real materials are missing, and why the packet still remains `software_proof/not_proven` until those materials arrive.

## User Value And North Star

User value:

- Field owner gets a single checklist for acceptance readiness instead of reading scattered handoff/result/review artifacts.
- Support can tell a normal phone user why Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Product can avoid inflating OKR progress from local software proof.

Product north star:

- A phone-first trash delivery robot must be accepted by coherent evidence: route runtime, elevator evidence, task record, completion signal, phone/browser proof, and delivery result must reconcile under the same safe `evidence_ref`.

## OKR Mapping

| Objective | Mapping | Expected Progress Effect |
| --- | --- | --- |
| Objective 5 | Numeric lowest at about 68%, but blocked without real public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, or true phone/browser proof. | No percentage movement. This sprint is not O5 external proof. |
| Objective 1 | Next-low at about 81%, but PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / material pending; reply comment `3269642220` is not reviewer resolution. | No percentage movement. This sprint is not hardware/HIL proof. |
| Objective 2 | Requires real delivery task closure, dropoff/cancel completion, delivery result, and elevator-assisted delivery evidence. | Prepares acceptance packet; no real delivery claim. |
| Objective 3 | Requires real Nav2/fixed-route runtime and route completion signal. | Prepares same-evidence-ref reconciliation; no real route pass claim. |
| Objective 4 | Requires true phone/browser evidence and phone-safe user clarity. | Adds read-only acceptance visibility; no true phone/browser claim. |

## KR Decomposition

- KR-A: Acceptance packet schema captures `field_evidence_rerun_execution_result_acceptance_packet`, same safe `evidence_ref`, packet verdict, missing material categories, accepted material categories, blocked categories, and owner next steps.
- KR-B: Required real materials are explicit: task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence.
- KR-C: PC/Autonomy gate refuses unsafe or mismatched packets and keeps `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`.
- KR-D: Robot diagnostics exposes only a safe summary / alias and does not expose raw artifacts, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER material, credentials, tracebacks, complete artifacts, checksums, or success/control claims.
- KR-E: Mobile/web renders a read-only acceptance packet panel and keeps Start Delivery, Confirm Dropoff, and Cancel disabled through `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- KR-F: Product closeout preserves Objective 5 and Objective 1 percentages unless real external or hardware materials appear.

## Core Product Lever

The core lever is acceptance readiness, not proof completion.

The sprint should create a packet that can say:

- `ready_for_field_owner_acceptance_review_not_proven` only when all required categories are present, safe, same-`evidence_ref`, and free of success/control claims.
- `needs_material_backfill` when required field materials are missing.
- `blocked_evidence_ref_mismatch` when materials do not share the same safe `evidence_ref`.
- `blocked_unsafe_material` when raw control, secrets, low-level hardware, or success/control claims leak into the packet.
- `rejected_success_claim` when any local packet claims `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true` without real acceptance evidence.

## What Needs To Be Done

1. Autonomy Algorithm Engineer creates the PC/evidence acceptance-packet gate and focused tests.
2. Robot Platform Engineer adds diagnostics safe summary / alias consumption for the acceptance packet and focused tests.
3. User Touchpoint Full-Stack Engineer adds the mobile/web read-only panel, fixture, and focused tests.
4. Product Manager / OKR Owner later closes `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` only after Engineer evidence is present.

## Priority And Acceptance Criteria

P0 acceptance criteria:

- All outputs include `field_evidence_rerun_execution_result_acceptance_packet`.
- All outputs include `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`.
- All outputs preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Required materials include task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence.
- Same safe `evidence_ref` is required across the packet.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` and comment `3269642220` remain correctly described as unresolved/material pending and software-proof reply only.

P1 acceptance criteria:

- Mobile copy is Chinese-first and support-oriented.
- Packet status distinguishes ready-for-review from accepted field pass.
- Docs under `docs/` are updated during implementation to reflect new contracts and user flow surfaces.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC evidence gate, schema, CLI, tests, evidence contract docs.
- Robot Platform Engineer: Robot diagnostics safe summary, redaction, tests, runtime contract docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, parser/fallback behavior, tests, mobile user flow docs.
- Product Manager / OKR Owner: sprint closeout, OKR conservatism, progress log, acceptance narrative after Engineer work returns.

## Risks, Blockers, And Evidence Chain

- Risk: The acceptance packet is misread as a real field pass. Mitigation: fixed `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and non-claim language.
- Risk: Field materials arrive with different `evidence_ref` values. Mitigation: default verdict `blocked_evidence_ref_mismatch`.
- Risk: Raw logs or unsafe details leak into Robot/mobile summaries. Mitigation: whitelist-only summaries and tests for forbidden strings.
- Risk: O5/O1 completion is inflated. Mitigation: `tech-plan.md` and closeout must state Objective 5 and Objective 1 do not move without real external/hardware evidence.
- Blocker: Real route/elevator/mobile field materials are still absent. The sprint can create acceptance readiness only.

## Sprint Documents To Create Or Update

Created in this planning pass:

- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/pre_start.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/prd.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-plan.md`

To update during execution / closeout:

- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/tech-done.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/side2side_check.md`
- `sprints/2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- relevant `docs/interfaces/` and `docs/product/` files touched by Engineer implementation
