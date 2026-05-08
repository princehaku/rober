# ROS Contracts

## Hardware: `esp32_bridge`

Vendor sources:

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

### Parameters

| Name | Type | Default | Contract |
| --- | --- | --- | --- |
| `serial_port` | string | `/dev/ttyUSB0` | Canonical UART device parameter. Confirm the Orange Pi device on hardware. |
| `serial_baudrate` | int | `115200` | Canonical UART baudrate parameter. Vendor examples use `115200`. |
| `port` | string | empty | Deprecated alias for `serial_port`. |
| `baudrate` | int | `0` | Deprecated alias for `serial_baudrate`; ignored when `0`. |
| `command_mode` | string | `speed` | `speed` maps `/cmd_vel` to vendor `T=1`; `ros` maps to vendor `T=13`. |
| `track_width_m` | double | `0.172` | Differential-drive width used by `speed` mode. Must be positive. |
| `max_wheel_speed_mps` | double | `1.3` | Normalization limit for `T=1` left/right values. Must be positive. |
| `feedback_interval_ms` | int | `100` | Sent to vendor `T=142`. Must be non-negative. |
| `odom_publish_hz` | double | `20.0` | ROS-side `/odom` publish rate. Must be positive. |

### Consumed Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | In `speed` mode, `linear.x` and `angular.z` are converted to normalized `T=1` `L`/`R`; positive `angular.z` makes left lower and right higher. In `ros` mode, the bridge sends `T=13` `X`/`Z`. |

### Produced Topics

| Topic | Type | Contract |
| --- | --- | --- |
| `/odom` | `nav_msgs/msg/Odometry` | Command-integrated odometry from last accepted `/cmd_vel`; not encoder-validated or fused localization. |
| `/imu/data` | `sensor_msgs/msg/Imu` | Yaw-only orientation derived from vendor `T=1001` field `y`. |
| `/battery` | `sensor_msgs/msg/BatteryState` | Voltage-only battery state from vendor `T=1001` field `v`. |

### Services

| Service | Type | Contract |
| --- | --- | --- |
| `/trashbot/stop` | `std_srvs/srv/Trigger` | Sends vendor `T=1` stop with `L=0`, `R=0`. |
| `/trashbot/reset_odom` | `std_srvs/srv/Trigger` | Resets ROS-side command-integrated odometry only; no ESP32 reset command is sent. |
| `/trashbot/beep` | `std_srvs/srv/Trigger` | Currently returns unsupported because the WAVE ROVER base JSON contract does not define a beep command. |

### UART Startup Contract

On startup the bridge sends:

1. `{"T":143,"cmd":0}` to disable UART echo.
2. `{"T":142,"cmd":feedback_interval_ms}` to set feedback interval.
3. `{"T":131,"cmd":1}` to enable streamed base feedback.

The ESP32 feedback frame used by this contract is vendor `T=1001` with at least `L`, `R`, `r`, `p`, `y`, and `v`.

## Behavior: `collect_trash`

### Action Server

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/collect_trash` | `ros2_trashbot_interfaces/action/TrashCollection` | Default product entry point is `task_orchestrator`; the legacy standalone server is installed as `legacy_trash_collection_server` only. |

### Feedback Fields

| Field | Contract |
| --- | --- |
| `status` | Compatibility numeric status: `0` idle/failure, `1` navigating, `3` delivering/dropoff, `4` done. |
| `percent_complete` | Compatibility progress percentage from `0` to `100`. |
| `current_step` | Compatibility readable step name. |
| `state` | Delivery state machine state, such as `loaded`, `delivering`, `dropoff`, `returning`, `idle`, or `error`. |
| `event` | Latest state machine event, including `invalid_transition` for rejected public transitions. |
| `message` | Human-readable progress or failure detail. |
| `elapsed_sec` | Elapsed action time in seconds. |

### Delivery Parameters

| Parameter | Values | Contract |
| --- | --- | --- |
| `delivery_mode` | `dry_run`, `waypoint`, `fixed_route` | `dry_run` succeeds without Nav2. `waypoint` resolves `delivery_target`/goal frame in `waypoint_file` and uses Nav2. `fixed_route` only reads `fixed_route_status_file`; it does not control UART or hardware directly. |
| `navigation_timeout_sec` | float seconds | Maximum duration for a waypoint or fixed-route attempt. |
| `navigation_retry_limit` | integer | Additional retry attempts after the first navigation attempt. |
| `dropoff_mode` | `dry_run`, `manual_confirm` | `dry_run` confirms immediately. `manual_confirm` waits through `dropoff_timeout_sec` unless canceled. |
| `dropoff_timeout_sec` | float seconds | Manual dropoff confirmation window. |
| `return_target` | waypoint name or empty | Optional return waypoint. Empty means no return navigation. |

### Dropoff Confirmation Service

| Name | Type | Contract |
| --- | --- | --- |
| `/trashbot/confirm_dropoff` | `std_srvs/srv/SetBool` | Valid only while a `manual_confirm` dropoff is pending. `request.data=true` confirms the user has removed or disposed of the load. `request.data=false` rejects the dropoff and the delivery action fails. `response.success=false` means no dropoff confirmation was pending. |

### Operator Gateway

The optional `operator_gateway` node exposes a local HTTP API for phone or browser control without requiring SSH or ROS2 CLI access.

| Endpoint | Method | Contract |
| --- | --- | --- |
| `/api/status` | GET | Returns `state`, `message`, `updated_at`, and the latest task metadata such as `task_record_path`, `error_message`, progress, or target when available. |
| `/api/collect` | POST | Starts `/trashbot/collect_trash`. Optional JSON body or query parameter `target` overrides the default delivery target. |
| `/api/dropoff/confirm` | POST | Calls `/trashbot/confirm_dropoff` with `true`. |
| `/api/cancel` | POST | Cancels the active `collect_trash` action goal if one is running. |

### Task Record

Every success, cancellation, missing target, navigation failure, dropoff failure, and unsupported-mode failure writes a JSON task record with `started_at`, `ended_at`, `delivery_mode`, `target`, `return_target`, `nav_attempts`, `nav_results`, `dropoff_result`, `detection_snapshot_refs`, `config`, `final_status`, and `error_message`. `dropoff_result` records `success`, `result_code`, `message`, `source`, and `elapsed_sec`; `manual_confirm_timeout` and `manual_rejected` are failures.
