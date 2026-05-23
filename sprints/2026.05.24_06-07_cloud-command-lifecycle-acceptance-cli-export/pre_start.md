# Cloud Command Lifecycle Acceptance CLI Export Pre-Start

Run time: 2026-05-24 06:05 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Sprint Goal

Create the next Epic sprint for `cloud_command_lifecycle_replay_acceptance_packet_cli_export`.

This sprint should let the independent cloud relay CLI directly export the command lifecycle replay acceptance packet that the previous Docker smoke already verified, so support and field owners can review the packet without scraping smoke logs or starting a long-running service.

Target evidence boundary:

`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`

## User Value And Product North Star

The user value is support-ready handoff speed. When a command lifecycle issue is being reviewed, a support or field owner should be able to run one explicit CLI export command and receive a sanitized JSON packet with ACK semantics, pending terminal-result status, owner handoff, next required evidence, and false control flags.

The product north star remains a low-cost phone-first trash delivery robot controlled through cloud relay without exposing ROS2 internals, raw robot control paths, serial details, WAVE ROVER details, or unsafe control toggles to ordinary users or support workflows.

## Evidence Read Before Start

- `AGENTS.md`: Epic sprint must use real sprint records, owner/file split, fenced validation, parallel Task A/B execution, and no hardware claims without vendor-backed materials.
- `OKR.md` 4.1 at 2026-05-24 05:16: Objective 5 is lowest at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md`: previous sprint completed `cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof` with `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`; it had no OKR percentage lift.
- `docs/product/remote_4g_mvp.md`: the acceptance packet is support / field-owner review metadata only, keeps `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`, and is not delivery success.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / `hardware_material_pending` per rerank evidence. This Docker-only host cannot turn that into Objective 1 HIL progress.

## Scope Boundary

This sprint is explicitly:

- CLI export for an existing Docker-smoke-verified command lifecycle replay acceptance packet.
- Support / field-owner review material only.
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`.
- no OKR percentage lift.
- not delivery success.
- not real external cloud proof.
- not public HTTPS/TLS proof.
- not 4G/SIM proof.
- not OSS/CDN live traffic.
- not production DB/queue proof.
- not worker/cutover proof.
- not true phone/browser proof.
- not verified terminal result.
- not route/elevator field pass.
- not Nav2/fixed-route runtime pass.
- not HIL, not WAVE ROVER/UART proof.
- not PR #5 resolution.

Required false states:

- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `not_proven`

## Owners

- Task A: User Touchpoint Full-Stack Engineer owns the independent cloud relay CLI export and cloud-relay/product docs.
- Task B: Robot Platform Engineer owns read-only diagnostics contract consultation, with only narrowly scoped diagnostics/docs edits if CLI export needs a missing builder or marker.
- Task C: Product Manager / OKR Owner owns closeout records, OKR/progress-log updates after Task A/B, and evidence-boundary language.

## Previous Blocker Scan

The last sprint closed as Docker/local smoke proof for an existing O5 packet, not as external cloud or delivery proof. This sprint does not consume missing public cloud, production DB/queue, phone/browser, hardware, or HIL evidence as progress. It advances the support workflow by making the already-smoked packet directly exportable by CLI.

The unresolved PR #5 review thread `PRRT_kwDOSWB9286CJ3tX` is a separate hardware-material blocker. It stays pending unless real reviewer/material evidence appears.

## Sprint Documents To Create Or Update

Planning documents created now:

- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/pre_start.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/prd.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/tech-plan.md`

Implementation and closeout documents to create or update later:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

This planning task must not modify `OKR.md`, previous sprint closeout docs, or any product/code file outside this fresh sprint directory.
