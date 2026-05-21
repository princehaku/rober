# Field Evidence Real Material Followup Escalation Status PRD

Run time: 2026-05-21 18:05 CST

## User Value

Field owners need one place to see why the current route/elevator/phone/hardware evidence is still blocked, what real material is missing, who owns the next action, and what SLA state applies. Without that escalation status, the team keeps producing local software-proof wrappers while the field owner still does not know what evidence to capture next.

The user-facing value is safer expectation management: phone and diagnostics surfaces can explain "not proven yet" in plain language while keeping Start Delivery, Confirm Dropoff, and Cancel disabled. This protects ordinary users from mistaking a software-proof reply, ACK, handoff, or review decision for real robot delivery success.

## Product North Star

The north star is still a phone-first trash delivery robot that can be trusted by non-technical users. Trust here means every visible claim has evidence: real route/elevator field pass, true phone/browser proof, real hardware material, HIL, or external cloud proof. This sprint only improves blocked-evidence escalation; it must not inflate product completion.

## Problem Statement

The latest sprint `2026.05.21_17-18_field-evidence-real-material-response-review-handoff` completed a handoff, but its final says the next step must not be another generic local wrapper. If real field materials are not available, the product needs a field-owner escalation status that records owner/SLA/next action/missing evidence/blocked reason in a safe, phone-readable way.

Current evidence constraints:

- Objective 5 is about 68% and remains lowest, but has no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser evidence.
- Objective 1 is about 81% and PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending. Comment `3269642220` is a software-proof reply publication only.
- Existing route/elevator/phone work remains `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.

## OKR Mapping

- Objective 5: acknowledged as lowest, but not targeted for percentage movement because real external proof is absent and repeated local O5 metadata is disallowed.
- Objective 1: tracked as the next low objective with unresolved PR #5 material evidence, but not advanced without real hardware materials and reviewer resolution.
- Objective 2: supported by making route/elevator missing field evidence actionable for field owners.
- Objective 3: supported by explicitly requiring real task record, Nav2/fixed-route runtime log, route completion signal, and same safe `evidence_ref`.
- Objective 4: supported by safe phone copy that explains blocked status without enabling primary actions or claiming true device proof.

## KR Breakdown

| KR | Product Requirement | Evidence Boundary |
| --- | --- | --- |
| KR1 | Escalation status lists owner, SLA/due status, next action, missing evidence, and blocked reason. | `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate` |
| KR2 | Route/elevator requirements include real task record, runtime log, completion signal, door state, floor confirmation, human assistance note, dropoff/cancel completion, delivery result, and same safe `evidence_ref`. | `not_proven` until real field materials arrive |
| KR3 | PR #5 hardware status keeps `PRRT_kwDOSWB9286CJ3tX` and `3269642220` as material-pending software-proof evidence only. | no HIL, no WAVE ROVER/UART proof, no reviewer resolution |
| KR4 | Phone copy is read-only and fail-closed: `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`. | no raw artifacts, no control enablement |
| KR5 | Product closeout preserves conservative OKR language and writes sprint evidence without claiming completion. | OKR percentage can only move with real materials |

## Scope

In scope:

- Add a software-proof escalation status capability named `field_evidence_real_material_followup_escalation_status`.
- Convert 17-18 handoff concepts into owner/SLA/missing evidence/blocked reason/next action/rerun guidance.
- Keep diagnostics/mobile summaries sanitized and read-only.
- Keep Hardware involvement read-only unless real materials are supplied.
- Prepare Product closeout docs and conservative OKR update instructions.

Out of scope:

- Real field run, real elevator proof, real Nav2/fixed-route proof, real dropoff/cancel completion, delivery result, or delivery success.
- Real iPhone/Android device validation, production app proof, PWA prompt/userChoice proof, or true phone/browser proof.
- O5 external proof: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover.
- O1 hardware proof: real 2D LiDAR / ToF procurement, installation, wiring, power, calibration, HIL-entry, WAVE ROVER/UART/HIL logs, or PR #5 thread resolution.

## Priority

P0:

- Preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.
- Include PR/review evidence: `PRRT_kwDOSWB9286CJ3tX`, `3269642220`, Objective 5, Objective 1, and the reason O5 metadata is not repeated.
- Produce a concrete owner/SLA/next-action escalation status.

P1:

- Make field owner next evidence explicit by material group.
- Keep phone copy Chinese-first, plain, and safe for non-technical users.
- Ensure worker file ranges and validation commands are clear enough for parallel execution.

P2:

- Product closeout should update `OKR.md` only after implementation evidence lands, and should keep percentages conservative if no real materials arrive.

## Acceptance Criteria

- The output status uses capability `field_evidence_real_material_followup_escalation_status`.
- The evidence boundary string `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate` appears in sprint planning and later worker outputs.
- The sprint explicitly references Objective 5, Objective 1, `PRRT_kwDOSWB9286CJ3tX`, and `3269642220`.
- The sprint explains why this is escalation status rather than another generic wrapper.
- The sprint keeps `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.
- The downstream implementation plan starts 4 parallel workers by default: Autonomy, Robot, Full-Stack, and Hardware read-only consultation.
- Product closeout remains a separate step after worker evidence is available.

## Safe Phone Copy Requirements

The user-facing status should say, in Chinese-first wording, that real field materials are still missing and primary actions remain disabled. It may summarize owner, due status, blocked reason, and next required evidence.

It must not say or imply:

- route/elevator field pass;
- true phone/browser proof;
- delivery success;
- dropoff or cancel completion;
- HIL or WAVE ROVER/UART proof;
- Objective 5 external cloud proof;
- PR #5 reviewer resolution.

It must not expose raw ROS topics, `/cmd_vel`, serial/UART paths, baudrate values, WAVE ROVER parameters, credentials, DB/queue URLs, OSS AK/SK, local paths, tracebacks, checksums, complete artifacts, or raw review artifacts.

## Responsibility

- Product Manager / OKR Owner: PRD, OKR mapping, closeout, `OKR.md` and progress-log update only after evidence lands.
- Autonomy Algorithm Engineer: route/elevator material taxonomy and rerun/backfill escalation semantics.
- Robot Platform Engineer: diagnostics artifact, summary schema, CLI/gate, and Robot validation.
- User Touchpoint Full-Stack Engineer: phone-safe read-only panel and fixture/browser/unit validation.
- Hardware Infra Engineer: read-only vendor/source consultation and PR #5 material-boundary statement.

## Risks And Blockers

- If no field owner provides materials, the sprint can only move the workflow to escalation status, not completion.
- If PR #5 remains unresolved, O1 cannot advance from this sprint.
- If O5 real external materials remain absent, O5 must stay about 68% and must not receive another metadata-only progress bump.
- If phone copy is too optimistic, users may mistake blocked software proof for safe control or delivery success.
