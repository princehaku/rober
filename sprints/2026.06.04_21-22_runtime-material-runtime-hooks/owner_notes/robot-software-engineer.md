# Robot Software Engineer Owner Note

## sprint_type

sprint_type: epic

## Scope

- Role: Robot Software Engineer.
- Task: add a read-only 8787 refresh hook for LiDAR/ROS2 scan proof material.
- Goal: let upper API expose `POST /api/radar/scan-proof/refresh`, refresh `runtime/lidar_scan_proof_latest.json`, and return a clear blocker summary when ROS2 topics or deployment are not ready.
- Safety boundary: no LiDAR driver start, no LiDAR serial open, no `/dev/ttyS5`, no WAVE ROVER `T=1/T=13/T=130/T=131`, no `/cmd_vel`, no `/api/base/manual`, and no chassis motion.

## Implementation

- Added `ROUTE_PATHS["radar_scan_proof_refresh"] = "/api/radar/scan-proof/refresh"`.
- Added a read-only collector runner that calls the repo-local `o1_lidar_scan_proof_collector.py` with `--once-json --expect-existing-topics --output <artifact>`.
- The refresh handler runs the collector in a worker thread so the collector can still GET local `8787` health/radar status while the POST request is active.
- Refresh response includes `command_result`, `artifact_path`, `proof_summary`, `blockers_summary`, `safe_to_control=false`, `sends_motion_commands=false`, and `robot_control_executed=false`.
- Added unit and aiohttp route coverage so the refresh endpoint is not a 404/405 drift and remains non-motion even when proof fields are observed.
- Updated O7 upper API and LiDAR closed-loop docs with the new endpoint and read-only safety boundary.

## Changed Files

- `onboard/scripts/upper_robot_api.py`
- `onboard/scripts/test_upper_robot_api.py`
- `docs/interfaces/o7_upper_robot_api.md`
- `docs/interfaces/lidar_ros2_closed_loop.md`
- `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/robot-software-engineer.md`

## Verification

Local contract verification passed:

```bash
python3 -m unittest onboard.scripts.test_upper_robot_api
```

```text
Ran 28 tests in 1.761s
OK (skipped=2)
```

```bash
python3 -m compileall -q onboard/scripts
```

```text
passed with no output
```

```bash
git diff --check -- \
  onboard/scripts/upper_robot_api.py \
  onboard/scripts/test_upper_robot_api.py \
  docs/interfaces/o7_upper_robot_api.md \
  docs/interfaces/lidar_ros2_closed_loop.md \
  sprints/2026.06.04_21-22_runtime-material-runtime-hooks/owner_notes/robot-software-engineer.md
```

```text
passed with no output
```

## SSH Runtime Check

Read-only SSH command family:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 root@192.168.1.11 -p 37878 '<python urllib GET /health and /api/radar/status>'
```

Key output:

```text
GET /health -> HTTP 200, status=ready, safe_to_control=false, robot_control_executed=false
GET /api/radar/status -> HTTP 200, schema=trashbot.upper_robot_api.v1.radar_status
GET /api/radar/status -> scan_status=not_proven
GET /api/radar/status -> observed_lidar_port=/dev/ttyACM0, observed_lidar_exists=true
GET /api/radar/status -> scan_proof_latest_status=loaded
GET /api/radar/status -> controls_keys=["start", "stop"]
GET /api/radar/status -> has_scan_proof_refresh_control=false
```

Interpretation:

- Live 8787 is reachable and still fail-closed.
- Live 8787 does not expose the new `scan_proof_refresh` control yet.
- Because the current task forbids killing/restarting unknown processes, `POST /api/radar/scan-proof/refresh` was not attempted.
- The live runtime remains on the previous deployed API version until the file is synced and the known service reload path is confirmed.

## Failure Location

Deployment blocker:

- Local implementation and tests are complete, but live 8787 has not loaded the new route.
- The observed live route set under `/api/radar/status.controls` is only `start/stop`, so `POST /api/radar/scan-proof/refresh` would currently be a route/version mismatch rather than a real proof refresh.
- No restart was attempted because the running process reload path was not verified in this task, and killing an unknown 8787 process could disrupt existing runtime evidence collection.

## Remaining Risk / Not Proven

- Not proven: fresh `/scan` once/hz through 8787 refresh, `/lidar/raw_packet` once, TF, SLAM `/map`, AMCL, Nav2 lifecycle, safe control, HIL, or delivery success.
- Local unit tests prove the software contract only; the upper computer still needs exact file sync to `/root/rober/onboard/scripts/upper_robot_api.py` and a known-safe 8787 service reload.
- Existing live `runtime/lidar_scan_proof_latest.json` remains readback material only; this sprint did not refresh it on the upper computer.
