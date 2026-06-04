# Robot Software Engineer Owner Note

## sprint_type

sprint_type: epic

## Scope

- Role: Robot Software Engineer.
- Task: use `ssh root@192.168.1.11 -p 37878` for non-motion ROS2 / 8787 runtime checks and material collection.
- Evidence focus: O3/O7 upper-computer runtime material for 8787, ROS2 Humble, LiDAR `/scan`, map/localize/Nav2 lifecycle entrypoints.
- Safety boundary: no `/api/base/manual`, no `/api/base/stop`, no `/cmd_vel`, no WAVE ROVER `T=1/T=13/T=130/T=131`, no chassis motion command, no hardware parameter change.
- Vendor entrypoint read: `docs/vendor/VENDOR_INDEX.md`. No hardware integration code or serial parameters were changed.

## Actions Taken

1. Read project and sprint context:
   - `AGENTS.md`
   - `OKR.md`
   - `docs/vendor/VENDOR_INDEX.md`
   - `sprints/2026.06.04_17-18_runtime-material-epic/pre_start.md`
   - `sprints/2026.06.04_17-18_runtime-material-epic/prd.md`
   - `sprints/2026.06.04_17-18_runtime-material-epic/tech-plan.md`
2. Ran SSH upper-computer reachability check with non-interactive timeout guards.
3. Queried 8787 read-only endpoints using Python `urllib.request` because remote `curl` is not installed.
4. Queried ROS2 graph, selected topics, selected services, lifecycle nodes, package prefixes, and launch argument parsing after sourcing ROS2 and workspace setup.
5. Did not edit runtime code or configuration. This owner note is the only file changed by Robot Software in this task.

## Command Evidence

### SSH / 8787 / ROS2 Command Presence

Command:

```bash
timeout 25s ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=5 -o ServerAliveCountMax=1 -o StrictHostKeyChecking=accept-new root@192.168.1.11 -p 37878 'hostname; date; ss -ltnp | grep -E ":8787|:5173" || true; command -v ros2 || true'
```

Key output:

```text
op-z3-b6.home
Thu Jun  4 05:18:13 PM CST 2026
LISTEN 0 128 0.0.0.0:8787 0.0.0.0:* users:(("python3",pid=24105,fd=6))
```

Interpretation:

- SSH reachable.
- 8787 reachable/listening.
- `command -v ros2` in the non-login shell printed nothing, but ROS2 exists after sourcing `/opt/ros/humble/setup.bash`; see next section.

### ROS2 Environment / Graph

Command:

```bash
ssh root@192.168.1.11 -p 37878 'bash -lc '"'"'source /opt/ros/humble/setup.bash 2>/dev/null || true; source /root/rober/onboard/install/setup.bash 2>/dev/null || true; command -v ros2; ros2 node list; ros2 topic list -t; for t in /scan /lidar/raw_packet /map /amcl_pose /tf /tf_static /parameter_events /rosout; do ros2 topic info "$t"; done; ros2 service list -t | grep -E "map|slam|amcl|lifecycle|trashbot|save_map|localize|nav" || true; ros2 lifecycle nodes'"'"''
```

Key output:

```text
/opt/ros/humble/bin/ros2
/root/rober/onboard/install/setup.bash exists
ros2_trashbot_bringup /root/rober/onboard/install/ros2_trashbot_bringup
ros2_trashbot_hardware /root/rober/onboard/install/ros2_trashbot_hardware
ros2_trashbot_nav /root/rober/onboard/install/ros2_trashbot_nav
ros2_trashbot_behavior /root/rober/onboard/install/ros2_trashbot_behavior
ros2_trashbot_interfaces /root/rober/onboard/install/ros2_trashbot_interfaces

==nodes==

==topics==
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]

/scan Unknown topic '/scan'
/lidar/raw_packet Unknown topic '/lidar/raw_packet'
/map Unknown topic '/map'
/amcl_pose Unknown topic '/amcl_pose'
/tf Unknown topic '/tf'
/tf_static Unknown topic '/tf_static'
```

Interpretation:

- ROS2 Humble and the trashbot workspace are installed on the upper computer.
- No application ROS2 nodes are currently running.
- `/scan`, `/lidar/raw_packet`, `/map`, `/amcl_pose`, `/tf`, `/tf_static`, map/localize/Nav2 services, and lifecycle nodes are not present in the current graph.

### 8787 Read-Only Endpoints

Remote `curl` failure:

```text
zsh:1: command not found: curl
```

Fallback used:

```bash
python3 - <<'PY'
import json
import urllib.request

for path in [
    "/health",
    "/api/radar/status",
    "/api/radar/scan-proof/latest",
    "/api/radar/raw-packet-proof/latest",
    "/api/map/list",
    "/api/map/proof/latest",
    "/api/localize/proof/latest",
    "/api/nav2/status",
    "/api/elevator/status",
    "/api/base/status",
]:
    with urllib.request.urlopen(f"http://127.0.0.1:8787{path}", timeout=5) as resp:
        print(path, resp.status)
        print(resp.read(4000).decode("utf-8", "replace"))
PY
```

Key output:

```text
/health HTTP 200 status=ready safe_to_control=false robot_control_executed=false
/api/radar/status HTTP 200 observed_lidar_port=/dev/ttyACM0 scan_status=not_proven
/api/radar/status controls.start.mode=dry_run_stub controls.stop.mode=dry_run_stub
/api/radar/scan-proof/latest HTTP 200 latest proof status=blocked_or_not_observed
/api/radar/raw-packet-proof/latest HTTP 200 latest proof status=raw_packets_parsed, but freshness status=stale
/api/map/list HTTP 200 artifact_dir_exists=false map_count=0 failure_reason=map_artifact_dir_missing
/api/map/proof/latest HTTP 404 latest runtime artifact is missing
/api/localize/proof/latest HTTP 404 latest runtime artifact is missing
/api/nav2/status HTTP 200 status=not_proven commands.start.mode=dry_run_stub commands.stop.mode=dry_run_stub
/api/elevator/status HTTP 200 status=not_proven latest runtime artifact is missing
/api/base/status HTTP 200 port=/dev/ttyS5 write_control_available=true safe_to_control=false
```

Interpretation:

- 8787 is live and reports safe fail-closed fields correctly.
- LiDAR device `/dev/ttyACM0` is present and a stale raw-packet artifact is readable, but fresh ROS2 `/scan` is not connected.
- Map/localize/Nav2/elevator runtime artifact files are missing.
- 8787 radar/map/localize/Nav2 command hooks are dry-run stubs because `ROBER_RADAR_START_COMMAND`, `ROBER_MAP_*_COMMAND`, `ROBER_LOCALIZE_RESET_COMMAND`, and `ROBER_NAV2_*_COMMAND` are not configured in the running upper API process.

### Launch Entrypoint Parsing

Command:

```bash
ssh root@192.168.1.11 -p 37878 'bash -lc '"'"'source /opt/ros/humble/setup.bash; source /root/rober/onboard/install/setup.bash; ros2 launch ros2_trashbot_bringup learn.launch.py --show-args; ros2 launch ros2_trashbot_bringup autonomous.launch.py --show-args'"'"''
```

Key output:

```text
learn.launch.py exposes lidar_enabled default false, lidar_serial_port default /dev/ttyACM0, lidar_scan_topic default /scan, lidar_raw_packet_topic default /lidar/raw_packet.
autonomous.launch.py exposes map_file, waypoint_file, operator_pose_topic default /amcl_pose, serial_port default /dev/ttyUSB0, delivery_mode default dry_run, elevator_assist_enabled default true, elevator_assist_mode default dry_run.
```

Interpretation:

- Launch files are installed and parseable.
- This command did not start nodes, did not open serial devices, and did not publish control topics.

## Root Cause / Blocker

Primary evidence type: `blocked_with_root_cause`.

Supporting evidence type: `robot_runtime_material` for SSH reachability, 8787 liveness, ROS2 Humble installation, trashbot package prefixes, and launch entrypoint parsing.

Root cause:

- The upper computer is reachable and ROS2 packages are installed, but no ROS2 runtime nodes are currently running.
- 8787 is running, but its radar/map/localize/Nav2 start hooks are configured as dry-run stubs, so 8787 cannot currently start LiDAR, SLAM, AMCL, or Nav2 runtime by itself.
- Fresh `/scan`, `/map`, `/amcl_pose`, TF, map artifact, localization artifact, and Nav2 lifecycle material are therefore absent.

## Not Proven

- No fresh ROS2 `/scan` material.
- No fresh `/lidar/raw_packet` ROS2 topic material.
- No `/map` topic material.
- No map YAML/PGM/PBStream artifact in `runtime/maps`.
- No `/amcl_pose`, `/initialpose` reset proof, or TF freshness proof.
- No map server / AMCL / planner / controller lifecycle state.
- No Nav2 consumption of `/scan` + map.
- No PC/browser operator workflow proof from this Robot Software note.
- No HIL, no chassis motion, no `safe_to_control=true`, no delivery success.

## Next Robot Software Recommendation

To convert this from blocked material to `robot_runtime_material`, configure or run a supervised non-motion runtime session on the upper computer:

1. Start LiDAR/learn runtime without base motion, for example via the installed `learn.launch.py` with `lidar_enabled:=true`, verified LiDAR port, and raw packet publishing as needed.
2. Capture fresh `ros2 topic echo --once /scan`, `ros2 topic hz /scan`, `/lidar/raw_packet` once, `/tf_static`, and 8787 `/api/radar/scan-proof/latest`.
3. Configure explicit 8787 non-motion command hooks for radar/map/localize/Nav2 only after deciding the process supervisor path; keep base UART and `/cmd_vel` outside these hooks.
4. For map/localize/Nav2, start with SLAM `/map` and map artifact creation before AMCL/Nav2, because Nav2 cannot prove consumption without a map and localization chain.

## Coordination Needed

- Product / OKR Owner: yes, to classify this note as `blocked_with_root_cause` with supporting `robot_runtime_material` and decide whether this sprint can涨分.
- Hardware Infra Engineer: yes, because LiDAR device/udev and any future driver start must keep vendor and no-motion boundaries explicit.
- Robot Algorithm Engineer: yes later, after fresh map/scan material exists, for Nav2 consumption and map quality checks.
- Full-Stack Engineer: yes, to align PC/8787 operator workflow with the same evidence ref once 8787 command hooks are configured.

## Fresh Verification Update: 2026-06-04 18:13 CST

本段为本轮 fresh verification 追加记录；没有执行任何 POST 底盘运动命令，没有调用
`/api/base/manual`、`/api/base/stop`、`/cmd_vel` 或 WAVE ROVER `T=1/T=13/T=130/T=131`。

### Fresh SSH / 8787 reachability

Command:

```bash
timeout 35s ssh -o BatchMode=yes -o ConnectTimeout=8 -o ServerAliveInterval=5 -o ServerAliveCountMax=1 -o StrictHostKeyChecking=accept-new root@192.168.1.11 -p 37878 'hostname; date; ss -ltnp | grep -E ":8787|:5173" || true; command -v ros2 || true'
```

Key output:

```text
op-z3-b6.home
Thu Jun  4 06:13:23 PM CST 2026
LISTEN 0      128          0.0.0.0:8787       0.0.0.0:*    users:(("python3",pid=24105,fd=6))
```

Interpretation:

- SSH still reachable.
- 8787 still listening.
- Non-login shell still does not expose `ros2` until ROS2/workspace setup is sourced.

### Fresh ROS2 graph / launch check

Command:

```bash
ssh root@192.168.1.11 -p 37878 'bash -s' <<'REMOTE'
source /opt/ros/humble/setup.bash 2>/dev/null || true
source /root/rober/onboard/install/setup.bash 2>/dev/null || true
command -v ros2
for p in ros2_trashbot_bringup ros2_trashbot_hardware ros2_trashbot_nav ros2_trashbot_behavior ros2_trashbot_interfaces; do ros2 pkg prefix "$p"; done
ros2 node list
ros2 topic list -t
for t in /scan /lidar/raw_packet /map /amcl_pose /tf /tf_static /parameter_events /rosout; do ros2 topic info "$t"; done
ros2 service list -t | grep -E 'map|slam|amcl|lifecycle|trashbot|save_map|localize|nav' || true
ros2 lifecycle nodes
REMOTE
```

Key output:

```text
/opt/ros/humble/bin/ros2
ros2_trashbot_bringup /root/rober/onboard/install/ros2_trashbot_bringup
ros2_trashbot_hardware /root/rober/onboard/install/ros2_trashbot_hardware
ros2_trashbot_nav /root/rober/onboard/install/ros2_trashbot_nav
ros2_trashbot_behavior /root/rober/onboard/install/ros2_trashbot_behavior
ros2_trashbot_interfaces /root/rober/onboard/install/ros2_trashbot_interfaces
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
Unknown topic '/scan'
Unknown topic '/lidar/raw_packet'
Unknown topic '/map'
Unknown topic '/amcl_pose'
Unknown topic '/tf'
Unknown topic '/tf_static'
```

`ros2 launch ros2_trashbot_bringup learn.launch.py --show-args` and
`ros2 launch ros2_trashbot_bringup autonomous.launch.py --show-args` both parsed.
Important exposed defaults remain:

- `learn.launch.py`: `lidar_enabled=false`, `lidar_serial_port=/dev/ttyACM0`,
  `lidar_scan_topic=/scan`, `lidar_raw_packet_topic=/lidar/raw_packet`.
- `autonomous.launch.py`: `operator_pose_topic=/amcl_pose`, `serial_port=/dev/ttyUSB0`,
  `delivery_mode=dry_run`, `elevator_assist_enabled=true`, `elevator_assist_mode=dry_run`.

Interpretation:

- ROS2 Humble and trashbot packages are installed on the upper computer.
- No application ROS2 nodes are running during this check.
- O3 `/scan`、`/map`、AMCL、TF、Nav2 lifecycle runtime material is still absent.
- Launch entrypoints are installed and parseable, but this command does not start runtime.

### Fresh 8787 read-only endpoint check

Command used Python `urllib.request` on the upper computer because remote `curl` is unavailable.

Key output:

```text
/health HTTP 200 status=ready safe_to_control=false robot_control_executed=false
/api/radar/status HTTP 200 observed_lidar_port=/dev/ttyACM0 scan_status=not_proven
/api/radar/scan-proof/latest HTTP 200 artifact status=loaded, latest proof still blocked/not_proven
/api/radar/raw-packet-proof/latest HTTP 200 artifact status=loaded, stale raw-packet proof remains readable
/api/map/list HTTP 200 status=not_proven failure_reason=map_artifact_dir_missing
/api/map/proof/latest HTTP 404 artifact status=missing
/api/localize/proof/latest HTTP 404 artifact status=missing
/api/nav2/status HTTP 200 status=not_proven
/api/elevator/status HTTP 200 status=not_proven
/api/operator/report HTTP 405 Method Not Allowed
```

Interpretation:

- 8787 liveness and fail-closed fields remain valid.
- `/dev/ttyACM0` LiDAR device is visible to 8787, but no fresh ROS2 `/scan` proof exists.
- Map/localize/Nav2/elevator latest runtime artifacts remain missing or `not_proven`.
- Deployed upper API still does not include local `/api/operator/report` GET/POST fix; the shared
  worktree patch in `onboard/scripts/upper_robot_api.py` is `not_deployed_to_upper_runtime`.

### Fresh local verification

Command:

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

Result:

```text
Ran 26 tests in 1.808s
OK (skipped=1)
```

Command:

```bash
python3 -m compileall onboard/scripts
```

Result:

```text
Listing 'onboard/scripts'...
```

Command:

```bash
git diff --check -- onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/interfaces/o7_upper_robot_api.md sprints/2026.06.04_17-18_runtime-material-epic/owner_notes/robot-software-engineer.md
```

Result: passed with no output.

### Updated blocker / remaining risk

- Evidence classification remains `blocked_with_root_cause` with supporting `robot_runtime_material`
  for SSH, 8787 liveness, ROS2 installation, package prefixes, and launch parseability.
- O3/O7 cannot涨分 from this Robot Software slice until a supervised non-motion runtime starts
  LiDAR/SLAM/localization/Nav2 enough to produce fresh `/scan`、`/map`、`/amcl_pose`、TF or artifact material.
- The operator-report API fix exists locally and passes unit tests, but the live upper 8787 process still
  returns HTTP 405; deployment/restart is required before Full-Stack can validate the PC同源 operator report path.
