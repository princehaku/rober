# PRD: cloud external evidence review handoff followup escalation status

- sprint_type: epic
- target capability: `cloud_external_evidence_review_handoff_followup_escalation_status`
- upstream capability: `cloud_external_evidence_review_handoff`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`
- closeout expectation: `software_proof`, `not_proven`, `no OKR percentage lift`

## Problem

The latest sprint completed `cloud_external_evidence_review_handoff`, which packages `cloud_external_evidence_review_decision` outcomes into owner/support/reviewer routing metadata. That is useful, but it still leaves an accountability gap: a handoff can remain unacted on unless the product shows due status, blocked reason, owner action, and whether CEO escalation is recommended.

Objective 5 remains the lowest OKR area at about 68%. The missing OKR-lifting evidence is still real external proof: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, WAVE ROVER/UART proof, route/elevator field pass, and delivery success. This host has Docker only, so this sprint must stay a software accountability rung and must not claim those gaps are closed.

## User Value And Product North Star

North star: ordinary users should eventually control a trash delivery robot from a phone through a safe cloud relay, without needing local WiFi, SSH, ROS2, serial logs, or raw diagnostics.

Current user value: support, owner, reviewer, and CEO can see whether the previous O5 handoff has a live follow-up path. If due, the owner action is explicit. If overdue or blocked, the blocked reason and escalation recommendation are visible. If still waiting on real external evidence or PR #5 `PRRT_kwDOSWB9286CJ3tX` materials, the UI and diagnostics remain fail closed and preserve `hardware_material_pending`.

## OKR Mapping

| OKR | Product interpretation |
| --- | --- |
| Objective 5 KR1 | Follow-up status must not expose `/cmd_vel` or inbound robot control; it routes O5 cloud evidence accountability only. |
| Objective 5 KR2 | Status should name missing cloud infrastructure proof without claiming the 4C 8G production baseline is live. |
| Objective 5 KR3/KR4 | OSS/CDN evidence references remain safe/redacted; no raw artifact bodies, signed URLs, or credentials. |
| Objective 5 KR5 | Unsafe materials with credentials, secrets, raw endpoints, or complete artifacts remain blocked and routed for remediation. |
| Objective 5 KR6 | Missing or degraded external evidence must map to owner action, support action, and CEO escalation recommendation while primary controls remain disabled. |

This sprint does not change Objective 1/2/3/4 percentages. It also does not lift Objective 5 because the result is Docker/local `software_proof`, not real external proof.

## KR Breakdown For This Sprint

1. Define a canonical `cloud_external_evidence_review_handoff_followup_escalation_status` summary after `cloud_external_evidence_review_handoff`.
2. Preserve source link to `cloud_external_evidence_review_handoff` and its upstream `cloud_external_evidence_review_decision`.
3. Represent follow-up states such as pending, due soon, overdue, blocked, escalated, and ready for real-material follow-up, all as `not_proven`.
4. Include blocked reason, owner action, support action, reviewer action, next required evidence, and CEO escalation recommendation.
5. Preserve false-state fields: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
6. Preserve evidence boundary fields: `source=software_proof`, `not_proven`, `Docker`, `not true phone/browser proof`, `no OKR percentage lift`.
7. Keep PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` as unresolved `hardware_material_pending` evidence input only.
8. Keep PC/mobile/support UI read-only; no Start Delivery, Confirm Dropoff, Cancel, ACK/cursor mutation, raw artifact fetch, GitHub mutation, replay, material upload, or robot control route.

## Scope

In scope for the implementation sprint:

- PC evidence gate and fixture for `cloud_external_evidence_review_handoff_followup_escalation_status`.
- `mobile/web` read-only follow-up escalation status panel and fixture.
- Product docs describing the read-only, fail-closed support surface.
- Robot diagnostics safe alias for the follow-up status summary.
- Interface docs describing safe fields and forbidden control/raw evidence fields.
- Sprint closeout docs, conservative OKR wording, and progress log after Task A/B return.

Out of scope:

- No public HTTPS/TLS deployment.
- No production DB/queue, worker/cutover, or 4G/SIM validation.
- No OSS/CDN live traffic claim.
- No true phone/browser proof.
- No HIL, WAVE ROVER/UART, route/elevator field pass, verified terminal result, or delivery success.
- No PR #5 hardware-source wrapper and no claim that `PRRT_kwDOSWB9286CJ3tX` is resolved.
- No product code implementation during this planning task.

## Acceptance Criteria

Planning is accepted when:

- `pre_start.md`, `prd.md`, and `tech-plan.md` exist in the fresh sprint folder.
- The plan names `cloud_external_evidence_review_handoff_followup_escalation_status`, `cloud_external_evidence_review_handoff`, `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`, Objective 5, Docker/local proof, PR #5 `PRRT_kwDOSWB9286CJ3tX`, `hardware_material_pending`, `not true phone/browser proof`, `no OKR percentage lift`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- `tech-plan.md` includes Task A / Task B / Task C, owner/file split, interface boundaries, implementation requirements, focused verification commands, and `## OKR 最低优先级核对`.
- The plan states Task A and Task B write scopes are disjoint and can be dispatched in parallel, while Task C waits for implementation evidence.

Implementation will be accepted later only if Task A and Task B return focused validation evidence, docs under `docs/` are updated by their owners, and Product closeout records the result as `software_proof`, not external proof, not true phone/browser proof, and not an OKR percentage lift.

## Risks And Evidence Gaps

- Follow-up escalation metadata can be mistaken for O5 external proof unless every surface repeats `no OKR percentage lift`.
- Read-only mobile support panels can be mistaken for true phone/browser proof unless final copy says this is Docker/local only.
- PR #5 `hardware_material_pending` can distract the sprint back into hardware wrappers; this sprint must use it only as unresolved evidence context.
- The same missing external proof can be consumed too many times; this sprint mitigates that by making CEO escalation recommendation explicit when due/overdue/blocked status persists.
- No real cloud materials are available on this host, so Objective 5 remains blocked for actual percentage lift.
