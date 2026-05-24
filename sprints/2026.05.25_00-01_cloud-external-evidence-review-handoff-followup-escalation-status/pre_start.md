# Sprint Pre-Start: cloud external evidence review handoff followup escalation status

- sprint_type: epic
- sprint folder: `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/`
- started_at: 2026-05-25 00:01 Asia/Shanghai
- target capability: `cloud_external_evidence_review_handoff_followup_escalation_status`
- upstream capability: `cloud_external_evidence_review_handoff`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate`
- closeout expectation: `software_proof`, `not_proven`, `no OKR percentage lift`

## User Value And Product North Star

The product north star remains a phone-first trash delivery robot that ordinary users can operate through safe cloud relay surfaces without ROS2, raw JSON, SSH, serial debugging, or hardware knowledge.

The user value for this sprint is narrow and concrete: convert the previous `cloud_external_evidence_review_handoff` owner/support/reviewer packet into follow-up due status, blocked reason, owner action, and CEO escalation recommendation. This prevents the handoff from sitting in a "sent but nobody is accountable" state while keeping the product honest that this is still Docker/local `software_proof`, not real external cloud evidence.

## Live Evidence Read Before Start

- `AGENTS.md`: this must be an Epic sprint because it has Full-Stack, Robot, and Product ownership, and it must create real sprint planning before implementation.
- `OKR.md` §4.1: Objective 5 is currently lowest at about 68%; Objective 1 is about 81%; Objective 2/3/4 are about 99%.
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/final.md`: latest sprint completed `cloud_external_evidence_review_handoff` as `software_proof_docker_cloud_external_evidence_review_handoff_gate`, with `no OKR percentage lift`.
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/final.md`: previous sprint completed `cloud_external_evidence_review_decision` as Docker/local `software_proof`, not true external proof.
- `docs/product/mobile_user_flow.md`: mobile surfaces must stay fail closed when backend proof is missing; Start Delivery, Confirm Dropoff, and Cancel remain disabled unless explicit safe gates allow them.
- GitHub evidence supplied by the main session: PR #7 is open but review_threads/comments are empty; PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`, and the reviewer still needs mandatory sensor assumptions to cite local vendor sources plus real 2D LiDAR/ToF SKU/source/receipt, mounting, wiring, power, calibration, HIL, and Nav2 field pass evidence.
- Environment boundary: this host has Docker only, with no real hardware. This sprint cannot claim public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, WAVE ROVER/UART proof, route/elevator field pass, or delivery success.

## OKR Mapping

| Objective | Current state | Sprint relevance |
| --- | --- | --- |
| Objective 1 | About 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; no real WAVE ROVER/UART, HIL, 2D LiDAR, or ToF material proof on this host. | Evidence context only. This sprint must not create another hardware wrapper or claim PR #5 resolution. |
| Objective 2 | About 99%; still lacks true route/elevator field pass, verified terminal delivery/dropoff/cancel result, and delivery success. | No runtime route/elevator change. Keep `delivery_success=false`. |
| Objective 3 | About 99%; still lacks real Nav2/fixed-route runtime proof and field route data. | No navigation scope. |
| Objective 4 | About 99%; true phone/browser proof is still missing. | Full-Stack work may add a read-only panel only; it remains `not true phone/browser proof`. |
| Objective 5 | About 68%; lowest; still lacks public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, route/elevator field pass, and delivery success. | Primary target. This sprint adds follow-up escalation status after `cloud_external_evidence_review_handoff`, still Docker/local `software_proof` only. |

## This Sprint

Capability: `cloud_external_evidence_review_handoff_followup_escalation_status`.

The sprint should transform a prior `cloud_external_evidence_review_handoff` packet into follow-up accountability metadata:

- follow-up due status: pending, due soon, overdue, blocked, or escalated.
- blocked reason: missing external evidence, unsafe material, evidence-ref mismatch, missing owner acknowledgement, or missing reviewer action.
- owner action: backfill evidence, reassign owner, request CEO decision, hold for real material, or close only after real external proof.
- CEO escalation recommendation: escalate when the same missing external evidence or PR #5 `hardware_material_pending` blocks real progress after handoff.

Required false-state and safety fields:

- `source=software_proof`
- `not_proven`
- `Docker`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not true phone/browser proof`
- `no OKR percentage lift`
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending`

## Owner Split

| Task | Owner | Purpose | Start mode |
| --- | --- | --- | --- |
| Task A | User Touchpoint Full-Stack Engineer | Add PC evidence gate, mobile/web read-only follow-up status panel, fixture, and product docs. | Parallel with Task B after planning. |
| Task B | Robot Platform Engineer | Add Robot diagnostics safe alias and interface docs for the follow-up escalation status summary. | Parallel with Task A after planning. |
| Task C | Product Manager / OKR Owner | Close out `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` after Task A/B complete. | Run after Task A/B evidence returns. |

## Blocker Reuse Check

This sprint does not consume the PR #5 hardware blocker as a new hardware sprint. PR #5 thread `PRRT_kwDOSWB9286CJ3tX` is evidence context only and remains `hardware_material_pending`.

The active O5 blocker is missing real external evidence. This sprint is acceptable because it follows the direct chain `cloud_external_evidence_review_decision` -> `cloud_external_evidence_review_handoff` -> `cloud_external_evidence_review_handoff_followup_escalation_status`, turning a handoff into due-status and escalation accountability. It must not claim public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, WAVE ROVER/UART, route/elevator field pass, verified terminal result, or delivery success.

## Sprint Documents To Create Or Update

Planning creates:

- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/pre_start.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/prd.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-plan.md`

Implementation closeout later must add or update:

- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/tech-done.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/side2side_check.md`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
