# Sprint Pre-Start: cloud external evidence review handoff

- sprint_type: epic
- sprint folder: `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/`
- started_at: 2026-05-24 23:03 Asia/Shanghai
- target capability: `cloud_external_evidence_review_handoff`
- upstream capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_handoff_gate`
- closeout expectation: `no OKR percentage lift`

## User Value And North Star

The product north star is still a phone-first trash delivery robot that ordinary users can control without ROS2, raw JSON, SSH, serial debugging, or hardware knowledge. Objective 5 is the lowest current Objective, so this sprint keeps moving the cloud handoff path forward while staying honest about the evidence boundary.

The user value for this sprint is not "real cloud is working." The value is that support, owner, and reviewer can receive a consistent handoff packet after `cloud_external_evidence_review_decision`, so accepted / needs backfill / rejected unsafe / blocked / evidence-ref mismatch outcomes do not sit as local review labels with no next owner.

## Live Evidence Read Before Start

- `AGENTS.md`: this must be an Epic sprint because it has Full-Stack, Robot, and Product ownership, and it must keep a real sprint record.
- `OKR.md` §4.1: latest sprint is `2026.05.24_22-23_cloud-external-evidence-review-decision`; Objective 5 is still lowest at about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%.
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/final.md`: `cloud_external_evidence_review_decision` is only `software_proof_docker_cloud_external_evidence_review_decision_gate`, not true external proof and not an OKR lift.
- `docs/product/mobile_user_flow.md`: phone UI and support surfaces must stay fail closed when backend proof is missing; primary actions remain disabled.
- `docs/product/remote_4g_mvp.md`: the current O5 cloud review-decision panel consumes safe summaries only and keeps `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, `not true phone/browser proof`, and `no OKR percentage lift`.
- GitHub evidence supplied by main session: PR #5 is merged/closed, but review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved/not outdated with latest reply `hardware_material_pending`; PR #7 is open with no review threads.

## OKR Mapping

| Objective | Current state | Sprint relevance |
| --- | --- | --- |
| Objective 1 | About 81%; PR #5 `PRRT_kwDOSWB9286CJ3tX` still unresolved with `hardware_material_pending`; no HIL or WAVE ROVER/UART proof on this host. | Evidence input only. This sprint must not create another hardware PR #5 local wrapper. |
| Objective 2 | About 99%; still lacks real field route/elevator pass and verified delivery/dropoff/cancel result. | No runtime route/elevator change in planning. |
| Objective 3 | About 99%; still lacks real Nav2/fixed-route runtime proof. | No navigation scope in planning. |
| Objective 4 | About 99%; true phone/browser proof is still missing. | Full-Stack handoff UI remains read-only and fail closed, not true phone/browser proof. |
| Objective 5 | About 68%; lowest; still lacks public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result, HIL, route/elevator field pass, and delivery success. | Primary target. This sprint creates the next handoff layer after review decision, still Docker/local `software_proof` only. |

## This Sprint

Capability: `cloud_external_evidence_review_handoff`.

The sprint should package review-decision outcomes into owner/support/reviewer handoff metadata. Supported source decisions:

- accepted external evidence
- needs backfill
- rejected unsafe
- blocked missing external evidence
- evidence-ref mismatch

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
| Task A | User Touchpoint Full-Stack Engineer | Add the read-only phone/support handoff surface and fixture boundary. | Parallel with Task B after this plan. |
| Task B | Robot Platform Engineer | Add the Robot diagnostics safe alias and behavior-side metadata exposure. | Parallel with Task A after this plan. |
| Task C | Product Manager / OKR Owner | Close out sprint docs and conservative OKR wording after Task A/B evidence returns. | Run after Task A/B. |

## Blocker Reuse Check

This is not another local wrapper for the same PR #5 hardware material blocker. PR #5 is used only as unresolved live evidence input: thread `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending`.

The active O5 blocker is missing real external cloud evidence. This sprint is acceptable because it follows the direct chain from `cloud_external_evidence_review_decision` to `cloud_external_evidence_review_handoff`, so future real evidence has explicit owner/support/reviewer routing. It must not claim public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, WAVE ROVER/UART, route/elevator field pass, verified terminal result, or delivery success.

## Sprint Documents To Create Or Update

Planning creates:

- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/pre_start.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/prd.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-plan.md`

Implementation closeout later must add:

- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/tech-done.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/side2side_check.md`
- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff/final.md`

