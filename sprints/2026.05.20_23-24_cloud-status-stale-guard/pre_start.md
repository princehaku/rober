# Cloud Status Stale Guard Pre-start

## Sprint Metadata

- sprint_type: epic
- Sprint: `2026.05.20_23-24_cloud-status-stale-guard`
- Started at: 2026-05-20 23:00 Asia/Shanghai
- Primary Objective: Objective 5 云中转 + OSS/CDN 数据通路产品化
- Evidence boundary target: `software_proof_docker_cloud_status_stale_guard`

## Evidence Basis

- `OKR.md` 4.1 shows Objective 5 remains the lowest numerical objective at about 68%.
- Latest sprint `2026.05.20_22-23_cloud-command-sequence-regression-guard` closed as `software_proof_docker_cloud_command_sequence_regression_guard`; it did not add real public HTTPS/TLS, 4G/SIM, production DB/queue, OSS/CDN live traffic, production worker/cutover, or true phone/browser proof.
- PR #5 live review evidence still has `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`; PR #6 is README docs-only and has no review comments.
- Recent O5 guards covered auth failure, media degradation, and command sequence regression. `status_stale` exists as a generic degradation state, but it is not yet a dedicated proof boundary with Robot/API, mobile/web, and OKR closeout language.

## Blocker Scan

- O5 external proof is blocked by missing real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, worker/migration/cutover, and real phone/browser evidence.
- O1 progress is blocked by missing WAVE ROVER/UART/HIL evidence and missing PR #5 real 2D LiDAR / ToF materials.
- This sprint does not consume those real-material blockers again. It advances a fresh Docker-only O5 safety gap: stale robot/cloud status must fail closed and stay phone-safe.

## Owner Split

- Robot Platform Engineer: Robot/API stale-status proof boundary, readiness/command-safety fields, focused tests, O5 docs.
- User Touchpoint Full-Stack Engineer: `mobile/web` read-only stale-status display and fixture; controls stay disabled.
- Product Manager / OKR Owner: sprint docs, OKR/progress closeout, evidence boundaries and non-claims.

## Acceptance Boundary

This sprint can only claim local Docker/software proof. It must not claim real external cloud, real 4G/SIM, production queue, real phone/browser acceptance, WAVE ROVER/UART/HIL, route/elevator field pass, dropoff/cancel completion, delivery result, delivery success, or PR #5 resolution.
