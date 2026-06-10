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

No-motion 现场证据采集也统一复用 `learn.launch.py`，但只允许采样传感器、TF、`/odom` 和地图服务，禁止任何 `/cmd_vel` 发布：

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  no_motion_static_odom_tf:=true \
  no_motion_mock_odom_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1 \
  route_recorder:=true \
  route_output_dir:=/tmp/trashbot_no_motion_route
```

这个 no-motion 入口的边界是：

- `slam_toolbox` + `map_recorder` 负责证明 `map.yaml` 是否真的可保存，而不是只证明 service 存在。
- `camera_publisher`、`lidar_driver`、`static_transform_publisher`、synthetic `/odom` 只为 route/keyframe 软件链路补齐输入拓扑，不代表真实运动、真实里程计或机械标定已完成。
- `route_data_recorder` 在缺 `cv_bridge` 时会自动退化到 numpy/cv2 raw buffer fallback；若图像仍无法转换，也必须继续写 `route.csv` 并落盘 `image_conversion_status.json`。

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

## 1.5 Board Live Route Preflight

现场场景下先跑统一预检脚本，再执行 learn/route capture，避免每次重复手工整理命令。推荐链路：

```bash
bash onboard/scripts/board_live_route_preflight.sh
```

脚本默认使用 `192.168.1.11:37878`（可通过环境变量 `TRASHBOT_LIVE_BOARD_HOST`/`TRASHBOT_LIVE_BOARD_PORT` 或 `--host`/`--port` 覆盖）。
运行结果写入：`~/.ros/trashbot_live_preflight/<run_id>.log`。

最低执行要求：

- 本机 `git status --short`
- 默认网关可达性检查（允许失败，继续留痕）
- `ping`/`nc` 到目标 host:port
- `ssh` 到 `root@192.168.1.11 -p 37878`
- SSH 可达时进行 ros2 预检：
  - `hostname`
  - `date`
  - `source /opt/ros/humble/setup.bash`
  - `command -v ros2`
  - `ros2 pkg list`
  - `/scan` `/camera/image_raw` `/odom` `/tf` `/map` topic list 与 `hz` smoke

脚本只输出 capture/replay 模板，不执行底盘运动命令。你可以在网络恢复并确认 SSH 可达后，基于同一 `run_id` 手动执行：

- `learn.launch.py route_recorder:=true`
- `/trashbot/save_map`
- `route_csv_to_yaml`
- `fixed_route_autonomy dry_run`
- 可选 `ros2 bag record`

失败边界约束：

- `--local-only` 仅做本机预检，不发起 SSH 远端命令。
- `--dry-run` 只复用/打印模板，不要求远端可达。
- `--skip-capture` 会跳过 capture 模板输出，仍产生日志和网络闭环；如网络不达则返回非 0 并注明日志路径，避免“只报错不闭环”。

Expected outputs:

- `route.csv`
- `keyframes/*.jpg`
- `keyframes/*.json`
- `manifest.json`
- `image_conversion_status.json`（仅在图像转换退化时出现）

采集完成后，如果 route 材料和 map 材料像 `2026.06.10_01-15` 一样分在相邻目录，应生成 `trashbot.field_evidence_manifest.v1`，供 O6/O7 archive、consumer detail 和 PC replay 使用：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/route \
  --map-yaml sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.yaml \
  --map-pgm sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map/trashbot_dynamic_odom_tf_map.pgm \
  --output /tmp/trashbot_real_route_field_manifest.json
```

这一步只整理真实路线材料，不发布运动命令，不证明 Nav2 实跑或送达成功；输出必须保持 `safe_to_control=false`、`primary_actions_enabled=false`、`delivery_success=false`、`not_proven=true`。`route/manifest.json` 若是 `trashbot.vision_samples.v1`，会作为 source manifest 进入 field evidence manifest，而不是被当作 schema mismatch。

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

## 2.5 Sensing-Assumption Boundary

Route, fixed-route, and Nav2 planning docs may reference the target sensing
baseline from product hardware boundary work: single camera for visual/elevator
semantics, 2D LiDAR for SLAM/Nav2, and ToF for near-field safety. In this
workflow that wording is only a product/source-boundary assumption until real
2D LiDAR / ToF materials, a real Nav2/SLAM field pass, a near-field safety
pass, and delivery result evidence are all present on the same safe evidence
chain.

The upstream `pr5_mandatory_sensor_source_alignment` summary is allowed here
only as source-boundary input for PR #5 thread `PRRT_kwDOSWB9286CJ3tX`. It may
show `hardware_material_pending`, `not_proven`, `safe_to_control=false`,
`delivery_success=false`, and `primary_actions_enabled=false`, but it is not a
route runtime log, fixed-route field pass, Nav2/SLAM pass, ToF safety pass,
elevator field material, dropoff/cancel completion, HIL result, or delivery
success proof.

For closeout and review language, keep these layers separate:

- `pr5_mandatory_sensor_source_alignment`: source-boundary summary and missing
  material classification for mandatory sensor assumptions.
- Route/elevator field materials: real Nav2/fixed-route runtime log, route
  completion signal, task record, door/floor/human-assistance materials, and
  dropoff/cancel/delivery result packet.
- True field proof: real Nav2/SLAM route execution plus near-field safety
  evidence, still requiring `delivery_success=false` until a real delivery
  result explicitly proves success.

## 2.6 Nav2 No-Motion Lifecycle Smoke Boundary

真实上车 Nav2 readiness 不能用 `autonomous.launch.py` 做 no-motion smoke，因为该
launch 无条件启动 `esp32_bridge` 并触碰底盘 UART。`2026-06-10 07:55` 现场
smoke 的边界如下：

- 允许启动 LiDAR `/dev/ttyACM0`、smoke-only static TF 和 Nav2 lifecycle nodes。
- 禁止 `/cmd_vel`、`/api/base/*`、`/api/map/start`、`/api/nav2/start`、
  `/api/nav2/stop`、`ros2 action send_goal`、compute path service 和
  lifecycle transition service。
- 禁止打开 WAVE ROVER/base UART `/dev/ttyS5`，只允许 `lsof/fuser` 只读检查。
- 不发布 `/initialpose`；因此 `/amcl_pose` 未观测仍是有效 blocker。

本轮结果显示 `/scan_once_observed=true`，但 `map_server`、`amcl`、
`planner_server`、`controller_server` 均停在 `unconfigured [1]`，`/map` 与
`/amcl_pose` 未产出。直接 root cause 是真实上位机缺 `nav2_bringup`、
`nav2_lifecycle_manager` 以及当前参数所需的 Navfn/RPP 插件包；安装
`ros-humble-nav2-bringup` 的 dry-run 会新增 164 个包并升级 5 个系统库，所以不应
在没有明确维护窗口时把它当作小修复执行。

`2026-06-10 08:15` 后续 probe 只安装窄包：

- `ros-humble-nav2-lifecycle-manager`
- `ros-humble-nav2-navfn-planner`
- `ros-humble-nav2-regulated-pure-pursuit-controller`

APT dry-run 和实际安装均为 `0 upgraded, 4 newly installed, 0 to remove`，额外新增
`ros-humble-diagnostic-updater`。安装后上述三个包以及
`nav2_amcl/nav2_planner/nav2_controller/nav2_map_server` 均可由
`ros2 pkg prefix` 定位到 `/opt/ros/humble`。

手动 no-motion runtime 证明包缺失层已经消失，但 Nav2 ready 仍未成立：

- `map_server` 手动窗口内可加载 `/root/rober/onboard/runtime/maps/trashbot_map.yaml`
  并进入 `active [3]`。
- `amcl` 手动窗口内进入 `active [3]`，但本流程禁止 `/initialpose`，所以
  `/amcl_pose` 未观测，AMCL 日志明确要求设置 initial pose。
- `planner_server` 卡在 global costmap activation，原因是缺
  `map -> base_link` 或等效 localization TF；日志反复出现
  `Timed out waiting for transform from base_link to map`。
- `controller_server` 插件可加载，但 lifecycle 停在 `inactive [2]`，未进入 active。
- 手动窗口内 `/scan_once_observed=true`，`/map_once_observed=false`，
  `amcl_pose_observed=false`。
- `/cmd_vel` topic 因 controller server 出现 publisher，但
  `timeout 8 ros2 topic echo /cmd_vel` 无消息；本轮仍未发 goal、未 compute path、
  未发布 `/initialpose`、未调用任何 `/api/base/*` 或 `/api/nav2/start/stop`。

正式 `/api/nav2/proof/refresh -d '{"timeout_s":20}'` 是 read-only existing graph
collector，清场后调用时不会复用手动 stack，因此 canonical artifact 仍保持
`status=blocked_with_root_cause`，并记录 `map_server_active=false`、
`amcl_active=false`、`planner_active=false`、`controller_active=false`、
`scan_once_observed=false`、`map_once_observed=false`、`amcl_pose_observed=false`。
这不是 ready 回退，而是 collector 与手动 runtime 证据边界不同。下一步如果要继续
no-motion Nav2 readiness，必须先定义不发布运动命令的 initial pose / localization
证据边界，或提供只读可验证的 `map -> odom -> base_link` TF 来源；否则 planner
global costmap 会继续卡住。

`2026-06-10 08:45` 起，`/api/nav2/proof/refresh` 支持显式 opt-in 的
no-motion initialpose/localization proof。默认 body 不传
`"initialpose_opt_in": true` 时仍保持 read-only collector，不发布 `/initialpose`。
只有 body 显式传入 `initialpose_opt_in=true` 时，helper 才会在证明窗口内向
`/initialpose` 发布一次 PoseWithCovarianceStamped，并记录 `initialpose_x`、
`initialpose_y`、`initialpose_yaw` 与 `initialpose_frame_id`。

该 opt-in 只用于验证 AMCL localization 证据，不改变固定路线执行边界：

- 允许采集 `/amcl_pose`、`map -> odom` 与 `map -> base_link` listener 结果。
- 禁止发送 Nav2 goal、调用 compute path、发布 `/cmd_vel`、调用 `/api/base/*`、
  启动 `/api/nav2/start` 或打开 WAVE ROVER/base UART `/dev/ttyS5`。
- Artifact 必须继续保留 `safe_to_control=false`、`publishes_cmd_vel=false`、
  `calls_base_manual=false`、`uses_base_uart=false`、`delivery_success=false`。
- 即使 `/amcl_pose` 或 TF 被观测，也只能说明 no-motion localization proof 前进；

`2026-06-10 09:05` 起，path generation proof 也走同一个 helper/API，但仍然必须显式
opt-in。默认 body 不传 `"path_generation_opt_in": true` 时，helper 不会调用
`ComputePathToPose`；只有在 managed runtime + initialpose/localization 已成立后，
才会在 no-motion 边界内尝试一次 planner 计算，并把 path 点数、目标、响应和
planner readiness 一起写入 artifact。

`/api/nav2/proof/refresh` 现在会先显式 source ROS Humble setup，再拉起 helper。
这样 `rclpy` 和 Nav2 action client 的运行时依赖不会被 systemd 服务环境吞掉；
但这个变化只影响 proof helper 的启动方式，不改变默认只读/no-motion 边界。

`2026-06-11 01:45` 起，上位机 API 的 helper subprocess timeout 与 PC
`检查路径` proxy 预算对齐。PC 固定 body 为 `timeout_s=8`、
`path_generation_timeout_s=8`、`managed_runtime_opt_in=false`、
`initialpose_opt_in=false`、`path_generation_opt_in=true`；对应上位机 subprocess
预算为约 `36s`，低于 PC proxy 的 `46s` 等待窗口。这个预算只限制 HTTP refresh
等待 helper 的最长时间，不改变 helper 内部 no-motion collector 的 ROS2 观测语义。
如果真实 Nav2 proof refresh 仍慢于该窗口，上位机会先返回结构化 timeout/root cause，
PC 再通过固定 `GET /api/nav2/proof/latest` 只读兜底展示最近 artifact；不能让 PC
侧先出现 `fetch_timeout_46000ms` 后才知道上位机实际已经生成路径。

这一步仍然不等于可发车：

- 允许：一次 `ComputePathToPose` 风格的 planner 计算。
- 禁止：`NavigateToPose`、`FollowPath`、`/cmd_vel`、`/api/base/*`、`bt_navigator`
  以及任何默认 motion side effect。
- `safe_to_control`、`delivery_success` 仍然必须保持 `false`。
仍不等于 path generation、path execution、fixed-route execution、HIL 或送达成功。

`2026-06-10 09:15` 起，`o10_amcl_nav2_runtime_proof.py` 增加显式 opt-in 的
managed no-motion localization runtime。默认不传 `managed_runtime_opt_in` 时仍保持
read-only collector；只有显式传入时，helper 才会在 proof 窗口内短暂启动：

- `ros2_trashbot_hardware/lidar_driver`：`/dev/ttyACM0 @ 150000`
- `static_transform_publisher`：`odom -> base_link`
- `static_transform_publisher`：`base_link -> laser_frame`
- `nav2_map_server/map_server`
- `nav2_amcl/amcl`
- `nav2_lifecycle_manager/lifecycle_manager`

该 managed runtime 的固定边界：

- 允许：`/scan`、`/map`、`/amcl_pose`、`map -> odom`、`map -> base_link`、
  lifecycle 和 topic once 证据采集。
- 禁止：planner/controller、`ros2 action send_goal`、compute path、
  `/cmd_vel`、`/api/base/*`、`/api/nav2/start`、`/api/nav2/stop`、
  `autonomous.launch.py`、WAVE ROVER base UART `/dev/ttyS5`。
- vendor 事实来源：`docs/vendor/VENDOR_INDEX.md`。WAVE ROVER base 是
  newline-delimited UART JSON；vendor Raspberry Pi UART 路径不是 Orange Pi
  固定事实；本 proof 只允许 LiDAR `/dev/ttyACM0`，不允许打开 `/dev/ttyS5`。

推荐 direct-helper 命令：

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
python3 scripts/o10_amcl_nav2_runtime_proof.py \
  --managed-runtime-opt-in \
  --managed-timeout-s 20 \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --initialpose-x 0.0 \
  --initialpose-y 0.0 \
  --initialpose-yaw 0.0
```

`2026-06-10 08:33 CST` 真实上位机 direct-helper 结果已经满足本轮 localization proof：

- `status=nav2_no_motion_localization_runtime_observed`
- `managed_runtime_started=true`
- `managed_runtime_cleanup_ok=true`
- `scan_once_observed=true`
- `map_once_observed=true`
- `map_server_active=true`
- `amcl_active=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=true`
- `safe_to_control=false`

清场后 `lsof /dev/ttyS5 /dev/ttyACM0` 与 `fuser -v /dev/ttyS5 /dev/ttyACM0`
均无输出，说明本轮没有残留 runtime，也没有触碰 base UART。

推荐 API 命令：

```bash
curl --max-time 90 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H "Content-Type: application/json" \
  -d '{"timeout_s":20}'

curl --max-time 150 -sS -X POST http://127.0.0.1:8787/api/nav2/proof/refresh \
  -H "Content-Type: application/json" \
  -d '{"timeout_s":20,"managed_runtime_opt_in":true,"managed_timeout_s":20,"managed_map_yaml":"/root/rober/onboard/runtime/maps/trashbot_map.yaml","initialpose_opt_in":true,"initialpose_x":0.0,"initialpose_y":0.0,"initialpose_yaw":0.0}'
```

`2026-06-10 08:37 CST` 真实上位机 API 结果：

- 默认 body 仍为 read-only：`managed_runtime_requested=false`、
  `managed_runtime_started=false`、`scan_once_observed=false`、
  `map_once_observed=false`、`safe_to_control=false`。
- managed body 成功：`proof_status=nav2_no_motion_localization_runtime_observed`，
  且 direct-helper 与 API artifact 一致。
- `GET /api/nav2/proof/latest` 的顶层 `status` 仍按 software guard 返回
  `not_proven`，但 `latest_proof_status` 和 `latest_*` 字段已经反映最新 proof。
- `GET /api/nav2/status` 当前通过嵌套 `proof_latest` 提供最新摘要，
  顶层不直接翻转为 runtime proven；读取方应消费
  `proof_latest.latest_proof_status` 和相关 `latest_*` 字段。

## 2.7 Localization Reset Phase Artifact

`/api/localize/reset` 现在通过 `o10_amcl_nav2_runtime_proof.py` 写阶段性
partial artifact。即使 helper 被上层 HTTP/进程 timeout 打断，
`/api/localize/proof/latest` 也应保留以下诊断字段：

- `last_phase` / `last_successful_phase`
- `phase_history`
- `current_command` / `recent_commands`
- `package_availability` / `package_check_mode` / `package_checks_batch_ok`
- `managed_runtime_started` / `managed_runtime_cleanup_ok`
- `initialpose_publish_attempted` / `initialpose_published`
- `amcl_pose_observed`
- `localization_tf_observed`
- `root_causes`

Package availability remains part of the proof, but it is now a single sourced
`ros2 pkg list` diagnostic instead of one `ros2 pkg prefix` process per
package. The helper records each expected package result under
`commands.package_checks` and the raw list command under
`commands.package_checks_batch`, while `/initialpose`, `/amcl_pose`, and TF
probes stay ahead of package and graph diagnostics in the evidence path.

这个机制只提升 evidence capture 可观测性，不改变 no-motion 边界：

- 只允许显式定位 reset 入口发布一次 `/initialpose`。
- 不发布 `/cmd_vel`，不调用 `/api/base/*`，不触发 `NavigateToPose`。
- 不打开 WAVE ROVER 底盘 UART `/dev/ttyS5`。
- managed runtime 只限 localization graph；路径生成和控制层仍由独立 opt-in
  证据链处理。

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

### 4.1 O7 Field Evidence Consumer Ingest

`trashbot.field_evidence_manifest.v1` 生成后，可以进入 PC 工作站的 O7 Field Evidence Consumer Ingest 主入口，把 manifest、route replay fixture 和 labeling fixture 合成同一份只读消费摘要。这个入口只服务于软件证明和本地/mock 复跑，不会把 route replay 变成真实播放，也不会把 labeling 变成真实提交。

推荐的本地消费链是：

1. 先生成 `field_evidence_manifest.json`
2. 再准备 `route replay` fixture 和 `labeling` fixture
3. 用 `pc-tools/workstation` 的 `GET /api/o7/field-evidence-consumer-ingest` 或 O7 Previews 面板加载三者

该入口必须继续暴露：

- `source_manifest_schema=trashbot.field_evidence_manifest.v1`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- 明确的 `blocked_reason` / `next_required_evidence`

只要 manifest 缺失、schema 不匹配、preflight 未 ready、fixture 不完整或 SSH 不可达，PC 侧都应 fail closed，而不是把缺口吞成 ready。

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

## 4.5 Field-Run Intake Review Console

真实路线-任务 field run 前后的 PC/support 复核分两层处理：

1. `pc-tools/evidence/route_task_field_run_intake.py` 接收 route status、task record、runtime log、robot-side task evidence 和 support-safe mobile summary，用同一 `evidence_ref` 做 software crosscheck。
2. `pc-tools/evidence/route_task_field_run_review.py` 只读 intake/crosscheck JSON，输出 operator/support 可读的 review report。

review console 示例：

```bash
python3 pc-tools/evidence/route_task_field_run_review.py \
  --intake-json /tmp/route_task_field_run_intake.json \
  --once-json
```

review report 使用 `schema=trashbot.route_task_field_run_review_console.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_review_console_gate`。核心字段包括：

- `review_decision`: 把 missing、mismatch、unsafe summary 或 unsupported schema 转成下一步操作分支。
- `operator_next_steps`: 给现场人员的补采、统一 `evidence_ref`、重跑 intake/review 或进入人工复核步骤。

## 4.6 Route/Task Field-Retest Callback Review Decision

现场复测 callback 链路在 `route_task_field_retest_callback_intake` 后新增一层 review decision：

```bash
python3 pc-tools/evidence/route_task_field_retest_callback_review_decision.py \
  --callback-intake-json /tmp/route_task_field_retest_callback_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

该 gate 使用 `schema=trashbot.route_task_field_retest_callback_review_decision.v1`，summary 使用 `schema=trashbot.route_task_field_retest_callback_review_decision_summary.v1`，证据边界为 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`。它只读 callback intake artifact / summary / wrapper / nested JSON，把 received filenames summary、missing materials、same-evidence-ref verdict 和 next-backfill 状态整理成 `ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema`、`blocked_unsafe_callback` 或 `blocked_success_claim`。

required evidence packet 固定覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。该层不读取真实材料目录、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser；所有输出都保持 `not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。因此即使 decision 为 `ready_for_result_intake`，也只表示 sanitized callback metadata 可进入后续 result intake 复账，不是真实 field pass、真实投放、HIL、手机/browser 或 Objective 5 external proof。
- `commands_to_rerun`: review 层整理后的重跑顺序，不是原样复制 intake 字段。
- `phone_safe_summary`: support/mobile 可展示的白名单摘要。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、真实硬件反馈、HIL、dropoff/cancel completion、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: review 不能放行控制动作，也不能声明送达成功。

`ready_for_operator_review` 只表示 Docker/local software proof 的 intake 材料足够进入人工复核；它不是实机 fixed-route/Nav2、真实路线采集、WAVE ROVER/HIL、真实投放、真实取消完成或 delivery success。任何缺 intake、坏 JSON、unsupported schema、unsafe support copy、缺材料或同一 `evidence_ref` 不一致，都必须保持 blocked review report，再按 `operator_next_steps` 补采和重跑。

## 4.6.1 Route/Task Field-Retest Review Result Handoff

callback review decision 之后，可以运行 PC 侧 review result handoff gate，把上一轮 `route_task_field_retest_callback_review_decision` 的 artifact、summary 或 wrapper/nested JSON 转成 result-intake 前交接摘要：

```bash
python3 pc-tools/evidence/route_task_field_retest_review_result_handoff.py \
  --callback-review-json /tmp/route_task_field_retest_callback_review_decision_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_review_result_handoff.json \
  --summary-output /tmp/route_task_field_retest_review_result_handoff_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_review_result_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_review_result_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`handoff_status`、`source_review_decision`、`result_intake_readiness`、`owner_handoff`、`rerun_commands`、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

Decision mapping 固定为：`ready_for_result_intake` -> `ready_for_result_intake_handoff` / `ready_for_result_material_intake`；`needs_material_backfill` -> `blocked_until_material_backfill` / `not_ready`；`evidence_ref_mismatch_rerun` -> `blocked_until_same_evidence_ref_rerun` / `not_ready`；`unsupported_callback_schema` -> `blocked_unsupported_source_schema` / `not_ready`；`blocked_unsafe_callback` 或 `blocked_success_claim` -> `blocked_unsafe_source_review` / `not_ready`。

`route_task_field_retest_review_result_handoff` 仍是 software proof。它不读取真实材料目录、不触发 result intake、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。`ready_for_result_intake_handoff` 只表示 Docker/local `software_proof_docker_route_task_field_retest_review_result_handoff_gate` 已把 review decision 交接给 result-intake 前置面；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.6 Field-Run Execution Pack

review console 完成后，现场联跑还需要一份“照着跑”的执行包。`pc-tools/evidence/route_task_field_run_execution_pack.py` 只读 review console JSON，输出现场 manifest、材料模板、first-run/rerun 命令清单和 phone-safe summary：

```bash
python3 pc-tools/evidence/route_task_field_run_execution_pack.py \
  --review-json /tmp/route_task_field_run_review.json \
  --once-json
```

execution pack 使用 `schema=trashbot.route_task_field_run_execution_pack.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_execution_pack_gate`。核心字段包括：

- `field_run_manifest`: 现场执行总目录，标明 source review 状态、`evidence_ref`、所需材料名称和 blocked/ready 状态。
- `required_material_templates`: route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary 和 PC review console 的字段模板。
- `first_run_commands`: 第一次现场联跑的材料采集与 intake/review/execution-pack 生成顺序。
- `rerun_commands`: review blocked、材料重采或同一 `evidence_ref` 修复后的重跑顺序。
- `same_evidence_ref_required=true`: 所有现场材料必须沿用同一 `evidence_ref`，不能把不同 run 的材料拼成成功证据。
- `phone_safe_summary`: support/mobile 可展示的白名单摘要。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、真实硬件反馈、HIL、dropoff/cancel completion、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: execution pack 不能放行控制动作，也不能声明送达成功。

`ready_for_field_run_execution_pack` 只表示 Docker/local software proof 的 review console 足以生成现场执行包。该 CLI 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；它不能证明实机 fixed-route/Nav2、真实路线采集、HIL、真实投放、真实取消完成或 delivery success。任何缺 review、坏 JSON、unsupported schema、unsafe copy、review blocked、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须保持 blocked execution pack，再按 `rerun_commands` 修复和重跑。

## 4.7 Field-Run Reconciliation Gate

execution pack 和 intake/review 材料回到同一条证据链后，用 `pc-tools/evidence/route_task_field_run_reconciliation.py` 做最终 Docker/local software-proof 复账：

```bash
python3 pc-tools/evidence/route_task_field_run_reconciliation.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --intake-json /tmp/route_task_field_run_intake.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

reconciliation artifact 使用 `schema=trashbot.route_task_field_run_reconciliation.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_reconciliation_gate`。核心字段包括：

- `same_evidence_ref_required=true`: execution pack 与 intake/review 必须沿用同一个 safe `evidence_ref`。
- `reconciliation_verdict`: ready 或 blocked 分支，覆盖缺 execution pack、缺 intake/review、坏 JSON、unsupported schema、unsupported boundary、缺 `evidence_ref`、`evidence_ref` mismatch、unsafe summary 和 missing materials。
- `materials_status`: intake/review 材料状态、缺失材料、mismatch 计数和可展示的 source status。
- `operator_next_steps`: 给现场人员的补采、重跑、统一 `evidence_ref` 或修复 phone-safe 摘要步骤。
- `phone_safe_summary`: diagnostics/mobile 可展示的白名单摘要，不复制 raw artifact、本机完整路径或控制细节。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、真实硬件反馈、HIL、dropoff/cancel completion、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: reconciliation 不能放行控制动作，也不能声明送达成功。

`ready_for_route_task_field_run_reconciliation` 只表示 Docker/local software proof 的 execution pack 与 intake/review 材料可读、schema/boundary 支持、同一 `evidence_ref` 对齐且 phone-safe 摘要可展示。它不是真实 fixed-route/Nav2、真实路线采集、WAVE ROVER/HIL、真实投放、真实取消完成或 delivery success。该 CLI 不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G。

## 4.8 PC Route Elevator Console Integration

PC route debug console 可以在原 fixed-route status 与 recent task 摘要之外，可选读取上一轮电梯路线复账 artifact/summary：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --elevator-route-reconciliation /tmp/elevator_route_evidence_reconciliation.json \
  --once-json
```

`/api/status`、`/api/summary` 与 HTML 页面使用同一份 `trashbot.pc_route_debug_console.v1` summary，父级证据边界保持 `software_proof_docker_pc_route_debug_console_gate`，以兼容 Robot diagnostics 的既有 PC console 消费契约。新增字段 `route_elevator_reconciliation` 只接受 `trashbot.elevator_route_evidence_reconciliation.v1` 或 `trashbot.elevator_route_evidence_reconciliation_summary.v1`，并要求输入 `source=software_proof`、`evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`、`delivery_success=false`、`primary_actions_enabled=false`。

该 section 只展示 safe `evidence_ref`、reconciliation status/verdict、same-evidence-ref 状态、source states、missing/mismatch 摘要、operator next steps、boundary、`not_proven` 和 `safe_copy`。嵌套 `route_elevator_reconciliation.evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`，并用 `source_evidence_boundary` 保留输入复账边界。缺文件、坏 JSON、unsupported schema/boundary、unsafe copy、success claim 或 control claim 都保持 blocked/not_proven；页面不读取 raw artifact、不暴露本机路径、token、serial/UART、WAVE ROVER、`/cmd_vel`、checksum 或 traceback。

该 gate 是 Docker/local software proof only。它不证明真实 Nav2/fixed-route、真实路线采集、真实电梯、HIL、dropoff/cancel completion、delivery success、真实手机设备/browser 或 Objective 5 external proof。

## 4.9 Route Elevator Field Session Handoff

PC route debug console、route completion signal 和 elevator-route reconciliation 都对齐后，可以生成下一次现场 session 的 handoff artifact，方便把真实现场材料按同一 `evidence_ref` 回填：

```bash
python3 pc-tools/evidence/route_elevator_field_session_handoff.py \
  --pc-route-debug-json /tmp/pc_route_debug_console.json \
  --route-completion-json /tmp/route_task_completion_signal.json \
  --elevator-route-reconciliation-json /tmp/elevator_route_evidence_reconciliation.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_elevator_field_session_handoff.json \
  --summary-output /tmp/route_elevator_field_session_handoff_summary.json
```

artifact 使用 `schema=trashbot.route_elevator_field_session_handoff.v1`，summary 使用 `schema=trashbot.route_elevator_field_session_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_elevator_field_session_handoff_gate`。顶层固定包含 `same_evidence_ref_required=true`、`source_summaries`、`field_session_manifest`、`required_materials`、`operator_handoff`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`required_materials` 至少要求同一 safe `evidence_ref` 下的 `nav2_fixed_route_runtime_log.json`、`route_completion_signal.json`、`task_record.json`、`door_state.json`、`target_floor_confirmation.json`、`human_assistance_operator_note.md`、`dropoff_or_cancel_completion.json`、`delivery_result.json` 和 `diagnostics_mobile_safe_summary.json`。本 gate 只生成 checklist/manifest，不读取 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、手机设备、外部云、OSS/CDN、DB/queue 或 4G。

保守阻断规则：

- 三份输入任一缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当交接证据。
- 任一输入 schema、evidence boundary 或显式 `source` 不支持：输出 blocked。
- 任一输入缺 `evidence_ref`，或与 `--evidence-ref` 不一致：输出 blocked。
- 任一输入或摘要含 unsafe copy、`primary_actions_enabled=true`、`delivery_success=true`、delivery/dropoff/cancel success 文案或 `hil_pass=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能展示白名单摘要，不包含 raw artifact、本机完整路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。该 gate 是现场 session handoff，不是 delivery success，也不是 Objective 5 external proof；`not_proven` 必须继续包含真实 Nav2/fixed-route、真实电梯门状态、真实目标楼层、人工协助、HIL、dropoff/cancel completion、真实手机和 O5 外部材料。

## 4.9.5 Route Task Field Retest Session Handoff

上一轮 `route_task_field_retest_execution_pack` 准备好后，可以生成路线-任务现场复测 session handoff，供 Robot diagnostics 和 mobile/web 只读展示同一 `evidence_ref` 的下一步回填要求：

```bash
python3 pc-tools/evidence/route_task_field_retest_session_handoff.py \
  --execution-pack-json /tmp/route_task_field_retest_execution_pack.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --session-owner "Autonomy Algorithm Engineer" \
  --output /tmp/route_task_field_retest_session_handoff.json \
  --summary-output /tmp/route_task_field_retest_session_handoff_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_session_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_session_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_session_handoff_gate`。顶层固定包含 `same_evidence_ref_required=true`、`source_execution_pack`、`session_handoff`、`operator_handoff`、`material_placeholders`、`material_paths`、`rerun_commands`、`field_callback_checklist`、`safe_copy`、`fail_closed_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

source execution pack 必须已经列出八类下一次真实现场回填材料：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。handoff 输出的 `material_placeholders` 只是相对路径和 required fields 清单，用于现场回填目录约定；本 gate 不读取 ROS graph、Nav2 runtime、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue、4G 或任何真实现场材料。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当交接证据。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- source execution pack 缺任一 required material，或只给 TBD/sample/placeholder 材料：输出 blocked。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary、safe copy 和 fail-closed flags，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_session_handoff_not_proven` 只表示 Docker/local software proof 足以生成复测 session 交接材料，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.6 Route Task Field Retest Material Pack

现场同学按 session handoff 回填材料目录后，先运行 PC 侧 material pack gate，把目录里的八类材料整理为 sanitized artifact / summary，供现有 result intake / result reconciliation 继续消费：

```bash
python3 pc-tools/evidence/route_task_field_retest_material_pack.py \
  --material-dir /tmp/route_task_field_retest_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_material_pack.json \
  --summary-output /tmp/route_task_field_retest_material_pack_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_material_pack.v1`，summary 使用 `schema=trashbot.route_task_field_retest_material_pack_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_material_pack_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`material_manifest`、`material_pack_summary`、`material_completeness`、`missing_materials`、`rejected_materials`、`operator_next_steps`、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

material pack 固定要求八类现场复测材料：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。该 gate 只读取目录内白名单文件名并输出脱敏状态，不复制 raw log、raw note、完整 artifact 或本机路径；每类材料都必须沿用同一 safe `evidence_ref`。

保守阻断规则：

- `--material-dir` 缺失或目录不存在：输出 blocked，不猜测材料存在。
- 任一材料缺失、JSON 不可读、不是 JSON object、仍是 placeholder/TBD/sample/not_collected：输出 blocked 或 rejected。
- 任一材料 `evidence_ref` 与同一证据号不一致：输出 blocked。
- 输入含 raw path、credential、ROS topic、`/cmd_vel`、serial/UART、WAVE ROVER detail、traceback、checksum、完整 artifact、unsafe success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`route_task_field_retest_material_pack` 仍是 software proof。`ready_for_field_retest_material_pack_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_material_pack_gate` 已把目录材料整理成可交给 result intake / reconciliation 的安全摘要；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.7 Route Task Field Retest Operator Drill

material pack 之后，可以运行 PC 侧 operator drill gate，把 material pack、result intake 和 result reconciliation 的操作顺序固化为现场同学可复账的 artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_operator_drill.py \
  --material-pack-json /tmp/route_task_field_retest_material_pack_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_operator_drill.json \
  --summary-output /tmp/route_task_field_retest_operator_drill_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_operator_drill.v1`，summary 使用 `schema=trashbot.route_task_field_retest_operator_drill_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_operator_drill_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`material_pack_command`、`result_intake_command`、`result_reconciliation_command`、`required_outputs`、`missing_material_prompts`、`operator_callback_checklist`、`rerun_notes`、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

operator drill 只读取 material pack artifact/summary/wrapper/nested JSON，不读取材料目录、ROS graph、Nav2 runtime、真实日志、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue、4G 或任何真实现场文件内容。它把 material pack 的 missing/rejected 状态转成补采提示，把同一 `evidence_ref` 串到 result intake 和 result reconciliation 命令，并要求现场 callback 只回填事实摘要、失败原因和安全结果输入。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 material pack 已存在。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`route_task_field_retest_operator_drill` 仍是 software proof。`ready_for_operator_drill_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_operator_drill_gate` 已把 material pack 到 result intake/reconciliation 的演练顺序复账清楚；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.8 Route Task Field Retest Drill Console

operator drill 之后，可以运行 PC 侧 drill console gate，把上一轮 `route_task_field_retest_operator_drill` 的命令标签、safe checklist、缺失材料提示和 operator callback checklist 整理成 console artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_drill_console.py \
  --operator-drill-json /tmp/route_task_field_retest_operator_drill_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_drill_console.json \
  --summary-output /tmp/route_task_field_retest_drill_console_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_drill_console.v1`，summary 使用 `schema=trashbot.route_task_field_retest_drill_console_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_drill_console_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`console_status`、material pack / result intake / result reconciliation command labels、`safe_checklist`、`missing_material_prompts`、`operator_callback_checklist`、`rerun_notes`、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

drill console 只读取 operator drill artifact/summary/wrapper/nested JSON，不读取真实材料目录、ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。它把 operator drill 的同一 `evidence_ref`、命令标签和安全补采提示整理成 PC console 摘要，供 Robot/mobile 只读消费。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 operator drill 已存在。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 上游 operator drill 不是 `ready_for_operator_drill_not_proven`：输出 blocked，不把未 ready 演练推进成 console ready。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`route_task_field_retest_drill_console` 仍是 software proof。`ready_for_drill_console_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_drill_console_gate` 已把 operator drill 的演练控制台摘要复账清楚；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.9 Route Task Field Retest Acceptance Brief

drill console 之后，可以运行 PC 侧 acceptance brief gate，把上一轮 `route_task_field_retest_drill_console` 的 console summary 转成现场入口前置条件、执行 checklist、pass/fail criteria、必需证据包、owner handoff 和 rerun notes：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_brief.py \
  --drill-console-json /tmp/route_task_field_retest_drill_console_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_brief.json \
  --summary-output /tmp/route_task_field_retest_acceptance_brief_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_brief.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_brief_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`acceptance_status`、`field_entry_prerequisites`、`execution_checklist`、`pass_fail_criteria`、`required_evidence_packet`、`owner_handoff`、`rerun_notes`、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

required evidence packet 固定列出 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。acceptance brief 只读取 drill console artifact/summary/wrapper/nested JSON，不读取真实材料目录、ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。它把现场验收前要看的材料清单固化下来，供 Robot/mobile 只读消费。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 drill console 已存在。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 上游 drill console 不是 `ready_for_drill_console_not_proven`：输出 blocked，不把未 ready 控制台推进成 acceptance brief ready。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`route_task_field_retest_acceptance_brief` 仍是 software proof。`ready_for_field_retest_acceptance_brief_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_brief_gate` 已把现场复测验收简报复账清楚；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.10 Route Task Field Retest Evidence Dispatch

acceptance brief 之后，可以运行 PC 侧 evidence dispatch gate，把上一轮 `route_task_field_retest_acceptance_brief` 的 required evidence packet 转成现场材料 owner、推荐文件名、回填顺序、callback checklist 和 fail-closed rerun notes：

```bash
python3 pc-tools/evidence/route_task_field_retest_evidence_dispatch.py \
  --acceptance-brief-json /tmp/route_task_field_retest_acceptance_brief_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_evidence_dispatch.json \
  --summary-output /tmp/route_task_field_retest_evidence_dispatch_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_evidence_dispatch.v1`，summary 使用 `schema=trashbot.route_task_field_retest_evidence_dispatch_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、dispatch status、material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist、fail-closed rerun notes、required evidence packet、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

required evidence packet 固定列出 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。evidence dispatch 只读取 acceptance brief artifact/summary/wrapper/nested JSON，不读取真实材料目录、ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。它只把下一次现场要回填的证据包分派清楚，供 Robot/mobile 只读消费。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 acceptance brief 已存在。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 上游 acceptance brief 不是 `ready_for_field_retest_acceptance_brief_not_proven`：输出 blocked，不把未 ready 简报推进成 dispatch ready。
- required evidence packet 缺任一固定材料：输出 blocked，避免现场回填口径不完整。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`route_task_field_retest_evidence_dispatch` 仍是 software proof。`ready_for_field_retest_evidence_dispatch_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_evidence_dispatch_gate` 已把现场证据包派发口径复账清楚；它不是真实 field pass、真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.11 Route Task Field Retest Callback Intake

evidence dispatch 派发推荐文件名后，可以运行 PC 侧 callback intake gate，把现场同学回传的 sanitized callback JSON 转成 Robot diagnostics 和 mobile/web 可只读展示的 fail-closed 回执入口摘要：

```bash
python3 pc-tools/evidence/route_task_field_retest_callback_intake.py \
  --dispatch-json /tmp/route_task_field_retest_evidence_dispatch_summary.json \
  --callback-json /tmp/route_task_field_retest_sanitized_callback.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_callback_intake.json \
  --summary-output /tmp/route_task_field_retest_callback_intake_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_callback_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_callback_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_callback_intake_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、intake status、received filenames summary、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、owner handoff、fail-closed rerun notes、required evidence packet、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

callback JSON 只允许 metadata 字段：recommended filename received status、safe `evidence_ref`、missing material ids、next backfill action、owner callback note 和 callback checklist result。该设计故意不读取真实材料目录，也不打开 dispatch 推荐的文件名，因为 callback intake 只能证明“现场回执元数据已按同一证据号复账”，不能证明材料内容真实、路线真的跑过、投放完成或 field pass。它也不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。

保守阻断规则：

- dispatch 或 callback 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测现场回执已经存在。
- dispatch schema / boundary 不支持，或 callback schema / boundary / 字段不在白名单：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- callback received status、missing material ids、next backfill action、owner note 或 checklist result 不是严格类型：输出 blocked。
- callback 缺项引用不属于八类 required evidence packet：输出 blocked。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary、safe copy 和 fail-closed flags，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_callback_intake_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_callback_intake_gate` 已把现场回执元数据复账清楚，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.12 Route Task Field Retest Result Intake

现场复测 session handoff 或 review-result handoff 被现场同学回填 summary 后，可以运行 result intake gate，把同一 `evidence_ref` 下的八类结果材料摘要转成 Robot diagnostics 和 mobile/web 可只读展示的 fail-closed result intake：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_intake.py \
  --result-json /tmp/route_task_field_retest_session_handoff_summary_with_results.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_intake.json \
  --summary-output /tmp/route_task_field_retest_result_intake_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_result_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_intake_gate`。顶层固定包含 `same_evidence_ref_required=true`、`source_result`、`result_materials`、`material_completeness`、`missing_materials`、`operator_next_steps`、`field_callback_checklist`、`rerun_summary`、`safe_copy`、`fail_closed_phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

result intake 必须看到八类现场复测结果材料摘要：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。输入可以是 result artifact、summary、session handoff artifact/summary、review-result handoff artifact/summary 或 wrapper/nested JSON；如果 handoff summary 已经带 `returned_materials`、`collected_materials`、`result_materials` 或 `field_result_materials`，gate 会从这些字段提取材料摘要。review-result handoff 只提供前置交接语义时不会裁剪八类固定清单，缺少任何一类材料仍会 fail closed。本 gate 不读取 ROS graph、Nav2 runtime、真实日志文件内容、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue、4G 或任何真实现场文件内容。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当结果材料。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 任一结果材料缺失、仍是 placeholder/TBD/sample/not_collected，或材料自身 `evidence_ref` 与同一证据号不一致：输出 blocked。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary、safe copy 和 fail-closed flags，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_result_intake_not_proven` 只表示 Docker/local software proof 足以接收同一 `evidence_ref` 的八类复测结果材料摘要，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.13 Route Task Field Retest Result Reconciliation

result intake 之后，可以运行 PC-side reconciliation gate，把上一轮 `route_task_field_retest_result_intake`、`route_task_field_retest_session_handoff`、`route_task_field_retest_execution_pack` 或现场 result wrapper/nested JSON 复账成 artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py \
  --result-json /tmp/route_task_field_retest_result_intake.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_reconciliation.json \
  --summary-output /tmp/route_task_field_retest_result_reconciliation_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_result_reconciliation.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_reconciliation_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`。顶层固定包含 `same_evidence_ref_required=true`、`same_evidence_ref_status`、`source_result`、`result_materials`、`missing_materials`、`mismatch_reasons`、`operator_next_steps`、`rerun_summary`、`field_callback_checklist`、`fail_closed_phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

如果输入是 result-intake artifact / summary，且其 `source_result.schema` 是 `trashbot.route_task_field_retest_review_result_handoff.v1` 或 `trashbot.route_task_field_retest_review_result_handoff_summary.v1`，reconciliation 会在 artifact、summary 和 phone-safe summary 中保留安全 lineage：`source_result_intake_schema`、`source_result_intake_status`、`source_review_result_handoff_schema`、`source_review_result_handoff_status`。这些字段只来自 result-intake 已输出的 `source_result` 摘要，用于说明本轮 result reconciliation 来自 handoff-derived result-intake；gate 不读取 raw handoff artifact、不追读本机文件、不裁剪八类 required result materials，也不改变 schema major version。

reconciliation 必须看到八类现场复测结果材料摘要：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。输入可以是 artifact、summary、wrapper 或 nested JSON；如果只拿到 execution pack / session handoff placeholder，gate 会保留 missing / placeholder-only 状态，不把准备包冒充为现场结果。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当结果材料。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 任一结果材料缺失、仍是 placeholder/TBD/sample/not_collected，或材料自身 `evidence_ref` 与同一证据号不一致：输出 blocked。
- 输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary 和 fail-closed flags，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_result_reconciliation_not_proven` 只表示 Docker/local software proof 足以复账同一 `evidence_ref` 的八类结果材料摘要，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.14 Route Task Field Retest Result Acceptance Packet

result reconciliation 之后，可以运行 PC-side acceptance packet gate，把上一轮 `route_task_field_retest_result_reconciliation` 的 artifact / summary 转成现场验收包：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py \
  --reconciliation-json /tmp/route_task_field_retest_result_reconciliation.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_acceptance_packet.json \
  --summary-output /tmp/route_task_field_retest_result_acceptance_packet_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_result_acceptance_packet.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_acceptance_packet_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、safe lineage、八类 required result materials、missing items、mismatch reasons、owner handoff、rerun commands、pass/fail criteria、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

acceptance packet 必须看到八类现场复测结果材料摘要：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。它只读取 reconciliation artifact / summary / wrapper / nested JSON 的白名单字段，不读取 raw handoff artifact，不访问 ROS graph、Nav2 runtime、真实日志文件内容、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。pass/fail criteria 只是下一次现场复测验收口径，不是本轮结果通过结论。

保守阻断规则：

- 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 reconciliation 已存在。
- 输入 schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 上游 reconciliation status 不是 `ready_for_field_retest_result_reconciliation_not_proven`：输出 blocked，不把未 ready 复账推进成 acceptance packet ready。
- 任一 result material 缺失、placeholder、同证据号不一致，或输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary / safe copy，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_result_acceptance_packet_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate` 已把现场结果验收包整理清楚，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.9.15 Route Task Field Retest Result Acceptance Backfill

acceptance packet 之后，可以运行 PC-side backfill gate，把上一轮 `route_task_field_retest_result_acceptance_packet` 的 artifact / summary 与 `--material-dir` 中八类回填材料做同证据号对齐检查：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py \
  --acceptance-packet-json /tmp/route_task_field_retest_result_acceptance_packet_summary.json \
  --material-dir /tmp/route_task_field_retest_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_acceptance_backfill.json \
  --summary-output /tmp/route_task_field_retest_result_acceptance_backfill_summary.json
```

artifact 使用 `schema=trashbot.route_task_field_retest_result_acceptance_backfill.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、source acceptance packet 摘要、八类 `material_states`、`material_completeness`、same-evidence-ref alignment、missing/rejected material categories、owner handoff、rerun commands、pass/fail decision inputs、`safe_copy`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

acceptance backfill 必须看到八类回填材料：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。它只读取 acceptance packet artifact / summary / wrapper / nested JSON 的白名单字段，并按 material pack 的安全规则扫描 `--material-dir`；它不读取 raw upstream artifact，不访问真实 Nav2 runtime、真实 fixed-route runtime、真实日志内容、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。

保守阻断规则：

- source 缺失、JSON 不可读或不是 JSON object：输出 blocked，不猜测 acceptance packet 已存在。
- source schema 或 evidence boundary 不支持：输出 blocked。
- 缺 safe `evidence_ref`、与 `--evidence-ref` 不一致或 `same_evidence_ref_required` 不是严格 true：输出 blocked。
- 上游 acceptance packet status 不是 `ready_for_field_retest_result_acceptance_packet_not_proven`：输出 blocked，不把未 ready packet 推进成 backfill ready。
- 任一回填材料缺失、placeholder、同证据号不一致、或输入含 unsafe copy、raw path、credential、ROS topic、serial/UART、WAVE ROVER detail、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true`：输出 blocked。

`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只能消费白名单 summary / safe copy，不展示 raw artifact、本机路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。`ready_for_field_retest_result_acceptance_backfill_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate` 已把 packet 后的八类材料回填入口复账清楚，不是真实 fixed-route/Nav2、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## 4.10 Mobile Field Material Intake

现场前检查完成后，`pc-tools/evidence/mobile_field_material_intake.py` 负责把手机设备观察、route/elevator 材料、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status 收到同一条 `evidence_ref` 证据链里：

```bash
python3 pc-tools/evidence/mobile_field_material_intake.py \
  --precheck-json /tmp/mobile_route_elevator_field_device_precheck_summary.json \
  --device-pwa-observation-json /tmp/device_pwa_observation.json \
  --route-elevator-field-materials-json /tmp/route_elevator_field_materials.json \
  --nav2-fixed-route-runtime-log-json /tmp/nav2_fixed_route_runtime_log.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_completion_signal.json \
  --dropoff-cancel-material-status-json /tmp/dropoff_cancel_material_status.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

summary 使用 `schema=trashbot.mobile_field_material_intake_summary.v1`，证据边界固定为 `software_proof_docker_mobile_field_material_intake_gate`。它只做现场材料回填前/回填后的 fail-closed 检查：所有 required material 都必须是 JSON object、带同一 safe `evidence_ref`、不含 placeholder、不含 unsafe copy、不含 success wording，且保持 `delivery_success=false`、`primary_actions_enabled=false`。

该 gate 的 route/elevator 检查重点是材料是否可复核，而不是判断现场已经成功。必须继续把 `route_elevator_field_pass=false`、`nav2_fixed_route_completed=false`、`dropoff_completion=false`、`cancel_completion=false` 和 `not_proven` 暴露给 mobile/support。缺真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、HIL 或 Objective 5 external proof 时，summary 只能作为 `software_proof` / `not_proven`，不证明真实手机或真实送达成功。

## 4.11 Mobile Field Material Review Decision

`mobile_field_material_intake` 输出后，`pc-tools/evidence/mobile_field_material_review_decision.py` 负责把同一条 `evidence_ref` 的 intake 状态转换成可执行的 owner handoff 和 next-required-evidence：

```bash
python3 pc-tools/evidence/mobile_field_material_review_decision.py \
  --intake-json /tmp/mobile_field_material_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

review artifact 使用 `schema=trashbot.mobile_field_material_review_decision.v1`，summary 使用 `schema=trashbot.mobile_field_material_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_mobile_field_material_review_decision_gate`。核心字段包括：

- `review_decision`: `blocked_missing_real_phone_or_pwa_observation`、`blocked_missing_route_elevator_field_materials`、`blocked_missing_nav2_or_fixed_route_runtime_log`、`blocked_missing_same_evidence_ref_task_record_or_completion_signal`、`blocked_missing_dropoff_or_cancel_completion`、`ready_for_owner_handoff_not_proven` 或 fail-closed `blocked_invalid_intake`。
- `owner handoff` / `owner_handoff`: 只映射到 `Full-stack`、`Robot`、`Autonomy` 或 `Product closeout`。
- `next-required-evidence` / `next_required_evidence`: 说明下一步要补真实手机/PWA observation、route/elevator 材料、Nav2/fixed-route runtime log、同 ref task record/completion signal、dropoff/cancel completion material，或进入 Product closeout 复核。
- `blocked_materials`: 保留材料 name、状态、owner 和紧凑原因，不复制 raw artifact、本机路径、凭证、ROS topic 或硬件传输细节。
- `not_proven`: 继续列出真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery_success、HIL、WAVE ROVER/UART 和 Objective 5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: review decision 不能放行 Start/Confirm Dropoff/Cancel，也不能声明送达成功。

`ready_for_owner_handoff_not_proven` 只表示 intake 材料形状、same `evidence_ref` 和 safety boundary 已足够交给 owner 复核。它不是真实手机设备验收、真实 route/elevator field pass、真实 Nav2/fixed-route 实跑、真实路线采集、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。缺 intake、坏 JSON、unsupported schema/boundary、缺 `evidence_ref`、same-evidence-ref mismatch、placeholder、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或 success wording 时，都必须保持 blocked review，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## 4.12 Mobile Field Material Retest Request

`mobile_field_material_review_decision` 输出后，`pc-tools/evidence/mobile_field_material_retest_request.py` 负责把 review artifact/summary 转成下一次 route/elevator field retest request：

```bash
python3 pc-tools/evidence/mobile_field_material_retest_request.py \
  --review-json /tmp/mobile_field_material_review_decision.json \
  --output /tmp/mobile_field_material_retest_request.json \
  --summary-output /tmp/mobile_field_material_retest_request_summary.json
```

retest request artifact 使用 `schema=trashbot.mobile_field_material_retest_request.v1`，summary 使用 `schema=trashbot.mobile_field_material_retest_request_summary.v1`，证据边界固定为 `software_proof_docker_mobile_field_material_retest_request_gate`。核心字段包括：

- `request_verdict`: `ready_for_route_elevator_field_retest_request_not_proven`、`blocked_mobile_field_material_review_not_ready`、`blocked_invalid_mobile_field_material_review`、`blocked_unsafe_copy` 或 `blocked_success_or_control_claim`。
- `route/elevator material checklist` / `route_elevator_material_checklist`: 下一轮复测材料清单，覆盖 device/PWA observation、route/elevator materials、Nav2/fixed-route runtime log、task record、completion signal 和 dropoff/cancel material status。
- `next_required_evidence` / `next-required-evidence`: 只说明下一步要补哪些同 `evidence_ref` 材料和重跑哪些 PC gate，不给机器人动作命令。
- `same_evidence_ref_required=true`: review、retest request 和下一轮 material checklist 必须沿用同一条 `evidence_ref`，不能拼接不同 run 的材料。
- `not_proven`: 继续列出真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 和 Objective 5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: retest request 不能放行 Start/Confirm Dropoff/Cancel，也不能声明送达成功。

`ready_for_route_elevator_field_retest_request_not_proven` 只表示上一轮 mobile review decision 足够生成 route/elevator material checklist 和复测请求。它不是真实 route/elevator、真实 Nav2/fixed-route、真实路线采集、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。缺 review、坏 JSON、unsupported schema/boundary、弱类型 `same_evidence_ref_required`、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或 success wording 时，都必须保持 blocked request，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

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

### 5.6 route/task rehearsal operator review

当 execution bundle 已经生成，需要把本轮软件排练转成操作员复盘/下一轮重跑决策时，使用 operator review 生成器：

```bash
python3 pc-tools/evidence/route_task_rehearsal_operator_review.py \
  --execution-bundle /tmp/route_task_rehearsal_bundle/route_task_rehearsal_execution_bundle.json \
  --output-dir /tmp/route_task_rehearsal_review
```

输出 `route_task_rehearsal_operator_review.json`，schema 为 `trashbot.route_task_rehearsal_operator_review.v1`，证据边界为 `software_proof_docker_route_task_rehearsal_operator_review_gate`。该工具只读 execution bundle JSON，不读取硬件、不访问 serial/UART、不触发 Nav2/ROS graph/网络；即使 execution bundle missing、read_error 或 unsupported schema，也会写出 blocked review package，便于复盘链路保留材料。

review 顶层包含 `crosscheck_status`、`hil_alignment_status`、`mismatch_summary`、`next_rehearsal_decision`、`not_proven`、`safe_copy`、`primary_actions_enabled=false` 和 `delivery_success=false`。`next_rehearsal_decision` 的分支规则固定为：crosscheck pass 且 HIL not_proven 时准备真实路线/任务材料或真实 HIL 上车复账；crosscheck fail 时先修 route status/task record mismatch 后重跑；missing/read_error/unsupported schema 时重建 execution bundle；safe copy whitelist 失败时先修摘要白名单。`safe_copy` 只允许固定摘要，不包含 artifact/raw path、本机绝对路径、凭证、ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum 或 complete artifact。该 package 仍不能声明真实 fixed-route、真实 HIL、dropoff/cancel completion 或 delivery success。

### 5.7 route/task field-run readiness handoff

下一次真实路线-任务联跑前，需要把 PC route debug console summary、operator review 和 execution bundle 合成同一 `evidence_ref` 的 readiness handoff：

```bash
python3 pc-tools/evidence/route_task_field_run_readiness.py \
  --pc-route-debug /tmp/pc_route_debug_console.json \
  --operator-review /tmp/route_task_rehearsal_operator_review.json \
  --execution-bundle /tmp/route_task_rehearsal_execution_bundle.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 summary 使用 `schema=trashbot.route_task_field_run_readiness.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_readiness_gate`。顶层固定包含 `same_evidence_ref_required=true`、`source_materials`、`required_field_run_materials`、`missing_materials`、`commands_to_run`、`phone_support_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

同一 `evidence_ref` field-run material chain 必须至少包含：route status JSON、task record JSON、PC route debug summary、route_task operator review、execution bundle、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary。`overall_status=ready_for_field_run_materials` 只表示 Docker/local handoff 材料可读、schema 可支持、同 `evidence_ref` 可对齐且 safe summary 可分享；它不表示真实 Nav2/fixed-route 实跑、真实路线采集、WAVE ROVER 运动、真实 serial/UART feedback、真实 HIL、dropoff/cancel completion、delivery success 或 Objective 5 外部云/4G/OSS/CDN/DB/queue proof。

缺任何输入文件、JSON 不可读、unsupported schema、source materials 不同 `evidence_ref` 或 phone/support-safe copy 命中敏感词时，readiness gate 必须输出 blocked/not_proven。该 CLI 不读取 ROS graph、不调用 Nav2、不访问 serial/UART、不暴露 `/cmd_vel`、baudrate、WAVE ROVER 参数、本机完整路径、traceback、checksum、complete artifact 或 raw robot response。

### 5.8 route/task field-run intake crosscheck

真实路线-任务联跑材料回到 PC 后，先用 intake crosscheck 做同一 `evidence_ref` 的软件复账：

```bash
python3 pc-tools/evidence/route_task_field_run_intake.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --runtime-log-json /tmp/runtime_log.json \
  --robot-side-task-evidence-json /tmp/robot_evidence.json \
  --support-safe-mobile-summary-json /tmp/mobile_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 summary 使用 `schema=trashbot.route_task_field_run_intake_crosscheck.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_intake_crosscheck_gate`。顶层固定包含 `same_evidence_ref_required=true`、`source_materials`、`missing_materials`、`mismatch_reasons`、`commands_to_rerun`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`overall_status=ready_for_review` 只表示五份 Docker/local JSON 材料可读、schema 支持、同一 `evidence_ref` 对齐且 phone-safe 摘要可展示。它不表示真实 Nav2/fixed-route 实跑、真实路线采集、WAVE ROVER 运动、真实 serial/UART feedback、真实 HIL、dropoff/cancel completion、cancel completion、delivery success 或 Objective 5 外部云/4G/OSS/CDN/DB/queue proof。

保守阻断规则：

- 任一材料缺失、JSON 不可读或不是 JSON object：`overall_status=blocked_missing_material`，`missing_materials` 写明来源。
- 任一材料 schema 不支持：`overall_status=blocked_unsupported_schema`。
- 任一材料的 `evidence_ref` 与目标 run 不一致：`overall_status=blocked_mismatch`，`mismatch_reasons` 写明来源。
- support-safe mobile summary 命中凭证、raw ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response：`overall_status=blocked_unsafe_summary`。

该 gate 仍是 software proof。它用于把现场五份材料变成可复盘入口和重跑清单，不触发 Nav2、不访问硬件、不放行手机主操作，也不能写成真实 fixed-route、真实 HIL、投放完成、取消完成或送达成功。

### 5.9 route/task field-run reconciliation

execution pack 生成后，最终复账必须把 execution pack 与 intake/review 材料重新锁定到同一 `evidence_ref`：

```bash
python3 pc-tools/evidence/route_task_field_run_reconciliation.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --intake-json /tmp/route_task_field_run_review.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 summary 使用 `schema=trashbot.route_task_field_run_reconciliation.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_reconciliation_gate`。顶层固定包含 `same_evidence_ref_required=true`、`reconciliation_verdict`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

保守阻断规则：

- execution pack 缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当成复账证据。
- intake/review 缺失、JSON 不可读或不是 JSON object：输出 blocked，并要求先重跑 intake/review。
- 任一输入 schema 或 evidence boundary 不支持：输出 `blocked_unsupported_schema` 或 `blocked_unsupported_boundary`。
- 任一输入缺 `evidence_ref` 或与 `--evidence-ref` 不一致：输出 `blocked_missing_evidence_ref` 或 `blocked_evidence_ref_mismatch`。
- phone-safe summary 命中凭证、raw ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response：输出 `blocked_unsafe_summary`。
- intake/review 仍有 missing materials 或 mismatch：输出 blocked，并把 `operator_next_steps` 指向补采、统一 `evidence_ref` 和重跑顺序。

该 gate 仍是 software proof。它用于把 execution pack、intake/review 和 phone-safe summary 串成可观测复账入口，不触发 Nav2、不访问硬件、不放行手机主操作，也不能写成真实 fixed-route、真实 HIL、投放完成、取消完成或送达成功。

### 5.10 route/task completion signal

reconciliation 之后，completion signal 把 route status/replay、task record 状态机、上一轮 reconciliation/review/intake summary，以及可选 dropoff/cancel completion material 汇总成 diagnostics/mobile 可读的只读完成信号：

```bash
python3 pc-tools/evidence/route_task_completion_signal.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-summary-json /tmp/route_task_field_run_reconciliation.json \
  --dropoff-completion-json /tmp/dropoff_completion.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

取消/失败分支可把 `--dropoff-completion-json` 换成 `--cancel-completion-json`。输出 summary 使用 `schema=trashbot.route_task_completion_signal.v1`，证据边界固定为 `software_proof_docker_route_task_completion_signal_gate`。顶层固定包含 `same_evidence_ref_required=true`、`completion_verdict`、`fixed_route_summary`、`task_record_summary`、`state_transition_summary`、`dropoff_completion`、`cancel_completion`、`failure_reason`、`recovery_reason`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

保守阻断规则：

- route status/replay、task record 或 completion summary 缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当完成信号。
- 任一输入 schema 不支持：输出 `blocked_unsupported_schema`。
- 任一已加载材料缺 `evidence_ref` 或与 `--evidence-ref` 不一致：输出 `blocked_mismatch_evidence_ref` 或缺材料 blocked。
- phone-safe summary 命中凭证、raw ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response：输出 `blocked_unsafe_phone_summary`。
- 任一输入含 `delivery_success=true`：输出 `blocked_delivery_success_claim`，继续强制 `delivery_success=false`。
- task record 状态机进入 dropoff/cancel 分支但缺对应 `dropoff_completion` / `cancel_completion` material：输出 `blocked_missing_completion_materials`。

该 gate 仍是 software proof。`completed_not_proven` 只表示 Docker/local 材料形状足够进入人工复核，不触发 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；它不是真实 delivery、真实 dropoff/cancel completion、真实 fixed-route/Nav2、真实路线采集、HIL、真实手机设备或 Objective 5 external proof。

### 5.10.1 route/task terminal completion rehearsal

completion signal 之后，PC/operator 可以用 terminal completion rehearsal 把 route status、task record、既有 `route_task_completion_signal` 和可选 dropoff/cancel material summary 复账成 Robot/mobile 可读的终态摘要：

```bash
python3 pc-tools/evidence/route_task_terminal_completion_rehearsal.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_task_completion_signal.json \
  --dropoff-material-json /tmp/dropoff_completion.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

取消/失败分支可把 `--dropoff-material-json` 换成 `--cancel-material-json`。输出 artifact 使用 `schema=trashbot.route_task_terminal_completion_rehearsal.v1`，summary 使用 `schema=trashbot.route_task_terminal_completion_rehearsal_summary.v1`，证据边界固定为 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`。顶层固定包含 `same_evidence_ref_required=true`、`terminal_verdict`、`route_status_summary`、`task_record_summary`、`completion_signal_summary`、`dropoff`、`cancel`、`failure_reason`、`recovery_reason`、`materials_status`、`operator_next_steps`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

保守阻断规则：

- route status、task record 或 completion signal 缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当终态复账通过。
- 任一输入 schema 或 completion signal evidence boundary 不支持：输出 blocked。
- 任一已加载材料缺 `evidence_ref` 或与 `--evidence-ref` 不一致：输出 `blocked_mismatch_evidence_ref` 或缺材料 blocked。
- phone/support/operator copy 命中凭证、raw path、raw ROS topic、serial/UART、baudrate、WAVE ROVER、HIL、traceback、checksum、complete artifact、raw robot response 或成功文案：输出 `blocked_unsafe_copy`。
- 任一输入含 `delivery_success=true` 或 `primary_actions_enabled=true`：输出 `blocked_success_or_control_claim`，继续强制 `delivery_success=false` 与 `primary_actions_enabled=false`。
- task record 状态机进入 dropoff/cancel 分支但缺对应 `dropoff` / `cancel` material：输出 `blocked_missing_route_task_terminal_completion_rehearsal`。

该 gate 仍是 software proof。`ready_for_terminal_completion_rehearsal_not_proven` 只表示 Docker/local 终态复账材料形状足够进入 Robot diagnostics、mobile 只读面板或下一轮现场复核；它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G，也不证明真实 dropoff/cancel completion、delivery success、HIL、真实手机设备或 Objective 5 external proof。

### 5.10.2 route/task terminal review decision

terminal completion rehearsal 之后，PC/operator 可以用 review decision gate 把终态复账结果整理成下一轮 operator decision、owner 交接和 field retest 请求清单：

```bash
python3 pc-tools/evidence/route_task_terminal_review_decision.py \
  --terminal-rehearsal-json /tmp/route_task_terminal_completion_rehearsal.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.route_task_terminal_review_decision.v1`，summary 使用 `schema=trashbot.route_task_terminal_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_terminal_review_decision_gate`。顶层固定包含 `same_evidence_ref_required=true`、`review_decision`、`decision_reason`、`owner_handoff`、`next_required_evidence`、`field_retest_request_guidance`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`software_proof`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

保守阻断规则：

- terminal rehearsal 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不生成 field retest 请求。
- 输入 schema 或 evidence boundary 不支持：输出 `blocked_unsupported_schema`。
- 输入缺 safe `evidence_ref` 或与 `--evidence-ref` 不一致：输出 `blocked_mismatch_evidence_ref`。
- phone/support/operator copy 命中凭证、raw path、raw ROS topic、serial/UART、baudrate、WAVE ROVER、HIL、traceback、checksum、complete artifact、raw robot response 或成功文案：输出 `blocked_unsafe_copy`。
- 输入含 `delivery_success=true` 或 `primary_actions_enabled=true`：输出 `blocked_success_or_control_claim`，继续强制 `delivery_success=false` 与 `primary_actions_enabled=false`。
- 上一轮 terminal rehearsal 仍是 blocked 或缺 recovery reason：只输出 repair guidance，不进入 field retest request guidance。

该 gate 仍是 software proof。`ready_for_operator_terminal_review_not_proven` 只表示 Docker/local 终态复账材料足够让 operator 做 review decision、owner handoff 和下一轮 field retest request guidance；它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G，也不证明真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success、HIL、真实手机设备或 Objective 5 external proof。

### 5.10.3 route/task field retest execution pack

terminal review decision 之后，下一次真实现场复测还需要一份可直接交给现场同学的 execution pack。`pc-tools/evidence/route_task_field_retest_execution_pack.py` 只读上一轮 `route_task_terminal_review_decision` artifact、summary 或 wrapper/nested JSON，输出复测材料清单、复跑命令、owner handoff 和检查表：

```bash
python3 pc-tools/evidence/route_task_field_retest_execution_pack.py \
  --review-decision-json /tmp/route_task_terminal_review_decision.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_execution_pack.v1`，summary 使用 `schema=trashbot.route_task_field_retest_execution_pack_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_execution_pack_gate`。顶层固定包含 `same_evidence_ref_required=true`、safe `evidence_ref`、`required_field_materials`、`rerun_commands`、`operator_handoff`、`field_retest_checklist`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`required_field_materials` 至少包括真实 Nav2/fixed-route runtime log、route completion signal、task record、operator field note 和 mobile/diagnostics safe summary。source review decision 只要提到 elevator，就必须额外回填 door state、target floor confirmation 和 human assistance note，继续沿用同一 `evidence_ref`。

保守阻断规则：

- terminal review decision 输入缺失、JSON 不可读或不是 JSON object：输出 blocked，不生成 ready 复测包。
- 输入 schema 或 evidence boundary 不支持：输出 `blocked_unsupported_schema`。
- 输入缺 safe `evidence_ref`：输出 `blocked_missing_evidence_ref`。
- 输入声明 `same_evidence_ref_required=false` 或与 `--evidence-ref` 不一致：输出 blocked，必须先对齐同一证据主键。
- phone/support/operator copy 命中凭证、raw path、raw ROS topic、serial/UART、baudrate、WAVE ROVER、HIL pass、traceback、checksum、complete artifact、raw robot response 或成功文案：输出 `blocked_unsafe_copy`。
- 输入含 `delivery_success=true`、`primary_actions_enabled=true`、field pass 或 control claim：输出 `blocked_success_or_control_claim`，继续强制 `delivery_success=false` 与 `primary_actions_enabled=false`。

该 gate 仍是 software proof。`ready_for_field_retest_execution_pack_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_execution_pack_gate` 已把上一轮 review decision 转成 Objective 2 / Objective 3 现场复测准备包；它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G，也不证明真实 field pass、真实 Nav2/fixed-route、真实手机/browser、delivery success、HIL 或 Objective 5 external proof。

### 5.10.4 elevator route evidence reconciliation

电梯 rehearsal evidence 进入 Robot dry-run 主链路后，route/task completion signal 还需要与它按同一 `evidence_ref` 复账，避免电梯阶段材料和路线完成信号来自不同 run：

```bash
python3 pc-tools/evidence/elevator_route_evidence_reconciliation.py \
  --elevator-json /tmp/elevator_assist_rehearsal_evidence.json \
  --route-completion-json /tmp/route_task_completion_signal.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.elevator_route_evidence_reconciliation.v1`，summary 使用 `schema=trashbot.elevator_route_evidence_reconciliation_summary.v1`，证据边界固定为 `software_proof_docker_elevator_route_evidence_reconciliation_gate`。顶层固定包含 `source=software_proof`、`same_evidence_ref_required=true`、`same_evidence_ref_status`、`reconciliation_verdict`、`source_states`、`elevator_rehearsal_summary`、`route_completion_summary`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

保守阻断规则：

- elevator rehearsal evidence 或 route completion signal 缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当复账通过。
- 任一输入 schema、evidence boundary 或 `source=software_proof` 边界不支持：输出 blocked。
- 任一输入缺 `evidence_ref` 或与 `--evidence-ref` 不一致：输出 `blocked_missing_evidence_ref` 或 `blocked_evidence_ref_mismatch`。
- phone-safe summary 命中凭证、raw ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response：输出 `blocked_unsafe_copy`。
- 任一输入含 `delivery_success=true`、`primary_actions_enabled=true`、`hil_pass=true` 或完成/成功文案：输出 blocked，并继续强制 `delivery_success=false` 与 `primary_actions_enabled=false`。

该 gate 仍是 software proof。`reconciled_not_proven` 只表示 Docker/local 电梯 rehearsal evidence 与 route completion signal 的材料形状、同一 `evidence_ref` 和安全摘要可进入人工复核；它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、硬件、外部云、OSS/CDN、DB/queue 或 4G，也不证明真实 fixed-route/Nav2、真实路线采集、HIL、dropoff/cancel completion、手机设备现场验收或 delivery success。

### 5.10.3 mobile route/elevator field-device precheck

真实设备和 route/elevator 现场开始前，使用 PC helper 把上一轮 route/elevator field-session handoff 转成 phone-safe precheck summary：

```bash
python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py \
  --route-elevator-handoff-json /tmp/route_elevator_field_session_handoff.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

需要复核 mobile/web 或 diagnostics 已消费的 summary 时，可改用：

```bash
python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py \
  --precheck-json /tmp/mobile_route_elevator_field_device_precheck_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.mobile_route_elevator_field_device_precheck.v1`，summary 使用 `schema=trashbot.mobile_route_elevator_field_device_precheck_summary.v1`，copy/export 白名单使用 `schema=trashbot.mobile_route_elevator_field_device_precheck_copy.v1`；证据边界固定为 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`。顶层固定包含 `source=software_proof`、`same_evidence_ref_required=true`、`route_elevator_handoff_summary`、`required_route_elevator_field_materials`、`device_pwa_observation_checklist`、`mobile_copy_summary`、`not_proven`、`real_device_observed=false`、`pwa_install_prompt_observed=false`、`route_elevator_field_pass=false`、`dropoff_completion=false`、`cancel_completion=false`、`delivery_success=false` 和 `primary_actions_enabled=false`。

`required_route_elevator_field_materials` 是现场前检查清单，不是材料已通过证明；它要求同一 `evidence_ref` 后续回填 Nav2/fixed-route runtime log、route status、route completion signal、task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 和 diagnostics mobile-safe summary。`device_pwa_observation_checklist` 要求真实设备现场记录浏览器加载、viewport/touch target、PWA install prompt/user choice、route/elevator precheck panel 可见、copy/export 白名单和主操作 disabled 状态。

保守阻断规则：

- route/elevator handoff 缺失、JSON 不可读或不是 JSON object：输出 blocked，不把异常当 precheck 通过。
- handoff schema、evidence boundary 或 `source=software_proof` 边界不支持：输出 blocked。
- handoff `evidence_ref` 与 `--evidence-ref` 不一致：输出 `blocked_evidence_ref_mismatch`，要求重新统一 same-evidence-ref。
- phone-safe copy 命中凭证、raw ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum、complete artifact 或 raw robot response：输出 blocked。
- 任一输入或被校验 summary 含 `real_device_observed=true`、`pwa_install_prompt_observed=true`、`route_elevator_field_pass=true`、`dropoff_completion=true`、`cancel_completion=true`、`delivery_success=true`、`primary_actions_enabled=true`、`hil_pass=true` 或完成/成功文案：输出 blocked，并继续强制 `delivery_success=false` 与 `primary_actions_enabled=false`。

该 gate 仍是 software proof。`ready_for_field_device_precheck_not_proven` 或 `validated_field_device_precheck_not_proven` 只表示 Docker/local handoff 能生成真实设备/route/elevator 现场前检查 summary；它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、真实手机、外部云、OSS/CDN、DB/queue 或 4G，也不证明真实设备行为、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 dropoff/cancel completion、真实 delivery success、HIL 或 Objective 5 external proof。

### 5.11 route/task field-run console

completion signal 之后，PC/operator 还需要一份可直接查看的现场运行准备 console。`pc-tools/evidence/route_task_field_run_console.py` 只读 execution pack、route status/replay、task record 和 completion signal，生成现场准备计划、采集清单、same `evidence_ref` verdict、robot diagnostics 只读摘要和 mobile readonly 摘要：

```bash
python3 pc-tools/evidence/route_task_field_run_console.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_task_completion_signal.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.route_task_field_run_console.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_console_gate`。顶层固定包含 `schema_version=1`、`same_evidence_ref_required=true`、`console_verdict`、`field_run_plan`、`capture_checklist`、`execution_pack_summary`、`route_status_summary`、`task_record_summary`、`completion_signal_summary`、`dropoff_completion`、`cancel_completion`、`operator_next_steps`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`field_run_materials_prepared_not_proven` 只表示 Docker/local console 已把同一 `evidence_ref` 的四份材料整理成 operator-facing 计划和采集模板。它不表示真实 Nav2/fixed-route 已运行，不表示真实路线采集、WAVE ROVER 运动、真实 serial/UART feedback、真实 HIL、真实 dropoff/cancel completion、delivery success、真实手机设备或 Objective 5 外部云/4G/OSS/CDN/DB/queue proof。

该 CLI 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G。缺 execution pack、route status、task record 或 completion signal、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true` 或输入含 `delivery_success=true` 时，console 必须 fail closed，并保留 `not_proven`、`primary_actions_enabled=false`、`delivery_success=false` 和修复用的 `operator_next_steps`。

### 5.12 route/task field-run evidence kit

console 生成后，现场同学还需要一份可以按目录执行和回填的证据包。`pc-tools/evidence/route_task_field_run_evidence_kit.py` 只读上一轮 console JSON，并可选检查 PC 侧材料目录：

```bash
python3 pc-tools/evidence/route_task_field_run_evidence_kit.py \
  --console-json /tmp/route_task_field_run_console.json \
  --material-dir /tmp/route_task_field_run_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

evidence kit artifact 使用 `schema=trashbot.route_task_field_run_evidence_kit.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_evidence_kit_gate`。核心字段包括：

- `material_directory_manifest`: 现场材料目录 manifest，检查 `route_task_field_run_console.json`、`route_status.json`、`task_record.json`、`completion_signal.json`、`operator_notes.md`、`robot_diagnostics_summary.json` 和 `mobile_readonly_summary.json` 是否齐全。
- `capture_templates`: route status、task record、completion signal 和 operator notes 的回填模板；所有模板都要求 `same_evidence_ref_required=true`。
- `commands_to_run` / `commands_to_rerun`: 给 PC/operator 的生成、补采和重跑命令清单，不触发 ROS graph、Nav2、硬件或手机控制动作。
- `evidence_kit_verdict`: `field_run_evidence_kit_ready_not_proven` 或 blocked 分支，覆盖缺 console、坏 JSON、unsupported schema、`evidence_ref` mismatch、缺材料、unsafe summary、越界 action/success 声明。
- `operator_handoff`: 给现场同学的只读交接步骤。
- `robot_diagnostics_summary` 与 `mobile_readonly_summary`: 只读摘要，固定 `primary_actions_enabled=false` 与 `delivery_success=false`。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、WAVE ROVER 运动、真实 serial/UART feedback、HIL、真实 dropoff/cancel completion、真实手机设备和 Objective 5 external proof 未证明。

`field_run_evidence_kit_ready_not_proven` 只表示 Docker/local evidence kit 已把上一轮 console 和材料目录整理成现场执行/回填包。它不是实机 field run、不是 HIL、不是真实 dropoff/cancel completion，也不是 delivery success。任何缺材料或安全/同 ref 约束失败都必须先修复并重跑 evidence kit，不得把 evidence kit 当作完成信号。

### 5.13 route/task field-run material bundle

evidence kit 之后，现场同学还需要一份可直接打开和回填的材料目录。`pc-tools/evidence/route_task_field_run_material_bundle.py` 只读上一轮 `trashbot.route_task_field_run_evidence_kit.v1`，生成 `trashbot.route_task_field_run_material_bundle.v1` summary；指定 `--material-dir` 时创建 route/task/completion/operator notes/diagnostics/mobile summary 的模板或占位文件：

```bash
python3 pc-tools/evidence/route_task_field_run_material_bundle.py \
  --evidence-kit-json /tmp/route_task_field_run_evidence_kit.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

material bundle 使用 `evidence_boundary=software_proof_docker_route_task_field_run_material_bundle_gate`。核心字段包括：

- `same_evidence_ref_required=true`: bundle、diagnostics/mobile summary 和所有模板必须沿用同一个 safe `evidence_ref`。
- `material_directory_scaffold`: 记录模板文件创建或保留状态，不覆盖现场已有 notes。
- `material_bundle_summary`: `schema=trashbot.route_task_field_run_material_bundle_summary.v1` 的只读消费摘要。
- `operator_next_steps`: 现场回填 route status、task record、completion material、diagnostics/mobile summary 和 operator notes 的下一步。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、真实硬件反馈、HIL、dropoff/cancel completion、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: material bundle 不能放行控制动作，也不能声明送达成功。

`field_run_material_bundle_ready_not_proven` 只表示 Docker/local software proof 的材料包生成能力已经可用。它不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G；它不是真实 fixed-route/Nav2、真实路线采集、真实投放、真实取消完成、HIL 或 delivery success。缺 evidence kit、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true`、输入含 `delivery_success=true` 或目录不可写时，都必须保持 blocked material bundle，再重建同一 `evidence_ref` 的 evidence kit 或换可写材料目录。

### 5.14 route/task field-run material validation

material bundle 生成目录后，真实现场材料回填前还需要一个 PC 侧 validation gate，把“模板已生成”变成“材料状态可检查”。`pc-tools/evidence/route_task_field_run_material_validation.py` 只读 `trashbot.route_task_field_run_material_bundle.v1` 和 `--material-dir`，不会访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/route_task_field_run_material_validation.py \
  --material-bundle-json /tmp/route_task_field_run_material_bundle.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

validation artifact 使用 `schema=trashbot.route_task_field_run_material_validation.v1`，证据边界固定为 `software_proof_docker_route_task_field_run_material_validation_gate`。核心字段包括：

- `source_material_bundle`: 只暴露上一轮 bundle schema、boundary、verdict 和 safe `evidence_ref`，不复制完整 raw artifact。
- `material_directory_status`: 检查 `route_status_template.json`、`task_record_template.json`、`completion_material_template.json`、`operator_notes.md`、`robot_diagnostics_summary_template.json` 和 `mobile_readonly_summary_template.json` 是否存在、可读、非占位模板、同 `evidence_ref` 且不含 unsafe copy。
- `material_validation_summary`: `schema=trashbot.route_task_field_run_material_validation_summary.v1` 的只读消费摘要，给 Robot diagnostics 和 mobile/web 展示。
- `missing_materials` / `placeholder_materials` / `mismatch_reasons`: 指向现场应补采、替换模板或统一 `evidence_ref` 的具体文件。
- `not_proven`: 继续列出真实 Nav2/fixed-route、真实路线采集、真实硬件反馈、HIL、dropoff/cancel completion、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: validation 只说明材料状态，不放行控制动作，也不声明送达成功。

`field_run_material_validation_ready_not_proven` 只表示 Docker/local material validation 通过，可以进入后续 intake/review 或现场复账。它不是真实 fixed-route/Nav2、真实路线采集、真实投放、真实取消完成、HIL、真实手机/browser 或 delivery success。缺 material bundle、坏 JSON、unsupported schema/boundary、缺材料、模板未替换、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true` 或输入含 `delivery_success=true` 时，都必须保持 blocked validation，并按 `operator_next_steps` 补材料或重建同一 `evidence_ref` 的 bundle。

### 5.15 elevator assisted delivery field material validation

电梯 assisted delivery 的现场复账在 route/task 材料之外还需要门状态、目标楼层确认和人工协助记录。`pc-tools/evidence/elevator_field_run_material_validation.py` 只读 PC 侧材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/elevator_field_run_material_validation.py \
  --material-dir /tmp/elevator_field_run_materials \
  --evidence-ref elevator-run-001 \
  --once-json
```

validation artifact 使用 `schema=trashbot.elevator_field_run_material_validation.v1`，证据边界固定为 `software_proof_docker_elevator_field_material_validation_gate`。目录内至少需要 `door_state.json`、`target_floor_confirmation.json`、`human_assistance_operator_note.md`、`nav2_fixed_route_runtime_log.json`、`task_record.json`、`completion_signal.json` 和 `diagnostics_mobile_safe_summary.json`。

`elevator_field_material_validation_ready_not_proven` 只表示七类现场材料的文件形状、同一 `evidence_ref` 和安全摘要可进入人工复核。它不是真实电梯门状态、真实目标楼层确认、真实 Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL、真实投放、真实取消完成或 delivery success。缺失、模板、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须保持 blocked validation，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

### 5.16 elevator assisted delivery field review decision

validation artifact 通过或 blocked 后，还需要一层 operator review decision，把材料状态转成复跑命令和采集清单。`pc-tools/evidence/elevator_field_run_review.py` 只读上一轮 validation artifact/summary，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/elevator_field_run_review.py \
  --validation-json /tmp/elevator_field_run_material_validation.json \
  --once-json
```

review artifact 使用 `schema=trashbot.elevator_field_run_review.v1`，summary 使用 `schema=trashbot.elevator_field_run_review_summary.v1`，证据边界固定为 `software_proof_docker_elevator_field_review_decision_gate`。核心字段包括：

- `review_decision`: `ready_for_controlled_elevator_field_rehearsal_not_proven`、`blocked_missing_materials`、`blocked_template_materials`、`blocked_evidence_ref_mismatch`、`blocked_unsafe_copy`、`blocked_success_claim` 或 `blocked_invalid_validation`。
- `blocked_categories`: 给 diagnostics/mobile 展示的紧凑原因。
- `operator_next_steps`: 给现场人员的补采、统一 `evidence_ref`、修复安全摘要或移除越界成功声明步骤。
- `commands_to_rerun`: 重跑 validation/review 的命令顺序。
- `capture_checklist`: 七类电梯现场材料的状态与补采动作。
- `not_proven`: 继续列出真实电梯、真实 Nav2/fixed-route、真实硬件反馈、HIL、投放/取消完成、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: review decision 不能放行控制动作，也不能声明送达成功。

`ready_for_controlled_elevator_field_rehearsal_not_proven` 只表示 Docker/local validation 材料可进入人工复核和受控演练准备。它不是真实电梯门状态、真实目标楼层确认、真实 Nav2/fixed-route 实跑、真实路线采集、HIL、真实投放、真实取消完成或 delivery success。缺 validation、坏 JSON、unsupported schema/boundary、缺材料、模板未替换、同一 `evidence_ref` 不一致、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true` 时，都必须保持 blocked review，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

### 5.17 elevator assisted delivery rehearsal execution pack

review decision 通过或 blocked 后，还需要一份面向现场人员的 execution pack，把复核结果转成材料模板、first-run/rerun 命令和 operator handoff。`pc-tools/evidence/elevator_field_run_execution_pack.py` 只读上一轮 review artifact/summary，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/elevator_field_run_execution_pack.py \
  --review-json /tmp/elevator_field_run_review.json \
  --once-json
```

execution pack 使用 `schema=trashbot.elevator_field_run_execution_pack.v1`，summary 使用 `schema=trashbot.elevator_field_run_execution_pack_summary.v1`，证据边界固定为 `software_proof_docker_elevator_field_rehearsal_execution_pack_gate`。核心字段包括：

- `execution_pack_verdict`: ready 或 blocked 分支，覆盖缺 review、坏 JSON、unsupported schema、unsafe copy、review blocked、成功/控制放行声明。
- `controlled_rehearsal_manifest`: 标明 source review、同一 `evidence_ref`、human observer、stop path 和七类材料名称。
- `required_material_templates`: 门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal 和 diagnostics/mobile safe summary 的字段模板。
- `first_run_commands`: 第一次受控电梯演练的材料采集和 validation/review/execution-pack 生成顺序。
- `rerun_commands`: review 修复、材料重采或同一 `evidence_ref` 修复后的重跑顺序。
- `operator_handoff`: 给现场人员和支持面的下一步、blocked categories 和 checklist。
- `not_proven`: 继续列出真实电梯、真实 Nav2/fixed-route、真实硬件反馈、HIL、投放/取消完成、delivery_success 和 O5 external proof 未证明。
- `primary_actions_enabled=false` 与 `delivery_success=false`: execution pack 不能放行控制动作，也不能声明送达成功。

`ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven` 只表示 Docker/local review 材料可生成受控演练执行清单。它不是真实电梯门状态、真实目标楼层确认、真实 Nav2/fixed-route 实跑、真实路线采集、HIL、真实投放、真实取消完成或 delivery success。任何缺 review、坏 JSON、unsupported schema/boundary、unsafe copy、review blocked、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须保持 blocked execution pack，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

### 5.18 elevator assist rehearsal evidence mainline gate

execution pack 之后，Robot dry-run 主链路需要一份更小的只读 evidence artifact 来驱动电梯阶段状态，而不是直接消费现场 raw 材料或成功声明。`pc-tools/evidence/elevator_assist_rehearsal_evidence.py` 生成 `trashbot.elevator_assist_rehearsal_evidence.v1`：

```bash
python3 pc-tools/evidence/elevator_assist_rehearsal_evidence.py \
  --evidence-ref elevator-rehearsal-001 \
  --target-floor 1F \
  --once-json
```

artifact 的证据边界固定为 `software_proof_docker_elevator_evidence_driven_mainline_gate`。顶层必须包含 `source=software_proof`、`same_evidence_ref_required=true`、`phase_evidence`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`phone_safe_summary` 也必须保留 `source=software_proof`，让 Robot dry-run consumption 和移动端只读摘要使用同一证据来源。`phase_evidence` 至少覆盖：

- `waiting_elevator_open`
- `entering_elevator`
- `requesting_floor_help`
- `waiting_target_floor`
- `exiting_elevator`

Robot task_orchestrator 只能在 dry-run 下只读消费这份 artifact。`failure` 存在时必须 fail closed，并把 `phase`、`reason` 和 `manual_takeover_reason` 写入后续任务记录或诊断摘要；不存在 failure 时，也只允许输出 `ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven`，不能放行真实控制动作。

该 gate 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。它只证明 Docker/local rehearsal evidence artifact 可生成、可校验、可由 Robot dry-run 只读消费；不证明真实电梯门状态、真实目标楼层确认、真实人工协助、真实 Nav2/fixed-route、真实路线采集、HIL、真实投放、真实取消完成、真实手机设备或 delivery success。非法 `evidence_ref`、非法 `target_floor`、unsafe copy、成功文案、`primary_actions_enabled=true` 或 `delivery_success=true` 都必须保持 blocked，并继续输出 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## 6. Debug Web

### 6.1 Onboard ROS debug page

Start the onboard debug page:

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

### 6.2 PC route debug console

PC 工作站复盘时可以使用独立 `pc-tools/route/route_debug_web.py`，它不依赖 ROS2，不 import `ros2_trashbot_*`，不读取硬件、serial/UART、Nav2 runtime、ROS graph 或网络外部服务。它只读消费 `fixed_route_autonomy` 写出的 debug status JSON，以及可选 task/task_record JSON 或 task_record dir：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --once-json
```

本地只读 HTML/API：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --host 127.0.0.1 \
  --port 8766
```

输出 summary 使用 `schema=trashbot.pc_route_debug_console.v1`，证据边界固定为 `evidence_boundary=software_proof_docker_pc_route_debug_console_gate`。JSON API `/api/status` 和 `/api/summary` 至少包含：

- `route_progress`
- `keyframe_preflight`
- `current_position`
- `current_checkpoint`
- `target`
- `match_status`
- `failure`
- `recent_task`
- `not_proven`
- `primary_actions_enabled=false`
- `delivery_success=false`

`--task-record-dir` 会按 `route_progress.evidence_ref` 或顶层 `evidence_ref` 查找同 run task record；找不到时输出 blocked/not_proven 摘要，不猜测任务完成。HTML/API 会隐藏本机完整路径、凭证、serial/UART、baudrate、WAVE ROVER 字样、ROS 控制 topic、traceback 和 checksum 类内容。

该 `pc_route_debug_console` gate 只证明 PC/local/Docker 环境能把 fixed-route status 与 task record 材料归一成可读 HTML/API。它不证明真实 Nav2/fixed-route 实跑、真实路线采集、关键帧实景验证、WAVE ROVER 运动、真实 serial/UART feedback、真实 HIL、dropoff/cancel completion 或 delivery success。

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

### 7.1 Autonomy sensor responsibility gate

Before treating a fixed-route or SLAM/Nav2 run as field material, keep the sensor responsibility boundary machine-checkable:

```bash
python3 pc-tools/evidence/hardware_baseline_review_gate.py --once-json
```

The `hardware_baseline_review` output is `software_proof` only. It records the product baseline from `docs/product/production_hardware_boundary.md`: `2D LiDAR` is the SLAM/Nav2 primary mapping and localization input, monocular camera is elevator door / target-floor semantic evidence, and `ToF` is a near-field safety gate rather than a primary mapping input. The artifact keeps every sensor at `hardware_material_pending` and `not_proven`, with `delivery_success=false` and `primary_actions_enabled=false`; it does not prove LiDAR field pass, ToF field pass, real monocular semantic pass, real Nav2/fixed-route execution, HIL, or delivery success.

When Hardware provides a procurement-specific intake summary, treat it as a narrower follow-up gate:

```bash
python3 pc-tools/evidence/hardware_sensor_procurement_intake.py \
  --procurement-json /tmp/hardware_sensor_procurement_intake.json \
  --summary-output /tmp/hardware_sensor_procurement_intake_summary.json
```

The PC gate / Robot / mobile handoff contract uses artifact `schema=trashbot.hardware_sensor_procurement_intake_gate.v1`, summary `schema=trashbot.hardware_sensor_procurement_intake_summary.v1`, and `boundary=software_proof_docker_hardware_sensor_procurement_intake_gate`. This summary is still `software_proof` / `not_proven`: it can tell Autonomy that procurement, installation, calibration, or owner handoff material is present or missing, but it cannot upgrade a route run into real SLAM/Nav2, fixed-route, elevator, HIL, or dropoff/cancel evidence. When the real procurement intake JSON is missing, the CLI must fail closed with `blocked_missing_hardware_sensor_procurement_intake`; that is the expected handoff state, not a broken field run. Robot diagnostics and mobile read-only surfaces may show the blocked summary as context, but must keep `not_proven`, `primary_actions_enabled=false`, and `delivery_success=false`.

Use the summary with these ownership rules:

- `2D LiDAR` remains the SLAM/Nav2 main-chain target only after procurement, physical install, calibration, and a later runtime evidence package are all available. Until then, fixed-route dry-run, route replay, and route/elevator handoff must keep relying on their existing status/task/evidence_ref contracts.
- `ToF` remains a near-field safety gate target. It may inform future conservative enter/exit or stop checks, but it must not be wired into the primary SLAM map, localization source, or fixed-route completion decision.
- `monocular` remains the elevator door / target-floor semantic evidence sensor. It may support `door_state.json`, `target_floor_confirmation.json`, and human-assistance notes in the elevator evidence chain, but it does not prove navigation completion by itself.

The procurement summary can be attached to route/elevator handoff material as context, not as a replacement for `nav2_fixed_route_runtime_log.json`, route status, task record, completion signal, door state, target-floor confirmation, or diagnostics mobile-safe summary. If any sensor material is missing, placeholder, cross-run, or outside the safe copy whitelist, keep the owner handoff blocked/not_proven and rerun the Hardware intake before Autonomy treats it as planning input.

### 7.2 PC Map Runtime Controls V1 boundary

2026-06-11 的 `PC/上位机 Map Start/Save Runtime Controls V1` 让 PC 高级诊断
可以通过固定代理触发上位机 no-motion map runtime：

- PC 固定代理：
  - `POST /api/robot-control/map/start?baseUrl=<upper-api>`
  - `POST /api/robot-control/map/save?baseUrl=<upper-api>`
- 上位机固定入口：
  - `POST /api/map/start`
  - `POST /api/map/save`
- helper：
  - `onboard/scripts/o3_map_lifecycle_proof.py`

该 runtime 的算法边界是：启动 LiDAR + SLAM，等待 `/scan`、`/map`，调用
`/trashbot/save_map`，写出 `map_name.yaml/pgm`，最后清理本轮进程。`map_name`
只允许短安全基名；`artifact_path` 在上位机响应中明确标记为 ignored，不参与写路径。

本轮实板 smoke 在 `root@192.168.1.11:37878` 上生成：

- `/root/rober/onboard/runtime/maps/pc_runtime_v1.yaml`
- `/root/rober/onboard/runtime/maps/pc_runtime_v1.pgm`
- `/root/rober/onboard/runtime/maps/pc_proxy_start.yaml`
- `/root/rober/onboard/runtime/maps/pc_proxy_start.pgm`
- `/root/rober/onboard/runtime/maps/pc_proxy_save2.yaml`
- `/root/rober/onboard/runtime/maps/pc_proxy_save2.pgm`

它们只能作为后续 map quality、AMCL/Nav2 readiness 和 fixed-route 采集的输入候选，
不能直接作为可导航地图或路线执行通过。后续进入 Nav2/fixed-route 前仍必须补：

- map quality gate；
- AMCL `/initialpose` 与 `/amcl_pose` 材料；
- map_server/amcl/planner/controller lifecycle readback；
- fixed-route route.csv/keyframe/route replay 或真实路线 runtime log；
- 无 `/cmd_vel` 误发、无 `/api/base/*`、无 `/dev/ttyS5` 底盘占用的同轮证据。

### 7.3 PC Localization Reset Controls V1 boundary

2026-06-11 的 `PC Localization Reset Controls V1` 新增一个高级诊断专用的
no-motion 定位重置入口：

- 上位机：`POST /api/localize/reset`
- 上位机 readback：`GET /api/localize/proof/latest`
- PC 固定代理：`POST /api/robot-control/localize/reset?baseUrl=<upper-api>`
- helper：`onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- artifact：`runtime/localization_reset_latest.json`

该入口默认使用 O10 helper 的 localization-only 模式：短暂 managed runtime、
发布一次 `/initialpose`，然后观察 `/amcl_pose`、`map->odom` 和 `map->base_link`
TF。PC 代理 body 固定为 `timeout_s=8`、`managed_runtime_opt_in=true`、
`managed_timeout_s=12`、`initialpose_opt_in=true`、`initialpose_x/y/yaw=0`、
`initialpose_frame_id=map`、`path_generation_opt_in=false`。浏览器不能传任意
body、goal、endpoint 或路径生成参数。

安全边界：

- 不调用 `NavigateToPose`、`FollowPath` 或 `ComputePathToPose`。
- 不调用 `/api/nav2/start`、`/api/nav2/stop`、`/api/base/manual`。
- 不发布 `/cmd_vel`，不打开底盘 UART `/dev/ttyS5`，不发送 `T=1/T=13/T=130/T=131`。
- `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
  `robot_control_executed=false` 永远保持 false。

`GET /api/localize/proof/latest` 会从 `runtime/localization_reset_latest.json`
摘要：`initialpose_published`、`amcl_pose_observed`、
`localization_tf_observed.map_to_odom/map_to_base_link`、`managed_runtime_started`、
`managed_runtime_cleanup_ok`、`root_causes` 和 `blocked_devices_not_opened`。
2026-06-11 的 `localization_tf_chain` 迭代进一步把 TF 诊断拆成稳定的
`tf_chain_observed` 四段：

- `map_to_odom`
- `odom_to_base_link`
- `base_link_to_laser_frame`
- `map_to_base_link`

helper 会先观测 `map->odom` 与 `odom->base_link`，再判断是否执行完整
`map->base_link` probe；这样 `map->base_link=false` 时可以区分
`map->odom` 缺失、`odom->base_link` 静态 TF 缺失、frame 命名不一致或
`tf2` timeout/timing。`base_link->laser_frame` 同步记录为 managed static TF
诊断字段，用于确认 AMCL scan frame 输入链路，但它仍不代表机械标定值。

这一步最多证明 AMCL no-motion localization material，可以作为后续 planner
readiness 的前置材料；它不证明路径执行、固定路线运行、真实运动、HIL pass 或
delivery success。

### 7.4 Route code structure after 2026-05-25 refactor

The fixed-route autonomy code is now split by proof responsibility:

- `route_contracts.py`: stable route data model, `fixed_route.v1`, checkpoint ids, failure codes, route replay JSONL payloads.
- `route_parsers.py`: ROS-free CSV/YAML parsing and waypoint validation. Use this for CLI conversion, offline proof, and runtime route loading so bad route files fail the same way everywhere.
- `route_proof_summary.py`: proof summary math only. It derives coverage rate, missing checkpoints, and first blocking reason.
- `elevator_assist.py`: conservative elevator assisted-delivery evidence schema. Visual route proof may fill the schema, but it must not claim door state, target floor confirmation, or safe exit unless a future dedicated source provides that evidence.
- `visual_gate_runtime.py`: OpenCV ORB matcher adapter. Tests and support scripts can replace it with a stub matcher without importing ROS2 or touching camera hardware.
- `route_utils.py`: compatibility facade for older imports. New code should import from the narrower modules above.

This split preserves the existing dry-run contract: fixed-route proof is still software proof unless it is paired with a real route runtime log, task record, completion signal, and field/elevator evidence under the same safe `evidence_ref`.

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
