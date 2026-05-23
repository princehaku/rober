# Cloud Command Lifecycle Replay Drill PRD

Run time: 2026-05-23 20:21 Asia/Shanghai

## 1. Product North Star

The product north star is a phone-first autonomous trash collection robot whose remote command lifecycle is safe, explainable, and supportable before real cloud and field evidence exists.

`cloud_command_lifecycle_replay_drill` is not a control feature. It is a safe support drill that lets support / field owner replay what happened to one cloud command and identify the next required evidence without touching robot controls.

## 2. User Value

Primary users:

- Support operator reviewing a remote command whose ACK exists but terminal result is pending.
- Field owner collecting missing terminal delivery/dropoff/cancel material.
- Product owner deciding whether Objective 5 can progress or must stay blocked by missing external evidence.

User jobs:

- See one safe command lifecycle timeline without raw cloud logs.
- Understand ACK semantics: accepted/processing is not delivery success.
- See why terminal result is still pending.
- Copy a sanitized replay drill artifact to the field owner.
- Know the exact next evidence required for closeout.

## 3. OKR Mapping

Objective 5 is the target objective because `OKR.md` 4.1 currently shows Objective 5 at about 68%, the lowest score.

This sprint is a software-proof advancement inside Objective 5:

- It moves from static `cloud_command_lifecycle_audit_export` summary to replayable `cloud_command_lifecycle_replay_drill`.
- It keeps `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`.
- It keeps `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

No OKR percentage lift is expected unless later real external evidence arrives.

Non-target objectives:

- Objective 1 remains about 81%. PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this PRD does not prove vendor source for mandatory sensor assumptions.
- Objective 2 and Objective 3 remain about 99%. This PRD does not prove route/elevator field pass, Nav2/fixed-route runtime, terminal result, or delivery success.
- Objective 4 remains about 99%. Mobile/web may render the drill, but this is not true phone/browser proof.

## 4. KR Breakdown

KR 5.1 Support replay readiness:

- Robot/API provides a sanitized replay drill summary derived from existing command lifecycle safe summary.
- The summary contains safe `command_id`, safe `evidence_ref`, ordered timeline, ACK semantics, terminal result status, next required evidence, and support copy.
- Missing, conflicting, or unsafe material fails closed.

KR 5.2 Phone-safe visibility:

- Mobile/web renders the drill as a read-only panel.
- Start Delivery, Confirm Dropoff, and Cancel remain disabled.
- The panel has no raw diagnostics fetch, replay/resubmit, ACK/cursor mutation, or command side effect.

KR 5.3 Evidence boundary discipline:

- All outputs preserve `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`.
- All outputs preserve `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Docs state that this is not real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, route/elevator field pass, verified terminal result, delivery result, delivery success, or PR #5 resolution.

## 5. Core Requirements

### Robot/API Requirements

- Add `cloud_command_lifecycle_replay_drill` and `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary` as safe diagnostics aliases.
- Consume only sanitized fields from the existing lifecycle audit/export summary.
- Reject unsafe or conflicting source material.
- Preserve timeline order and make pending terminal result explicit.
- Produce support copy that describes replay steps without instructing users to send commands.
- Fail closed if safe `command_id` or safe `evidence_ref` is missing.

### Mobile/Web Requirements

- Add fixture coverage for `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary`.
- Render a read-only "云命令生命周期复演演练" panel.
- Show safe command id, safe evidence ref, timeline, ACK semantics, pending terminal result, next required evidence, and copy availability.
- Keep primary actions disabled with `primary_actions_enabled=false`.
- Do not expose raw JSON, local paths, URLs with credentials, bearer tokens, Authorization headers, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, or success claims.

### Product Requirements

- Keep this sprint under Objective 5.
- Ensure final closeout does not lift OKR percentage unless real external proof is added by another owner with evidence.
- Record remaining material gaps in sprint closeout, `OKR.md`, and `docs/process/okr_progress_log.md`.

## 6. Priority And Acceptance Criteria

Priority P0:

- Safe replay drill summary exists in Robot/API diagnostics.
- It is read-only, fail-closed, and covered by unit tests.
- Required false-state flags are preserved.

Priority P1:

- Mobile/web renders the drill safely from fixture and API-shaped diagnostics payloads.
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

- Docker/local proof can easily be mistaken for real cloud proof. Copy must explicitly say this is `software_proof` and `not_proven`.
- A "replay" name can sound like command replay. The feature must be a human-readable support drill only, not a command replay or resubmit action.
- Mobile copy must not look like a green success state when ACK is only accepted/processing.

Known blockers:

- No real hardware on this host.
- No true phone/browser evidence.
- No real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or external probe material.
- Real route/elevator/terminal result material remains missing.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.

Evidence to collect later:

- Worker validation logs.
- Safe fixture showing `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`.
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

