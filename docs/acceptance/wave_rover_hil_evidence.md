# WAVE ROVER Hardware-In-Loop Evidence

Use this file as the evidence checklist for the first real robot run. Do not mark hardware validation complete until each item has a captured value or artifact.

## Run Metadata

- Date/time:
- Operator:
- Robot:
- Orange Pi OS:
- Serial device:
- Baudrate:
- Git branch/commit:
- Launch command:
- Smoke command:

## Vendor Sources Used

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## Required Evidence

| Check | Evidence |
| --- | --- |
| UART opens at 115200 or documented override | |
| Final stop command succeeds before and after every movement test | |
| Startup frames sent: `T=143`, `T=142`, `T=131` | |
| `T=1001` feedback received | |
| `T=1001` includes `L`, `R`, `r`, `p`, `y`, `v` | |
| Positive low-speed `T=1` forward direction verified | |
| Reverse low-speed `T=1` direction verified | |
| Positive low-speed turn direction verified | |
| `T=13` ROS mode tested only if intentionally enabled | |
| `/battery` publishes voltage-only data | |
| `/imu/data` yaw convention recorded | |
| `/odom` labeled command-integrated unless encoder validation is done | |
| Emergency stop path demonstrated | |

## Attached Artifacts

- Hardware smoke terminal output:
- ROS log path:
- Task record JSON:
- Route debug status JSON:
- Photos/video:
