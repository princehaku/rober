# Cloud Poll Backoff Rate Limit Guard PRD

## User Value And Product North Star

Normal users should not need to understand cloud polling, retries, ACK cursors, or Docker proof boundaries. When the remote cloud link is weak, the product must show a conservative phone-safe state and prevent repeated user actions from creating more cloud pressure or ambiguous robot state.

This sprint advances the north star by making the cloud control loop quieter and safer under repeated poll failures or empty-poll pressure. It is still Docker/local `software_proof`, not real cloud completion.

## Problem

Objective 5 remains the weakest Objective at about 68%, but external proof is unavailable on this host. Recent O5 work closed many fail-closed states, including command ACK outage, pending ACK, expired command, duplicate command, command-id conflict, auth failure, media degradation, command sequence regression, stale status, cloud unreachable, and malformed response.

The remaining fresh local control-plane gap is poll pressure and retry visibility:

- A robot can keep polling aggressively during repeated transient failures or long empty-command windows.
- The operator/mobile surface can show cloud failure states without distinguishing a deliberate backoff window from general unreachable/malformed states.
- A user may retry too early unless the product exposes a clear wait/retry state.

`docs/product/cloud_4g_infrastructure.md` already sets the product boundary: cloud relay is lightweight JSON command/status/ack, and robot polling interval should be controlled to avoid high-frequency empty polling.

## OKR Mapping

- Objective 5 / KR1: strengthens command/status/ack control-plane reliability without exposing `/cmd_vel` or inbound robot control.
- Objective 5 / KR6: turns repeated cloud poll failures into graceful degradation with a recoverable retry state.
- Objective 4: phone surface must present the state in plain Chinese and keep primary actions disabled.
- Objective 1: no progress claim; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved and material pending.
- Objective 2/3: no route/elevator, Nav2, fixed-route, dropoff/cancel, or delivery result claim.

## KR Split

- KR-A Robot: repeated poll failure / empty-poll pressure produces `cloud_poll_backoff` readiness/status with bounded backoff metadata, redacted fields, and no delivery success claim.
- KR-B Full-Stack: mobile/web consumes `cloud_poll_backoff` diagnostics and shows phone-safe Chinese copy, wait guidance, and disabled Start / Confirm / Cancel controls.
- KR-C Product/Docs: docs and sprint closeout preserve `software_proof_docker_cloud_poll_backoff_rate_limit_guard` and explicitly state no O5 percentage movement without real external evidence.

## Scope

In scope:

- Add a Docker/local software-proof guard for poll backoff/rate limiting.
- Expose a safe summary to operator gateway diagnostics/status.
- Add a mobile fixture and read-only rendering branch for the new state.
- Update `docs/product/remote_4g_mvp.md`, `docs/product/mobile_user_flow.md`, and the relevant interface docs during implementation.
- Run only fenced validation commands.

Out of scope:

- Real cloud deployment, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof.
- Hardware, WAVE ROVER, UART, HIL, 2D LiDAR / ToF procurement/source materials, or PR #5 reviewer resolution.
- Nav2/fixed-route, route/elevator field pass, dropoff/cancel completion, delivery result, delivery success.
- Broad regression sweeps or unrelated refactors.

## Acceptance

P0:

- Robot diagnostics/status can represent `cloud_poll_backoff` with `remote_ready=false`, `safe_to_control=false`, `primary_actions_enabled=false`, `delivery_success=false`, `retry_hint=wait_for_backoff_window`, and `proof_boundary=software_proof_docker_cloud_poll_backoff_rate_limit_guard`.
- Mobile/web renders the state in Chinese and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
- No phone/operator output leaks bearer token, Authorization header, cloud credential, credential-bearing URL, state path, `/cmd_vel`, raw ROS topic, serial device, WAVE ROVER details, traceback, or `delivery_success=true`.
- Existing O5 states keep their current priority: auth failure, pending ACK, expired command, duplicate/conflict, stale status, cloud unreachable, malformed response, and media degradation must not be silently downgraded by the new backoff state.

P1:

- Docs explain that backoff/rate-limit proof is capacity and safety hygiene only, not real cloud proof.
- Tests are fenced to touched Robot/mobile code paths.

## Priority

P0 because it is the only identified fresh O5 Docker-local control-plane gap after the latest O5 guard sprint. If implementation discovers this is already fully covered by existing logic, Product must stop and rerank rather than create another duplicate wrapper.

## Risks And Evidence Needed

- Risk: The guard could mask more specific failure states. Mitigation: tech plan requires explicit priority ordering tests.
- Risk: Backoff metadata could expose internals. Mitigation: safe summary allowlist and redaction assertions.
- Risk: Product could overclaim O5. Mitigation: closeout must keep Objective 5 about 68% unless real external evidence appears.
- Evidence still needed for future percentage movement: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or true phone/browser evidence.

## Responsible Engineers

- Robot Platform Engineer: P0 Robot implementation and tests.
- User Touchpoint Full-Stack Engineer: P0 mobile rendering and tests.
- Product Manager / OKR Owner: closeout and OKR wording after workers finish.
- Autonomy and Hardware: read-only boundary review if implementation touches route/elevator or hardware wording.
