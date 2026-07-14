# Final - O3 Radar Status Baudrate Readback Repair

## Product Acceptance

Product accepts this sprint as O3/O1 strict no-motion same-run planner-only path proof after a two-gate repair:

- Gate 1 Robot Software repaired `/api/radar/status` baudrate readback.
- Gate 2 Algorithm reused the existing `150000` LiDAR lifecycle and, after fallback repair, generated a same-run ComputePathToPose path without motion.

Proof boundary: `software_proof_o3_o1_strict_no_motion_planner_only_path_proof`.

## 用户价值和产品北极星

北极星仍是普通手机用户一键发车送垃圾，并得到可验证结果。本轮的用户价值是把真实上位机导航链路推进到“同轮可生成路径”的明确证据层：以后路线执行失败不能再归因于 stale radar status、generic `/scan` wrapper 或未尝试 path generation。

## OKR Mapping And Direction

- Direction: continue O3/O1 strict no-motion toward fixed-route replay and route execution.
- O1: adjust conservatively from about `93%` to `约 94%` because current same-run planner-only path generation is now proven.
- O5: remains about `85%`; no external production evidence was added.
- O6/O7: remain about `93%`; no live route execution, delivery/operator, or production readback was added.
- KR archive decision: `不归档`.

This O1 adjustment is no-motion planner-only path proof credit. It is not mission delivery credit.

## KR 拆解、更新或历史归档

No KR is archived. Completed KR historical records remain in `OKR.md` archived Objective/KR section and `docs/process/okr_progress_log.md`.

New evidence added to the current O3/O1 chain:

- Radar status current readback: `baudrate=150000`.
- LiDAR reuse policy: `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`.
- Same-run inputs: `/scan`, `/map`, `/amcl_pose`, initialpose, and `map_to_odom`.
- Planner-only path: `path_generation_attempted=true`, `path_generated=true`, `path_point_count=21`.

## Core Lever

The sprint turned a stale-readback blocker into a planner-only path proof:

- `baudrate_readback_source=driver_diagnostics_latest.serial.serial_baudrate`.
- `managed_lidar_driver_started_by_helper=false`.
- `fallback_mode=ros2_cli_action_send_goal`.
- `path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion`.
- `root_causes=[]`.

## Actual Closeout Updates

Product closeout created or updated:

- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/side2side_check.md`
- `sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

Engineering evidence accepted from `tech-done.md`:

- Robot Software compile: `python3 -m py_compile onboard/scripts/upper_robot_api.py`, exit `0`.
- Robot Software tests: `Ran 113 tests in 0.333s OK (skipped=1)`.
- Gate 2 first run compile/tests: `Ran 134 tests in 2.305s OK`.
- Gate 2 fallback repair tests: `Ran 139 tests in 2.275s OK`.
- Owner implementation evidence is recorded in `tech-done.md`; Product closeout ran the scoped `rg` and `git diff --check` commands listed below.

## Accepted Evidence

Robot Software artifact:

- `artifacts/robot_software/board_radar_status_after_deploy.json`
- `baudrate=150000`
- `baudrate_readback_source=driver_diagnostics_latest.serial.serial_baudrate`
- start/scan-proof controls include `--serial-baudrate 150000`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

Algorithm artifact:

- `artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`
- `status=nav2_no_motion_path_generation_runtime_observed`
- `evidence_type=robot_runtime_material`
- `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`
- `managed_lidar_driver_started_by_helper=false`
- `managed_lidar_serial_baudrate=150000`
- `scan_once_observed=true`
- `map_once_observed=true`
- `amcl_pose_observed=true`
- `initialpose_published=true`
- `map_to_odom=true`
- `path_generation_attempted=true`
- `path_generated=true`
- `path_point_count=21`
- `fallback_used=true`
- `fallback_mode=ros2_cli_action_send_goal`
- `root_causes=[]`

## Rejected Scope

This sprint is not:

- route execution
- NavigateToPose
- controller/BT execution
- `/cmd_vel`
- `/api/base/manual`
- WAVE ROVER UART
- delivery/operator acceptance
- current live HIL
- safe-to-control
- production external evidence

Safety fields remain fixed:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Priority And Next Acceptance

Next owner: `robot-algorithm-engineer`.

Support owner: `robot-software-engineer` only if action/runtime readback regresses.

Next sprint should convert this proof into fixed-route replay or route-intent material while keeping no-motion boundaries. Route execution credit requires an actual Nav2 route/goal execution record. Delivery credit requires delivery/operator evidence. HIL credit requires current live HIL acceptance.

## Risks And Remaining Evidence Gap

- Planner-only path generation does not prove route following.
- CLI action fallback is acceptable for ComputePathToPose evidence but is not a product control interface.
- No current live HIL acceptance exists.
- No delivery/operator acceptance exists.
- No production cloud or external readback exists.
- Existing LiDAR lifecycle should continue to be reused unless Hardware explicitly owns an exclusive check after reading vendor docs.

## Verification Evidence

Product closeout validation:

```text
rg -n "radar status|baudrate=150000|nav2_no_motion_path_generation_runtime_observed|path_generated=true|path_point_count=21|fallback_mode=ros2_cli_action_send_goal|safe_to_control=false|route_execution_success=false|delivery_success=false|hil_pass=false|约 94%|不归档|O5.*85" ...
exit 0

git diff --check -- sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/side2side_check.md sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/final.md OKR.md docs/process/okr_progress_log.md
exit 0
```
