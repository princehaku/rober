# Field Evidence Rerun Queue PRD

## Product North Star

`rober` must become a phone-first trash delivery robot whose claims are backed by replayable task evidence. The next useful product step is to make a controlled field rerun schedulable and auditable without pretending that the rerun has already passed.

## Problem

The previous `field_evidence_rerun_handoff_intake` sprint made owner-safe handoff receipts visible across PC, Robot diagnostics, and mobile/web. It did not yet answer a practical operator question:

Can this handoff intake be queued as a controlled field rerun candidate, and what exact real-world materials are still required before any route/elevator or delivery result can be reviewed?

Without a queue candidate, support and field owners still read scattered blockers: task record missing, Nav2/fixed-route runtime missing, route completion missing, elevator and dropoff evidence missing, and phone/browser evidence missing. That makes the next field attempt hard to schedule and easy to overclaim.

## Users

- Field owner: needs a clear, metadata-only queue candidate and required material checklist before running a controlled field rerun.
- PC support operator: needs a deterministic gate that says whether handoff intake can become a queue candidate.
- Robot diagnostics consumer: needs a redacted safe alias that other surfaces can consume without raw artifacts or control details.
- Phone/mobile reviewer: needs to see that a rerun is queued or blocked, while primary actions stay disabled until real safe control is available.

## OKR Mapping

| Objective | Mapping | Product decision |
| --- | --- | --- |
| Objective 2 | Route/elevator delivery chain needs real rerun materials before delivery state can advance. | Targeted indirectly by queue readiness, not by claiming delivery pass. |
| Objective 3 | Fixed-route/Nav2 proof needs runtime log, route completion signal, and same-`evidence_ref` reconciliation. | Targeted directly by required queue evidence. |
| Objective 4 | Phone surface must explain rerun queue state to non-technical users without exposing raw diagnostics. | Targeted directly by read-only panel. |
| Objective 1 | PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending; `3269642220` is not HIL or hardware proof. | No progress claim. |
| Objective 5 | Completion is about 68% and lowest, but external materials are absent on this Docker-only host. | No new local O5 depth; no external-proof claim. |

## KR Breakdown

1. A canonical `field_evidence_rerun_queue` PC artifact exists and can classify queue state as metadata-only, not control-ready.
2. The artifact preserves safe lineage from `field_evidence_rerun_handoff_intake`, including same safe `evidence_ref`.
3. The artifact lists the required real materials before review: real task record, Nav2/fixed-route runtime log, route completion signal, elevator door state, target floor confirmation, human assistance record, dropoff/cancel completion, delivery result, and real phone/browser evidence.
4. Robot diagnostics exposes a safe alias for the queue summary without raw ROS topics, `/cmd_vel`, serial/UART details, credentials, local paths, complete artifacts, checksums, or success claims.
5. Mobile/web shows a read-only field rerun queue panel and keeps Start Delivery, Confirm Dropoff, and Cancel disabled unless existing unrelated command-safety gates explicitly allow them.
6. Product closeout records the evidence boundary as `software_proof_docker_field_evidence_rerun_queue_gate` and keeps `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Scope

In scope for the implementation sprint:

- Autonomy PC gate for `field_evidence_rerun_queue`.
- Robot diagnostics safe alias for queue summary.
- Full-stack mobile/web read-only queue panel and fixture/test/docs updates.
- Fenced tests and static checks for the three surfaces.
- Sprint closeout docs and conservative OKR/progress updates after evidence lands.

Out of scope:

- Real route/elevator field execution.
- Real Nav2/fixed-route runtime proof.
- Real WAVE ROVER/UART/HIL proof.
- Real iPhone/Android or production app/browser validation.
- Public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or O5 external proof.
- Resolving PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Enabling Start Delivery, Confirm Dropoff, Cancel, ACK/cursor, or robot command side effects from the queue panel.

## Functional Requirements

- The queue artifact must consume a handoff intake artifact or safe summary from the previous rung.
- Missing or mismatched `evidence_ref` must fail closed.
- The output must include queue status, blocker summary, next required evidence, owner handoff, same-`evidence_ref` status, and safe copy.
- The output must include `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- The output must use `software_proof_docker_field_evidence_rerun_queue_gate` as the evidence boundary.
- Robot and mobile consumers must prefer the Robot diagnostics safe alias when present.
- Mobile/web must render the queue state in Chinese-first product copy and must not expose raw JSON, ROS topics, serial/UART paths, credentials, traces, checksums, or complete artifacts.

## Acceptance Criteria

- Autonomy worker returns changed files, validation outputs, and any remaining risk for the PC gate.
- Robot worker returns changed files, validation outputs, and any remaining risk for the diagnostics alias.
- Full-stack worker returns changed files, validation outputs, and any remaining risk for the mobile/web panel.
- Product closeout confirms that the implementation did not claim real field pass, HIL, delivery success, O5 external proof, true phone/browser proof, or PR #5 resolved.
- `OKR.md` progress only changes if the implemented evidence genuinely moves a KR; otherwise it must record the new software-proof boundary without increasing completion.

## Evidence Chain Still Needed After This Sprint

- Real task record.
- Real Nav2/fixed-route runtime log.
- Route completion signal.
- Real elevator door and target-floor evidence.
- Real human assistance record.
- Real dropoff completion and cancel completion material.
- Delivery result from a controlled route/elevator run.
- Real phone/browser evidence for the same safe `evidence_ref`.
- Separate O1 materials: WAVE ROVER/UART/HIL and real 2D LiDAR/ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry.
- Separate O5 materials: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and external phone/browser proof.

## Responsibility

- Autonomy Algorithm Engineer: PC gate and canonical queue artifact.
- Robot Platform Engineer: diagnostics safe alias and Robot-facing tests.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel, fixtures, and phone-safe docs.
- Product Manager / OKR Owner: closeout, evidence boundary review, `OKR.md` and progress-log updates after engineering evidence lands.
