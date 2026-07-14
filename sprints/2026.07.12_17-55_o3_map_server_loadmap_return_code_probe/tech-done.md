# Tech Done - O3 Map Server LoadMap Return Code Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/`
- Owner: `robot-software-engineer`
- Boundary: `software_proof_o3_o1_strict_no_motion_map_server_loadmap_return_code_probe_only`
- Result: `/map_server active=true` was reached in the true-board strict no-motion artifact through managed runtime log lifecycle readback. Overall route/localization proof remains blocked and fail-closed.

## Actual Changes

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - Added `load_map_response_from_yaml` summary under `proof.map_server_transition_callback_probe`.
  - Split the 16:55 return-source bucket into direct LoadMap/YAML response-status fields:
    `direct_return_code_observed`, `return_code`, `response_status`,
    `load_map_response_status_at_changestate_failure`, `on_configure_return_path`,
    `executor_log_ordering_summary`, and `lifecycle_changestate_response_handling`.
  - Added strict no-motion stale managed-runtime process-group cleanup before starting a new managed runtime, scoped to helper-generated runtime markers.
  - Added managed runtime log lifecycle readback. When runtime logs show `Server map_server connected with bond`, `Server amcl connected with bond`, and `Managed nodes are active`, the artifact can mark `map_server_active=true` and `amcl_active=true` even if graph readback times out.
  - Preserved all motion/control booleans as fail-closed.
- `onboard/scripts/o11_nav2_lifecycle.sh`
  - Passed manager flags for base, LiDAR, LiDAR serial, and static laser TF settings so lifecycle shell startup matches the helper/runtime parameter surface.
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - Added/updated tests for LoadMap response-status classification, stale runtime cleanup scoping, and managed runtime log lifecycle active readback.
- `docs/navigation/field_route_evidence_preflight.md`
  - Documented the 17:55 `load_map_response_from_yaml` fields and final active-readback interpretation.
- `docs/navigation/fixed_route_workflow.md`
  - Documented how fixed-route consumers should treat the final `map_server_lifecycle_active` artifact: map-server lifecycle precondition is unblocked, but route/path gate remains closed until graph/topic/TF readback is clean.
- `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/artifacts/`
  - Wrote local and true-board strict no-motion raw artifacts.

## Verification Results

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Result: PASS, exit code 0.

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Result: PASS, exit code 0.
- Output: `Ran 129 tests in 2.294s` / `OK`.

```bash
bash -n onboard/scripts/o11_nav2_lifecycle.sh
```

- Result: PASS, exit code 0.

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --output-json sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/artifacts/local_o10_map_server_loadmap_return_code_probe.raw.json
```

- Result: expected fail-closed local artifact, exit code 2.
- Local boundary: macOS does not have `/opt/ros/humble/setup.bash`; artifact records `board_source_preflight_source_failed`.
- Local primary root cause: `map_lifecycle_latest_missing`.
- Safety readback: `safe_to_control=false`, `publishes_cmd_vel=false`, `calls_base_manual=false`, `uses_base_uart=false`, `route_execution_success=false`, `delivery_success=false`, `hil_pass=false`, `path_generation_attempted=false`, `path_generated=false`.

```bash
ssh -p 37878 root@192.168.1.11 \
  'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
```

- Result: PASS, exit code 0.

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Result: PASS, exit code 0.

```bash
scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh \
  root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
```

- Result: PASS, exit code 0.

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_map_server_loadmap_return_code_probe.raw.json'
```

- Result: artifact written, process exit code 2 because full downstream localization/path proof remains blocked.
- This is not an SSH/run/pull blocker; the 420s command completed naturally inside the timeout.
- True-board key fields:
  - `status=blocked_with_root_cause`
  - `map_server_active=true`
  - `amcl_active=true`
  - `managed_runtime_log_lifecycle_readback.clean=true`
  - `managed_runtime_log_lifecycle_readback.managed_nodes_active_logged=true`
  - `map_server_transition_callback_probe.canonical_classification=map_server_lifecycle_active`
  - `load_map_response_from_yaml.direct_return_code_observed=false`
  - `load_map_response_from_yaml.return_code=not_logged_by_nav2_map_server_runtime`
  - `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure`
  - `load_map_response_from_yaml.load_map_response_status_at_changestate_failure=completed_or_not_ordered_before_failure`
  - `load_map_response_from_yaml.on_configure_return_path=return_failure_after_loadmap_response_completion_log`
  - `commands.managed_runtime.pre_start_stale_cleanup.boundary=no_stale_managed_runtime_process_groups`
  - `commands.managed_runtime.pre_start_stale_cleanup.ok=true`

```bash
scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_map_server_loadmap_return_code_probe.raw.json \
  sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/artifacts/live_o10_map_server_loadmap_return_code_probe.raw.json
```

- Result: PASS, exit code 0.

## Failure Location

- Fixed/narrowed: 16:55 `/map_server active=false` is no longer the final blocker in the live artifact. The board run now proves `map_server_active=true` and `amcl_active=true` from lifecycle manager runtime logs.
- Remaining primary root cause:
  - `layer=Managed runtime graph readback`
  - `reason=managed_runtime_graph_probe_timeout_after_lifecycle_active_log`
  - `detail=map_server_and_amcl_lifecycle_active_logged_but_graph_wait_or_downstream_readback_not_clean`
- Secondary blocked facts in the same artifact:
  - `/scan_no_publisher`
  - `/map_once_not_observed`
  - `/amcl_pose_topic_missing`
  - `/tf_topic_missing`
- The LiDAR driver log still shows `SerialException: device reports readiness to read but returned no data (device disconnected or multiple access on port?)`, but it is not promoted to the only primary blocker in this sprint because the accepted Robot Software target was the map-server lifecycle gate and graph/downstream readback remains blocked first.

## No-Motion Safety Readback

True-board artifact safety fields remain fail-closed:

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `path_generation_attempted=false`
- `path_generated=false`

No `/cmd_vel`, `/api/base/manual`, NavigateToPose, WAVE ROVER UART, route execution, HIL, or delivery claim was made.

## Remaining Risks

- ROS graph readback can still time out after lifecycle active logs, so downstream topic/TF probes are not clean enough for path generation.
- AMCL still lacks initial pose / pose sample proof in this run.
- `/map` sample, `/scan` publisher/sample, `/tf`, and `map->odom` remain unproven.
- LiDAR serial instability may need Hardware follow-up if it becomes the next primary blocker; that follow-up must re-read `docs/vendor/VENDOR_INDEX.md`.
- This sprint is software proof only. It does not change OKR percentage, archive a KR, prove route execution, or prove production external evidence.

## Collaboration Needed

- Product: accept that the `/map_server active=true` objective was reached while path/route proof remains closed.
- Algorithm: next useful handoff is only after Robot Software chooses whether to fix graph readback first or proceed to AMCL initialpose/TF gate with active lifecycle evidence.
- Hardware: not needed for this sprint closeout; may be needed next if LiDAR serial becomes the selected primary blocker.
- Full-Stack: not needed.
