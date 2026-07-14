# Final - O3 ROS2 Graph Timeout Root Cause

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout time: `2026-07-12 02:42 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## Summary

This sprint closes as a conservative diagnostic success. The old final `ros2_node_list_timeout` was split further, and the misleading reason `board_source_preflight_ready` is no longer the primary explanation in the fresh live artifact.

The accepted live result is still blocked and fail-closed:

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- `ros2_graph_timeout_root_cause.classification=ros2_cli_plugin_or_import_timeout`
- `primary_candidate.reason=ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`
- remaining candidates include `workspace_source_or_env_mismatch`, `managed_process_lifecycle_not_ready`, and `tf_runtime_secondary_after_graph_blocked`

## Actual Evidence

Algorithm evidence recorded in `tech-done.md`:

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`: passed.
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper`: passed, `Ran 87 tests in 2.252s OK`.
- Local helper dry-run: fail-closed exit `2`.
- Fresh live push: `scp returncode=0`.
- Fresh live helper: bounded remote helper `returncode=2`, `elapsed_s=138.856`.
- Fresh live pull: `scp returncode=0`.
- Fresh live artifact SHA256: `7f4f45b2303b33e1b112a39cc98440c9ade923af6bf4b50481fb9a5e4b26c645`.

## No-Motion Boundary

The sprint did not cross any motion or mission-success gate:

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

Therefore this is not path generation, route execution, delivery/operator acceptance, HIL pass, safe-to-control success, or production cloud external evidence.

## OKR Closeout

- O5 remains about `85%`; this sprint did not produce external production evidence.
- O1 remains about `93%`; this sprint did not produce current same-run path generation success, Nav2 route execution success, or HIL pass.
- O6 remains about `93%`; this sprint did not consume new same-task route/delivery/operator/production material.
- O7 remains about `93%`; this sprint did not add new operator-facing production or delivery acceptance evidence.
- `不调整` O5/O1/O6/O7 percentages.
- `不归档` KR.

## Product Judgment

Accepted as O3/O1 supporting no-motion diagnostic progress. The blocker has moved from the generic final `ros2_node_list_timeout` label to a more actionable CLI/plugin/import plus rclpy graph segment timeout classification, with workspace, lifecycle, and TF/runtime still listed as remaining candidates.

## Remaining Risk And Next Sprint

The next sprint should stay in O3/O1 no-motion and isolate the board-side cause of `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`. Do not attempt path generation, route execution, `/cmd_vel`, `/api/base/manual`, WAVE ROVER UART, delivery, or HIL until the graph/lifecycle/localization gates are ready.
