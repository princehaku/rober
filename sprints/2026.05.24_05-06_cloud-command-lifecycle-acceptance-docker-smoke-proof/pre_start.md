# Cloud Command Lifecycle Acceptance Docker Smoke Proof Pre-Start

Run time: 2026-05-24 05:36 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Sprint Goal

Create the next Epic sprint for `cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof`.

The sprint should connect the already landed `cloud_command_lifecycle_replay_acceptance_packet` capability to `cloud-relay/scripts/docker_smoke.sh` so the independent cloud-relay deploy proof checks the acceptance packet markers during Docker/local smoke.

## User Value And Product North Star

The user value is freshness and deploy confidence for the cloud command lifecycle support packet. A support reviewer should be able to trust that the Docker cloud-relay proof still sees the read-only acceptance packet contract, instead of only seeing API/mobile unit proof from the earlier sprint.

The product north star remains a low-cost phone-first trash delivery robot that can be operated through cloud relay without exposing raw robot control paths. This sprint is not a new user feature; it is a deployment-proof guard that keeps the cloud command lifecycle evidence chain honest.

## Evidence Read Before Start

- `AGENTS.md`: Epic sprint must use real sprint records, owner/file split, fenced validation, and no hardware claims without vendor-backed materials.
- `OKR.md` 4.1 at 2026-05-24 05:11: Objective 5 is the lowest Objective at about 68%; Objective 1 is about 81%; Objectives 2/3/4 are about 99%.
- `sprints/2026.05.24_04-05_mobile-current-panel-browser-proof-refresh-owner-response-bridge/final.md`: local-only wrapper work must not create OKR progress; O5 still lacks real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, and verified terminal result.
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/final.md`: Robot/API and mobile already expose the read-only acceptance packet, but the independent `cloud-relay/scripts/docker_smoke.sh` does not yet assert that capability.
- `cloud-relay/scripts/docker_smoke.sh`: current smoke covers readiness, blocked preflight, DB/queue gates, public ingress/TLS gates, worker migration, worker cutover/drain, command/ACK, backup/restore, and state recovery; it has no explicit `cloud_command_lifecycle_replay_acceptance_packet` marker check.
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` remains `is_resolved=false` / `hardware_material_pending`; this sprint does not attempt to prove hardware on a Docker-only host.

## Scope Boundary

Target evidence boundary:

`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`

This sprint is explicitly:

- Docker/local cloud-relay smoke freshness for the already landed acceptance packet.
- no OKR percentage lift.
- not real external cloud proof.
- not public HTTPS/TLS proof.
- not 4G/SIM proof.
- not OSS/CDN live traffic.
- not production DB/queue proof.
- not worker/cutover proof.
- not true phone/browser proof.
- not HIL.
- not delivery success.
- not PR #5 resolution.

## Owners

- Task A: User Touchpoint Full-Stack Engineer owns the cloud-relay smoke integration and cloud-relay product docs.
- Task B: Robot Platform Engineer owns read-only diagnostics contract confirmation, with only narrowly scoped diagnostics/docs edits if the smoke proof reveals a missing marker.
- Task C: Product Manager / OKR Owner owns closeout records, OKR/progress-log updates after implementation, and evidence-boundary language.

## Previous Blocker Scan

The last three closeouts all kept Objective 5 at about 68% with no OKR percentage lift, and kept PR #5 `PRRT_kwDOSWB9286CJ3tX` unresolved. This sprint does not consume the same missing external-material blocker as progress; it creates a deploy-smoke regression guard for a capability already landed.

If Docker itself is unavailable, the sprint may close only as a syntax/marker-plan proof with the Docker block recorded in `tech-done.md` and `final.md`. That blocked result must not count as O5 progress.

## Sprint Documents To Create Or Update

This Epic sprint must use the full chain:

- `pre_start.md` now created.
- `prd.md` now created.
- `tech-plan.md` now created.
- `tech-done.md` to be updated by implementation/validation workers.
- `side2side_check.md` to be created during Product closeout.
- `final.md` to be created during Product closeout.

Closeout may later update `OKR.md` and `docs/process/okr_progress_log.md`, but this planning task must not change them.
