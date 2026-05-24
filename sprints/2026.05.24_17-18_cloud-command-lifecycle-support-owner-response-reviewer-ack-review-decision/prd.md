# PRD - Cloud command lifecycle support owner-response reviewer ACK review decision

- sprint_type: epic
- sprint: `2026.05.24_17-18_cloud-command-lifecycle-support-owner-response-reviewer-ack-review-decision`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`

## User Value

Support, field owner, and reviewer need a safe review-decision layer after reviewer ACK intake. The user value is not a new control action; it is a clearer support state that says whether the reviewer ACK can proceed, needs reassignment, lacks material, conflicts with the safe `evidence_ref`, or must stay blocked because the input is unsafe.

For normal phone users, the value is indirect but important: the mobile surface keeps explaining why Start Delivery, Confirm Dropoff, and Cancel remain disabled instead of presenting cloud-support metadata as a successful delivery.

## Product North Star

The product north star is a phone-safe and support-safe cloud command lifecycle. Every O5 support rung must expose enough status for recovery and escalation while proving only what the local Docker/software gate actually verifies.

This sprint must keep the O5 support branch honest:

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not verified terminal result`
- `not true phone/browser proof`
- `no OKR percentage lift`

## OKR Mapping

- Primary Objective: Objective 5 云中转 + OSS/CDN 数据通路产品化, currently about 68% and still the lowest in `OKR.md` 4.1.
- Secondary guardrails: Objective 1 stays at about 81% because this is not HIL, WAVE ROVER/UART, LiDAR/ToF material, or PR #5 resolution. Objectives 2/3/4 stay at about 99% because this is not route/elevator runtime, Nav2/fixed-route runtime, real field pass, or true phone/browser proof.
- Expected OKR effect: no OKR percentage lift unless real external proof appears, which is outside this planning scope.

## KR Breakdown

- KR5.1 support-readiness: Robot/API exposes `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision` as a safe, read-only summary derived from reviewer ACK intake.
- KR5.2 phone-readiness: `mobile/web` renders a read-only reviewer ACK review-decision panel and keeps all primary actions disabled.
- KR5.3 evidence-boundary clarity: Robot/API, mobile UI, tests, and product docs all carry `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision_gate`.
- KR5.4 blocker preservation: PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains visible only as unresolved / `hardware_material_pending`.
- KR5.5 non-claim enforcement: docs and tests preserve `not verified terminal result`, `not true phone/browser proof`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `no OKR percentage lift`.

## Core Grab

The core grab is one review-decision layer after reviewer ACK intake:

`cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_intake` -> `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_reviewer_ack_review_decision`

This is a support workflow refinement, not a hardware, cloud-production, or delivery-completion sprint.

## Needs To Be Done

- Add Robot/API safe summary construction and focused validation for reviewer ACK review decisions.
- Add a read-only `mobile/web` panel and fixture for the same safe summary.
- Update `docs/product/remote_4g_mvp.md` and `docs/product/mobile_user_flow.md` during implementation to keep docs synchronized with the new support boundary.
- Preserve the fixed proof boundary and false flags in source, tests, fixture, and docs.
- Defer `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and progress-log updates until implementation evidence exists. This planning task must not modify them.

## Priority And Acceptance

P0 acceptance:

- Robot/API and mobile both use the exact capability and proof boundary strings.
- Both lanes preserve one safe command id and one safe `evidence_ref`.
- Both lanes expose reviewer ACK review decision, source ACK intake status, decision reasons, owner/support/reviewer next steps, blocker state, PR #5 material blocker context, and next required evidence.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Unsafe inputs, missing safe IDs, conflicting refs, raw paths, credentials, bearer tokens, signed URLs, ROS topics, `/cmd_vel`, serial/UART, WAVE ROVER details, tracebacks, complete artifacts, checksums, cursor changes, and success wording stay blocked/not_proven.
- Required validation commands in `tech-plan.md` pass.

P1 acceptance:

- Product docs explain why this is not public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, WAVE ROVER/UART proof, PR #5 resolved, route/elevator field pass, or delivery success.

## Responsibility

- Task A owner: Robot Platform Engineer.
- Task B owner: User Touchpoint Full-Stack Engineer.
- Product Manager / OKR Owner owns planning docs now and later closeout evidence review, but does not implement product code, tests, fixtures, product docs, `OKR.md`, or progress log in this planning-only task.

## Risks, Blockers, And Evidence Chain

- Risk: review-decision wording could imply verified terminal result. Required mitigation: keep `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift` visible in docs/tests.
- Risk: mobile panel could become an action surface. Required mitigation: Start Delivery, Confirm Dropoff, and Cancel stay disabled, and no mutation route is added.
- Risk: PR #5 material blocker could be overstated as resolved because PR #5 is merged. Required mitigation: preserve `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending`.
- Risk: Docker/local support proof could be mistaken for external cloud proof. Required mitigation: explicitly state not public HTTPS/TLS, not 4G/SIM, not OSS/CDN live traffic, not production DB/queue, and not worker/cutover.
- Evidence chain still missing for real OKR lift: real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser/device proof, verified terminal delivery/dropoff/cancel result, route/elevator field pass, HIL, WAVE ROVER/UART proof, and PR #5 reviewer resolution.

## Sprint Documents

- Current planning documents: `pre_start.md`, `prd.md`, `tech-plan.md`.
- Future implementation closeout documents: `tech-done.md`, `side2side_check.md`, `final.md`.
- No `OKR.md`, progress log, source, test, fixture, or product-doc changes are allowed in this planning task.
