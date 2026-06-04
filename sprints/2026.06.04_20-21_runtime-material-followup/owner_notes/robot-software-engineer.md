# Robot Software Engineer Owner Note

## sprint_type

sprint_type: epic

## Scope

- Role: Robot Software Engineer.
- Task: continue hourly O3/O7 runtime-material iteration through `ssh root@192.168.1.11 -p 37878`.
- Goal: try to obtain fresh non-motion `/scan`, `/map`, AMCL/TF/Nav2 lifecycle material, or identify the runtime blocker.
- Safety boundary: no `/api/base/manual`, no `/cmd_vel`, no WAVE ROVER movement command, no `T=1/T=13/T=130/T=131`, and no chassis motion.
- Allowed readback: 8787 `/health`、`/api/status`、radar/map/localize/Nav2/elevator/base status readback, plus radar/map/localize/Nav2 non-motion hooks.

## Remote Runtime Evidence

### SSH / 8787 / ROS2

Command family:

```bash
ssh root@192.168.1.11 -p 37878 'bash -s'
```

Key output:

```text
op-z3-b6.home
2026-06-04 20:17:28 CST
LISTEN 0 128 0.0.0.0:8787 0.0.0.0:* users:(("python3",pid=30042,fd=6))
/opt/ros/humble/bin/ros2
/root/rober/onboard/install/ros2_trashbot_bringup
/root/rober/onboard/install/ros2_trashbot_hardware
/root/rober/onboard/install/ros2_trashbot_nav
/root/rober/onboard/install/ros2_trashbot_behavior
/root/rober/onboard/install/ros2_trashbot_interfaces
```

Interpretation:

- SSH reachable and 8787 is live.
- ROS2 Humble and trashbot install prefixes exist after sourcing `/opt/ros/humble/setup.bash` and `/root/rober/onboard/install/setup.bash`.
- First SSH script attempt failed before runtime probing because `set -u` is incompatible with ROS setup scripts on the upper computer. Rerun used `set +u`; this was a probe-script issue, not a product runtime conclusion.

### ROS2 Graph Before And After Non-motion Hooks

Key output before hooks:

```text
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
Unknown topic '/scan'
Unknown topic '/lidar/raw_packet'
Unknown topic '/map'
Unknown topic '/amcl_pose'
Unknown topic '/tf'
Unknown topic '/tf_static'
```

Key output after hooks:

```text
POST /api/radar/start HTTP 200 command_result.mode=dry_run_stub reason=no_command_configured
POST /api/map/start HTTP 200 command_result.mode=dry_run_stub reason=no_command_configured
POST /api/localize/reset HTTP 200 command_result.mode=dry_run_stub reason=no_command_configured
POST /api/nav2/start HTTP 200 command_result.mode=dry_run_stub reason=no_command_configured

Unknown topic '/scan'
Unknown topic '/lidar/raw_packet'
Unknown topic '/map'
Unknown topic '/amcl_pose'
Unknown topic '/tf'
Unknown topic '/tf_static'
WARNING: topic [/scan] does not appear to be published yet
WARNING: topic [/map] does not appear to be published yet
WARNING: topic [/amcl_pose] does not appear to be published yet
```

Interpretation:

- The non-motion hook calls did not start ROS2 runtime because the live 8787 process has no hook commands configured.
- No fresh `/scan`、`/map`、`/amcl_pose`、TF or Nav2 lifecycle graph material was observed in this check.

### 8787 Readback

Key output:

```text
GET /health HTTP 200 status=ready safe_to_control=false robot_control_executed=false
GET /api/radar/status HTTP 200 observed_lidar_port_info.path=/dev/ttyACM0 exists=true
GET /api/radar/scan-proof/latest HTTP 200 artifact.status=loaded
GET /api/radar/raw-packet-proof/latest HTTP 404 artifact.status=missing
GET /api/map/list HTTP 200 failure_reason=map_artifact_dir_missing
GET /api/map/proof/latest HTTP 404 artifact.status=missing
GET /api/localize/proof/latest HTTP 404 artifact.status=missing
GET /api/nav2/status HTTP 200 status=not_proven
GET /api/elevator/status HTTP 200 status=not_proven
GET /api/base/status HTTP 200 safe_to_control=false robot_control_executed=false
```

8787 process readback:

```text
pid=30042
cwd=/root
ROBER env: none
/root/runtime/lidar_scan_proof_latest.json mtime=2026-06-04 19:29:44 +0800
/root/runtime/lidar_raw_packet_proof_latest.json missing
/root/runtime/map_lifecycle_latest.json missing
/root/runtime/localization_reset_latest.json missing
/root/runtime/nav2_lifecycle_latest.json missing
/root/runtime/maps missing
```

Existing scan proof compact:

```json
{
  "proof_status": "scan_and_raw_packet_observed",
  "scan_once_observed": true,
  "scan_hz_observed": null,
  "raw_packet_once_observed": true,
  "tf_observed": null,
  "all_required_observations_observed": null
}
```

Interpretation:

- `/dev/ttyACM0` LiDAR device is visible, but the latest loaded scan proof is an older artifact from `19:29:44 +0800`, not fresh material from the 20:17 probe.
- The live 8787 process cwd is `/root`, so relative `runtime/*` paths resolve under `/root/runtime`.
- No `ROBER_RADAR_*`、`ROBER_MAP_*`、`ROBER_LOCALIZE_*` or `ROBER_NAV2_*` hook environment variables are present in the live 8787 process.

## Small Readback Bug Fixed

During fresh collector probing, the deployed remote `o1_lidar_scan_proof_collector.py` misreported:

```text
ros2_command_unavailable
topic_reads_attempted=false
```

Root cause:

- The collector used `ros2 --version` as ROS2 CLI readiness check.
- ROS2 Humble target CLI does not support that flag, so the collector could falsely block before topic read even when `command -v ros2` works after setup sourcing.

Implementation:

- Updated local collector to use Humble-compatible `command -v ros2 && ros2 --help >/dev/null`.
- Updated the collector unit test to assert the new command.
- Updated LiDAR ROS2 closed-loop interface docs with this false-blocker boundary.

Fresh fixed-collector run through SSH stdin, without writing remote latest artifact:

```json
{
  "generated_at": "2026-06-04T12:28:29.616418Z",
  "ros2_available": true,
  "ros2_cli_check_ok": true,
  "topic_reads_attempted": true,
  "topic_reads_reason": "expect_existing_topics_requested_read_only_ros2_topic_observation",
  "proof_status": "blocked_or_not_observed",
  "scan_once_observed": false,
  "scan_hz_observed": false,
  "raw_packet_once_observed": false,
  "tf_observed": false,
  "all_required_observations_observed": false,
  "blockers": [
    {
      "code": "upper_api_scan_not_proven",
      "detail": "8787 radar scan_status='not_proven'"
    }
  ],
  "safe_to_control": false,
  "sends_motion_commands": false,
  "robot_control_executed": false
}
```

## Changed Files

- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - Replaced the Humble-incompatible `ros2 --version` readiness check with `command -v ros2 && ros2 --help >/dev/null`.
  - Kept collector in read-only topic mode; no driver start, no serial open, no `/cmd_vel`, no base API call.
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
  - Updated the expected CLI readiness command.
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - Documented the Humble CLI readiness caveat and the unchanged no-motion boundary.
- `sprints/2026.06.04_20-21_runtime-material-followup/owner_notes/robot-software-engineer.md`
  - Recorded this runtime probe, blocker, fix, and verification evidence.

## Verification

Remote non-motion SSH / ROS2 / 8787 checks:

```text
Result: completed after rerun with set +u.
SSH reachable, 8787 live, ROS2 packages installed.
No fresh /scan, /map, /amcl_pose, TF, or Nav2 lifecycle observed.
radar/map/localize/nav2 hooks returned dry_run_stub / no_command_configured.
No forbidden base manual, cmd_vel, or chassis movement command was issued.
```

Local tests after code change:

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

```text
Ran 26 tests in 1.773s
OK (skipped=1)
```

```bash
python3 -m unittest onboard.scripts.test_o1_lidar_scan_proof_collector
```

```text
Ran 5 tests in 0.603s
OK
```

```bash
python3 -m compileall -q onboard/scripts
```

```text
passed with no output
```

```bash
git diff --check -- onboard/scripts docs/interfaces sprints/2026.06.04_20-21_runtime-material-followup
```

```text
passed with no output
```

## Failure Location

Primary blocker:

- Live upper 8787 has no configured non-motion ROS2 hook commands, so `/api/radar/start`、`/api/map/start`、`/api/localize/reset` and `/api/nav2/start` remain software guards only.

Secondary blocker:

- No ROS2 application nodes are running during this check. The graph only exposes `/parameter_events` and `/rosout`.

Resolved local readback bug:

- `o1_lidar_scan_proof_collector.py` no longer uses `ros2 --version`, avoiding a Humble false blocker.

## Remaining Risk / Not Proven

- Not proven: fresh `/scan` once/hz, `/lidar/raw_packet` once, `/map`, map artifact, AMCL pose, `/initialpose` reset, TF freshness, Nav2 lifecycle, Nav2 consuming scan+map, field HIL, chassis ACK, `T=1001`, or delivery success.
- The fixed collector was run remotely via SSH stdin for proof, but the live upper filesystem still needs code sync/deploy before `/root/rober/onboard/scripts/o1_lidar_scan_proof_collector.py` itself has the fix.
- Existing `/root/runtime/lidar_scan_proof_latest.json` is older readback material and should not be used as fresh 20:17 runtime evidence.
- Product / OKR Owner should classify this Robot Software slice as `blocked_with_root_cause` with supporting runtime reachability material, not as O3/O7 completion progress.

## Coordination Needed

- Product / OKR Owner: yes, to decide whether this blocker changes O3/O7 scoring or next hourly priority.
- Hardware Infra Engineer: yes, if the next step starts LiDAR-only smoke, because `/dev/ttyACM0` and LiDAR start/stop bytes remain hardware-facing.
- Robot Algorithm Engineer: yes after fresh `/scan` and `/map` exist, to validate map quality, AMCL/TF, and Nav2 consumption.
- Full-Stack Engineer: yes if PC direct-upper should surface `no_command_configured` and stale-artifact age more prominently.
