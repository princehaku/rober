# Cloud Manual Takeover Command Safety Guard PRD

## Product North Star And User Value

The user value is safety clarity during remote-control degradation. When the robot or operator flow requires manual takeover / human help, a normal phone user must see that the robot is not safe to command remotely and must not be offered primary controls that look available.

The product north star remains phone-first trash delivery: the phone is the user's control and recovery surface, but it must fail closed when the robot needs a human. `cloud_manual_takeover_command_safety_guard` closes the specific O5 gap where manual takeover is already listed under `command_safety` blockers but lacks an independent proof boundary/status guard.

## OKR Mapping

- Primary Objective: Objective 5, cloud relay / OSS-CDN data path productization, currently about 68%.
- Secondary Objective: Objective 4, phone user experience and production boundary, currently about 99%, because the phone must explain manual takeover without exposing raw robot details.
- Guarded Objective: Objective 1, currently about 81%, remains blocked by PR #5 `PRRT_kwDOSWB9286CJ3tX` and real hardware material. This sprint must not claim WAVE ROVER/UART/HIL or hardware-material progress.

This sprint does not raise OKR percentages by itself. It creates bounded `software_proof_docker_cloud_manual_takeover_command_safety_guard` evidence only.

## KR Breakdown

- KR-A Robot/API: represent `manual_takeover_required` as a phone-safe degraded remote-control state with `remote_ready=false`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `retry_hint=contact_support`, and `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`.
- KR-B Robot diagnostics: expose `robot_diagnostics_cloud_manual_takeover_command_safety_guard_summary` or equivalent safe summary through the existing diagnostics/status path without raw command payloads, ROS topics, serial details, WAVE ROVER details, credentials, or tracebacks.
- KR-C Mobile/Web: consume the Robot/API summary and render manual takeover / human help copy while keeping Start Delivery, Confirm Dropoff, and Cancel disabled.
- KR-D Product/Docs: update `docs/product/remote_4g_mvp.md` and `docs/product/mobile_user_flow.md` during execution closeout so manual takeover has a dedicated guard section and mobile consumption boundary.
- KR-E Evidence: provide focused backend/mobile tests and `rg` checks proving `manual_takeover_required`, `delivery_success=false`, `primary_actions_enabled=false`, and the evidence boundary appear in code/docs/fixtures.

## Scope

### In Scope

- Add a dedicated manual takeover command-safety degraded state.
- Keep the state local/Docker software proof only.
- Preserve the existing `trashbot.command_safety.v1` action contract and legacy action permissions.
- Provide phone-safe copy in Chinese-first language.
- Add focused tests and fixtures for the new state.
- Update sprint docs and product docs during execution.

### Out Of Scope

- Real public cloud deployment, real HTTPS/TLS, real 4G/SIM, production DB/queue, production worker/cutover, OSS/CDN live traffic, and true phone/browser validation.
- Any WAVE ROVER, ESP32, Orange Pi, UART, serial, voltage, pinout, firmware, or mechanical changes.
- Any change that enables primary actions while manual takeover / human help is active.
- Any attempt to resolve PR #5 `PRRT_kwDOSWB9286CJ3tX` or claim hardware-material availability.

## Core User Flow

1. The Robot/API receives or derives a manual-takeover/human-help condition.
2. Status/readiness reports `degradation_state=manual_takeover_required` and `proof_boundary=software_proof_docker_cloud_manual_takeover_command_safety_guard`.
3. Phone command safety sets Start Delivery, Confirm Dropoff, and Cancel to disabled.
4. The user sees safe copy such as: `需要人工接管；远程主操作已暂停，请按现场/支持指引处理。`
5. Diagnostics and support handoff remain visible with redacted, phone-safe evidence.

## Priority And Acceptance Criteria

### P0 Acceptance

- Robot/API exposes a deterministic safe manual takeover state using `manual_takeover_required`.
- Robot/API and mobile surfaces preserve `delivery_success=false` and `primary_actions_enabled=false`.
- The proof boundary is exactly `software_proof_docker_cloud_manual_takeover_command_safety_guard`.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled from the mobile user's point of view.
- Safe output contains no bearer tokens, Authorization headers, DB/queue URLs, OSS AK/SK, raw ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, local paths, tracebacks, checksums, or complete raw artifacts.

### P1 Acceptance

- Product docs explain that manual takeover is not delivery success, not true phone/browser proof, not external cloud proof, not HIL, and not PR #5 material resolution.
- Diagnostics/support copy gives the operator a clear next action: contact support or follow manual takeover procedure.
- Tests cover missing summary or unsafe summary as fail-closed rather than permissive.

## Responsibility Matrix

| Area | Owner | Expected Output |
| --- | --- | --- |
| Robot/API status and diagnostics | Robot Platform Engineer | Safe status/diagnostics summary, backend tests, docs/interface update if needed |
| Mobile/Web rendering and fixture | User Touchpoint Full-Stack Engineer | Fixture, parser/rendering behavior, disabled controls, mobile tests |
| Sprint closeout and evidence boundary | Product Manager / OKR Owner | `tech-done.md`, `side2side_check.md`, `final.md`, OKR/progress-log updates after implementation |

## Risks And Evidence Gaps

- Risk: manual takeover gets treated as a support-only message while primary controls remain enabled. Mitigation: acceptance requires `primary_actions_enabled=false` and mobile disabled buttons.
- Risk: ACK wording or diagnostics copy implies delivery success. Mitigation: require `delivery_success=false` and explicit non-delivery wording.
- Risk: another local O5 proof is mistaken for O5 completion. Mitigation: close as software proof only and keep Objective 5 about 68% unless real external cloud/phone materials appear.
- Risk: Objective 1 material blocker is blurred into O5 command-safety work. Mitigation: cite `PRRT_kwDOSWB9286CJ3tX` as unresolved/material pending and make no hardware claims.

## Sprint Docs To Update Later

- `tech-done.md`: actual Engineer changes, verification results, and deviations.
- `side2side_check.md`: product acceptance table for manual takeover fail-closed behavior.
- `final.md`: conservative OKR result and remaining risks.
- `OKR.md`: only after implementation closeout; no expected percentage lift.
- `docs/process/okr_progress_log.md`: software-proof entry only.

