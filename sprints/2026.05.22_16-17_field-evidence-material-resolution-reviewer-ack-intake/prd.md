# Field Evidence Material Resolution Reviewer ACK Intake PRD

Run time: 2026-05-22 16:00 Asia/Shanghai

## 1. User Value And Product North Star

The user-facing product goal remains a low-cost ROS2 trash delivery robot that ordinary phone users can operate without understanding ROS2, serial hardware, cloud internals, or evidence artifacts.

This sprint focuses on support/reviewer value: after the owner-response review handoff is sent to reviewer/support/field-owner, the system needs a safe ACK intake gate. That gate receives and validates the human response, then tells the team whether the evidence chain may proceed to later reviewer material review, whether the field owner must supplement handoff material, or whether the chain is blocked.

The ACK intake must reduce ambiguity. It must not turn an ACK into robot control permission, phone success, field pass, HIL, or OKR completion.

## 2. OKR Mapping

### Objective 5

- Current status: about 68%, lowest in `OKR.md` 4.1.
- Mapping: this sprint is adjacent to Objective 5 because it improves material-resolution governance for cloud/terminal-result/external-proof blockers.
- Boundary: no OKR percentage lift. The sprint does not prove public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser, verified terminal result, or delivery success.

### Objective 1

- Current status: about 81%.
- Mapping: hardware consultation must keep PR #5 and WAVE ROVER/HIL boundaries explicit.
- Boundary: no OKR percentage lift. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / hardware-material pending unless live evidence proves otherwise; comment `3269642220` remains software-proof only.

### Objective 2 / Objective 3 / Objective 4

- Current status: about 99% each.
- Mapping: ACK intake can support future route/elevator field material review, Robot diagnostics, and mobile support visibility.
- Boundary: no OKR percentage lift. This sprint does not prove real task record, Nav2/fixed-route runtime, route completion signal, route/elevator field pass, true phone/browser, dropoff/cancel completion, verified terminal result, or delivery success.

## 3. KR Breakdown

### KR-A: ACK Intake Contract

Create `field_evidence_material_resolution_reviewer_ack_intake` as the canonical PC gate that consumes the previous owner-response review-handoff summary or artifact and a reviewer/support/field-owner ACK material.

Supported ACK states:

- `acknowledged`: handoff was received and can proceed to later reviewer material review, still `not_proven`.
- `needs_reassignment`: current assignee cannot review; output must route support/product to reassign.
- `blocked_missing_handoff`: ACK cannot be accepted because the required handoff reference or safe evidence material is missing.
- `rejected_unsafe_ack`: ACK claims unsafe success, control permission, HIL, delivery success, external proof, raw artifacts, or credentials.

### KR-B: Robot Safe Summary

Expose only a sanitized Robot diagnostics alias for ACK intake. The alias must be metadata-only, read-only, and fail closed.

Required flags:

- `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`
- `not_proven`
- `delivery_success=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`

### KR-C: Mobile Support Visibility

Add a read-only mobile/web support panel for ACK intake status. It must explain in Chinese-first copy whether the reviewer material review can proceed, field owner needs to supplement, reassignment is required, or the chain is blocked.

The panel must not enable Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, diagnostics fetch, replay, resubmit, or robot control.

### KR-D: Hardware / PR Boundary Consultation

Hardware must confirm the ACK intake does not resolve PR #5 and does not prove WAVE ROVER/UART/HIL or 2D LiDAR/ToF material. Hardware work is read-only unless a later implementation plan explicitly authorizes hardware files.

## 4. Core Grab

Build one ACK intake layer immediately after `field_evidence_material_resolution_owner_response_review_handoff`.

The expected lifecycle is:

1. Prior handoff exists and is safe.
2. Reviewer/support/field-owner sends ACK material.
3. ACK intake classifies it into one of the four supported states.
4. Robot diagnostics exposes a safe summary.
5. Mobile/web displays the safe summary.
6. Product closeout decides whether the next sprint may enter reviewer material review, must request field owner supplement, must reassign, or must remain blocked.

## 5. Scope

### In Scope

- PC gate for ACK intake classification and summary output.
- Unit tests and CLI validation for all four ACK states.
- Robot diagnostics safe alias.
- Mobile/web read-only panel and fixture.
- Interface/product docs updates during implementation.
- Hardware read-only consultation on PR #5 and vendor/material evidence boundaries.
- Sprint closeout docs after implementation.

### Out Of Scope

- Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or production migration.
- Real phone/browser validation, PWA prompt/userChoice, or production app acceptance.
- Real WAVE ROVER/UART/HIL, `/odom`, `/imu/data`, `/battery`, 2D LiDAR/ToF procurement/install/calibration/HIL-entry, or PR #5 resolution.
- Real route/elevator field pass, Nav2/fixed-route runtime, task record, route completion signal, verified terminal result, dropoff/cancel completion, or delivery success.
- Any robot control endpoint, ACK mutation endpoint, cursor mutation, replay/resubmit, serial open, ROS topic command, or `/cmd_vel` exposure.

## 6. Priority And Acceptance

### P0 Acceptance

- `field_evidence_material_resolution_reviewer_ack_intake` exists as a fenced PC gate.
- All four ACK states are covered: `acknowledged`, `needs_reassignment`, `blocked_missing_handoff`, `rejected_unsafe_ack`.
- Output includes a next-step decision: proceed to later reviewer material review, request field owner supplement, reassign, or remain blocked.
- Proof boundary and flags are preserved: `software_proof_docker_field_evidence_material_resolution_reviewer_ack_intake_gate`, `not_proven`, `delivery_success=false`, `safe_to_control=false`, `primary_actions_enabled=false`.

### P1 Acceptance

- Robot diagnostics exposes a safe metadata-only alias with redacted fields.
- Mobile/web renders the safe alias without changing primary action enablement.
- Docs explain the evidence boundary and downstream handoff path.

### P2 Acceptance

- Product closeout explicitly states no OKR percentage lift unless real external/hardware/field/phone/browser/terminal-result evidence appears.

## 7. Responsible Engineers

- `autonomy-engineer`: PC gate, artifact schema, classification tests, evidence contract docs.
- `robot-software-engineer`: Robot diagnostics safe alias and diagnostics docs.
- `full-stack-software-engineer`: mobile/web panel, fixture, tests, and mobile product docs.
- `rober-hardware-engineer`: read-only vendor/PR #5/material boundary consultation.
- `product-okr-owner`: sprint closeout, OKR boundary, side-by-side acceptance, and no-lift decision.

## 8. Risks And Evidence Gaps

- Risk: ACK wording can look like approval. Mitigation: every state must include `not_proven`, `delivery_success=false`, `safe_to_control=false`, and `primary_actions_enabled=false`.
- Risk: `acknowledged` can be mistaken for reviewer resolution. Mitigation: it only means the handoff was received and may proceed to later reviewer material review.
- Risk: mobile panel can imply phone proof. Mitigation: Chinese-first copy must state this is not true phone/browser proof.
- Risk: PR #5 thread may be over-closed. Mitigation: Hardware consultation must keep `PRRT_kwDOSWB9286CJ3tX` unresolved / hardware-material pending unless live evidence proves otherwise.
- Evidence gap: real O5 external proof, O1 HIL/material proof, route/elevator field proof, true phone/browser proof, verified terminal result, and delivery success remain missing.

## 9. Documents To Create Or Update

Planning task creates:

- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/pre_start.md`
- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/prd.md`
- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/tech-plan.md`

Implementation and closeout must later update:

- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.22_16-17_field-evidence-material-resolution-reviewer-ack-intake/final.md`
- Relevant `docs/interfaces/` and `docs/product/` docs touched by implementation.
- `OKR.md` and `docs/process/okr_progress_log.md` only during closeout and only with no-lift wording unless real evidence appears.

