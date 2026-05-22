# Field Evidence Material Resolution Reviewer ACK Followup Escalation Status PRD

Run time: 2026-05-22 20:21 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_followup_escalation_status`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`

## Problem

The reviewer ACK review-handoff rung can explain what was handed off after review. The next product gap is follow-up status: support and field owners need a single sanitized status that says whether the reviewer-ACK handoff has a pending owner response, is overdue, remains blocked by missing materials, contains unsafe/rejected claims, or is accepted for a real owner-response intake.

Without this rung, the team can see that handoff happened but cannot reliably distinguish "waiting", "escalate", "blocked", and "ready for next real-material response" without reading raw artifacts or overstating progress.

## User Value And Product North Star

User value: the support/operator view can tell a human what to do next after reviewer ACK handoff: wait for a field owner, escalate missing materials, reject unsafe material claims, or prepare owner-response intake. The phone surface remains safe and does not expose raw engineering details.

Product north star: a normal phone user should never need SSH, ROS2, serial tools, GitHub thread context, or raw JSON to know whether the robot is safe to control. The product should turn evidence gaps into plain blocked-safe next actions while preserving the proof boundary.

## OKR Mapping

- Objective 5: lowest at about 68%. This sprint supports the evidence-governance path while true O5 proof is absent; it is not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal result proof.
- Objective 1: about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not imply real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL, operator HIL report, or reviewer resolution.
- Objective 2/3/4: about 99%. This sprint must not imply real route/elevator field pass, Nav2/fixed-route runtime, real phone/browser behavior, dropoff/cancel completion, verified terminal result, or delivery success.
- Expected outcome: no OKR percentage lift unless real external, hardware, or field materials arrive before closeout.

## KR Breakdown

- KR-A PC evidence gate: produce `field_evidence_material_resolution_reviewer_ack_followup_escalation_status` artifact and summary from reviewer ACK review-handoff input, with same safe `evidence_ref`, escalation due status, owner routing, missing evidence, and fail-closed flags.
- KR-B Robot diagnostics: expose `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_summary` as a phone-safe alias with no raw artifacts or control semantics.
- KR-C mobile/web panel: render a read-only follow-up escalation status panel and fixture while Start Delivery, Confirm Dropoff, and Cancel stay disabled.
- KR-D docs sync: update evidence contracts, diagnostics contract, and mobile user flow docs so the status vocabulary and non-claim boundary are explicit.
- KR-E Product closeout: after implementation only, write `tech-done.md`, `side2side_check.md`, `final.md`, and update `OKR.md` / progress log conservatively.

## Core Grab

Turn reviewer ACK handoff into an actionable follow-up escalation status:

- Is a real owner response still pending?
- Is the response overdue and ready to escalate?
- Which evidence is missing or unsafe?
- Which owner owns the next real-material response?
- Why do primary actions remain disabled?

All outputs must preserve:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Scope

In scope:

- PC-only CLI gate and focused unittest.
- Robot diagnostics safe alias and focused diagnostics test.
- Mobile/web read-only panel, fixture JSON, and focused entrypoint test.
- `pc-tools/README.md`, `docs/interfaces/evidence_contracts.md`, `docs/interfaces/operator_gateway_diagnostics.md`, and `docs/product/mobile_user_flow.md` updates during implementation.

Out of scope:

- Resolving PR #5 thread `PRRT_kwDOSWB9286CJ3tX`.
- Raising OKR percentages from Docker-only proof.
- Adding robot control endpoints, ACK mutation, cursor fetch, diagnostics fetch, replay, resubmit, copy/export controls, or material upload flows.
- Claiming real cloud, true phone/browser, WAVE ROVER/UART/HIL, route/elevator field pass, verified terminal result, dropoff/cancel completion, or delivery success.

## Priority And Acceptance

P0:

- PC gate exists, fails closed on unsafe/missing/mismatched input, and emits a sanitized summary with escalation status.
- Robot diagnostics exposes only the safe alias and keeps `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Mobile/web renders the panel read-only and keeps primary actions disabled.

P1:

- Docs explain the exact schemas, fields, status vocabulary, and non-claims.
- Focused tests cover accepted, pending/overdue, missing source, unsafe claim, and evidence-ref mismatch cases.

Acceptance boundary:

- This sprint can pass only as `software_proof_docker_field_evidence_material_resolution_reviewer_ack_followup_escalation_status_gate`.
- It remains not true phone/browser proof, not true cloud proof, not HIL, not PR #5 resolution, and not delivery success.

## Responsible Engineers

- Autonomy Algorithm Engineer owns PC gate and evidence contract docs.
- Robot Platform Engineer owns diagnostics safe alias and diagnostics docs.
- User Touchpoint Full-Stack Engineer owns mobile/web panel, fixture, and mobile flow docs.
- Product Manager / OKR Owner owns closeout after implementation evidence returns.

## Risks And Evidence Gaps

- Real external O5 materials remain absent, so Objective 5 must stay about 68%.
- Real hardware/HIL materials remain absent, so Objective 1 must stay about 81% and `PRRT_kwDOSWB9286CJ3tX` must remain unresolved unless GitHub live state changes.
- Real route/elevator/mobile field materials remain absent, so Objective 2/3/4 should not receive a completion lift from this sprint.
- The main product risk is overclaiming escalation status as owner acceptance or delivery readiness; all docs and UI must keep fail-closed wording.
