# Field Evidence Rerun Execution Callback Review Handoff Pre-start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff`
- Target capability: `field_evidence_rerun_execution_callback_review_handoff`
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_review_handoff_gate`
- Required preserved states: `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning scope: create planning docs only; no product code, tests, `OKR.md`, `docs/`, or previous sprint files are changed in this planning step.

## User Value And Product North Star

The product north star remains a low-cost ROS2 trash delivery robot that an ordinary phone user can operate without ROS2, SSH, serial tools, or hardware knowledge. This sprint does not prove real trash delivery. It keeps the field evidence rerun chain moving by turning the previous execution callback review decision into a bounded owner handoff: who owns the next action, what same-safe-`evidence_ref` evidence must be collected next, and how to rerun or reconcile without claiming field success.

## Required Evidence Inputs

- `OKR.md` 4.1 currently shows Objective 5 as the lowest Objective at about 68%, but this Docker-only host has no real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser external proof. Recent O5 local guards are already metadata/software proof, so this sprint must not add another same-class O5 blocker wrapper.
- Objective 1 is about 81%, but PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` and requires mandatory sensor baseline vendor/source materials. This host has no real hardware, WAVE ROVER/UART/HIL, or real 2D LiDAR / ToF materials.
- PR #5 has been merged. Review threads `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved; `PRRT_kwDOSWB9286CJ3tX` is unresolved. Conservative reply comment id `3269642220` exists, but it is not thread resolution and not hardware proof.
- PR #6 is README/docs-only and has no review threads. It is not runtime, hardware, HIL, phone/browser, or O5 external proof.
- Previous sprint `sprints/2026.05.21_02-03_field-evidence-rerun-execution-callback-review-decision/final.md` says the next useful action is real same-safe-`evidence_ref` materials; if those are absent, only an explicitly bounded software-proof handoff/reconciliation rung is valid.

## Why This Sprint

The current lowest Objective, Objective 5, cannot advance without external materials. Objective 1 also cannot advance without real mandatory sensor baseline materials. The next actionable family is the O2/O3/O4 field-evidence rerun ladder, because it can improve owner handoff and evidence hygiene while preserving the boundary that nothing here proves delivery, HIL, route execution, phone behavior, or external cloud readiness.

## Owners And Parallel Plan

- Autonomy Algorithm Engineer: PC handoff gate and canonical artifact/summary.
- Robot Platform Engineer: diagnostics safe alias for the handoff summary.
- User Touchpoint Full-Stack Engineer: read-only mobile panel for owner handoff, next evidence, and rerun guidance.
- Product Manager / OKR Owner: sprint planning docs, scope boundary, and later closeout evidence if implementation proceeds.

This is an epic because it crosses three Engineer owner surfaces and requires parallel worker execution after planning.

## Risks, Blockers, And Evidence Gaps

- Real same-safe-`evidence_ref` materials remain missing: task record, Nav2/fixed-route runtime log, route completion signal, elevator door state, target floor confirmation, human assistance record, dropoff/cancel completion, delivery result, and true phone/browser field material.
- O5 remains blocked on external public/cloud/mobile evidence.
- O1 remains blocked on mandatory PR #5 sensor baseline vendor/source/procurement/installation/calibration/HIL-entry materials.
- The sprint must keep `source=software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false` in every surface.
- `field_evidence_rerun_execution_callback_review_handoff` must be presented only as owner handoff / next evidence / rerun guidance, not as field pass or delivery success.

## Sprint Documents To Create

- `pre_start.md`: this sprint start, evidence inputs, owner routing, and blocker boundary.
- `prd.md`: user value, OKR mapping, KR breakdown, non-claims, and acceptance language.
- `tech-plan.md`: three parallel worker scopes, allowed file ranges, implementation requirements, and fenced validation commands.
