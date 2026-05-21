# Field Evidence Rerun Execution Result Acceptance Packet Pre-Start

## Sprint Declaration

- sprint_type: epic
- sprint: `2026.05.21_11-12_field-evidence-rerun-execution-result-acceptance-packet`
- capability: `field_evidence_rerun_execution_result_acceptance_packet`
- evidence_boundary: `software_proof_docker_field_evidence_rerun_execution_result_acceptance_packet_gate`
- planning_owner: Product Manager / OKR Owner
- target_delivery_owner: Autonomy Algorithm Engineer, Robot Platform Engineer, User Touchpoint Full-Stack Engineer
- fixed_safe_states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## Why This Sprint Exists

Objective 5 is still the lowest numeric Objective in `OKR.md` 4.1 at about 68%, but the 2026.05.21 10-11 closeout says not to add another local O5 wrapper unless real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser evidence appears. No such material is available for this planning pass.

Objective 1 is next lowest at about 81%, but PR #5 still has unresolved hardware-material evidence. Live PR review state remains:

- `PRRT_kwDOSWB9286CJ3tQ`: resolved
- `PRRT_kwDOSWB9286CJ3tU`: resolved
- `PRRT_kwDOSWB9286CJ3tX`: unresolved / `is_resolved=false` / material pending
- comment `3269642220`: published software-proof reply only; it is not reviewer resolution

The recent O2/O3/O4 chain has already moved through:

- `field_evidence_rerun_execution_result_intake`
- `field_evidence_rerun_execution_result_review_decision`
- `field_evidence_rerun_execution_result_review_handoff`

This sprint continues that ladder by converting the review handoff into a concrete field-owner acceptance packet checklist. It must ask for real same-safe-`evidence_ref` execution materials while staying conservative: the packet may be ready for field-owner acceptance review, but the repo still has no real field pass.

## User Value And Product North Star

User value: a field owner or support operator can see exactly which real materials are needed before anyone can accept a route/elevator execution result: task record, Nav2/fixed-route runtime log, route completion signal, elevator evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence under the same safe `evidence_ref`.

Product north star: the robot should become a phone-first trash delivery product that can be verified by evidence, not by optimistic labels. This sprint improves evidence acceptance readiness for the delivery path, but it does not prove real delivery or raise OKR percentages by itself.

## Scope Boundary

In scope for the implementation sprint:

- Define `field_evidence_rerun_execution_result_acceptance_packet`.
- Require one same safe `evidence_ref` across all real field materials.
- Add PC/Autonomy acceptance-packet gate or equivalent evidence tool.
- Add Robot diagnostics safe summary / alias for the acceptance packet.
- Add mobile/web read-only acceptance packet panel and fixture.
- Keep Start Delivery, Confirm Dropoff, Cancel, ACK/cursor, and robot-command paths unchanged and fail closed.
- Update related `docs/` product/interface material during implementation because repo policy requires docs to reflect current behavior.

Out of scope:

- No O5 wrapper, cloud deployment, public ingress/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, or production app claim.
- No WAVE ROVER/UART/HIL claim and no PR #5 thread resolution claim.
- No true phone/browser pass unless real device/browser material is supplied and explicitly attached to the same safe `evidence_ref`.
- No `delivery_success=true`, no route/elevator field pass, no dropoff success, and no cancel completion claim from local software proof alone.

## Blocker Reuse Check

The prior two closeouts do not justify another O5 local wrapper. The current blocker has moved from cloud wrapper depth to missing real route/elevator/mobile field materials. This sprint therefore pivots to Objective 2/3/4 acceptance-packet readiness while explicitly preserving Objective 5 and Objective 1 blocker language.

If the execution phase discovers that no implementation file can move without real site materials, the sprint must stop as blocked and record the missing field materials, rather than invent another success wrapper.

## Initial Evidence Needed For Acceptance

The future acceptance packet must require all of these under the same safe `evidence_ref`:

- real task record
- real Nav2/fixed-route runtime log
- route completion signal
- elevator door state evidence
- target floor confirmation
- human assistance note
- dropoff/cancel completion
- delivery result
- true phone/browser evidence
- diagnostics/mobile safe summary

All acceptance packet outputs must preserve `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` until the actual field materials are supplied and separately reviewed.
