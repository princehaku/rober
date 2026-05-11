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

Use these launch arguments when the robot topic names differ from defaults:

- `route_camera_topic` defaults to `/camera/image_raw`.
- `route_odom_topic` defaults to `/odom`.
- `route_output_dir` defaults to `~/.ros/trashbot_runs/run_001`.
- `route_min_distance_m` defaults to `0.8`.
- `route_id` defaults to blank and is copied into keyframe sample manifest context.
- `route_sample_manifest_name` defaults to `manifest.json`.
- `route_sample_manifest_max_entries` defaults to `500`.

`route_recorder` defaults to `false` so basic mapping sessions can still run without requiring a camera stream or route dataset. When enabled, it starts `ros2_trashbot_nav/route_data_recorder` under the same launch and writes route poses plus latest camera keyframes during manual driving. Each saved keyframe also writes a companion JSON sample and appends `manifest.json` using `trashbot.vision_samples.v1` contract, so `/api/diagnostics` can report learned route keyframe evidence through the same vision sample summary path used for detector samples.

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

When `enable_visual_gate:=true`, dry-run preflights keyframe coverage for the full route before first checkpoint. A route with missing/unreadable/descriptorless keyframes stays in `waiting_visual_gate` and exposes missing/invalid checkpoint lists in `keyframe_preflight`.

## 4. Debug Status Contract (O3 目标面)

`fixed_route_autonomy` writes JSON status to `debug_status_file`:

- `state`
- `mode`
- `route_contract_version`
- `route_file`
- `route_file_basename`
- `route_id`
- `route_progress`
- `checkpoint`
- `current_index`
- `target`
- `current_target`
- `checkpoint_id`
- `evidence_ref`
- `source`
- `total`
- `dry_run`
- `enable_visual_gate`
- `navigation_timeout_sec`
- `navigation_elapsed_sec`
- `keyframe_preflight`
- `visual_gate_status`
- `visual_gate_detail`
- `visual_gate_checkpoint`
- `route_proof_summary`
- `failure_reason`
- `failure_code`
- `last_error`
- `last_transition`
- `last_nav_result`
- `updated_at`
- `elevator_assist`

`route_progress` 是本轮新增用于 task_record 对齐的最小主键对象，包含：

- `route_id`: 路线标识（默认取 `route_file` basename stem）
- `route_file_basename`
- `checkpoint_id`: `route_id:NNN` 格式
- `evidence_ref`: status 文件路径
- `checkpoint`: 当前索引
- `total_checkpoints`: 路线总 checkpoint
- `route_contract_version`
- `source`
- `failure_code`: 与顶层 `failure_code` 一致，用于复盘回放

示例状态片段：

```json
{
  "state": "running",
  "route_contract_version": "fixed_route.v1",
  "route_file": "/home/orangepi/.ros/trashbot_maps/fixed_route.yaml",
  "route_file_basename": "fixed_route.yaml",
  "route_id": "fixed_route",
  "checkpoint": 1,
  "current_index": 1,
  "checkpoint_id": "fixed_route:001",
  "target": null,
  "current_target": null,
  "total": 2,
  "evidence_ref": "/tmp/trashbot_fixed_route_status.json",
  "route_progress": {
    "route_id": "fixed_route",
    "route_file_basename": "fixed_route.yaml",
    "checkpoint_id": "fixed_route:001",
    "evidence_ref": "/tmp/trashbot_fixed_route_status.json",
    "checkpoint": 1,
    "total_checkpoints": 2,
    "route_contract_version": "fixed_route.v1",
    "source": "fixed_route",
    "failure_code": ""
  },
  "navigation_timeout_sec": 0.0,
  "navigation_elapsed_sec": 0.24,
  "failure_code": "",
  "last_nav_result": "succeeded"
}
```

Failure code update (O3):

- `NO_ROUTE`: route file missing, unreadable, or invalid/empty.
- `CHECKPOINT_MISSING`: keyframe assets missing or checkpoint mapping incomplete.
- `NAVIGATION_TIMEOUT`: route status loop超过 `navigation_timeout_sec`。
- `NAVIGATION_INTERRUPTED`: Nav2 返回取消/终止。
- `NAVIGATION_ABORT`: 其它导航失败。

`route_proof_summary` 仍作为覆盖率与门控依据：

- `coverage_rate`
- `covered_checkpoints`
- `total_checkpoints`
- `missing_checkpoints`
- `gate_status`
- `last_block_reason`

`waiting_visual_gate` 属于 keyframe 或视觉门控未完成状态；`failure_code` 可能为空。

## 5. 关键缺失与超时复现脚本（离线）

### 5.1 固定路线关键点缺失

```bash
cat >/tmp/missing_keyframe_route.yaml <<'YAML'
waypoints:
  - frame_id: map
    x: 1.0
    y: 2.0
    qw: 1.0
YAML

ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:=/tmp/missing_keyframe_route.yaml \
  -p keyframe_dir:=/tmp/does_not_exist \
  -p enable_visual_gate:=true \
  -p debug_status_file:=/tmp/trashbot_fixed_route_status.json \
  -p dry_run:=true
jq '.state,.failure_code,.failure_reason,.keyframe_preflight,.route_progress' /tmp/trashbot_fixed_route_status.json
```

预期：

- `state` 为 `waiting_visual_gate`
- `failure_code` 为 `CHECKPOINT_MISSING`
- `failure_reason` 包含 `missing keyframes`
- `route_progress.checkpoint_id` 为 `route_id:000`
- `route_progress.evidence_ref` 仍是 status 文件路径

### 5.2 导航中断/超时（离线复现框架）

本地可通过伪造 `BasicNavigator` 让 `isTaskComplete()` 长期返回 `False`，并设置 `navigation_timeout_sec` 为 0.2s，确认状态进入 timeout 分支，写入：

- `failure_code` 为 `NAVIGATION_TIMEOUT`
- `navigation_elapsed_sec` > 0
- `state=error`
- `route_progress.evidence_ref` 一致

可复现点在以下文件里：

- `src/ros2_trashbot_nav/ros2_trashbot_nav/fixed_route_autonomy.py`
  - `_poll_nav_result`
  - `_set_navigation_error`
  - `_write_debug_status`

## 6. Debug Web

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

## 7. Autonomous Run

Run the full autonomous launch with a saved map:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  map_file:=~/.ros/trashbot_maps/trashbot_map.yaml
```

Use Nav2 waypoint mode when localization and map quality are good. Use fixed-route mode when the route has been learned and keyframes are the primary guardrail for repeatable movement.

Switch from `fixed_route_dry_run:=true` to real fixed-route navigation only after all of these are true:

- The route YAML or CSV passes offline parsing and contains the expected checkpoint count.
- Dry-run reaches `state: completed` with empty `failure_reason`.
- `checkpoint/current_index/target` 与任务复盘 `evidence` 的 `current_index/target/evidence_ref` 可对齐。
- `route_progress.checkpoint == checkpoint == current_index` 且 `route_progress.evidence_ref == evidence_ref`，`route_progress.failure_code == failure_code`。
- `navigation_timeout_sec` and `navigation_elapsed_sec` 在出现异常时可用于复现与修复。
- No waypoint patrol node is active at the same time; use `navigation_mode:=fixed_route`.

## 8. Delivery Action Modes

The task orchestrator defaults to safe dry-run delivery:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  delivery_mode:=dry_run \
  delivery_target:=trash_station
```

After map/localization and recovery checks pass, enable waypoint delivery:

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  delivery_mode:=waypoint \
  delivery_target:=trash_station
```
