# PRD - Cloud command lifecycle support owner-response review handoff

- sprint_type: epic
- sprint: `2026.05.24_16-17_cloud-command-lifecycle-support-owner-response-review-handoff`
- capability: `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`
- proof boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`

## 1. User Value And Product North Star

Remote support must be able to inspect a command lifecycle acceptance packet, understand the owner-response review decision, and hand the next action to the correct owner/reviewer without accidentally implying the robot is safe to control or that delivery succeeded.

The product north star remains a phone-safe, support-safe command lifecycle: every visible state must say what is known, what is missing, who owns the next evidence, and whether primary actions are allowed. In this sprint the answer remains fail-closed: `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## 2. OKR Mapping

- Objective 5：云中转 + OSS/CDN 数据通路产品化。`OKR.md` 4.1 currently records this as the lowest Objective, about 68%. This sprint targets Objective 5 by extending the Docker/local command lifecycle support branch from owner-response review decision to review handoff.
- Objective 1：硬件协议可信底盘。Only retained as a boundary because PR #5 thread `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `hardware_material_pending`; this sprint does not resolve PR #5 and does not change hardware proof.
- Objectives 2/3：route/elevator and navigation remain unchanged. This sprint does not prove route/elevator field pass, Nav2/fixed-route runtime, dropoff/cancel completion, or delivery success.
- Objective 4：mobile/web may render a read-only panel, but this is `not true phone/browser proof` and does not change the O4 percentage.

## 3. KR Breakdown Or Update

KR kept unchanged for this planning sprint:

- O5 KR for command lifecycle support handoff becomes one rung more explicit by planning the review-handoff state after review decision.
- O5 completion stays about 68%; this planning sprint and the later Docker/local implementation must record `no OKR percentage lift`.
- A future OKR lift still requires at least one real external proof source: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue connectivity, worker/cutover evidence, true phone/browser proof, or verified terminal delivery/dropoff/cancel result.

No KR percentage update is authorized by this sprint planning task.

## 4. Core Lever

The core lever is a safe handoff package:

- Robot/API turns `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_decision` into `cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff`.
- Mobile/web renders the same safe handoff summary after the existing review-decision panel.
- Product closeout later records that this is still `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_support_handoff_owner_response_review_handoff_gate`.

## 5. Scope

In scope for later implementation:

- Safe command lifecycle review-handoff summary.
- Safe `command_id` and safe `evidence_ref` display.
- Review decision, handoff owner, handoff reason, next required evidence, blocker summary, owner/support/reviewer routing, and safe copy state.
- Explicit false flags: `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Documentation updates in `docs/product/remote_4g_mvp.md` and `docs/product/mobile_user_flow.md`.

Out of scope:

- Robot command replay, resubmit, ACK/cursor mutation, material upload, GitHub mutation, diagnostics mutation, raw artifact fetch, Nav2 trigger, WAVE ROVER/UART access, or any control path.
- PR #5 resolution. Thread `PRRT_kwDOSWB9286CJ3tX` remains `hardware_material_pending`.
- True phone/browser proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, verified terminal result, HIL, route/elevator field pass, or delivery success.

## 6. Priority And Acceptance

Priority order:

1. Preserve the proof boundary and negative claims.
2. Add Robot/API safe summary with tests.
3. Add mobile/web read-only panel with fixture and tests.
4. Close out Product docs only after implementation evidence exists.

Acceptance:

- Task A focused Robot/API commands pass.
- Task B focused mobile/web commands pass.
- Task C closeout commands pass after A/B land.
- Planning-only validation commands pass for these three sprint docs.
- No files outside the requested planning scope are changed during this task.

## 7. Responsible Engineers

- Robot Platform Engineer: Task A, Robot/API summary/status/diagnostics embedding.
- User Touchpoint Full-Stack Engineer: Task B, read-only mobile/web panel and fixture.
- Product Manager / OKR Owner: Task C, closeout docs, OKR/progress-log wording after evidence exists.

## 8. Risks, Blocks, And Evidence Chain

- Risk: review-handoff copy could be mistaken for verified terminal result. Required mitigation: every surface keeps `not verified terminal result`, `delivery_success=false`, and `no OKR percentage lift`.
- Risk: mobile fallback could consume unsafe diagnostics. Required mitigation: tests reject raw paths, credentials, ROS/control terms, `/cmd_vel`, ACK cursor fields, checksums, complete artifacts, and success/control wording.
- Risk: O1/PR #5 scope creep. Required mitigation: `PRRT_kwDOSWB9286CJ3tX` remains only a boundary fact, still unresolved / `hardware_material_pending`.
- Block: this Docker-only host has no real hardware, real phone, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, or verified terminal result evidence.

Evidence chain required before closeout:

- Task A command output and touched-file list.
- Task B command output and touched-file list.
- Product side-by-side check proving proof boundary, false flags, PR #5 boundary, and `no OKR percentage lift` stayed intact.

## 9. Sprint Documents

Created now:

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

Must be created or updated later after implementation evidence:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
