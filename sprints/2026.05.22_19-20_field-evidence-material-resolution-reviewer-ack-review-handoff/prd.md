# Field Evidence Material Resolution Reviewer ACK Review Handoff PRD

Run time: 2026-05-22 19:20 Asia/Shanghai

## Sprint Type

sprint_type: epic

Capability: `field_evidence_material_resolution_reviewer_ack_review_handoff`

Evidence boundary: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_review_handoff_gate`

## Problem

The previous sprint can decide whether a reviewer ACK after material-resolution intake is acceptable, blocked, unsafe, missing prerequisites, or needs field-owner supplement. The next product gap is handoff: support and field owners still need one sanitized package that explains the review decision, the remaining blocker, the next evidence required, and the exact safety boundary without exposing raw artifacts or enabling robot control.

## User Value And Product North Star

User value: a phone user and support staff can see that the robot is still blocked, why it remains blocked, and who owns the next real-material step. Field owners and reviewers get a clear handoff package instead of reconstructing context from raw artifacts.

Product north star: ordinary users should rely on the phone surface for safe status and next action, while engineering keeps evidence traceability across PC gate, Robot diagnostics, and mobile/web without converting software proof into real-world proof.

## OKR Mapping

- Objective 5: lowest at about 68%; this sprint supports O5 evidence governance while real public HTTPS/TLS, 4G/SIM, OSS/CDN, production DB/queue, worker/cutover, and true phone/browser proof remain unavailable.
- Objective 1: about 81%; `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`, so this sprint must not imply real 2D LiDAR / ToF material readiness, WAVE ROVER/UART/HIL, or reviewer resolution.
- Objective 2/3/4: about 99%; this sprint must not imply route/elevator field pass, Nav2/fixed-route runtime, dropoff/cancel completion, verified terminal result, or delivery success.
- Expected outcome: no OKR percentage lift.

## KR Breakdown

- KR-A PC handoff gate: generate a reviewer ACK review handoff artifact and summary from the prior review-decision artifact/summary, preserving one safe `evidence_ref`, redaction, missing evidence, owner routing, and fail-closed flags.
- KR-B Robot diagnostics: expose a phone-safe alias `robot_diagnostics_field_evidence_material_resolution_reviewer_ack_review_handoff_summary` without raw artifacts, credentials, local paths, ROS topics, serial details, or control permissions.
- KR-C mobile/web read-only panel: render the handoff status, decision context, safe `evidence_ref`, blocker, owner handoff, and next required evidence while keeping Start Delivery, Confirm Dropoff, and Cancel disabled.
- KR-D docs sync: update PC evidence contracts, Robot diagnostics contracts, and mobile user flow docs so the new surface is documented.
- KR-E Product closeout: after implementation only, update `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` conservatively.

## Core Grab

Build a support/field-owner/reviewer handoff package for `field_evidence_material_resolution_reviewer_ack_review_handoff` that consumes the prior reviewer ACK review-decision output and keeps these flags invariant:

- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Scope

In scope:

- PC-only gate, focused tests, and evidence contract docs.
- Robot diagnostics safe alias, focused diagnostics tests, and diagnostics docs.
- Mobile/web read-only panel, fixture, focused tests, and mobile flow docs.
- Product closeout after implementation.

Out of scope:

- Resolving PR #5 thread `PRRT_kwDOSWB9286CJ3tX`.
- Raising OKR percentages.
- Adding robot commands, ACK mutation, replay, cursor fetch, diagnostics fetch, or control endpoints.
- Real public cloud proof, true phone/browser proof, WAVE ROVER/UART/HIL, route/elevator field pass, dropoff/cancel completion, verified terminal result, or delivery success.

## Acceptance Criteria

- PC gate rejects unsafe raw fields, missing prior review-decision input, mismatched `evidence_ref`, success/control overclaims, credentials, local paths, ROS/control details, and hardware details.
- Robot diagnostics summary exposes only phone-safe handoff data and keeps all control/success flags false.
- Mobile/web panel appears only as read-only support metadata and never enables primary actions.
- All user-facing and docs language keeps Docker-only software proof separate from real cloud, real phone, real hardware, HIL, field pass, and delivery success.
- Sprint closeout records no OKR percentage lift unless real external, hardware, or field materials appear before closeout.

## Responsible Engineers

- Autonomy Algorithm Engineer owns PC gate and evidence contract docs.
- Robot Platform Engineer owns Robot diagnostics safe alias and diagnostics docs.
- User Touchpoint Full-Stack Engineer owns mobile/web read-only panel and mobile flow docs.
- Product Manager / OKR Owner owns post-implementation closeout and conservative OKR logging.

## Risks And Evidence Gaps

- `PRRT_kwDOSWB9286CJ3tX` remains unresolved and cannot be closed by this sprint.
- Missing real cloud materials block O5 progress lift.
- Missing real WAVE ROVER/UART/HIL and 2D LiDAR/ToF materials block O1 progress lift.
- Missing real route/elevator/task-record/phone/browser materials block any field-pass or true mobile proof claim.
