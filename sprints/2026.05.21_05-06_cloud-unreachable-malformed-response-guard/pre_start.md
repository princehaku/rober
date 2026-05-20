# Cloud Unreachable Malformed Response Guard Pre-start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_05-06_cloud-unreachable-malformed-response-guard`
- Target capability: `cloud_unreachable_malformed_response_guard`
- Evidence boundary: `software_proof_docker_cloud_unreachable_malformed_response_guard`
- Preserved states: `source=software_proof`, `not_proven`, `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`
- Planning scope: create planning docs only. This step does not modify product code, test code, `OKR.md`, `docs/`, or previous sprint files.

## User Value And Product North Star

The product north star remains a low-cost ROS2 trash delivery robot that ordinary phone users can control through a phone-facing cloud path without knowing ROS2, SSH, serial tools, or cloud diagnostics. This sprint protects that path when the cloud is unreachable or responds with malformed data: Robot/API and `mobile/web` must fail closed, disable primary actions, show safe Chinese recovery copy, and preserve diagnostics without turning communication failure into delivery success.

This is a fresh Docker/local fail-closed gap inside Objective 5. It is not real external cloud proof, not true phone/browser proof, and not a reason to raise Objective 5 percentage.

## Required Evidence Inputs

- `OKR.md` 4.1 shows Objective 5 remains lowest at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
- Latest sprint `sprints/2026.05.21_04-05_pr5-mandatory-sensor-source-alignment/final.md` says not to add another local wrapper for PR #5 missing materials, and says O5 percentage movement needs real external evidence unavailable on this Docker-only host.
- Recent O5 guards already cover auth failure, media degradation, command sequence regression, and stale status; `cloud_unreachable` and `malformed_response` exist in the product flow but do not yet have the same explicit fail-closed guard surface.
- `docs/product/mobile_user_flow.md` and `docs/product/remote_4g_mvp.md` require phone-safe command/status/ACK semantics and prohibit exposing raw ROS topics, `/cmd_vel`, serial details, credentials, tracebacks, or hardware control internals to ordinary users.

## Why This Sprint

Objective 5 remains the numerical lowest priority, but real percentage movement is blocked by missing public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, and true phone/browser evidence. This sprint therefore targets only the next Docker-actionable safety gap: explicit fail-closed behavior for `cloud_unreachable` and `malformed_response`.

The sprint is epic because it crosses two implementation owners with distinct surfaces: Robot/API status normalization and mobile/web user-facing rendering. Product planning must make the evidence boundary explicit before Engineers implement it.

## Owners And Parallel Plan

- Robot Platform Engineer: owns the Robot/API guard summary, diagnostics normalization, and software proof command/status/ACK boundary.
- User Touchpoint Full-Stack Engineer: owns the `mobile/web` read-only fail-closed surface, fixture, and phone-safe copy.
- Product Manager / OKR Owner: owns planning docs now and later conservative closeout. `OKR.md` must remain unchanged unless implementation evidence lands and still must not raise Objective 5 without real external proof.

## Risks, Blockers, And Evidence Gaps

- O5 cannot increase without real public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, production worker/cutover, or true phone/browser evidence.
- This sprint must not claim real cloud availability, real phone behavior, real app behavior, PWA prompt/userChoice, OSS/CDN live traffic, production queue ordering, Nav2/fixed-route, WAVE ROVER/UART, HIL, dropoff/cancel completion, delivery result, or delivery success.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved/material pending and must not be consumed by this sprint.
- The implementation must keep support diagnostics visible while disabling Start Delivery, Confirm Dropoff, Cancel, ACK/cursor requests, retries, resubmits, or hidden robot command side effects.

## Sprint Documents To Create Or Update

- Created in planning: `pre_start.md`, `prd.md`, `tech-plan.md`.
- To be created after implementation: `tech-done.md`, `side2side_check.md`, `final.md`.
