# Field Evidence Rerun Acceptance Owner Response Reviewer ACK Review Handoff PRD

Run time: 2026-05-23 11:12 Asia/Shanghai

## 1. User Value And Product North Star

User value: when a reviewer ACK has already reached review-decision, field owner / support / reviewer need a safe handoff state that says what to do next, what remains missing, and why robot control is still disabled. The handoff must be readable on PC, Robot diagnostics, and mobile web without leaking raw artifacts.

Product north star: ordinary phone users can send trash safely and understand blocked states without ROS2, SSH, serial tools, or hardware debugging. This sprint supports that north star by keeping evidence governance clear and fail-closed while real materials are still absent.

This is not a delivery feature completion. It is a bounded software-proof rung that prevents ambiguous reviewer ACK states from being treated as real route/elevator, cloud, phone, or hardware proof.

## 2. Problem

The previous sprint completed `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_decision`. That answers whether the reviewer ACK intake is acceptable, incomplete, unsafe, or blocked. It does not yet package that decision into the next handoff artifact that field owner, support, and reviewer can use for follow-through.

Without this handoff rung, the project risks either stopping at review-decision metadata or letting downstream users infer success from a decision state. The correct next step is to create a safe handoff that preserves the same evidence boundary and false safety flags.

## 3. OKR Mapping

- Objective 5 remains the lowest at about 68%. This sprint does not target O5 external proof because the host lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, and verified terminal result.
- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint does not provide real 2D LiDAR / ToF materials, WAVE ROVER powered bench logs, UART logs, or HIL.
- Objective 2/3/4 remain about 99%. This sprint does not prove real route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser behavior, dropoff/cancel completion, delivery result, or delivery success.

Expected OKR impact: no OKR percentage lift.

## 4. KR Decomposition

Capability KR:

- Produce `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff` from the prior reviewer ACK review-decision safe metadata.
- Preserve the exact evidence boundary `software_proof_docker_field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff_gate`.
- Keep the same safe `evidence_ref` through PC gate, Robot diagnostics, and mobile read-only panel.
- Make missing, rejected, and next-required evidence explicit.

Safety KR:

- Preserve `source=software_proof`, `software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled on mobile.
- Reject or block raw ROS topics, `/cmd_vel`, serial/UART paths, WAVE ROVER parameters, credentials, DB/queue URLs, local filesystem paths, complete artifacts, checksums, tracebacks, HIL/pass wording, true phone/browser wording, route/elevator field-pass wording, and delivery success wording.

Documentation KR:

- Update PC evidence contracts, ROS runtime contracts, and mobile user flow documentation during implementation.
- Product closeout later must update sprint `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` after worker evidence returns.

## 5. Core Lever This Round

The core lever is not a new control path. It is a safe cross-surface handoff contract:

- PC gate creates and validates the handoff summary.
- Robot diagnostics exposes only a sanitized safe alias.
- Mobile web renders only read-only user/support copy and keeps all primary controls disabled.

This is the correct next rung because the latest reviewer ACK review-decision is already in place; the next useful software movement is to make that decision actionable for follow-up without weakening proof boundaries.

## 6. Priority And Acceptance Criteria

P0 acceptance:

- Three IC workers can be dispatched in parallel from `tech-plan.md` without overlapping file ownership.
- Each worker has explicit allowed files and fenced validation commands.
- The implementation must produce capability string `field_evidence_rerun_execution_result_acceptance_handoff_intake_owner_response_reviewer_ack_review_handoff`.
- The implementation must preserve false safety flags and no OKR percentage lift.
- Mobile primary actions must remain disabled.

P1 acceptance:

- Product closeout later records actual worker file lists and validation snippets.
- `OKR.md` remains conservative: Objective 5 about 68%, Objective 1 about 81%, no percentage lift for this sprint unless new real evidence appears.

## 7. Responsible Engineers

- Autonomy Algorithm Engineer owns PC evidence gate and `docs/interfaces/evidence_contracts.md`.
- Robot Platform Engineer owns Robot diagnostics safe alias and `docs/interfaces/ros_runtime_contracts.md`.
- User Touchpoint Full-Stack Engineer owns `mobile/web` read-only panel, fixture, focused mobile test, and `docs/product/mobile_user_flow.md`.
- Product Manager / OKR Owner owns sprint closeout and OKR/progress log update after implementation evidence exists.

## 8. Risks, Blockers, And Evidence Chain

Remaining blockers:

- No true public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal result.
- No real 2D LiDAR / ToF source/receipt/procurement/installation/wiring/power/calibration/HIL-entry materials.
- No WAVE ROVER powered bench, UART, `/odom`, `/imu/data`, `/battery`, or HIL evidence.
- No real route/elevator field pass, Nav2/fixed-route runtime log, task record, door/floor/human-assist evidence, dropoff/cancel completion, delivery result, or delivery success.

Evidence chain needed later:

- Same safe `evidence_ref` must connect reviewer ACK review-decision, reviewer ACK review handoff, field owner/support follow-up, and any future real material backfill.
- Any future OKR lift requires real external, hardware, phone, or field evidence rather than this Docker-only metadata.

## 9. Sprint Documents

This planning phase creates:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Implementation phase must later create or update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
