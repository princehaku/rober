# Cloud Command Lifecycle Replay Drill Tech Plan

Run time: 2026-05-23 20:21 Asia/Shanghai

## Goal

Build `cloud_command_lifecycle_replay_drill` as a replayable support drill artifact on top of the existing `cloud_command_lifecycle_audit_export` safe summary.

The drill must let support / field owner复演 a safe command lifecycle timeline, ACK semantics, pending terminal result, and next required evidence while preserving `software_proof_docker_cloud_command_lifecycle_replay_drill_gate`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

## OKR 最低优先级核对

Current `OKR.md` 4.1 lowest objective is Objective 5 at about 68%.

This sprint directly targets Objective 5 because it advances the O5 cloud command lifecycle support path from safe audit/export summary to replayable support drill artifact.

Docker-only boundary: this host has no real hardware and this sprint is only Docker/local `software_proof`. It must not claim real public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, true phone/browser proof, HIL, route/elevator field pass, verified terminal delivery/dropoff/cancel result, delivery success, or PR #5 resolution. `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`.

## Architecture

Robot/API remains the source of truth for sanitized diagnostics. It should derive a new replay drill summary from the existing lifecycle audit/export safe summary and expose it through `/api/status` and `/api/diagnostics`.

Mobile/web remains a read-only consumer. It renders the drill from Robot/API summary or fixture, keeps primary actions disabled, and does not add any command, ACK, cursor, replay, resubmit, raw diagnostics, or material mutation route.

Product owns planning and later closeout only. Product must not treat the drill artifact as business completion; it is readiness for support and field owner replay, not real external cloud proof.

## Parallel Owner Plan

### Robot Platform Engineer

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/product/remote_4g_mvp.md`

Implementation requirements:

- Add a safe alias named `cloud_command_lifecycle_replay_drill`.
- Expose `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary`.
- Derive from existing `cloud_command_lifecycle_audit_export` / `robot_diagnostics_cloud_command_lifecycle_audit_export_summary` only.
- Preserve safe `command_id`, safe `evidence_ref`, ordered lifecycle timeline, ACK semantics, terminal result pending status, next required evidence, and support drill copy.
- Fail closed for missing safe ids, conflicting command/evidence refs, unsafe text, raw paths, credentials, URLs with secrets, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success copy, `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.
- Do not create command replay/resubmit, ACK posting, cursor mutation, persistence mutation, Nav2, WAVE ROVER, or HIL behavior.
- Update `docs/interfaces/operator_gateway_diagnostics.md` and `docs/product/remote_4g_mvp.md` with the new read-only contract and evidence boundary.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "cloud_command_lifecycle_replay_drill|robot_diagnostics_cloud_command_lifecycle_replay_drill_summary|software_proof_docker_cloud_command_lifecycle_replay_drill_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_http.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md docs/product/remote_4g_mvp.md
```

### User Touchpoint Full-Stack Engineer

Allowed files:

- `mobile/web/app.js`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_drill.json`
- `docs/product/mobile_user_flow.md`

Implementation requirements:

- Add a read-only "云命令生命周期复演演练" panel.
- Consume `robot_diagnostics_cloud_command_lifecycle_replay_drill_summary` first, then safe compatible summary fields only if already present in status/diagnostics payloads.
- Render safe `command_id`, safe `evidence_ref`, lifecycle timeline, ACK semantics, terminal result pending status, next required evidence, support drill copy availability, evidence boundary, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- Keep Start Delivery, Confirm Dropoff, and Cancel disabled.
- Do not add any raw diagnostics fetch, raw JSON view, command replay/resubmit, ACK/cursor route, copy of credentials, local paths, ROS topics, `/cmd_vel`, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, or success claims.
- Update `docs/product/mobile_user_flow.md` with the read-only mobile contract.

Acceptance commands:

```bash
node --check mobile/web/app.js
python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_drill.json
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "cloud_command_lifecycle_replay_drill|robot_diagnostics_cloud_command_lifecycle_replay_drill_summary|software_proof_docker_cloud_command_lifecycle_replay_drill_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|云命令生命周期复演演练" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_drill.json docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures/robot_diagnostics_cloud_command_lifecycle_replay_drill.json docs/product/mobile_user_flow.md
```

### Product Owner

Allowed files after worker implementation:

- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/tech-done.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/side2side_check.md`
- `sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Closeout requirements:

- Record worker file changes and validation logs.
- Confirm all required false-state flags remain present.
- Confirm no OKR percentage lift unless real external cloud or real terminal result proof is added.
- Confirm docs under `docs/` were updated by responsible owners.
- Preserve PR #5 status: `PRRT_kwDOSWB9286CJ3tX` unresolved / `hardware_material_pending`.

Closeout acceptance commands:

```bash
test -f sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/tech-done.md && test -f sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/side2side_check.md && test -f sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill/final.md
rg -n "cloud_command_lifecycle_replay_drill|software_proof_docker_cloud_command_lifecycle_replay_drill_gate|Objective 5|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|PRRT_kwDOSWB9286CJ3tX|no OKR percentage lift" sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.23_20-21_cloud-command-lifecycle-replay-drill OKR.md docs/process/okr_progress_log.md
```

## Interface Contract

Expected Robot/API summary fields:

- `schema=trashbot.cloud_command_lifecycle_replay_drill_summary.v1`
- `capability=cloud_command_lifecycle_replay_drill`
- `source=software_proof`
- `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_drill_gate`
- safe `command_id`
- safe `evidence_ref`
- ordered `replay_timeline`
- `ack_semantics=accepted_processing_only_not_delivery_success`
- `terminal_result_status=pending`
- `next_required_evidence`
- sanitized `support_drill_copy`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Unsafe source material must become blocked/not_proven and must not be rendered as a successful drill.

## Validation Boundary

Validation is intentionally fenced:

- Robot unit tests and py_compile for touched Robot/API files.
- Mobile unit tests, node syntax check, and JSON fixture validation for touched mobile files.
- Scoped `rg` checks for required boundary strings.
- Scoped `git diff --check` on touched files.

No broad regression sweep is required in this planning phase. If worker implementation touches shared behavior or test failures expose wider risk, the responsible worker must rerun the smallest expanded fence that explains the risk.

## Product Acceptance

The sprint can close only if:

- Robot/API exposes a safe replay drill summary.
- Mobile/web renders it read-only.
- Support copy explains ACK semantics and pending terminal result without control instructions.
- Primary actions remain disabled.
- Docs are synchronized.
- Sprint closeout records the proof as `software_proof`, not real cloud or delivery proof.

The sprint cannot close as OKR completion if:

- Any output claims `delivery_success=true`, `primary_actions_enabled=true`, or `safe_to_control=true`.
- Any output claims true phone/browser proof, real public HTTPS/TLS, real 4G/SIM, OSS/CDN live traffic, production DB/queue, HIL, route/elevator field pass, verified terminal result, delivery result, delivery success, or PR #5 resolution.
- The implementation adds a command replay/resubmit, ACK/cursor mutation, raw diagnostics fetch, or robot command route.

