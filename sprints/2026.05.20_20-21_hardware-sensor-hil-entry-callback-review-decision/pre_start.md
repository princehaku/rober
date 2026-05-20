# Hardware Sensor HIL-entry Callback Review Decision Pre-start

## Sprint Type

- sprint_type: epic
- Sprint: `2026.05.20_20-21_hardware-sensor-hil-entry-callback-review-decision`
- Started at: 2026-05-20 20:04 CST

## Evidence-backed Direction

`OKR.md` 4.1 shows Objective 5 is still lowest at about 68%, but the latest `cloud_auth_failure_status_guard` final states that O5 can only increase with real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or real phone/browser external proof. This Docker-only host has none of those materials.

The next numerical objective is Objective 1 at about 81%. PR #5 is merged, but live GitHub review thread `PRRT_kwDOSWB9286CJ3tX` remains unresolved and still asks for repo-local vendor/source evidence for mandatory sensor assumptions. Recent sprints already created procurement receipt, HIL-entry readiness, execution pack, and callback intake gates. The next actionable software step is to review the callback intake result into a machine-readable decision without claiming real hardware.

## Objective

Advance Objective 1 with `hardware_sensor_hil_entry_callback_review_decision`: consume the existing `hardware_sensor_hil_entry_callback_intake` summary/artifact, classify received/missing/rejected callback materials, and expose a fail-closed review decision through PC gate, Robot diagnostics, and mobile/web.

## Owners

- Hardware Infra Engineer: PC gate, focused test, and hardware/source docs.
- Robot Platform Engineer: Robot diagnostics safe alias and focused diagnostics fence.
- User Touchpoint Full-Stack Engineer: mobile/web read-only panel and phone-safe fixture.
- Product Manager / OKR Owner: closeout, OKR snapshot, and progress log.

## Blocker Red Line

This sprint must preserve `software_proof`, `hardware_material_pending`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`. It must not resolve PR #5, claim real 2D LiDAR / ToF materials, WAVE ROVER/UART/HIL, route/elevator pass, real phone/browser proof, O5 external proof, or delivery success.
