# Field Evidence Rerun Execution Callback Intake PRD

## Product North Star

`rober` must be a phone-first trash delivery robot whose route/elevator delivery claims are backed by replayable field evidence. The next useful step is not another local wrapper around missing proof; it is a strict intake surface for the field owner's execution callback packet after the `field_evidence_rerun_execution_pack`.

## Problem

The latest `field_evidence_rerun_execution_pack` sprint produced a metadata-only execution package and made it visible across PC, Robot diagnostics, and mobile/web. It still did not consume a field owner execution callback packet.

Without callback intake, real-world follow-through can fail quietly: field owner may return a task record for the wrong `evidence_ref`, omit the Nav2/fixed-route runtime log, provide an unverifiable route completion signal, miss elevator door/floor/human-assistance evidence, omit dropoff/cancel completion, or submit phone/browser evidence that cannot be reconciled. The product need is a deterministic gate that classifies each returned material as accepted, missing, rejected, or blocked.

## Users

- Field owner: needs a clear callback packet shape and immediate classification of submitted materials.
- PC support operator: needs a deterministic gate that consumes execution pack plus callback packet and emits safe intake state.
- Robot diagnostics consumer: needs a redacted safe alias that other consumers can trust without raw artifacts or command capability.
- Phone/mobile reviewer: needs Chinese-first read-only visibility into callback status while primary actions remain disabled.
- Product owner: needs evidence wording that separates callback-intake readiness from real route/elevator pass, HIL, phone/browser proof, and O5 external proof.

## OKR Mapping

| Objective | Mapping | Product decision |
| --- | --- | --- |
| Objective 2 | Route/elevator delivery chain needs real controlled rerun materials before delivery state can advance. | Targeted indirectly through callback material classification, not by claiming delivery pass. |
| Objective 3 | Fixed-route/Nav2 proof needs runtime log, route completion signal, task record, and same-`evidence_ref` reconciliation. | Targeted directly through accepted/missing/rejected/blocked classification. |
| Objective 4 | Phone surface must explain field callback status to non-technical users without exposing raw diagnostics. | Targeted directly by read-only panel. |
| Objective 1 | PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and requests vendor sources for mandatory sensor assumptions. | No progress claim. |
| Objective 5 | Completion is about 68% and lowest, but external materials are absent on this Docker-only host. | No local O5 progress claim. |

## KR Breakdown

1. A canonical `field_evidence_rerun_execution_callback_intake` PC artifact exists and consumes both `field_evidence_rerun_execution_pack` and a field owner execution callback packet.
2. The artifact preserves one safe `evidence_ref` and rejects missing, mismatched, or unsafe evidence refs.
3. The artifact classifies required field materials into `accepted_materials`, `missing_materials`, `rejected_materials`, and `blocked_materials`.
4. Required material categories cover task record, Nav2/fixed-route runtime log, route completion signal, elevator door state, target floor confirmation, human assistance record, dropoff completion, cancel completion, delivery result, and real phone/browser evidence.
5. Robot diagnostics exposes `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary` without raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, credentials, local paths, complete artifacts, checksums, tracebacks, or success/control claims.
6. Mobile/web shows a read-only "现场证据复跑执行回执入口" panel and keeps Start Delivery, Confirm Dropoff, Cancel, ACK/cursor, execution scheduling, and robot command side effects out of this panel.
7. Product closeout records `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.

## Scope

In scope for implementation:

- PC gate `pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py`.
- Focused test `tests/test_field_evidence_rerun_execution_callback_intake.py`.
- `pc-tools/README.md` and `docs/interfaces/evidence_contracts.md`.
- Robot diagnostics safe alias in existing diagnostics files, focused diagnostics tests, and `docs/interfaces/ros_runtime_contracts.md`.
- Mobile/web read-only "现场证据复跑执行回执入口" panel, fixture/test, and `docs/product/mobile_user_flow.md`.
- Product closeout later in `OKR.md`, `docs/process/okr_progress_log.md`, `tech-done.md`, `side2side_check.md`, and `final.md`.

Out of scope:

- Real field rerun execution.
- Real Nav2 or fixed-route runtime proof.
- Real route/elevator field pass.
- Real task record generation.
- Real route completion signal generation.
- Real elevator, floor, or human-assistance proof generation.
- Real dropoff/cancel completion or delivery success.
- Real WAVE ROVER/UART/HIL.
- Real iPhone/Android browser/device acceptance.
- Public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or O5 external proof.
- Resolving PR #5 `PRRT_kwDOSWB9286CJ3tX`.

## Functional Requirements

- The PC gate must consume a prior `field_evidence_rerun_execution_pack` artifact or summary.
- The PC gate must consume a field owner execution callback packet from a local JSON path or fixture.
- The gate must fail closed if the execution pack state is missing, unsafe, not from `software_proof`, not `not_proven`, has mismatched `evidence_ref`, or carries success/control claims.
- The gate must validate callback packet schema, callback source, safe `evidence_ref`, material categories, redaction status, and no-success/no-control wording.
- The gate must output accepted, missing, rejected, and blocked material groups with owner-facing next required evidence.
- Accepted material classification is review eligibility only. It must not set `delivery_success=true`, `safe_to_control=true`, `primary_actions_enabled=true`, or any field-pass wording.
- Robot and mobile consumers must prefer the Robot diagnostics safe alias when present.
- Mobile/web must render Chinese-first product copy and must not expose raw JSON, ROS topics, serial/UART paths, credentials, tracebacks, checksums, full artifacts, or control authorization.

## Acceptance Criteria

- Autonomy worker returns changed files, validation outputs, failures if any, and remaining risk for the PC gate.
- Robot worker returns changed files, diagnostics validation outputs, failures if any, and remaining risk for the safe alias.
- Full-stack worker returns changed files, mobile validation outputs, failures if any, and remaining risk for the read-only panel.
- Product closeout confirms implementation did not claim real现场复跑、真实 Nav2、真实 route/elevator field pass、HIL、O5 external proof、真实 phone/browser proof、PR #5 resolved, or delivery success.
- `OKR.md` progress only changes if real external/material evidence appears and has a separate proof boundary; otherwise it records only the new software-proof callback-intake boundary.

## Evidence Chain Still Needed After This Sprint

- Real task record for the same safe `evidence_ref`.
- Real Nav2/fixed-route runtime log.
- Route completion signal.
- Real elevator door state, target-floor confirmation, and human assistance record.
- Real dropoff completion and cancel completion material.
- Delivery result from a controlled route/elevator run.
- Real phone/browser evidence for the same safe `evidence_ref`.
- Separate O1 materials: WAVE ROVER/UART/HIL plus real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry.
- Separate O5 materials: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, and external phone/browser proof.

## Responsibility

- Autonomy Algorithm Engineer: PC gate, canonical callback-intake schema, focused tests, PC README, and evidence contract.
- Robot Platform Engineer: diagnostics safe alias, focused diagnostics tests, and ROS runtime contract.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel, fixture/test, and mobile user flow doc.
- Product Manager / OKR Owner: later closeout, OKR/progress log update, evidence-boundary review, and sprint final.
