# Cloud Command Lifecycle Replay Drill Pre Start

## sprint_type

sprint_type: epic

Run time: 2026-05-23 20:21 Asia/Shanghai

## User Value And Product North Star

Product north star: a low-cost phone-first trash delivery robot whose remote command state is understandable to ordinary users, support, and field owners without exposing raw robot internals or pretending local proof is real delivery.

This sprint advances Objective 5 by turning the existing `cloud_command_lifecycle_audit_export` safe summary into `cloud_command_lifecycle_replay_drill`: a replayable, support-facing drill artifact that lets support / field owner复演 one command lifecycle timeline, ACK semantics, pending terminal result, and next evidence needs from the same safe `command_id` and `evidence_ref`.

The user value is practical debugging: when a cloud command is stuck between accepted/processing ACK and missing terminal delivery/dropoff/cancel result, support can hand over one sanitized replay packet instead of asking users or field owners to inspect cloud logs, ROS topics, ACK cursors, local paths, or raw diagnostics.

## Background Evidence

- `OKR.md` 4.1 shows Objective 5 is lowest at about 68%; Objective 1 is about 81%; Objective 2, Objective 3, and Objective 4 are about 99%.
- `sprints/2026.05.23_19-20_mobile-current-panel-browser-proof-refresh-field-evidence-followup/final.md` only completed local Chromium/current-panel proof. It was not true phone/browser proof, not real public cloud, not real 4G/SIM, not HIL, not delivery success, and did not lift OKR percentage.
- `sprints/2026.05.23_18-19_field-evidence-rerun-acceptance-owner-response-reviewer-ack-followup-escalation-status/final.md` states real route/elevator/terminal result material is still missing.
- GitHub PR #5 thread state used for planning: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`; reviewer still requests vendor source for mandatory sensor assumptions.
- Current host has Docker/local proof only and no real hardware. This sprint must not claim HIL, real phone, real public internet, real cloud, real delivery, real terminal result, or PR #5 resolution.

## OKR Mapping

- Objective 5: direct target. Build a replayable command lifecycle support drill from existing cloud lifecycle safe summary, preserving O5 evidence boundary.
- Objective 4: mobile/web should expose a read-only drill panel or copy surface, but this is still not true phone/browser proof.
- Objective 1: PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not change hardware claims or sensor assumptions.
- Objective 2 and Objective 3: no route/elevator runtime, Nav2/fixed-route runtime, dropoff/cancel completion, or delivery success is proven.

## Core Grasp

The core grasp is `cloud_command_lifecycle_replay_drill`: make the existing audit/export summary replayable for support without adding any control path.

Required boundary strings:

- `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Scope

In scope:

- Create a safe replay drill summary from the existing lifecycle audit/export summary.
- Bind one safe `command_id` to one safe `evidence_ref`.
- Preserve timeline order across enqueue, robot poll/status, ACK lookup or accepted/processing state, pending terminal result, and next required evidence.
- Provide support-safe copy/export text that can be replayed by humans as a drill.
- Surface the drill through Robot/API diagnostics and mobile/web in read-only form.
- Update docs under `docs/interfaces/` and `docs/product/` during implementation so the contract stays current.

Out of scope:

- Enabling Start Delivery, Confirm Dropoff, Cancel, ACK posting, cursor mutation, command replay/resubmit, robot commands, Nav2, WAVE ROVER, HIL, or production cloud actions.
- Claiming real external cloud, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, route/elevator field pass, verified terminal result, dropoff/cancel completion, delivery result, delivery success, or PR #5 resolution.
- Changing hardware config, sensor assumptions, vendor source claims, serial/UART setup, WAVE ROVER parameters, launch defaults, or physical packaging.

## Parallel Owners

- Robot Platform Engineer owns Robot/API diagnostics and tests.
- User Touchpoint Full-Stack Engineer owns `mobile/web` consumption and tests.
- Product Owner owns sprint closeout, OKR update, and progress log after worker evidence lands.

Workers are expected to run in parallel. Do not overwrite parallel edits; each owner must keep to its file range and reconcile against current file content.

## Risks And Blockers

- This host has no real hardware; all proof remains Docker/local `software_proof`.
- The replay drill can improve support readiness, but it cannot lift Objective 5 percentage unless real external materials arrive.
- The UI could accidentally look actionable; mobile/web must keep primary actions disabled and the copy must explicitly say ACK is not delivery success.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` is still unresolved / `hardware_material_pending`; this sprint must not imply vendor source alignment is done.

## Sprint Documents To Create Or Update

Initial planning documents:

- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/pre_start.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/prd.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/tech-plan.md`

After implementation and validation:

- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/tech-done.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/side2side_check.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

