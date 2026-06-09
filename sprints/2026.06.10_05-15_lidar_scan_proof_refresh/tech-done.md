# LiDAR Scan Proof Refresh Tech Done

## Sprint Type

- `sprint_type: micro`
- Owner: `robot-hardware-engineer`
- Scope: true upper computer LiDAR-only `/scan` runtime proof refresh on `root@192.168.1.11:37878`.
- Remote capture time: `2026-06-10T04:28:20+08:00` to `2026-06-10T04:31:09+08:00`.

## Safety Boundary

Vendor and local source review completed before field action:

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/README.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

WAVE ROVER vendor facts used only as safety exclusions: the base UART protocol is UTF-8 newline-delimited JSON, vendor Raspberry Pi examples use `/dev/ttyAMA0` or `/dev/serial0` at `115200`, and base command IDs include `T=1`, `T=13`, `T=130`, `T=131`. This sprint did not send those commands and did not open `/dev/ttyS5` for base communication.

Allowed LiDAR path facts:

- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` references `/dev/ttyACM*` LiDAR serial at `230400` in the vendor upper-computer sample.
- The project board smoke history records the current Orange Pi field LiDAR as `/dev/ttyACM0 @ 150000`; this is a field observation, not a WAVE ROVER base UART fact.

Forbidden actions not performed:

- No non-zero `/cmd_vel`.
- No direct UART `T=1`, `T=13`, `T=130`, or `T=131`.
- No `/api/base/manual`, `/api/base/status`, `/api/base/stop`, `/api/map/start`, `/api/nav2/start`, or any base/navigation motion endpoint.
- Only `POST /api/radar/scan-proof/refresh` was called among write-like HTTP endpoints.

## Remote Pre-State

Artifacts:

- `artifacts/remote_capture/pre_service_status.txt`
- `artifacts/remote_capture/pre_device_enum.txt`
- `artifacts/remote_capture/pre_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/pre_ros_topic_list.txt`

Key observations:

- `trashbot-upper-robot-api.service` was `active (running)` with main PID `99004`.
- `/dev/ttyACM0` existed as STC USB Serial and `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`.
- `/dev/ttyS5` existed as the Orange Pi serial device.
- `lsof /dev/ttyS5 /dev/ttyACM0` had no process rows before refresh.
- Pre-refresh ROS topics were `/amcl_pose`, `/map`, `/parameter_events`, `/rosout`, and `/trashbot/waypoints`; `/scan` was missing.

## Refresh Result

Command executed on the upper computer:

```bash
curl -sS -X POST http://127.0.0.1:8787/api/radar/scan-proof/refresh \
  -H "Content-Type: application/json" \
  -d '{"start_runtime": true, "runtime_warmup_s": 6, "timeout_s": 12}'
```

Refresh response artifact:

- `artifacts/remote_capture/api_scan_proof_refresh_response.json`

Key response fields:

- `status=refreshed`
- `evidence_type=robot_runtime_material`
- `proof_state=scan_once_hz_raw_packet_tf_observed`
- `runtime_start_proven=true`
- `ros2_runtime_proven=true`
- `scan_runtime_proven=true`
- `proof_summary.scan_once_observed=true`
- `proof_summary.scan_hz_observed=true`
- `proof_summary.scan_hz_average_rate_hz=14.951`
- `proof_summary.raw_packet_once_observed=true`
- `proof_summary.tf_observed=true`
- `proof_summary.all_required_observations_observed=true`
- `runtime_start.allowed_script=o1_lidar_ros2_scan_smoke.sh`
- `runtime_start.log_path=/tmp/rober_lidar_scan_proof_runtime_1781036938372.log`
- `blocked_commands_not_sent=["T=1","T=13","T=130","T=131","/cmd_vel","/api/base/manual"]`
- `blocked_devices_not_opened=["/dev/ttyS5"]`
- `sends_motion_commands=false`
- `sends_base_motion_commands=false`
- `uses_base_uart=false`
- `publishes_cmd_vel=false`
- `safe_to_control=false`
- `hil_pass=false`

This proves a fresh API-managed LiDAR runtime window where ROS2 `/scan`, `/lidar/raw_packet`, and TF were observed. It does not prove continuous resident `/scan` after the smoke runtime exits.

## Pulled Artifacts

Remote `/tmp/o1_lidar_ros2_scan_smoke` files copied into `artifacts/o1_lidar_ros2_scan_smoke/`:

- `summary.json`
- `scan_hz.txt`
- `scan_once.txt`
- `topic_list.txt`
- `raw_packet_once.txt`
- `tf2_echo.txt`
- `tf_static.log`
- `lidar_driver.log`

Remote API/runtime files copied into sprint artifacts:

- `artifacts/lidar_scan_proof_latest.json`
- `artifacts/runtime_logs/rober_lidar_scan_proof_runtime_1781036938372.log`

The canonical latest artifact was found at `/root/rober/runtime/lidar_scan_proof_latest.json` with mtime `2026-06-10 04:29:23`.
The `artifacts/remote_capture/api_*_response.json` files keep the raw curl
capture format: line 1 is the JSON response payload and line 2 is
`HTTP_STATUS:<code>`. Use line 1 when parsing JSON, or use
`artifacts/lidar_scan_proof_latest.json` / `artifacts/o1_lidar_ros2_scan_smoke/summary.json`
for pure JSON proof material.

Runtime smoke summary:

- `driver_started_by_smoke=true`
- `lidar_start_command_sent_by_smoke=true`
- `lidar_start_command_hex=A5 60`
- `refuses_base_uart_ttyS5=true`
- `sends_base_motion_commands=false`
- `calls_base_manual=false`
- `publishes_cmd_vel=false`
- `all_required_observations_observed=true`

`scan_hz.txt` reported rates up to the final window:

```text
average rate: 14.855
    min: 0.001s max: 0.352s std dev: 0.04806s window: 111
```

`scan_once.txt` captured a `sensor_msgs/msg/LaserScan` sample with `frame_id=laser_frame`, `range_min=0.05`, `range_max=8.0`, and finite ranges.

## Post-State And Continuity Boundary

Artifacts:

- `artifacts/remote_capture/post_ros_topic_list.txt`
- `artifacts/remote_capture/post_lsof_ttyS5_ttyACM0.txt`
- `artifacts/remote_capture/post_scan_echo_once.txt`
- `artifacts/remote_capture/post_scan_hz.txt`
- `artifacts/remote_capture/final_lsof_and_runtime_processes.txt`
- `artifacts/remote_capture/final_ros_topic_list.txt`

Post-refresh immediate ROS topic list at `2026-06-10T04:29:34+08:00` included:

- `/lidar/raw_packet`
- `/scan`
- `/tf`
- `/tf_static`

The immediate post-refresh lsof showed only the LiDAR runtime touching `/dev/ttyACM0`:

```text
COMMAND      PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
lidar_dri 101492 root   19u   CHR  166,0      0t0  438 /dev/ttyACM0
```

There was no `/dev/ttyS5` row.

Manual `ros2 topic echo --once /scan` and short `ros2 topic hz /scan` were attempted at `2026-06-10T04:30:05+08:00`, after the smoke runtime had already exited. Both saw `/scan` missing:

```text
WARNING: topic [/scan] does not appear to be published yet
Could not determine the type for the passed topic
```

Final state at `2026-06-10T04:30:36+08:00`:

- `lsof /dev/ttyS5 /dev/ttyACM0` had no process rows.
- `ps` found no `o1_lidar_ros2_scan_smoke`, `lidar_driver`, or runtime log process.
- Final ROS topic list again omitted `/scan`.

Therefore the proof is fresh runtime material captured by the API-managed LiDAR smoke window, not a continuous always-on `/scan` service.

## API Readback

Artifacts:

- `artifacts/remote_capture/api_scan_proof_latest_response.json`
- `artifacts/remote_capture/api_radar_status_response.json`

`GET /api/radar/scan-proof/latest` returned HTTP 200 and the same proof status:

- `latest_proof_status=scan_once_hz_raw_packet_tf_observed`
- `latest_scan_once_observed=true`
- `latest_scan_hz_observed=true`
- `latest_scan_hz_average_rate_hz=14.951`
- `latest_raw_packet_once_observed=true`
- `latest_tf_observed=true`
- `latest_all_required_observations_observed=true`
- `sends_commands=false`
- `sends_motion_commands=false`
- `safe_to_control=false`
- `delivery_success=false`

`GET /api/radar/status` remained conservative:

- `sends_commands=false`
- `sends_motion_commands=false`
- `sends_base_motion_commands=false`
- `publishes_cmd_vel=false`
- `safe_to_control=false`
- `blocked_reasons=["scan_continuity_not_observed"]`

## Proof State

Proven true in this sprint:

- `scan_runtime_proven=true` for the API-managed LiDAR runtime window.
- `ros2_runtime_proven=true` for `/scan`, `/lidar/raw_packet`, and TF observation during that window.
- `/dev/ttyS5` was not opened by the LiDAR proof runtime.

Still false or not proven:

- `scan_continuity_not_observed` remains in radar status because `/scan` is not continuous after the runtime exits.
- `physical_motion_lidar_delta_proven=false`.
- `wheel_feedback_lr_nonzero_proven=false`.
- `safe_to_control=false`.
- `delivery_success=false`.
- This is not map, AMCL, Nav2, route, motion, or delivery proof.

## Validation Commands

Required local validation commands were run after documentation updates:

```bash
git status --short --branch --untracked-files=all
rg -n "LiDAR scan proof refresh|/api/radar/scan-proof/refresh|/scan|scan_runtime_proven|ros2_runtime_proven|sends_motion_commands|sends_base_motion_commands|uses_base_uart|/dev/ttyACM0|/dev/ttyS5|physical_motion_lidar_delta_proven|delivery_success" docs/hardware/board_sensor_stack_smoke.md sprints/2026.06.10_05-15_lidar_scan_proof_refresh/tech-done.md
find sprints/2026.06.10_05-15_lidar_scan_proof_refresh/artifacts -maxdepth 3 -type f | sort
git diff --check
```

See the final response for key output snippets.

## Remaining Risk

- The API proof refresh starts a temporary LiDAR smoke runtime and exits; it does not make `/scan` continuously available.
- The manual `ros2 topic echo --once /scan` and `ros2 topic hz /scan` commands were run after runtime exit, so they document the continuity boundary rather than adding live samples.
- No base feedback, odometry, wheel movement, map lifecycle, Nav2 consumption, route execution, or delivery success was tested in this no-motion sprint.
- Camera visible-content remains outside this sprint and is still required before any richer HIL lane.
