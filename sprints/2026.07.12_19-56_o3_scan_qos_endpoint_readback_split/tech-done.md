# Tech Done - O3 Scan QoS Endpoint Readback Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/`
- Owner: `Robot Software`
- Completed at: `2026-07-12 20:16 CST`
- Status: implementation validated; true-board strict no-motion artifact remains blocked, but primary root cause is narrower than the starting `/scan_reliable_and_best_effort_timeout`.

## Actual Changes

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - Added `proof.scan_qos_endpoint_readback_split` with three explicit layers:
    `publisher_endpoint_classification`, `qos_window_ros_readback_classification`, and `lidar_runtime_classification`.
  - Added endpoint stability and requested-vs-offered QoS compatibility readback for `/scan`.
  - Added LiDAR runtime handoff classification only after endpoint is visible, BEST_EFFORT and RELIABLE child attempts both timeout, QoS is compatible, and `sample_count=0`.
  - Enriched `artifact_closeout.primary_root_cause` so the primary reason becomes the most specific split reason while retaining `canonical_blocker=/scan_reliable_and_best_effort_timeout`.
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - Added regression coverage for endpoint-visible, QoS-compatible, no-sample `/scan` split.
  - Added regression coverage that `attach_artifact_summaries()` promotes the split reason into the primary root cause.
- `docs/navigation/field_route_evidence_preflight.md`
  - Documented the new `scan_qos_endpoint_readback_split` read order and Hardware handoff boundary.
- `docs/navigation/fixed_route_workflow.md`
  - Documented the fixed-route/no-motion closeout rule for reading publisher endpoint, QoS/window, runtime classification, and `primary_split`.
- Artifacts written:
  - `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/local_o10_scan_qos_endpoint_readback_split.raw.json`
  - `sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json`

## Validation Results

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 133 tests in 2.302s
OK
```

```text
bash -n onboard/scripts/o11_nav2_lifecycle.sh
exit 0
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/local_o10_scan_qos_endpoint_readback_split.raw.json
exit 2
```

Local macOS result is expected fail-closed: `/opt/ros/humble/setup.bash` and `/root/rober/onboard/install/setup.bash` are not present locally, so the artifact stayed at `board_source_preflight_source_failed`. This local result does not replace live evidence.

```text
ssh -p 37878 root@192.168.1.11 'mkdir -p /root/rober/onboard/scripts /tmp/rober_o10_artifacts'
exit 0

scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0

scp -P 37878 onboard/scripts/o11_nav2_lifecycle.sh root@192.168.1.11:/root/rober/onboard/scripts/o11_nav2_lifecycle.sh
exit 0

ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && /usr/bin/timeout 420s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --output-json /tmp/rober_o10_artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json'
remote_rc=2

scp -P 37878 root@192.168.1.11:/tmp/rober_o10_artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json
exit 0
```

```text
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/o11_nav2_lifecycle.sh onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split
exit 0
```

## Live Artifact Anchors

Primary live artifact:
`sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json`

- Starting canonical blocker retained: `/scan_reliable_and_best_effort_timeout`.
- New primary root cause:
  `/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`.
- `artifact_closeout.primary_root_cause.canonical_blocker=/scan_reliable_and_best_effort_timeout`.
- `artifact_closeout.primary_root_cause.split_classification=lidar_runtime_exception_candidate_after_endpoint_qos_readback_split`.
- `artifact_closeout.primary_root_cause.next_owner=hardware_after_vendor_doc_review`.
- publisher endpoint classification:
  `publisher_endpoint_classification.classification=publisher_endpoint_visible`.
- `/scan` publisher endpoint:
  `publisher_count=1`, `publisher_nodes[0].node_name=lidar_driver`, `topic_type=sensor_msgs/msg/LaserScan`.
- Publisher QoS:
  `publisher_reliability_values=["RELIABLE"]`.
- Endpoint stability:
  `publisher_stability.stable=true`, observed across 2 child attempts.
- QoS/window/ROS readback classification:
  `qos_window_ros_readback_classification.classification=qos_compatible_readback_timeout_no_samples`.
- BEST_EFFORT readback:
  `timed_out=true`, `sample_count=0`, `subscription_created=true`, `import_ok=true`.
- RELIABLE readback:
  `timed_out=true`, `sample_count=0`, `subscription_created=true`, `import_ok=true`.
- Requested vs endpoint QoS:
  `best_effort_compatible=true`, `reliable_compatible=true`, `compatibility_risk=false`.
- LiDAR runtime classification reached:
  `lidar_runtime_classification.classification=lidar_runtime_exception_candidate_after_endpoint_qos_readback_split`.
- Runtime exception observed:
  `runtime_exception.type=serial.serialutil.SerialException`, `message_hint=device reports readiness to read but returned no data`.
- Hardware handoff condition:
  `hardware_handoff_allowed=true`, `hardware_handoff_requires_vendor_docs=true`, `does_not_claim_vendor_hardware_root_cause=true`.
- `map_server_active=true`.
- `amcl_active=true`.
- `managed_runtime_log_lifecycle_readback.clean=true`.
- `amcl_pose_observed=false`.
- TF remains blocked at `map_to_odom_dynamic_source_missing`.
- `path_generation_attempted=false`.
- `path_generated=false`.
- `safe_to_control=false`.
- `publishes_cmd_vel=false`.
- `calls_base_manual=false`.
- `uses_base_uart=false`.
- `robot_control_executed=false`.
- `route_execution_success=false`.
- `delivery_success=false`.
- `hil_pass=false`.

## Failure Location

This sprint no longer closes as generic `/scan_reliable_and_best_effort_timeout`.

Current true-board split:

- Endpoint layer: `/scan` endpoint exists and is stable; `lidar_driver` publishes `sensor_msgs/msg/LaserScan` with `RELIABLE` QoS.
- QoS/readback layer: BEST_EFFORT and RELIABLE requested QoS are compatible with the publisher endpoint; both child readback attempts timed out with `sample_count=0`, and both CLI fallbacks also timed out.
- Runtime layer: managed runtime log observed a LiDAR runtime `serial.serialutil.SerialException`. This is enough to hand off to Hardware after vendor-doc review, but it is not a vendor-backed hardware root cause by itself.

Downstream gates remain blocked:

- `/amcl_pose` not observed.
- Dynamic `map->odom` source missing.
- Path generation not attempted and not generated.

## Remaining Risks

- The live result is still strict no-motion diagnostic evidence only; it does not prove same-run path generation, route execution, delivery success, HIL pass, or safe-to-control.
- ROS readback false timeout remains possible in principle because `ros_readback_false_timeout_still_possible=true`, though endpoint visibility, QoS compatibility, dual child timeout, CLI timeout, and the runtime exception make the next actionable handoff narrower.
- Hardware must read `docs/vendor/VENDOR_INDEX.md` before making any vendor-backed conclusion about LiDAR serial/runtime/wiring; this sprint intentionally did not edit serial, UART, baudrate, wiring, voltage, WAVE ROVER, or ESP32 configuration.
- Algorithm should continue waiting until `/scan`, `/amcl_pose`, and dynamic `map->odom` are clean enough for planner-only path proof.

## Coordination

- Product: needed for acceptance, flat OKR wording, and final closeout.
- Hardware: now has a bounded handoff condition, but must perform vendor-doc-backed diagnosis before changing hardware config or claiming root cause.
- Autonomy: not yet; `/scan` sample, `/amcl_pose`, and dynamic `map->odom` are still not clean.
- Full-Stack: not needed.
