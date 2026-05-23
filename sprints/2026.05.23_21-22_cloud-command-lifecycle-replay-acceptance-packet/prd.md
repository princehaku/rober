# Cloud Command Lifecycle Replay Acceptance Packet PRD

Run time: 2026-05-23 21:05 Asia/Shanghai

## 1. Product North Star

The product north star is a phone-first autonomous trash delivery robot whose cloud command lifecycle can be safely accepted, explained, and handed off by support / field owners before real external cloud and field proof exists.

`cloud_command_lifecycle_replay_acceptance_packet` is not a control feature and not a delivery-success claim. It is a safe acceptance contract that packages replay drill evidence into a support / field-owner review artifact.

## 2. User Value

Primary users:

- Support operator reviewing a cloud command whose ACK exists but terminal delivery/dropoff/cancel result is still pending.
- Field owner collecting the next evidence needed for Objective 5 closeout.
- Product Owner deciding whether O5 can move or must stay blocked by missing external proof.

User jobs:

- See one safe acceptance packet without raw cloud logs.
- Confirm the packet's safe `command_id` and safe `evidence_ref`.
- Understand ACK semantics: accepted/processing is not delivery success.
- See the lifecycle timeline and terminal-result pending status.
- Know exactly what evidence is missing next.
- Share safe owner handoff copy without exposing credentials, paths, ROS topics, ACK cursors, or Robot internals.

## 3. OKR Mapping

Objective 5 is the target because `OKR.md` 4.1 currently shows Objective 5 at about 68%, the lowest score.

This sprint advances Objective 5 inside a strict software-proof boundary:

- It moves from `cloud_command_lifecycle_replay_drill` to `cloud_command_lifecycle_replay_acceptance_packet`.
- It keeps `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- It keeps `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

No OKR percentage lift is expected unless later real external evidence arrives.

Non-target objectives:

- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this PRD does not prove mandatory sensor vendor source, procurement, installation, calibration, WAVE ROVER, UART, or HIL.
- Objective 2 and Objective 3 remain about 99%. This PRD does not prove route/elevator field pass, Nav2/fixed-route runtime, terminal result, dropoff/cancel completion, or delivery success.
- Objective 4 remains about 99%. Mobile/web may render the packet, but this is not true phone/browser proof.

## 4. KR Breakdown

KR 5.1 Acceptance packet readiness:

- Robot/API provides a sanitized acceptance packet derived from the existing command lifecycle replay drill summary.
- The packet contains safe `command_id`, safe `evidence_ref`, replay timeline, ACK semantics, terminal result status, packet review status, owner handoff, next required evidence, and support-safe copy.
- Missing, conflicting, or unsafe material fails closed.

KR 5.2 Phone-safe visibility:

- Mobile/web renders the acceptance packet as a read-only panel.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel has no raw diagnostics fetch, replay/resubmit, ACK/cursor mutation, material upload, review action, GitHub action, or robot side effect.

KR 5.3 Evidence boundary discipline:

- All outputs preserve `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- All outputs preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Docs state that this is not real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, route/elevator field pass, verified terminal result, delivery result, delivery success, or PR #5 resolution.

## 5. Core Requirements

### Robot/API Requirements

- Add `cloud_command_lifecycle_replay_acceptance_packet` and `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` as safe diagnostics aliases.
- Consume only sanitized fields from the existing lifecycle replay drill summary.
- Reject unsafe or conflicting source material.
- Preserve safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, terminal result pending status, packet status, owner handoff, next required evidence, and support-safe copy.
- Fail closed if safe `command_id` or safe `evidence_ref` is missing.
- Never create command replay/resubmit, ACK posting, cursor mutation, persistence mutation, Nav2, WAVE ROVER, UART, or HIL behavior.

### Mobile/Web Requirements

- Add fixture coverage for `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`.
- Render a read-only "云命令生命周期验收包" panel.
- Show safe command id, safe evidence ref, timeline, ACK semantics, pending terminal result, packet status, owner handoff, next required evidence, support copy availability, evidence boundary, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep primary actions disabled with `primary_actions_enabled=false`.
- Do not expose raw JSON, local paths, credential-bearing URLs, bearer tokens, Authorization headers, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, ACK payloads, cursors, or success claims.

### Product Requirements

- Keep this sprint under Objective 5.
- Ensure final closeout does not lift OKR percentage unless real external proof is added by another owner with evidence.
- Record remaining material gaps in sprint closeout, `OKR.md`, and `docs/process/okr_progress_log.md`.
- Confirm `docs/` updates land with the responsible Robot and Full-Stack implementation owners.

## 6. Priority And Acceptance Criteria

Priority P0:

- Safe acceptance packet summary exists in Robot/API diagnostics.
- It is read-only, fail-closed, and covered by unit tests.
- Required false-state flags are preserved.

Priority P1:

- Mobile/web renders the packet safely from fixture and API-shaped diagnostics payloads.
- Unit tests confirm actions stay disabled and unsafe copy is blocked.

Priority P2:

- Docs under `docs/interfaces/operator_gateway_diagnostics.md`, `docs/product/remote_4g_mvp.md`, and `docs/product/mobile_user_flow.md` describe the new contract.
- Sprint closeout later updates `OKR.md` and `docs/process/okr_progress_log.md`.

Acceptance criteria:

- Robot validation commands in `tech-plan.md` pass.
- Full-Stack validation commands in `tech-plan.md` pass.
- Product closeout later records actual evidence and remaining risk.
- No output claims HIL, real phone/browser proof, real external cloud, real public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue, route/elevator field pass, verified terminal result, delivery result, delivery_success=true, primary_actions_enabled=true, safe_to_control=true, or PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution.

## 7. Responsible Engineers

- Robot Platform Engineer: Robot/API diagnostics, safe alias, validation, and related interface/product docs.
- User Touchpoint Full-Stack Engineer: mobile/web panel, fixture, tests, and mobile user-flow docs.
- Product Owner: planning docs now; after implementation, closeout docs, `OKR.md`, and progress log.

## 8. Risks, Blockers, Evidence Chain

Known risks:

- Docker/local proof can be mistaken for real cloud proof. Copy must explicitly say this is `software_proof` and `not_proven`.
- "Acceptance packet" can sound like accepted delivery. The feature must mean support / field-owner acceptance readiness only.
- Mobile copy must not look like a green success state when ACK is only accepted/processing.

Known blockers:

- No real hardware on this host.
- No true phone/browser evidence.
- No real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or external probe material.
- Real route/elevator/terminal result material remains missing.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.

Evidence to collect later:

- Worker validation logs.
- Safe fixture showing `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- Robot/API summary showing packet status, owner handoff, and next required evidence.
- Mobile/web rendered proof that Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- Closeout docs preserving `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## 9. Sprint Documents

Created in planning:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Required after implementation:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
