# Pre Start - Cloud external evidence review decision

- sprint_type: epic
- sprint: `2026.05.24_22-23_cloud-external-evidence-review-decision`
- start time: 2026-05-24 22:07 Asia/Shanghai
- Product owner: `product-okr-owner`
- target capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_decision_gate`
- execution mode: Product planning only in this step; implementation must be dispatched to Engineer subagents later.

## Why This Sprint Exists

Objective 5 remains the lowest current Objective in `OKR.md` §4.1, about 68%. The latest closeout `2026.05.24_21-22_mobile-current-panel-browser-proof-refresh-cloud-command-lifecycle-owner-response-intake-bridge/final.md` explicitly says the previous sprint was an Objective 4 local Chromium proof refresh, not an Objective 5 lift, and that the next lift requires real external or hardware evidence rather than another local-only wrapper.

Live review evidence also remains unchanged: PR #5 is merged/closed but review thread `PRRT_kwDOSWB9286CJ3tX` on `docs/product/production_hardware_boundary.md` is still unresolved/not outdated with latest reply `hardware_material_pending`; PR #7 is open with no review threads/comments and does not close that evidence gap.

This host has Docker only and no real hardware. The sprint therefore targets a bounded O5 software capability: a review-decision gate for existing `trashbot.external_evidence_intake` materials. The capability should let future real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, and production DB/queue evidence be safely classified as accepted, needs backfill, rejected unsafe, or blocked missing input, while keeping `production_ready=false` and `no OKR percentage lift` unless real external evidence is actually supplied.

## User Value And Product North Star

User value: support and field operators get a concrete place to review future O5 external evidence instead of adding another read-only status panel. The product can distinguish "materials not supplied", "materials supplied but incomplete", and "materials unsafe or credential-bearing" before any phone control or production-readiness claim changes.

Product north star: ordinary phone users should eventually control the robot through cloud relay without sharing WiFi, while support can explain missing cloud proof in plain language. This sprint moves the cloud evidence workflow toward that north star, but stays fail-closed on the Docker-only host.

## OKR Snapshot

| Objective | Current evidence | Sprint stance |
| --- | --- | --- |
| Objective 1 | About 81%; PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending`. | Not targeted; no WAVE ROVER/UART/HIL, LiDAR/ToF source, install, wiring, calibration, or reviewer resolution is produced. |
| Objective 2 | About 99%; no new route/elevator field result. | Not targeted. |
| Objective 3 | About 99%; no new Nav2/fixed-route runtime proof. | Not targeted. |
| Objective 4 | About 99%; latest local browser proof is not true phone/browser proof. | Consumed only as phone-surface boundary for the planned O5 review decision. |
| Objective 5 | About 68%; lowest; real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof and verified terminal result are still missing. | Targeted through `cloud_external_evidence_review_decision`, with `software_proof` only and `no OKR percentage lift`. |

## Core Lever

Build a review decision after the already documented `trashbot.external_evidence_intake` gate. The implementation should not create a mutable command path. It should classify safe external-material intake summaries into a review state and expose only phone-safe, redacted metadata across cloud/Robot/mobile surfaces.

Expected decision states:

- `accepted_external_evidence_not_proven`
- `needs_external_evidence_backfill_not_proven`
- `rejected_unsafe_external_evidence_not_proven`
- `blocked_missing_external_evidence_intake_not_proven`
- `external_evidence_ref_mismatch_not_proven`

## Scope Boundaries

In scope:

- Review-decision schema and local PC/cloud validation for external evidence intake.
- Robot diagnostics safe alias for the review-decision summary.
- `mobile/web` read-only panel that keeps Start Delivery, Confirm Dropoff, and Cancel disabled.
- Docs updates under the relevant cloud/mobile/interface docs after implementation.
- Focused tests and `git diff --check` only.

Out of scope:

- Real public HTTPS/TLS proof.
- Real 4G/SIM proof.
- Real OSS/CDN live traffic.
- Real production DB/queue or worker/cutover proof.
- True phone/browser proof.
- HIL, WAVE ROVER/UART, LiDAR/ToF material resolution, PR #5 thread resolution, route/elevator field pass, verified terminal result, delivery result, or delivery success.
- `OKR.md` updates in this planning-only step.
- `tech-done.md`, `side2side_check.md`, or `final.md` generation before implementation evidence exists.

## Team And Owner Routing

- `full-stack-software-engineer`: PC/cloud evidence review-decision gate, mobile panel, focused cloud/mobile docs, and mobile browser/UI fences.
- `robot-software-engineer`: Robot diagnostics safe alias and ROS runtime contract docs.
- `product-okr-owner`: later closeout only, after Engineer evidence exists; closeout may update `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md`.

No hardware Engineer implementation is planned because this sprint must not invent hardware facts or touch vendor/hardware configuration. If later work mentions UART, WAVE ROVER, LiDAR/ToF, wiring, voltage, or HIL, it must first reread `docs/vendor/VENDOR_INDEX.md`.

## Blocker And Redline Check

The last two O5/O4 closeouts already warn against another local-only wrapper. This sprint is acceptable only because it creates a named review-decision capability for future real external evidence intake. It must still report `software_proof`, `Docker`, `not true phone/browser proof`, `not O5 external proof`, `hardware_material_pending`, and `no OKR percentage lift`.

If implementation drifts into another read-only panel over an already reviewed owner-response support state, it should stop and return for rerank.

## Sprint Documents

Created in this planning step:

- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/pre_start.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/prd.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-plan.md`

Do not create `tech-done.md`, `side2side_check.md`, or `final.md` until Engineer implementation and validation evidence exists.
