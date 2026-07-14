# Tech Plan - O3 Fixed Route Consumer Dry Run

## Objective

Assign `robot-algorithm-engineer` a single-owner implementation sprint: consume the 00:00 route-intent packet and produce a strict no-motion fixed-route consumer dry-run/material validation, or produce stronger full structured path poses if the current `partial_stdout_tail_only` material is not enough for a trustworthy dry-run.

This sprint must move from "route-intent packet exists" to "a consumer can validate or fail closed on that packet".

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对 O5 的理由：O5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 或其他 external production evidence。继续做 support-only readiness、checklist、wrapper、handoff、review、owner response 或状态面板不会产生 `okr_credit_allowed=true`。
- 本 sprint 选择 O3/O1 的理由：00:00 已产出可复用 `route_intent_id=route_intent_20260713_0000_from_20260712_2157_path_proof` 和 `task_id=task_o3_fixed_route_intent_20260713_0000`，下一步必须消费这个材料，做 strict no-motion fixed-route consumer dry-run 或补 full structured path poses，才有资格进入后续 route execution / delivery / HIL / production evidence。
- 收口复核口径：如果只产出 consumer dry-run/material validation，O5/O1/O6/O7 百分比保持 flat，KR `不归档`。只有新增 route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 real production external evidence，才进入百分比调整评审。

## Owner And Scope

- Primary implementation owner: `robot-algorithm-engineer`
- Product owner: `product-okr-owner` for acceptance wording and OKR boundary
- Support owner if blocked by helper/export format only: `robot-software-engineer`
- Not involved: Hardware and Full-stack for this sprint

Implementation should be one owner, single line. It is not a cross-owner epic unless the dry-run exposes a helper/export blocker that cannot be solved artifact-only.

## Input Artifacts

Read-only inputs:

- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_summary.json`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_replay.jsonl`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route.csv`
- source proof ref inside summary: `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`

Accepted source facts:

- `route_intent_id=route_intent_20260713_0000_from_20260712_2157_path_proof`
- `task_id=task_o3_fixed_route_intent_20260713_0000`
- `path_generation_attempted=true`
- `path_generated=true`
- `path_point_count=21`
- `fallback_mode=ros2_cli_action_send_goal`
- `path_pose_materialization_status=partial_stdout_tail_only`
- `materialized_stdout_tail_pose_count=14`
- `minimum_unmaterialized_path_pose_count=7`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Planned Output Artifacts

Preferred output directory:

- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/`

Preferred output files:

- `fixed_route_consumer_dry_run_summary.json`
- `fixed_route_consumer_dry_run_events.jsonl`
- `fixed_route_consumer_dry_run_route_check.csv`

Alternative stronger output if the dry-run cannot be trusted with partial material:

- `structured_full_path_poses_summary.json`
- `structured_full_path_poses.jsonl`
- `structured_full_path_poses.csv`

Every output must state whether it is consumer dry-run material or full structured path material. Neither output type may claim route execution.

## Implementation Plan For robot-algorithm-engineer

1. Load the 00:00 summary JSON, JSONL, and CSV using structured parsers.
2. Validate identity consistency:
   - same `route_intent_id`
   - same `task_id`
   - same source proof ref
   - expected route material refs
3. Validate source evidence preservation:
   - `path_generation_attempted=true`
   - `path_generated=true`
   - `path_point_count=21`
   - `fallback_mode=ros2_cli_action_send_goal`
4. Validate material shape:
   - JSONL line count and event types
   - CSV header and row count
   - request start anchor
   - request goal anchor
   - 14 stdout-tail pose events
   - at least 7 unmaterialized source path poses explicitly recorded as unavailable
5. Validate route-order consistency:
   - consumer can iterate the material in deterministic order
   - frame fields are present for every materialized pose/anchor
   - no missing x/y pose fields for materialized entries
6. Validate safety invariants:
   - strict no-motion is true
   - `safe_to_control=false`
   - `publishes_cmd_vel=false`
   - `calls_base_manual=false`
   - `uses_base_uart=false`
   - `robot_control_executed=false`
   - `route_execution_success=false`
   - `delivery_success=false`
   - `hil_pass=false`
7. Write dry-run artifacts with pass/fail checks and exact blocker fields if any validation fails.
8. If the consumer dry-run fails only because the material is partial, attempt a stronger full structured path pose extraction/export from the accepted source proof or declare the narrow blocker `full_structured_path_poses_missing`.
9. Update `tech-done.md` with actual files, validation logs, failure定位, and remaining risk.

## File Scope For Implementation Sprint

Likely allowed files for `robot-algorithm-engineer` when implementation starts:

- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/`
- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/tech-done.md`
- `docs/navigation/fixed_route_workflow.md` only if the consumer contract changes workflow guidance
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py` only if a no-motion helper export is required for full structured path poses
- `onboard/tests/test_nav2_runtime_proof_helper.py` only if the helper is changed

Forbidden for this sprint:

- product code outside the listed helper exception
- hardware config
- launch parameter changes
- WAVE ROVER UART, ESP32, Orange Pi UART, serial, baudrate, wiring, voltage, firmware, or vendor-backed hardware edits
- O5/O6/O7 implementation files unless Product opens a separate consumer sprint
- historical sprint files, except read-only source artifact consumption
- `OKR.md` and `docs/process/okr_progress_log.md` before Product acceptance closeout

## Strict No-Motion 禁止项

Implementation must not:

- publish `/cmd_vel`
- call `/api/base/manual`
- run NavigateToPose
- run controller/BT execution
- open WAVE ROVER UART
- send base manual relay commands
- claim route execution
- claim delivery success
- claim HIL pass
- claim safe-to-control

Required false fields in output:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Acceptance Commands For Algorithm

Algorithm should run a structured validation command appropriate to the implementation. Minimum required checks:

```bash
python3 -m json.tool sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_summary.json >/tmp/fixed_route_consumer_dry_run_summary.pretty.json
```

```bash
python3 - <<'PY'
import csv, json
from pathlib import Path
base = Path('sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm')
summary = json.loads((base / 'fixed_route_consumer_dry_run_summary.json').read_text())
assert summary['route_intent_id'] == 'route_intent_20260713_0000_from_20260712_2157_path_proof'
assert summary['task_id'] == 'task_o3_fixed_route_intent_20260713_0000'
assert summary['strict_no_motion'] is True
assert summary['route_execution_success'] is False
assert summary['delivery_success'] is False
assert summary['hil_pass'] is False
events = [json.loads(line) for line in (base / 'fixed_route_consumer_dry_run_events.jsonl').read_text().splitlines()]
assert events
with (base / 'fixed_route_consumer_dry_run_route_check.csv').open(newline='') as f:
    rows = list(csv.DictReader(f))
assert rows
print('fixed_route_consumer_dry_run_ok')
PY
```

Anchor inspection:

```bash
rg -n "route_intent_20260713_0000|task_o3_fixed_route_intent_20260713_0000|strict no-motion|fixed-route consumer dry-run|route_execution_success=false|delivery_success=false|hil_pass=false|full_structured_path_poses_missing|next_evidence_required" \
  sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run
```

If helper/tests are touched:

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

Scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run
```

## Product Acceptance Gate

Accept as progress if:

- a fixed-route consumer dry-run summary and event material exists; or
- a stronger full structured path pose material exists; or
- a narrow blocker names the exact missing field/schema/export needed, such as `full_structured_path_poses_missing`, `route_intent_identity_mismatch`, or `consumer_rejects_partial_stdout_tail_only`.

Reject if:

- the result only republishes the 00:00 route-intent packet
- the result claims full 21-point replay while still based only on 14 stdout-tail poses
- any motion/control/HIL/delivery/safe-to-control field is true
- any implementation publishes `/cmd_vel`, calls `/api/base/manual`, runs NavigateToPose, or touches WAVE ROVER UART
- the result routes to O5/O6/O7 support-only work without consuming this material

## OKR And KR Closeout Rules

- Expected closeout if successful: O5 about `85%`, O1 about `94%`, O6/O7 about `93%`, KR `不归档`.
- Consumer dry-run material is useful but does not by itself prove route execution or delivery.
- Full structured path material may strengthen the next route execution sprint, but still should not claim HIL or safe-to-control.
- Product should update `side2side_check.md`, `final.md`, `OKR.md`, and `docs/process/okr_progress_log.md` only after implementation evidence exists.

## Risks

- The current input is partial stdout-tail material, so a consumer can validate shape/order but may still lack exact full 21-point semantics.
- A dry-run consumer can prove material consumption, not robot motion.
- Full structured path extraction may require helper changes if the source artifact did not persist all pose points.
- O5 remains blocked on real external production evidence; this sprint does not unblock O5.
