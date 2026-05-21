# Field Evidence Real Material Followup Escalation Status Pre-Start

Run time: 2026-05-21 18:05 CST

## Sprint Type

- sprint_type: epic
- capability: `field_evidence_real_material_followup_escalation_status`
- evidence boundary: `software_proof_docker_field_evidence_real_material_followup_escalation_status_gate`
- expected proof state: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- sprint folder: `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/`

## Product North Star

The product north star remains a phone-first, low-cost ROS2 trash delivery robot that ordinary users can trust because every delivery, route, elevator, hardware, phone, and cloud claim has a clear evidence boundary.

This sprint does not attempt to prove field success. Its value is to turn the prior 17-18 handoff into an escalation status that tells the field owner exactly what is missing, who owns the next action, what SLA state applies, why the claim remains blocked, and what phone-safe copy must stay disabled.

## Evidence Read Before Start

- `AGENTS.md`: Epic sprint must keep sprint records real, preserve hardware/source boundaries, and avoid repeated blocker consumption.
- `OKR.md` 4.1, updated 2026-05-21 17:58 CST: Objective 5 is the lowest at about 68%, but it still lacks real external cloud, 4G, OSS/CDN, DB/queue, production worker, and true phone/browser evidence. The next direction says not to repeat local O5 metadata depth without real external materials.
- `OKR.md` 4.1: Objective 1 is about 81%, with PR #5 thread `PRRT_kwDOSWB9286CJ3tX` still unresolved / material pending. Comment `3269642220` is only software-proof reply publication and must not be counted as reviewer resolution, HIL, or hardware proof.
- GitHub PR #5 live review-thread check on 2026-05-21 18:05 CST: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved; `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false`, `is_outdated=false`, `resolved_by=null`.
- `sprints/2026.05.21_17-18_field-evidence-real-material-response-review-handoff/final.md`: next product direction says the next sprint should not add another generic local wrapper; if no field materials arrive, escalate for field-owner evidence or pivot.
- `docs/product/mobile_user_flow.md`: phone UI must keep Start Delivery, Confirm Dropoff, and Cancel disabled when proof is blocked or missing; safe copy must not expose raw ROS, serial/UART, credentials, WAVE ROVER, DB/queue, OSS, local paths, checksums, or success claims.
- `docs/process/iteration_velocity.md`: Epic sprint requires complete planning, explicit OKR lowest-priority check, and repeated blocker avoidance.

## Repeated Blocker Scan

Recent field-evidence and real-material work already consumed the same missing-real-material blocker through readiness, intake, template, review decision, and 17-18 response review handoff surfaces. The latest 17-18 final explicitly says another generic wrapper would be the wrong next action.

This sprint avoids the blocker red line by changing the output from "another local wrapper" to `field_evidence_real_material_followup_escalation_status`: a concrete field-owner escalation state with owner, SLA, next action, missing evidence, blocked reason, and safe phone copy. It remains software proof and does not pretend that missing real materials have arrived.

## OKR Mapping

- Objective 5: stays lowest at about 68%. This sprint does not target O5 percentage movement because real external cloud / 4G / OSS/CDN / DB/queue / phone evidence is absent.
- Objective 1: stays about 81%. This sprint references the unresolved PR #5 hardware-material thread `PRRT_kwDOSWB9286CJ3tX`, but cannot close it because comment `3269642220` is not a real 2D LiDAR / ToF material, reviewer resolution, WAVE ROVER/UART proof, or HIL pass.
- Objectives 2/3/4: the actionable focus is field-owner evidence escalation for route/elevator/phone evidence gaps. This supports execution readiness only and must not be written as route/elevator field pass, true phone/browser proof, delivery result, or delivery success.

## Core Handle For This Sprint

Define and implement a software-proof escalation status layer that converts the 17-18 handoff output into:

- field owner and escalation owner;
- SLA status and due status;
- next required field-owner action;
- missing real evidence list;
- blocked reason;
- rerun/backfill guidance;
- safe phone copy;
- conservative flags: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`.

## KR Breakdown

- KR1: Robot produces a sanitized diagnostics summary for `field_evidence_real_material_followup_escalation_status` without exposing raw artifacts or control details.
- KR2: Full-Stack renders the status as a read-only, phone-safe panel that keeps primary controls disabled.
- KR3: Autonomy defines route/elevator field-material groups, missing evidence, and rerun/backfill escalation semantics without claiming field pass.
- KR4: Hardware performs read-only source consultation for PR #5 / hardware-material pending status and confirms no real HIL or sensor material proof is present unless actual materials are supplied.
- KR5: Product closes the Epic by updating `tech-done.md`, `side2side_check.md`, `final.md`, and, if implementation lands, `OKR.md` plus `docs/process/okr_progress_log.md` with unchanged or conservative progress boundaries.

## Owners

- Product Manager / OKR Owner: scope, PRD, OKR boundary, closeout evidence, sprint records.
- Autonomy Algorithm Engineer: route/elevator missing-real-material taxonomy and escalation semantics.
- Robot Platform Engineer: sanitized diagnostics summary and gate validation.
- User Touchpoint Full-Stack Engineer: phone-safe read-only status copy and disabled controls.
- Hardware Infra Engineer: read-only vendor/source and PR #5 material-boundary consultation.

## Risks And Evidence Gaps

- Real field materials may still be absent, so this sprint can only produce escalation status and software proof.
- `PRRT_kwDOSWB9286CJ3tX` may remain unresolved until real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry evidence exists.
- O5 remains blocked without public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser evidence.
- Phone copy must remain safe and blocked: no raw ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER parameters, credentials, DB/queue URLs, raw artifacts, complete logs, checksums, tracebacks, or success phrasing.

## Sprint Documents To Create Or Update

Already created during planning:

- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/pre_start.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/prd.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/tech-plan.md`

Required after worker implementation:

- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/tech-done.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.21_18-19_field-evidence-real-material-followup-escalation-status/final.md`
- `OKR.md` and `docs/process/okr_progress_log.md` only during Product closeout if implementation evidence lands; progress should remain conservative unless real materials arrive.
