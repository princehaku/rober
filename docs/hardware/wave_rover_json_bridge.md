# WAVE ROVER JSON Bridge

## Sources

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/IMU_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/battery_ctrl.h`

## UART Framing

The official WAVE ROVER ESP32 firmware expects one UTF-8 JSON object per UART line, terminated by `\n`.

Vendor Raspberry Pi examples use `/dev/ttyAMA0` or `/dev/serial0` at `115200`. On the Orange Pi robot, confirm the actual Linux UART device before launch; do not hardcode Raspberry Pi paths.

## Command Table

| ROS bridge use | Vendor JSON | Direction | Source |
| --- | --- | --- | --- |
| Stop or left/right speed command | `{"T":1,"L":0.0,"R":0.0}` | ROS to ESP32 | `json_cmd.h` `CMD_SPEED_CTRL`, `base_ctrl.py` |
| ROS velocity command mode | `{"T":13,"X":0.1,"Z":0.3}` | ROS to ESP32 | `json_cmd.h` `CMD_ROS_CTRL`, `movtion_module.h` `rosCtrl()` |
| One-shot base feedback request | `{"T":130}` | ROS to ESP32 | `json_cmd.h` `CMD_BASE_FEEDBACK` |
| Enable/disable feedback stream | `{"T":131,"cmd":1}` / `{"T":131,"cmd":0}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Feedback stream interval | `{"T":142,"cmd":100}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h`, `ugv_advance.h` |
| UART echo off/on | `{"T":143,"cmd":0}` / `{"T":143,"cmd":1}` | ROS to ESP32 | `json_cmd.h`, `uart_ctrl.h` |
| Base feedback frame | `{"T":1001,"L":...,"R":...,"r":...,"p":...,"y":...,"v":...}` | ESP32 to ROS | `json_cmd.h` `FEEDBACK_BASE_INFO`, `ugv_advance.h` |

## Command Modes

- `speed`: maps ROS `/cmd_vel` to `T=1` left/right speed values. This is the conservative project default.
- `ros`: maps ROS `/cmd_vel` to `T=13` `X`/`Z` values. Enable only after hardware validation on the loaded firmware.

For `speed` mode, positive `angular.z` lowers the left wheel command and raises the right wheel command using the differential-drive relation:

```text
left_mps = linear.x - angular.z * track_width_m / 2
right_mps = linear.x + angular.z * track_width_m / 2
```

The normalized `T=1` `L` and `R` values are clamped to `[-1.0, 1.0]` using `max_wheel_speed_mps`.

## Configurable Launch Parameters

- `serial_port`
- `serial_baudrate`
- `port` deprecated alias for `serial_port`
- `baudrate` deprecated alias for `serial_baudrate`
- `command_mode`
- `track_width_m`
- `max_wheel_speed_mps`
- `feedback_interval_ms`
- `odom_publish_hz`

Startup validation rejects unknown `command_mode`, non-positive `track_width_m`, non-positive `max_wheel_speed_mps`, negative `feedback_interval_ms`, and non-positive `odom_publish_hz`.

## Published ROS Data Contracts

### `/odom`

`/odom` is currently ROS-side command integration from the last accepted `/cmd_vel`, not a fused or encoder-validated pose. The vendor `T=1001` feedback includes wheel speed fields `L` and `R`, but the current bridge does not yet treat them as calibrated odometry. Use this topic for bringup visibility only until wheel feedback is validated on hardware.

### `/imu/data`

The bridge publishes yaw-only orientation from vendor `T=1001` field `y`. Roll and pitch fields exist in the feedback frame, but the current ROS message intentionally publishes only the yaw quaternion. The vendor IMU code exposes yaw through `IMU_ctrl.h` and `ugv_advance.h`.

### `/battery`

The bridge publishes voltage-only `sensor_msgs/BatteryState` from vendor `T=1001` field `v`. Current, charge, percentage, and chemistry are not provided by this contract.

## Validation Checklist

- Confirm actual Orange Pi serial device.
- Confirm baud rate at `115200`.
- Send stop command and verify wheels stop.
- Confirm startup sends `T=143`, `T=142`, and `T=131` before relying on streamed feedback.
- Verify `T=1` positive left/right direction at low speed.
- Verify `T=1001` feedback fields.
- Verify IMU yaw unit and battery voltage.
- Test `T=13` only after stop and low-speed `T=1` are safe.

## Known Limits

`/odom` may be command-integrated until measured wheel odometry is validated. Do not treat it as fused localization.
