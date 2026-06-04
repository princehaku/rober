# Robot Software Runtime Root Cause Summary

generated_at: 2026-06-05 06:28:07 CST

## Scope

- Sprint: `sprints/2026.06.05_06-07_o9-pc-slam-runtime-epic`
- Owner: `robot-software-engineer`
- Evidence files:
  - `robot_software_radar_or_slam_lifecycle.log`
  - `robot_software_bash_ros2_map_root_cause.log`

## Runtime evidence

- `POST /api/radar/scan-proof/refresh` returned `status=refreshed`,
  `proof_state=scan_once_hz_raw_packet_tf_observed`, and
  `evidence_type=robot_runtime_material`.
- Latest radar status returned `scan_status=fresh_scan_proof_observed`,
  `latest_scan_hz_average_rate_hz=173.643`, and
  `runtime_summary_fallback_used=true`.
- Latest radar status still returned `continuous_scan_status=not_proven` and
  `continuous_blocked_reasons=["scan_continuity_not_observed"]`.

## Root cause

- Continuous radar is not proven because the live ROS graph has no continuous
  LiDAR runtime. After sourcing ROS2 with `bash -lc`, `ros2 topic list` returned
  only `/parameter_events` and `/rosout`.
- SLAM `/map` is not proven because no SLAM/map lifecycle runtime is active and
  no map artifacts exist. `GET /api/map/proof/latest` returned structured HTTP
  404 with `runtime/map_lifecycle_latest.json` missing, and
  `/root/rober/onboard/runtime/maps` does not exist.
- The required SSH command also exposed a command-shape blocker: the remote
  login shell is `zsh`, so directly sourcing `setup.bash` under the default
  shell leaves `ros2` unavailable. Use `bash -lc` for ROS2 validation commands.

## Next minimum command

Run a no-motion SLAM/map lifecycle proof in `bash -lc`, with LiDAR enabled and
without `/cmd_vel`, `/api/base/manual`, or base UART access. Minimum proof must
capture `/map` once, map YAML/image or pbstream artifact, map metadata, and the
same artifact through `GET /api/map/proof/latest`.

## Not proven

- continuous radar ready
- SLAM map usable
- AMCL/Nav2 ready
- PC WASD
- HIL
- `safe_to_control=true`
- delivery success
