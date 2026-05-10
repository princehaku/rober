# Fixed Route Workflow

## 1. Learning Run

Start SLAM and manual driving:

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py
```

Start SLAM/manual driving and fixed-route pose/keyframe capture in one learning launch:

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  route_recorder:=true \
  route_output_dir:=~/.ros/trashbot_runs/run_001 \
  route_id:=trash_station_route \
  route_min_distance_m:=0.8 \
  route_frame_id:=map
```

Use these launch arguments when the robot topic names differ from the defaults:

- `route_camera_topic` defaults to `/camera/image_raw`.
- `route_odom_topic` defaults to `/odom`.
- `route_output_dir` defaults to `~/.ros/trashbot_runs/run_001`.
- `route_min_distance_m` defaults to `0.8`.
- `route_frame_id` defaults to `map`.
- `route_id` defaults to blank and is copied into keyframe sample manifest context.
- `route_sample_manifest_name` defaults to `manifest.json`.
- `route_sample_manifest_max_entries` defaults to `500`.

`route_recorder` defaults to `false` so basic mapping sessions can still run without requiring a camera stream or route dataset. When enabled, it starts `ros2_trashbot_nav/route_data_recorder` under the same launch and writes route poses plus latest camera keyframes during manual driving. Each saved keyframe also writes a companion JSON sample and appends `manifest.json` using the shared `trashbot.vision_samples.v1` contract, so `/api/diagnostics` can report learned route keyframe evidence through the same vision sample summary path used for detector samples.

You can still run the recorder manually for focused route-capture debugging:

```bash
ros2 run ros2_trashbot_nav route_data_recorder \
  --ros-args \
  -p output_dir:=~/.ros/trashbot_runs/run_001 \
  -p min_distance_m:=0.8 \
  -p route_frame_id:=map \
  -p route_id:=trash_station_route
```

Expected outputs:

- `route.csv`
- `keyframes/*.jpg`
- `keyframes/*.json`
- `manifest.json`

## 2. Route Conversion

Convert a CSV route to fixed-route YAML when needed:

```bash
ros2 run ros2_trashbot_nav route_csv_to_yaml \
  --ros-args \
  -p input_csv:=~/.ros/trashbot_runs/run_001/route.csv \
  -p output_yaml:=~/.ros/trashbot_maps/fixed_route.yaml
```

CSV input can also be passed directly to `fixed_route_autonomy`.

Minimal offline YAML sample:

```yaml
waypoints:
  - frame_id: map
    x: 0.0
    y: 0.0
    z: 0.0
    qx: 0.0
    qy: 0.0
    qz: 0.0
    qw: 1.0
  - frame_id: map
    x: 1.2
    y: 0.4
    qw: 1.0
```

The fixed-route contract is `fixed_route.v1`. A valid route must contain at least one waypoint, and each waypoint must provide numeric `x`, `y`, and `qw`. Optional `z`, `qx`, `qy`, and `qz` default to `0.0`; `frame_id` defaults to `map`.

## 3. Dry-Run Verification

Run fixed-route logic without Nav2 movement:

```bash
ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:=~/.ros/trashbot_runs/run_001/route.csv \
  -p keyframe_dir:=~/.ros/trashbot_runs/run_001/keyframes \
  -p enable_visual_gate:=true \
  -p dry_run:=true
```

Launch dry-run from bringup without allowing waypoint patrol to compete for control:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  navigation_mode:=fixed_route \
  route_file:=~/.ros/trashbot_maps/fixed_route.yaml \
  keyframe_dir:=~/.ros/trashbot_maps/keyframes \
  fixed_route_dry_run:=true \
  enable_visual_gate:=false \
  route_debug_web:=true
```

Use dry-run to verify route parsing, checkpoint progression, optional keyframe gate behavior, and debug status output before hardware movement. In dry-run mode `fixed_route_autonomy` does not create `BasicNavigator`.

When `enable_visual_gate:=true`, dry-run now preflights keyframe coverage for the full route before advancing the first checkpoint. A route with missing, unreadable, or descriptorless keyframes stays in `waiting_visual_gate` and exposes the full missing/invalid checkpoint list in `keyframe_preflight`.

## 4. Debug Status

`fixed_route_autonomy` writes JSON status to `debug_status_file`. The status includes:

- state
- mode
- route contract version
- route file
- keyframe directory
- current index
- current target pose
- total checkpoints
- dry-run flag
- visual gate flag
- route proof summary
- keyframe preflight summary
- last error
- failure reason
- last transition
- last navigation result
- update timestamp

Example status JSON:

```json
{
  "state": "completed",
  "mode": "dry_run",
  "route_contract_version": "fixed_route.v1",
  "route_file": "/home/orangepi/.ros/trashbot_maps/fixed_route.yaml",
  "keyframe_dir": "/home/orangepi/.ros/trashbot_maps/keyframes",
  "current_index": 2,
  "current_target": null,
  "total": 2,
  "dry_run": true,
  "enable_visual_gate": false,
  "route_proof_summary": {
    "coverage_rate": 1.0,
    "covered_checkpoints": 2,
    "total_checkpoints": 2,
    "missing_checkpoints": [],
    "gate_status": "passed",
    "last_block_reason": ""
  },
  "keyframe_preflight": {
    "enabled": false,
    "total_checkpoints": 2,
    "loaded_keyframes": [],
    "missing_keyframes": [0, 1],
    "invalid_keyframes": [],
    "route_visual_ready": true
  },
  "last_error": "",
  "failure_reason": "",
  "last_transition": "running->completed",
  "last_nav_result": "dry_run_checkpoint_passed",
  "updated_at": 1778256000.0
}
```

`route_proof_summary` is the navigation-side source of truth for Objective 3 route proof coverage:

- `coverage_rate`: `covered_checkpoints / total_checkpoints`, rounded to 4 decimals.
- `covered_checkpoints`: checkpoints already proven by fixed-route dry-run progression.
- `total_checkpoints`: full checkpoint count from the validated fixed route.
- `missing_checkpoints`: checkpoint indexes that are not yet proven (`covered_checkpoints..total_checkpoints-1`).
- `gate_status`: current visual gate block state, or `passed` when all checkpoints are covered.
- `last_block_reason`: latest block reason copied from `failure_reason`/`last_error`; empty when fully covered.

Stability rules:

- Full coverage: `coverage_rate=1.0`, `missing_checkpoints=[]`, `gate_status=passed`.
- Partial coverage: `coverage_rate<1.0`, `missing_checkpoints` lists uncovered tail indexes.
- Partial coverage without an active gate block can still report `gate_status=passed`; readiness must be decided from `coverage_rate` + `missing_checkpoints` together.
- Missing keyframe: `gate_status=keyframe_preflight_failed` or `missing_keyframe`, with keyframe detail in `last_block_reason`.
- Visual gate not passed (camera frame/descriptors/matches): `gate_status` reflects the concrete gate status and keeps the failure detail in `last_block_reason`.

## 5. Debug Web

Start the debug page:

```bash
TRASHBOT_STATUS_FILE=/tmp/trashbot_fixed_route_status.json \
TRASHBOT_WEB_PORT=8765 \
ros2 run ros2_trashbot_nav route_debug_web
```

Or start it with autonomous launch:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  navigation_mode:=fixed_route \
  fixed_route_dry_run:=true \
  route_debug_web:=true
```

Open:

```text
http://<host-ip>:8765
```

## 6. Autonomous Run

Run the full autonomous launch with a saved map:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  map_file:=~/.ros/trashbot_maps/trashbot_map.yaml
```

Use Nav2 waypoint mode when localization and map quality are good. Use fixed-route mode when the route has been learned and keyframes are the primary guardrail for repeatable movement.

Switch from `fixed_route_dry_run:=true` to real fixed-route navigation only after all of these are true:

- The route YAML or CSV passes offline parsing and contains the expected checkpoint count.
- Dry-run reaches `state: completed` with empty `failure_reason`.
- `current_target` coordinates match the learned route and the debug web updates once per checkpoint.
- If `enable_visual_gate:=true`, each checkpoint has a corresponding keyframe and live camera frames pass the visual gate at the expected locations.
- Nav2 localization, map loading, emergency stop, low-speed base motion, and manual recovery have been verified on the robot.
- No waypoint patrol node is active at the same time; use `navigation_mode:=fixed_route` or `delivery_mode:=fixed_route`.

## 7. Delivery Action Modes

The task orchestrator defaults to safe dry-run delivery:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  delivery_mode:=dry_run \
  delivery_target:=trash_station
```

After map, localization, waypoint YAML, emergency stop, and low-speed base checks pass, enable waypoint delivery:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  map_file:=~/.ros/trashbot_maps/trashbot_map.yaml \
  waypoint_file:=~/.ros/trashbot_maps/waypoints.yaml \
  delivery_mode:=waypoint \
  delivery_target:=trash_station \
  return_target:=home
```

`delivery_target` and `return_target` are waypoint names from the YAML file. If `delivery_target` is blank, the behavior layer selects the first waypoint with `type: 2`.
