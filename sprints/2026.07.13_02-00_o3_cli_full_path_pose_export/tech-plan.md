# Tech Plan - O3 CLI Full Path Pose Export

## Objective

Assign `robot-algorithm-engineer` a single-owner implementation sprint: make `o10_amcl_nav2_runtime_proof.py` preserve structured path poses from ROS2 CLI `ComputePathToPose` fallback, then prove the old 21:57 artifact remains partial because it only stored truncated `stdout_tail`.

This sprint must move the blocker from generic `full_structured_path_poses_missing` to either:

- `cli_fallback_structured_path_pose_export_ready` for future live captures; or
- a narrower live rerun blocker such as `historic_stdout_tail_truncated_full_pose_replay_unavailable`.

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：O5，约 `85%`。
- 本 sprint 是否针对该最低 Objective：否。
- 不针对 O5 的理由：O5 仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 或其他 external production evidence。继续做 support-only readiness、checklist、wrapper 或状态面板不会产生 `okr_credit_allowed=true`。
- 本 sprint 选择 O3/O1 的理由：上一轮 fixed-route consumer dry-run 已证明 partial material 可消费，但后续 route replay / route execution 前的直接 blocker 是 `full_structured_path_poses_missing`。修 CLI fallback structured export 是当前环境可推进的最低可行动作。
- 收口复核口径：helper/export contract 和历史 artifact fail-closed 通常不调整 O5/O1/O6/O7 百分比；只有新 live same-run full structured path artifact 或更强 route/delivery/HIL/production evidence 到位才进入调分。

## Owner And Scope

- Primary implementation owner: `robot-algorithm-engineer`
- Product owner: `product-okr-owner` for acceptance wording and OKR boundary after implementation
- Support owner if blocked by helper ownership only: `robot-software-engineer`
- Not involved: Hardware and Full-stack

Single owner is intentional: this is a helper/export and route-material problem, not a cross-owner implementation.

## Input Artifacts

Read-only inputs:

- `sprints/2026.07.13_01-00_o3_fixed_route_consumer_dry_run/artifacts/algorithm/fixed_route_consumer_dry_run_summary.json`
- `sprints/2026.07.13_00-00_o3_fixed_route_intent_replay_material/artifacts/algorithm/route_intent_summary.json`
- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`

Accepted facts:

- `path_generated=true`
- `path_point_count=21`
- `fallback_mode=ros2_cli_action_send_goal`
- old source artifact has `path_preview_points=[]`
- old source artifact has only truncated `stdout_tail` materialized to 14 full poses
- safety fields remain false

## Implementation Plan For robot-algorithm-engineer

1. Add a parser for CLI `ros2 action send_goal ... ComputePathToPose` stdout path poses.
2. Extract at least `source_index`, `frame_id`, `stamp`, `x`, `y`, `z`, `qx`, `qy`, `qz`, `qw` where present.
3. Keep parsing tolerant of quoted/unquoted YAML-ish scalar values and missing optional stamp fields.
4. In `parse_cli_compute_path_result`, return structured fields such as:
   - `path_structured_poses`
   - `path_structured_pose_count`
   - `path_preview_points`
   - `path_preview_point_count`
   - `path_preview_source_point_count`
   - `path_preview_frame_id`
5. In `compute_path_generation_cli_fallback`, copy those fields into `result_payload` and `path_goal_response`.
6. Add unit tests in `onboard/tests/test_nav2_runtime_proof_helper.py` proving:
   - CLI fallback parses two complete poses from sample stdout;
   - parsed poses preserve frame and coordinates;
   - no `/cmd_vel`, `/api/base/manual`, `NavigateToPose`, `FollowPath`, controller/BT execution, or WAVE ROVER UART command appears;
   - truncated historical tail cannot be expanded into 21 poses.
7. Generate this sprint's artifact directory:
   - `artifacts/algorithm/cli_full_path_pose_export_summary.json`
   - optional `artifacts/algorithm/cli_full_path_pose_export_sample.jsonl`
8. Update `docs/navigation/fixed_route_workflow.md` with the new export contract and old-artifact boundary.
9. Update `tech-done.md` with actual files, verification logs, failure定位, and remaining risk.

## File Scope For Implementation Sprint

Allowed files:

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/artifacts/algorithm/`
- `sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/tech-done.md`

Forbidden:

- hardware config
- launch parameter changes
- WAVE ROVER UART, ESP32, Orange Pi UART, serial, baudrate, wiring, voltage, firmware, vendor-backed hardware edits
- O5/O6/O7 implementation files
- historical sprint artifact mutation
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

Required false fields in any output artifact:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Acceptance Commands For Algorithm

Run:

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 -m json.tool sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/artifacts/algorithm/cli_full_path_pose_export_summary.json >/tmp/cli_full_path_pose_export_summary.pretty.json
```

```bash
python3 - <<'PY'
import json
from pathlib import Path
base = Path('sprints/2026.07.13_02-00_o3_cli_full_path_pose_export/artifacts/algorithm')
summary = json.loads((base / 'cli_full_path_pose_export_summary.json').read_text())
assert summary['strict_no_motion'] is True
assert summary['safe_to_control'] is False
assert summary['publishes_cmd_vel'] is False
assert summary['calls_base_manual'] is False
assert summary['uses_base_uart'] is False
assert summary['route_execution_success'] is False
assert summary['delivery_success'] is False
assert summary['hil_pass'] is False
assert summary['cli_fallback_structured_path_pose_export_ready'] is True
print('cli_full_path_pose_export_summary_ok')
PY
```

Anchor inspection:

```bash
rg -n "cli_fallback_structured_path_pose_export_ready|path_structured_pose_count|historic_stdout_tail_truncated_full_pose_replay_unavailable|strict no-motion|route_execution_success=false|delivery_success=false|hil_pass=false" \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_02-00_o3_cli_full_path_pose_export
```

Scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.13_02-00_o3_cli_full_path_pose_export
```

## Product Acceptance Gate

Accept as progress if:

- tests prove full structured pose parsing for CLI fallback;
- artifacts show the helper/export contract is ready;
- historical 21:57 artifact boundary remains fail-closed without fabricated missing points;
- all no-motion safety booleans stay false.

Reject if:

- worker claims full 21-point replay from old truncated `stdout_tail`;
- result only repeats the 01:00 consumer dry-run;
- any output claims route execution, delivery, HIL, safe-to-control, NavigateToPose, controller/BT, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, or production external evidence;
- validation is not run or failing validation is not repaired.

## OKR And KR Closeout Rules

- Expected closeout if successful without live rerun: O5 about `85%`, O1 about `94%`, O6/O7 about `93%`, KR `不归档`.
- This is helper/export readiness plus historical artifact fail-closed proof; it is not route execution or delivery.
- If Algorithm also produces a new live same-run full structured path artifact without motion, Product may evaluate whether O1 wording should improve, but must still reject HIL, route execution, delivery, safe-to-control, and production claims.

## Risks

- Old `stdout_tail` cannot reconstruct the first missing path poses; do not invent them.
- The current environment may not have live board access, so this sprint may stop at software export readiness.
- Full route execution, delivery/operator acceptance, current live HIL, safe-to-control, and production credit require separate live evidence.
