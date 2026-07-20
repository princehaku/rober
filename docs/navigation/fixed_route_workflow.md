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

2026-06-22 起，map lifecycle proof 会在保存后继续检查 PGM 质量：只有保存出的地图
包含 `254` free cell，`algorithm_boundary.map_usable_for_navigation` 才能为 true。当前
真实上位机 no-motion 保存出的 runtime maps 只有 `205` unknown 和少量 `0` occupied，
没有 free cell，因此 `proof_status=blocked_with_root_cause`、
root cause 为 `map_has_no_free_cells_after_slam_save`。这类地图只能证明保存链路存在，
不能作为 Nav2 readiness、固定路线转换或自主导航验收材料。

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

`2026-07-11` 起，如果现场卡在 `/amcl_pose`、`map` frame 或 `map->odom`，预检不再只停留在
topic smoke。`field_route_evidence_preflight.py` 会额外记录 `/map` 与 `/amcl_pose` 的
type/publisher、安全版 managed map yaml 摘要、`map_server`/`amcl`/`planner_server`
lifecycle state、TF 失败短句，以及 `/api/nav2/proof/refresh` readback。no-motion 现场
收口优先看这些 root-cause 字段，而不是重复执行旧的 route capture 模板。`2026-07-11 08:39`
返工后，这段 refresh/readback 还必须在硬超时内自然返回；即使卡在 SSH 远端 readback，
也要落盘 fail-closed `*.raw.json`，而不是再靠人工 `Ctrl-C` 收口。

`2026-07-11 09:39` 起，现场若出现 `xmlrpc.client.Fault: RuntimeError: !rclpy.ok()`，预检会先把
它归类为 ROS CLI/daemon graph 层故障，而不是直接把 `/map`、`/amcl_pose` 或 lifecycle 判成
“topic 不存在”。脚本会仅对只读 graph 命令执行一次 daemon-safe retry，并把结果写进
`daemon_fault_detected`、`daemon_recovered`、`recovered_topics`、`unrecovered_blockers` 和
`root_cause_layers`。如果 retry 后 `/scan` 仍有 publisher、但 `/map_server`/`/amcl`
lifecycle unavailable、`map->odom`/`map->base_link` 继续报 `Invalid frame ID "map"`，则应把
下一轮动作明确落到 map server、AMCL 和 TF bringup，而不是回到 generic ROS graph 排查。

`2026-07-11 11:40` 这一轮还补了一个 helper 侧收口规则：`o10_amcl_nav2_runtime_proof.py`
不再执行 `ros2 topic info /initialpose --verbose`。如果 initialpose publish 路径没有拿到
`subscriber_count`，artifact 只写
`initialpose_verbose_info_skipped_to_avoid_cli_stall`。这样做是为了避免现场 direct helper
再次卡死在旧 `/initialpose` topic-info probe，而优先把时间留给 `/scan`、`/amcl_pose`、
TF 和 path 相关 blocker。

最新 live direct helper 的边界因此更新为：已经越过旧 `/initialpose` topic-info 卡点，但仍
fail-closed 在 `/scan_once_not_observed`、`cli_initialpose_publish_failed`、
`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`，且 `path_generated=false`。
这仍然不是 fixed-route path proof、Nav2 route execution、HIL pass 或 delivery success。
no-motion proof boundary 继续固定保持：

- `safe_to_control=false`
- `robot_control_executed=false`
- `hil_pass=false`
- `delivery_success=false`

`2026-07-11 12:41` 起，`o10_amcl_nav2_runtime_proof.py` 的 direct helper 会在同一个
no-motion artifact 中输出 `localization_signal_freshness` 和 `tf_source_freshness`。
前者覆盖 `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static` 的 topic type、probe
耗时/timeout、可解析 timestamp 与 freshness；后者把 `map_to_odom`、`odom_to_base_link`、
`base_link_to_laser_frame` 分成 dynamic/static source 观察结果。现场 fixed-route 或 path proof
继续 fail-closed 时，优先看这些字段，而不是只看泛化的 `map_to_odom_not_observed`。

本轮 live artifact `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json`
显示：`/scan` 与 `/amcl_pose` topic type 可见但 once probe timeout，`/odom` 已 observed 且
fresh，`/tf` 和 `/tf_static` topic type 可见但 dynamic/static source inventory 未取到 edge。
最终仍 `map_to_odom=false`、`path_generated=false`；本轮只是更细的 fail-closed root cause，
不是 fixed-route path proof、Nav2 route execution、HIL pass 或 delivery success。

`2026-07-11 13:41` 起，现场如果继续卡在 `/scan`，helper 不再只保留一条
`ros2 topic echo --once /scan` 结果，而是顺序执行：

1. `rclpy_sensor_data_once`
2. `cli_sensor_data_echo_once`
3. `cli_default_echo_once`

artifact 会把这些尝试写入
`proof.localization_signal_freshness["/scan"].probe.attempts[]`，并额外给出
`best_attempt`、`qos_probe_boundary` 和 `source`。因此 fixed-route/no-motion 收口时，应先看：

- 第一条 sensor-data rclpy 尝试是否因为板端 Python/ROS 共享库缺失直接失败；
- 第二条 sensor-data CLI 是否 timeout；
- 默认 CLI 是否也 timeout；
- root cause 是否收口到 `/scan_rclpy_probe_failed`、`/scan_sensor_data_qos_timeout`
  或 `/scan_all_probe_attempts_timed_out`。

当前 live artifact
`sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json`
显示：`rclpy_sensor_data_once` 命中 `librcl_action.so` / `_rclpy_pybind11` 导入失败，
两条 CLI `/scan` echo 仍超时，因此 `/scan` 的主 blocker 已从泛化 timeout 下钻到
`/scan_rclpy_probe_failed`。这同样不代表 Nav2 route execution、HIL pass 或 delivery success。

`2026-07-11 21:47` 之后，fixed-route/no-motion 收口还要先看 helper 的
`managed_runtime_wait_result`。原因是当前 O3 路线已经证明“节点出现在 graph”和
“lifecycle 真正 active”不是一回事，而且旧的 wait graph probe 直接跑主进程 `rclpy`
时，还可能因为环境没 source 干净而误报 `No module named 'rclpy'`。现在
`o10_amcl_nav2_runtime_proof.py` 会用 sourced child Python 做 node graph probe，并在 managed wait
窗口内反复读取 `/map_server`、`/amcl` lifecycle，把结果归为：

1. `managed_runtime_lifecycle_active_observed`
2. `managed_runtime_nodes_observed_but_lifecycle_inactive`
3. `managed_runtime_wait_timeout`

只有第 1 类才说明 localization graph 至少已经跨过 lifecycle active gate。若是第 2 类，
下一步动作应继续盯 `/map_server`、`/amcl` 激活链，而不是过早转去解释 `/scan` timeout 或强行做
planner-only path attempt。若是第 3 类，则优先回到 managed runtime bringup 本身。

`2026-07-11 14:42` 起，`rclpy_sensor_data_once` 的 `/scan` 订阅改为 sourced child Python
probe：它复用 helper 的 ROS setup/workspace setup 环境，而不是在主 Python 进程里直接
import `rclpy`/`sensor_msgs`。现场 fixed-route/no-motion 收口时，应优先看本轮 artifact：

`sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`

本轮结论是：`/scan.topic_type=sensor_msgs/msg/LaserScan` 仍可见；`/scan` child rclpy
probe 的 `import_check.ok=true`，说明上一轮 `/scan` 的 `librcl_action.so` import failure
已经从该 probe 上消除；但 child probe 没在窗口内读到 frame，并收口为
`/scan_rclpy_child_timeout_after_import`。两条 CLI fallback 仍 timeout，`/amcl_pose`
仍 timeout，`map_to_odom=false`，`path_generated=false`。这把下一步动作从“修主进程
ROS import 环境”推进到“确认 `/scan` publisher 实际发帧、QoS/graph timing 或 child
probe 窗口”的层级。

安全边界不变：该 artifact 仍不证明 fixed-route path proof、Nav2 route execution、HIL pass
或 delivery success，且继续固定 `safe_to_control=false`、`robot_control_executed=false`、
`delivery_success=false`、`hil_pass=false`。

`2026-07-11 15:44` 起，现场 `/scan` 排查的第一读数不再是泛化 timeout，而是
`proof.localization_signal_freshness["/scan"]` 的 publisher / endpoint / sample timing 清单。
fixed-route 或 no-motion path proof 失败时，按下面顺序读 artifact：

1. `publisher_inventory.publisher_count`：为 0 时先处理 `/scan_no_publisher` 或
   `/scan_lidar_runtime_not_started`，不要继续归因到 child timeout。
2. `endpoint_inventory.endpoint_qos_profiles` 与 `endpoint_inventory.requested_qos_profile`：
   publisher 已可见但无 sample 时，先判断 QoS 或 sample window。
3. `sample_timing.sample_count`、`first_sample_latency_ms`、`last_sample_stamp` 与
   `timeout_boundary_ms`：确认 child probe 是否已经建立 subscription 并等满窗口。
4. `probe.classification`：稳定值为 `/scan_no_publisher`、
   `/scan_lidar_runtime_not_started`、`/scan_publisher_visible_but_no_sample`、
   `/scan_qos_or_window_timeout`、`/scan_rclpy_child_timeout_after_import` 或
   `/scan_sample_observed`。
5. 只有 `/scan_sample_observed` 后，才继续看 `/amcl_pose`、`map_to_odom` 和
   `path_generated`。

这份 scan endpoint timing inventory 仍是 no-motion supporting evidence。没有
`path_generated=true`、route CSV/rosbag/keyframe 或 Nav2 result 时，不得把它当作
fixed-route execution、safe-to-control、HIL pass 或 delivery success。安全字段必须继续为
`safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、
`hil_pass=false`、`delivery_success=false`。

`2026-07-11 22:48` 起，再读一层 `proof.board_source_preflight`：

- 如果 `cli_ready=false`，说明 sourced shell 或 `ros2` CLI 自身还没恢复，本轮只接受
  `ros2_cli_unavailable_tf_source_probe_skipped` 这类前置 blocker；
- 如果 `cli_ready=true` 但 `runtime_ready=false`，说明 managed runtime / lifecycle / CLI
  仍应继续尝试，但 rclpy-based TF source inventory 不能再被包装成“未执行”，而要明确收口到
  `tf_source_probe_rclpy_runtime_unavailable_after_board_preflight`；
- 只有 `cli_ready=true` 且 `runtime_ready=true` 时，才期望 rclpy source inventory 真正返回
  `/tf`、`/tf_static`、AMCL param/node info 和 edge freshness。

因此 fixed-route/no-motion closeout 里，`tf_source_probe_not_executed` 不再是可接受的最终表述；
必须给出更具体的 CLI/runtime gate 或实际 TF source blocker。

`2026-07-11 16:43` 起，若 15:44 那轮已经证明 publisher endpoint 可见但 `sample_count=0`，
下一轮现场 helper 必须带长窗口并比较两条 child subscription attempt：

1. `best_effort_attempt`：`BEST_EFFORT` / `VOLATILE`
2. `reliable_attempt`：`RELIABLE` / `VOLATILE`
3. 仍保留 CLI fallback，但 child 对照是主判据

读取 `sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/*` 时，先比
两条 attempt 的 `requested_qos_profile`、`sample_timing.sample_count`、`timed_out`、
`first_sample_latency_ms` 和 `error`。如果两条都 timeout 且 publisher 仍可见，应优先采信
`/scan_reliable_and_best_effort_timeout` 这类分类；如果其中一条收到 sample，才进入
`/scan_sample_observed` 后续链路。该结论仍只服务于 `/amcl_pose`、`map_to_odom` 和
`path_generated` 的前置诊断，不等于 fixed-route execution、HIL pass 或 delivery success。

`2026-07-12 19:56` 起，fixed-route/no-motion closeout 必须优先读取
`proof.scan_qos_endpoint_readback_split`，不要只读旧的
`proof.localization_signal_freshness["/scan"].probe.classification`。该字段把
`/scan_reliable_and_best_effort_timeout` 拆成：

1. `publisher_endpoint_classification`：topic/type、publisher node、endpoint QoS、
   endpoint inventory 是否稳定；
2. `qos_window_ros_readback_classification`：BEST_EFFORT 与 RELIABLE child attempt 的
   timeout、sample count、requested QoS 与 endpoint QoS compatibility；
3. `lidar_runtime_classification`：endpoint/QoS/readback 已足够指向 runtime 时，才给出
   Hardware handoff 条件；
4. `primary_split`：写入 `artifact_closeout.primary_root_cause` 的最细原因，同时保留
   `canonical_blocker=/scan_reliable_and_best_effort_timeout`。

本轮 live artifact
`sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json`
已经把 primary closeout 推进到
`/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`。同时它明确
publisher endpoint 为 `lidar_driver`、publisher QoS 为 `RELIABLE`、BEST_EFFORT/RELIABLE
readback 均 timeout、`sample_count=0`、QoS compatibility risk 为 false，并仅把
`serial.serialutil.SerialException` 作为 LiDAR runtime handoff 条件。该结论不等于 vendor-backed
hardware root cause；Hardware 后续介入前仍要读取 `docs/vendor/VENDOR_INDEX.md`，并单独证明
serial/runtime/wiring 事实。

`2026-07-12 20:57` 起，Hardware 的 LiDAR runtime gate 按以下顺序收口，不再重复消费
19:56 的 endpoint/QoS blocker：

1. 确认本地 vendor gate：`docs/vendor/VENDOR_INDEX.md`、Orange Pi USB/供电资料，以及
   WAVE ROVER `ugv_rpi/base_ctrl.py`。当前本地 vendor 参考只证明 `/dev/ttyACM* @ 230400`
   和 STC `0x54`/47 字节/12 点 LiDAR 帧；历史现场 `150000` 仍是需要实板对比的候选。
2. 分别运行 LiDAR-only no-motion smoke：`--serial-baudrate 230400` 和
   `--serial-baudrate 150000`。两个输出目录都必须保留 `summary.json`、
   `lidar_driver_diagnostics.json`、`device_snapshot_*.json`、`scan_once.txt`、
   `raw_packet_once.txt` 和 `scan_hz.txt`。
3. 优先看 `summary.json` 里的 `raw_bytes_observed`、`empty_read_count`、
   `serial_exception_observed`、`serial_exception_message_hint`、`packet_count_total`、
   `published_raw_packet_count`、`published_scan_count` 和 `/scan` sample 状态。
4. 只有 `/scan` sample 或 `/lidar/raw_packet` 已恢复到 clean enough，才把下一轮交回
   Algorithm 复验 `/amcl_pose`、dynamic `map->odom` 和 planner-only path proof。

这条 gate 不执行 fixed-route、route capture、NavigateToPose、`/cmd_vel` 或
`/api/base/manual`；它只能产出 LiDAR serial/runtime/wiring 证据或更窄 blocker。

`2026-07-12 21:57` 起，Robot Software 若已经用 `/api/radar/status` 证明现有 lifecycle 的
current baudrate readback 为 `150000`，Algorithm 的 strict no-motion path proof 必须复用该
holder。运行 `o10_amcl_nav2_runtime_proof.py` 时，在 `--managed-runtime-opt-in` 和
`--managed-lidar-serial-baudrate 150000` 外还要带
`--reuse-existing-lidar-lifecycle`。该模式只启动 map_server、AMCL、planner_server 和静态 TF，
不会启动第二个 `ros2_trashbot_hardware lidar_driver`，artifact 应固定：

- `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`
- `managed_lidar_driver_started_by_helper=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `uses_base_uart=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

只有 `/scan`、`/amcl_pose`、dynamic `map->odom` 和 planner-only ComputePathToPose 都在同一
artifact 中 clean 后，才能声明 same-run planner path generation；仍不能声明 NavigateToPose、
route execution、HIL 或 delivery。

`2026-07-13 00:00` 起，21:57 accepted same-run planner-only path proof 可以被转成
fixed-route / route-intent material，但边界必须继续写清楚：source artifact 的
`path_point_count=21`、`path_generated=true` 和 `fallback_mode=ros2_cli_action_send_goal`
只证明 ComputePathToPose 在 strict no-motion 条件下成功；如果 artifact 只暴露 CLI
`stdout_tail` 的部分 pose block，route-intent 包必须标注
`path_pose_materialization_status=partial_stdout_tail_only`，不得补造缺失的 path points。
这类材料可以生成 `route_intent_summary.json`、`route_intent_replay.jsonl` 或 `route.csv`
作为下一轮 replay/execution 的同一 `route_intent_id` 入口，但仍必须固定
`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
`safe_to_control=false`，并继续禁止 NavigateToPose、`/cmd_vel`、`/api/base/manual` 和
WAVE ROVER UART。

`2026-07-13 02:00` 起，`o10_amcl_nav2_runtime_proof.py` 的 ROS2 CLI
`ComputePathToPose` fallback 在成功生成 path 时，必须同时写出
`path_structured_poses`、`path_structured_pose_count`、`path_preview_points`、
`path_preview_point_count`、`path_preview_source_point_count` 和 `path_preview_frame_id`。
fixed-route / route-intent consumer 应优先消费这些 structured poses；只有缺少这些字段时，
才允许降级读取 CLI `stdout_tail`，并且只能 materialize tail 内完整出现的 pose block。
旧 21:57 artifact 的权威事实仍是 `path_point_count=21`，但可追溯结构化材料只有
stdout tail 中的 14 个完整 pose，因此必须标注
`historic_stdout_tail_truncated_full_pose_replay_unavailable`，不得把缺失的 7 个点补造成
full replay。本规则仍是 strict no-motion export contract：
`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
`safe_to_control=false`，继续禁止 NavigateToPose、controller/BT、`/cmd_vel`、
`/api/base/manual` 和 WAVE ROVER UART。

`2026-07-13 03:00` 的 live rerun 已证明 helper 能在 strict no-motion 条件下持久化完整
structured path poses，但当前 live 计数不是旧的 21。主 artifact
`sprints/2026.07.13_03-00_o3_live_full_structured_path_capture/artifacts/algorithm/live_full_structured_path_capture_summary.json`
显示 `path_generated=true`、`path_point_count=28`、`path_structured_pose_count=28`，
并记录 `blocked_reason=expected_21_structured_pose_count_not_reproduced_current_live_returned_28_after_map_bounds_adaptation`。
原因是当前 AMCL start 在 map bounds 外侧，helper 触发
`map_bounds_adapted_no_motion_planner_probe`，把 start/goal 调整到 `y=0.25`；即使用旧 21:57
planner start 作为 explicit initialpose 重试，live AMCL 仍收敛到需要 map-bound adaptation 的状态，
因此 pinned-start artifact 也返回 28 个 structured poses。

后续 fixed-route / route-intent consumer 应优先消费本轮 fresh `path_structured_poses`，
不要再假设 full structured path 必然是 21 个点。若 Product acceptance 仍要求复现 21，
下一轮 blocker 应写成 current live localization/map-bound drift，而不是历史 stdout tail 缺失。
该材料仍只证明 planner-only no-motion path export：`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`，继续禁止 NavigateToPose、
controller/BT、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。

`2026-07-13 04:02` 起，fixed-route / route-intent consumer 的 primary source 应改为
03:00 fresh same-run 28-pose structured material，而不是 01:00 对旧 21:57 partial
stdout-tail 的 dry-run summary。本轮 consumer 输出：

- `fixed_route_28_pose_consumer_summary.json`
- `fixed_route_28_pose_replay.jsonl`
- `fixed_route_28_pose_route.csv`

summary 必须记录新的 `route_intent_id`、`task_id`、`primary_source_artifact`、
`fresh_28_pose_structured_material_consumed=true`、
`historic_21_57_artifact_primary_source=false` 和 `path_structured_pose_count=28`。
JSONL / CSV 必须覆盖 28 个 structured poses 的 order、frame、position 和 orientation，
旧 21:57 partial stdout-tail 只能作为 comparator，不能再作为 primary route material。
这仍然只是 strict no-motion consumer material：`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`，继续禁止
NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。

`2026-07-13 05:02` 起，04:02 accepted material 可以被消费成 same-task route replay packet，
但消费者必须实际读取 `route_csv` 和 `replay_jsonl`，不能只复制
`fixed_route_28_pose_consumer_summary.json`。Algorithm offline packet 的最小合同是：

- `schema=trashbot.o3.same_task_route_replay_packet.v1`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `route_csv_row_count=28`
- `replay_jsonl_event_count=28`
- `path_structured_pose_count=28`
- `same_task_identity_verified=true`
- `consumer_integration_status=pass_strict_no_motion_same_task_replay_packet`

packet summary 还必须保留 summary/CSV/JSONL 的 source fingerprints、first/last pose readback
或等价摘要，证明 28-pose 顺序与字段是从两份行级材料交叉读回。该材料仍然只是
strict no-motion offline replay packet：`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`，继续禁止
NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、
route execution、delivery 和 HIL。若后续需要 O6/O7 archive/readback 或真实 route execution，
必须另开跨 owner sprint。

`2026-07-11 18:45` 起，fixed-route/no-motion 现场读 artifact 时要再往前加一层：
先看 `proof.board_source_preflight`，再看 `proof.map_lifecycle_preflight`。`2026-07-11 19:46`
之后，`board_source_preflight` 又被拆成 `source_stage`、`path_lookup`、`cli_invocation`
和 `python_rclpy` 四块。这是为了把“source 脚本慢/失败”、“PATH 或 which 找不到 ros2”、
“`ros2` CLI 自身启动 timeout/失败”、“Python/rclpy import 失败”和“ROS source 已经好，
但 `map_server` 或 `amcl` lifecycle 没 active”拆开。

推荐读取顺序：

1. `proof.board_source_preflight`
2. `proof.map_lifecycle_preflight`
3. `proof.localization_signal_freshness["/scan"]`
4. `proof.localization_signal_freshness["/amcl_pose"]`
5. `proof.tf_source_freshness["map_to_odom"]`
6. `proof.path_generated`

如果 `proof.board_source_preflight.ready=false`，helper 必须 fail-closed 跳过 `/scan`、
`/initialpose` 和 path generation。此时不要再把现场结论写成泛化 `/scan timeout`；应该直接
根据 `classification` 判断是：

- `board_source_preflight_source_timeout`
- `board_source_preflight_source_failed`
- `board_source_preflight_ros2_cli_path_missing`
- `board_source_preflight_ros2_cli_which_timeout`
- `board_source_preflight_ros2_cli_invocation_timeout`
- `board_source_preflight_ros2_cli_invocation_failed`
- `board_source_preflight_rclpy_import_timeout`
- `board_source_preflight_rclpy_import_failed_*`

`2026-07-12 05:52` 起，`proof.board_source_preflight` 的 source、PATH lookup 和 CLI
readiness 改为同一个 amortized shell 读取。现场 closeout 先确认
`proof.board_source_preflight.source_amortized_cli_preflight_schema=trashbot.o10.source_amortized_cli_preflight.v1`，
再看 `source_and_cli_in_one_shell`、`per_command_source_overhead_eliminated`、
`commands_executed_after_single_source` 和 `amortized_shell.boundary`。旧字段
`source_stage`、`path_lookup`、`cli_invocation`、`python_rclpy`、`cli_ready`、
`runtime_ready` 和 `classification` 继续保留，便于旧 reader 兼容。

分类规则也要按同一个 shell 的事实读取：

- source 成功且 PATH lookup 成功，但 `ros2 --help` timeout：收口到
  `board_source_preflight_ros2_cli_invocation_timeout`；
- source 成功但 `command -v` / `which` / `type -a` 任一 timeout：继续收口到
  `board_source_preflight_ros2_cli_which_timeout`；
- `cli_ready=true` 后，如果 rclpy import、ROS graph、map lifecycle、AMCL 或 TF 失败，
  不得再写成 `workspace_source_or_env_mismatch`，而应进入 runtime/graph/lifecycle
  对应 blocker。

`2026-07-12 06:54` 起，fixed-route/no-motion closeout 再往前加一层：先分清
heavy help 与 lightweight CLI readiness。当前 helper 合同是：

- `cli_invocation` 继续记录 `ros2 --help >/dev/null`，但它只做 heavy 诊断；
- `lightweight_readiness` 固定记录 `ros2 daemon status` 和 `ros2 node list`；
- `python_rclpy` 继续只记录 `rclpy import`。

因此只要 `lightweight_readiness.ok=true`，即使 `cli_invocation.timed_out=true`，也要接受：

- `board_source_preflight.classification=board_source_preflight_ready`
- `board_source_preflight.lightweight_cli_ready=true`
- `board_source_preflight.cli_ready=true`
- `board_source_preflight.runtime_ready=true`

当前 true-board `330s` artifact
`sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness_330s.raw.json`
已经命中这组条件，其中 `lightweight_readiness.primary_label=ros2_node_list`、
`successful_labels=["ros2_node_list"]`，而 `ros2 daemon status` 与 heavy `ros2 --help`
都仍超时。也就是说，fixed-route helper 已经越过 preflight 本身，真正进入 lifecycle、
`/scan`、`/map` 和 TF 这些后续 no-motion gates。

如果 `board_source_preflight.ready=true` 但 `proof.map_lifecycle_preflight.classification`
仍显示 `map_server` 或 `amcl` inactive，下一轮动作应该继续清 lifecycle，而不是回去改 `/scan`
QoS 合同或 O5/O6/O7 wrapper/readback。

`2026-07-12 07:53` 起，fixed-route/no-motion closeout 应优先读取
`proof.downstream_recovery_summary`，再回看原始命令。该 summary 的目的不是证明路线已能执行，
而是在 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、
`runtime_ready=true` 之后，把后续 blocker 直接拆成可派工的几类：

- `map_lifecycle.node_summaries.map_server/amcl.failure_mode`：区分 lifecycle 命令 timeout、
  stdout 明确 inactive、命令失败和 graph blocked 后 skipped。skipped 不能当作 inactive。
- `scan.blocked_reason`：区分 `/scan_no_publisher`、publisher 可见但无 sample、QoS/window timeout
  和 sample 已观测。若下一步落到 LiDAR runtime/串口/接线事实，必须交 Hardware owner 查
  `docs/vendor/VENDOR_INDEX.md`。
- `map.topic_sample`：保留 `/map_once_not_observed` 作为 legacy root cause，同时展示
  `/map_topic_missing`、`/map_no_publisher`、`/map_sample_timeout` 或
  `/map_sample_not_observed`。
- `amcl.blocked_reason`：只说明 `/amcl` lifecycle 或 `/amcl_pose` sample gate，不代表 TF 已 ready。
- `tf.blocked_reason`：先区分 `/tf_topic_missing`，再区分 dynamic
  `map_to_odom_dynamic_source_missing`。`map_to_base_link` 只是 downstream derived gate。
- `path_generation_gate`：只有 map、scan、AMCL 和 TF 都 ready 后，才允许 planner-only
  ComputePathToPose 证据；仍禁止 NavigateToPose、`/cmd_vel`、`/api/base/manual` 和 WAVE ROVER UART。

如果 `ready_for_planner_only_path_gate=false`，本轮只能算 no-motion downstream diagnostic delta；
不能写成 route execution、HIL pass、safe-to-control 或 delivery success。

## 1.6 RViz2 Engineering Map View

普通用户在 PC 上优先使用 `http://<PC>:7001/` 的大地图和 `/map` 地图大屏；首页和 `/map`
默认都是 `100%` 完整态势，真实地图按画布高度优先铺满，宽图横向滚动，点 `细节放大` 可到
`1200%` 做局部排障，点 `完整态势` 回到 `100%`。ROS2 原生配套用于工程排障，不替代普通 PC 界面：

```bash
ros2 launch ros2_trashbot_bringup rviz.launch.py
```

PC 大地图的主数据源是上位机 `GET /api/map/preview`。该接口只读地图/路线/目标/小车位姿/雷达贴图，不启动 ROS2 lifecycle、不发 `/cmd_vel`、不打开底盘串口。2026-07-03 起，`/api/map/preview` 会把 Nav2 path preview 终点折成 `target`；如果 path 点数组暂缺但最近 NavigateToPose artifact 仍有 `goal_request`，则用 `source=latest_goal_request` 返回最近目标点。PC 端会把这两类目标都画到同一张地图上，但只有 `path_preview_points` 至少 2 个时才声明“图上路线已显示”。

该 launch 加载 `ros2_trashbot_bringup/rviz/trashbot_nav.rviz`，只读观察以下 topic/frame：

- `/map` 和 `/map_updates`：确认当前地图是否真的发布。
- `/scan`：确认雷达点是否进入 ROS graph。
- TF：确认 `map`、`odom`、`base_link`、`laser_frame` 链路是否连通。
- `/plan`、`/local_plan`：确认 Nav2 全局/局部路线是否生成。
- `/amcl_pose`：确认定位是否可见。
- `/global_costmap/costmap`、`/local_costmap/costmap`：确认 Nav2 costmap 是否有数据。

这个 RViz2 配置不包含 GoalTool，也不用于普通用户发车。现场要执行路线仍回到 PC `7001` 普通界面，按图上路线按钮走固定 gate。
当前普通路线执行默认走 PWM/HTTP 底盘链路：PC 请求带 `base_command_mode=pwm`、`managed_runtime_opt_in=true`
和 `confirm_navigation_execution=true`。如果返回 `goal_succeeded`、同窗口非零底盘命令和 IMU 姿态变化，PC 会把 wheel raw
L/R=0/0 保留为底盘反馈诊断，但允许进入送达收口；送达材料使用 PC 大地图路线叠加 ref
`pc-map-route-overlay:<nav2 evidence_ref>`，最终仍由 delivery gate 判断 `delivery_success`。

远程浏览器观察可用 Foxglove：先在 ROS2 环境启动 `foxglove_bridge`，再用浏览器连接 `ws://192.168.1.11:8765`。Foxglove 与 RViz2 一样只用于观察地图、雷达、TF、路径、定位和 costmap，不作为普通用户发车入口。

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

## 3. Fixed-Route Autonomous Run

2026-06-29 起，`autonomous.launch.py navigation_mode:=fixed_route` 的默认行为是创建
Nav2 `BasicNavigator` 并执行固定路线：`fixed_route_dry_run` 默认 `false`，
`enable_visual_gate` 默认 `false`。这让自动驾驶是否能动主要由 Nav2 服务、地图、
定位和底盘 `/cmd_vel` 链路决定，不再被相机 keyframe gate 或 dry-run 默认值挡住。

需要只做软件演练时显式打开 dry-run：

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  navigation_mode:=fixed_route \
  fixed_route_dry_run:=true
```

需要把相机 keyframe 作为路线 checkpoint gate 时显式打开视觉 gate：

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  navigation_mode:=fixed_route \
  enable_visual_gate:=true
```

真实发车前仍必须确认现场安全、停止兜底、地图和定位状态；上述默认值只移除
“默认不动”和“相机无帧就卡住固定路线”的软件阻塞，不等于 Nav2 HIL 或送达成功。

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
- 若改走 `o11_nav2_lifecycle.sh` 的受管 start 入口，必须把 `base_enabled`、
  `lidar_enabled`、`lidar_serial_port`、`lidar_serial_baudrate` 和
  `static_laser_tf_enabled` 原样透传给 `__run` 子进程；否则 manager/status 看到的
  runtime 参数会与真实 launch 参数分叉，现场 root-cause 会被读歪。

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

## 2.7 Nav2 No-Motion Path Generation Refresh

2026-06-11 起，PC 高级诊断里的“检查路径（高级）”固定通过 workstation
代理调用上位机 `/api/nav2/proof/refresh`，body 使用 managed no-motion
runtime：

```json
{
  "timeout_s": 20,
  "managed_runtime_opt_in": true,
  "managed_timeout_s": 20,
  "managed_map_yaml": "trashbot_map.yaml",
  "initialpose_opt_in": true,
  "initialpose_x": 0,
  "initialpose_y": 0,
  "initialpose_yaw": 0,
  "path_generation_opt_in": true,
  "path_generation_timeout_s": 20,
  "path_goal_frame_id": "map",
  "path_goal_x": 0.8,
  "path_goal_y": 0,
  "path_goal_yaw": 0
}
```

文档与 summary-facing 字段只记录 configured managed map basename，例如 `trashbot_map.yaml`；不回显板上完整 runtime map 路径。

这个入口只拉起 map_server、AMCL、planner_server 和必要的静态 TF/LiDAR
证据 runtime，用一次 `/initialpose` 建立 AMCL 定位，再调用
`ComputePathToPose` 风格的 planner 计算接口生成全局路径。它不是
`NavigateToPose`，不启动 controller/BT navigator，不发布 `/cmd_vel`，
不调用 `/api/base/manual`，不打开 WAVE ROVER 底盘 UART `/dev/ttyS5`。
上位机 artifact 必须保持 `safe_to_control=false`、`delivery_success=false`、
`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。

如果 refresh 失败，artifact 应优先把 blocker 缩到具体层级：map source、
AMCL/TF readiness、planner lifecycle、ComputePath action、outer timeout 或
cleanup。PC 代理只转发固定 body 并读取 latest，不允许前端传入任意 goal、
Nav2 start/stop 或底盘控制参数。

2026-06-25 起，PC 普通首屏的固定目标预检会把定位证据来源从单一
`/api/localize/proof/latest` 扩展为 `localize latest + nav2 proof latest + nav2 status`。
如果 localize latest 保留旧失败，但 Nav2 no-motion proof/status 已读到 AMCL pose、
`map_to_base_link` 和正数路径点，PC 预检可以通过；雷达 lifecycle 状态继续作为普通提示和
WYSIWYG 扫描显示，不再作为行程按钮的前端硬挡。该预检仍不发送 `NavigateToPose`、
`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART 命令；真正执行仍由
`/api/robot-control/nav2/goal/execute` 的确认字段和后端定位/路线 gate 再次复查。

`/api/nav2/proof/refresh` 现在会先显式 source ROS Humble setup，再拉起 helper。
这样 `rclpy` 和 Nav2 action client 的运行时依赖不会被 systemd 服务环境吞掉；
但这个变化只影响 proof helper 的启动方式，不改变默认只读/no-motion 边界。

`2026-06-11 11:15` clean-baseline refresh 复核了上一轮 `upper_ros_quiescent=true`
之后的 fresh no-motion path proof。清场前目标 `ps`、`ros2 node list`、
`/dev/ttyS5`/`/dev/ttyACM0` 的 `lsof/fuser` 均无 `o10_amcl_nav2_runtime_proof`、
`map_server`、`amcl`、`planner_server`、`lifecycle_manager` 或 `lidar_driver`
残留。第一次 direct API refresh 使用 20s collector/runtime/path 窗口，保留了
partial artifact 并定位为 helper timeout：`/amcl_pose` 已观测，但 partial
诊断里 static TF 未完整观测，`map -> base_link` 因 `odom -> base_link` 缺失而阻塞。
按“失败后最多一次重试”规则，第二次仍使用同一 no-motion opt-in contract，只把
collector/runtime/path 窗口放宽到 30s；结果为
`nav2_no_motion_path_generation_runtime_observed`：

- `evidence_ref=o10-amcl-nav2-runtime-1781147133452`，`generated_at_ms=1781147181031`，
  新于本轮 `run_start_ms=1781146923423`。
- `managed_runtime_started=true`、`managed_runtime_cleanup_ok=true`、
  `initialpose_published=true`、`amcl_pose_observed=true`。
- `map_server_active=true`、`amcl_active=true`、`planner_server_active=true`。
- `path_generation_succeeded=true`、`path_generated=true`、`path_point_count=31`、
  `root_causes=[]`。

这仍然只证明 clean-baseline 下 map/AMCL/planner 能在 no-motion 边界内生成一条
`map:(0.8, 0, 0)` 全局路径。它不是 `NavigateToPose`、不是 controller/BT 执行、
不是固定路线执行、不是物理运动 gate，也不是 delivery success。artifact 继续保持
`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`uses_base_uart=false`。结束读回必须仍确认 managed runtime 和 LiDAR 进程无残留，
且 `/dev/ttyS5`、`/dev/ttyACM0` 无占用。

`2026-06-11 01:45` 起，上位机 API 的 helper subprocess timeout 与 PC
`检查路径` proxy 预算按固定 body 对齐；该早期合同在 08:25 后仍以 84s upper cap 和
90s PC cap 为边界。2026-06-11 19:45 修复后，PC 固定 body 改为
`timeout_s=30`、`path_generation_timeout_s=30`、`managed_runtime_opt_in=true`、
`managed_timeout_s=30`、`initialpose_opt_in=true`、`path_generation_opt_in=true`；
对应上位机 subprocess raw 预算为 `120s`，helper cap 为 `132s`，PC proxy fetch
timeout 为 `150s`。这个预算只限制 HTTP refresh 等待 helper 的最长时间，不改变
helper 内部 no-motion collector 的 ROS2 观测语义。如果真实 Nav2 proof refresh
仍慢于该窗口，上位机会先返回结构化 timeout/root cause，PC 再通过固定
`GET /api/nav2/proof/latest` 只读兜底展示最近 artifact；不能让 PC 侧先出现
`fetch_timeout_150000ms` 后才知道上位机实际已经生成路径。

这一步仍然不等于可发车：

- 允许：一次 `ComputePathToPose` 风格的 planner 计算。
- 禁止：`NavigateToPose`、`FollowPath`、`/cmd_vel`、`/api/base/*`、`bt_navigator`
  以及任何默认 motion side effect。
- `safe_to_control`、`delivery_success` 仍然必须保持 `false`。
仍不等于 path generation、path execution、fixed-route execution、HIL 或送达成功。

`2026-06-11 19:25` direct Robot API 复跑定位了上一轮 PC proxy 回归：
`o10-amcl-nav2-runtime-wrapper-failure-1781172997846` 的直接原因是 outer helper
timeout。该 artifact 中 managed runtime 已启动、`/initialpose` 已发布、
`/amcl_pose` 已观测，`last_successful_phase=lifecycle_probe`，但 helper 在
`current_command=timeout 8 ros2 topic echo --once /map` 时被 PC proxy/upper wrapper 的
约 `84s` process cap 打断，因此写成 `blocked_with_root_cause` 且
`path_generation_attempted=false`。同一现场随后用 direct Robot API 固定 30s body
复跑成功：

- `POST /api/nav2/proof/refresh` HTTP 200。
- `evidence_ref=o10-amcl-nav2-runtime-1781173633739`。
- `managed_runtime_started=true`、`managed_runtime_cleanup_ok=true`。
- `initialpose_published=true`、`amcl_pose_observed=true`。
- `planner_server_active=true`。
- `path_generation_attempted=true`、`path_generation_succeeded=true`、
  `path_generated=true`、`path_point_count=32`。
- `root_causes=[]`、`blockers=[]`。
- `publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、
  `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`。

清理读回显示没有 `o10_amcl_nav2_runtime_proof`、`map_server`、`amcl`、
`planner_server`、`lifecycle_manager`、`controller_server` helper 残留；
`ros2 topic info /cmd_vel` 为 `Unknown topic '/cmd_vel'`。`lsof /dev/ttyS5` 与
`fuser -v /dev/ttyS5` 均无 holder 输出。`ps` 中只有常驻
`upper_robot_api.py --base-port /dev/ttyS5` 服务参数包含底盘串口字符串，不代表本轮
helper 打开了 WAVE ROVER UART。后续若经 PC proxy 再次出现 wrapper timeout，应优先调整
PC proxy/upper API timeout 预算，而不是把它判为 map 或 planner 回归。

`2026-06-11 23:45` PC fixed proxy 重新执行安全 evidence recapture 时，
`POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
返回 HTTP 200，说明 proxy/upper timeout 预算没有先截断；但上位机最新 artifact
`o10-amcl-nav2-runtime-1781183302822` 重新落到 `blocked_with_root_cause`：

- `planner_server_active=true`
- `path_generation_requested=true`
- `path_generated=false`
- `path_generation_succeeded=false`
- `path_point_count=0`
- blockers 为 `map_to_odom_not_observed`、
  `map_to_base_link_blocked_by_missing_map_to_odom`（detail: `/tf_topic_missing`）、
  `base_link_to_laser_frame_not_observed` 和 `localization_not_ready_for_path_generation`

因此本轮 root cause 不再是 PC/upper wrapper timeout，而是 managed no-motion runtime 内
localization TF 未成链：`map -> odom -> base_link -> laser_frame` 没有在 proof 窗口
同时被观测。后续应优先检查 AMCL frame 参数、`tf_broadcast`、static lidar TF 启动时机和
proof collector 的 TF 观测窗口；仍不得用 NavigateToPose、`/cmd_vel` 或
`/api/base/manual` 绕过 no-motion 证明。

`2026-06-12 02:50` PC full safe evidence sweep 重新通过 fixed proxy 串起
localize reset 与 Nav2 no-motion proof refresh。PC summary 在巡检前能读到上一轮
Nav2 latest `path_generated=true/path_point_count=30`，但本轮 refresh 后再次回落：

- `localize/reset`：HTTP 200，`status=blocked_with_root_cause`，
  `initialpose_published=true`，`amcl_pose_observed=false`，
  `managed_runtime_cleanup_ok=false`。
- `nav2/proof/refresh`：HTTP 200，`status=blocked_with_root_cause`，
  `planner_server_active=true`，`path_generation_requested=true`，
  `path_generated=false`，`path_generation_succeeded=false`，`path_point_count=0`。
- 边界仍保持 no-motion：未执行 NavigateToPose，未发布 `/cmd_vel`，未调用
  `/api/base/manual` 成功路径，未打开 WAVE ROVER UART。

因此当前结论不是“Nav2 已稳定可用”，而是 no-motion proof 已具备 PC 触发入口，但运行时
稳定性仍不足。下一轮应优先固定 managed runtime cleanup、AMCL pose/TF 观测窗口和 planner
输入一致性，再谈真实移动或固定路线执行。

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
  --managed-map-yaml trashbot_map.yaml \
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
  -d '{"timeout_s":20,"managed_runtime_opt_in":true,"managed_timeout_s":20,"managed_map_yaml":"trashbot_map.yaml","initialpose_opt_in":true,"initialpose_x":0.0,"initialpose_y":0.0,"initialpose_yaw":0.0}'
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
TF。PC 代理 body 固定为 `timeout_s=30`、`managed_runtime_opt_in=true`、
`managed_timeout_s=30`、`initialpose_opt_in=true`、`initialpose_x/y/yaw=0`、
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
从 `2026-07-11 17:43` 起，读取 latest artifact 时必须先看 managed runtime /
lifecycle readiness，再决定是否解释 `/scan` attempts：

- 如果 `managed_runtime_started=true` 且 `/map_server`、`/amcl` 已由 lifecycle CLI
  或 managed wait 证明 active，但 `amcl_tf_root_cause` 仍是 `/tf_topic_missing`、
  `map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom` 等定位 blocker，
  helper 会直接返回 `managed_runtime_*_root_cause_fast_path`，同时把
  `/scan.probe.boundary` 记为 `scan_probe_skipped_after_managed_runtime_lifecycle_ready`。
- 只有在 lifecycle readiness 未成立时，才继续消费 BEST_EFFORT / RELIABLE `/scan`
  attempts、`sample_timing` 和 QoS/source inventory 细节。

这样 latest artifact 就不会因为重复 `/scan` echo 再次停在 `partial_runtime_in_progress`，
而能优先把 blocker 收敛到更前置的 runtime / TF / localization 层。
`2026-07-11 23:49` 起，true-board latest 若再次命中 `managed_runtime_wait_timeout`，还要同步读：

- `managed_runtime_wait_result.history[*].node_list.boundary`
- `managed_runtime_wait_result.history[*].node_list.fallback.boundary`
- `managed_runtime_wait_result.history[*].node_list.fallback.node_names`

因为 `rclpy_node_names_failed` 已不再等于“graph 一片空白”。如果 artifact 显示
`rclpy_node_names_failed_with_ros2_node_list_fallback_observed`，说明 child Python 自身仍有
runtime/import/timeout 问题，但 ROS CLI graph 已经能看到 `/map_server`、`/amcl`，下一轮应优先
修 child runtime boundary 或继续做 lifecycle recheck，而不是重复把 blocker 写成纯 wait timeout。

同样，`amcl_rclpy_probe` 若进入 `probe_mode=ros2_cli_fallback`，closeout 必须先检查
`fallback_boundary=cli_amcl_inventory_*`、`rclpy_import_failure_classification`、
`topic_endpoint_summaries["/tf"]` / `["/tf_static"]` 与 `/amcl` node info。只要 CLI inventory
已经看到 `/tf` 或 `/tf_static`，最终 blocked reason 就不应再写成泛化 `/tf_topic_missing`；若参数仍缺，
应优先收口为 `amcl_param_probe_failed`。

`2026-07-12 00:49` 起，fixed-route/no-motion 现场 closeout 还必须优先读取
`proof.managed_runtime_wait_result.graph_wait_summary`。这一层会把 wait 循环里的 child
Python node graph probe 与 `ros2 node list` fallback 压成 final 字段：

- `latest_node_list_boundary`
- `latest_ros2_node_list_boundary`
- `fallback_used`
- `fallback_observed`
- `observed_node_names`

如果 final `reason` 是 `ros2_node_list_timeout`、`ros2_node_list_empty_after_wait`、
`ros2_node_list_failed` 或 `managed_runtime_required_nodes_not_observed`，说明 runtime wait
已经自然结束并给出更窄 graph blocker；不得再引用上一轮 partial artifact 的
`current_command.command=ros2 node list` 当作最新结论。AMCL/TF source closeout 也要看
`commands.tf_source_probe.amcl_rclpy_probe.probe_mode`：当值为 `ros2_cli_fallback` 时，
说明 helper 已在不依赖 rclpy 的情况下读取 `/tf`、`/tf_static`、`/amcl` node info 和参数
fallback。只要 AMCL pose、dynamic `map->odom` 或 downstream `map->base_link` 任一 gate 未 ready，
fixed-route proof 必须继续保持 `path_generation_attempted=false`、`path_generated=false`，
不能进入 route execution 或任何 motion gate。

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

2026-06-11 04:45 起，helper 在慢 `tf2_echo` 前先采集 AMCL/TF source snapshot，
避免 upper timeout 时丢失下一层 root cause。`/api/localize/reset` 和
`/api/localize/proof/latest` 会继续透传 `tf_topics_observed`、`tf_static_observed`、
`tf_frame_inventory`、`amcl_pose_frame_id`、`amcl_node_publishers`、
`amcl_node_subscribers`、`amcl_tf_broadcast_param`、`amcl_frame_params`、
`map_frame_observed`、`odom_frame_observed` 和 `amcl_tf_root_cause`。这些字段只用于判断
AMCL 是否实际广播 `map->odom`、managed static TF 是否存在、frame id 是否一致；
不代表路径执行、底盘运动或 HIL 通过。

2026-06-11 05:05 起，source snapshot 不再依赖多条串行 `ros2 param/node`
CLI。helper 会在同一 Python 进程内用短生命周期 rclpy probe 查询 `/amcl` 的
`tf_broadcast`、`global_frame_id`、`odom_frame_id`、`base_frame_id` 和 graph
publisher/subscriber，并新增 `amcl_param_probe_ok`、`amcl_node_info_observed`、
`tf_source_root_cause_detail`、`amcl_broadcast_conditions`。如果 `/amcl_pose` 已在
`map` frame 发布但 `map->odom` 不出现，artifact 必须进一步指出是
`tf_broadcast=false`、AMCL frame 参数不一致、`/scan`/`/map` 输入缺失，还是
`odom->base_link` 等 static TF 输入缺失。

managed localization runtime 也会在日志和 artifact 中记录 static TF source：
`managed_static_tf_processes` 保存 `odom->base_link`、`base_link->laser_frame` 两个
`static_transform_publisher` 的进程角色，`static_tf_source_observed` 只有在进程源和
`/tf_static` 观测同时成立时才为 true。这样下一轮能区分“static publisher 没启动”、
“进程启动但 `/tf_static` QoS/timing 未读到”和“AMCL 自身未广播 `map->odom`”。

2026-06-11 05:25 起，managed localization runtime 不再用两个独立
`static_transform_publisher` 进程发布 static TF。helper 改为启动一个
`managed_static_tf_broadcaster` rclpy 节点，用同一个 `StaticTransformBroadcaster`
一次性发布并周期性刷新同一组 transient-local static transforms：

- `odom -> base_link`
- `base_link -> laser_frame`

这样 late subscriber 读取 `/tf_static` 时只需要接收同一个 source 的 TFMessage，
不会再依赖两个独立 CLI publisher 的发现顺序或 latch timing。artifact 中
`managed_static_tf_processes.source_strategy` 会写
`single_rclpy_static_transform_broadcaster_transient_local`，同时继续用
`observed_roles=["static_tf_base_laser","static_tf_odom_base"]` 证明两条 edge 都由
本轮 source 覆盖。

同轮真实上位机 evidence：

- artifact：
  `sprints/2026.06.11_05-25_static_tf_broadcaster/artifacts/remote_capture/localization_reset_latest.final.remote.json`
- `status=nav2_no_motion_localization_runtime_observed`
- `tf_chain_observed.map_to_odom=true`
- `tf_chain_observed.odom_to_base_link=true`
- `tf_chain_observed.base_link_to_laser_frame=true`
- `tf_chain_observed.map_to_base_link=true`
- `tf_frame_inventory.static_edges` 同时包含 `odom -> base_link` 与
  `base_link -> laser_frame`
- `root_causes=[]`

helper 还会在 TF source inventory 已完整时跳过后续慢 `ros2 topic/node info`
诊断，改用同轮 rclpy graph、AMCL 参数、`/amcl_pose` 和 TF inventory 作为
no-motion fast path，避免在 upper/PC 固定预算内已经成功后又被诊断 CLI 拖成
timeout。该 fast path 不扩大权限：仍不触发路径规划、运动控制、底盘 UART 或 HIL。

2026-06-11 08:05 起，map lifecycle 的 `/scan` 观测同样采用稳定化采样。失败
artifact 曾证明 `/scan` 在 topic list 中存在、`/map` 与 YAML/PGM 已成功，但一次性
`ros2 topic echo --once /scan` 可能在 DDS discovery 或聚合首帧窗口内超时。helper
现在用 sensor_data QoS 的 `/scan` echo 做最多 2 次独立尝试，并把每次尝试写入
artifact；`/scan_once_observed` 仍必须为 true 才能进入 clean pass。这一步只证明
no-motion map lifecycle material，不证明地图质量、AMCL 定位、Nav2 规划、固定路线
执行或 delivery success。

2026-06-11 11:05 起，任何真实上车 Nav2/path proof 或后续运动实跑前，应先确认
上位机 ROS graph 没有历史 `waypoint_manager`、`map_recorder`、
`task_orchestrator` 残留。`sprints/2026.06.11_11-05_upper_ros_quiescence_baseline/`
已在 `root@192.168.1.11:37878` 上清理三组三类目标残留，并记录
`upper_ros_quiescent=true`：清场后目标 `ps` 过滤为空，`ros2 node list` 不再出现这些
节点，`/dev/ttyS5`、`/dev/ttyACM0` 和视频设备无 `lsof/fuser` 占用输出，
`trashbot-upper-robot-api.service` 与 `trashbot-local-webrtc-camera.service` 仍为
active。该基线只是后续定位、planner readiness、Nav2 或运动证据的前置清洁条件，
不证明路径执行、固定路线运行、真实运动、HIL pass 或 delivery success。

2026-06-11 14:05，PC workstation 用临时本机 API `http://127.0.0.1:18791`
通过固定代理触发真实上位机 `http://192.168.1.11:8787` 的
`/api/localize/reset`。本轮只证明 PC 触点可以触发 no-motion `/initialpose + AMCL`
定位材料：

- `proxy_status=refresh_forwarded`
- `remote_endpoint=/api/localize/reset`
- `evidence_ref=o10-amcl-nav2-runtime-1781157704384`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `amcl_pose_frame_id=map`
- `amcl_frame_params.base_frame_id=base_link`
- `amcl_frame_params.global_frame_id=map`
- `amcl_frame_params.odom_frame_id=odom`
- `root_causes=[]`

该 smoke 故意向 PC proxy 发送包含 `/api/base/manual`、`cmd_vel` 和运动危险字段的
浏览器 body；workstation route 忽略 body，仍只调用固定 `/api/localize/reset`。
本轮没有调用 NavigateToPose、`compute_path_to_pose`、`/cmd_vel`、
`/api/base/manual` 或 fixed-route execution，也没有写 WAVE ROVER UART。
`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、
`robot_control_executed=false`、`sends_motion_commands=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false` 保持不变。

Cleanup 只读 SSH 复核显示 `trashbot-upper-robot-api.service=active`，无长期
localize/Nav2/AMCL/helper 进程残留，`/dev/ttyS5` 与 `/dev/ttyACM0` 的 `lsof/fuser`
均无输出。该证据仍不证明路径执行、固定路线运行、真实运动、HIL pass 或 delivery
success；它只是后续 planner readiness / path proof 的定位前置材料。

2026-06-11 19:45 起，PC workstation 的固定 `检查路径（高级）` 代理和上位机
Nav2 helper 使用分层 timeout 预算：上位机 helper cap 为 132s，覆盖固定
`timeout_s=30` collector、`managed_timeout_s=30` runtime、`path_generation_timeout_s=30`
以及 helper 启动/路径/managed/initialpose 余量后的 120s raw 预算；PC proxy
fetch timeout 为 150s，明确比上位机 helper cap 多出 HTTP 返回余量。该修复只处理
PC/upper wrapper timeout 误报，不改变 no-motion 合同：仍不执行 NavigateToPose，不发布
`/cmd_vel`，不调用 `/api/base/manual`，不打开 `/dev/ttyS5`，也不证明 fixed-route
execution、真实运动、HIL pass 或 delivery success。

2026-06-12 03:20 起，Nav2 no-motion path proof 不再对 `free=0` 的 map 继续调用
`ComputePathToPose`。真实上位机当前 `/root/rober/onboard/runtime/maps/*.yaml` 对应 PGM
全部为 `free=0`，只有 unknown/occupied cell；这类地图不能作为可导航地图质量证据。

新收口语义：

- `path_generation_boundary=path_generation_blocked_by_map_has_no_free_cells`
- `root_causes=[{"layer":"map quality","reason":"map_has_no_free_cells_for_nav2_path_proof"}]`
- `path_generation_attempted=false`
- `path_generated=false`
- `path_point_count=0`

这不是 Nav2 运行时包缺失，也不是 PC proxy timeout；它是建图质量 blocker。后续要进入
定位移动或 fixed-route execution，必须先采到至少包含 free cell 的真实地图，再重跑
localize/Nav2 no-motion proof。该结论仍保持 no-motion 边界：不发布 `/cmd_vel`，不调用
`/api/base/manual`，不执行 NavigateToPose。

2026-06-12 04:05 起，`/api/map/list` 也会直接暴露同一份地图质量摘要。真实上位机
当前 13 张 YAML 地图均为 `free=0`，因此 PC 侧可在进入 Nav2 proof 前提示“当前地图不
可导航，需要重新建图”。这只是地图质量 readback，不代表已经完成重新建图或 fixed-route
execution。

2026-06-12 04:25 起，PC 普通地图卡片新增 `重新建图` 与 `保存地图` 两个普通按钮，
仍只调用固定 map lifecycle 代理。真实 PC proxy 已执行一次 `/api/map/start` no-motion
LiDAR+SLAM 窗口并得到 `o3-map-lifecycle-1781190084998`，但随后 `/api/map/list`
仍显示 `usable_map_count=0`、`no_free_cell_map_count=13`。因此建图控制入口已通，
可导航地图仍未完成；进入定位移动前仍必须采到含 free cell 的地图。

2026-06-25 14:50 起，上位机新增只读 `/api/map/preview`。该入口仅从
`/root/rober/onboard/runtime/maps` 读取安全 basename 对应的 YAML/PGM，校验 YAML 和
image 路径仍在 maps 目录内，并把 P5 PGM 用标准库转成 PNG data URL 给 PC 视口展示。
PC 代理固定为 `GET /api/robot-control/map/preview?baseUrl=...`，不接受动态 endpoint，
不启动雷达/建图，不执行 Nav2，不调用 `/api/base/manual` 或 `/cmd_vel`。它只解决“地图
所见即所得”的读图入口；fixed-route 是否能执行仍取决于定位、Nav2 execution 和送达证据。

2026-06-25 15:00 起，PC 地图视口的雷达 marker 只在 map-frame pose 已读到时叠在机器人
marker 上并显示脉冲圈；若雷达 lifecycle 已运行但 AMCL/map-frame pose 未读到，视口直接
显示“雷达已运行，位置未读到”。该规则是 fixed-route 前的显示围栏：不能用运行中的雷达
替代定位，也不能把未知坐标画成已知坐标。

2026-06-25 15:10 起，PC 地图视口还会画最近 Nav2 goal 的目标点。PC latest 代理只读
`/api/nav2/goal/execution/latest`，把 `latest_result.goal_request` 的 map-frame x/y/yaw
压成短 key values；前端用真实地图 `origin + resolution + width/height` 换算到 PGM 视图。
这推进 fixed-route 的所见即所得：现场能看到最近目标点落在地图哪里。它仍不是完整路径
轨迹，也不会重新发送 NavigateToPose。

2026-06-25 18:40 起，PC 普通地图 caption 会直接显示最新 no-motion planner path preview
是否已经叠到地图上：例如 `路线已显示 36/36 个点`。该路线线段只消费
`/api/nav2/proof/latest` 经 PC summary 提升的 `path_preview_points`，按真实地图
`origin/resolution/width/height` 转成 SVG polyline；没有地图预览时只提示“路线已准备，
刷新地图画面查看”。它仍不发送 NavigateToPose，不调用 `/api/nav2/goal/execute`、
manual、keyboard、delivery 或 `/cmd_vel`。

2026-06-25 18:50 起，PC 普通地图还会把同一条 path preview 的首尾点画成路线端点。
若已有真实 Nav2 execution latest 目标点，地图只额外显示 `起点`，避免和 `本轮目标`
重复；若没有执行目标，则显示 `起点/终点`。这些端点只表示规划 path 的首尾，不是机器人
当前位置，也不是完整路线执行成功证明。

2026-06-12 04:45 起，PC 普通 `移动/导航` 卡片新增 `重新定位`。该入口仍只调用
workstation 固定 `POST /api/robot-control/localize/reset?baseUrl=<upper-api>`，由 PC
后端转发到上位机固定 `POST /api/localize/reset`，不会接收浏览器传入的 goal、
endpoint、initialpose 参数或路径生成参数。真实 PC proxy 对
`http://192.168.1.11:8787` 的本轮结果为：

- `proxy_status=refresh_forwarded`
- `remote_endpoint=/api/localize/reset`
- `remote_http_status=200`
- `latest_proof_status=nav2_no_motion_localization_runtime_observed`
- `initialpose_published=true`
- `amcl_pose_observed=true`
- `localization_reset_observed=true`
- `managed_runtime_cleanup_ok=true`
- `hard_dangerous_true_fields=[]`

上位机 `GET /api/localize/proof/latest` 二次回读同样显示
`localization_reset_observed=true`、`managed_runtime_cleanup_ok=true`。该入口只把
AMCL no-motion 定位材料放到普通用户可理解的按钮上，不执行 NavigateToPose，不调用
`/api/base/manual`，不发布 `/cmd_vel`，不证明 fixed-route execution、真实运动、HIL
 pass 或 delivery success。

2026-06-12 05:05 起，PC 普通 `移动/导航` 卡片新增 `移动前检查`。该入口只提交
operator report 的基础现场确认：

- `operator_present=true`
- `physical_clearance_confirmed=true`
- `emergency_stop_ready=true`
- `observed_stop=true`
- `site_state=plain_motion_precheck_ready_for_review`

它显式保持以下材料为 false 或缺 ref：`external_video_recorded`、
`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、
`physical_motion_lidar_delta_proven`、`real_route_map_proven`、`delivery_success`。
真实 PC proxy 提交后，上位机 summary readback 显示基础三项为 true，但 external video、
camera visible、wheel feedback、LiDAR delta 均为 `false; ref=not_loaded`。随后本轮
PC fixed proxy 尝试 `forward speed=0.08 duration_ms=500` 且
`confirm_hil_checklist=true` 时，本机返回 HTTP 400 `operator_report_preflight_required`，
`remote_http_status=null`，缺项仍包括 external video/ref、visible camera/ref、wheel
feedback/ref 和 scan delta/ref。该结果证明普通预检查不会绕过 motion gate，也不会执行
NavigateToPose、`/cmd_vel`、`/api/base/manual` 或 fixed-route movement。

2026-06-21 起，PC 后端新增首次低速试动固定入口
`POST /api/robot-control/base/first-jog?baseUrl=<robot-api-base-url>`，用于处理
wheel feedback 与 LiDAR motion delta 必须在第一次真实动作后才能生成的循环。该入口
只允许 `forward/back/left/right`、`speed<=0.12m/s`、`duration<=800ms`，并要求
请求体 `confirm_hil_checklist=true`。2026-06-29 05:20 起，该入口不再把 operator report
里的外部视频、可见相机、wheel feedback 或 LiDAR delta 当作发车前置；这些材料只作为试动后验收输出或建图/送达材料。
PC 本机固定代理会在安全确认后转发远端 `/api/base/manual`，仍不直连 `/cmd_vel`，也不等于 fixed-route movement、
Nav2 execution 或 delivery proof。

同日 23:50 起，普通 PC 首屏把 first-jog 接成“记录现场画面 -> 试动一下”的普通流程。
`记录画面` 只提交 external video ref，不提交 wheel feedback、LiDAR delta 或 route map
成功；`试动一下` 固定请求 `forward speed=0.08 duration_ms=500` 的 first-jog 代理。
最新口径下，缺外部视频/可见相机材料不再返回 HTTP 400；只要现场安全确认已勾选，就会通过固定代理发出限速限时
`/api/base/manual`，再用回包和只读反馈判断 wheel raw L/R、LiDAR delta 或其它 motion evidence。
因此它只是 PC 控制触点推进和低速试动入口，不是路线移动、建图移动或自动导航完成。

2026-06-22 起，`sprints/2026.06.22_01-35_motion_map_runtime_probe/` 把该入口推进到
真实 LiDAR delta 和小范围地图材料：

- PC first-jog 固定代理在真实上位机上返回 `command_forwarded`，速度 `0.08m/s`、
  时长 `800ms`。
- 运动前后 `/scan` JSON 对比得到 `paired_bins=162`、`median_abs_diff_m=1.735`、
  `changed_bin_ratio=1.0`，满足现场 HIL execution pack 的 scan delta 阈值。
- Operator report 已提交 `physical_motion_lidar_delta_proven=true`，但仍保持
  `wheel_feedback_lr_nonzero_proven=false`，因为当前反馈 artifact 没有原始 L/R 轮速。
- 修复 `map_recorder.py` 后，PC map lifecycle 生成
  `fixed_free_cells_20260622_0112.yaml/.pgm`，`map/list` 显示
  `map_usable_for_navigation=true`，PGM 复核含 `394` 个 free pixels。

该证据说明 PC 可连接和触发受控试动、LiDAR 观察到真实环境变化、小范围地图可保存为
含 free cells 的 map_server 兼容地图。仍未完成完整路线采集、route.csv/keyframe、
Nav2 path/runtime 执行、外部视频和 wheel L/R 非零反馈。

2026-06-27 10:50 再次读取真实上位机 latest artifact 后，PC 首屏 Nav2 诊断补充
IMU 姿态变化事实：

- `nav2_goal_execution_latest.json` 显示最近一次 Nav2 action 返回 `goal_succeeded`，
  `base_command_mode=pwm`，`base_command_summary.nonzero_command_count=49`。
- 同一执行窗口底盘反馈日志有 `239` 条有效样本，但
  `base_feedback_summary.wheel_feedback_lr_nonzero_proven=false`，
  `latest_pair.left_speed=0.0`、`latest_pair.right_speed=0.0`。
- 同一批反馈里的 IMU 姿态变化已观测到：
  `imu_attitude_delta_observed=true`，`max_abs_roll_delta=4.387221`，
  `max_abs_pitch_delta=24.210531`。
- 因此 PC 普通首屏现在同时显示三件事：Nav2 已发非零底盘命令、车身姿态有变化、
  wheel raw L/R 仍为 `0/0`。这能把问题从“雷达/相机阻塞”或“完全没有运动迹象”
  收敛到“执行窗口 wheel raw L/R 非零复验未闭合”。

结论仍保持保守：IMU 姿态变化只能作为运动迹象，不能替代 wheel raw L/R 非零；
完整 Nav2 路线执行仍需要下一次按 `next_execution_base_command_mode=ros` 复验，
并在同一执行窗口证明 L/R 非零。

2026-06-28 11:55 起，PC workstation 的 Nav2 readiness 读数会把
`/api/nav2/status.proof_latest` 中的嵌套路由证明纳入同一摘要。这个兜底只解决
“路线点实际存在但 PC 端只看直接 proof latest 导致显示 0 点”的读数问题；
它不发 NavigateToPose goal，不发布 `/cmd_vel`，不调用 `/api/base/manual`，也不证明
wheel raw L/R 非零、完整路线执行或 delivery success。现场发车仍必须在普通首屏勾选安全确认后显式执行路线，
并用同一执行窗口的 goal result、wheel raw L/R 和送达材料收口。

2026-06-28 12:07 起，`o10_amcl_nav2_runtime_proof.py` 修正真实上位机 Nav2 proof 的三类误判：
`command -v ros2` preflight 从 3 秒放宽到 6 秒，避免 API 子进程首次 source ROS/workspace 时被误判为
`ros2_command_unavailable_after_bash_source`；AMCL `/initialpose` 显式使用 `stamp=0`，让 TF 使用 latest
transform，避免 managed runtime 刚启动时出现 `extrapolation into the past`；`odom->base_link`
既接受 no-motion `/tf_static`，也接受真实桥接节点在 `/tf` 动态发布的里程计 TF，避免把动态 odom
误报为缺 static TF。真实上位机同步脚本后，固定 no-motion body 的
`POST /api/nav2/proof/refresh` 返回 `proof_state=nav2_no_motion_path_generation_runtime_observed`、
`path_generated=true`、`path_point_count=18`，`tf_chain_observed.map_to_odom/odom_to_base_link/base_link_to_laser_frame/map_to_base_link`
均为 true，`blocked_commands_not_sent` 仍包含 `T=1/T=13/T=130/T=131`、`/cmd_vel` 和
`/api/base/manual`。这证明自动驾驶服务、定位 TF 和 planner 路线生成的 no-motion blocker 已解除；
仍不等于真实 NavigateToPose 执行、wheel raw L/R 非零、完整路线通过或 delivery success。

发车验收的下一步是：普通 PC 首屏勾选安全确认后显式执行图上路线，用同一执行窗口的 Nav2 goal result、
wheel raw L/R 非零和送达材料收口；如果 wheel raw L/R 仍为 `0/0`，问题就不再是 planner/TF 路线准备，
而要继续查底盘命令模式、bridge feedback 或 WAVE ROVER 反馈链路。

2026-06-28 12:12 起，PC 侧不再要求 no-motion proof 的 managed runtime 常驻，才能把图上路线判为可执行。
原因是 `/api/nav2/proof/refresh` 只负责生成路线证据，结束后会清理临时 runtime；真正
`/api/nav2/goal/execute` 会按固定代理重新启动 bounded NavigateToPose runtime。真实 live summary
验证形态为：`nav2_stack_running=false`、`controller_server_requested=false`、`path_generated=true`、
`path_point_count=18`、`robot_pose` 已读到，PC `nav2_goal_ready=true`、`nav2_goal_blockers=[]`。
这只解除 PC 误挡，仍不证明 wheel raw L/R 非零或真实路线执行完成。

2026-06-27 14:47 起，PC summary 额外暴露机器可读字段
`readback_summary.nav2.goal_execution_mode_rerun_status`。当前 live 形态会被标成
`pending_ros_rerun_after_pwm`：最近 artifact 来自旧 PWM 执行，下一次执行模式已经是 ROS/T=13。
普通首屏据此把自动驾驶诊断写成“旧 PWM 结果，等待 ROS 复验”，避免把旧结果误读成当前 ROS
模式已经失败。该字段只用于诊断与 UI 收口，不自动执行 NavigateToPose。

2026-07-11 20:46 起，fixed-route/no-motion 现场 path proof 读取顺序再细化为
`board_source_preflight -> amcl_readiness_summary -> tf_readiness_summary -> path_generation_gate`。
`amcl_readiness_summary` 必须同时看 lifecycle active 和 `/amcl_pose` sample timing；`/amcl_pose`
有样本但 stamp stale，或 `/amcl` lifecycle inactive，都不能进入路线执行。`tf_readiness_summary`
必须把 dynamic `map_to_odom` 与 downstream `map_to_base_link` 分开：`map_to_base_link` 只是在
`map->odom` 与 `odom->base_link` 成立后的 derived gate，不能替代 AMCL 发布 dynamic
`map->odom`。

本轮 live artifact
`sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json`
证明 source/CLI 已 ready，但 route 仍不能执行：

- `board_source_preflight_ready`、`ros2_cli_ok=true`、`rclpy_import_ok=true`；
- `managed_runtime_started=true`；
- `/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`，sample 可读但 stale；
- `/amcl` lifecycle 为 inactive，AMCL gate 不 ready；
- dynamic `map_to_odom` 未观测，`map_to_base_link` 被 `map_to_odom` 阻塞；
- `path_generation_requested=true`，`path_generation_attempted=false`，`path_generated=false`；
- no-motion 安全字段继续为 false：`safe_to_control`、`publishes_cmd_vel`、
  `calls_base_manual`、`robot_control_executed`、`route_execution_success`、`delivery_success`、
  `hil_pass`、`uses_base_uart`。

这说明 fixed route 下一步仍是 no-motion localization/path readiness 修复，不是发车。
只有 `path_generation_gate.generated=true` 且 point count 大于 0，才可作为 planner-only
path proof；它仍不等于 NavigateToPose route execution、wheel feedback、HIL pass 或 delivery
success。

2026-07-12 01:50 起，如果现场 fixed-route/no-motion proof 仍卡在 managed runtime graph wait，
读取顺序再前移一层到 `proof.ros2_graph_timeout_root_cause`。该字段的职责是把
`ros2_node_list_timeout` 拆成 ROS daemon/DDS graph discovery、CLI/plugin/import、
workspace source/env、managed process lifecycle、TF secondary 或 unclassified 六类之一。

fixed-route 收口时按这个顺序读：

1. `ros2_graph_timeout_root_cause.classification`
2. `primary_candidate.reason`
3. `evidence_priority`
4. `probes.source_amortized_batch`
5. `excluded_candidates`
6. `remaining_candidates`
7. `probes.managed_process.expected_nodes / observed_nodes / lifecycle_probe_status`
8. `evidence_boundary`

2026-07-12 02:51 起，`probes.source_amortized_batch` 是 graph timeout 的主证据。旧的逐命令
probe 会在每条 `ros2 node list`、`ros2 node list --help`、`ros2 topic list` 前重新
source ROS/workspace；当 source 本身约 5 秒时，2 到 5 秒的 per-command timeout 不能直接说明
ROS2 subcommand 或 rclpy graph 卡住。source-amortized batch 只 source 一次，然后批量记录：

- `source_stage`；
- `commands.ros2_node_list`、`commands.ros2_node_list_no_daemon`、
  `commands.ros2_daemon_status`、`commands.ros2_node_list_help`、
  `commands.ros2_topic_list`；
- `workspace_environment.summary`；
- `rclpy_graph_stage_stream.last_started_stage / last_completed_stage / boundary`。

因此 fixed-route/no-motion closeout 里，若 `evidence_priority=source_amortized_batch`，
必须先用这组字段判断旧 timeout 是否被 source overhead 污染。只有 batch 证明 help 和 rclpy
startup stage 仍卡住时，才保留 CLI/plugin/import 方向；如果 help 已完成但 graph command
timeout，下一步应优先查 daemon/DDS discovery、managed process graph visibility 或 lifecycle
ready，不应继续重复上一轮 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`。

若 classification 是 `ros2_daemon_or_dds_graph_discovery_timeout`，且
`excluded_candidates` 已排除 `workspace_source_or_env_mismatch` 与
`ros2_cli_plugin_or_import_timeout`，下一步应查 ROS daemon/DDS graph discovery 或进程 graph
可见性，不应直接跳到 `/tf_topic_missing` 或 path generation。若 `remaining_candidates` 中出现
`tf_runtime_secondary_after_graph_blocked`，它表示 `/tf_topic_missing` 只是 graph blocked 后的
secondary/readback；只有 graph probe 恢复后 `/tf` 仍缺失，才能把 TF runtime 转成主因。

`probes.managed_process.lifecycle_probe_status=skipped_after_ros2_graph_timeout` 时，不能把
`map_server`、`amcl` 或 `planner_server` 写成已证明 inactive。该状态只说明 graph wait 阻塞后
lifecycle proof 未完成。真正的 fixed-route path proof 仍必须等待：

- AMCL/lifecycle gate 可读且 active；
- `/scan`、`/amcl_pose`、`/map`、`/tf`、`/tf_static` freshness/source 形成当前窗口证据；
- dynamic `map->odom` 与 downstream `map->base_link` ready；
- `path_generation_attempted=true` 且 `path_generated=true`。

在此之前，`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`、`uses_base_uart=false` 必须保持 false；该字段只证明 root-cause isolation，
不证明路线执行、HIL pass 或送达成功。

2026-07-12 03:52 起，同一 root-cause 对象新增
`daemon_dds_split`，用于把 `ros2_daemon_or_dds_graph_discovery_timeout` 拆到可执行层级。
fixed-route/no-motion closeout 要按下面顺序读：

1. `daemon_dds_split.primary_candidate.candidate`：稳定候选只接受
   `ros2_daemon_state_timeout`、`dds_discovery_or_domain_mismatch`、
   `workspace_source_or_env_mismatch`、`managed_process_lifecycle_visibility_blocked`、
   `graph_command_budget_insufficient`、`ros2_cli_no_daemon_unsupported`。
2. `daemon_dds_split.safe_environment_summary`：只读 ROS/DDS/domain 和路径 presence 摘要，
   不要求完整 env dump，也不得把空 `ROS_DOMAIN_ID` 或空 `RMW_IMPLEMENTATION` 单独解释成失败。
3. `daemon_dds_split.daemon_command_summaries`：如果 `reset_skipped=true`，用
   `reset_skip_reason` 解释为什么没有 stop/start；如果 `reset_attempted=true`，优先比较
   reset 前 `ros2_daemon_status` 与 reset 后 `ros2_node_list_after_daemon_reset`、
   `ros2_topic_list_after_daemon_reset`。
4. `daemon_dds_split.managed_lifecycle_visibility_summary`：graph blocked 时，这里只能证明
   lifecycle visibility 被遮蔽，不能直接证明 `/map_server`、`/amcl` 或 `/planner_server`
   inactive。
5. `daemon_dds_split.graph_budget_summary`：确认本轮是 bounded budget 问题，还是 reset 后仍
   有 DDS/domain/RMW discovery 层 timeout。

`2026-07-12 04:51` 起，同一 closeout 还要继续读
`daemon_dds_split.daemon_safe_graph_readback`。推荐顺序：

1. `reset_attempted/reset_completed/reset_skipped/reset_skip_reason`
2. `commands.ros2_daemon_stop/start/status_after_reset`
3. `commands.ros2_node_list_after_daemon_reset`
4. `commands.ros2_topic_list_after_daemon_reset`
5. `graph_readback.node_list_outcome/topic_list_outcome`
6. `primary_conclusion`
7. `next_step`

这里的 `primary_conclusion` 只用于判断 daemon-safe reset 后 graph 是 timeout、empty 还是
observed，以及下一跳应回 lifecycle/localization gate 还是继续收窄到 DDS/domain、graph
budget 或 managed lifecycle visibility。它不等于 path generation ready，更不等于 route
execution、HIL pass 或 delivery success。

daemon stop/start 是 graph 层 no-motion probe，只允许作为 `ros2` daemon-safe retry；
它不发送 NavigateToPose，不发布 `/cmd_vel`，不调用 `/api/base/manual`，也不打开 WAVE ROVER
UART。`daemon_dds_split.next_live_command` 只能作为下一轮只读/daemon-safe 复验入口，不能被
PC 或 fixed-route UI 当成发车命令。即使 split 明确排除了 daemon 状态，也仍需恢复
AMCL/TF/path gate 后，才允许 planner-only path generation proof；route execution、HIL pass
和 delivery success 仍需要独立真实证据。

`2026-07-12 08:55` 起，fixed-route/no-motion closeout 还必须先读
`proof.map_lifecycle_preflight.lifecycle_cli_budget_recovery`。该字段把
`ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` 拆成 first/retry attempts，
保留 command、timeout budget、elapsed、stdout、stderr、returncode、timed_out、
classification 和 graph visibility snapshot。

本轮 live strict no-motion artifact：
`sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`。
读取结论：

- `board_source_preflight.classification=board_source_preflight_ready`。
- `/amcl` first attempt 10s timeout，retry 18s budget 内返回 `active [3]`，分类为 `active`。
- `/map_server` first attempt 10s timeout，retry 返回 `Node not found`，分类为
  `lifecycle command failed`，因此 `map_server_active=false`。
- lifecycle 未 clean，`scan_once`、`map_once`、`odom_once` 和 `tf_source_probe` 均为
  `*_skipped_until_lifecycle_cli_readback_clean`。

因此 fixed-route 工作不能基于该 artifact 进入 planner-only path generation、NavigateToPose、
route execution 或 delivery closeout。下一步应先恢复 `/map_server` lifecycle/graph readback；
只有 `/map_server` 与 `/amcl` 都 clean 后，才继续读取 `/scan`、`/map`、`/tf` 和 path gate。
本轮仍固定：`safe_to_control=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false`、`path_generation_attempted=false`。

`2026-07-12 09:54` 起，fixed-route/no-motion closeout 的第一读数改为
`proof.map_server_graph_lifecycle_visibility`。它只回答 `/map_server` graph/lifecycle
visibility，不回答 route 是否能跑。字段读法如下：

- `canonical_classification=map_server_node_absent`：graph 或 lifecycle retry 证明
  `/map_server` 当前缺席，例如 retry stderr 为 `Node not found`。
- `canonical_classification=lifecycle_manager_or_process_startup_missing`：managed runtime、
  lifecycle manager 或 process startup 没有把 `/map_server` 拉到可读状态。
- `canonical_classification=daemon_or_dds_graph_visibility_failed`：`ros2 node list`、
  daemon status 或 DDS graph readback 本身不可见，不能把它误写成节点缺席。
- `canonical_classification=helper_budget_or_timing_exhausted`：graph 已见节点但 lifecycle
  command 超时，或 helper 观测窗口不足。
- `canonical_classification=map_server_lifecycle_active`：只说明 `/map_server` lifecycle
  readback active；仍必须继续验证 `/map` sample、AMCL pose、dynamic `map->odom`、planner
  path gate，才能讨论 path generation。

这个 09-54 proof boundary 是
`software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`。
它保留 08-55 的 `/amcl active [3]` 事实或明确记录新 live state regression；同时继续把
07-53 的 `/scan`、`/map`、TF 当 guarded context，而不是 primary blocker。fixed-route
流程仍不得据此发送 NavigateToPose、发布 `/cmd_vel`、调用 `/api/base/manual` 或打开
WAVE ROVER UART；`path_generation_attempted=false`、`path_generated=false`、
`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false` 必须保持。

`2026-07-12 10:54` 起，fixed-route/no-motion closeout 还要优先读取
`proof.map_server_presence_recovery`。它把 09-54 的只读 `/map_server` absent 诊断升级为
显式 recovery proof：

- `recovery_attempted=true` 且 `recovery_path.managed_runtime_requested=true`：说明 helper
  已使用 `--managed-runtime-opt-in` 尝试拉起 no-motion localization runtime。
- `managed_map_yaml.basename` / `configured_basename`：用于确认本轮请求的 map yaml；
  外部 closeout 只消费 basename、exists、sha256_prefix 和 path policy，不依赖板端绝对路径。
- `process_presence`：区分 runtime 未启动、进程提前退出、startup error 或日志中 map_server
  启动失败。
- `node_presence`：区分 `/lifecycle_manager`、`/amcl` 已可见但 `/map_server` 仍不可见，还是
  ROS graph 本身不可读。
- `lifecycle_readback.node_not_found_observed`：保留旧 `Node not found` 事实，但需要结合
  `canonical_classification` 判断它是否已经收窄。

当 `canonical_classification=lifecycle_manager_not_serving_map_server` 时，fixed-route 下一步不是
planner/path，而是检查 lifecycle manager `node_names`、map_server process/log 和 map yaml 启动。
当 `canonical_classification=managed_runtime_graph_unreadable_after_start` 时，下一步回到 ROS2 graph、
daemon、DDS/domain/RMW 环境。只有 `canonical_classification=map_server_lifecycle_active` 后，
才能恢复 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path gate 的 no-motion 检查。

该字段不改变安全边界：不发送 NavigateToPose，不发布 `/cmd_vel`，不调用 `/api/base/manual`，
不打开 WAVE ROVER UART；`safe_to_control=false`、`route_execution_success=false`、
`delivery_success=false`、`hil_pass=false` 继续固定。

`2026-07-12 11:54` 起，fixed-route/no-motion closeout 还要读取
`proof.map_server_lifecycle_activation`，它比 presence recovery 更靠近当前 blocker：

- `map_yaml_pgm_readback.yaml/pgm`：确认 map yaml 与 PGM 是否存在、可读、hash basename 和 size。
- `map_yaml_pgm_readback.fields`：确认 `image`、`resolution`、`origin` 等 required fields
  是否 valid；`mode` 缺失时以 artifact 中 `optional_missing` 记录，不能直接当作 map invalid。
- `launch_parameters`：确认 `frame_id=map`、lifecycle manager 管辖 `map_server/amcl`、
  `service_timeout_s=12.0`、`bond_timeout_s=8.0`、`RMW_FASTRTPS_USE_SHM=0` 和
  `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`。
- `runtime_log.events` 与 `lifecycle_manager_state_change_result`：确认是否已经走到
  `Configuring map_server`、加载 yaml/PGM、read map，然后 lifecycle manager 报
  `Failed to change state for node: map_server`。
- `canonical_classification`：优先消费
  `map_server_yaml_image_unreadable`、`map_server_yaml_invalid_fields`、
  `map_server_frame_id_missing_or_invalid`、`lifecycle_manager_map_server_name_mismatch`、
  `lifecycle_manager_map_server_namespace_mismatch`、`map_server_activate_callback_failed`、
  `map_server_lifecycle_service_timeout_with_process_alive` 或 `map_server_lifecycle_active`。

本轮 true-board artifact 已把 10:54 的
`map_server_lifecycle_not_active_after_recovery` 继续下钻为
`map_server_activate_callback_failed`：`trashbot_map.yaml` 与 `trashbot_map.pgm` 可读，
required yaml fields valid，map_server 进入 configure 并读取 map，但 activation state change
失败。fixed-route 下一步仍是 no-motion lifecycle repair；不能进入 planner-only path gate、
NavigateToPose、route execution、HIL 或 delivery。

`2026-07-12 12:55` 起，fixed-route/no-motion closeout 还要读取
`proof.map_server_transition_callback_probe`。它比 `map_server_lifecycle_activation` 再往下分一层，
用于区分 configure callback return、activate callback return、service/RPC timing、bond timing
和 process exit。当前 true-board artifact
`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`
显示：

- `canonical_classification=map_server_configure_callback_return_failure`
- `transition_sequence.observed_stage=configure`
- `transition_sequence.configure.state_change_failed=true`
- `transition_sequence.configure.map_read_completed=true`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`

因此 fixed-route 下一步仍归 Robot Software 的 no-motion lifecycle repair：检查 map_server
`on_configure` return path、map IO completion ordering、lifecycle manager ChangeState response
处理和 executor timing。它不是 `/map_server` active 证明，也不能解锁 planner-only path gate、
NavigateToPose、route execution、HIL、delivery 或 production evidence。安全字段继续固定为
false。

`2026-07-12 13:54` 起，同一字段还要消费更窄的 configure ordering 分类。当前 true-board artifact
`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`
显示：

- `board_source_preflight.classification=board_source_preflight_ready`
- `managed_runtime_started=true`
- `map_server_active=false`
- `amcl_active=false`
- `canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`
- `failure_detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`

这说明 blocker 已从 generic `map_server_configure_callback_return_failure` 收窄为 configure
ChangeState failure 与 deferred map read completion 的先后顺序问题。下一轮仍由 Robot Software
处理 lifecycle manager / map_server `on_configure` / map IO ordering；Algorithm 继续等待
`/map_server` lifecycle clean 后再恢复 `/map`、AMCL、TF 和 planner-only path gate。安全字段继续
固定为
`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`、`uses_base_uart=false`、`path_generation_attempted=false`、
`path_generated=false`。

`2026-07-12 14:54` 起，fixed-route closeout 还要优先读取
`transition_sequence.line_indices` 与 `transition_sequence.event_timestamps_s`。helper 会从多个
runtime log 候选中选择 pre-cleanup transition 证据最强的一段，避免 cleanup tail 让 line index
全部变空。如果新 live artifact 输出
`canonical_classification=map_server_changestate_response_failure_after_image_load_before_map_read_completed`，
含义是 lifecycle manager 的 ChangeState failure 发生在 `/map_server` configure callback 已进入、
`image_file` 已开始加载、但 `Read map` 尚未完成的窗口；下一步仍归 Robot Software 查 lifecycle
manager response/future timeout 与 map IO image decode completion 的顺序。该分类不能视为
`/map_server` active，也不能解锁 `/map` sample、AMCL、TF、planner-only path gate、NavigateToPose、
route execution、HIL 或 delivery。

若 artifact 输出 `map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure`，说明当轮
map_server configure 已完成并进入 AMCL configure 后失败；这只能作为 map_server blocker 已移动到
AMCL lifecycle 的 strict no-motion 证据，仍不等于 map_server active 或固定路线可执行。

`2026-07-12 15:54` 起，如果 live artifact 输出
`canonical_classification=map_server_changestate_response_false_before_map_io_completion`，
应优先读取 `service_rpc_timing.map_io_timing`。该分类表示 lifecycle manager 的 ChangeState
failure/false response 先于 `Read map ...` completion 出现，且 map IO 随后仍完成；这是
`map_server_changestate_response_failure_after_image_load_before_map_read_completed` 的更窄版本。
固定路线侧只能把它当成 Robot Software 的 map_server `on_configure` / ChangeState response
root cause，不能解锁 `/map`、AMCL、TF、planner path、NavigateToPose 或 route execution。

`2026-07-12 16:55` 起，如果 live artifact 进一步输出
`canonical_classification=map_server_on_configure_return_false_after_valid_map_io_deferred_completion`，
固定路线侧应读取 `on_configure_return_source`。该字段要求 managed map YAML/PGM readback valid、
map_server-scoped exception 未观察到，并把 `primary_source` 写成
`on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`。这只说明 root cause
从 15:54 timing 现象继续落到 Robot Software 的 `on_configure` return source bucket；仍不能消费
`/map` sample、AMCL、TF、planner-only path、NavigateToPose、route execution、HIL 或 delivery。

`2026-07-12 17:55` 的 accepted true-board artifact 最终 routing baseline 是
`canonical_classification=map_server_lifecycle_active`。如果同轮中间字段或候选分类仍出现
`map_server_loadmap_response_success_equivalent_after_changestate_failure`，固定路线侧只能把它当作
load-map ordering context，最终收口应读取 `load_map_response_from_yaml` 与
`managed_runtime_log_lifecycle_readback`。`load_map_response_from_yaml` 说明 runtime 未直接暴露
`loadMapResponseFromYaml` return code，`return_code` 应保持
`not_logged_by_nav2_map_server_runtime`；可消费的新增事实只是：
`response_status=success_equivalent_map_read_completed_before_failure`；17:55 不再把主因回退成
旧 `on_configure` / ChangeState wrapper blocker。

固定路线侧可以把
`proof.managed_runtime_log_lifecycle_readback.clean=true` 作为 `/map_server` 与 `/amcl`
lifecycle active 的软件证据；同时 `load_map_response_from_yaml.response_status` 可读取为
`success_equivalent_map_read_completed_before_failure`。这只解除 fixed-route path gate 的
map-server lifecycle 上游前置条件，不等于路线可执行。只要 closeout 仍是
`managed_runtime_graph_probe_timeout_after_lifecycle_active_log`，并且 `/map`、`/amcl_pose`、
`/tf` 或 `/scan` readback 未 clean，`path_generation_attempted=false` 和所有 motion/control
字段必须保持 false。

`2026-07-12 18:56` 起，如果 lifecycle active 已由 runtime log clean 证明，fixed-route closeout
要继续消费 helper 的下游只读 readback，而不是把
`managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 当作终点。新的读取顺序是：
`proof.artifact_closeout.primary_root_cause`、`proof.downstream_recovery_summary.scan/map/amcl/tf`、
`proof.localization_signal_freshness`、`proof.tf_readiness_summary`，再回看
`managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 作为 secondary diagnostic。只要这些
gate 仍有 `/scan_no_publisher`、`/map_once_not_observed`、`/amcl_pose_topic_missing` 或
`/tf_topic_missing`，仍不得进入 planner-only path、NavigateToPose、route execution、HIL 或 delivery。

如果同一字段输出 `map_server_changestate_response_failure_before_configure_callback_log`，含义是
lifecycle manager 已请求 configure 并收到 failure，但 artifact 未观察到 `[map_server]:
Configuring` callback log、yaml/image load 或 map read。固定路线侧应把它留给 Robot Software
继续查 ChangeState future/service discovery/executor dispatch，不要把它误读成 map IO 已完成。

`2026-07-12 21:57` Gate 2 返工后的 fixed-route 读取边界是 planner-only proof 已同轮成立，
但 route execution 仍未开始。成功 artifact
`sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`
证明 `path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`，且
`fallback_used=true`、`fallback_mode=ros2_cli_action_send_goal`。fallback 只调用
`nav2_msgs/action/ComputePathToPose`，并在 `path_goal_request.start_source` 中记录
`amcl_pose_observed_for_planner_only_start`，用于绕开 `use_start=false` 时 planner 回查当前 TF 时间窗
导致的 extrapolation。

固定路线工作流可以把这条 artifact 作为 `/scan -> /amcl_pose -> map->odom -> planner-only path`
same-run evidence；不能把它升级为 fixed-route replay、NavigateToPose、controller/BT、
`/cmd_vel`、`/api/base/manual`、route execution、delivery 或 HIL。该 gate 的安全字段必须继续读作
`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`uses_base_uart=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

`2026-07-13 07:07` 起，05:02 same-task replay packet 之后新增
`controlled_route_execution_gate_record` 合同。Algorithm helper 只读取
`same_task_replay_packet_summary.json`，复核同一
`packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id`、
`route_intent_id`、28/28/28 counts 与三份 source hash；hash、identity 或 count
任一不匹配时必须 fail closed。该 gate 的 `controlled_route_execution_gate_status` 只能表示
`fail_closed_input_packet_validated`，用于把下一步收敛到人工安全复核、current live HIL、stop path、
bounded command plan、同窗口 LiDAR/localization/TF 与 Nav2/controller execution result。它仍然是
software proof，不执行也不允许宣称 route execution、delivery、HIL 或 safe-to-control。固定路线
收口和后续消费者必须继续保留
`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false`，并显式记录 no /cmd_vel、no /api/base/manual、
no NavigateToPose、no WAVE ROVER UART。

`2026-07-13 08:09` 起，07:07 accepted gate 之后新增
`bounded_route_command_plan` 合同。Algorithm helper 只读取
`controlled_route_execution_gate_record.json` 和其中的 28 行 route CSV ref，复核同一
`packet_o3_28_pose_same_task_replay_7d57826142b0c79c`、`task_id`、`route_intent_id`、
28 rows / 27 segments、固定 false safety fields 与 literal guard。输出状态必须保持
`blocked_pending_live_safety_gate`，并且只能记录未来受控执行的保守 caps、segment distance
summary 和 abort criteria；这些字段不是实际控制命令，也不能被解释为 controller/BT 或
NavigateToPose 已开始。

08:09 bounded plan 的 no-motion 边界必须继续写明
`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、
`calls_base_manual=false`、`uses_base_uart=false`。任何后续消费者如果要把该 artifact 用作
live execution 输入，必须另行满足 operator approval、current live HIL/stop path、同窗口
LiDAR/localization/TF readiness 和 Nav2/controller result，并继续保留 no /cmd_vel、
no /api/base/manual、no NavigateToPose、no WAVE ROVER UART 作为本 sprint 的不可越界 guard。

`2026-07-20` 起，O10 的 current path gate 不再把 `path_generation_opt_in` 硬绑到
`initialpose_opt_in=true`。固定路线可以在 persistent Nav2 stack 已由安全入口启动后，走
`current_fresh_persisted_pose_no_publish` 分支生成 planner-only path；该分支必须同时满足：

- `/map_server`、`/amcl`、`/planner_server`、`/controller_server` lifecycle 均为 active；
- `persisted_pose_audit.persisted_pose_live_consumed=true`；
- 当前 `/amcl_pose` 已观测、timestamp 可解析且 freshness 为 `fresh`；
- 当前 `map->odom` 来自 dynamic TF、timestamp 可解析且 freshness 为 `fresh`；
- `map->odom.publisher_attribution_status=attributed_unique_amcl`，不能是 static、missing 或
  ambiguous multiple publishers；
- `map->base_link` 已观测，且 localization root causes 为空；
- `initialpose_publish_attempts=0`，helper `managed_runtime_opt_in=false`。

任一条件 missing、stale 或 ambiguous 时，`path_generation_precondition_gate.clean=false`，
`path_generation_attempted=false`，并在 `Persisted localization path gate` 中保留具体 blocker。
只有 gate clean 后才允许一次 `ComputePathToPose`；它只计算路线，不调用 `NavigateToPose`、
`FollowPath`、`/cmd_vel`、`/api/base/manual` 或 WAVE ROVER UART。该 path 即使生成成功，也只表示
同窗口定位与 planner readiness，可交给后续独立 motion gate 复核；不证明 route execution、
wheel feedback、HIL、safe-to-control、delivery 或 Mission Objective 0 已完成。

同日起，Upper API 会把实际外层等待预算通过 `--outer-process-timeout-s` 传给 O10 helper。
helper 从启动时建立 monotonic deadline，并固定预留 final artifact reserve；直接运行 CLI 且不传
该参数时仍保持兼容，不额外施加 outer deadline。所有带阶段记录的子命令 timeout 都会收敛到
`remaining - final_artifact_reserve_s`，因此外层预算进入 reserve 后不会再启动新子进程。

`ros2 pkg list` 只属于非关键 package inventory，执行顺序必须晚于 localization、TF、lifecycle、
planner 与 planner-only path 的关键判定。剩余预算足够时，它的 timeout 会 clamp 到
`remaining - final_artifact_reserve_s`；预算不足时必须返回
`boundary=package_check_skipped_to_preserve_final_artifact_budget`、`executed=false`，并把 package
availability 保持为 unknown/null，不能伪装成 installed、missing 或 command success。

自然收口的 JSON 必须同时满足 `artifact_kind=final`、`last_phase=final`、
`current_command=null`，并记录 `outer_process_timeout_s`、`final_artifact_reserve_s`、
`runtime_budget.remaining_s`、`finalization_reason` 与 package batch boundary。blocked/offline 仍是
合法 final outcome；`SIGINT` partial artifact 和 Upper API timeout fallback 只保留为异常兜底，
不能作为这一预算合同的通过条件。该离线合同只证明
`software_proof_o3_o10_offline_runtime_budget_contract_only`，不证明 current ROS graph、定位、
path、route execution、HIL、delivery、safe-to-control、robot control 或 Mission Objective 0。

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
