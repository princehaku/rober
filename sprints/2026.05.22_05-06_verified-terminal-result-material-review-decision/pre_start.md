# Verified Terminal Result Material Review Decision Pre Start

Run time: 2026-05-22 05:06 Asia/Shanghai

## Sprint Declaration

- sprint_type: epic
- capability: `verified_terminal_result_material_review_decision`
- evidence_boundary: `software_proof_docker_verified_terminal_result_material_review_decision_gate`
- target sprint path: `sprints/2026.05.22_05-06_verified-terminal-result-material-review-decision/`
- current host boundary: Docker-only local environment, no real hardware, no real route/elevator/phone/cloud/HIL/delivery proof.

## User Value And North Star

North star: ordinary phone users should only see delivery, dropoff, or cancel completion after a same-safe-`evidence_ref` terminal result has been reviewed and accepted with real materials. Before that, support and field owners need a clear, phone-safe review decision that says whether the previous intake output is accepted for review, needs material backfill, rejected, or blocked.

This sprint moves from `verified_terminal_result_material_intake` to `verified_terminal_result_material_review_decision`. It reads the previous intake artifact, summary, and Robot safe alias, then produces a metadata-only review decision and owner handoff. The decision can guide the next owner without turning Docker-only metadata into delivery success.

## Evidence Inputs

- `OKR.md` 4.1 says Objective 5 remains lowest at about 68%.
- Objective 5 still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, real phone/browser evidence, and verified terminal delivery/dropoff/cancel result.
- `sprints/2026.05.22_04-05_verified-terminal-result-material-intake/final.md` closed the previous sprint as `software_proof_docker_verified_terminal_result_material_intake_gate` and explicitly said the next sprint should not wrap the same missing-material blocker again.
- The previous sprint delivered intake capability but supplied no real terminal result material.
- Objective 1 remains about 81%; PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved / material pending, and comment `3269642220` is only software-proof publication, not reviewer resolution.
- Current host has Docker only and cannot produce real WAVE ROVER/UART/HIL, real phone/browser, real cloud, or real route/elevator field evidence.

## Blocker Scan

The repeated blocker is missing real-world materials. This sprint does not consume that blocker as another generic status wrapper. It advances the previous intake output into a concrete review-decision gate:

1. If intake material is safe and reviewable, mark `accepted_for_review`.
2. If required real material is missing, mark `needs_material_backfill` with precise `next_required_evidence`.
3. If material is unsafe or overclaiming, mark `rejected`.
4. If no intake artifact or safe Robot alias exists, mark `blocked`.

All outcomes remain metadata-only and fail closed.

## Sprint Goal

Create a software-proof, fail-closed review-decision path for terminal delivery/dropoff/cancel result intake outputs:

1. Read prior intake artifact, summary, and Robot diagnostics safe alias.
2. Normalize one safe `evidence_ref` and reject mismatches.
3. Produce a metadata-only review decision: `accepted_for_review`, `needs_material_backfill`, `rejected`, or `blocked`.
4. Include `owner_handoff`, `next_required_evidence`, safe copy, and no-overclaim fields.
5. Preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and safe-copy-only output.
6. Keep Objective 5 at about 68% unless real materials arrive and are separately verified during closeout.

## Owner Routing

- Autonomy Algorithm Engineer owns the PC review-decision CLI and schema/tests.
- Robot Platform Engineer owns diagnostics/status safe alias integration for the review decision.
- User Touchpoint Full-Stack Engineer owns the mobile/web read-only review-decision panel and safe-copy handling.
- Product Manager / OKR Owner owns sprint closeout, OKR/progress evidence language, and no-overclaim acceptance.

## Scope Boundary

In scope for implementation:

- New or extended PC review-decision CLI for `verified_terminal_result_material_review_decision`.
- Robot diagnostics/status safe summary alias.
- Mobile/web read-only panel with safe copy only.
- Related docs under `docs/interfaces/` and `docs/product/`.
- Sprint closeout docs after worker evidence exists.

Out of scope:

- No production cloud, OSS/CDN, public HTTPS/TLS, 4G/SIM, production DB/queue, worker/cutover proof.
- No real phone/browser/device proof.
- No route/elevator/Nav2/fixed-route field pass.
- No WAVE ROVER/UART/HIL, serial device, hardware config, launch parameter, or vendor material change.
- No Start Delivery, Confirm Dropoff, Cancel, ACK mutation, cursor mutation, replay, resubmit, or control enablement.
- No PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution claim from comment `3269642220`.
- No `OKR.md` percentage increase unless real materials are provided and verified during closeout.

## Required Sprint Documents

This Epic sprint must create and then complete the full chain:

1. `pre_start.md`
2. `prd.md`
3. `tech-plan.md`
4. `tech-done.md`
5. `side2side_check.md`
6. `final.md`

This planning task creates only the first three files. Implementation workers must update `tech-done.md`; Product closeout must update `side2side_check.md`, `final.md`, and only then decide whether `OKR.md` changes are justified.
