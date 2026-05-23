# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Followup Escalation Status PRD

Run time: 2026-05-23 18:00 Asia/Shanghai

## Product North Star

Rober should be a low-cost, phone-first trash delivery robot whose users and operators can trust the readiness state. Trust depends on refusing to convert missing real materials into success copy. This sprint turns the latest reviewer ACK handoff into an explicit follow-up escalation status so the next owner action is visible without pretending that route/elevator field execution has passed.

## User Value

The primary user is the field operator or reviewer trying to decide what to do after the reviewer ACK review-handoff. They need one safe status that says whether the follow-up is pending, overdue, escalated, blocked, or ready for reviewer material follow-up, plus the exact missing evidence list. Ordinary mobile users should see only a read-only explanation and should not gain any Start Delivery, Confirm Dropoff, or Cancel capability from this metadata.

## OKR Mapping

- Objective 5: remains the numerically lowest objective at about 68%. This sprint does not satisfy O5 because it has no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal result material.
- Objective 2 / Objective 3: this sprint is an actionable software-proof continuation for route/elevator field-evidence governance. It clarifies the missing real field materials needed before delivery, route/elevator pass, terminal result, dropoff/cancel completion, or delivery success can be claimed.
- Objective 4: mobile/web gains a read-only fail-closed panel only. This is not true phone/browser proof.
- Objective 1: PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint does not resolve 2D LiDAR / ToF or HIL evidence.

## KR Breakdown

KR-A Autonomy:
Produce `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status` from the prior reviewer ACK review-handoff safe metadata.

KR-B Robot:
Expose `robot_diagnostics_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_summary` as a safe alias that strips raw artifacts and preserves fail-closed flags.

KR-C Full-Stack:
Render the mobile panel from the Robot safe alias and fixture. The panel must be read-only, show the escalation status and missing evidence, and keep primary actions disabled.

KR-D Product:
After implementation, close out the sprint with no OKR percentage lift unless real evidence appears. Update OKR/docs only to reflect the new software-proof boundary.

## Scope

In scope:

- PC gate, fixture or sample material, focused tests, and evidence contract docs.
- Robot diagnostics safe alias, focused tests, and ROS runtime docs.
- `mobile/web` panel, fixture, focused tests, and mobile user flow docs.
- Sprint closeout and conservative OKR/docs update after implementation.

Out of scope:

- Real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or external O5 proof.
- Real WAVE ROVER, UART, HIL, 2D LiDAR / ToF procurement, installation, wiring, power, calibration, or PR #5 reviewer resolution.
- Real route/elevator field pass, Nav2/fixed-route runtime pass, verified terminal delivery/dropoff/cancel result, dropoff/cancel completion, delivery result, or delivery success.
- True iPhone/Android browser/device proof or production app proof.
- GitHub review-thread mutation or PR #5 closure.

## Required Status Semantics

The implementation should support fixed safe status values such as:

- `pending_reviewer_ack_followup_not_proven`
- `overdue_reviewer_ack_followup_not_proven`
- `escalated_missing_real_material_not_proven`
- `blocked_missing_reviewer_ack_review_handoff_not_proven`
- `ready_for_real_material_reviewer_followup_not_proven`

Every status remains `source=software_proof`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Acceptance Criteria

- Capability string appears exactly as `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status`.
- Boundary string appears exactly as `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_followup_escalation_status_gate`.
- PC, Robot, and mobile surfaces agree on safe `evidence_ref`, status, missing evidence, owner next step, reviewer next step, and boundary.
- Mobile panel is read-only and cannot trigger Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, diagnostics fetch, material upload, review, handoff, procurement, GitHub action, or robot command.
- Product closeout states no OKR percentage lift and preserves `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending`.

## Responsibilities

- Autonomy Algorithm Engineer owns the PC gate and evidence-contract surface.
- Robot Platform Engineer owns Robot diagnostics safe alias and ROS runtime contract surface.
- User Touchpoint Full-Stack Engineer owns mobile/web display and fixture behavior.
- Product Manager / OKR Owner owns sprint closeout, OKR truth boundary, and documentation acceptance.

## Risks And Evidence Gaps

- The sprint can only prove local Docker software behavior. It cannot reduce real O5, O1, O2/O3, or O4 missing-evidence gaps by itself.
- Repeating PR #5 material wrappers would violate the same-blocker red line; PR #5 is tracked only as unresolved risk evidence here.
- The planned implementation must not leak raw JSON, raw ROS topics, `/cmd_vel`, serial/UART paths, credentials, local filesystem paths, raw artifacts, checksums, complete artifacts, or success/control copy.
- If real field materials arrive during implementation, Product should route them into material intake/review instead of continuing only with escalation metadata.
