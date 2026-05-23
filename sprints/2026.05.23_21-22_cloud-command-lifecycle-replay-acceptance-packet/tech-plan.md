# Cloud Command Lifecycle Replay Acceptance Packet Tech Plan

Run time: 2026-05-23 21:05 Asia/Shanghai

## Goal

Build `cloud_command_lifecycle_replay_acceptance_packet` as the next support / field-owner contract after `cloud_command_lifecycle_replay_drill`.

The packet must summarize safe replay drill evidence into an acceptance package containing safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, pending terminal result, owner handoff, packet review status, and next required evidence while preserving `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR 最低优先级核对

Current `OKR.md` 4.1 lowest objective is Objective 5 at about 68%.

This sprint directly targets Objective 5 because it advances the O5 cloud command lifecycle path from replay drill to support / field-owner acceptance packet.

Docker-only boundary: this host has no real hardware and this sprint is only Docker/local `software_proof`. It must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, route/elevator field pass, verified terminal delivery/dropoff/cancel result, delivery success, or PR #5 resolution. GitHub PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; `PRRT_kwDOSWB9286CJ3tQ` and `PRRT_kwDOSWB9286CJ3tU` are resolved, but X is not.

## Architecture

Robot/API remains the source of truth for sanitized diagnostics. It should derive a new acceptance packet summary from the existing lifecycle replay drill safe summary and expose it through `/api/status` and `/api/diagnostics`.

Mobile/web remains a read-only consumer. It renders the acceptance packet from Robot/API summary or fixture, keeps primary actions disabled, and does not add any command, ACK, cursor, replay, resubmit, raw diagnostics, material upload, review action, GitHub action, or robot command route.

Product owns planning and later closeout only. Product must not treat the packet as business completion; it is readiness for support / field-owner acceptance review, not real external cloud proof or delivery proof.

## Parallel Owner Plan

### Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Implementation requirements:

- Add a safe alias named `cloud_command_lifecycle_replay_acceptance_packet`.
- Expose `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary`.
- Derive from existing `cloud_command_lifecycle_replay_drill` / `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary` only.
- Preserve safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, terminal result pending status, acceptance packet status, owner handoff, next required evidence, and support-safe copy.
- Fail closed for missing safe ids, conflicting command/evidence refs, unsafe text, raw paths, credentials, URLs with secrets, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, ACK payloads, cursors, success copy, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.
- Do not create command replay/resubmit, ACK posting, cursor mutation, persistence mutation, material upload, review action, GitHub action, Nav2, WAVE ROVER, UART, or HIL behavior.
- Update `docs/interfaces/operator_gateway_diagnostics.md` and `docs/product/remote_4g_mvp.md` with the new read-only contract and evidence boundary.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet.json`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only "云命令生命周期验收包" panel.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary` first, then safe compatible summary fields only if already present in status/diagnostics payloads.
- Render safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, terminal result pending status, packet status, owner handoff, next required evidence, support copy availability, evidence boundary, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add any raw diagnostics fetch, raw JSON view, command replay/resubmit, ACK/cursor route, material upload, review action, GitHub action, copy of credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, ACK payloads, cursors, or success claims.
- Update `docs/product/mobile_user_flow.md` with the read-only mobile contract.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|云命令生命周期验收包" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet.json docs/product/mobile_user_flow.md
```

### Product Owner

Allowed files after worker implementation:

- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/tech-done.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/side2side_check.md`
- `sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record worker file changes and validation logs.
- Confirm all required false-state flags remain present.
- Confirm no OKR percentage lift unless real external cloud, true phone/browser, production DB/queue, or verified terminal-result proof is added.
- Confirm docs under `docs/` were updated by responsible owners.
- Preserve PR #5 status: `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`.
- Keep Objective 5 direct-target language and preserve Docker-only `software_proof` boundaries.

Closeout acceptance commands:

```bash
test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/tech-done.md && test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/side2side_check.md && test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|Objective 5|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|no OKR percentage lift" sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet OKR.md docs/process/okr_progress_log.md
```

## Interface Contract

Expected Robot/API summary fields:

- `schema=trashbot.cloud_command_lifecycle_replay_acceptance_packet_summary.v1`
- `capability=cloud_command_lifecycle_replay_acceptance_packet`
- `source_schema=trashbot.cloud_command_lifecycle_replay_drill_summary.v1`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
- safe `command_id`
- safe `evidence_ref`
- ordered `replay_timeline`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `terminal_result_status=pending`
- `acceptance_packet_status=ready_for_field_owner_acceptance_review_not_proven`
- `owner_handoff`
- `next_required_evidence`
- sanitized `support_acceptance_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Unsafe source material must become blocked/not_proven and must not be rendered as a successful acceptance packet.

## Validation Boundary

Validation is intentionally fenced:

- Robot unit tests and py_compile for touched Robot/API files.
- Mobile unit tests, node syntax check, and JSON fixture validation for touched mobile files.
- Scoped `rg` checks for required boundary strings.
- Scoped `git diff --check` on touched files.

No broad regression sweep is required in this planning phase. If worker implementation touches shared behavior or test failures expose wider risk, the responsible worker must rerun the smallest expanded fence that explains the risk.

## Product Acceptance

The sprint can close only if:

- Robot/API exposes a safe acceptance packet summary.
- Mobile/web renders it read-only.
- Support copy explains ACK semantics, pending terminal result, owner handoff, and next required evidence without control instructions.
- Primary actions remain disabled.
- Docs are synchronized.
- Sprint closeout records the proof as `software_proof`, not real cloud or delivery proof.

The sprint cannot close as OKR completion if:

- Any output claims `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.
- Any output claims true phone/browser proof, real public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue, HIL, route/elevator field pass, verified terminal result, delivery result, delivery success, or PR #5 resolution.
- The implementation adds a command replay/resubmit, ACK/cursor mutation, raw diagnostics fetch, material upload, review action, GitHub action, or robot command route.

## Planning Validation Commands

```bash
test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/pre_start.md && test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/prd.md && test -f sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet/tech-plan.md
rg -n "sprint_type: epic|cloud_command_lifecycle_replay_acceptance_packet|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|Objective 5|OKR 最低优先级核对|PRRT_kwDOSWB9286CJ3tX|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet
git diff --check -- sprints/2026.05.23_21-22_cloud-command-lifecycle-replay-acceptance-packet
```
