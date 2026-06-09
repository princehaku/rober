# Hardware Gate Report

## Scope

- Sprint: `sprints/2026.06.09_23-00_board-live-full-stack-evidence/`
- Role: `robot-hardware-engineer`
- Target: `ssh root@192.168.1.11 -p 37878`
- Run time: 2026-06-09 23:00 CST
- Boundary: no hardware configuration changes, no launch parameter changes, no motion command sent.

## Vendor Sources Read

- `docs/vendor/VENDOR_INDEX.md`
  - Source-of-truth order: local `docs/vendor/` first.
  - WAVE ROVER upper/lower controller link: UART, newline-delimited JSON.
  - Vendor Raspberry Pi default UART examples are not Orange Pi defaults and must be confirmed on target.
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
  - Serial JSON frames are written as `json.dumps(data) + "\n"` encoded as UTF-8.
  - Vendor Raspberry Pi example uses `/dev/ttyAMA0` at `115200`; alternate comment references `/dev/serial0`.
  - Vendor helper probes `/dev/ttyUSB*` for extra sensor and `/dev/ttyACM*` for lidar.
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
  - `cmd_movition_ctrl: 1`, `cmd_pwm_ctrl: 11`, `cmd_gimbal_ctrl: 133`.
  - `max_speed: 1.3`, `slow_speed: 0.2`, `feedback_interval: 0.001`.
  - Feedback key map includes `base_voltage: 112`.
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
  - `FEEDBACK_BASE_INFO = 1001`, `FEEDBACK_IMU_DATA = 1002`.
  - `CMD_SPEED_CTRL = 1`, `CMD_ROS_CTRL = 13`, `CMD_BASE_FEEDBACK = 130`, `CMD_BASE_FEEDBACK_FLOW = 131`, `CMD_FEEDBACK_FLOW_INTERVAL = 142`, `CMD_UART_ECHO_MODE = 143`.
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
  - `T=1` dispatches to `setGoalSpeed(L, R)`.
  - `T=13` dispatches to `rosCtrl(X, Z)`.
  - `T=130` dispatches to `baseInfoFeedback()`.
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
  - `setGoalSpeed()` accepts wheel speed style input and for non-encoder `mainType != 3` converts to PWM by `input * 512 * speed_rate`.
  - Encoder speed variables exist for encoder-capable mode.

## Verified Hardware Runtime Facts

- SSH target is reachable.
  - `hostname`: `op-z3-b6.home`
  - `date`: `Tue Jun  9 10:58:42 PM CST 2026`
  - `uname`: `Linux op-z3-b6.home 6.1.31-sun50iw9 #1.0.4 SMP Thu Jul 11 16:37:41 CST 2024 aarch64`
- Devices observed:
  - `/dev/ttyACM0`: USB CDC ACM, by-id `usb-STC_STC_USB_Serial-if00`, consistent with observed lidar candidate in API evidence.
  - `/dev/ttyS2`: `dw-apb-uart`, alias `serial2`.
  - `/dev/ttyS5`: `dw-apb-uart`, alias `serial5`.
  - `/dev/video0`, `/dev/video1`, `/dev/video2`: present.
- ROS2 runtime:
  - `ros2` is installed at `/opt/ros/humble/bin/ros2` when sourced through remote `bash -lc`.
  - Installed project packages include `ros2_trashbot_behavior`, `ros2_trashbot_bringup`, `ros2_trashbot_hardware`, `ros2_trashbot_interfaces`, `ros2_trashbot_nav`, `ros2_trashbot_vision`.
  - Current ROS graph only exposed `/parameter_events` and `/rosout`.
  - `ros2 topic info -v` reported unknown topics for `/cmd_vel`, `/battery`, `/odom`, `/imu/data`, `/scan`, `/camera/image_raw`, and `/tf`.
  - `timeout 5s ros2 topic echo /battery --once` and `/odom --once` both failed because the topics were not published.
- Running non-ROS robot services:
  - `python3 /root/rober/onboard/scripts/local_webrtc_camera_smoke.py --host 0.0.0.0 --port 8088 ...`
  - `python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
- `upper_robot_api` read-only status:
  - API root reports `safe_to_control=false`, `delivery_success=false`, `primary_actions_enabled=false`, `robot_control_executed=false`.
  - `/api/base/status` reports configured base port `/dev/ttyS5`, baudrate `115200`, `pyserial_available=true`, `write_control_available=true`, but still `safe_to_control=false`.
  - `/api/base/feedback-samples` POST sent only vendor read-only `T=130` feedback requests.
  - Fresh feedback sampling observed vendor `T=1001` in `3/3` samples on `/dev/ttyS5 @ 115200`.
  - Feedback response explicitly reports `blocked_commands_not_sent=["T=1","T=13","T=131","cmd_vel","/api/base/manual"]`, `sends_motion_commands=false`, `robot_control_executed=false`, `hil_pass=false`.

## Motion Smoke Gate

Decision: blocked, not executed.

Reasons:

- ROS2 `/cmd_vel` topic is unknown and no ROS2 hardware bridge node is active.
- `/odom` and `/battery` are not published, so there is no ROS-side before/after observation path.
- Available base feedback was gathered through `upper_robot_api` by read-only `T=130`; this proves vendor feedback reachability on `/dev/ttyS5`, not ROS2 robot ACK or safe motion control.
- Existing API policy keeps `safe_to_control=false` and `primary_actions_enabled=false`.
- The task explicitly requested motion through ROS2 `/cmd_vel` and forbade direct vendor JSON control except read-only feedback probing.

No `/cmd_vel` was published. No `/api/base/manual` was called. No direct `T=1` or `T=13` command was sent. No stop command was required because no motion command was executed.

## Remaining Risks

- Current proof is not HIL pass: no wheel direction check, no low-speed movement, no observed stop, no `/odom` before/after delta, and no `/battery` ROS topic.
- `/dev/ttyS5 @ 115200` is evidenced by running API configuration and fresh `T=1001` read-only feedback, but not yet wired into the ROS2 `esp32_bridge` runtime.
- ROS2 bringup is not active on the board, so hardware topics and motion smoke remain blocked until a controlled ROS2 hardware bridge session is started with operator clearance.
- Camera and lidar devices/API evidence exist, but this hardware report did not execute the algorithm lane's sensor capture or rosbag workflow.
