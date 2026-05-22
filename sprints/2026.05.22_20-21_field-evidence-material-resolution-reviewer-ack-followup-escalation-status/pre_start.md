# Field Evidence Material Resolution Reviewer ACK Followup Escalation Status Pre Start

Run time: 2026-05-22 20:21 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`

## Current Evidence

- Current repo path is `/Users/m4/apps/rober`; this host has Docker only and no real hardware.
- `OKR.md` 4.1 shows Objective 5 at about 68%, Objective 1 at about 81%, and Objective 2/3/4 at about 99%; Objective 5 remains the lowest Objective.
- Latest closeout states that O5 must not keep stacking external-proof claims while real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, and verified terminal result materials are absent.
- PR #5 live review-thread evidence remains mixed: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`.
- Recent sprint chain already completed `field_evidence_material_resolution_reviewer_ack_intake` -> `field_evidence_material_resolution_reviewer_ack_review_decision` -> `field_evidence_material_resolution_reviewer_ack_review_handoff`.
- This sprint continues the explicit follow-through rung after reviewer ACK handoff. It must not claim true hardware, true cloud, true phone/browser, PR #5 resolution, delivery success, or OKR percentage lift.

## User Value And Product North Star

User value: support, field owners, and reviewers need one safe escalation status after reviewer ACK handoff so they can see whether follow-up is still pending, overdue, blocked by missing materials, or ready for a real owner response without reading raw artifacts.

Product north star: ordinary phone users and support staff should see a clear blocked-safe state and next evidence owner. The robot must stay fail-closed until real materials prove control is safe.

## OKR Mapping

- Objective 5 is the lowest at about 68%, but this sprint does not create O5 external proof. It only improves the software-proof material-resolution follow-up chain.
- Objective 1 remains about 81%; `PRRT_kwDOSWB9286CJ3tX` still needs true 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials, WAVE ROVER/UART/HIL logs, operator HIL report, and reviewer resolution.
- Objective 2/3/4 remain about 99%; this sprint does not prove real Nav2/fixed-route, route/elevator field pass, real phone/browser, dropoff/cancel completion, verified terminal result, or delivery success.
- Expected OKR result is no OKR percentage lift.

## Core Grab

Create `field_evidence_material_resolution_reviewer_ack_followup_escalation_status` across three implementation owners:

- Autonomy: PC-only evidence gate that consumes reviewer ACK review-handoff and emits a safe follow-up escalation status artifact/summary.
- Robot: `operator_gateway_diagnostics` safe summary alias for Robot/status consumers.
- Full-Stack: `mobile/web` read-only panel and fixture that show the escalation state while keeping primary actions disabled.

Required invariant: `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## Need To Do

- Define the follow-up escalation status vocabulary: pending, overdue, blocked missing materials, unsafe, accepted for owner response, and no-source fail-closed states.
- Preserve same safe `evidence_ref` from reviewer ACK review-handoff through PC gate, Robot diagnostics, and mobile/web.
- Document the evidence contract and phone-safe UI boundary.
- Keep validation fenced to py_compile, focused unittest, node --check, json.tool, required `rg`, and scoped `git diff --check`.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC-only evidence gate, focused unittest, `pc-tools/README.md`, and `docs/interfaces/evidence_contracts.md`.
- Robot Platform Engineer: diagnostics safe summary alias, focused diagnostics test, and `docs/interfaces/operator_gateway_diagnostics.md`.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel, fixture JSON, focused entrypoint test, and `docs/product/mobile_user_flow.md`.
- Product Manager / OKR Owner: planning now; after implementation only, closeout docs and conservative `OKR.md` / progress log updates.

## Risk And Blockers

- O5 blocker: no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal result materials.
- O1 blocker: no real WAVE ROVER/UART/HIL, no operator HIL report, no real 2D LiDAR / ToF materials, and PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved.
- Field blocker: no real Nav2/fixed-route runtime, task record, route completion signal, elevator door/floor evidence, dropoff/cancel completion, delivery result, route/elevator field pass, or true phone/browser field proof.
- Evidence-substitution risk: future closeout may accidentally treat `software_proof` escalation status as reviewer resolution, real owner response, or delivery readiness.

## Sprint Documents

Create now:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Do not pre-generate:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
