# Cloud Poll Backoff Rate Limit Guard Pre Start

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_06-07_cloud-poll-backoff-rate-limit-guard`
- Automation: `skill-progression-map`
- Product owner: `product-okr-owner`
- Planned execution mode: enter implementation after `tech-plan.md` is accepted; do not stop at planning.
- Evidence boundary target: `software_proof_docker_cloud_poll_backoff_rate_limit_guard`

## Evidence Read Before Start

- `AGENTS.md` requires fresh sprint docs, owner/file-scope split, `## OKR 最低优先级核对` in Epic `tech-plan.md`, fenced validation, and sub-agent execution for implementation.
- `OKR.md` 4.1 was updated at 2026-05-21 05:18. Objective 5 is still lowest at about 68%; Objective 1 is about 81%; Objective 2/3/4 are about 99%.
- Latest sprint `2026.05.21_05-06_cloud-unreachable-malformed-response-guard` closed O5 `cloud_unreachable` / `malformed_response` fail-closed handling as Docker/local software proof and explicitly says not to repeat local O5 guard depth unless a fresh unguarded failure mode is identified.
- PR #5 review state remains material-relevant: `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false`; reply comment id `3269642220` is not reviewer resolution and not real hardware material.
- PR #6 is README/docs-only and does not add runtime proof.
- Recent field-evidence closeout `2026.05.21_03-04_field-evidence-rerun-execution-callback-review-handoff` says not to add another local wrapper around missing real same-safe-`evidence_ref` field materials.
- `docs/product/cloud_4g_infrastructure.md` states the 4C/8G cloud baseline carries only lightweight JSON command/status/ack and that robot polling interval should be controlled to avoid low-value high-frequency empty polling.

## Rerank Decision

Objective 5 remains numerically lowest, but the next percentage-moving proof still needs real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser evidence. The current Docker-only host cannot provide that.

This sprint still targets Objective 5 because there is a fresh local control-plane gap, not another blocked wrapper: repeated empty polls or repeated transient cloud failures can still create aggressive polling pressure and unclear phone/operator state. Recent O5 guards cover ACK outage, pending ACK, command expiry, idempotency, command-id conflict, auth failure, media degradation, command sequence regression, stale status, cloud unreachable, and malformed response. They do not establish an explicit backoff/rate-limit readiness state for repeated poll failures or empty-poll pressure.

Chosen capability: `cloud_poll_backoff_rate_limit_guard`.

## User Value And North Star

The north star remains a low-cost ROS2 trash delivery robot controlled from a normal phone through cloud relay. This sprint protects that user experience by making remote control conservative under weak network conditions: the robot should avoid hammering the cloud during repeated failures, the phone should see a clear "remote control is cooling down / retrying safely" state, and no cloud retry state should be confused with delivery success.

## Core Product Grip

Turn repeated poll failure / empty-poll pressure into one explicit, observable, fail-closed state across Robot diagnostics and mobile/web:

- `degradation_state=cloud_poll_backoff`
- `remote_ready=false`
- `safe_to_control=false`
- `primary_actions_enabled=false`
- `delivery_success=false`
- `retry_hint=wait_for_backoff_window`
- `proof_boundary=software_proof_docker_cloud_poll_backoff_rate_limit_guard`

## Blockers And Non-Claims

- This sprint will not increase Objective 5 percentage unless real external evidence appears during implementation.
- This sprint is not public HTTPS/TLS proof, not 4G/SIM proof, not OSS/CDN live traffic, not production DB/queue, not worker/cutover, not true phone/browser proof, not HIL, not PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, and not delivery success.
- Objective 1 remains blocked by missing real 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry or reviewer-resolved PR #5 state.
- Objective 2/3/4 remain blocked on real route/elevator field materials, true phone/browser evidence, dropoff/cancel completion, delivery result, and delivery success.

## Team

- Robot Platform Engineer: owner for `remote_bridge`, operator gateway diagnostics/status, Robot tests, and Robot docs.
- User Touchpoint Full-Stack Engineer: owner for mobile/web phone-safe rendering, fixture, mobile tests, and mobile product doc sync.
- Product Manager / OKR Owner: owner for sprint closeout, `OKR.md`, and progress log after implementation lands.
- Autonomy Algorithm Engineer: read-only consultation only; confirm no Nav2/fixed-route or field-evidence claims are introduced.
- Hardware Infra Engineer: read-only consultation only; confirm no PR #5 / WAVE ROVER / HIL claim is introduced.

## Immediate Next Action

Proceed to implementation using `tech-plan.md`. The main session should dispatch Robot and Full-Stack workers in parallel because file ranges are disjoint, with Product closeout after worker verification.
