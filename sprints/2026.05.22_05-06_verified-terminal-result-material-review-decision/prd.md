# Verified Terminal Result Material Review Decision PRD

Run time: 2026-05-22 05:06 Asia/Shanghai

## Product Summary

`verified_terminal_result_material_review_decision` is a fail-closed review-decision capability for the prior terminal delivery/dropoff/cancel material intake output. It reads the previous intake artifact, summary, and Robot diagnostics safe alias, then emits a metadata-only decision that tells the next owner what can happen next.

This is not a success detector and not a reviewer-resolution detector. The required output boundary is `software_proof_docker_verified_terminal_result_material_review_decision_gate`, with `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false` unless future real material is supplied and accepted through a separate closeout decision.

## User Value And Product North Star

User value: support and field owners need a concrete review outcome after material intake, not another generic "missing materials" note. A review decision should say whether the intake is reviewable, needs material backfill, is rejected because of unsafe/overclaiming content, or is blocked because safe input is absent.

Product north star: a normal user should only see task completion when real terminal delivery/dropoff/cancel result material is accepted under the same safe `evidence_ref`. Before that, the phone experience must explain the review decision and keep motion-related actions disabled.

## OKR Mapping

- Objective 5 remains the lowest current Objective at about 68%. This sprint targets Objective 5 through the verified terminal result path, but only as the next review-decision step after intake.
- Objective 2 and Objective 3 benefit only as downstream consumers when real route/elevator/task materials are later provided. This sprint does not prove real route/elevator field pass, Nav2/fixed-route runtime, dropoff completion, cancel completion, or delivery result.
- Objective 4 benefits through a read-only phone-safe review-decision panel. This sprint does not prove real iPhone/Android behavior, production app, PWA prompt/user choice, or true browser/device acceptance.
- Objective 1 remains blocked on real hardware materials. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` stays unresolved / material pending, and comment `3269642220` stays software-proof publication only unless reviewer state changes and real materials are provided.

## KR Breakdown

1. KR-A Autonomy review decision: a PC CLI reads prior intake output and emits `accepted_for_review`, `needs_material_backfill`, `rejected`, or `blocked` with same-safe-`evidence_ref` checks.
2. KR-B Robot diagnostics: a safe Robot alias exposes the review decision while forcing `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
3. KR-C Mobile touchpoint: mobile/web renders a read-only review-decision panel with backend-provided safe copy only.
4. KR-D Product closeout: sprint closeout records evidence boundaries, keeps Objective 5 unchanged unless real verified materials appear, and documents remaining proof gaps.

## Core Product Grabs

The core grab is a decision layer after intake:

- input: prior intake artifact, intake summary, or Robot safe alias;
- same safe `evidence_ref` enforced;
- decision values constrained to `accepted_for_review`, `needs_material_backfill`, `rejected`, or `blocked`;
- `owner_handoff` and `next_required_evidence` required;
- unsafe raw details and success overclaims rejected;
- safe summary out for diagnostics/mobile;
- controls remain disabled.

## Functional Requirements

### Review Input

The review-decision gate must support prior intake data from:

- `trashbot.verified_terminal_result_material_intake.v1`
- `trashbot.verified_terminal_result_material_intake_summary.v1`
- `robot_diagnostics_verified_terminal_result_material_intake_summary`

Required review input fields:

- `capability=verified_terminal_result_material_intake` or compatible safe alias.
- `evidence_boundary=software_proof_docker_verified_terminal_result_material_intake_gate`.
- safe `evidence_ref`.
- `terminal_result_type` equal to `delivery`, `dropoff`, or `cancel`.
- material status or required-materials summary.
- `owner_handoff` or field-owner context when present.
- explicit proof flags: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.

### Review Decision Rules

The decision output must use exactly one of:

- `accepted_for_review`: intake is safe, same-`evidence_ref`, and complete enough for a human or field owner to review; this still does not mean delivery success.
- `needs_material_backfill`: intake is safe but lacks required real materials, so `next_required_evidence` must name the missing material groups.
- `rejected`: unsafe fields, overclaims, raw artifacts, credential-like content, or evidence mismatches make the intake unfit for review.
- `blocked`: no safe intake artifact/summary/Robot alias is available, or the source is malformed enough that the reviewer cannot classify it.

The gate must fail closed when:

- `evidence_ref` is missing, unsafe, or inconsistent across source artifacts.
- intake status is missing or says the bundle is unsafe/incomplete.
- `terminal_result_type` is not one of `delivery`, `dropoff`, or `cancel`.
- any source claims `delivery_success=true`, `primary_actions_enabled=true`, `safe_to_control=true`, `route_elevator_field_pass=true`, `hil_pass=true`, reviewer resolution, or similar success/control overclaim.
- raw artifacts, full JSON dumps, credentials, bearer tokens, signed URLs, DB/queue URLs, OSS AK/SK, local paths, checksums, tracebacks, ROS topics, `/cmd_vel`, serial/UART details, baudrate values, or WAVE ROVER control details appear in safe fields.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is described as resolved from comment `3269642220` without live reviewer resolution and real hardware materials.

### Summary Artifact

The review-decision summary must include only phone-safe fields:

- summary schema and capability.
- source intake capability and source intake status.
- `review_decision`.
- safe `evidence_ref` and safe `command_id` when available.
- terminal result type.
- decision reasons.
- material status summary.
- blocked or rejection reason when applicable.
- `next_required_evidence`.
- `owner_handoff`.
- safe copy text if all copied content is sanitized.
- `not_proven`.
- `delivery_success=false`.
- `primary_actions_enabled=false`.
- `safe_to_control=false`.
- evidence boundary.

## Non-Goals

- This sprint does not prove real delivery, real dropoff, real cancel completion, or route/elevator field pass.
- This sprint does not prove real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or external O5 proof.
- This sprint does not prove real iPhone/Android behavior, production app, or real PWA prompt/userChoice.
- This sprint does not prove WAVE ROVER/UART/HIL, real serial, real 2D LiDAR/ToF source/procurement/install/calibration, or PR #5 material closure.
- This sprint does not enable Start Delivery, Confirm Dropoff, Cancel, replay, resubmit, ACK mutation, cursor mutation, or any robot control path.

## Priority And Acceptance

P0:

- PC review-decision gate must reject unsafe, incomplete, inconsistent, and overclaiming intake summaries.
- Robot diagnostics must expose the safe review-decision summary without control enablement.
- Mobile/web must show read-only decision status and safe copy without enabling primary actions.
- Product closeout must preserve evidence language and keep Objective 5 unchanged if no real material is accepted.

P1:

- The summary should provide enough `owner_handoff` text for the next field owner to know whether to review, backfill material, or reject and recollect.
- Docs must explain that this gate reviews intake metadata and is not proof of delivery success.

Acceptance:

- All implementation owners run the fenced commands in `tech-plan.md`.
- Required strings appear across implementation, docs, and sprint records: `verified_terminal_result_material_review_decision`, `software_proof_docker_verified_terminal_result_material_review_decision_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- No surface claims true success, reviewer resolution, or control readiness from Docker-only proof.

## Responsible Engineers

- Autonomy Algorithm Engineer: PC review-decision CLI, schema validation, test fixtures, evidence interface docs.
- Robot Platform Engineer: diagnostics/status alias, safe summary integration, operator gateway diagnostics tests, interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, safe copy behavior, fixture, UI tests, mobile user flow docs.
- Product Manager / OKR Owner: sprint closeout, OKR/progress log decision, evidence boundary review, no-overclaim acceptance.

## Risks And Evidence Gaps

- The host has Docker only, so all proof remains `software_proof_docker_verified_terminal_result_material_review_decision_gate`.
- No real terminal delivery/dropoff/cancel result material is currently supplied; in that case this sprint is a review-decision gate, not a completed delivery result.
- `accepted_for_review` can be misread as accepted delivery success unless all surfaces keep `delivery_success=false`.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and cannot be closed by this sprint.
- Objective 5 should not increase unless real terminal result materials or external proof are supplied and verified.

## Sprint Docs To Create Or Update

Planning phase creates:

- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/pre_start.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/prd.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-plan.md`

Implementation and closeout must later create or update:

- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/tech-done.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/side2side_check.md`
- `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/final.md`
- related `docs/interfaces/` and `docs/product/` files touched by the implementation owners.
- `OKR.md` and `docs/process/okr_progress_log.md` only at Product closeout, and only with conservative evidence boundaries.
