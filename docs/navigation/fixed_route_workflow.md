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
- `software_proof`
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
- `current_index`: 与 `checkpoint` 一致的索引副本
- `target`: 当前目标位姿（若已覆盖该 checkpoint）
- `total_checkpoints`: 路线总 checkpoint
- `route_contract_version`
- `source`
- `failure_code`: 与顶层 `failure_code` 一致，用于复盘回放

`software_proof` 提供最小 route replay 证据落盘路径（软件证据，不代表 HIL）：

- `type`: 固定为 `route_replay`
- `artifact_format`: 固定为 `jsonl`
- `artifact_path`: 默认 `${debug_status_file}.software_proof.route_replay.jsonl`
- `evidence_ref`: 与顶层 `evidence_ref` 保持一致
- `fields`: 回放时必须关注的最小字段集合（`checkpoint/current_index/target/failure_code/evidence_ref/checkpoint_id`）

`artifact_path` 中每一行都是一次状态写入的 replay 记录，所有行复用同一个 `evidence_ref`，用于单次 run 的一致性回放（O3 software proof）。

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
    "current_index": 1,
    "target": null,
    "total_checkpoints": 2,
    "route_contract_version": "fixed_route.v1",
    "source": "fixed_route",
    "failure_code": ""
  },
  "software_proof": {
    "type": "route_replay",
    "artifact_format": "jsonl",
    "artifact_path": "/tmp/trashbot_fixed_route_status.json.software_proof.route_replay.jsonl",
    "evidence_ref": "/tmp/trashbot_fixed_route_status.json",
    "fields": [
      "checkpoint",
      "current_index",
      "target",
      "failure_code",
      "evidence_ref",
      "checkpoint_id"
    ]
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

### 5.3 同一 `evidence_ref` 的复盘回放（受控环境）

固定路线与任务复盘要在同一 run 上聚合时，可通过固定 `evidence_ref` 覆盖 status 记录：

```bash
ROUTE_STATUS=/tmp/trashbot_fixed_route_status.json
ROUTE_REPLAY_EVIDENCE=/tmp/route_replay_evidence.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest src/ros2_trashbot_nav/test/test_fixed_route_dry_run_offline.py::FixedRouteDryRunOfflineTest.test_dry_run_evidence_ref_syncs_to_route_progress

ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:=/tmp/replay_route.yaml \
  -p keyframe_dir:=/tmp/replay_keyframes \
  -p debug_status_file:=$ROUTE_STATUS \
  -p evidence_ref:=$ROUTE_REPLAY_EVIDENCE \
  -p dry_run:=true

jq '.state,.checkpoint,.current_index,.failure_code,.evidence_ref,.route_progress | {checkpoint, current_index, failure_code, evidence_ref, target: .target, current_index_in_progress: .current_index}' \
  $ROUTE_STATUS
```

示例输出（关键字段）：

```text
{
  "state": "completed",
  "checkpoint": 1,
  "current_index": 1,
  "failure_code": "",
  "evidence_ref": "/tmp/route_replay_evidence.json",
  "route_progress": {
    "checkpoint": 1,
    "current_index": 1,
    "target": null,
    "failure_code": "",
    "evidence_ref": "/tmp/route_replay_evidence.json"
  }
}
```

检查清单：

- `route_progress.checkpoint == payload.current_index == payload.checkpoint`
- `route_progress.target == payload.target`
- `route_progress.current_index == payload.current_index`
- `route_progress.failure_code == payload.failure_code`
- `route_progress.evidence_ref == payload.evidence_ref`
- `route_replay` 的 JSONL 每行都应含 `state/checkpoint/current_index/target/failure_code/evidence_ref/checkpoint_id`。
- 受控 replay 场景可用 `route_progress.evidence_ref` 查 task record 的同名证据文件。

### 5.4 run-level 复账脚本（只读）

新增只读复账脚本（不改动 payload）：

```bash
python3 pc-tools/evidence/evidence_crosscheck.py \
  /tmp/trashbot_fixed_route_status.json \
  --evidence-ref /tmp/route_replay_evidence.json \
  --task-record-dir ~/.ros/trashbot_tasks
```

当 task_record 同 run 不存在时，脚本会明确提示：

- `task_record not provided: cross-check skipped`（仅在 status/replay 可核验）
- `task_record route_progress not found`（说明 behavior 端暂未持久化该 run 的 route_progress）
- `FAIL` 明细中的字段不一致（用于复盘定位）

脚本要求：

- `route_status` 必须是 `fixed_route_autonomy` 的 status 输出路径（可用于 `evidence_ref` 定位）。
- `--evidence-ref` 为可选；不传时默认用 `status.evidence_ref`。
- `--task-record-dir` 在 `task_record` 为空时可用于按 `evidence_ref` 自动检索同 run 文件。
- 脚本始终是 read-only，无副作用。

需要把 fixed-route status、software proof replay、task record 和可选 HIL gate 状态保存成可复核材料时，增加 route/task rehearsal artifact 输出：

```bash
python3 pc-tools/evidence/evidence_crosscheck.py \
  /tmp/trashbot_fixed_route_status.json \
  --evidence-ref /tmp/route_replay_evidence.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --hil-gate-output /tmp/hil_gate_output.json \
  --rehearsal-artifact /tmp/route_task_rehearsal_artifact.json
```

artifact 字段要求：

- `schema=trashbot.route_task_rehearsal_artifact`
- `schema_version=1`
- `evidence_boundary=software_proof_docker_route_task_rehearsal_artifact_gate`
- `evidence_ref`
- `route_status_summary`
- `task_record_summary`
- `crosscheck_status`
- `hil_alignment_status`
- `diagnostics_summary`
- `not_proven`

`crosscheck_status.status=pass` 只表示 status/replay/task_record 软件对账通过。HIL gate 未提供、缺失、`software_proof` 或 `blocked` 时 artifact 仍可保存，但 `hil_alignment_status.alignment_status=not_proven`，且 `not_proven` 继续列出真实 Nav2/fixed-route、WAVE ROVER 运动、真实串口、真实 HIL 和 delivery success。该证据边界是 `software_proof_docker_route_task_rehearsal_artifact_gate`，不能用于声明真实路线实跑或上车交付闭环。

`diagnostics_summary` 是 diagnostics consumption 的只读摘要，schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，`evidence_boundary=software_proof_docker_route_task_rehearsal_diagnostics_gate`。它只给诊断面提供脱敏后的 `status`、`evidence_ref`、`crosscheck_status`、`hil_alignment_status`、`not_proven` 和 `next_step`，可映射到 diagnostics payload 的 `route_task_rehearsal` 字段。该字段不改变 Start/Confirm/Cancel、ACK、cursor、Nav2、WAVE ROVER 或 HIL 语义；缺 HIL 或 HIL 未对齐时仍必须显示 `not_proven`，不能写成真实 fixed-route、真实 HIL、真实 delivery success 或 Objective 5 外部云证明。

### 5.5 route/task rehearsal execution bundle

当需要把 route status、software replay、task record 和 crosscheck artifact 作为一份可传递材料交给 diagnostics 或 sprint closeout 时，使用 execution bundle 生成器：

```bash
python3 pc-tools/evidence/route_task_rehearsal_bundle.py \
  /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --output-dir /tmp/route_task_rehearsal_bundle
```

输出目录包含：

- `route_task_rehearsal_artifact.json`：由 `evidence_crosscheck.py` 生成的底层 artifact。
- `route_task_rehearsal_execution_bundle.json`：交接用 manifest，`schema=trashbot.route_task_rehearsal_execution_bundle`，`evidence_boundary=software_proof_docker_route_task_rehearsal_execution_bundle_gate`。

execution bundle manifest 顶层直接记录 diagnostics 只读消费字段：`route_task_rehearsal_artifact_ref`、`crosscheck_status`、`hil_alignment_status` 和 `diagnostics_summary`；同时保留脱敏路径引用、`evidence_ref`、`not_proven` 和 `next_step`。`status=available_software_proof` 与 `crosscheck_status.status=pass` 只表示 Docker/local route status、software replay 和 task record 软件对账通过；`hil_alignment_status.alignment_status=not_proven` 时仍缺真实 HIL。该 manifest 不是真实 Nav2/fixed-route、真实路线采集、WAVE ROVER 运动、真实串口/UART feedback、真实 HIL、dropoff/cancel completion 或 delivery success。

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
