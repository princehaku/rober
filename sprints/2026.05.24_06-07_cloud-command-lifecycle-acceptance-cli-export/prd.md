# Cloud Command Lifecycle Acceptance CLI Export PRD

Run time: 2026-05-24 06:05 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Product Problem

The previous sprint proved the command lifecycle replay acceptance packet inside Docker/local cloud-relay smoke. That is valuable deploy freshness, but the packet is still awkward for support and field owners: the direct artifact is embedded in smoke proof rather than available through an explicit CLI export.

The product gap is a support workflow gap. A reviewer needs a deterministic JSON export for `cloud_command_lifecycle_replay_acceptance_packet` without starting a service, scraping logs, replaying commands, posting ACKs, mutating cursors, or touching robot hardware.

## User Value And Product North Star

User value:

- Support can export one sanitized command lifecycle acceptance packet for handoff and review.
- Field owners can inspect ACK semantics, terminal-result pending state, owner handoff, and next required evidence without seeing raw ROS2, serial, credentials, or local paths.
- Engineers keep the support packet as a bounded CLI artifact instead of broadening it into command replay or delivery proof.

Product north star:

Build a phone-first, cloud-mediated trash delivery robot where ordinary users never see ROS2 internals or raw control topics, and support can diagnose cloud command lifecycle state while all unsafe robot actions remain disabled.

## OKR Mapping

Primary OKR:

- Objective 5: 云中转 + OSS/CDN 数据通路产品化, currently about 68% and the lowest Objective.

KR mapping:

- O5 KR1: strengthens the `trashbot.remote.v1` command/status/ACK support path by making a safe command lifecycle acceptance packet directly exportable from the relay CLI.
- O5 KR6: preserves graceful degradation and support diagnostics when terminal result is pending, external proof is missing, or field-owner review still needs more evidence.

Non-goals:

- This is no OKR percentage lift.
- Objective 1 is unchanged; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live evidence changes.
- Objectives 2/3/4 are unchanged because this sprint does not run real route/elevator, Nav2/fixed-route, true phone/browser, or delivery validation.

## KR Decomposition

KR-A: CLI export creates a sanitized JSON packet.

- Required capability marker: `cloud_command_lifecycle_replay_acceptance_packet_cli_export`.
- Required boundary marker: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`.
- Export must include safe packet identity, `cloud_command_lifecycle_replay_acceptance_packet`, ACK semantics, terminal-result pending state, owner handoff, next required evidence, and false control flags.
- Export must reject or omit unsafe material: bearer tokens, Authorization headers, signed URLs, raw paths, `/cmd_vel`, ROS topics, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, and true-state control flags.

KR-B: CLI help and docs make the boundary obvious.

- CLI `--help` must show the export flag or capability marker clearly enough for support to discover it.
- `cloud-relay/README.md` must document the CLI export command and expected JSON validation boundary.
- `docs/product/remote_4g_mvp.md` must state that the CLI export is support / field-owner review material only.

KR-C: Robot diagnostics remains read-only and reusable.

- Robot diagnostics should remain the single safe source for existing packet semantics when possible.
- If Task A can reuse the existing builder/summary, Task B should not change Robot files.
- If a missing marker requires a narrow Robot change, it must preserve `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`, and `not_proven`.

KR-D: Product closeout keeps OKR conservative.

- `tech-done.md`, `side2side_check.md`, and `final.md` must record Task A/B actual results and validation.
- `OKR.md` and `docs/process/okr_progress_log.md` must be updated only after Task A/B finish.
- Objective 5 remains about 68% unless real external cloud, production queue/DB, verified terminal result, or true phone/browser evidence appears outside this plan.

## Core Lever For This Round

The core lever is making the existing Docker-smoke-verified acceptance packet directly exportable by CLI. This is functional forward motion for support and field review, not another read-only test wrapper and not a hardware claim.

## What Needs To Be Done

1. Full-Stack adds a CLI export path in `remote_cloud_relay.py` that writes a sanitized JSON artifact for `cloud_command_lifecycle_replay_acceptance_packet_cli_export`.
2. Full-Stack updates `cloud-relay/README.md` and `docs/product/remote_4g_mvp.md` with the command, JSON validation expectations, and evidence boundary.
3. Robot checks whether existing diagnostics builders already provide the required fields. Robot stays read-only unless a missing marker blocks CLI export reuse.
4. Product closes the sprint after Task A/B, updates closeout docs, then updates `OKR.md` and `docs/process/okr_progress_log.md` conservatively.

## Priority And Acceptance Criteria

P0 acceptance:

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py` passes.
- CLI `--help` exposes the CLI export marker or flag.
- CLI writes a temporary JSON artifact that includes `cloud_command_lifecycle_replay_acceptance_packet_cli_export` and `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`.
- Python JSON validation confirms false flags: `delivery_success is False`, `primary_actions_enabled is False`, `safe_to_control is False`, and `not_proven` is present.
- Focused `rg` and scoped `git diff --check` pass.

P1 acceptance:

- Robot read-only validation confirms diagnostics still expose safe acceptance-packet fields for reuse.
- No task claims real cloud, public HTTPS/TLS, true phone/browser, production DB/queue, worker/cutover, HIL, route/elevator field pass, delivery result, or PR #5 resolution.

## Responsible Engineers

- Task A: User Touchpoint Full-Stack Engineer.
- Task B: Robot Platform Engineer.
- Task C: Product Manager / OKR Owner.

## Risks And Evidence Gaps

- The CLI export may need a small adapter around an existing Robot/API builder. That is acceptable only if it preserves single-source semantics and does not duplicate unsafe logic.
- This sprint does not address real O5 blockers: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result.
- This sprint does not address the O1 blocker: PR #5 `PRRT_kwDOSWB9286CJ3tX` hardware materials and real HIL evidence.
- The result is still `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`, not delivery success and not OKR percentage lift.

## Sprint Documents

Planning documents created now:

- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/pre_start.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/prd.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/tech-plan.md`

Implementation closeout documents to create later:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
