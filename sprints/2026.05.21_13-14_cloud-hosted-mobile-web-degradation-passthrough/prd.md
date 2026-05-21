# Cloud Hosted Mobile Web Degradation Passthrough PRD

## User Value And Product North Star

The user value is degraded-state clarity in the cloud-hosted phone entry. A normal phone user should not see a vague "status exists" signal when the robot/cloud path is actually blocked by auth failure, cloud backoff, manual takeover, pending command, expired command, duplicate command, command conflict, sequence regression, cloud unreachable, or malformed response.

The product north star remains phone-first trash delivery: the phone is the user's control and recovery surface, but it must fail closed and explain why primary actions are unavailable. `cloud_hosted_mobile_web_degradation_passthrough` closes the specific gap where same-origin `/api/status` can flatten safe upstream relay status into generic `status_present` / `status_missing` / `status_stale` instead of carrying the precise safe `remote_readiness.degradation_state`.

## OKR Mapping

- Primary Objective: Objective 5, cloud relay / OSS-CDN data path productization, currently about 68% and the lowest Objective in `OKR.md` 4.1.
- Secondary Objective: Objective 4, phone user experience and low-cost production boundary, currently about 99%, because the cloud-hosted phone shell must explain degraded control states without exposing raw robot/cloud details.
- Guarded Objective: Objective 1, currently about 81%, remains blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved / `is_resolved=false` / `hardware_material_pending`; comment `3269642220` remains only software-proof reply publication.

This sprint must not raise OKR percentages by itself. It creates bounded `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate` evidence only, not real external O5 proof.

## KR Breakdown Or Update

- KR-A Robot/API passthrough: same-origin cloud-hosted `GET /api/status` preserves a safe `remote_readiness` summary when latest relay status already contains `degradation_state` and fail-closed fields.
- KR-B Robot/API sanitization: the adapter must preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, redaction, and disabled command safety; it must not forward raw cloud/robot fields.
- KR-C Mobile/Web rendering: `mobile/web` renders the specific degraded state and Chinese-first safe copy, not only a generic `status_present` message.
- KR-D Mobile/Web controls: Start Delivery, Confirm Dropoff, and Cancel remain disabled for every degraded passthrough state.
- KR-E Documentation and evidence: `cloud-relay/README.md`, `docs/product/mobile_user_flow.md`, sprint closeout, `OKR.md`, and `docs/process/okr_progress_log.md` later state the proof boundary and no-percentage-lift rule.

## In Scope

- Add `cloud_hosted_mobile_web_degradation_passthrough` as a Docker/local software-proof capability.
- Pass through the safe `remote_readiness.degradation_state` classes already used by Robot/mobile contracts:
  - `auth_failed`
  - `cloud_poll_backoff`
  - `manual_takeover_required`
  - `command_pending`
  - `command_expired`
  - `command_duplicate_deduped`
  - `command_id_conflict`
  - `command_sequence_regression`
  - `cloud_unreachable`
  - `malformed_response`
  - existing `status_stale` / `status_missing` handling where applicable
- Preserve read-only hosted shell behavior and fail-closed command gates.
- Add focused backend and mobile tests, JSON fixture validation, and required `rg` evidence.
- Update product docs during implementation closeout, not in this planning-only task.

## Out Of Scope

- Real public HTTPS/TLS, real 4G/SIM, real phone device/browser behavior, production app, PWA prompt/userChoice, OSS/CDN live traffic, production DB/queue connectivity, production worker/migration/cutover, external cloud proof, HIL, WAVE ROVER/UART, Nav2/fixed-route proof, route/elevator field pass, dropoff/cancel completion, delivery result, or delivery_success.
- Any hardware, vendor, serial, UART, WAVE ROVER, ESP32, Orange Pi, voltage, pinout, firmware, or mechanical change.
- Any new control endpoint, replay/resubmit behavior, ACK/cursor request from mobile, or raw diagnostics fetch from degraded states.
- Any claim that PR #5 `PRRT_kwDOSWB9286CJ3tX` is resolved or that comment `3269642220` means material acceptance.

## Core User Flow

1. The robot/relay has a latest status with safe `remote_readiness.degradation_state`.
2. The cloud-hosted same-origin phone entry calls `GET /api/status`.
3. The adapter returns `state=status_present` only as transport presence while also returning the exact safe `remote_readiness.degradation_state`, `proof_boundary=software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
4. The phone shell displays the specific degraded state with safe Chinese copy.
5. Start Delivery, Confirm Dropoff, and Cancel remain disabled; Diagnostics and support-safe context may remain visible.

## Priority And Acceptance Criteria

### P0 Acceptance

- `/api/status` preserves specific safe degradation state rather than losing it behind only `status_present`.
- The exact proof boundary appears as `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate`.
- Every passthrough degraded state keeps `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Mobile shell renders the state-specific copy and keeps Start Delivery / Confirm Dropoff / Cancel disabled.
- Safe output contains no bearer token, Authorization header, DB/queue URL, OSS AK/SK, raw ROS topic, `/cmd_vel`, serial/UART details, WAVE ROVER detail, local path, traceback, checksum, or complete raw artifact.

### P1 Acceptance

- Documentation states this is Docker/local software proof only and not real external O5 proof.
- Tests cover at least one representative backend passthrough fixture and one representative mobile fixture, with required strings proving the fail-closed boundary.
- Product closeout keeps Objective 5 about 68% unless real external cloud/phone materials arrive.

## Responsibility Matrix

| Area | Owner | Expected Output |
| --- | --- | --- |
| Cloud-hosted `/api/status` adapter | Robot Platform Engineer | Safe passthrough, backend tests, cloud relay README/interface docs |
| Mobile shell rendering and fixture | User Touchpoint Full-Stack Engineer | Fixture, parser/rendering, disabled controls, mobile tests, product mobile doc update |
| Sprint closeout and OKR wording | Product Manager / OKR Owner | `tech-done.md`, `side2side_check.md`, `final.md`, OKR/progress-log update after implementation |

## Risks, Blockers, And Evidence Chain Gaps

- Risk: `status_present` is misread as remote readiness. Mitigation: acceptance requires exact `remote_readiness.degradation_state` and fail-closed flags.
- Risk: mobile copy implies delivery success or safe remote control. Mitigation: require `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and disabled controls.
- Risk: local Docker proof is mistaken for O5 completion. Mitigation: close as `software_proof_docker_cloud_hosted_mobile_web_degradation_passthrough_gate` only and preserve Objective 5 at about 68%.
- Risk: raw relay or diagnostics data leaks into phone JSON. Mitigation: backend and mobile tests must assert redaction boundaries.
- Remaining evidence gaps: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, production app/device, true phone/browser evidence, HIL, WAVE ROVER/UART, route/elevator field pass, delivery result, and PR #5 reviewer resolution remain missing.

## Sprint Docs To Update Later

- `tech-done.md`: actual Engineer changes, validation output, deviations, and evidence boundary.
- `side2side_check.md`: Product acceptance table for state-specific passthrough and fail-closed phone behavior.
- `final.md`: conservative OKR result and remaining risks.
- `OKR.md`: no expected percentage lift; update only after implementation evidence.
- `docs/process/okr_progress_log.md`: software-proof entry only.
