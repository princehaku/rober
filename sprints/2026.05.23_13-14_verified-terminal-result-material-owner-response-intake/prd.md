# Verified Terminal Result Material Owner Response Intake PRD

Run time: 2026-05-23 13:14 Asia/Shanghai

## Product North Star

`rober` should make trash delivery observable and supportable for ordinary phone users. A user or support owner should not need raw ROS2, cloud logs, terminal ACK payloads, serial details, or hardware debug access to understand whether a terminal result is still waiting on real evidence.

## Problem

The previous sprint created `verified_terminal_result_material_followup_escalation_status`, which makes missing verified terminal-result material visible. The next product gap is intake: when a field owner or support owner responds with backfill material, the product needs a safe place to classify that response without converting it into real delivery proof.

Without this intake, support can see that material is missing but cannot safely capture whether the response is accepted, missing, rejected, unsafe, blocked, or mismatched to the original `evidence_ref`.

## Target Capability

`verified_terminal_result_material_owner_response_intake`

The capability consumes a prior follow-up escalation status plus optional sanitized owner response metadata and emits a safe summary for PC tools, Robot diagnostics, and mobile/web. It must keep all primary controls disabled and must preserve:

- `source=software_proof`
- `software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `no OKR percentage lift`
- `software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`

## Users

- Field owner: provides terminal delivery/dropoff/cancel material references under the same safe `evidence_ref`.
- Support owner: checks whether the owner response is complete enough for review or still blocked.
- Reviewer: later decides whether accepted intake material can proceed to review decision/handoff.
- Phone user: only sees safe, read-only support status; no primary action should be enabled by this panel.

## OKR Mapping

- Primary Objective: Objective 5, because terminal-result material intake is part of cloud/phone/operator reliability and supportability.
- Current priority: Objective 5 is about 68%, the lowest current Objective; this sprint directly targets it.
- Expected progress: `no OKR percentage lift`, because Docker/local intake readiness is not real external proof or real terminal result proof.
- Objective 1 stays about 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / `hardware_material_pending`.
- Objective 2/3/4 stay about 99%; no route/elevator field pass, Nav2/fixed-route runtime pass, true phone/browser proof, or real delivery/dropoff/cancel result is produced.

## KR Breakdown

1. Add a PC-only owner response intake gate that accepts safe prior follow-up status and sanitized response material metadata.
2. Add Robot diagnostics safe alias so downstream support/mobile surfaces can consume the same summary.
3. Add a mobile/web read-only panel showing owner response intake status without enabling Start Delivery, Confirm Dropoff, Cancel, or any control path.
4. Preserve the evidence boundary and forbidden-claim list across interface docs, runtime docs, product docs, tests, and closeout.
5. Close with Task D only after worker validation evidence is present.

## Acceptance Criteria

The sprint is acceptable when:

- PC gate can classify owner response material into accepted, missing, rejected, unsafe, or blocked states while preserving the same safe `evidence_ref`.
- Robot diagnostics exposes a safe summary alias and never emits control authorization.
- Mobile/web renders the summary as read-only, with `primary_actions_enabled=false` and `safe_to_control=false`.
- Tests prove missing, mismatched, unsafe, and accepted-safe paths remain fail-closed.
- Docs state that this is `software_proof` / `not_proven` and `no OKR percentage lift`.
- Closeout explicitly records that PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved.

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
- PR #5 resolution
- delivery success

## Product Copy Requirements

Use clear support-facing language:

- "Owner response intake received, still not proven."
- "Same evidence_ref required before review."
- "Material accepted for review queue, not delivery success."
- "Material missing or unsafe; robot controls remain disabled."

Avoid copy that says or implies "delivered", "dropoff succeeded", "cancel completed", "field passed", "HIL passed", "phone passed", or "PR #5 resolved".

## Responsibility

- Autonomy Algorithm Engineer: PC gate, tests, interface doc, README.
- Robot Platform Engineer: diagnostics safe alias, tests, runtime/interface docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, tests, product docs.
- Product Manager / OKR Owner: closeout and OKR/progress log after A/B/C evidence returns.

## Evidence Chain

Input chain:

`verified_terminal_result_material_followup_escalation_status` with `software_proof_docker_verified_terminal_result_material_followup_escalation_status_gate`

Output chain:

`verified_terminal_result_material_owner_response_intake` with `software_proof_docker_verified_terminal_result_material_owner_response_intake_gate`

Downstream chain:

Future review-decision and review-handoff work may consume this intake only if it preserves the same safe `evidence_ref` and still avoids real delivery-success claims.
