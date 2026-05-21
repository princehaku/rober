# Field Evidence Rerun Execution Result Review Handoff PRD

## Product Context

The previous sprint produced `field_evidence_rerun_execution_result_review_decision`, which can classify a rerun result packet as reviewable, missing backfill, rejected, or blocked. That is useful, but it is not enough for the field owner to act. The next product step is a handoff layer that turns the safe review decision into a concrete field backfill request.

The handoff must be explicit about what real materials are still missing for the same safe `evidence_ref`: task record, route/elevator runtime logs, route completion signal, elevator door/floor evidence, human assistance note, dropoff or cancel completion, delivery result, and true phone/browser evidence. It must also preserve that the current host is Docker-only and that all output remains `software_proof`.

## User Value And Product North Star

- Field owner value: receive a short, structured request instead of reverse-engineering a review decision artifact.
- Support value: see the blocker summary and next required evidence from Robot diagnostics or mobile/web without opening raw files.
- Product value: reduce repeated blocker churn by moving from "review decision exists" to "owner can backfill the exact real materials needed".
- North star fit: reliable low-cost trash delivery requires a real evidence chain. This sprint improves the handoff chain without pretending Docker metadata is a real field run.

## OKR Mapping

- Objective 5 remains about 68% and is not the target. This sprint has no public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, or true phone/browser proof.
- Objective 1 remains about 81% unless real hardware material appears. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending; comment `3269642220` is not reviewer resolution.
- Objective 2 benefits only as field owner handoff support for the delivery/elevator evidence chain. It is not real route/elevator execution.
- Objective 3 benefits only as same-`evidence_ref` reconciliation and rerun guidance. It is not real Nav2/fixed-route runtime proof.
- Objective 4 benefits only as a read-only support/mobile panel. It is not true iPhone/Android, production app, PWA prompt, or real phone/browser proof.

## KR Breakdown

1. Autonomy PC gate emits `trashbot.field_evidence_rerun_execution_result_review_handoff.v1` and a summary schema from the previous review-decision summary.
2. Robot diagnostics exposes `robot_diagnostics_field_evidence_rerun_execution_result_review_handoff_summary` as a safe alias.
3. Mobile/web adds a read-only "现场证据复跑执行结果复核交接" panel that shows next required materials and owner handoff without changing controls.
4. All three surfaces preserve `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
5. Docs are updated by the responsible workers after implementation so `docs/` matches the new capability.

## Core Product Lever

The core lever is a fail-closed owner handoff, not another blocker display. The handoff must answer:

- Which review decision was consumed?
- Which safe `evidence_ref` must be preserved?
- Which real materials are missing?
- Which owner should backfill them?
- Which rerun or reconciliation guidance should the field team follow?
- Which blockers prevent claiming delivery success?

## Scope

In scope:

- PC gate and fixture/test coverage for review handoff.
- Robot diagnostics safe alias.
- Mobile/web read-only panel and fixture/test coverage.
- Documentation sync in `docs/interfaces/` and `docs/product/mobile_user_flow.md`.
- Later Product closeout to `OKR.md`, progress log, and sprint closeout docs only after workers implement.

Out of scope:

- Real field rerun, real task execution, real route/elevator pass, real Nav2/fixed-route, real phone/browser, HIL, WAVE ROVER/UART, real dropoff/cancel completion, and Objective 5 external proof.
- Resolving PR #5 `PRRT_kwDOSWB9286CJ3tX` or treating PR #6 docs-only work as runtime proof.
- Any direct command/control change, including Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, queue, cloud command, or robot motion.

## Priority And Acceptance

Priority order:

1. Fail-closed PC handoff gate with clear schema and owner backfill request.
2. Robot-safe diagnostics alias that can be consumed without leaking raw artifacts or low-level implementation details.
3. Mobile/web read-only panel that makes the handoff visible while all primary actions remain disabled.

Product acceptance requires:

- The handoff names `field_evidence_rerun_execution_result_review_handoff`.
- The evidence boundary is `software_proof_docker_field_evidence_rerun_execution_result_review_handoff_gate`.
- The output explicitly contains `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.
- The plan names Objective 5 and Objective 1 blocker evidence, including PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Worker verification remains fenced to py_compile, unittest, CLI help, `rg`, scoped `git diff --check`, node syntax check, mobile unittest, and JSON validation.

## Responsibility

- Product Manager / OKR Owner: planning docs, sprint scope, OKR mapping, Product closeout after implementation.
- Autonomy Algorithm Engineer: PC gate, canonical artifact/schema, focused tests, evidence docs.
- Robot Platform Engineer: diagnostics safe alias, focused tests, ROS runtime docs.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel, fixture/test coverage, mobile product doc update.

## Risks And Evidence Gaps

- The handoff may make blockers easier to see, but it cannot reduce the blocker without real field-owner backfill.
- If future copy says "accepted" without `not_proven`, it may be misread as delivery success. The schema and UI must keep success/control wording blocked.
- If Robot/mobile consumers expose raw artifacts, credentials, ROS topics, serial/UART, WAVE ROVER details, checksums, or tracebacks, the surface becomes unsafe for phone/support consumption.
- Remaining evidence gaps are real same-safe-`evidence_ref` task record, route/elevator runtime logs, route completion signal, door/floor proof, human assistance record, dropoff/cancel completion, delivery result, true phone/browser evidence, HIL, Objective 5 external proof, and PR #5 reviewer resolution.

## Sprint Documentation

- This planning step creates only `pre_start.md`, `prd.md`, and `tech-plan.md`.
- `tech-done.md`, `side2side_check.md`, and `final.md` must wait for implementation and validation evidence.
