# Cloud Hosted Mobile Web Degradation Passthrough Pre Start

## Sprint Declaration

- sprint_type: epic
- run_time: 2026-05-21 13:14 CST
- capability: `cloud_hosted_mobile_web_degradation_passthrough`
- evidence_boundary: `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`
- required preserved states: `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`

## User Value And Product North Star

The product north star remains: a normal phone user can hand trash to the robot, use a phone as the primary control and recovery surface, and understand degraded states without learning ROS2, SSH, cloud relay internals, serial/UART, or hardware debug.

This sprint targets the cloud-hosted same-origin mobile shell. When the relay already knows a safe `remote_readiness.degradation_state`, the hosted phone entry must show the specific state instead of flattening it into generic `status_present`. The user value is safer recovery language: `auth_failed`, `cloud_poll_backoff`, `manual_takeover_required`, `command_pending`, `command_expired`, `command_duplicate_deduped`, `command_id_conflict`, `command_sequence_regression`, `cloud_unreachable`, and `malformed_response` must stay visible as fail-closed phone-safe states.

## Evidence Read Before Planning

- `AGENTS.md`: Epic sprint requires `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`, `pre_start.md` must declare `sprint_type: epic`, and implementation must use 2+ owner parallel Engineer dispatch when file scopes are disjoint.
- `OKR.md` 4.1, updated 2026-05-21 12:16 Asia/Shanghai: Objective 5 is the current lowest Objective at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
- `OKR.md` section 6: Objective 5 percentage should only move with real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, production app/device, or true phone/browser evidence.
- Latest final `sprints/2026.05.21_12-13_field-evidence-rerun-execution-result-acceptance-backfill/final.md`: do not add another local wrapper to the same acceptance-backfill gate; O5/O1/O2/O3/O4 still lack real materials.
- PR #5 review evidence supplied by CEO and reflected in `OKR.md`: `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `is_resolved=false` / `hardware_material_pending`; reply comment id `3269642220` is software-proof reply publication only, not reviewer resolution.
- `cloud-relay/README.md`: current same-origin `GET /api/status` / `GET /api/diagnostics` adapter is `software_proof_docker_cloud_hosted_mobile_web_gate`, returns status_missing/status_stale fail-closed states, and must not claim real cloud or phone proof.
- `docs/product/mobile_user_flow.md`: `remote_readiness.degradation_state` is already the phone-facing readiness class for local/mock remote-control states, and prior mobile views already consume individual safe states through fixtures.

## Blocker Scan And Re-Rank

- Objective 5 is still the lowest numeric Objective and is the right family because this is cloud-hosted mobile web degradation visibility.
- This is not an O5 percentage sprint. The host still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, production app/device, and true phone/browser evidence.
- This is not a repeated acceptance-backfill wrapper. It does not add a new wrapper to `field_evidence_rerun_execution_result_acceptance_backfill`; it fixes a separate hosted-shell adapter gap where safe degradation state is present upstream but becomes too generic at `/api/status`.
- Objective 1 remains blocked by real hardware material and PR #5 `PRRT_kwDOSWB9286CJ3tX`; this sprint makes no WAVE ROVER/UART/HIL, 2D LiDAR/ToF, or reviewer-resolution claim.
- Objectives 2/3/4 still lack real route/elevator/phone field materials; this sprint must not claim route/elevator field pass, delivery result, delivery success, or true phone/browser proof.

## Core Sprint Grab

Create a Docker/local software-proof passthrough for cloud-hosted same-origin mobile web degraded readiness:

- Robot Platform Engineer owns the cloud relay adapter/status API path and backend tests so `remote_readiness.degradation_state` survives into the hosted `/api/status` response with safe fields and fail-closed controls.
- User Touchpoint Full-Stack Engineer owns `mobile/web` rendering, fixture coverage, and user-facing copy so the hosted shell shows the specific safe state while keeping Start Delivery / Confirm Dropoff / Cancel disabled.
- Product Manager / OKR Owner owns post-implementation sprint closeout, OKR/progress-log wording, and proof-boundary review; Product does not edit implementation in this planning pass.

## Owners For Execution

- Robot Platform Engineer: cloud-hosted `/api/status` adapter, relay/backend fixture or tests, sanitization, and cloud relay docs/interface wording.
- User Touchpoint Full-Stack Engineer: `mobile/web` parsing/rendering, fixture, focused mobile tests, and `docs/product/mobile_user_flow.md` update.
- Product Manager / OKR Owner: after Engineer evidence returns, update `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` conservatively.

## Non Goals

- Do not implement real public cloud deployment, real HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, production worker/cutover, production app/device, true phone/browser validation, HIL, WAVE ROVER/UART proof, route/elevator field pass, dropoff/cancel completion, delivery result, or delivery success.
- Do not close or claim resolution of PR #5 `PRRT_kwDOSWB9286CJ3tX`.
- Do not enable Start Delivery, Confirm Dropoff, Cancel, replay, resubmit, ACK/cursor request, or any primary action from a degraded state.
- Do not expose bearer tokens, Authorization headers, OSS secrets, DB/queue URLs, local paths, raw diagnostics, raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, checksums, or complete raw artifacts.

## Required Next Sprint Documents

This planning pass creates:

- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/pre_start.md`
- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/prd.md`
- `sprints/2026.05.21_13-14_cloud-hosted-mobile-web-degradation-passthrough/tech-plan.md`

After Engineer execution, Product must update:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
