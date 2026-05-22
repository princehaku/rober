# Field Evidence Material Resolution Reviewer ACK Intake Pre Start

Run time: 2026-05-22 16:00 Asia/Shanghai

## Sprint Declaration

- sprint_type: epic
- Sprint folder: `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/`
- Capability: `field_evidence_material_resolution_reviewer_ack_intake`
- Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`
- Product status: `not_proven`
- Safety flags: `delivery_success=false`, `safe_to_control=false`, `primary_actions_enabled=false`
- OKR effect: no OKR percentage lift

## User Value And Product North Star

Product north star: ordinary phone users should be able to hand trash to the robot and understand, from a safe phone/support surface, whether the route/elevator/material evidence chain is ready for the next human review step without needing SSH, ROS2, hardware debugging, or raw artifact inspection.

This sprint does not try to prove delivery. It closes the next workflow gap after `field_evidence_material_resolution_owner_response_review_handoff`: reviewer, support, or field owner may acknowledge the handoff, ask for reassignment, report missing handoff material, or reject an unsafe ACK. The value is making that response machine-checkable before any later reviewer material review is allowed.

## Evidence Read Before Start

- `AGENTS.md`: Epic sprint planning must include `pre_start.md -> prd.md -> tech-plan.md`, OKR lowest-priority review, owner split, file scopes, interface impact, and fenced acceptance commands.
- `OKR.md` 4.1, updated 2026-05-22 15:33: Objective 5 is still the lowest objective at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
- `sprints/2026.05.22_14-15_field-evidence-material-resolution-owner-response-review-decision/final.md`: owner-response review decision closed as software proof only, no OKR percentage lift.
- `sprints/2026.05.22_15-16_field-evidence-material-resolution-owner-response-review-handoff/final.md`: owner-response review handoff closed as `software_proof_docker_field_evidence_material_resolution_owner_response_review_handoff_gate`, with `not_proven`, `safe_to_control=false`, `primary_actions_enabled=false`, and `delivery_success=false`.
- `/Users/m4/.codex/automations/skill-progression-map/memory.md`: latest runs preserve Docker/software-proof boundaries and require no-lift closeout unless real external, hardware, phone/browser, route/elevator, or terminal-result evidence appears.
- `docs/product/mobile_user_flow.md`: mobile/web field/support panels must remain read-only and must not enable Start Delivery, Confirm Dropoff, or Cancel.
- `docs/product/production_hardware_boundary.md`: hardware facts remain vendor/source-boundary only; no 2D LiDAR/ToF procurement, installation, wiring, calibration, WAVE ROVER UART/HIL, or delivery proof exists here.

## Why This Sprint Exists Now

Objective 5 is still numerically lowest, but the missing proof requires real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, or verified terminal result. This Docker/local host cannot create those materials.

Objective 1 is next-lowest, but PR #5 thread `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `hardware_material_pending`; comment `3269642220` is software-proof only; no real WAVE ROVER/UART/HIL or 2D LiDAR/ToF material exists.

The previous two sprint rungs already created owner-response review decision and handoff. The next useful software-proof move is not another blocker wrapper; it is an ACK intake gate that makes reviewer/support/field-owner response state explicit before downstream reviewer material review.

## Current Blockers

- Real Objective 5 external proof is missing: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, true phone/browser, and verified terminal delivery/dropoff/cancel result.
- Real Objective 1 hardware proof is missing: WAVE ROVER powered bench, UART/HIL logs, `/odom`, `/imu/data`, `/battery`, operator HIL report, 2D LiDAR/ToF real material, and PR #5 reviewer resolution.
- Real Objective 2/3/4 field proof is missing: task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor evidence, human-assistance record, true phone/browser evidence, dropoff/cancel completion, and delivery success.

## Owner Model

- Product Manager / OKR Owner: define value, KR mapping, scope boundary, and closeout rules.
- Autonomy Algorithm Engineer: own the PC ACK intake gate and canonical artifact contract.
- Robot Platform Engineer: own Robot diagnostics safe alias and fail-closed summary.
- User Touchpoint Full-Stack Engineer: own mobile/web read-only ACK panel and phone-safe copy.
- Hardware Infra Engineer: provide read-only PR #5 and vendor/material boundary consultation.

## Entry Criteria

- Existing owner-response handoff artifact/schema from 15-16 must be the source handoff input.
- ACK intake must support exactly these reviewer/support/field-owner response classes: `acknowledged`, `needs_reassignment`, `blocked_missing_handoff`, and `rejected_unsafe_ack`.
- Outputs must decide whether the chain can enter later reviewer material review, needs field owner supplement, or remains blocked.
- All outputs must preserve `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`, `not_proven`, `delivery_success=false`, `safe_to_control=false`, and `primary_actions_enabled=false`.

## Required Sprint Documents

- Create now: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Create during implementation/closeout: `tech-done.md`, `side2side_check.md`, `final.md`.
- Update during implementation/closeout if code/docs land: relevant `docs/` documents, `OKR.md`, and `docs/process/okr_progress_log.md` only after worker evidence is available. This planning task intentionally does not modify them.

