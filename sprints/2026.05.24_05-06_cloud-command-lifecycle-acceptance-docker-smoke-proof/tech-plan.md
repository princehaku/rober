# Cloud Command Lifecycle Acceptance Docker Smoke Proof Tech Plan

Run time: 2026-05-24 05:36 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Goal

Implement `cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof` by adding a targeted cloud-relay Docker smoke assertion for the existing read-only command lifecycle replay acceptance packet.

Target boundary:

`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`

## Architecture And Current Evidence

The acceptance packet already exists in Robot/API and mobile surfaces:

- Capability: `cloud_command_lifecycle_replay_acceptance_packet`.
- Existing packet boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- Safe states: `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, `safe_to_control=false`.
- Product purpose: support / field-owner review of ACK semantics, pending terminal result, owner handoff, next required evidence, and support-safe copy.

The gap is in `cloud-relay/scripts/docker_smoke.sh`. Current smoke coverage includes readiness, preflight, DB/queue gates, public ingress/TLS gates, worker migration, worker cutover/drain, command/ACK flow, backup/restore, and state recovery. It does not yet cover `cloud_command_lifecycle_replay_acceptance_packet` or `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint targets Objective 5.
3. This sprint still does not raise Objective 5 percentage. It is no OKR percentage lift because it only adds Docker/local deploy-smoke freshness for an existing acceptance packet. It is not real external cloud proof, not true phone/browser proof, not production DB/queue proof, not worker/cutover proof, not verified terminal result, and not delivery success.
4. Objective 1 remains about 81%, with PR #5 thread `PRRT_kwDOSWB9286CJ3tX` still unresolved / `hardware_material_pending` unless live evidence changes. This sprint cannot prove hardware on the Docker-only host.

## Evidence Boundary

Must preserve:

- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`
- `source=software_proof`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift
- not true phone/browser proof

Must not claim:

- real external cloud proof
- public HTTPS/TLS proof
- 4G/SIM proof
- OSS/CDN live traffic
- production DB/queue proof
- worker/cutover proof
- true phone/browser proof
- verified terminal result
- route/elevator field pass
- Nav2/fixed-route runtime pass
- HIL
- WAVE ROVER/UART proof
- PR #5 resolution
- delivery result or delivery success

## Owner / File Split

### Task A - Full-Stack: cloud-relay Docker smoke proof

Owner: User Touchpoint Full-Stack Engineer.

Allowed files:

- `cloud-relay/scripts/docker_smoke.sh`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md` only if product-facing evidence wording changes.

Expected implementation:

1. Add a focused smoke section that verifies the cloud command lifecycle replay acceptance packet is visible in the Docker cloud-relay proof path.
2. Assert the markers:
   - `cloud_command_lifecycle_replay_acceptance_packet`
   - `cloud_command_lifecycle_replay_acceptance_packet_summary`
   - `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`
   - `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
   - `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`
   - `accepted_processing_only_not_delivery_success`
   - `terminal_result_pending`
   - `owner_handoff`
   - `next_required_evidence`
   - `not_proven`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `safe_to_control=false`
3. Keep forbidden marker checks for credentials, raw paths, `/cmd_vel`, ROS topics, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, and true-state control flags.
4. Update `cloud-relay/README.md` to describe the new docker smoke assertion and boundary.
5. Update `docs/product/remote_4g_mvp.md` only if the implementation changes product-visible wording or introduces a new named docker-smoke boundary.

Acceptance commands:

```bash
bash -n cloud-relay/scripts/docker_smoke.sh
rg -n "cloud_command_lifecycle_replay_acceptance_packet|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate|accepted_processing_only_not_delivery_success|terminal_result_pending|owner_handoff|next_required_evidence|not true phone/browser proof|no OKR percentage lift" cloud-relay/scripts/docker_smoke.sh cloud-relay/README.md docs/product/remote_4g_mvp.md
git diff --check -- cloud-relay/scripts/docker_smoke.sh cloud-relay/README.md docs/product/remote_4g_mvp.md
```

Docker command, if environment supports Docker:

```bash
bash cloud-relay/scripts/docker_smoke.sh
```

If Docker cannot run, Task A must report the exact blocker and include the substitute proof from `bash -n`, required `rg`, and scoped `git diff --check`.

### Task B - Robot: diagnostics contract consultation

Owner: Robot Platform Engineer.

Default mode: read-only.

Allowed files only if a missing marker requires a narrow docs/diagnostics adjustment:

- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

Expected work:

1. Confirm Robot/API diagnostics already expose the acceptance packet fields required by Task A.
2. Confirm the packet remains read-only metadata and cannot replay commands, post ACKs, mutate cursors, upload materials, run GitHub actions, trigger Nav2, touch WAVE ROVER, use UART, prove HIL, or authorize robot control.
3. If no Robot code change is required, return read-only evidence and do not edit files.
4. If a narrow edit is required, add or adjust only the missing marker/summary and update the matching docs.

Read-only acceptance commands:

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|accepted_processing_only_not_delivery_success|terminal_result_pending|owner_handoff|next_required_evidence|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
git diff --check -- docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

If Robot edits code, add focused validation:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

Do not run broad ROS2 or whole-repo tests for this task.

### Task C - Product: closeout, OKR, and progress log

Owner: Product Manager / OKR Owner.

Allowed files after Task A/B complete:

- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/tech-done.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/side2side_check.md`
- `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Expected work:

1. Record Task A and Task B actual changes and validation outputs.
2. Record whether Docker smoke actually ran or was blocked by host Docker conditions.
3. Update `OKR.md` and `docs/process/okr_progress_log.md` conservatively after implementation proof exists.
4. Keep Objective 5 at about 68% unless real external cloud/terminal-result evidence is introduced outside this plan.
5. Preserve PR #5 `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending` unless live GitHub evidence changes.

Acceptance commands:

```bash
test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/tech-done.md && test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/side2side_check.md && test -f sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_proof|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not true phone/browser proof|no OKR percentage lift|not production DB/queue|not worker/cutover|not HIL|not delivery success" sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof OKR.md docs/process/okr_progress_log.md
```

## Parallel Execution Rule

Start Task A and Task B in parallel because their default file scopes do not overlap. Task A owns cloud-relay smoke/docs. Task B owns Robot diagnostics consultation and only edits Robot diagnostics/docs if a missing marker is proven.

Task C starts after Task A/B return, because closeout depends on their actual validation evidence.

## Integration And Acceptance

The sprint is acceptable only when:

- `tech-done.md` records actual changed files and validation evidence.
- `side2side_check.md` compares the result against the PRD boundaries.
- `final.md` states whether the sprint closed as full Docker smoke proof or as Docker-blocked syntax/marker proof.
- If Docker smoke ran, the output proves the new acceptance-packet smoke section.
- If Docker smoke did not run, the final result explicitly says the Docker/local deploy-smoke proof is incomplete and no OKR progress was claimed.

## Remaining Risks To Carry Into Final

- Real O5 progress still needs public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal result.
- Real O1 progress still needs PR #5 `PRRT_kwDOSWB9286CJ3tX` material resolution plus real 2D LiDAR / ToF and WAVE ROVER/UART/HIL evidence.
- This sprint only strengthens deploy-smoke freshness for an existing acceptance packet. It does not close delivery, hardware, phone, production cloud, or external evidence gaps.
