# Cloud Command Lifecycle Acceptance CLI Export Tech Plan

Run time: 2026-05-24 06:05 Asia/Shanghai

## Sprint Type

sprint_type: epic

## Goal

Implement `cloud_command_lifecycle_replay_acceptance_packet_cli_export` by adding a direct independent cloud relay CLI export for the command lifecycle replay acceptance packet that was already verified by Docker smoke in the previous sprint.

Target boundary:

`software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`

## Architecture And Current Evidence

Current evidence chain:

- `cloud_command_lifecycle_replay_acceptance_packet` exists as support / field-owner review metadata.
- Previous packet boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`.
- Previous Docker-smoke boundary: `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_docker_smoke_gate`.
- Previous sprint `sprints/2026.05.24_05-06_cloud-command-lifecycle-acceptance-docker-smoke-proof/final.md` closed that Docker smoke with no OKR percentage lift.
- Required safe states remain `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.

The gap is artifact access. Support can trust the Docker-smoke-verified packet, but the independent cloud relay CLI does not yet directly export a sanitized JSON acceptance packet for field-owner review.

## OKR 最低优先级核对

1. Current lowest Objective in `OKR.md` 4.1 is Objective 5 at about 68%.
2. This sprint targets Objective 5.
3. This sprint still does not raise Objective 5 percentage. It is no OKR percentage lift because it only adds Docker/local CLI export for an existing command lifecycle acceptance packet. It is not real external cloud proof, not public HTTPS/TLS, not true phone/browser proof, not production DB/queue proof, not worker/cutover proof, not verified terminal result, not route/elevator field pass, not HIL, and not delivery success.
4. Objective 1 remains about 81%, with PR #5 thread `PRRT_kwDOSWB9286CJ3tX` still unresolved / `hardware_material_pending` unless live evidence changes. This sprint cannot prove WAVE ROVER/UART/HIL or hardware materials on the Docker-only host.

## Evidence Boundary

Must preserve:

- `cloud_command_lifecycle_replay_acceptance_packet_cli_export`
- `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`
- source packet marker `cloud_command_lifecycle_replay_acceptance_packet`
- previous source boundary `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
- `accepted_processing_only_not_delivery_success`
- `terminal_result_pending`
- `owner_handoff`
- `next_required_evidence`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- no OKR percentage lift
- not delivery success

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

### Task A - Full-Stack: cloud relay CLI export

Owner: User Touchpoint Full-Stack Engineer.

Allowed files:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `cloud-relay/README.md`
- `docs/product/remote_4g_mvp.md`

Expected implementation:

1. Add an argparse CLI export flag in `remote_cloud_relay.py`, such as `--write-cloud-command-lifecycle-replay-acceptance-packet-cli-export`.
2. Reuse the existing safe acceptance-packet builder when possible. If an adapter is needed, keep it small and keep the source packet semantics single-source.
3. Write a JSON artifact containing:
   - `capability=cloud_command_lifecycle_replay_acceptance_packet_cli_export`
   - `evidence_boundary=software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate`
   - source packet marker `cloud_command_lifecycle_replay_acceptance_packet`
   - source packet boundary `software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate`
   - `ack_semantics=accepted_processing_only_not_delivery_success`
   - `terminal_result_status=terminal_result_pending`
   - `owner_handoff`
   - `next_required_evidence`
   - `not_proven`
   - `delivery_success=false`
   - `primary_actions_enabled=false`
   - `safe_to_control=false`
4. Ensure the export rejects or redacts unsafe content: bearer tokens, Authorization headers, signed URLs, raw paths, `/cmd_vel`, ROS topics, serial/UART details, WAVE ROVER details, tracebacks, complete artifacts, checksums, success wording, and true-state control flags.
5. Update `cloud-relay/README.md` with the CLI command and expected JSON validation.
6. Update `docs/product/remote_4g_mvp.md` to describe the CLI export as support / field-owner review metadata only.

Acceptance commands:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --help | rg "cloud_command_lifecycle_replay_acceptance_packet_cli_export|write-cloud-command-lifecycle-replay-acceptance-packet-cli-export"
tmp_json="$(mktemp /tmp/trashbot_cli_export.XXXXXX.json)" && PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m ros2_trashbot_behavior.remote_cloud_relay --write-cloud-command-lifecycle-replay-acceptance-packet-cli-export "$tmp_json" && python3 - "$tmp_json" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as handle:
    payload = json.load(handle)

text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
required = [
    "cloud_command_lifecycle_replay_acceptance_packet_cli_export",
    "software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate",
    "cloud_command_lifecycle_replay_acceptance_packet",
    "accepted_processing_only_not_delivery_success",
    "terminal_result_pending",
    "owner_handoff",
    "next_required_evidence",
    "not_proven",
]
missing = [marker for marker in required if marker not in text]
assert not missing, missing
assert '"delivery_success": false' in text
assert '"primary_actions_enabled": false' in text
assert '"safe_to_control": false' in text
print("cli export json markers ok")
PY
rg -n "cloud_command_lifecycle_replay_acceptance_packet_cli_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate|cloud_command_lifecycle_replay_acceptance_packet|accepted_processing_only_not_delivery_success|terminal_result_pending|owner_handoff|next_required_evidence|not delivery success|no OKR percentage lift|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py cloud-relay/README.md docs/product/remote_4g_mvp.md
```

Do not run broad ROS2 or whole-repo tests for this task unless the implementation unexpectedly changes shared runtime behavior.

### Task B - Robot: diagnostics contract consultation

Owner: Robot Platform Engineer.

Default mode: read-only. If CLI export can reuse the existing builder and safe summary, do not edit Robot files.

Allowed files only if a missing marker requires a narrow docs/diagnostics adjustment:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`

Expected work:

1. Confirm Robot/API diagnostics already expose the acceptance packet fields required by Task A.
2. Confirm the packet remains read-only metadata and cannot replay commands, post ACKs, mutate cursors, upload materials, run GitHub actions, trigger Nav2, touch WAVE ROVER, use UART, prove HIL, or authorize robot control.
3. If no Robot code change is required, return read-only evidence and do not edit files.
4. If a narrow edit is required, add or adjust only the missing marker/summary and update `docs/interfaces/operator_gateway_diagnostics.md`.

Read-only acceptance commands:

```bash
rg -n "cloud_command_lifecycle_replay_acceptance_packet|robot_diagnostics_cloud_command_lifecycle_replay_acceptance_packet_summary|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_gate|accepted_processing_only_not_delivery_success|terminal_result_pending|owner_handoff|next_required_evidence|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/operator_gateway_diagnostics.md
```

If Robot edits code, add focused validation:

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

Do not run broad ROS2 or whole-repo tests for this consultation task.

### Task C - Product: closeout, OKR, and progress log

Owner: Product Manager / OKR Owner.

Must execute after Task A/B complete.

Allowed files after Task A/B complete:

- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/tech-done.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/side2side_check.md`
- `sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Expected work:

1. Record Task A and Task B actual changes and validation outputs.
2. Record whether CLI help and CLI JSON export actually ran.
3. Update `OKR.md` and `docs/process/okr_progress_log.md` conservatively after implementation proof exists.
4. Keep Objective 5 at about 68% unless real external cloud/terminal-result evidence is introduced outside this plan.
5. Preserve PR #5 `PRRT_kwDOSWB9286CJ3tX` as unresolved / `hardware_material_pending` unless live GitHub evidence changes.

Acceptance commands:

```bash
test -f sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/tech-done.md && test -f sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/side2side_check.md && test -f sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export/final.md
rg -n "cloud_command_lifecycle_replay_acceptance_packet_cli_export|software_proof_docker_cloud_command_lifecycle_replay_acceptance_packet_cli_export_gate|Objective 5|PRRT_kwDOSWB9286CJ3tX|not true phone/browser proof|no OKR percentage lift|not production DB/queue|not worker/cutover|not HIL|not delivery success" sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.24_06-07_cloud-command-lifecycle-acceptance-cli-export OKR.md docs/process/okr_progress_log.md
```

## Parallel Execution Rule

Start Task A and Task B in parallel because their default file scopes do not overlap. Task A owns the independent relay CLI export and docs. Task B owns Robot diagnostics consultation and only edits Robot diagnostics/docs if a missing marker is proven.

Task C starts after Task A/B return, because closeout depends on actual implementation and validation evidence.

## Integration And Acceptance

The sprint is acceptable only when:

- `tech-done.md` records actual changed files and validation evidence.
- `side2side_check.md` compares the result against this PRD and tech-plan boundary.
- `final.md` states whether CLI help and CLI JSON export both passed.
- The CLI export JSON contains the target boundary and false control flags.
- If the export cannot run, the final result explicitly says the CLI export proof is incomplete and no OKR progress was claimed.

## Remaining Risks To Carry Into Final

- Real O5 progress still needs public HTTPS/TLS, 4G/SIM, OSS/CDN live traffic, production DB/queue, worker/cutover, true phone/browser proof, or verified terminal result.
- Real O1 progress still needs PR #5 `PRRT_kwDOSWB9286CJ3tX` material resolution plus real 2D LiDAR / ToF and WAVE ROVER/UART/HIL evidence.
- This sprint only creates a CLI export for an existing acceptance packet. It does not close delivery, hardware, phone, production cloud, or external evidence gaps.
