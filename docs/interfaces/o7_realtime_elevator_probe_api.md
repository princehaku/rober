# O7 Realtime/Elevator Probe API

`pc-tools/workstation` exposes `GET /api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>` as a PC-only, read-only probe for the relay endpoint `/api/o7/realtime-elevator/snapshot`.

## Boundary

- Allowed `baseUrl` values are local HTTP loopback only: `http://127.0.0.1`, `http://localhost`, or `http://[::1]`.
- The browser calls the PC workstation backend; the browser does not directly fetch relay, ROS2, `/tf`, map files, elevator devices, hardware, RTC, video, or control APIs.
- The response is `trashbot.pc_tools_workstation.o7_realtime_elevator_probe.v1` and remains `source=software_proof`, `proof_status=not_proven`, `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `pc_only=true`.

## Safe Summary Fields

The PC UI may display only the probe response safe strings:

- `map_ref_summary`
- `map_frame_summary`
- `robot_pose_summary`
- `pose_freshness_summary`
- `probe_observed_at_ms`
- `remote_pose_timestamp_ms`
- `remote_pose_age_ms`
- `freshness_gate_status`
- `latency_lt_2s_proven`
- `elevator_status`
- `elevator_state_samples_summary`
- `current_floor_evidence_summary`
- `human_takeover_summary`

`robot_pose_summary` may be parsed in the browser only for `x_m`, `y_m`, and `yaw_rad` when the string contains tokens such as `x_m=1.25, y_m=-0.75, yaw_rad=1.57`. If parsing fails, the UI must show `blocked_pose_coordinate_unavailable` and must not draw a marker.

The freshness gate fields are PC-only observation metadata:

- `probe_observed_at_ms` is the workstation backend time when the probe response was summarized.
- `remote_pose_timestamp_ms` is copied only from numeric `robot_pose.timestamp_ms`; otherwise it is `null`.
- `remote_pose_age_ms` is copied from numeric `pose_freshness.age_ms` when available, or derived as `probe_observed_at_ms - remote_pose_timestamp_ms`; otherwise it is `null`.
- `freshness_gate_status` is a fail-closed status string for the PC probe gate.
- `latency_lt_2s_proven` is always `false`.

These fields do not prove real ROS2 `/tf`, a real realtime API, real auto-refresh, or <2s latency. Even when `remote_pose_age_ms` is below 2000, the proof boundary remains `proof_status=not_proven`.

## Visualization Contract

The `Realtime map pose preview` is a fixed-viewBox SVG visualization of the safe summary fields only. It must show `map_visualization_status`, `pose_marker`, `map_frame/ref`, `latency_lt_2s_proven=false`, `real_ros2_tf_connected=false`, `real_realtime_api_connected=false`, `safe_to_control=false`, and `robot_control_executed=false`.

The `Elevator state timeline preview` displays at most five `elevator_state_samples_summary` strings with local sample indexes. Empty samples must show `blocked_not_proven`. It must keep `real_elevator_state_chain_connected=false`, `floor_recognition_proven=false`, `human_takeover_proven=false`, and `safe_to_control=false`.

These previews do not prove real realtime map/pose, ROS2 `/tf`, <2s latency, real elevator state chain, floor recognition, human takeover, robot ACK, hardware safety, or O7 completion.
