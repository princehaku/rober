# PRD: cloud external evidence review handoff

- sprint_type: epic
- target capability: `cloud_external_evidence_review_handoff`
- upstream capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_gate`
- closeout expectation: `no OKR percentage lift`

## Problem

The previous sprint added `cloud_external_evidence_review_decision`, which can classify future `trashbot.external_evidence_intake` materials as accepted, needs backfill, rejected unsafe, blocked, or evidence-ref mismatch. That is useful, but it still leaves a product gap: a decision without an owner/support/reviewer handoff is easy to lose, misroute, or overclaim.

Objective 5 is still lowest at about 68%. The missing work is real external evidence: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, WAVE ROVER/UART proof, route/elevator field pass, and delivery success. This host has Docker only, so the sprint must not pretend those gaps are closed.

## User Value And Product North Star

North star: ordinary users should eventually control a trash delivery robot from a phone through a safe cloud relay, without needing local WiFi, SSH, ROS2, serial logs, or raw diagnostics.

Current user value: support and reviewers get deterministic routing metadata for O5 external-evidence review outcomes. If a future public HTTPS/TLS or OSS/CDN material is accepted, the handoff says who owns the next step. If it needs backfill, is unsafe, blocked, or mismatched, the handoff says what evidence is missing and keeps phone controls disabled.

## OKR Mapping

| OKR | Product interpretation |
| --- | --- |
| Objective 5 KR1 | Handoff must not expose `/cmd_vel` or inbound robot control; it routes review metadata only. |
| Objective 5 KR2 | Handoff should point support toward cloud infrastructure evidence families without claiming the 4C 8G production baseline is live. |
| Objective 5 KR3/KR4 | OSS/CDN evidence references remain safe/redacted; no raw artifact bodies or credentials. |
| Objective 5 KR5 | Unsafe materials with credentials, secrets, raw endpoints, or full artifacts are rejected and routed for remediation. |
| Objective 5 KR6 | Missing or degraded external evidence routes to backfill/support, while the product remains fail closed. |

This sprint does not change Objective 1/2/3/4 percentages. It also does not lift Objective 5 because the result is Docker/local `software_proof`, not real external proof.

## KR Breakdown For This Sprint

1. Define a canonical `cloud_external_evidence_review_handoff` packet after `cloud_external_evidence_review_decision`.
2. Preserve supported source outcomes: accepted / needs backfill / rejected unsafe / blocked / evidence-ref mismatch.
3. Include safe owner/support/reviewer routing fields and next-required-evidence fields.
4. Preserve false-state fields: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
5. Preserve evidence boundary fields: `source=software_proof`, `not_proven`, `Docker`, `not true phone/browser proof`, `no OKR percentage lift`.
6. Keep PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` as unresolved `hardware_material_pending` evidence input only.
7. Keep phone/support UI read-only; no Start Delivery, Confirm Dropoff, Cancel, ACK/cursor mutation, raw artifact fetch, GitHub mutation, replay, or robot control route.

## Scope

In scope for the implementation sprint:

- PC evidence gate and fixtures for `cloud_external_evidence_review_handoff`.
- Robot diagnostics safe alias for the handoff summary.
- `mobile/web` read-only panel and fixture.
- Related product/interface docs updated by the implementation owners after code lands.
- Sprint closeout docs and conservative OKR closeout after Task A/B return.

Out of scope:

- No public HTTPS/TLS deployment.
- No production DB/queue, worker/cutover, or 4G/SIM validation.
- No OSS/CDN live traffic claim.
- No true phone/browser proof.
- No HIL, WAVE ROVER/UART, route/elevator field pass, or delivery success.
- No PR #5 hardware-source wrapper or claim that `PRRT_kwDOSWB9286CJ3tX` is resolved.
- No product code implementation during this planning task.

## Acceptance Criteria

Planning is accepted when:

- `pre_start.md`, `prd.md`, and `tech-plan.md` exist in the fresh sprint folder.
- The plan names `cloud_external_evidence_review_handoff`, `cloud_external_evidence_review_decision`, `software_proof_docker_cloud_external_evidence_review_handoff_gate`, Objective 5, Docker/local proof, PR #5 `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, `not true phone/browser proof`, `no OKR percentage lift`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- `tech-plan.md` includes owner/file split, interface boundaries, verification commands, and `## OKR 最低优先级核对`.

Implementation will be accepted later only if Task A and Task B return focused validation evidence and Product closeout records the boundary as `software_proof`, not external proof.

## Risks And Evidence Gaps

- Handoff metadata can be mistaken for O5 external proof unless every surface repeats `no OKR percentage lift`.
- Read-only phone/support surfaces can be mistaken for true phone/browser proof unless final copy says this is Docker/local only.
- PR #5 `hardware_material_pending` can distract the sprint back into hardware wrappers; this sprint must use it only as unresolved evidence context.
- No real cloud materials are available on this host, so Objective 5 remains blocked for actual percentage lift.

