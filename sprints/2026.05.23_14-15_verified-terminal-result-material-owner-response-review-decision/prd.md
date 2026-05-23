# Verified Terminal Result Material Owner Response Review Decision PRD

Run time: 2026-05-23 14:15 Asia/Shanghai

## Product North Star

`rober` should make trash delivery observable and supportable for ordinary phone users. A user or support owner should never need raw ROS2, cloud logs, ACK payloads, serial details, or hardware debug access to understand that terminal-result material is still unproven and blocked on reviewable evidence.

## Problem

The previous sprint created `verified_terminal_result_material_owner_response_intake`, which safely captures owner response/backfill metadata for verified terminal-result material. The next product gap is review decision: support can see that owner material was received, but cannot yet classify whether it is accepted for the next handoff, still missing, rejected, unsafe, mismatched, or blocked.

Without this review-decision rung, downstream workers may accidentally treat intake presence as proof. That would weaken the boundary between "material received" and "verified delivery/dropoff/cancel result".

## Target Capability

`verified_terminal_result_material_owner_response_review_decision`

The capability consumes prior `verified_terminal_result_material_owner_response_intake` safe metadata and emits a safe review-decision summary for PC tools, Robot diagnostics, and mobile/web. It must keep all primary controls disabled and must preserve:

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`
- `software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`

## Users

- Field owner: sees why submitted terminal-result material is accepted for next review/handoff, still missing, rejected, unsafe, or blocked.
- Support owner: decides what safe evidence must be requested next without exposing raw artifacts or enabling controls.
- Reviewer: consumes a conservative review-decision packet before any future review-handoff rung.
- Phone user: only sees read-only support status; no Start Delivery, Confirm Dropoff, Cancel, ACK, cursor, replay, resubmit, or review route should become available.

## OKR Mapping

- Primary Objective: Objective 5, because terminal-result material review is part of cloud/phone/operator reliability and supportability.
- Current priority: Objective 5 is about 68%, the lowest current Objective; this sprint directly targets it.
- Expected progress: `no OKR percentage lift`, because Docker/local review-decision readiness is not real external proof, true phone/browser proof, or real terminal result proof.
- Objective 1 stays about 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`.
- Objective 2/3/4 stay about 99%; no route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser proof, verified terminal delivery/dropoff/cancel result, or delivery success is produced.

## KR Breakdown

1. Add a PC-only owner-response review-decision gate that consumes prior owner response intake safe metadata.
2. Add Robot diagnostics safe alias so downstream support/mobile surfaces can consume the same review-decision summary.
3. Add a mobile/web read-only panel showing review-decision status without enabling Start Delivery, Confirm Dropoff, Cancel, or any control path.
4. Preserve the evidence boundary and forbidden-claim list across interface docs, runtime docs, product docs, tests, and closeout.
5. Close with Task D only after worker validation evidence is present.

## Acceptance Criteria

The sprint is acceptable when:

- PC gate can classify owner response intake as accepted-for-handoff, missing, rejected, unsafe, evidence-ref-mismatched, or blocked while preserving the same safe `evidence_ref`.
- Robot diagnostics exposes a safe summary alias and never emits control authorization.
- Mobile/web renders the summary as read-only, with `primary_actions_enabled=false` and `safe_to_control=false`.
- Tests prove missing, mismatched, unsafe, rejected, and accepted-for-handoff paths remain fail-closed.
- Docs state that this is `software_proof` / `not_proven` and `no OKR percentage lift`.
- Closeout explicitly records that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved unless live evidence changes before closeout.

## Non Goals

This sprint must not claim or imply:

- real terminal delivery/dropoff/cancel result
- O5 external proof
- true phone/browser proof
- public HTTPS/TLS
- 4G/SIM
- OSS/CDN live traffic
- production DB/queue
- worker/cutover
- route/elevator field pass
- Nav2/fixed-route runtime pass
- HIL
- WAVE ROVER/UART proof
- real 2D LiDAR/ToF installed proof
- PR #5 resolution
- delivery success

## Product Copy Requirements

Use clear support-facing language:

- "Owner response reviewed, still not proven."
- "Accepted for next handoff, not delivery success."
- "Same evidence_ref required before any further review."
- "Material missing, rejected, unsafe, or mismatched; robot controls remain disabled."

Avoid copy that says or implies "delivered", "dropoff succeeded", "cancel completed", "field passed", "HIL passed", "phone passed", "external cloud proven", or "PR #5 resolved".

## Responsibility

- Autonomy Algorithm Engineer: PC gate, tests, interface doc, README.
- Robot Platform Engineer: diagnostics safe alias, tests, runtime/interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, tests, product docs.
- Product Manager / OKR Owner: closeout and OKR/progress log after A/B/C evidence returns.

## Evidence Chain

Input chain:

`verified_terminal_result_material_owner_response_intake` with `software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`

Output chain:

`verified_terminal_result_material_owner_response_review_decision` with `software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate`

Downstream chain:

Future review-handoff work may consume this review decision only if it preserves the same safe `evidence_ref`, keeps every primary/control flag disabled, and still avoids real delivery-success or O5 external-proof claims.
