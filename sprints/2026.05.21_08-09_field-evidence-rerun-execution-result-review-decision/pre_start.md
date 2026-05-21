# Field Evidence Rerun Execution Result Review Decision Pre-start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision`
- Target capability: `field_evidence_rerun_execution_result_review_decision`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_review_decision_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Start time: 2026-05-21 08:09 Asia/Shanghai

## Read-only Evidence Checked

- `AGENTS.md`: fresh Epic sprint must enter sprint records, preserve evidence boundaries, and be ready for parallel Autonomy / Robot / Full-Stack Engineer workers when file scopes do not overlap.
- `OKR.md`: 4.1 says Objective 5 is the current lowest Objective at about 68%, but section 6 says not to repeat local O5 metadata depth without real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser material.
- `OKR.md`: Objective 1 is about 81%; PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / material pending even though comment `3269642220` has been published. The other two PR #5 review threads are resolved. PR #6 is README/docs-only and gives no runtime, hardware, HIL, true phone/browser, or O5 external proof.
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/final.md`: previous sprint completed `field_evidence_rerun_execution_result_intake` under `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`; it did not prove field pass, HIL, real phone/browser, O5 external proof, dropoff/cancel completion, or delivery success.
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-plan.md`: the previous PC gate path must advance to `field_evidence_rerun_execution_result_review_decision` when result intake status is `accepted`.

## User Value And North Star

The north star remains a low-cost ROS2 trash delivery robot that ordinary phone users can operate without SSH, ROS2 commands, serial tools, or hardware debugging. This sprint turns an accepted field rerun execution result packet into an explicit review decision so operators can see whether the packet is review-accepted, needs material backfill, is rejected, or remains blocked, while the product keeps primary controls disabled until real evidence exists.

The user value is evidence clarity, not motion. A field owner or support user should know exactly what evidence must be supplied next for the same safe `evidence_ref`, without mistaking a Docker/local review decision for real route/elevator success.

## OKR Mapping

- Objective 5 remains the numeric lowest at about 68%, but it is blocked for this host because real external cloud/phone materials are absent. This sprint must not raise Objective 5.
- Objective 1 remains about 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved / material pending. This sprint must not raise Objective 1 or claim PR #5 reviewer resolution.
- Objectives 2/3/4 remain the actionable family for Docker-only progress: result-review decision improves route/elevator evidence triage, Robot diagnostics visibility, and mobile read-only support visibility while preserving `not_proven`, `delivery_success=false`, and `primary_actions_enabled=false`.

## KR Breakdown

- KR-A: Autonomy PC gate reviews an accepted execution-result intake summary and emits `accepted_for_review`, `needs_material_backfill`, `rejected`, or `blocked` decision states.
- KR-B: Robot diagnostics exposes only the safe review-decision summary and strips raw artifacts, control details, credentials, local paths, ROS topics, serial/UART, WAVE ROVER, HIL/pass wording, and delivery success claims.
- KR-C: mobile/web renders a read-only "现场证据复跑执行结果复核决策" panel that explains the review decision, next required evidence, and fail-closed flags without enabling Start Delivery / Confirm Dropoff / Cancel.
- KR-D: Product closeout later updates sprint evidence and OKR conservatively only after Engineers return implementation proof; no planning document can be counted as business completion.

## Core Lever

Advance the explicit evidence ladder from `field_evidence_rerun_execution_result_intake` to `field_evidence_rerun_execution_result_review_decision`. The lever is a fail-closed review decision over an accepted result packet, not a real field rerun, not a real delivery result, and not a reviewer-resolved PR #5 thread.

## Owner Plan

- Autonomy Algorithm Engineer owns the PC review-decision gate and canonical safe artifact.
- Robot Platform Engineer owns the diagnostics safe alias.
- User Touchpoint Full-Stack Engineer owns the phone-safe read-only panel.
- Product Manager / OKR Owner owns later closeout, OKR/progress log conservatism, and sprint record completion after implementation.

## Risks And Blockers

- No real hardware is available on this host; this is Docker/local `software_proof` only.
- Missing real evidence remains: real field rerun, real task record, real Nav2/fixed-route runtime log, route completion signal, real elevator door/floor proof, human assistance note, dropoff/cancel completion, delivery result, true phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, WAVE ROVER/UART/HIL, and PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution.
- Rejected or blocked review decisions must remain actionable but cannot unlock robot motion or product completion claims.

## Sprint Documents

Create now:

- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/pre_start.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/prd.md`
- `sprints/2026.05.21_08-09_field-evidence-rerun-execution-result-review-decision/tech-plan.md`

Do not create implementation closeout documents during this planning-only step:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
