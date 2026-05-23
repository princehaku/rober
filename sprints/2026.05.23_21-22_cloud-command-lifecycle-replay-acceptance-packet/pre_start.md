# Cloud Command Lifecycle Replay Acceptance Packet Pre Start

## sprint_type

sprint_type: epic

Run time: 2026-05-23 21:05 Asia/Shanghai

## User Value And Product North Star

Product north star: a low-cost phone-first trash delivery robot whose remote command lifecycle can be safely understood, accepted, and handed off by support / field owners before real cloud, real phone, real terminal-result, or delivery evidence arrives.

This sprint advances Objective 5 by turning the existing `cloud_command_lifecycle_replay_drill` into `cloud_command_lifecycle_replay_acceptance_packet`: a support / field-owner acceptance contract that packages safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, pending terminal result, next required evidence, and owner-facing acceptance status.

The user value is acceptance clarity. A support operator or field owner should be able to answer "what evidence do we have, what is still pending, and what must be collected next" without reading raw cloud logs, ACK cursors, ROS topics, local paths, credentials, or Robot internals.

## Background Evidence

- `OKR.md` 4.1 shows Objective 5 is the lowest objective at about 68%; Objective 1 is about 81%; Objective 2, Objective 3, and Objective 4 are about 99%.
- Latest sprint `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/final.md` completed `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`. It is not real external cloud proof, not true phone/browser proof, not verified terminal result, and not delivery success.
- GitHub PR #5 planning evidence remains split: `PRRT_kwDOSWB9286CJ3tQ` resolved, `PRRT_kwDOSWB9286CJ3tU` resolved, and `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`. This sprint must not imply PR #5 is fully resolved and must not repeat a local hardware-material wrapper.
- Recent work already covered O4 browser proof refresh and O5 cloud command lifecycle replay drill. This sprint stays on O5 but must move a concrete follow-up feature package, not only add tests.
- Current host has Docker/local proof only and no real hardware. This sprint must preserve `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR Mapping

- Objective 5: direct target. Build a cloud command lifecycle replay acceptance packet as the next O5 support/field-owner contract after replay drill.
- Objective 4: mobile/web should expose a read-only acceptance packet panel, but this remains local software proof and not true phone/browser proof.
- Objective 1: PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint does not change hardware, sensor, vendor-source, WAVE ROVER, UART, HIL, 2D LiDAR, or ToF claims.
- Objective 2 and Objective 3: this sprint does not prove route/elevator runtime, Nav2/fixed-route runtime, verified terminal delivery/dropoff/cancel result, or delivery success.

## Core Grasp

The core grasp is `cloud_command_lifecycle_replay_acceptance_packet`: turn the replay drill into a structured acceptance packet that support / field owners can review safely and use to request the next real evidence.

Required boundary strings:

- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

## Scope

In scope:

- Define a safe acceptance packet contract derived from the existing replay drill summary.
- Keep one safe `command_id` tied to one safe `evidence_ref`.
- Preserve lifecycle timeline, ACK semantics, pending terminal result, support acceptance status, owner handoff, and next required evidence.
- Surface the packet through Robot/API diagnostics and mobile/web in read-only form.
- Update related `docs/` files during implementation so diagnostics, remote 4G, and mobile user-flow contracts stay current.
- After implementation, Product Owner records conservative closeout in sprint docs, `OKR.md`, and `docs/process/okr_progress_log.md`.

Out of scope:

- Enabling Start Delivery, Confirm Dropoff, Cancel, command replay/resubmit, ACK posting, cursor mutation, diagnostics mutation, material upload, GitHub review action, robot commands, Nav2, WAVE ROVER, UART, HIL, or production cloud actions.
- Claiming real external cloud proof, public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, verified terminal result, route/elevator field pass, delivery result, delivery success, or PR #5 resolution.
- Changing hardware config, sensor assumptions, vendor-source claims, serial/UART setup, WAVE ROVER parameters, launch defaults, or physical packaging.

## Parallel Owners

- Robot Platform Engineer owns Robot/API safe alias, diagnostics summary, unit tests, and diagnostics / remote 4G docs.
- User Touchpoint Full-Stack Engineer owns `mobile/web` read-only acceptance packet panel, fixture, tests, and mobile user-flow docs.
- Product Owner owns this planning chain now and later owns `tech-done.md`, `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` after worker evidence lands.

Workers are expected to run in parallel when implementation starts. They must not overwrite parallel edits; each owner must keep to its file range and reconcile against current file content.

## Risks And Blockers

- This host has no real hardware; all proof remains Docker/local `software_proof`.
- An "acceptance packet" name could be misread as accepted delivery. The packet must explicitly mean support / field-owner review readiness, not delivery acceptance.
- Mobile/web can accidentally look actionable; Start Delivery, Confirm Dropoff, and Cancel must remain disabled.
- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; this sprint must not convert that unresolved hardware material thread into an O1 claim.
- Objective 5 cannot lift unless real external cloud, true phone/browser, production DB/queue, or verified terminal-result material arrives later.

## Sprint Documents To Create Or Update

Initial planning documents:

- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/pre_start.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/prd.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/tech-plan.md`

After implementation and validation:

- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/tech-done.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/side2side_check.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`
