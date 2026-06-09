# Software Bringup Report

## Scope

- Sprint: `sprints/2026.06.09_23-00_board-live-full-stack-evidence/`
- Role: `robot-software-engineer`
- Target: `ssh root@192.168.1.11 -p 37878`
- Run time: 2026-06-09 23:10 CST
- Boundary: no product code changes, no launch default changes, no `/cmd_vel` publish, no direct motion command.

## Sources Read

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/pre_start.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/prd.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/tech-plan.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/hardware_report.md`
- `sprints/2026.06.09_23-00_board-live-full-stack-evidence/artifacts/algorithm_report.md`
- `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`

Hardware facts use the vendor entry point `docs/vendor/VENDOR_INDEX.md`: WAVE ROVER upper/lower controller link is UART newline-delimited UTF-8 JSON, vendor Raspberry Pi defaults are not Orange Pi defaults, and target serial device must be confirmed on the robot. This run used the hardware agent's proven `/dev/ttyS5 @ 115200` only as an explicit launch argument; no default was changed.

## Launch Argument Discovery

Command:

```bash
ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -p 37878 root@192.168.1.11 'bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args; ros2 launch ros2_trashbot_bringup learn.launch.py --show-args"'
```

Key remote arguments:

- `bringup.launch.py`
  - `serial_port`, default `/dev/ttyUSB0`
  - `serial_baudrate`, default `115200`
  - `command_mode`, default `speed`
  - `lidar_enabled`, default `false`
  - `lidar_serial_port`, default `/dev/ttyACM0`
  - `lidar_serial_baudrate`, default `150000`
  - `lidar_scan_topic`, default `/scan`
- `learn.launch.py`
  - `route_recorder`, default `false`
  - `route_output_dir`, default `$HOME/.ros/trashbot_runs/run_001`
  - `route_camera_topic`, default `/camera/image_raw`
  - `route_odom_topic`, default `/odom`
  - `lidar_enabled`, default `false`
  - `no_motion_static_odom_tf`, default `false`
  - `map_dir`, default `$HOME/.ros/trashbot_maps`

The remote installed launch files expose LiDAR parameters that are newer than the local source snapshot read in `onboard/src/ros2_trashbot_bringup/launch/`.

## Short Bringup Session

Command summary:

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py serial_port:=/dev/ttyS5 serial_baudrate:=115200 lidar_enabled:=true
```

The command ran only long enough to observe ROS graph and one-shot topic samples, then was interrupted. No motion command was sent.

Observed nodes during the session:

- `/base_link_to_laser_frame`
- `/esp32_bridge`
- `/lidar_driver`
- `/map_recorder`

Observed topics during the session:

- `/scan [sensor_msgs/msg/LaserScan]`
- `/odom [nav_msgs/msg/Odometry]`
- `/battery [sensor_msgs/msg/BatteryState]`
- `/imu/data [sensor_msgs/msg/Imu]`
- `/cmd_vel [geometry_msgs/msg/Twist]`
- `/map [nav_msgs/msg/OccupancyGrid]`
- `/tf_static [tf2_msgs/msg/TFMessage]`
- `/parameter_events [rcl_interfaces/msg/ParameterEvent]`
- `/rosout [rcl_interfaces/msg/Log]`

One-shot evidence:

- `/scan`: published by `lidar_driver`, frame `laser_frame`, sample ranges included `5.479`, `1.402`, `1.392`, `1.370` meters.
- `/odom`: published by `esp32_bridge`, frame `odom`, child `base_link`, zero pose/twist while no motion was commanded.
- `/cmd_vel`: one subscriber from `esp32_bridge`; publisher count was zero.
- `/battery` and `/imu/data`: publishers from `esp32_bridge` were registered.
- `/camera/image_raw`: unknown topic.
- `/tf`: not published; only `/tf_static` was present.

## Failure / Blocker Details

- `waypoint_manager` died because `nav2_simple_commander` is missing on the board:

```text
ModuleNotFoundError: No module named 'nav2_simple_commander'
```

- `task_orchestrator` died because `elevator_assist_target_floor` was passed as an integer while the node declares it as a string:

```text
rclpy.exceptions.InvalidParameterTypeException: Trying to set parameter 'elevator_assist_target_floor' to '1' of type 'INTEGER', expecting type 'STRING'
```

- `esp32_bridge` connected successfully:

```text
Connected to WAVE ROVER ESP32 on /dev/ttyS5 @ 115200
ESP32Bridge ready: vendor WAVE ROVER UART protocol is one UTF-8 JSON object per newline; command_mode=speed; odom source=ROS-side command integration until measured wheel odometry is validated
```

- `lidar_driver` connected successfully:

```text
LiDAR serial started: /dev/ttyACM0 @ 150000
```

- The launch cleanup command left a stale `/base_link_to_laser_frame` graph entry briefly, but a process check found no matching `esp32_bridge`, `lidar_driver`, `static_transform_publisher`, `map_recorder`, or `ros2 launch ros2_trashbot_bringup` process after cleanup.

## Pulled Evidence

Pulled to local:

- `artifacts/pulled_remote_run/field_full_stack_20260609_230304/`
  - `route_bag/metadata.yaml`
  - `route_bag/route_bag_0.db3`
  - `record_mode.txt`
  - `record_topics.txt`
  - `rosbag_rc.txt`
  - `topic_list.txt`
  - `topic_list_typed.txt`
- `artifacts/pulled_remote_run/software_bringup_20260609_230745/`
  - `bringup.log`
  - `nodes.txt`
  - `topics.txt`
  - `topic_info.txt`
  - `topic_echo_once.txt`

The graph-only rosbag contains `/rosout` and `/parameter_events` only, `message_count: 7`, and remains useful as runtime evidence only. It is not route, SLAM, or sensor bag evidence.

## Preflight / Manifest

Generated:

- `artifacts/preflight_ssh.json`
  - `schema=trashbot.board_field_evidence_preflight.v1`
  - `status=blocked_ros2_cli_missing`
  - Reason: the script checks `command -v ros2` without sourcing remote setup. Manual `bash -lc "source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 ..."` works.
- `artifacts/field_evidence_manifest.json`
  - `schema=trashbot.field_evidence_manifest.v1`
  - `status=blocked_artifacts_missing`
  - `gate_pass=false`
  - `safe_to_control=false`
  - `delivery_success=false`
  - `primary_actions_enabled=false`
  - Present required artifact: `rosbag`
  - Missing required artifacts: `map_yaml`, `route_csv`, `keyframes`, `replay_jsonl`

## Gate Status

| Gate | Status | Evidence |
| --- | --- | --- |
| 雷达 | partial pass | `/scan` published by `lidar_driver`; one-shot LaserScan sample captured. |
| 摄像头 | blocked | `/camera/image_raw` unknown; no ROS camera driver/topic in bringup evidence. |
| 建图 | blocked | `/map` topic exists from `map_recorder`, but no `map.yaml`, route, SLAM output, or valid map artifact. |
| 运动 | blocked by policy | `/cmd_vel` has an `esp32_bridge` subscriber and `/odom` is observable, but no operator safety gate or HIL clearance; no motion command sent. |

## Next Minimal Action

1. Fix board runtime dependencies/configuration before full bringup: install/source `nav2_simple_commander` dependency and fix `elevator_assist_target_floor` parameter typing.
2. Add or start the camera ROS driver so `/camera/image_raw` exists.
3. Rerun short bringup and record `/scan /odom /tf_static /camera/image_raw /map` before attempting route/keyframe capture.
4. Only after explicit safety gate, use `/cmd_vel` low-speed smoke and observe `/odom` before/after plus stop.
