# Cloud Command Lifecycle Acceptance Docker Smoke Proof PRD

Run time: 2026-05-24 05:36 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Product Problem

The repo already has a read-only `cloud_command_lifecycle_replay_acceptance_packet` across Robot/API and mobile surfaces. That packet helps support and field owners review ACK semantics, terminal-result pending state, owner handoff, next required evidence, and blocked proof boundaries.

The remaining gap is deployment freshness: `cloud-relay/scripts/docker_smoke.sh` proves many cloud-relay Docker/local contracts, but it does not explicitly check that the command lifecycle replay acceptance packet is present and fail-closed in the independent cloud-relay smoke path.

## User Value And Product North Star

User value:

- Support can rely on the cloud-relay Docker smoke as a single deploy proof that includes the command lifecycle acceptance packet.
- Field owners get a safer handoff packet because the smoke path asserts the same false states and redaction boundaries before a deploy is treated as locally fresh.
- Engineers avoid mistaking API/mobile unit proof for cloud-relay deploy proof.

Product north star:

Build a phone-first, cloud-mediated trash delivery robot where users never see ROS2 internals or raw control topics, and support can diagnose command lifecycle state without enabling unsafe robot actions.

## OKR Mapping

Primary OKR:

- Objective 5: 云中转 + OSS/CDN 数据通路产品化, currently about 68% and the lowest Objective.

KR mapping:

- O5 KR1: strengthens the `trashbot.remote.v1` command/status/ACK proof path by verifying the lifecycle acceptance packet inside the Docker cloud-relay smoke.
- O5 KR6: keeps graceful degradation and support diagnostics explicit when terminal result is pending or external proof is missing.

Non-goals:

- No Objective percentage increase is expected. This is no OKR percentage lift.
- Objective 1 is unchanged; PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending` unless live reviewer evidence changes.
- Objectives 2/3/4 are unchanged because this sprint does not run real route/elevator, Nav2/fixed-route, true phone/browser, or delivery validation.

## KR Decomposition

KR-A: Cloud-relay smoke explicitly validates acceptance packet markers.

- Required capability marker: `cloud_command_lifecycle_replay_acceptance_packet`.
- Required previous boundary marker: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- Required new smoke boundary marker: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`.
- Required false states: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Required safety copy: not true phone/browser proof, no external cloud proof, no production DB/queue, no HIL, no delivery success.

KR-B: Documentation makes the deploy-proof boundary obvious.

- `cloud-relay/README.md` must describe the new docker smoke assertion if Task A changes the smoke.
- `docs/product/remote_4g_mvp.md` must be updated only if the implementation changes the product-visible evidence contract or naming.
- The docs must keep the acceptance packet as support/review metadata, not command replay, ACK mutation, cursor mutation, robot control, or delivery acceptance.

KR-C: Product closeout keeps OKR conservative.

- `tech-done.md`, `side2side_check.md`, and `final.md` must record whether the smoke actually ran.
- `OKR.md` and `docs/process/okr_progress_log.md` may be updated during closeout after worker results, but must keep Objective 5 about 68% unless real external proof appears.
- The final record must preserve `PRRT_kwDOSWB9286CJ3tX` as unresolved / hardware material pending unless live PR evidence changes.

## Core Lever For This Round

The core lever is not another local metadata wrapper. It is adding one targeted Docker smoke proof assertion to the cloud-relay deploy path, so the existing acceptance packet cannot regress out of the deploy proof unnoticed.

## What Needs To Be Done

1. Full-Stack updates `cloud-relay/scripts/docker_smoke.sh` to generate or read the safe lifecycle acceptance packet through the cloud-relay Docker path and assert the required markers.
2. Full-Stack updates `cloud-relay/README.md`, and only updates `docs/product/remote_4g_mvp.md` if the public evidence wording changes.
3. Robot performs a read-only check that Robot/API diagnostics already expose the required packet fields; Robot changes diagnostics/docs only if the smoke path needs a missing safe marker.
4. Product closes the sprint with `tech-done.md`, `side2side_check.md`, `final.md`, then updates `OKR.md` and `docs/process/okr_progress_log.md` conservatively after implementation proof exists.

## Priority And Acceptance Criteria

P0 acceptance:

- `bash -n cloud-relay/scripts/docker_smoke.sh` passes.
- A focused `rg` proves the smoke and docs contain `cloud_command_lifecycle_replay_acceptance_packet` and `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`.
- If Docker is available, `bash cloud-relay/scripts/docker_smoke.sh` runs and the log includes the acceptance-packet smoke section.
- If Docker is unavailable, Task A must document the exact Docker blocker and provide the strongest substitute validation: shell syntax, marker rg, and scoped diff check.

P1 acceptance:

- Robot read-only validation confirms the acceptance packet remains metadata-only, fail-closed, and safe for deploy-smoke consumption.
- No task claims real cloud, public HTTPS/TLS, true phone/browser, production DB/queue, worker/cutover, HIL, route/elevator field pass, delivery result, or PR #5 resolution.

## Responsible Engineers

- Task A: User Touchpoint Full-Stack Engineer.
- Task B: Robot Platform Engineer.
- Task C: Product Manager / OKR Owner.

## Risks And Evidence Gaps

- Docker may be unavailable on this host; then this sprint cannot close as a full Docker smoke run.
- The acceptance packet may currently be produced only through Robot/API diagnostics, not a first-class cloud-relay CLI artifact; Task A must choose the smallest integration that proves deploy freshness without inventing a new product feature.
- This sprint does not address the real O5 blockers: public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, verified terminal result.
- This sprint does not address the O1 blocker: PR #5 `PRRT_kwDOSWB9286CJ3tX` hardware materials and real HIL evidence.

## Sprint Documents

Planning documents created now:

- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/pre_start.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/prd.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/tech-plan.md`

Implementation closeout documents to create later:

- `tech-done.md`
- `side2side_check.md`
- `final.md`
