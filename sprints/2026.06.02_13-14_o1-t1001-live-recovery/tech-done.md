# 2026-06-02 13-14 O1 T1001 Live Recovery

## Sprint Type

`sprint_type: micro`

## Owner

Hardware Infra Engineer

## Vendor Sources Read

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## Verified Hardware Conclusions

- `json_cmd.h` defines `CMD_BASE_FEEDBACK=130`.
- `json_cmd.h` defines `FEEDBACK_BASE_INFO=1001`.
- `uart_ctrl.h` dispatches `CMD_BASE_FEEDBACK` to `baseInfoFeedback()`.
- `ugv_advance.h` `baseInfoFeedback()` emits `T=FEEDBACK_BASE_INFO` with `L/R/r/p/y/v` fields through `Serial.println`.
- The project must still treat real `T=1001` as `not_proven`, because this sprint did not observe any serial feedback line.

## Actual Changes

- Updated `OKR.md` to record that SSH recovered, serial open and `T=130` write were observed, but `T=1001` remains `not_proven`.
- Updated `docs/hardware/o1_wave_rover_serial_feedback_probe.md` with the 13-14 remote observation, safety boundary, and next onsite checks.
- Updated `docs/interfaces/o1_o5_90_evidence_boundary.md` so the latest O1 evidence boundary reflects `serial_open_t130_no_feedback_after_request`.
- Updated `docs/process/okr_progress_log.md` with this micro sprint closeout.
- Created this sprint closeout file.

## Remote Probe Results

Remote upper readiness:

```text
host.hostname=op-z3-b6.home
host.machine=aarch64
host.python_version=3.10.12
pyserial.available=true
serial_candidates include /dev/serial/by-id/usb-STC_STC_USB_Serial-if00 and /dev/ttyACM0
safe_to_control=false
sends_commands=false
robot_control_executed=false
delivery_success=false
```

Remote read-only serial probe:

```text
port=/dev/serial/by-id/usb-STC_STC_USB_Serial-if00
realpath=/dev/ttyACM0
serial_opened=true
feedback_request.enabled=false
feedback_request.sent=false
read_line_count=0
parsed_json_count=0
observed_feedback_types=[]
t1001_feedback_status=not_requested
safe_to_control=false
sends_motion_commands=false
robot_control_executed=false
delivery_success=false
```

Remote explicit non-motion `T=130` request:

```text
serial_opened=true
feedback_request.enabled=true
feedback_request.sent=true
feedback_request.write_error=null
read_timeout_s=12.0
read_line_count=0
parsed_json_count=0
invalid_json_count=0
observed_feedback_types=[]
raw_line_preview=[]
error=null
t1001_feedback_status=not_observed_after_t130
safe_to_control=false
sends_commands=true
sends_motion_commands=false
robot_control_executed=false
delivery_success=false
```

No `T=1`, `T=13`, `T=131`, `cmd_vel`, or motion command was sent.

## Verification

```text
$ python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py onboard/scripts/o1_wave_rover_serial_feedback_probe.py
passed

$ PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py
..................
----------------------------------------------------------------------
Ran 18 tests in 0.304s

OK
```

```text
$ git diff --check -- OKR.md docs/hardware/o1_wave_rover_serial_feedback_probe.md docs/interfaces/o1_o5_90_evidence_boundary.md docs/process/okr_progress_log.md sprints/2026.06.02_13-14_o1-t1001-live-recovery/tech-done.md
passed
```

## Failure Location

Current blocker is no longer SSH or pyserial. The blocker is now:

```text
serial_open_t130_no_feedback_after_request
```

Meaning: the target serial path opens, and one explicit vendor `{"T":130}\n` write returns `write_error=null`, but the 12 second read window still receives zero serial lines and no `T=1001`.

## Remaining Risks And Next Actions

- `T=1001` is still `not_proven`; O1 percentage must not be raised.
- Confirm WAVE ROVER ESP32 power and loaded firmware.
- Confirm UART TX/RX crossing and cable integrity.
- Confirm `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00` is actually the WAVE ROVER ESP32, not LiDAR or another STC USB serial device.
- Check whether another process owns the same serial device.
- Use vendor terminal or a minimal serial terminal to manually cross-check `{"T":130}`.
- Verify the loaded firmware includes the `CMD_BASE_FEEDBACK -> baseInfoFeedback()` branch.
- Do not claim HIL pass, chassis controllability, real odometry, real IMU/battery validation, or delivery success until a real `T=1001` packet and follow-up HIL evidence packet are captured.
