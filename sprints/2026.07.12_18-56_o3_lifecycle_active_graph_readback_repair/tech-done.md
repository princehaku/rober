# Tech Done - O3 Lifecycle-Active Graph Readback Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair/`
- Owner: `Robot Software`
- Status: implementation validated, strict no-motion live artifact still blocked with narrower downstream root cause.

## Actual Changes

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - Preserved the 17:55 lifecycle-active baseline by reading `managed_runtime_log_lifecycle_readback` before deciding whether graph wait should suppress downstream probes.
  - Added `managed_runtime_wait_graph_blocked_without_lifecycle_log`; graph wait now blocks downstream only when lifecycle-active log evidence is not clean.
  - When lifecycle-active log readback is clean, the helper continues bounded no-motion downstream readback for `/scan`, `/map`, `/amcl_pose`, TF source, and summaries even if the managed graph wait still reports `ros2_node_list_timeout`.
  - Updated root-cause normalization so concrete downstream blockers can become `artifact_closeout.primary_root_cause`; `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` is retained as secondary diagnostic instead of hiding `/scan` / AMCL / TF gates.
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - Added regression coverage for lifecycle-active log override after graph wait blocked.
  - Added regression coverage that promotes concrete downstream root cause after lifecycle-active log evidence.
- `docs/navigation/field_route_evidence_preflight.md`
  - Documented the 18:56 lifecycle-active downstream readback rule and strict no-motion boundary.
  - Corrected 17:55 routing wording to treat `map_server_lifecycle_active` as the accepted baseline.
- `docs/navigation/fixed_route_workflow.md`
  - Corrected the stale 17:55 `map_server_loadmap_response_success_equivalent_after_changestate_failure` wording: it is context, not the accepted final routing label.
  - Documented the new read order: primary root cause, downstream recovery summary, signal freshness, TF readiness, then graph timeout as secondary diagnostic.
- `onboard/scripts/o11_nav2_lifecycle.sh`
  - Existing scoped diff includes manager flag forwarding for base/lidar/static TF runtime inputs; syntax validation passed.
- Artifacts written:
  - `artifacts/local_o10_lifecycle_active_graph_readback_repair.raw.json`
  - `artifacts/live_o10_lifecycle_active_graph_readback_repair.raw.json`

## Validation Results

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 131 tests in 2.287s
OK
```

```text
bash -n onboard/scripts/o11_nav2_lifecycle.sh
exit 0
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json artifacts/local_o10_lifecycle_active_graph_readback_repair.raw.json
exit 2
```

Local macOS result is expected fail-closed: ROS setup is unavailable locally, `board_source_preflight_source_failed`, artifact written, all safety and motion fields stayed false.

```text
ssh/scp true-board deploy commands
exit 0

true-board strict no-motion helper
remote_rc=2

scp live artifact back
exit 0
```

Live artifact summary:

- `status=blocked_with_root_cause`
- `map_server_active=true`
- `amcl_active=true`
- `managed_runtime_log_lifecycle_readback.clean=true`
- `managed_runtime_wait_result.reason=ros2_node_list_timeout`
- `artifact_closeout.primary_root_cause.reason=/scan_reliable_and_best_effort_timeout`
- secondary root cause retains `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
- `/map_once_not_observed=false`; `/map` sample was observed
- AMCL remains blocked at `/amcl_pose_once_not_observed`
- TF remains blocked at `map_to_odom_dynamic_source_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

```text
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/o11_nav2_lifecycle.sh onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_18-56_o3_lifecycle_active_graph_readback_repair
exit 0
```

## Failure Location

This sprint moved the blocker forward. It is no longer acceptable to close the lane as old `map_server_lifecycle_not_active`, `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`, or ChangeState wrapper work.

Current true-board blocker:

- Primary: `/scan_reliable_and_best_effort_timeout`
- Secondary diagnostic: `managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
- Additional downstream gates: `/amcl_pose_once_not_observed` and `map_to_odom_dynamic_source_missing`

This is strict no-motion diagnostic evidence only. It does not prove path generation, route execution, delivery, HIL, or safe-to-control.

## Remaining Risks

- `/scan` has a publisher/runtime path but no sample was read through BEST_EFFORT or RELIABLE attempts in the proof window.
- `/amcl_pose` was not observed, so AMCL localization readiness is still false even though AMCL lifecycle is active.
- Dynamic `map->odom` source is still missing, so `map->base_link` remains blocked downstream.
- `ros2_node_list_timeout` still appears as a secondary graph diagnostic; it should not be ignored, but it no longer masks the concrete downstream blockers.
- No Product/OKR percentage update should be claimed from this sprint.

## Coordination

- Product: needed only for acceptance/final closeout and OKR flat-score wording.
- Hardware: not needed yet; LiDAR wiring/serial/vendor investigation should wait until `/scan` timeout is proven to be publisher/runtime or hardware-primary rather than ROS readback/QoS/window.
- Autonomy: wait until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof.
- Full-Stack: not needed.
