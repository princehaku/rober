# Field Evidence Rerun Execution Result Review Decision PRD

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision`
- Capability: `field_evidence_rerun_execution_result_review_decision`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`

## Product Problem

The previous sprint created `field_evidence_rerun_execution_result_intake`, which can classify a field owner result packet as `missing`, `accepted`, `rejected`, or `blocked`. When the packet is `accepted`, the next product gap is review decision: support and field owners need to know whether the accepted packet is sufficient for review intake, needs material backfill, should be rejected with reasons, or remains blocked by absent real evidence.

Without a review-decision layer, an accepted intake can be overread as a delivery result. That would break the evidence boundary because this host has only Docker/local software proof and no real route/elevator field pass, no HIL, no true phone/browser proof, and no O5 external proof.

## User Value And North Star

North star: ordinary phone users and support operators can move a trash delivery task through clear, evidence-backed states without touching ROS2, SSH, serial tools, or raw artifacts.

This sprint gives them a readable review decision for the same safe `evidence_ref`: accepted for review, needs material backfill, rejected, or blocked. The decision tells users what to provide next while keeping all primary actions disabled and preventing false delivery-success claims.

## OKR Mapping

- Objective 5: current lowest at about 68%, but not actionable here without real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser evidence. This sprint must not claim O5 external proof.
- Objective 1: about 81%, still blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / material pending. Published comment `3269642220` is not reviewer resolution. This sprint must not claim hardware material closure.
- Objective 2 / 3 / 4: actionable route/elevator/user-touchpoint evidence chain. The sprint improves reviewability of field rerun execution results while preserving `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Scope

In scope:

- Create a canonical PC gate for `field_evidence_rerun_execution_result_review_decision`.
- Consume only safe result-intake summaries or compatible safe aliases.
- Preserve same-safe-`evidence_ref` and fail closed on unsafe, missing, or contradictory material.
- Expose a Robot diagnostics safe summary.
- Add a mobile/web read-only panel for the review decision and next evidence.
- Sync relevant interface and product docs during implementation.

Out of scope:

- Real robot motion, real route/elevator execution, real delivery, real dropoff/cancel completion, real phone/browser validation, WAVE ROVER/UART/HIL, PR #5 reviewer resolution, PR #6 runtime proof, O5 external cloud proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, and production worker/cutover.
- Enabling Start Delivery, Confirm Dropoff, Cancel, ACK/cursor fetch, queue scheduling, execution scheduling, review submission to remote services, or any robot command.

## Product Requirements

1. The review decision must accept only `field_evidence_rerun_execution_result_intake` status `accepted` as eligible for review; other states must remain `blocked` or `needs_material_backfill`.
2. The decision vocabulary must be explicit and conservative: `accepted_for_review`, `needs_material_backfill`, `rejected`, `blocked`.
3. `accepted_for_review` means only accepted for Product/Engineer review of the result packet; it must not mean field pass, route pass, elevator pass, dropoff completion, cancel completion, delivery result, or delivery success.
4. Every output must carry `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`, `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. The mobile panel must show safe `evidence_ref`, decision, blocker/rejection/backfill reason, next required evidence, owner handoff, and fail-closed flags in Chinese-first copy.
6. The implementation must not expose raw artifacts, local paths, credentials, DB/queue URLs, OSS secrets, bearer tokens, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, checksums, or complete packet contents.
7. Documentation under `docs/` must be synchronized by the responsible Engineer workers if code or interface behavior changes.
8. Any code added by Engineers must use Chinese technical comments and keep the comment ratio above 20% where applicable.

## Acceptance Criteria

- Autonomy gate emits a deterministic review-decision artifact and summary from safe inputs, with focused tests covering accepted, backfill, rejected, blocked, unsafe leakage, and non-accepted intake cases.
- Robot diagnostics safe alias exposes the decision summary while preserving existing aliases and redaction behavior.
- mobile/web renders the read-only review-decision panel from Robot-safe summary fixtures and keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
- `rg` checks find `field_evidence_rerun_execution_result_review_decision`, `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`, `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false` in implementation and docs.
- Product closeout later records that this is software proof only and does not update Objective 5 or Objective 1 unless real evidence appears.

## Responsibility

- Autonomy Algorithm Engineer: canonical PC review-decision gate.
- Robot Platform Engineer: diagnostics safe alias and ROS runtime docs.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel and product mobile flow docs.
- Product Manager / OKR Owner: post-implementation `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` only after Engineer proof exists.

## Evidence Still Required For Product Completion

The following remain missing and must not be implied by this sprint: real same-safe-`evidence_ref` field rerun, task record, Nav2/fixed-route runtime log, route completion signal, elevator door state, target floor confirmation, human assistance record, dropoff/cancel completion, delivery result, true phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, WAVE ROVER/UART/HIL, real 2D LiDAR / ToF material, and PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution.
