# Field Evidence Rerun Queue Pre-Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.20_17-18_field-evidence-rerun-queue`
- Planned start: 2026-05-20 17:00 Asia/Shanghai
- Product owner: Product Manager / OKR Owner
- Required implementation workers: Autonomy Algorithm Engineer, Robot Platform Engineer, User Touchpoint Full-Stack Engineer
- Product closeout: after the three Engineer workers return implementation and validation evidence
- Scope: planning only in this handoff. Engineering implementation is explicitly out of scope for these three documents.

## User Value And Product North Star

The north star remains a phone-first, low-cost ROS2 trash delivery robot that can prove a delivery attempt through replayable evidence rather than through optimistic demo claims.

This sprint should turn the previous owner-safe `field_evidence_rerun_handoff_intake` output into a metadata-only controlled field rerun queue candidate. The value is operational: PC support, Robot diagnostics, and the phone-safe mobile/web surface can agree on the same safe `evidence_ref`, the same queue state, the same missing real-world materials, and the same fail-closed boundary before anyone schedules a controlled field rerun.

This is not the field rerun itself. The queue candidate must remain `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Evidence Basis

- `OKR.md` 4.1 reports Objective 5 at about 68%, the lowest current completion. The Docker-only host still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, and real phone/browser external proof. Continuing local O5 metadata depth would repeat a blocked path instead of moving user-visible delivery evidence forward.
- `OKR.md` 4.1 reports Objective 1 at about 81%. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending, and manual GitHub reply `3269642220` is only a published software-proof reply, not hardware proof.
- Local machine evidence still lacks WAVE ROVER/UART/HIL, real `feedback_T1001.log`, real `/odom`, `/imu/data`, `/battery`, operator HIL report, and real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry material.
- Live PR #5 evidence from GitHub: PR #5 was merged on 2026-05-14. The review thread list still shows `PRRT_kwDOSWB9286CJ3tX` as `is_resolved=false`, while the earlier review concerns included default hardware set vs mandatory 2D LiDAR/ToF contradiction, missing vendor source attribution for mandatory sensor assumptions, and an OKR lowest-objective claim/table mismatch.
- Live PR #6 evidence from GitHub: PR #6 was merged on 2026-05-20. It rewrote the README product narrative and its testing notes were documentation diff/status checks only; no code, runtime, hardware, HIL, real phone, or external cloud tests were run.
- Previous sprint `2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md` closed `software_proof_docker_field_evidence_rerun_handoff_intake_gate` but still listed the missing real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor/human assistance evidence, dropoff/cancel completion, delivery result, and real phone/browser evidence.

## OKR Mapping

- Objective 2: primary beneficiary. The queue candidate should make the next controlled route/elevator field rerun explicit and auditable, while preserving that no real delivery success has happened yet.
- Objective 3: primary beneficiary. The queue candidate should require real Nav2/fixed-route runtime log, route completion signal, route material, and same-`evidence_ref` reconciliation before any result can be reviewed.
- Objective 4: supporting beneficiary. The phone-safe read-only panel should explain queue state and missing materials without enabling Start Delivery, Confirm Dropoff, or Cancel.
- Objective 1: remains blocked for progress until real WAVE ROVER/UART/HIL and PR #5 2D LiDAR/ToF materials arrive. This sprint must not claim O1 progress from `3269642220`.
- Objective 5: remains lowest numerically but not actionable on this host. This sprint must not claim O5 external proof.

## KR Breakdown

- KR-Autonomy: create a PC gate contract for `field_evidence_rerun_queue` that consumes the previous handoff intake summary and emits a controlled rerun queue candidate with required evidence categories and same-`evidence_ref` checks.
- KR-Robot: expose a diagnostics safe alias for the queue candidate, with redacted metadata only and no control grant.
- KR-Full-stack: expose a mobile/web read-only panel for queue state, blocker summary, next required evidence, and the new evidence boundary.
- KR-Product: after engineering evidence lands, update sprint closeout docs and OKR/progress log conservatively; keep Objective 5 and Objective 1 boundaries unchanged unless real materials appear.

## Core Lever

The core lever is not another blocker wrapper. It is a queue readiness contract that says whether the existing handoff intake is safe to schedule for a controlled field rerun, while still blocking control and success claims until real materials return.

Suggested new evidence boundary: `software_proof_docker_field_evidence_rerun_queue_gate`.

## Priority And Acceptance

Priority order:

1. Autonomy PC gate defines the canonical queue candidate schema and CLI behavior.
2. Robot diagnostics safe alias consumes only the safe summary and keeps sensitive/raw data out.
3. Full-stack mobile/web renders queue state read-only and preserves existing primary-action gating.
4. Product closeout verifies the boundary, updates sprint docs, and only updates OKR progress if evidence actually supports it.

Acceptance requires all surfaces to preserve:

- `source=software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- evidence boundary `software_proof_docker_field_evidence_rerun_queue_gate`

## Risks And Blockers

- O5 remains blocked by missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and external phone/browser proof.
- O1 remains blocked by missing WAVE ROVER/UART/HIL and PR #5 real 2D LiDAR/ToF materials. `PRRT_kwDOSWB9286CJ3tX` must remain unresolved/material pending until reviewer and real materials change that state.
- O2/O3/O4 still lack real task record, Nav2/fixed-route runtime log, route completion signal, elevator door/floor/human assistance evidence, dropoff/cancel completion, delivery result, and true phone/browser evidence.
- The implementation sprint must not convert queue readiness into route/elevator field pass, HIL, real phone/browser acceptance, delivery success, O5 external proof, or PR #5 resolved.

## Sprint Documents To Create Or Update

This planning handoff creates:

- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/pre_start.md`
- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/prd.md`
- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-plan.md`

The implementation closeout must later create or update:

- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/tech-done.md`
- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/side2side_check.md`
- `sprints/2026.05.20_17-18_field-evidence-rerun-queue/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
- relevant docs under `docs/`, especially mobile/product or evidence contract docs touched by Engineering
