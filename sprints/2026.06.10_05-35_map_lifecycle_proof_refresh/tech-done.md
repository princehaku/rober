# Map Lifecycle Proof Refresh Tech Done

## Sprint Type

- `sprint_type: micro`
- Owner: `robot-algorithm-engineer` + `rober-hardware-engineer`
- Scope: true upper-computer no-motion map lifecycle proof refresh on `root@192.168.1.11:37878`.
- Remote capture time: `2026-06-10T04:38:05+08:00` to `2026-06-10T04:40:13+08:00`.

## Safety Boundary

Required local source review was completed before field action:

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `onboard/scripts/upper_robot_api.py`
- `docs/hardware/board_sensor_stack_smoke.md`
- `sprints/2026.06.10_05-15_lidar_scan_proof_refresh/tech-done.md`

Vendor facts used only as safety exclusions: WAVE ROVER base UART is newline-delimited UTF-8 JSON, current board evidence uses `/dev/ttyS5 @ 115200` for base UART and `/dev/ttyACM0 @ 150000` for LiDAR, and `T=1`, `T=13`, `T=130`, `T=131` are WAVE ROVER command IDs that this sprint did not send.

Forbidden actions not performed:

- No non-zero `/cmd_vel`.
- No direct UART `T=1`, `T=13`, `T=130`, or `T=131` to `/dev/ttyS5`.
- No `/api/base/manual`, `/api/base/status`, `/api/base/stop`, `/api/map/start`, `/api/nav2/start`, `/api/nav2/proof/refresh`, or motion/navigation endpoint.
- The only write-like HTTP endpoint called was `POST /api/map/proof/refresh`.

## Remote Pre-State

Artifacts:

- `artifacts/remote_capture/pre_service_status.txt`
- `artifacts/remote_capture/pre_device_enum.txt`
- `artifacts/remote_capture/pre_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/pre_ros_topic_list.txt`
- `artifacts/remote_capture/pre_map_runtime_listing.txt`
- `artifacts/remote_capture/pre_api_map_proof_latest_response.json`
- `artifacts/remote_capture/pre_api_map_list_response.json`

Key observations:

- `trashbot-upper-robot-api.service` was `active (running)`.
- `/dev/ttyS5` and `/dev/ttyACM0` existed; `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`.
- `lsof /dev/ttyS5 /dev/ttyACM0` had no process rows before refresh.
- Pre-refresh ROS graph had `/amcl_pose`, `/map`, `/parameter_events`, `/rosout`, and `/trashbot/waypoints`; `/scan` was not present before the helper runtime.
- Pre-refresh `GET /api/map/proof/latest` returned the older successful material from the runtime readback path: `map_once_observed=true`, `map_file_observed=true`, `map_metadata_observed=true`. This was not current refresh evidence.

## Refresh Result

Command executed on the upper computer:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/map/proof/refresh \
  -H "Content-Type: application/json" \
  -d '{"timeout_s":60}'
```

Refresh response artifact:

- `artifacts/remote_capture/api_map_proof_refresh_response.json`

Key response fields:

- HTTP status: `200`
- top-level `status=not_proven`
- `failure_reason=configured_command_failed`
- helper `returncode=2`
- helper elapsed time: `46443ms`
- canonical latest evidence ref: `o3-map-lifecycle-1781037490165`
- canonical latest `status=blocked_with_root_cause`
- `scan_once_observed=true`
- `map_once_observed=false`
- `map_file_observed=true`
- `map_metadata_observed=false`
- root cause: `SLAM/TF/topic remap` / `/map_once_not_observed`
- helper runtime mode: `learn_launch_lidar_slam_no_motion`
- helper runtime command started `learn.launch.py` with `lidar_enabled:=true`, `lidar_serial_port:=/dev/ttyACM0`, `lidar_serial_baudrate:=150000`, `lidar_publish_raw_packets:=true`, and `no_motion_static_odom_tf:=true`.
- guard fields stayed false: `publishes_cmd_vel=false`, `calls_base_manual=false`, `sends_base_motion_commands=false`, `uses_base_uart=false`, `safe_to_control=false`, `delivery_success=false`.

The helper observed a fresh `/scan` sample and a runtime ROS graph containing `/scan`, `/map`, `/map_metadata`, `/tf`, `/tf_static`, and `slam_toolbox` topics. It still timed out on `timeout 12 ros2 topic echo --once /map`, so it skipped the save-map step and did not produce a new current map lifecycle proof.

Runtime log artifact:

- `artifacts/remote_capture/runtime_logs/rober_map_lifecycle_runtime_1781037503387.log`

The log shows `async_slam_toolbox_node`, `map_recorder`, `lidar_driver`, and `static_transform_publisher` starting, then repeated `slam_toolbox` message-filter drops for `laser_frame` scans because the queue filled. This is consistent with the helper root cause: `/scan` existed, but SLAM did not produce a usable one-shot `/map` observation inside the proof window.

## Map Artifact State

Artifacts copied from the upper computer:

- `artifacts/remote_capture/onboard_runtime_map_lifecycle_latest.json`
- `artifacts/remote_capture/legacy_runtime_map_lifecycle_latest.json`
- `artifacts/remote_capture/runtime_maps/trashbot_map.yaml`
- `artifacts/remote_capture/runtime_maps/trashbot_map.pgm`

Important distinction:

- Canonical current file `/root/rober/onboard/runtime/map_lifecycle_latest.json` is now `blocked_with_root_cause`.
- Legacy file `/root/rober/runtime/map_lifecycle_latest.json` still contains the older `map_once_artifact_metadata_observed` proof and must not be treated as this run's current result.
- `runtime_maps/trashbot_map.yaml` and `runtime_maps/trashbot_map.pgm` exist, but their remote mtimes are still `1780633687044` and `1780633687036`; this refresh did not prove a newly saved map.

Map file observations:

- `map_file_observed=true` only means the canonical map directory has YAML/PGM candidates.
- `map_once_observed=false` because `/map` one-shot timed out in the current helper runtime.
- `map_metadata_observed=false` because no current metadata was captured.
- `real_route_map_proven=false`; no same-run movement, `route.csv`, keyframes, rosbag, fixed-route replay, Nav2 goal, or delivery evidence was collected.

## API Readback And Downstream Boundary

Artifacts:

- `artifacts/remote_capture/post_api_map_proof_latest_response.json`
- `artifacts/remote_capture/post_api_map_list_response.json`
- `artifacts/remote_capture/post_api_nav2_status_response.json`

Post-refresh `GET /api/map/proof/latest` loaded the canonical current artifact and returned:

- `latest_proof_status=blocked_with_root_cause`
- `latest_map_once_observed=false`
- `latest_map_file_observed=true`
- `latest_map_metadata_observed=false`
- `safe_to_control=false`
- `delivery_success=false`

Post-refresh `GET /api/map/list` listed only:

- `/root/rober/onboard/runtime/maps/trashbot_map.yaml`
- `/root/rober/onboard/runtime/maps/trashbot_map.pgm`

Post-refresh `GET /api/nav2/status` stayed conservative:

- `status=not_proven`
- `amcl_nav2_readiness.status=blocked_with_root_cause`
- readiness blockers: `map_lifecycle_proof_not_clean`, `map_once_not_observed`, `map_metadata_not_observed`
- `latest_map_server_active=false`
- `latest_scan_consumed=false`
- `latest_map_consumed=false`
- `latest_path_generated=false`
- `safe_to_control=false`
- `delivery_success=false`

This confirms the downstream readiness boundary: the old YAML/PGM files are material candidates, but current map lifecycle proof does not unlock AMCL/Nav2 proof or route execution.

## Cleanup State

Artifacts:

- `artifacts/remote_capture/final_clean_after_capture_bash.txt`
- `artifacts/remote_capture/final_ros_topic_list.txt`
- `artifacts/remote_capture/post_lsof_ttyS5_ttyACM0.txt`

Authoritative cleanup check at `2026-06-10T04:40:13+08:00`:

- `trashbot-upper-robot-api.service` was `active`.
- `lsof /dev/ttyS5 /dev/ttyACM0` had no process rows.
- No `o3_map_lifecycle_proof`, `slam_toolbox`, `map_saver`, `lidar_driver`, or `ros2 launch` process remained.
- Final ROS graph returned to `/amcl_pose`, `/map`, `/parameter_events`, `/rosout`, and `/trashbot/waypoints`; `/scan` was absent after the helper runtime exited.

## Raw Artifact Format

The `artifacts/remote_capture/api_*_response.json` files are raw curl captures: line 1 is the JSON payload and line 2 is `HTTP_STATUS:<code>`. Validation parsed line 1 of all six raw curl files successfully. Pure JSON proof files are:

- `artifacts/remote_capture/onboard_runtime_map_lifecycle_latest.json`
- `artifacts/remote_capture/legacy_runtime_map_lifecycle_latest.json`

## Proof State

Proven true in this sprint:

- SSH/API path reached the true upper computer.
- The built-in no-motion map lifecycle helper executed.
- The helper started a LiDAR + SLAM no-motion runtime and observed `/scan`.
- The helper did not open `/dev/ttyS5`, did not publish `/cmd_vel`, and did not call base/manual.
- The canonical current map lifecycle artifact was refreshed to the latest failure state, replacing stale optimism with current root cause.

Still false or not proven:

- `map_once_observed=false`
- `map_metadata_observed=false`
- `map_artifact_proven=false` for current lifecycle proof, even though old YAML/PGM files exist.
- `real_route_map_proven=false`
- `nav2_runtime_proven=false`
- `path_generated=false`
- `fixed_route_execution=false`
- `safe_to_control=false`
- `delivery_success=false`

## Failure定位

Primary root cause: current no-motion SLAM runtime did not provide a `/map` one-shot within the helper window. The runtime log shows `slam_toolbox` repeatedly dropping `laser_frame` messages because the queue was full. The helper therefore skipped save-map and reported `/map_once_not_observed`.

Likely next no-motion debug direction is SLAM/TF/topic timing rather than base hardware: confirm `laser_frame -> base_link -> odom` TF direction/timestamps, SLAM queue settings, scan rate/queue compatibility, and whether `/map` is latched or delayed beyond the helper's 12-second `map_once` echo window.

## Validation Commands

Required local validation commands were run after documentation updates:

```bash
git status --short --branch --untracked-files=all
rg -n "map lifecycle proof refresh|/api/map/proof/refresh|map_once|map_file|map_metadata|map_yaml|map_pgm|real_route_map_proven|sends_motion_commands|publishes_cmd_vel|calls_base_manual|/dev/ttyS5|/dev/ttyACM0|delivery_success" docs/hardware/board_sensor_stack_smoke.md sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/tech-done.md
find sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/artifacts -maxdepth 4 -type f | sort
git diff --check
```

Validation results:

- `git status --short --branch --untracked-files=all` showed only the expected modified `docs/hardware/board_sensor_stack_smoke.md` plus the new `sprints/2026.06.10_05-35_map_lifecycle_proof_refresh/` files.
- `rg` found the required proof terms in this `tech-done.md` and in `docs/hardware/board_sensor_stack_smoke.md`, including `/api/map/proof/refresh`, `map_once_observed=false`, `map_file_observed=true`, `map_metadata_observed=false`, `real_route_map_proven=false`, `publishes_cmd_vel=false`, `calls_base_manual=false`, `/dev/ttyS5`, `/dev/ttyACM0`, and `delivery_success=false`.
- `find .../artifacts -maxdepth 4 -type f | sort` listed 36 pulled artifact files, including raw API responses, canonical/legacy proof JSON, `trashbot_map.yaml`, `trashbot_map.pgm`, runtime log, and cleanup proof.
- `git diff --check` produced no output.
- Raw curl artifact validation parsed line 1 of all six `api_*_response.json` files successfully; pure JSON validation passed for `onboard_runtime_map_lifecycle_latest.json` and `legacy_runtime_map_lifecycle_latest.json`.
