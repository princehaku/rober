# Side2Side Check - O3 ROS2 Graph Timeout Root Cause

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Check time: `2026-07-12 02:50 CST`

## Acceptance Verdict

Product acceptance: pass as a conservative O3/O1 supporting no-motion diagnostic delta.

This sprint successfully moved the previous `ros2_node_list_timeout` blocker into a lower-level classification and fixed the misleading `board_source_preflight_ready` reason. It does not prove path generation, route execution, delivery, HIL, safe-to-control, or production external evidence.

## Evidence Checked

- `tech-done.md` records `py_compile` passing.
- `tech-done.md` records `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` passing with `Ran 87 tests in 2.252s OK`.
- Local dry-run remains fail-closed with exit `2`.
- Fresh live rerun pushed the helper with `scp returncode=0`, ran the bounded remote helper with `returncode=2` and `elapsed_s=138.856`, then pulled the artifact with `returncode=0`.
- Fresh live artifact SHA256: `7f4f45b2303b33e1b112a39cc98440c9ade923af6bf4b50481fb9a5e4b26c645`.

## Artifact Fields

Fresh live artifact acceptance fields:

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- `ros2_graph_timeout_root_cause.classification=ros2_cli_plugin_or_import_timeout`
- `primary_candidate.reason=ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`
- remaining candidates include `workspace_source_or_env_mismatch`, `managed_process_lifecycle_not_ready`, and `tf_runtime_secondary_after_graph_blocked`

No-motion and fail-closed fields:

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## Side By Side Against PRD

| PRD expectation | Result | Product judgment |
| --- | --- | --- |
| Do not repeat only `ros2_node_list_timeout` | Artifact now classifies `ros2_cli_plugin_or_import_timeout` with concrete probe reason | Accepted |
| Do not leave partial `current_command=ros2 node list` | Fresh artifact has `artifact_kind=final` and `current_command=null` | Accepted |
| Keep no-motion safety fields false | All required control, delivery, route, HIL and UART fields remain false | Accepted |
| Sync sprint closeout docs | `side2side_check.md` and `final.md` created in this closeout | Accepted |

## OKR Judgment

- O5 remains about `85%`; no external production evidence was added.
- O1 remains about `93%`; no current same-run path generation, route execution, or HIL pass was added.
- O6 remains about `93%`; no new same-task delivery, route execution, or production readback material was consumed.
- O7 remains about `93%`; no new operator acceptance, route execution, or production UI evidence was consumed.
- `不调整` Objective percentages.
- `不归档` KR.

## Remaining Risk

The live primary classification is now narrower than the previous `ros2_node_list_timeout`, but it still blocks the graph/lifecycle/localization gate. The next sprint should isolate why `ros2 node list --help` and the rclpy graph segment probe time out on the board before attempting any planner path generation.
