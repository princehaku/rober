# Field Route Evidence Preflight

`onboard/scripts/field_route_evidence_preflight.py` 是现场路线证据采集前的预检入口。它只生成 JSON evidence packet、只读探测 ROS2/SSH/topic 状态，并输出下一步 map、route、keyframe、rosbag、replay 采集命令模板；它不是路线成功、送达成功或 Nav2 实跑通过证明。

## 本地 dry-run

在 macOS 开发机、无 ROS2、无真实 SSH 时也应稳定运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --dry-run \
  --output /tmp/trashbot_field_preflight.json
```

dry-run 输出状态固定为 `dry_run_template_only_not_proven`，并保持：

- `not_proven=true`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`

## 上位机或本机真实预检

在已经 source ROS2 工作区的上位机上运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode local \
  --output "$HOME/.ros/trashbot_runs/field_preflight.json"
```

通过 SSH 从开发机探测上位机：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 5 \
  --output /tmp/trashbot_field_preflight_ssh.json
```

从 2026-06-09 的 board bringup blocker 修复开始，SSH 模式下所有远端 ROS2 命令都通过
`bash -lc` 执行，并先 source：

- `/opt/ros/humble/setup.bash`
- `/root/rober/onboard/install/setup.bash`（优先）
- 若不存在，再回退到脚本内候选 workspace setup

这样做是为了修复此前 `command -v ros2` / `ros2 topic list` 在非登录 SSH shell 中的假阴性
`blocked_ros2_cli_missing`。

SSH 不可达时，工具仍会写出 JSON，状态为 `blocked_ssh_unreachable`。这份 JSON 只能证明预检入口可用和网络 blocker 已分层，不能证明现场路线材料已经产生。

## 2026-07-11 live localization smoke

`2026-07-11` 起，预检脚本在真实模式下会在通用 topic smoke 之后追加一段固定 no-motion localization smoke，并在 smoke 后只读重跑一次 `/api/nav2/proof/refresh`：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py \
  --mode ssh \
  --ssh-target root@192.168.1.11 \
  --ssh-port 37878 \
  --timeout-s 8 \
  --output sprints/2026.07.11_05-55_o3_live_localization_sensor_smoke/artifacts/live_localization_preflight.raw.json
```

新增只读命令模板固定为：

- `ros2 topic echo --once /scan`
- `ros2 topic echo --once /amcl_pose`
- `ros2 topic type /map`、`ros2 topic info -v /map`
- `ros2 topic type /amcl_pose`、`ros2 topic info -v /amcl_pose`
- `ros2 lifecycle get /map_server`、`/amcl`、`/planner_server`
- managed map yaml 存在性、basename、size 和 `sha256` 前缀摘要
- `ros2 run tf2_ros tf2_echo map odom`
- `ros2 run tf2_ros tf2_echo map base_link`
- `curl ... /api/nav2/proof/refresh`（固定 no-motion body）

这段 smoke 的目标是把上一轮 `localization_not_ready_for_path_generation` 拆成当前同窗可复验的子 blocker，而不是发起导航执行。

从 `2026-07-11 08:39` 这轮返工起，refresh readback 的 `curl --max-time` 与外层
`subprocess.run(timeout=...)` 都改成由请求体 timeout 推导出的硬上限，并封顶在 45 秒量级，
不再使用 `args.timeout_s + 62` 这类长等待吞掉 automation。即使远端 readback 超时，脚本也必须自然返回并写出主 JSON artifact。

从 `2026-07-11 06:37` 这轮 root-cause probe 起，artifact 顶层还会新增 `root_cause_summary`，专门收敛：

- `/scan` topic type / publisher count；
- `/map` topic type / publisher count；
- `/amcl_pose` topic type / publisher count；
- `map_server`、`amcl`、`planner_server` lifecycle state；
- managed map yaml 的安全摘要；
- `map->odom`、`map->base_link` 的 TF 失败短句；
- `/api/nav2/proof/refresh` 的 readback status / root causes / blocked reasons。

这样做是为了把“topic 名字存在但无 publisher”、“configured managed map basename 对应文件缺失”、“AMCL lifecycle 未 active”、“TF 因 `Invalid frame ID \"map\"` 失败”等根因与单纯 echo timeout 分开记录。

从 `2026-07-11 09:39` 这轮 daemon-safe recovery 起，所有 ROS graph 只读查询还会额外检测
`xmlrpc.client.Fault: RuntimeError: !rclpy.ok()`。命中时，脚本只允许对 CLI graph 层执行一次
`ros2 daemon stop` / `ros2 daemon start` / 原命令重试；不会触发 `/cmd_vel`、`/api/base/manual`、
`NavigateToPose` 或其他运动入口。artifact 顶层同步新增：

- `daemon_fault_detected`
- `daemon_recovered`
- `retry_attempts`
- `recovered_topics`
- `unrecovered_blockers`
- `ros_daemon_health`
- `ros_cli_retry_summary`
- `root_cause_summary.root_cause_layers`

如果 daemon 恢复后 `/scan` 仍缺 publisher，会收口到 `lidar_missing`；如果 `/map_server` 或
`/amcl` lifecycle 不可读/不 active，会收口到 `map_server_not_active`、`amcl_not_active`；
如果 TF 仍报 `Invalid frame ID "map"`，则继续收口到 `tf_missing`。这样下一轮可以直接修
launch/runtime 或 map/AMCL，而不是再把 graph fault 误记成 topic 缺失。

输出中的顶层危险字段固定保持：

- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`

如果 live localization smoke 任一步失败，脚本会 fail-closed 在：

- `blocked_live_localization_chain_not_ready`
- `blocked_scan_not_observed`
- `blocked_amcl_pose_not_observed`
- `blocked_map_to_odom_not_observed`
- `blocked_map_to_base_link_not_observed`

如果 `/api/nav2/proof/refresh` 返回里出现 `safe_to_control=true`、`publishes_cmd_vel=true`、`calls_base_manual=true`、`sends_motion_commands=true`、`robot_control_executed=true` 等危险 true 字段，脚本会直接返回 `blocked_refresh_invokes_motion_or_goal_execution`。这表示 refresh 边界被破坏，本轮 readback 不能继续使用。

如果 refresh artifact 明确给出 `managed_runtime_started=true`，readback 中的
`starts_nav2=true` 也是允许且预期的。它只表示 helper 曾在 no-motion 边界内短暂拉起
Nav2 runtime，不表示执行过 goal、发过 `/cmd_vel`、调用过 `/api/base/manual`，更不表示
safe-to-control、HIL pass 或 delivery success。

`2026-07-11 11:40` 这一轮 O3 path recovery 继续把 helper 侧 root cause 往前推了一步。
`onboard/scripts/o10_amcl_nav2_runtime_proof.py` 已把
`ros2 topic info /initialpose --verbose` 从主路径移除：如果 initialpose publish 没有拿到
`initialpose_subscriber_count`，artifact 只记录
`initialpose_verbose_info_skipped_to_avoid_cli_stall`。原因是现场 direct helper 已经证明
这条 CLI 可能卡成不可回收阻塞，但它对当前 root cause 没有新增信息。

这一轮最新 live direct helper 产物已经越过旧的 `/initialpose` topic-info 卡点，但仍然
fail-closed，关键边界是：

- `/scan_once_not_observed`
- `cli_initialpose_publish_failed`
- `/amcl_pose_once_not_observed`
- `map_to_odom_not_observed`
- `path_generated=false`

也就是说，本轮新增价值是“旧卡点已移除、当前 blocker 更前置”，而不是拿到
`map_to_odom=true`、`map_to_base_link=true` 或 path proof。proof boundary 仍固定保持：

- `safe_to_control=false`
- `robot_control_executed=false`
- `hil_pass=false`
- `delivery_success=false`

如果 refresh 在硬上限内仍未完成，`checks.nav2_proof_refresh.summary` 会固定输出：

- `status=refresh_readback_timed_out`
- `timed_out=true`
- `naturally_returned=false`
- 固定 no-motion false 字段：`safe_to_control=false`、`delivery_success=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`

这样做是为了保证 `*.raw.json` 仍可被 sprint、O6/O7 和后续 automation 消费，而不是只留下中断说明。

`2026-07-11 12:41` 这一轮 O3 signal freshness / TF source 分层把
`o10_amcl_nav2_runtime_proof.py` 的 helper artifact 扩展为两块可回读摘要：

- `proof.localization_signal_freshness`：覆盖 `/scan`、`/amcl_pose`、`/odom`、`/tf`、
  `/tf_static`，记录 topic type、topic presence、publisher/subscriber 摘要、once probe
  `executed/observed/elapsed_ms/timeout_s/timed_out`、可解析 header stamp 与 freshness 状态。
- `proof.tf_source_freshness`：按 `map_to_odom`、`odom_to_base_link`、
  `base_link_to_laser_frame` 记录 dynamic/static source、source topic、transform stamp 和 freshness。

本轮真实板 direct helper 产物为
`sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json`。
关键结论是：`/scan` topic type 为 `sensor_msgs/msg/LaserScan`，但 once probe timeout；
`/amcl_pose` topic type 为 `geometry_msgs/msg/PoseWithCovarianceStamped`，但 once probe timeout；
`/odom` topic type 为 `nav_msgs/msg/Odometry`，且 header stamp freshness 为 `fresh`；
`/tf` 与 `/tf_static` topic type 均可见，但 rclpy source inventory 失败，未拿到 dynamic/static edge source；
最终 root causes 收敛为 `/scan_probe_timeout`、`/amcl_pose_probe_timeout`、
`map_to_odom_dynamic_source_missing`、`map_to_base_link_blocked_by_missing_map_to_odom` 和
`localization_not_ready_for_path_generation`。本轮仍 `map_to_odom=false`、`path_generated=false`。

`2026-07-11 22:48` 这一轮再把 board source preflight 拆成两层 readiness：

- `board_source_preflight.cli_ready`：只要求 sourced shell + `ros2` CLI 可用，足以继续跑
  managed runtime、lifecycle 和只读 CLI probe；
- `board_source_preflight.runtime_ready`：在 `cli_ready=true` 基础上再要求 `rclpy import`
  成功，才允许把 rclpy child/runtime 当成可执行前提。

这样做是为了避免板端偶发 `rclpy` import 抖动时，把整个 managed runtime / map lifecycle /
TF source 链路一起误判成“不可执行”。当 `cli_ready=true` 但 `runtime_ready=false` 时，
helper 必须继续保留 no-motion false safety 字段，并把 TF source 收口成
`tf_source_probe_rclpy_runtime_unavailable_after_board_preflight` 这类明确 boundary，
而不是再次只留下 `tf_source_probe_not_executed`。

`2026-07-11 13:41` 这一轮继续把 `/scan` once probe 改成多尝试 QoS 诊断。新的
`proof.localization_signal_freshness["/scan"].probe` 除了原有 `executed/observed/timed_out`
外，还会新增：

- `attempts[]`：逐次记录 `label`、`source`、`qos_profile`、`command`、`elapsed_ms`、
  `timed_out`、`error`；
- `best_attempt`：当前最有信息的一次尝试；
- `qos_probe_boundary`：本轮 `/scan` probe 的汇总边界；
- `source`：最终被采信的 probe 来源。

当前 live artifact
`sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json`
显示：

- `rclpy_sensor_data_once` 首次尝试立即失败，错误为
  `ImportError: librcl_action.so ... _rclpy_pybind11... failed to be imported`；
- `cli_sensor_data_echo_once` 与 `cli_default_echo_once` 都超时；
- 因为 endpoint inventory 本轮并未成功建立，root cause 不再误记成
  `/scan_no_publishers`，而是保守收口到 `/scan_rclpy_probe_failed`；
- `/amcl_pose` 仍为 `probe_timeout`，`map_to_odom` 仍缺 dynamic source。

这说明 blocker 已经从“topic 是否存在”进一步拆成“板端 rclpy/rcl 依赖不完整”与
“CLI sensor-data/default echo 都未在窗口内读到一帧”。它仍不是 fixed-route path proof、
Nav2 route execution、HIL pass 或 delivery success。

`2026-07-11 21:47` 这一轮继续修 helper 的 managed runtime wait 语义。此前 artifact 容易把
“`/map_server`、`/amcl` 节点已经进 graph”误读成 lifecycle 已就绪，随后又被一次性的
`ros2 lifecycle get` `inactive [2]` 快照固定成最终 blocker。另外，旧的
`rclpy_node_names()` 直接跑在 helper 主 Python 进程里，板端一旦主进程没有继承好 ROS Python
环境，就会反复报 `No module named 'rclpy'`，把 managed wait 误收口成 timeout。现在
`o10_amcl_nav2_runtime_proof.py` 改成 sourced child Python node graph probe，并在 managed wait
窗口内反复做只读 lifecycle recheck，把结果写回 `managed_runtime_wait_result.lifecycle_active`、
`managed_runtime_wait_result.lifecycle_results` 和
`managed_runtime_wait_result.lifecycle_history`。

因此当前 no-motion artifact 会明确区分三类边界：

- `managed_runtime_lifecycle_active_observed`：节点已进 graph，且 `/map_server`、`/amcl`
  已在同一 helper 窗口内确认 `active`；
- `managed_runtime_nodes_observed_but_lifecycle_inactive`：节点出现过，但到窗口结束 lifecycle
  仍未 active；
- `managed_runtime_wait_timeout`：连节点都没在窗口内稳定出现。

收口时优先看这三类边界，再看 `/scan`、`/map`、`/amcl_pose` freshness 与 `map->odom`。
这样可以避免把“启动中 lifecycle 还没切到 active”和“根本没拉起 runtime”混成同一个 blocker。

`2026-07-11 23:49` 起，`rclpy_node_names()` 再增加一层 `ros2 node list` fallback。也就是说：

- 如果 sourced child Python 成功，仍以 `rclpy_node_names_observed` 为准；
- 如果 child timeout、parse 失败或 import 失败，但 `ros2 node list` 仍能看到 `/map_server`、
  `/amcl`，artifact 会写成
  `rclpy_node_names_failed_with_ros2_node_list_fallback_observed` 之类的组合 boundary；
- 只有 child 与 CLI 两层都拿不到节点名，才继续落到带 `ros2_node_list_*` 后缀的失败边界。

同一轮里 `collect_amcl_rclpy_probe()` 若命中 `librcl_action.so`、`_rclpy_pybind11` 或其他
rclpy runtime/import failure，也不再只回 `rclpy_amcl_probe_failed`。helper 会追加 ROS CLI
inventory fallback，把 `/tf`、`/tf_static` topic availability、`ros2 topic info --verbose`
计数，以及 `/amcl` node info 写进 artifact，并额外保留：

- `probe_mode=ros2_cli_fallback`
- `fallback_used=true`
- `fallback_boundary=cli_amcl_inventory_*`
- `rclpy_import_failure_classification`

因此 closeout 要先看 `amcl_tf_root_cause` 是否已经从 `/tf_topic_missing` 收窄到
`amcl_param_probe_failed`、`amcl_node_info_not_observed` 或更具体的 TF/source blocker，再决定
是否继续追 `map_to_odom`。

`2026-07-12 00:49` 起，managed runtime wait 的 graph probe 不再允许一条 child Python
或 `ros2 node list` fallback 独占整个 wait 窗口。helper 会按剩余 managed wait 预算给
child probe 与 CLI fallback 分配短窗口，并在 final artifact 中写回：

- `proof.managed_runtime_wait_result.reason`
- `proof.managed_runtime_wait_result.graph_wait_summary.latest_node_list_boundary`
- `proof.managed_runtime_wait_result.graph_wait_summary.latest_ros2_node_list_boundary`
- `proof.managed_runtime_wait_result.graph_wait_summary.fallback_used`
- `proof.managed_runtime_wait_result.graph_wait_summary.observed_node_names`

如果 final reason 是 `ros2_node_list_timeout`、`ros2_node_list_empty_after_wait`、
`ros2_node_list_failed` 或 `managed_runtime_required_nodes_not_observed`，说明本轮已经自然收口到
graph/wait 层；不能再把结论写成上一轮的 `partial_runtime_in_progress` 或
`current_command.command=ros2 node list`。同一轮里，AMCL/TF source probe 即使 rclpy runtime
不可用或 rclpy probe 返回不完整，也会尝试短窗口 ROS CLI fallback，artifact 会保留
`commands.tf_source_probe.amcl_rclpy_probe.probe_mode=ros2_cli_fallback`、
`fallback_boundary=cli_amcl_inventory_*`、`/tf`、`/tf_static` 和 `/amcl` node/param closeout
字段。只有 `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`、
dynamic `map->odom` 与 `map->base_link` gate 全部成立后，才允许 planner-only path attempt；
否则 `path_generation_attempted=false`、`path_generated=false` 必须保持。

`2026-07-11 14:42` 这一轮继续修正 `/scan` rclpy probe 的运行时边界：`rclpy_sensor_data_once`
不再在 helper 主 Python 进程内直接 import ROS 包，而是通过与 `run_ros()` 相同的
`bash -lc` / `source /opt/ros/humble/setup.bash` / workspace setup 环境启动 child Python
订阅 `/scan`。artifact 中 `/scan.probe.attempts[]` 因此新增并保留：

- `runtime=ros_sourced_child_python`
- `environment_check`：`LD_LIBRARY_PATH`、`PYTHONPATH`、`AMENT_PREFIX_PATH`、Python 版本和 cwd 摘要
- `import_check`：rclpy import 是否成功、失败分类或 `rclpy_file`
- `runtime_diagnostics.child_process`：child 进程 timeout/returncode/elapsed 摘要

本轮 live artifact
`sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`
显示 `/scan.topic_type=sensor_msgs/msg/LaserScan` 仍可见，但 `/scan` frame 仍未 observed。
关键变化是 `/scan` 的 `rclpy_sensor_data_once` 已在 sourced child Python 中完成 import：
`import_check.ok=true`，不再是上一轮 `librcl_action.so` / `_rclpy_pybind11` import failure；
新的第一层 blocker 收口为 `/scan_rclpy_child_timeout_after_import`。两条 CLI fallback
`cli_sensor_data_echo_once` 与 `cli_default_echo_once` 仍 timeout，因此下一轮应优先确认
LiDAR publisher 是否在 managed runtime 窗口内实际发布 sample，或把 child probe 的 graph/endpoint
采样提前到 timeout 前，而不是再重复修主进程 import。

这份证据只说明 signal freshness / TF source root cause 比上一轮更细，不证明
fixed-route path proof、Nav2 route execution、HIL pass、safe-to-control 或 delivery success。
顶层安全字段继续固定为 `safe_to_control=false`、`robot_control_executed=false`、
`hil_pass=false`、`delivery_success=false`。

`2026-07-11 15:44` 这一轮继续把 `/scan` blocker 从 child timeout 拆成 publisher、
endpoint QoS 与 sample timing 三层。读取
`sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/*_o10_scan_endpoint_timing_inventory.raw.json`
时，先看 `proof.localization_signal_freshness["/scan"]` 下列字段：

- `publisher_inventory`：确认 `/scan` topic 是否可见、`publisher_count` 是否大于 0、
  publisher node 是否像 LiDAR driver，而不是先看 child timeout；
- `endpoint_inventory`：确认 publisher/subscriber endpoint、`endpoint_qos_profiles` 与
  `requested_qos_profile`，用来区分无 publisher、QoS 不匹配和 sample window 不足；
- `sample_timing`：确认 `sample_wait_started_at_ms`、`timeout_boundary_ms`、
  `first_sample_latency_ms`、`sample_count`、`last_sample_stamp` 和
  `last_sample_received_at_ms`；
- `managed_runtime_scan_status`：把 managed runtime 是否启动、LiDAR publisher 是否可见、
  sample 是否 observed 和 `blocked_reason` 放在同一层；
- `probe.classification`：稳定分类只能使用 `/scan_no_publisher`、

`2026-07-11 17:43` 这一轮进一步把读取顺序前移到 managed runtime / lifecycle readiness。
如果 true-board latest artifact 已满足下列条件：

- `managed_runtime_started=true`
- `initialpose_opt_in=true`
- `ros2 lifecycle get /map_server`、`/amcl` 已证明 active
- 但 `amcl_tf_root_cause` 仍是 `/tf_topic_missing`、`map_to_odom_not_observed` 或同类定位 blocker

则 helper 会直接把 `/scan` 与 `/map` 标成：

- `scan_probe_skipped_after_managed_runtime_lifecycle_ready`
- `map_probe_skipped_after_managed_runtime_lifecycle_ready`

并在 phase detail 里标出
`managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path`。这表示本轮应先处理
`/tf`、`map->odom`、`map->base_link` 或 AMCL source blocker，而不是把 latest artifact
再次卡回 BEST_EFFORT / RELIABLE `/scan` attempt 的长等待。只有当 lifecycle readiness
本身不成立时，才继续解释 `/scan.probe.best_effort_attempt`、`reliable_attempt`、
`sample_timing` 和 QoS/timeout 分类。
  `/scan_lidar_runtime_not_started`、`/scan_publisher_visible_but_no_sample`、
  `/scan_qos_or_window_timeout`、`/scan_rclpy_child_timeout_after_import` 或
  `/scan_sample_observed`。

如果 `endpoint_inventory.inventory_observed=true` 且 `publisher_count=0`，后续 root cause 不应再写成
`/scan_rclpy_child_timeout_after_import`；应先处理 no publisher 或 LiDAR runtime 未启动。如果
publisher 可见但 `sample_count=0`，下一轮应调 QoS/window 或检查 LiDAR driver 是否持续发帧。只有
`probe.classification=/scan_sample_observed` 后，才继续复验 `/amcl_pose`、dynamic `map_to_odom` 和
`path_generated`。本轮 artifact 仍固定 `safe_to_control=false`、`robot_control_executed=false`、
`route_execution_success=false`、`hil_pass=false`、`delivery_success=false`，不证明 fixed-route
path proof、Nav2 route execution、HIL pass 或 production cloud。

`2026-07-11 16:43` 起，`/scan` child probe 继续扩成双 QoS 对照：同一轮 artifact 必须同时保留
`BEST_EFFORT` / `VOLATILE` 与 `RELIABLE` / `VOLATILE` 两条 child subscription attempt，
并分别记录 `requested_qos_profile`、`sample_timing`、`timed_out`、`error`。读取
`sprints/2026.07.11_16-43_o3_scan_long_window_reliable_probe/artifacts/*_o10_scan_long_window_reliable_probe.raw.json`
时，优先对照：

- `proof.localization_signal_freshness["/scan"].probe.best_effort_attempt`
- `proof.localization_signal_freshness["/scan"].probe.reliable_attempt`
- `proof.localization_signal_freshness["/scan"].probe.attempts[]`

如果任一 attempt 收到 sample，classification 应进入 `/scan_sample_observed`；如果两条 child
attempt 都 timeout 且 publisher endpoint 仍可见，classification 至少应收口到
`/scan_reliable_and_best_effort_timeout` 或同等具体值，而不是继续泛化成单条
`/scan_qos_or_window_timeout`。这仍是 no-motion diagnostic evidence，不证明 `safe_to_control`、
`route_execution_success`、`hil_pass` 或 `delivery_success`。

`2026-07-12 19:56` 起，`o10_amcl_nav2_runtime_proof.py` 会在上述原始 probe 外再输出
`proof.scan_qos_endpoint_readback_split`，作为 `/scan_reliable_and_best_effort_timeout`
的第一层结构化拆分。现场或 sprint closeout 读取顺序改为：

1. `publisher_endpoint_classification`：确认 `/scan` topic/type、publisher endpoint、
   publisher 节点、publisher QoS 和 endpoint 是否跨 child attempts 稳定。
2. `qos_window_ros_readback_classification`：确认 BEST_EFFORT / RELIABLE 两条 child
   attempt 是否分别 timeout、请求 QoS 与 endpoint QoS 是否兼容、CLI fallback 是否也 timeout。
3. `lidar_runtime_classification`：只有 endpoint 可见、QoS 兼容、两条 child attempt 都 timeout、
   `sample_count=0` 时才进入 runtime candidate；若 managed runtime log 同时出现 LiDAR runtime
   exception，只允许输出 Hardware handoff 条件。
4. `primary_split`：给 `artifact_closeout.primary_root_cause` 使用的最细 split reason，同时保留
   `canonical_blocker=/scan_reliable_and_best_effort_timeout` 方便历史检索。

本轮 live artifact
`sprints/2026.07.12_19-56_o3_scan_qos_endpoint_readback_split/artifacts/live_o10_scan_qos_endpoint_readback_split.raw.json`
的结论是：`publisher_endpoint_classification.classification=publisher_endpoint_visible`，
publisher 为 `lidar_driver`，publisher QoS 为 `RELIABLE`，AMCL/probe subscriber 为
`BEST_EFFORT`，endpoint 两次 child attempt 观测稳定；BEST_EFFORT 与 RELIABLE child
attempt 均 timeout，`sample_count=0`，QoS compatibility risk 为 false；managed runtime log
出现 `serial.serialutil.SerialException` 且包含 `device reports readiness to read but returned no data`。
因此 closeout primary split 为
`/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout`，
但该字段仍只是 runtime handoff 条件，不是 vendor-backed hardware root cause。Hardware 介入前仍必须
按 `AGENTS.md` 读取 `docs/vendor/VENDOR_INDEX.md`；本 helper 不改 serial、UART、baudrate、
wiring、电压或 WAVE ROVER 配置。

`2026-07-12 20:57` 起，Hardware handoff 的下一层不再重复 generic
`/scan_reliable_and_best_effort_timeout`。LiDAR runtime gate 必须读取本地 vendor 来源后，
用 no-motion smoke 对 `/dev/ttyACM0`、baudrate、raw bytes、empty read 和 topic sample
做结构化对比：

- 本地 WAVE ROVER vendor 上位机参考
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 打开 `/dev/ttyACM* @ 230400`，
  并按 STC `0x54`、47 字节 packet、12 个采样点解析 LiDAR。
- 历史现场 runbook 仍保留 `/dev/ttyACM0 @ 150000` 候选；该值来自实板 artifact，
  不是 vendor 文档。两者必须通过同一 smoke 对比，不能凭默认值直接覆盖。
- `o1_lidar_ros2_scan_smoke.sh` 会写 `device_snapshot_before/during/after.json`、
  `lidar_driver_diagnostics.json` 和 `summary.json`，其中 `read_exception_count`、
  `last_exception_type`、`last_exception_message_hint`、`empty_read_count`、
  `raw_bytes_observed`、`bytes_read_total`、`last_chunk_preview_hex` 和
  `packet_count_total` 是判定下一步的主字段。
- 若 `raw_bytes_observed=false` 且出现 `serial.serialutil.SerialException`，优先检查
  `/dev/ttyACM0` holder、USB 供电/线缆和雷达供电；若已有 raw bytes 但无 packet，
  优先检查 baud/protocol mismatch；若 packet 有但 `/scan` sample 缺失，优先检查
  aggregation 阈值、ROS topic discovery 或 `/lidar/raw_packet` 发布。

该 Hardware gate 仍固定 strict no-motion：`safe_to_control=false`、
`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`。

`2026-07-12 21:57` Gate 2 起，如果 `/api/radar/status` 已经证明 current readback 为
`baudrate=150000`，Algorithm 的 path proof 不再允许随 managed runtime 启动第二个
`lidar_driver`。板端命令必须在 `--managed-lidar-serial-baudrate 150000` 外额外带
`--reuse-existing-lidar-lifecycle`，artifact 需要回写：

- `managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`
- `managed_lidar_serial_baudrate=150000`
- `managed_lidar_driver_started_by_helper=false`

这表示 helper 只拉起 strict no-motion Nav2/map/AMCL/planner/static TF 侧 proof，继续复用
已有 `/dev/ttyACM0` LiDAR holder；它不得 stop/start 当前 LiDAR lifecycle，也不得把 `/scan`
readiness 误写成 route execution、delivery、HIL 或 safe-to-control。

## JSON contract

输出 schema 为 `trashbot.board_field_evidence_preflight.v1`，关键字段包括：

- `status`
- `source`
- `mode`
- `dry_run`
- `generated_at`
- `target`
- `checks`
- `commands`
- `next_required_evidence`
- `blocked_reason`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

失败状态采用 fail closed 分层：

- `blocked_ssh_unreachable`
- `blocked_ros2_cli_missing`
- `blocked_setup_missing`
- `blocked_trashbot_packages_missing`
- `blocked_required_topics_missing`
- `blocked_topic_smoke_failed`
- `blocked_live_localization_chain_not_ready`
- `blocked_refresh_readback_failed`
- `blocked_refresh_invokes_motion_or_goal_execution`
- `live_localization_smoke_refresh_readback_not_proven`
- `dry_run_template_only_not_proven`

`checks.setup_candidates.candidates` 现在也会优先列出 `/root/rober/onboard/install/setup.bash`，
便于现场确认真实上位机工作区是否已完成 build 并可被 SSH 采样。

## 安全边界

工具不发布 `/cmd_vel`，不启动运动任务，不修改 WAVE ROVER、ESP32、UART、串口、底盘协议或 launch 默认硬件参数。命令输出进入 JSON 前会做长度裁剪和常见凭证脱敏，避免把 token、password、private key 片段带入证据包。

真实路线验收仍需要补齐上位机 SSH 可达、ROS2 topic smoke、`map.yaml`、`route.csv`、`keyframes/`、`route_bag/` 或 fixed-route replay JSONL。

## 2026-06-09 实板 topic gate 补充

对 `root@192.168.1.11:37878` 的短时 bringup smoke 说明，当前 `ros2_trashbot_bringup/bringup.launch.py` 只覆盖基础硬件桥、地图记录、航点、行为和可选相机，不包含：

- `lidar_driver`
- `robot_state_publisher`
- `static_transform_publisher`

因此：

1. 仅运行当前 `bringup.launch.py` 时，`/scan` 缺失不能直接判定为 LiDAR 硬件坏；更常见原因是该 launch 根本没有把 LiDAR node 拉起。
2. `/tf_static` 缺失在当前 bringup 下也是预期现象，因为 launch 组成里没有静态 TF 发布者。
3. 2026-06-09 的实板 smoke 还额外暴露：`esp32_bridge` 默认串口仍指向 `/dev/ttyUSB0`，而实板实际观察到的入口是 `/dev/ttyS5` 与 `/dev/ttyACM0`。这会让 topic 观察窗口进一步变差。

所以现场预检里对 `/scan` / `/tf_static` 的 gate 应明确区分：

- `bringup 基础 topic gate`：例如 `/map`、参数面、节点存活。
- `LiDAR no-motion smoke gate`：单独运行 `ros2 run ros2_trashbot_hardware lidar_driver --ros-args -p serial_port:=/dev/ttyACM0` 采样 `/scan`。
- `full field stack gate`：从 2026-06-09 当晚开始，`bringup.launch.py` 已支持 `base_enabled:=false`、`lidar_enabled:=true` 和 `static_laser_tf_enabled:=true` 的 sensor-only 组合；只有显式使用这组参数时，才把 `/scan` 与 `/tf_static` 作为同一条 bringup gate。

推荐的 no-motion full sensor stack gate：

```bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=false \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  static_laser_tf_enabled:=true \
  camera_enabled:=true \
  camera_device:=/dev/video1
```

该 gate 仍然只证明 topic 链路，不证明：

- `/dev/ttyS5` 底盘串口冲突已解决；
- `base_link -> laser_frame` 已标定；
- 运动、建图和固定路线已完成 HIL。

## 2026-06-10 no-motion 现场补充

在 `root@192.168.1.11:37878` 上继续执行 no-motion evidence capture 后，现场边界进一步收敛：

1. `topic list` 里可见 `/map`，但 `ros2 topic echo --once /map` 没有拿到消息，额外执行 `ros2 topic info /map` 还会返回 `Unknown topic '/map'`。
2. `/trashbot/save_map` service 虽然存在，但在单独重试时明确返回：

```text
std_srvs.srv.Trigger_Response(success=False, message='No map data received')
```

3. 这说明当前 sensor-only bringup 的 no-motion 组合里，`map_recorder` 只是被启动了；它并不等于现场已经有持续发布的 mapping source。若要收集 `map.yaml`，必须把真实 mapping node（例如 `learn.launch.py` 中的 `slam_toolbox`）明确纳入现场链路。
4. `route_data_recorder` 本轮在板上先失败于 Python 依赖：

```text
ModuleNotFoundError: No module named 'cv_bridge'
```

5. 即使补齐 `cv_bridge`，当前 no-motion sensor-only bringup 依然没有 `/odom`，因此也不会生成有效 `route.csv` 轨迹点。

因此 2026-06-10 这轮现场 no-motion 采集的正确定位应是：

- **已证明**：`/scan`、`/camera/image_raw`、`/tf_static`、短 rosbag、相机单帧 keyframe fallback。
- **未证明**：`map.yaml`、`route.csv`、keyframe manifest、fixed-route replay JSONL。

从 `learn.launch.py` 增补 no-motion 入口后，下一轮现场验证必须改为以下链路，而不是继续使用缺 `/odom` 的 sensor-only bringup：

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

该入口的现场验收顺序必须固定为：

1. `ros2 launch ... --show-args` 确认新增参数都已暴露。
2. `ros2 topic echo --once /scan`、`/camera/image_raw`、`/tf_static`、`/odom`。
3. 检查 `/tmp/trashbot_no_motion_route/route.csv` 是否至少新增 1 行。
4. 若图像转换成功，检查 `keyframes/*.jpg`、`keyframes/*.json`、`manifest.json`；若转换失败，必须检查 `image_conversion_status.json` 并记录失败原因。
5. 调用 `/trashbot/save_map`，仅以 `map.yaml` 实际落盘作为地图成功标准；service 存在或 `/map` topic 名称出现都不算成功。

## 2026-06-10 learn.launch no-motion capture 入口

为避免现场同时手工启动多个 launch 造成参数漂移，`ros2_trashbot_bringup/learn.launch.py` 已新增一组默认关闭的 no-motion 现场证据采集参数。正常学习模式默认行为不变；只有显式传参时才启动 camera、LiDAR、smoke-only TF、synthetic `/odom` 和 `route_data_recorder`。

推荐命令：

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

采样 gate：

- `/scan`
- `/camera/image_raw`
- `/tf_static`
- `/odom`
- `/map`
- `/trashbot/save_map`

检查产物：

- `/tmp/trashbot_no_motion_route/route.csv`
- `/tmp/trashbot_no_motion_route/keyframes/`
- `/tmp/trashbot_no_motion_route/manifest.json`
- `/tmp/trashbot_no_motion_route/image_conversion_status.json`（仅在图像转换降级或失败时出现）

重要边界：

1. `no_motion_mock_odom_enabled:=true` 通过 ROS2 CLI 发布零速 synthetic `nav_msgs/Odometry`，只用于验证 route recorder 软件链路，不是实测里程计、轮速标定或 HIL。
2. `no_motion_static_odom_tf:=true` 只发布 `odom -> base_link` 的 no-motion 拓扑 TF，不代表定位或底盘运动已经成立。
3. `static_laser_tf_enabled:=true` 仍是 smoke-only `base_link -> laser_frame` 拓扑证据，不代表 LiDAR 机械安装标定。
4. 本命令不发布 `/cmd_vel`，不绕过 `upper_robot_api.py` 安全 gate，不修改 WAVE ROVER 串口、协议或速度默认值。
5. 当前实板设备号 `/dev/video1`、`/dev/ttyACM0 @ 150000` 来自本 sprint 现场探测；硬件事实入口仍以 `docs/vendor/VENDOR_INDEX.md` 及其指向的本地 vendor 资料为准，不能写死成全项目默认。

`route_data_recorder` 也已把 `cv_bridge` 改为可选依赖：优先使用 `cv_bridge`；缺失时对 `rgb8`、`bgr8`、`mono8`、`bgra8`、`rgba8` 使用 `numpy` + `cv2` 转换；不支持的 encoding 只记录原因并继续等待 `/odom`，避免节点启动即崩溃。

## 2026-06-10 清场后复跑补充

对 `root@192.168.1.11:37878` 做第二次 no-motion 复跑时，现场经验需要补一条强制 gate：

1. 先盘点：
   - `ros2 node list`
   - `ps -ef | grep -E 'slam|lidar|camera_publisher|route_data_recorder|static_transform|topic pub'`
   - `fuser -v /dev/video1 /dev/ttyACM0`
2. 只清理本轮 no-motion 残留 ROS2/launch 进程，**不要杀 `upper_robot_api.py`**。
3. 清场后必须再次确认：
   - `ros2 node list` 为空
   - `/dev/video1`、`/dev/ttyACM0` 无占用
4. 只有在基线干净后，才允许重新执行 `learn.launch.py` 的 no-motion capture。

本次 clean rerun 已证明：如果先清场，再复跑 `learn.launch.py`，则 `/scan`、`/camera/image_raw`、`/tf_static`、`/odom`、`route.csv`、`manifest.json`、`keyframes/000.*`、`save_map`、`trashbot_map.yaml` 都可以在同一轮里拿到干净证据，不再混入重复同名节点。

但该 clean rerun 也暴露了两个边界：

- 当前 no-motion route 仍依赖 synthetic zero `/odom`，所以只能证明软件链路，不证明真实路线。
- `waypoint_manager` 会持续追加 `auto_000x` 零位航点；如果现场目标只是最小 clean capture，建议显式关闭它或在验收时把这部分副作用单独记录。

## 下游 artifact gate

预检 JSON 生成后，使用 `onboard/scripts/field_route_evidence_manifest.py` 继续生成 `trashbot.field_evidence_manifest.v1`。manifest gate 会校验 `map.yaml`、`route.csv`、`keyframes/`、rosbag 和 fixed-route replay JSONL 是否存在且非空，并记录 sha256 或目录摘要。

示例：

```bash
python3 onboard/scripts/field_route_evidence_manifest.py \
  --mode local \
  --artifact-root /tmp/trashbot_field_manifest_fixture_complete \
  --preflight-json /tmp/trashbot_field_preflight_ssh.json \
  --output /tmp/trashbot_field_manifest_complete.json
```

如果 SSH 仍不可达，必须保留 `blocked_ssh_unreachable` 与 `not_proven=true`，但可以用本地完整 fixture 和缺失 fixture 验证 manifest 功能，确保不再次只消费同一 SSH blocker。无论 artifact gate 是否通过，manifest 仍保持 `delivery_success=false` 和 `primary_actions_enabled=false`，直到真实现场路线和送达验收另行证明。

## 2026-06-11 18:20 live no-motion refresh 补充

`sprints/2026.06.11_18-20_board_live_evidence_sweep/` 在真实上位机
`root@192.168.1.11:37878` 执行当前 live readback 与 no-motion refresh。所有要求的
Robot API readback 均返回 HTTP 200：`/api/status`、`/api/camera/health`、
`/api/camera/devices`、`/api/radar/status`、`/api/map/proof/latest`、
`/api/nav2/status`、`/api/operator/report`、`/api/base/status`。

本轮 refresh 结果：

- Radar：`POST /api/radar/scan-proof/refresh` HTTP 200，`status=refreshed`，
  `proof_state=scan_once_hz_raw_packet_tf_observed`，
  `evidence_ref=o1-lidar-scan-proof-1781171493054`。refresh 后 status 读回
  `lifecycle_running=false`、`lifecycle_state=stopped`、`freshness=fresh`、
  `/scan` hz `15.926`、raw packet 和 TF 均 observed。
- Map：`POST /api/map/proof/refresh` HTTP 200，
  `status=map_once_artifact_metadata_observed`，`command_result.ok=true`，
  `map_once_observed=true`、`map_file_observed=true`、`map_metadata_observed=true`。
  后续 latest evidence 为 `o3-map-lifecycle-1781171513110`。
- Nav2：`POST /api/nav2/proof/refresh` HTTP 200，
  `proof_state=nav2_no_motion_path_generation_runtime_observed`，
  `evidence_ref=o10-amcl-nav2-runtime-1781171562670`，
  `path_generated=true`、`path_generation_succeeded=true`、`path_point_count=31`、
  `planner_server_active=true`。

安全边界保持不变：

- Radar/map/Nav2 refresh 均返回 `sends_motion_commands=false`、
  `sends_base_motion_commands=false`、`calls_base_manual=false` 或等价 false 字段，
  `uses_base_uart=false`、`robot_control_executed=false`。
- Cleanup 读回 `ros2 topic info /cmd_vel` 为 `Unknown topic '/cmd_vel'`，未见
  `o1_lidar/o3_map/o10_amcl/nav2/slam/lidar_driver/camera_publisher/topic pub/cmd_vel`
  残留。
- 本轮没有 route execution、NavigateToPose、controller 执行、`/api/base/manual` 或
  非 stop 底盘动作；Nav2 只证明 no-motion path generation readiness。

## 2026-06-22 managed map Nav2 proof 补充

`sprints/2026.06.22_10-41_nav2_route_proof_readback/` 在真实上位机
`root@192.168.1.11:37878` 上修正了 Nav2 no-motion proof 的地图选择和 readback 聚合。

现场根因是 PC fixed body 早先写死了空的 `trashbot_map.yaml`，而 canonical map proof
latest 仍保留旧 blocked 状态。helper 现在会在未显式指定 `--managed-map-yaml` 时，从
canonical map candidates 中选择包含 free cell 的地图；本轮选择：

- `/root/rober/onboard/runtime/maps/fixed_free_cells_20260622_0112.yaml`
- `managed_runtime_map_yaml_source=canonical_map_proof_usable_yaml_candidate`
- `cell_counts.free=394`

真实 PC proxy `POST /api/robot-control/nav2/proof/refresh?baseUrl=http://192.168.1.11:8787`
读回：

- `evidence_ref=o10-amcl-nav2-runtime-1782095872075`
- `map_server_active=true`
- `amcl_active=true`
- `planner_server_active=true`
- `initialpose_published=true`
- `scan_once_observed=true`
- `map_once_observed=true`
- `amcl_pose_observed=true`
- `localization_tf_observed.map_to_odom=true`
- `localization_tf_observed.map_to_base_link=true`
- `path_generation_service_name=/compute_path_to_pose`
- `path_generation_succeeded=true`
- `path_point_count=31`
- `root_causes=[]`

该 proof 仍只允许 `ComputePathToPose` no-motion action，用于证明当前地图、AMCL 和 planner
能生成路线；它没有调用 NavigateToPose、controller execution、`/cmd_vel`、`/api/base/manual`
或 WAVE ROVER UART 运动命令。因此它不是真实路线执行、wheel raw L/R 非零、dropoff 或
delivery success 证明。

## 2026-06-27 Nav2 受管 lifecycle start 修正

真实上位机 `root@192.168.1.11:37878` 只读复核显示，当前 `/api/nav2/status` 的 `commands.start.configured=false`，
即 `ROBER_NAV2_START_COMMAND` 未配置；PC summary 同步表现为 `planner_server_active=false`、
`controller_server_active=false`，并带 `planner_server_inactive/controller_server_inactive` blocker。
这说明自动驾驶当前不是被摄像头卡住，也不是“车能不能低速动”的问题，而是 Nav2 runtime 没有受管 start 入口。

本轮新增 `onboard/scripts/o11_nav2_lifecycle.sh`，并把 `upper_robot_api.py` 的默认
`/api/nav2/start|stop` 接到该脚本：

- `start` 固定调用 `ros2 launch ros2_trashbot_bringup autonomous.launch.py nav2_stack_only:=true`。
- `nav2_stack_only=true` 只启动 ESP32 bridge 与 Nav2 bringup，不启动 `waypoint_manager`、`nav_to_goal`、
  `task_orchestrator`、`fixed_route_autonomy`、operator gateway 或 remote bridge。
- 默认 managed map yaml basename 为 `trashbot_map.yaml`；summary-facing 输出只记录 basename，不回显板上完整路径。
- 默认 WAVE ROVER UART 为现场确认的 `/dev/ttyS5@115200`，默认 `command_mode=ros`，即按
  `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 和
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 的本地资料使用 newline JSON，
  ROS `cmd_vel` bridge 口径对应 `T=13`。
- `start` 本身不发送 NavigateToPose goal、不发布 `/cmd_vel`、不调用 `/api/base/manual`，真正路线执行仍只能走
  显式安全确认后的 `/api/nav2/goal/execute`。

因此 PC 或上位机现在可以先用固定 `/api/nav2/start` 恢复 planner/controller runtime，再通过
`/api/nav2/proof/refresh` 重新采集 map/AMCL/planner/controller 证据。该修正不等于真实路线执行成功，也不等于
wheel raw L/R 非零、dropoff 或 delivery success。

## 2026-06-28 PC Nav2 lifecycle 恢复入口

PC 工作站新增固定 `POST /api/robot-control/nav2/start|stop?baseUrl=...` 代理，供普通首屏在
`planner_server_inactive/controller_server_inactive` 时先恢复自动驾驶服务。该代理只允许访问上位机固定
`/api/nav2/start|stop`，请求 body 固定 `{}`；浏览器传入的 endpoint、goal、速度字段都会被忽略。

安全边界：

- `starts_nav2=true` 只表示服务栈恢复事实，不能作为路线执行或 HIL 通过证明。
- `sends_motion_commands=true`、`sends_base_motion_commands=true`、`publishes_cmd_vel=true`、
  `calls_base_manual=true` 或 `robot_control_executed=true` 仍会让 PC 代理 fail closed。
- 普通首屏按钮文案为 `恢复自动驾驶服务（不发车）`；恢复后仍需重新执行
  `/api/nav2/proof/refresh` 生成图上路线，再由用户勾选安全确认并显式点击执行路线。

这条入口解决的是 planner/controller runtime 未运行导致的“自动驾驶无法准备/无法动”，不是摄像头问题，也不要求雷达作为
低速底盘能动的前置条件；真实完整路线执行、wheel raw L/R 非零和 delivery success 仍要后续独立证明。

## 2026-07-20 Nav2 strict-no-motion start 合同

2026-06-28 记录的 PC 空 body `{}` 代理合同已被本节取代。`POST /api/nav2/start`
现在必须消费下列完整 JSON，不再忽略 request body：

```json
{
  "strict_no_motion": true,
  "base_enabled": false,
  "lidar_enabled": false,
  "reuse_existing_scan": true,
  "timeout_s": 20
}
```

合同只接受上述 5 个字段。bodyless、旧 `{}`、`base_enabled/lidar_enabled=auto`、
任一 enabled 为 `true`、未知字段、缺字段、非 JSON 数字/非有限或超出 `4..20` 秒的
`timeout_s` 都在 subprocess 前 fail closed，并回包
`lifecycle_command_invocation_count=0`。旧 PC 代理必须改为发送该 strict body，
否则 HTTP 即使为 200 也只是结构化 NO-GO。

服务端不会把 body 字段拼到 shell，而是从受管 `o11_nav2_lifecycle.sh start`
命令重建唯一生效 argv，强制 `--base-enabled false --lidar-enabled false`。
`reuse_existing_scan=true` 表示只复用已有 `/scan`；本 start 阶段的
`base_uart_new_open_count=0` 且 `lidar_serial_new_open_count=0`。成功判定必须同时满足：

- `command_result.executed=true` 且 `command_result.ok=true`；
- lifecycle 后置 readback 显示 `running=true`；
- readback 同时确认 `base_enabled=false` 和 `lidar_enabled=false`。

因此 HTTP 200 本身不等于 start 成功，调用方必须检查 `semantic_success`、
`evidence_type`、`root_causes`、`command_result`、`nav2_lifecycle_status`、`evidence.effective_contract`
和 `cleanup`。任一语义验收失败时，API 仅调用受管 `o11 stop` 回收该脚本拥有的
PID/process group。`POST /api/nav2/stop` 也只做同样的 owned cleanup，不发底盘 stop、
不访问 WAVE ROVER UART，不关闭非 o11 拥有的外部进程。

该改动只建立本地可验证的 strict-no-motion API 合同；它不是上车部署证据、
不是 HIL、不是路线执行，也不证明 wheel raw L/R、dropoff 或 delivery success。

## 2026-06-29 Nav2 现场失败分层

2026-06-29 04:00 对 `root@192.168.1.11:37878` 做了一次受控复核：

- `GET /api/camera/health` 返回 `source_first_frame_failed`、`source_readiness=first_frame_failed`、
  `source_usage.status=not_in_use` 和 `uvc_no_frame_not_exclusive`。当前摄像头问题不是后进入页面独占，
  而是 `/dev/video1` UVC 设备没有输出首帧；共享 MJPEG 仍可以让多人看到同一个真实失败原因。
- `GET /api/free-roam/autonomy/latest` 显示 runtime 已加载但 `cmd_vel_publish_enabled=false`、
  `operator_confirmed=false`。自由移动的 start gate 仍是现场安全确认和停止兜底；相机首帧、
  雷达 fresh 和地图画面属于建图验收 gate，不是低速能否移动的前置。
- `POST /api/nav2/start` 只启动 stack-only manager，没有发送 goal、`/cmd_vel`、manual、free-roam、
  delivery 或底盘 JSON 运动命令。当前车上 `nav2_bringup` 已可解析，旧的缺包 blocker 已消失。
- Nav2 bringup 能加载 planner/controller/BT 等节点，但 local costmap 日志仍报
  `Timed out waiting for transform from base_link to map`，`/api/nav2/status` 仍未证明
  `map -> base_link`、AMCL pose、当前 `/scan` 和 fresh route proof。因此自动驾驶“没法动”的当前层级是
  定位/TF/scan/路线证据未成立，不是相机首帧，也不是雷达作为底盘运动前置。
- ESP32 bridge 同时出现 `Serial read error ... device disconnected or multiple access on port?`，
  本轮 start 后立即执行 stop，释放受管 Nav2 进程组和底盘串口，避免影响手控/free-roam 后续验证。

对应代码层收紧：`o11_nav2_lifecycle.sh` start 前新增 `nav2_bringup` 依赖 preflight。若未来又回到缺包状态，
脚本会写 `failed_missing_dependency` 与安装建议，PC/API 不再只能从 launch log 反推根因。

## 2026-06-29 Nav2 stack-only 地图/AMCL/path proof 恢复

本轮继续在真实上位机 `root@192.168.1.11:37878` 上验证。硬件口径仍以
`docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER UART/JSON 资料为准；现场沿用
WAVE ROVER `/dev/ttyS5@115200` 与 LiDAR `/dev/ttyACM0@150000`。

修复点：

- `autonomous.launch.py` 的 `nav2_stack_only` 可显式启动 LiDAR driver 和 `base_link->laser_frame` static TF。
- `o11_nav2_lifecycle.sh` 的 `--base-enabled auto` 会在已有 `/esp32_bridge` 或 `/dev/ttyS5` holder 时复用现有 bridge，
  不开第二个底盘串口进程；`--lidar-enabled auto` 同理避免重复抢 `/dev/ttyACM0`。
- `nav2_params.yaml` 补 `map_server.yaml_filename` 占位，让 Nav2 bringup 的 `map:=...` 真正传给 map server。
- AMCL 默认 `set_initial_pose=true`，启动后先产生 `map->odom`；真实执行前 PC initialpose 仍可覆盖。
- `o10_amcl_nav2_runtime_proof.py` 放宽 TF fallback 探针窗口，避免 Orange Pi 上 ROS CLI 慢启动导致假 timeout。

现场 no-motion 证据：

- `/map_server=active`、`/amcl=active`、`/planner_server=active`、`/controller_server=active`。
- `/map` publisher count 为 1，`/scan` publisher count 为 1。
- `/amcl_pose` frame 为 `map`，`tf2_echo map base_link` 可读。
- `POST /api/nav2/proof/refresh` 返回 `latest_proof_status=nav2_no_motion_path_generation_runtime_observed`、
  `latest_path_generation_succeeded=true`、`latest_path_point_count=18`、
  `latest_scan_consumed=true`、`latest_map_consumed=true`。
- 安全边界仍为 `safe_to_control=false`、`robot_control_executed=false`、`sends_base_motion_commands=false`、
  `delivery_success=false`；本轮未执行 NavigateToPose、未发布 `/cmd_vel`、未发送 WAVE ROVER 运动 JSON。

剩余缺口：这解决“自动驾驶服务为什么准备不起来/没法生成路线”的软件链路问题，但不等于完整路线执行成功。
下一轮真实发车必须在 PC 安全确认后执行路线，并用同窗口 wheel raw L/R 非零、goal result 和 delivery result 收口。

## 2026-07-03 ROS /cmd_vel CLI 发布卡死修复

现场复核自动驾驶/ROS 控制面时，直接在上位机通过 `ros2 topic pub --once /cmd_vel` 发布 Twist 曾卡在
FastDDS shared-memory port 锁文件上，表现为 `RTPS_TRANSPORT_SHM open_and_lock_file failed` 后 API
侧短超时。这会让 PC 或上车 API 看起来像“自动驾驶没法动”，即使底层 `/cmd_vel` topic 和 bridge 仍可用。

本轮上车 `upper_robot_api.py` 修复：

- `publish_ros_cmd_vel_once()` 默认超时从 `2s` 提高到 `10s`，匹配 Orange Pi 上 source ROS 环境和
  `ros2 topic pub` 的实际启动耗时。
- ROS CLI 发布前显式 `export RMW_FASTRTPS_USE_SHM=0`，并在同一命令前缀
  `RMW_FASTRTPS_USE_SHM=0 ros2 topic pub --once --wait-matching-subscriptions 0 --keep-alive 0.1 /cmd_vel ...`，
  避免等待订阅匹配或 FastDDS SHM 锁文件把一次性 publisher 卡死。
- 硬件协议口径继续采用 `docs/vendor/VENDOR_INDEX.md`、
  `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py` 和
  `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：WAVE ROVER newline JSON、
  `/dev/ttyS5@115200` 由现场 bridge 持有，ROS `/cmd_vel` 对应 bridge 下发 `T=13 X/Z`，API 不再为 ROS
  手控另开 UART。

现场验证：

- `POST http://192.168.1.11:8787/api/base/manual`，body
  `{"direction":"forward","speed":0.08,"duration_ms":300,"command_mode":"ros","feedback_mode":"bridge_debug","confirm_hil_checklist":true}`
  返回 `command_result.ok=true`、`stop_result.ok=true`、`manual_command_executed=true`、
  `auto_stop_executed=true` 和 `ros_cmd_vel_transaction.mode=ros_cmd_vel_bridge`。
- 前进 publisher stdout 只显示 `publishing #1`，未再因 SHM 卡死；stop publisher 仍可能打印 FastDDS
  SHM 历史锁警告，但 returncode 为 `0`，不再阻塞 API。
- 同窗口 bridge debug 仍显示 `wheel_feedback_lr_nonzero_proven=false`、`latest_pair L/R=0/0`；因此该修复只证明
  ROS `/cmd_vel` 发布链路恢复，不证明完整 Nav2 路线、wheel raw L/R 非零或 delivery success 已完成。

## 2026-07-03 NavigateToPose runtime reuse and rejection boundary

2026-07-03 05:17-05:20 CST 在真实上位机 `root@192.168.1.11:7878` 复核完整路线执行时，
发现同一台车上已经存在常驻 `esp32_bridge`，它持有 `/dev/ttyS5 @ 115200` 并订阅 `/cmd_vel`。
旧的 O11 goal helper 在 `managed_runtime_opt_in=true` 时会再启动一个 `esp32_bridge`，导致日志出现
`Serial read error ... device disconnected or multiple access on port?`。这不是相机或雷达 gate，
而是自动驾驶执行 helper 与常驻 bridge 抢同一个 WAVE ROVER UART。

本轮调整 `onboard/scripts/o11_nav2_goal_execution_proof.py`：托管 runtime 启动前先只读
`ros2 action list -t`。如果已经观察到 `/navigate_to_pose [nav2_msgs/action/NavigateToPose]`，
helper 复用现有 ROS graph，不再启动第二套 Nav2/bridge runtime，也就不会重复打开
`/dev/ttyS5`。现场坏 graph 会让 `ros2 action list -t` 本身超时，因此 helper 还新增只读进程级
保护：只要 `ps` 观察到现有 `esp32_bridge`、`autonomous.launch.py` 或 `nav2_container`，
也按“现场 runtime 已存在”处理。该分支会在 artifact 的
`managed_runtime.reuse_existing_runtime=true` 与 `managed_runtime.reuse_reason` 中留证。

现场复测结果：

- `POST /api/nav2/goal/execute`，body 使用 `managed_runtime_opt_in=true`、
  `base_command_mode=pwm`、`server_timeout_s=5`、`result_timeout_s=4` 和预览终点
  `goal=(0.8,0.05)`，13.9s 内返回 `status=goal_rejected`。
- artifact 显示 `managed_runtime.reuse_existing_runtime=true`、
  `reuse_reason=existing_runtime_process_observed`、`started=false`、
  `cleanup.boundary=no_process_started`；进程探针同时观察到常驻 `esp32_bridge`、`autonomous.launch.py`
  和 `nav2_container`。这证明 helper 没有再启动第二套 bridge，也没有再抢 `/dev/ttyS5`。
- action server 可达，但 `goal_accepted=false`，没有进入 `/cmd_vel` 运动阶段。
- 常驻 Nav2 日志显示 local costmap 曾持续报 `Invalid frame ID "map"`，随后
  `lifecycle_manager_navigation` 在 planner/server bond 阶段失败，说明当前失败层级是
  Nav2 lifecycle/BT/controller 运行态不健康，而不是 PC 安全确认、摄像头、雷达或目标点坐标本身。
- 因 goal 被拒收，`sends_motion_commands=false`、`publishes_cmd_vel=false`、
  `robot_control_executed=false`、`delivery_success=false` 必须保持关闭；下一步应先通过
  `POST /api/nav2/stop` 与 `POST /api/nav2/start` 恢复 lifecycle，再重跑 goal execution 并复验
  同窗口 wheel raw L/R 与 delivery result。
`2026-07-11 18:45` 起，`o10_amcl_nav2_runtime_proof.py` 在进入 `/scan`、`/initialpose`、
AMCL/TF 和 path generation 之前，先落一层 `proof.board_source_preflight`。`2026-07-11 19:46`
继续把这层从“`command -v ros2` 整段 timeout”拆成四个只读阶段，避免把 source 卡顿、
PATH 缺失、CLI 启动卡死和 Python/rclpy import 混成同一个 blocker：

- `source_stage`：`/opt/ros/humble/setup.bash`、workspace setup、`cd workdir` 是否完成；
- `path_lookup`：`command -v ros2`、`type -a ros2`、`which ros2` 的 returncode、timeout 与短输出；
- `cli_invocation`：最小 `ros2 --help` invocation 是否能自然返回；
- `python_rclpy`：sourced shell `python3 -c 'import rclpy'`。

artifact 必须至少能读回：

- `proof.board_source_preflight.source_stage_ok`
- `proof.board_source_preflight.source_stage`
- `proof.board_source_preflight.path_lookup`
- `proof.board_source_preflight.cli_invocation`
- `proof.board_source_preflight.python_rclpy`
- `proof.board_source_preflight.ros2_cli_path_ok`
- `proof.board_source_preflight.ros2_cli_invocation_ok`
- `proof.board_source_preflight.ros2_cli_ok`
- `proof.board_source_preflight.rclpy_import_ok`
- `python_executable`
- `rclpy.__file__`
- `sys.path[:8]`
- `proof.board_source_preflight.classification`

如果这层失败，helper 必须 fail-closed：

- 跳过 `/scan` attempt
- 跳过 `/initialpose` publish
- 跳过 path generation
- 继续保持 `safe_to_control=false`
- 继续保持 `robot_control_executed=false`
- 继续保持 `delivery_success=false`
- 继续保持 `hil_pass=false`

同时，map lifecycle 不再只混在泛化 root cause 中，而是单独写到
`proof.map_lifecycle_preflight`。因此这轮之后的现场读数顺序必须是：

1. `board_source_preflight`
2. `map_lifecycle_preflight`
3. `/scan` attempts
4. `/amcl_pose`
5. `map->odom`
6. `path_generated`

如果 root cause 仍只写历史泛化 `ros2_command_unavailable_after_bash_source`，而没有以上 preflight
字段，就说明 helper 还没有进入 18:45/19:46 合同。本轮之后新的失败分类必须落到更窄层级：

- `board_source_preflight_source_timeout`
- `board_source_preflight_source_failed`
- `board_source_preflight_ros2_cli_path_missing`
- `board_source_preflight_ros2_cli_which_timeout`
- `board_source_preflight_ros2_cli_invocation_timeout`
- `board_source_preflight_ros2_cli_invocation_failed`
- `board_source_preflight_rclpy_import_timeout`
- `board_source_preflight_rclpy_import_failed_*`
- `board_source_preflight_ready`

`2026-07-12 05:52` 起，`proof.board_source_preflight` 的主路径改为
`schema=trashbot.o10.source_amortized_cli_preflight.v1`。helper 会在同一个 bounded shell
内完成 `/opt/ros/humble/setup.bash`、workspace setup、`cd workdir`、`command -v ros2`、
`which ros2`、`type -a ros2`、最小 `ros2 --help` invocation 和 child Python
`rclpy import`。这些子命令继承同一次 source 后的环境，不再分别通过 `run_ros()` 重新
source ROS/workspace，因此 artifact 中会额外写：

- `proof.board_source_preflight.source_amortized_cli_preflight_schema`
- `proof.board_source_preflight.source_and_cli_in_one_shell`
- `proof.board_source_preflight.per_command_source_overhead_eliminated`
- `proof.board_source_preflight.commands_executed_after_single_source`
- `proof.board_source_preflight.amortized_shell`

旧字段仍必须存在：`source_stage`、`path_lookup`、`cli_invocation`、`python_rclpy`、
`ros2_cli_path_ok`、`ros2_cli_invocation_ok`、`ros2_cli_ok`、`cli_ready`、`runtime_ready`、
`classification` 和 `commands`。读数规则也随之收紧：

- source 成功但 `command -v` / `which` / `type -a` 任一超时，继续收口为
  `board_source_preflight_ros2_cli_which_timeout`；
- source 成功且 PATH lookup 成功，但 `ros2 --help` 超时，收口为
  `board_source_preflight_ros2_cli_invocation_timeout`；
- `cli_ready=true` 后，rclpy import、graph、lifecycle、AMCL 或 TF 失败不得再反推成
  `workspace_source_or_env_mismatch`，只能写成对应 runtime/graph/lifecycle blocker；
- 所有场景仍保持 strict no-motion：不得发布 `/cmd_vel`、不得调用 `/api/base/manual`、
  不得发送 NavigateToPose、不得打开 WAVE ROVER UART。

`2026-07-12 06:54` 起，`proof.board_source_preflight` 再把 CLI readiness 明确拆成
heavy/light/rclpy 三段：

- `cli_invocation` 继续保留 `ros2 --help >/dev/null`，但只做 heavy 诊断；
- `lightweight_readiness` 当前固定记录 `ros2 daemon status` 和 `ros2 node list`；
- `python_rclpy` 继续只回答 child Python `rclpy import` 是否可用。

因此 closeout 时不要再把 `ros2 --help` timeout 直接当成 preflight 主 blocker。只要
`lightweight_readiness.ok=true`，就接受：

- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.board_source_preflight.lightweight_cli_ready=true`
- `proof.board_source_preflight.cli_ready=true`
- `proof.board_source_preflight.runtime_ready=true`（前提是 `rclpy_import_ok=true`）

最新 true-board `330s` no-motion artifact
`sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness_330s.raw.json`
已经证明：

- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `cli_invocation.timed_out=true`
- `cli_ready=true`
- `runtime_ready=true`

helper 也因此真正进入了 downstream no-motion probes。当前 final blocker 已从 preflight 前移到
`map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed` 和
`/tf_topic_missing`，不再回退成 `workspace_source_or_env_mismatch`。

`2026-07-12 07:53` 起，本轮 strict no-motion helper 会在旧字段外新增
`proof.downstream_recovery_summary`，专门把 map、AMCL、scan 和 TF 的下游 blocker 放在同一层读。
这层 summary 不替代旧的 `map_lifecycle_preflight`、`localization_signal_freshness`、
`amcl_readiness_summary`、`tf_readiness_summary` 或 `path_generation_gate`；它只是把这些字段归一成
下一轮可派工的摘要。

读取顺序固定为：

1. `proof.downstream_recovery_summary.readiness_inputs`：确认
   `board_source_preflight_ready=true`、`lightweight_cli_ready=true`、`cli_ready=true`、
   `runtime_ready=true`。`ros2 --help` 仍只是 heavy diagnostic。
2. `proof.downstream_recovery_summary.map_lifecycle.node_summaries`：区分
   `*_lifecycle_command_timeout`、`*_lifecycle_inactive_stdout`、`*_lifecycle_command_failed`
   和 `*_lifecycle_probe_skipped`。只有 stdout 明确 inactive 或 active parse 失败，才把它写成
   lifecycle 事实；graph blocked 后 skipped 不能当作 inactive。
3. `proof.downstream_recovery_summary.scan`：先看 `publisher_count` 和
   `blocked_reason`。`/scan_no_publisher`、`/scan_qos_or_window_timeout`、
   `/scan_publisher_visible_but_no_sample` 是不同 blocker；如果落到 LiDAR serial/runtime 事实，
   必须交 Hardware owner 读取 `docs/vendor/VENDOR_INDEX.md`，不能在本 helper 里猜串口或接线。
4. `proof.downstream_recovery_summary.map.topic_sample`：保留 `/map_once_not_observed`
   的 legacy root cause，同时把当前分类拆成 `/map_topic_missing`、`/map_no_publisher`、
   `/map_sample_timeout` 或 `/map_sample_not_observed`。
5. `proof.downstream_recovery_summary.tf`：先看 `tf_topic.blocked_reason` 是否为
   `/tf_topic_missing`，再看 `map_to_odom_dynamic.blocked_reason` 是否为
   `map_to_odom_dynamic_source_missing`。`map_to_base_link` 只是 downstream derived gate，不能替代
   AMCL dynamic `map->odom` source。
6. `proof.downstream_recovery_summary.path_generation_gate`：只有 map、scan、AMCL 和 TF 全 ready
   时才允许 planner-only path gate；否则 `path_generation_attempted=false` 必须保持。

本字段仍是 `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`。它不证明
NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、route execution、HIL pass、
delivery success 或 production evidence。

`2026-07-11 20:46` 起，`o10_amcl_nav2_runtime_proof.py` 的 live/local artifact
继续把 AMCL、TF 和 path gate 收束成固定摘要字段，便于在 helper 被 timeout、SIGTERM
或 SSH 中断时仍能读到第一 root cause：

- `proof.artifact_closeout`：记录 `artifact_kind`、`last_phase`、`primary_root_cause`
  和 `signal_root_causes`。如果同时存在 AMCL/TF blocker 与 `sigterm_before_final_artifact`，
  读取时优先看 `primary_root_cause`，不要把 signal 当成定位根因。
- `proof.amcl_readiness_summary.amcl_lifecycle`：记录 `/amcl` lifecycle 是否 active、
  `map_server_active`、`classification` 和原始 lifecycle result。
- `proof.amcl_readiness_summary.amcl_pose_sample`：记录 `/amcl_pose` topic type、
  publisher/subscriber、sample timing、stamp/freshness 和 blocked reason。AMCL active
  不等于 `/amcl_pose` sample fresh，二者必须分开验收。
- `proof.tf_readiness_summary.map_to_odom_dynamic`：只接受 dynamic `map->odom` 作为 AMCL
  定位边，不能用 static source 或 downstream `map->base_link` 反推。
- `proof.tf_readiness_summary.odom_to_base_link`：记录 odom/base edge 的 source、freshness
  和 failure reason。
- `proof.tf_readiness_summary.map_to_base_link`：作为 downstream derived gate，只在
  `map->odom` 和 `odom->base_link` 都 ready 时成立；失败时写 `blocking_segment`。
- `proof.path_generation_gate`：记录 path generation requested/attempted/generated、point
  count、planner readiness 和未 attempt 的 root cause。

本轮真实板 artifact
`sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/artifacts/live_o10_amcl_tf_final_artifact_bounded_probe.raw.json`
显示旧 source/CLI blocker 已保持 ready：`board_source_preflight_ready`、
`ros2_cli_ok=true`、`rclpy_import_ok=true`。新的 live 结论是：

- `managed_runtime_started=true`；
- `/amcl_pose` 有 sample，但 freshness 为 stale；
- `/amcl` lifecycle readback 为 inactive，`amcl_readiness_summary.ready=false`；
- `map_to_odom_dynamic.observed=false`，`map_to_base_link.observed=false`；
- `path_generation_requested=true`，但 `path_generation_attempted=false`、
  `path_generated=false`，blocked reason 为 `path_generation_blocked_by_localization_not_ready`；
- `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
  `robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
  `hil_pass=false`、`uses_base_uart=false`。

因此该 artifact 是 no-motion AMCL/TF/path readiness diagnosis，不是 fixed-route execution、
NavigateToPose、HIL pass、delivery success 或 production evidence。下一轮最小命令仍是复跑
同一 no-motion helper，但优先修复 `/amcl` lifecycle inactive、`/scan` 双 QoS timeout、
`/map_once_not_observed`、`cli_initialpose_publish_failed` 和 dynamic `map->odom` 缺失。

`2026-07-12 01:50` 起，`o10_amcl_nav2_runtime_proof.py` 在 strict no-motion helper 中新增
`proof.ros2_graph_timeout_root_cause`。该字段专门承接上一轮 final
`ros2_node_list_timeout`，不能被 `/tf_topic_missing`、lifecycle skipped 或 path gate 失败覆盖。

字段形状固定为：

- `classification`：主分类，取值限定在 `ros2_daemon_or_dds_graph_discovery_timeout`、
  `ros2_cli_plugin_or_import_timeout`、`workspace_source_or_env_mismatch`、
  `managed_process_lifecycle_not_ready`、`tf_runtime_secondary_after_graph_blocked`、
  `root_cause_unclassified_after_probe`。
- `primary_candidate`：当前最可信主因和短 reason。
- `excluded_candidates`：本轮已通过 probe 排除的候选，例如 sourced env ready、`ros2 node list --help`
  可返回、`rclpy import` 可返回。
- `remaining_candidates`：仍未排除的候选；当 graph wait blocked 时，managed lifecycle 和
  `/tf_topic_missing` 通常只能留在这里，不能写成主因。
- `probes`：低预算只读命令摘要，包括 `ros2 node list`、`ros2 node list --no-daemon`、
  `ros2 daemon status`、`ros2 node list --help`、`ros2 topic list`、
  `rclpy_graph_segments` 和 `workspace_environment`。
- `evidence_boundary`：固定写明 strict no-motion proof boundary。

`2026-07-12 02:51` 起，root-cause probes 的测量口径改为 source-amortized batch。
旧版每条 `probes.*` 都通过 `run_ros()` 重新 source ROS/workspace；当
`board_source_preflight.source_stage.elapsed_ms` 接近 5 秒，而单条 timeout 只有 2 到 5 秒时，
timeout 可能只是在 source 阶段耗尽预算。新版 artifact 必须优先看：

- `probes.source_amortized_batch.source_stage`：单次 source ROS setup、workspace setup 和
  `cd workdir` 的结果与耗时；
- `probes.source_amortized_batch.commands.ros2_node_list`、
  `ros2_node_list_no_daemon`、`ros2_daemon_status`、`ros2_node_list_help`、
  `ros2_topic_list`：这些 command 的 timeout 不再包含重复 source 开销；
- `probes.source_amortized_batch.workspace_environment.summary`：同一个 sourced shell 内的
  ROS/workspace 环境摘要；
- `probes.source_amortized_batch.rclpy_graph_stage_stream`：逐段 flush 的
  `import_rclpy`、`rclpy_init`、`create_node`、`graph_wait` stage，用于定位 timeout
  发生在 rclpy 启动前段还是 graph discovery 窗口。

兼容旧 reader 时，`probes.ros2_node_list`、`probes.ros2_node_list_help`、
`probes.workspace_environment` 和 `probes.rclpy_graph_segments` 仍会存在，但它们应视为
`source_amortized_batch` 的回填摘要，不再代表逐条 `run_ros()` 的旧测量方式。分类器也必须把
`evidence_priority=source_amortized_batch` 作为主读数：只有 source 后 `ros2 node list --help`
仍 timeout，且 `rclpy_graph_stage_stream` 卡在 `import_rclpy` / `rclpy_init` /
`create_node` 前段时，才允许继续把主因写成 `ros2_cli_plugin_or_import_timeout`；如果 help
可完成而 node/topic/daemon graph timeout，则主因应优先落到 daemon/DDS graph discovery 或
managed lifecycle，而不是 CLI/plugin/import。

`probes.workspace_environment` 只保留 `ROS_DISTRO`、`ROS_DOMAIN_ID`、`RMW_IMPLEMENTATION`
和 `AMENT_PREFIX_PATH` / `PYTHONPATH` / `LD_LIBRARY_PATH` 是否包含 ROS 与上车 workspace 的摘要；
不得记录全量环境变量。`ros2 node list --no-daemon` 在当前 ROS2 CLI 不支持时应写
`boundary=unsupported_option`，这不是失败，只说明该对照不可用。

如果 `managed_runtime_started=true` 但 graph wait blocked，`probes.managed_process` 必须写：

- managed process 是否仍存活；
- expected nodes 与 observed nodes；
- missing expected nodes；
- managed runtime log tail；
- lifecycle probe 是 executed、partial 还是 `skipped_after_ros2_graph_timeout`。

这条规则的验收含义是：skipped lifecycle 不能再被读成 `map_server_active=false` 或
`amcl_active=false` 的强证明。它只能说明 graph blocked 后未能完成 lifecycle proof。只有实际
`ros2 lifecycle get` 返回 inactive，才能把 lifecycle inactive 当成主证据。

同一 artifact 必须继续保持 no-motion false 字段：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- gate 未 ready 时 `path_generation_attempted=false`、`path_generated=false`

`2026-07-12 03:52` 起，`proof.ros2_graph_timeout_root_cause` 下还有 additive
`daemon_dds_split`。该字段不替代旧 `classification`、`primary_candidate` 或
`probes`，只负责把 `ros2_daemon_or_dds_graph_discovery_timeout` 继续拆成可执行候选。
读取顺序如下：

1. 先读 `daemon_dds_split.primary_candidate.candidate`。候选名固定为
   `ros2_daemon_state_timeout`、`dds_discovery_or_domain_mismatch`、
   `workspace_source_or_env_mismatch`、`managed_process_lifecycle_visibility_blocked`、
   `graph_command_budget_insufficient`、`ros2_cli_no_daemon_unsupported`。
2. 再读 `safe_environment_summary`。这里仅保留 `ROS_DISTRO`、`ROS_DOMAIN_ID`、
   `RMW_IMPLEMENTATION`、`which_ros2`，以及 `AMENT_PREFIX_PATH`、`PYTHONPATH`、
   `LD_LIBRARY_PATH` 是否包含 ROS 和 onboard workspace 的布尔/count 摘要。
3. 再读 `daemon_command_summaries`。若 `reset_skipped=true`，必须记录
   `reset_skip_reason`；若 `reset_attempted=true`，必须对照 `ros2_daemon_stop`、
   `ros2_daemon_start`、`ros2_node_list_after_daemon_reset`、
   `ros2_topic_list_after_daemon_reset` 的 bounded summary。
4. 再读 `managed_lifecycle_visibility_summary` 和 `graph_budget_summary`，区分
   managed lifecycle 被 graph timeout 遮蔽，还是命令预算不足。

`2026-07-12 04:51` 起，`daemon_dds_split` 下继续新增 additive
`daemon_safe_graph_readback`。它专门记录上一轮 `next_live_command` 等价的 daemon-safe
stop/start + 8s graph readback，读取顺序如下：

1. `reset_attempted`、`reset_completed`、`reset_skipped`、`reset_skip_reason`
2. `commands.ros2_daemon_stop`、`ros2_daemon_start`、`ros2_daemon_status_after_reset`
3. `commands.ros2_node_list_after_daemon_reset`、
   `commands.ros2_topic_list_after_daemon_reset`
4. `graph_readback.node_list_outcome`、`graph_readback.topic_list_outcome`
5. `primary_conclusion`
6. `next_step`

这个合同不替代 `daemon_command_summaries`、`graph_budget_summary` 或
`primary_candidate`；它只是把 reset 后的 8s node/topic readback 单独固化出来。即使
`primary_conclusion=graph_readback_recovered_after_daemon_reset`，下一跳也只能回
lifecycle/localization gate，不能直接进入 motion/path。

daemon reset 只允许用于 ROS2 CLI graph 层的 no-motion recovery。它不发布 `/cmd_vel`，
不调用 `/api/base/manual`，不发送 NavigateToPose，也不打开 WAVE ROVER UART。reset 后
如果 node/topic list 恢复，只能说明 daemon graph visibility 有进展；reset 后如果仍 timeout，
下一步应优先查 DDS/domain/RMW/env 或 managed lifecycle visibility。该 split 仍不证明
path generation、fixed-route execution、HIL pass、delivery success 或 production cloud。

`2026-07-12 08:55` 起，strict no-motion helper 又新增
`proof.map_lifecycle_preflight.lifecycle_cli_budget_recovery`。它是本轮 O3/O1
`lifecycle_cli_budget_recovery` 的主读数，必须优先于 `/scan`、`/map` 和 TF 下游字段读取：

- `map_server.command_summary.first_attempt`：`ros2 lifecycle get /map_server`，10s budget。
- `map_server.command_summary.retry_attempt`：同一命令，retry budget 来自 `--timeout-s`，本轮为 18s。
- `amcl.command_summary.first_attempt` / `retry_attempt`：同样保留 command、timeout budget、
  elapsed、stdout、stderr、returncode、timed_out 和 classification。
- `graph_visibility`：同窗 `ros2 node list` readback，记录 target node 是否可见。
- `classification`：稳定值包含 `lifecycle_command_timeout`、`inactive stdout`、
  `graph ok but lifecycle timeout`、`active` 和 `lifecycle command failed`。

本轮 live artifact 为
`sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`。
关键结论是：`board_source_preflight_ready` 仍成立；`/amcl` first attempt 10s timeout，
retry 15.615s 返回 `active [3]`，因此 `amcl` 分类为 `active`；`/map_server`
first attempt 10s timeout，retry 11.324s 返回 `Node not found`，因此
`map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_inactive`，
`blocking_reasons.map_server=map_server_lifecycle_command_failed`。同窗
`ros2 node list` lifecycle visibility probe 8s timeout，但 daemon-safe graph readback 后
node/topic graph 可见，且只看到 `/amcl`、`/planner_server` 等节点，没有 `/map_server`。

因此该轮只允许收口为 lifecycle/graph diagnostic delta：`/scan`、`/map`、`/odom` 和
TF source 已按 gate 写成 `*_skipped_until_lifecycle_cli_readback_clean`，不能再把
`/scan_reliable_and_best_effort_timeout`、`/map_topic_missing` 或 `/tf_topic_missing`
当作本轮主 blocker。安全字段必须继续为 `safe_to_control=false`、
`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、
`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、
`uses_base_uart=false`，且 `path_generation_attempted=false`、`path_generated=false`。

`2026-07-12 09:54` 起，strict no-motion helper 在 08-55 lifecycle budget 字段外新增
`proof.map_server_graph_lifecycle_visibility`。这个字段是本轮主读数，proof boundary 为
`software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`。读取顺序是：

1. `readiness_inputs`：确认 `board_source_preflight_ready`、`lightweight_cli_ready=true`、
   `cli_ready=true`、`runtime_ready=true` 是否仍成立。这些只是进入 graph/lifecycle
   诊断的前提，不能写成 localization ready。
2. `node_graph_inventory`：看 `/map_server` 是否在 graph 中可见，并同时保留 lifecycle
   snapshot、managed wait observed nodes 和 target node visibility。
3. `daemon_dds_visibility`：看 `ros2 node list`、`ros2 node list --no-daemon`、
   `ros2 daemon status`、`ros2 topic list` 与 daemon-safe readback 是否把问题归到
   daemon/DDS graph visibility。
4. `lifecycle_readback`：读取 `/map_server` first/retry `ros2 lifecycle get /map_server`
   的 command、timeout budget、elapsed、stdout、stderr、returncode 和 classification。
5. `managed_runtime_context` 与 `lifecycle_manager_or_process_startup_context`：只用于区分
   lifecycle manager 或 managed process startup 未完成，不能替代 node graph 事实。
6. `canonical_classification`：稳定值为 `map_server_node_absent`、
   `lifecycle_manager_or_process_startup_missing`、`daemon_or_dds_graph_visibility_failed`、
   `helper_budget_or_timing_exhausted` 或 `map_server_lifecycle_active`。

09-54 与 08-55 的区别是：08-55 证明 `/amcl` retry 已读到 `active [3]`，并把
`/map_server` retry 收口为 `Node not found`；09-54 进一步解释 `Node not found`
属于节点缺席、daemon/DDS graph 不可见、lifecycle manager/process startup 未完成，还是 helper
budget/timing 不足。09-54 与 07-53 的区别是：07-53 关注 downstream `/scan`、`/map`
和 TF；09-54 只把这些字段当 guarded context，主 blocker 必须来自 `/map_server`
graph/lifecycle visibility。

无论分类是否变成 `map_server_lifecycle_active`，该 artifact 仍不证明 planner path、
NavigateToPose、route execution、delivery、HIL 或 production cloud。固定红线仍是：不发布
`/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART，
并继续保持 `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`、`uses_base_uart=false`、`path_generation_attempted=false`、
`path_generated=false`。

`2026-07-12 10:54` 起，strict no-motion helper 在 09-54 visibility 字段外新增
`proof.map_server_presence_recovery`。这个字段是 presence recovery sprint 的主读数，
schema 为 `trashbot.o10.map_server_presence_recovery.v1`，proof boundary 为
`software_proof_o3_o1_strict_no_motion_map_server_presence_recovery_only`。读取顺序是：

1. `recovery_attempted` 与 `recovery_path.managed_runtime_requested`：必须为 `true` 才说明
   本轮真的走了 `--managed-runtime-opt-in` recovery，而不是继续只读 existing graph。
2. `managed_map_yaml`：只把 `basename`、`configured_basename`、`exists`、`size_bytes`、
   `sha256_prefix` 和 `path_policy` 作为消费字段；绝对 board path 只保留在内部 artifact
   字段中，不作为外部 summary 的匹配条件。
3. `process_presence`：读取 managed runtime process group、startup error、expected process
   names 和 log tail，用来区分进程未起、提前退出、启动日志报错。
4. `node_presence`：读取 observed nodes、`/lifecycle_manager` 是否可见、`/amcl` 是否可见、
   `/map_server` target 是否可见，以及 managed wait reason。
5. `lifecycle_readback`：读取 `/map_server` first/retry lifecycle command、timeout budget、
   stdout/stderr/returncode 和 `node_not_found_observed`。
6. `canonical_classification`：稳定值包含
   `presence_recovery_not_requested_read_only_existing_graph`、`managed_map_yaml_missing`、
   `managed_map_yaml_unreadable`、`managed_runtime_start_failed`、
   `managed_runtime_process_exited_before_map_server_presence`、
   `managed_runtime_graph_unreadable_after_start`、`managed_runtime_started_map_server_not_observed`、
   `lifecycle_manager_not_serving_map_server`、`map_server_lifecycle_rpc_timeout_after_recovery`、
   `map_server_lifecycle_not_active_after_recovery`、
   `map_server_lifecycle_command_failed_after_recovery` 或 `map_server_lifecycle_active`。

如果 09-54 的 `map_server_graph_lifecycle_visibility.canonical_classification` 仍显示
`map_server_node_absent`，但 10-54 的 `map_server_presence_recovery.canonical_classification`
已经变成 `lifecycle_manager_not_serving_map_server`、`managed_runtime_started_map_server_not_observed`
或 `managed_runtime_graph_unreadable_after_start`，closeout 应以 10-54 字段为主，因为它证明
recovery path 已执行，blocker 已从“只读节点缺席”收窄到 managed runtime 启动后的可修复层。

该 recovery 仍是 no-motion proof。即使 `canonical_classification=map_server_lifecycle_active`，
也只能继续交给 Algorithm 恢复 `/map` sample、AMCL pose、dynamic `map->odom` 和 planner/path
readiness；不能宣称 route execution、delivery、HIL、safe-to-control 或 production cloud。

`2026-07-12 11:54` 起，strict no-motion helper 在 presence recovery 外新增
`proof.map_server_lifecycle_activation`。这个字段只回答 `/map_server` configure/activate
为什么没有 clean，不把 `/scan`、AMCL、TF 或 planner timeout 当作主结论。读取顺序是：

1. `map_yaml_pgm_readback.yaml` / `pgm`：确认 `trashbot_map.yaml` 与 `trashbot_map.pgm`
   是否存在、可读、size 和 `sha256_prefix`。
2. `map_yaml_pgm_readback.fields`：读取 `image`、`image_path`、`resolution`、`origin`、
   `occupied_thresh`、`free_thresh`、`mode`、`negate`、`required_missing` 和
   `valid_for_map_server`。
3. `launch_parameters`：确认 map_server `frame_id=map`、`use_sim_time=false`、
   lifecycle manager `managed_node_list=["map_server","amcl"]`、`bond_timeout_s=8.0`、
   `service_timeout_s=12.0`，以及 `RMW_FASTRTPS_USE_SHM=0`、
   `FASTDDS_BUILTIN_TRANSPORTS=UDPv4`。
4. `runtime_log` 与 `lifecycle_manager_state_change_result`：读取 configure、yaml load、
   image load、map read、`Failed to change state for node: map_server` 和 bringup failed 的顺序。
5. `canonical_classification`：稳定值包含
   `map_server_yaml_image_unreadable`、`map_server_yaml_invalid_fields`、
   `map_server_frame_id_missing_or_invalid`、`map_server_process_exited_during_configure`、
   `map_server_configure_exception`、`lifecycle_manager_map_server_name_mismatch`、
   `lifecycle_manager_map_server_namespace_mismatch`、`map_server_activate_callback_failed`、
   `map_server_lifecycle_service_timeout_with_process_alive` 或 `map_server_lifecycle_active`。

本轮 true-board primary artifact 为
`sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/artifacts/live_o10_map_server_lifecycle_activation_repair.raw.json`。
结论是 `board_source_preflight_ready`、managed runtime 已启动，map yaml/PGM 都可读，
required yaml fields valid，但 lifecycle manager 在 valid map readback 后仍报
`Failed to change state for node: map_server`。因此主分类收口为
`map_server_activate_callback_failed`，下一轮应检查 Nav2 map_server transition callback、
lifecycle manager RPC/bond 时序或同一进程日志，而不是转去消费 `/scan`、AMCL、TF 或 planner
secondary blocker。

`2026-07-12 12:55` 起，strict no-motion helper 在 activation summary 外新增
`proof.map_server_transition_callback_probe`。这个字段专门消费 `/map_server` configure/activate
transition、`/map_server/change_state` response、lifecycle manager service/RPC timing、bond timing、
process status 和 preserved pre-cleanup log evidence。当前 true-board artifact 为
`sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/artifacts/live_o10_map_server_transition_callback_probe.raw.json`，
主分类已从上一轮泛化的 `map_server_activate_callback_failed` 下钻为
`map_server_configure_callback_return_failure`，detail 为
`lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`。

读取该字段时，优先看：

1. `transition_sequence.observed_stage`：当前为 `configure`，说明 activate 阶段尚未 clean 到达。
2. `transition_sequence.configure`：确认 lifecycle manager requested、map_server callback entered、
   yaml/image load、map read completed、state change failed 以及 state-change failure 与 map read
   完成的先后顺序。
3. `service_rpc_timing`：记录 `/map_server/change_state`、service timeout budget、readback timeout
   与 inferred change-state response；当前 response 收口为 `failure`，不是 generic CLI timeout。
4. `bond_timing`：当前为 `not_created_before_configure_return_failure`，说明尚未进入 active 后 bond wait。
5. `activation_summary_reference`：保留上一轮 activation 字段，供兼容旧 closeout，但不能再把它作为
   本轮最窄主 blocker。

这个 transition callback proof 仍是 O3/O1 strict no-motion diagnostic material。它不证明
`/map_server` lifecycle active、`/map` sample、AMCL pose、dynamic `map->odom`、planner path、
route execution、delivery、HIL 或 production external evidence。

`2026-07-12 13:54` 起，helper 对同一 configure failure 再细分 map IO / ChangeState ordering。
为了避免板端 FastDDS SHM 端口锁把 graph/lifecycle RPC 混成泛化 callback failure，所有
`run_ros()` 与 managed runtime 子进程都继承 `RMW_FASTRTPS_USE_SHM=0` 和
`FASTDDS_BUILTIN_TRANSPORTS=UDPv4`。`proof.map_server_transition_callback_probe.canonical_classification`
新增稳定值：

- `map_server_configure_return_failure_before_deferred_map_read_completed`：lifecycle manager 已发起
  configure ChangeState 并收到 failure，但 map read completion 在 failure 之后才出现在日志中。
- `map_server_configure_return_failure_after_map_read_completed`：map read completion 已先出现，随后
  configure ChangeState 仍失败。
- `map_server_change_state_rpc_dds_shm_transport_port_lock`：日志出现 FastDDS SHM
  `open_and_lock_file failed`，同时 graph/lifecycle readback timeout 或 state-change failure 存在。

本轮 true-board artifact 为
`sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/artifacts/live_o10_map_server_configure_failure_repair.raw.json`。
结论是 `board_source_preflight_ready`、`managed_runtime_started=true`，但
`map_server_active=false`、`amcl_active=false`。Primary root cause 已从 12:55 的泛化
`map_server_configure_callback_return_failure` 收窄为
`map_server_configure_return_failure_before_deferred_map_read_completed`，detail 仍记录
`lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`。
下一轮应继续查 lifecycle manager ChangeState 与 map_server `on_configure` / map IO completion
ordering；不能把该 artifact 当成 lifecycle clean、path generation、route execution、delivery、
HIL 或 production external evidence。固定保持
`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`、`uses_base_uart=false`、`path_generation_attempted=false`、
`path_generated=false`。

`2026-07-12 14:54` 起，helper 不再简单优先使用 managed runtime cleanup tail，而是从
`process_presence.log_tail`、`managed_runtime_wait_result.log_tail`、`commands.managed_runtime.log_tail`
等候选中选择包含 `/map_server` configure、ChangeState failure、yaml/image/map IO 事件最多的
日志窗口。`proof.map_server_transition_callback_probe.transition_sequence` 与
`runtime_log_window` 会新增：

- `line_indices.lifecycle_manager_configure_requested`
- `line_indices.map_server_configure_callback_entered`
- `event_timestamps_s.*`
- `transition_sequence.configure.state_change_failed_before_map_server_configure_callback`

若同一 pre-cleanup 窗口证明 lifecycle manager 的 ChangeState failure 发生在 `/map_server`
callback 进入之后、`image_file` 开始加载之后、`Read map` 完成之前，canonical classification 会收口为
`map_server_changestate_response_failure_after_image_load_before_map_read_completed`。这个分类比
`map_server_configure_return_failure_before_deferred_map_read_completed` 更窄，下一步应查
lifecycle manager ChangeState future/response timeout 与 map IO image decode completion 的顺序；
它仍然不是 lifecycle clean/active、planner path、route execution、HIL 或 delivery proof。

如果某次 live 窗口已经完成 map read 并继续进入 `Configuring amcl` 后才失败，helper 会把主因降到
`map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure`。该分类说明旧 map_server
configure blocker 当轮未复现，但仍未证明 `/map_server` active，因为 lifecycle manager 在完成整组
configure/activate 前已被 AMCL configure 阻断。

`2026-07-12 15:54` 起，helper 会继续拆分 14:54 的 image-load 窗口：如果同一 runtime log
证明 lifecycle manager 已收到 `/map_server/change_state` failure，并且后续仍出现 `Read map ...`
完成日志，则主分类升级为
`map_server_changestate_response_false_before_map_io_completion`。这个分类表示 ChangeState response
已经是 false，但 map IO 在 response failure 后继续完成；比
`map_server_changestate_response_failure_after_image_load_before_map_read_completed` 更窄，下一步应查
`nav2_map_server` `on_configure` return false path、map IO continuation 和 lifecycle manager
ChangeState future/response 关系。`service_rpc_timing.map_io_timing` 会记录
`image_load_to_state_failure_ms`、`state_failure_to_map_read_completed_ms`、
`configure_to_map_read_completed_ms` 和
`change_state_response_false_while_map_io_incomplete`。

`2026-07-12 16:55` 起，如果同一窗口还能证明 managed map YAML/PGM readable、
YAML fields valid、runtime analysis ok，且未观察到 map_server-scoped exception 或 ChangeState RPC
timeout，helper 会把主因继续收窄到
`map_server_on_configure_return_false_after_valid_map_io_deferred_completion`。这时必须同时读取
`proof.map_server_transition_callback_probe.on_configure_return_source`：

- `primary_source=on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`
- `source_family=on_configure_return_false_source`
- `map_input_validation.valid_for_map_server=true`
- `excluded_sources.parameter_or_map_file_invalid_excluded_by_readback=true`
- `return_path_evidence.change_state_response_false_before_map_io_completion=true`

这个分类把 15:54 的 timing 现象落到 `on_configure` return false source bucket，而不是再次包装
同名 wrapper。下一轮应查 Nav2 map_server `loadMapResponseFromYaml` return code、callback exception
是否被吞掉、executor/log ordering，或 lifecycle manager 对 ChangeState response 的处理。

该分类仍是 strict no-motion diagnostic material，不证明 `/map_server active`、AMCL ready、
planner path、route execution、HIL、delivery 或 production external evidence。

`2026-07-12 17:55` 起，helper 在 transition summary 中新增
`proof.map_server_transition_callback_probe.load_map_response_from_yaml`，并把 valid map inputs 下的
主分类继续收窄到
`map_server_loadmap_response_success_equivalent_after_changestate_failure`。这个字段的核心边界是：

- `direct_return_code_observed=false`
- `return_code=not_logged_by_nav2_map_server_runtime`
- `response_status=success_equivalent_logged_after_lifecycle_changestate_failure`
- `load_map_response_status_at_changestate_failure=pending_or_not_logged`
- `on_configure_return_path=return_failure_before_deferred_loadmap_response_completion_log`
- `lifecycle_changestate_response_handling.inferred_response_status=failure`

这表示现场 runtime log 没有直接打印 `loadMapResponseFromYaml` return code 或 error string，
但已同时证明 YAML/image 开始加载、lifecycle manager 先收到 ChangeState failure、随后 `Read map ...`
仍完成。因此可把 root cause 从 16:55 的 on_configure source bucket 继续下钻到
LoadMap response/status ordering：response success-equivalent 证据晚于 lifecycle failure 出现，
下一步应查 `nav2_map_server` 的 `on_configure` return false 分支、executor/log ordering，或
lifecycle manager 对 ChangeState response 的处理。该字段仍不能证明 `/map_server active`。

17:55 accepted true-board artifact 的最终 routing baseline 是
`canonical_classification=map_server_lifecycle_active`，应以
`proof.managed_runtime_log_lifecycle_readback` 为准解释生命周期状态：

- `clean=true`
- `managed_nodes_active_logged=true`
- `map_server_active=true`
- `amcl_active=true`
- `load_map_response_from_yaml.response_status=success_equivalent_map_read_completed_before_failure`

这表示 runtime log 已证明 `Read map ...`、`Server map_server connected with bond`、
`Server amcl connected with bond` 和 `Managed nodes are active` 同窗出现，16:55 的
`/map_server active=false` 上游 blocker 已被越过。但如果 artifact closeout 仍为
`managed_runtime_graph_probe_timeout_after_lifecycle_active_log`，它只说明 graph/downstream
readback 未 clean：`/scan_no_publisher`、`/map_once_not_observed`、`/amcl_pose_topic_missing` 或
`/tf_topic_missing` 仍会阻塞 path gate。该证据仍固定保持 strict no-motion，不能声明
route execution、HIL、delivery 或 safe-to-control。

`2026-07-12 18:56` 起，helper 对这类 artifact 的处理顺序改为：如果 managed runtime log 已经
`clean=true` 证明 `/map_server` 与 `/amcl` lifecycle active，即使
`managed_runtime_wait_result.reason` 仍是 `ros2_node_list_timeout`、`ros2_node_list_failed` 等
graph wait blocker，也不能再整体跳过下游只读 readback。helper 会继续在 strict no-motion
边界内读取 `/scan`、`/map`、`/amcl_pose`、`/tf` / `/tf_static` 与 AMCL/TF fallback summary；
如果读到了更具体 blocker，`proof.artifact_closeout.primary_root_cause` 应优先落到这些 topic/TF
gate，并把 `managed_runtime_graph_probe_timeout_after_lifecycle_active_log` 保留为 secondary
diagnostic。所有 motion/control 字段仍必须保持 false。

同一轮还要读取 `transition_sequence.configure.map_server_callback_entered` 与
`map_server_configure_callback_log_observed`。如果 lifecycle manager 已记录
`Configuring map_server` 和 `Failed to change state for node: map_server`，但没有出现
`[map_server]: Configuring`、yaml load、image load 或 `Read map`，主分类应为
`map_server_changestate_response_failure_before_configure_callback_log`。这表示 failure 已在
map_server `on_configure` 日志可见前发生，下一步应查 lifecycle manager ChangeState future/response、
service discovery 和 map_server executor/callback dispatch 顺序；仍不能转成运动或 planner 证据。

`2026-07-12 21:57` Gate 2 返工后，Algorithm path proof 的读取规则更新为：当
`--reuse-existing-lidar-lifecycle` 与 `--managed-lidar-serial-baudrate 150000` 同时出现时，helper
必须复用既有 `/dev/ttyACM0` LiDAR holder，artifact 里应看到
`managed_lidar_policy=reuse_existing_lidar_lifecycle_no_driver_start`、
`managed_lidar_driver_started_by_helper=false` 和 `managed_lidar_serial_baudrate=150000`。
若板端 Python action runtime 因 `librcl_action.so` / `_rclpy_pybind11` ImportError 不能创建
ActionClient，helper 允许转入 `ros2 action send_goal` CLI fallback，但 action 类型必须仍是
`nav2_msgs/action/ComputePathToPose`，不得调用 NavigateToPose、controller、BT、`/cmd_vel`、
`/api/base/manual`、WAVE ROVER UART 或 `/dev/ttyS5`。

同轮成功 artifact
`sprints/2026.07.12_21-57_o3_radar_status_baudrate_readback_repair/artifacts/algorithm/live_o10_reuse_existing_lidar_lifecycle_path_proof_after_fallback.raw.json`
显示 `status=nav2_no_motion_path_generation_runtime_observed`、
`path_generation_attempted=true`、`path_generated=true`、`path_point_count=21`、
`path_generation_boundary=explicit_opt_in_compute_path_to_pose_cli_action_no_motion`、
`fallback_used=true`、`fallback_mode=ros2_cli_action_send_goal`。为了避免
`use_start=false` 触发 planner 回查当前 TF 时间窗并产生 extrapolation，helper 在同一 run 已观测
`/amcl_pose` 且 frame 为 `map` 时，会把 `path_goal_request.start_source` 写成
`amcl_pose_observed_for_planner_only_start` 并发送 `use_start=true`。这只证明
`/scan -> /amcl_pose -> map->odom -> ComputePathToPose` 的 planner-only same-run path generation；
`safe_to_control`、`publishes_cmd_vel`、`calls_base_manual`、`uses_base_uart`、
`route_execution_success`、`delivery_success` 和 `hil_pass` 必须继续为 false。

`2026-07-14 23:49` 起，strict no-motion helper 对 dynamic `map->odom` 增加 publisher
attribution 合同。tf2 buffer 中能查到变换、或 `/tf` sample 中仅出现目标 edge，都不足以证明
AMCL 是当前广播源；应同时读取
`proof.tf_readiness_summary.map_to_odom_dynamic` 的以下字段：

- `source_topic=/tf`、`source_class=dynamic`、`dynamic_source_observed=true`；
- `timestamp.parsed=true` 与 `freshness.status=fresh`；
- `publisher_attribution_status=attributed_unique_amcl`；
- `publisher_endpoint.node_full_name=/amcl`、topic type 与 QoS；
- `publisher_endpoint_candidates`，用于保留同窗其他 `/tf` publisher，而不把它们冒充 AMCL。

归因通过 `/amcl` node publisher inventory 与 `/tf` publisher endpoint inventory 的唯一交集建立。
多个 `/tf` publisher 本身不等于歧义；只要唯一 `/amcl` endpoint 与 node graph 一致，仍可 clean。
如果同窗出现多个可匹配的 AMCL endpoint、endpoint inventory 不可读、AMCL node graph 未列出
`/tf`、stamp missing/stale，artifact 必须分别收口为
`ambiguous_multiple_amcl_tf_publisher_endpoints`、
`unavailable_tf_publisher_endpoint_inventory_not_observed`、
`unavailable_amcl_tf_publisher_not_observed_in_node_graph` 或
`map_to_odom_dynamic_timestamp_*`，并保留 candidates/root cause，不能用 tf2 buffer 成功洗白。

source probe 仍是有界 read-only 采集。它会在窗口内等待目标 dynamic `map->odom`，避免先收到
`odom->base_link` 就提前退出；不会调用 planner、NavigateToPose、controller/BT、`/cmd_vel`、
`/api/base/manual`、LiDAR start/stop 或底盘 UART。`/tf_static` 的 `map->odom` 只能记为 static，
不得继承 AMCL publisher attribution 或冒充 dynamic source。

`2026-07-15 00:53` 起，managed localization 的 graph wait 在 sourced rclpy child 失败后使用
`ros2 node list --no-daemon`，避免旧 daemon discovery 把 70 秒窗口全部消耗在重复 timeout。
若两层 graph probe 仍 blocked，但本轮自有 lifecycle manager 日志已经完整记录 map_server/AMCL
active 与 bond，wait 会以 `managed_lifecycle_log_active_graph_probe_blocked` 提前收口，把 graph
timeout 保留为 secondary，并把剩余预算交给 compact TF endpoint probe、final artifact 和自有
process-group cleanup；日志 active 不能替代后续 endpoint/timestamp/freshness 验收。

同一 compact child 现在会只读订阅 `/amcl_pose`，输出 `amcl_pose_sample` 的 count、frame、接收时间
和 header stamp。该订阅不会发布 `/initialpose`，也不会触发 planner 或运动；没有样本时必须保持
`observed=false` 与 timestamp/freshness fail-closed。使用 `--reuse-existing-lidar-lifecycle` 时，
helper 日志里的 managed baudrate 仅是未使用的 requested/reference 参数，`driver_started_by_helper=false`；
current LiDAR 必须以既有 holder/lifecycle 的独立 readback 为准，不能把默认 `230400` 冒充现场值。
managed static TF 可能与既有 `odom->base_link` / `base_link->laser_frame` source 重叠，因此目标
`map->odom` 仍只能接受唯一 AMCL dynamic endpoint，不能从 static 或其他 publisher 推断。

本规则在 `2026-07-15 01:24-01:26` 的真实上位机复验中自然收口：helper `75e5722f...`
两端 SHA 一致，运行 `97.743s` 后 exit `2`（非外层 timeout），pull exit `0`，自有 PGID
`643654` 清理后残留 `0`。map_server/AMCL 均 active，`/scan` 由既有
`/dev/ttyACM0@150000` LiDAR 发布且样本 fresh；`/amcl_pose` 的 AMCL publisher endpoint 与
只读 subscriber 可见，但 sample count 为 `0`。AMCL 日志明确要求设置 initial pose，而本轮
safety scope 禁止发布 `/initialpose`，所以 dynamic `map->odom` 无 current edge/stamp，必须以
`amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope`、
`/amcl_pose_once_not_observed` 和 `map_to_odom_dynamic_source_missing` fail closed。该证据只证明
localization runtime active 与 blocker 收紧，不证明定位 ready、路线执行、HIL、delivery 或
safe-to-control。

`2026-07-15 04:55` controlled initialpose 合同把 `/initialpose` 从“显式 opt-in 后立即发布”
收紧为“全部写前门禁 clean 后，全 helper 最多一次实际 publish”。调用方必须同时显式传
`--initialpose-opt-in --initialpose-canonical-free-cell-opt-in`；helper 会先完成：

- `persisted_pose_audit`：分别记录仓库 config presence、helper 生成参数中的
  `set_initial_pose: false`、current runtime effective AMCL params、startup log 与发布前 live
  `/amcl_pose` / dynamic `map->odom`。仓库 `set_initial_pose: true` 永远不直接等于 live consumed；
  只有 fresh `/amcl_pose` 与 fresh、唯一归因 AMCL 的 dynamic `map->odom` 同窗成立才允许零次发布收口。
- `canonical_initialpose_map_audit`：绑定 YAML/PGM SHA256、尺寸、resolution、origin、mode/threshold，
  选择离图像中心最近且 row/column 可稳定 tie-break 的 free cell，并按 PGM 左上原点到 map
  左下坐标和 origin yaw 旋转换算 `frame_id=map` world pose。non-free、像素数不符、字段缺失、
  world pose 越界或 canonical ranking top 不一致都 fail-closed。
- `pre_initialpose_gate`：要求 map_server/AMCL active、current `/scan` sample/stamp fresh、
  `/initialpose` subscriber 只归属 `/amcl`、无 static `map->odom`、无竞争 dynamic `map->odom`。
  任一失败必须保持 `initialpose_publish_attempts=0`。

rclpy publisher 即使调用方传入大于一的 limit，也会被 helper 钳制为一次。若 rclpy 在 publish 前
import/初始化失败且 attempt 仍为 `0`，才允许一次 CLI `--once` fallback；若 rclpy 已调用过一次
publish，无论 subscriber match 或 post-write 输出如何，都禁止 CLI 重发。发布后只读采集必须得到
fresh `/amcl_pose` 与 `source_class=dynamic`、`publisher_attribution_status=attributed_unique_amcl`、
timestamp parsed/fresh 的 `map->odom`。旧字段值 `attributed_to_amcl_graph_endpoint` 已被更严格的
`attributed_unique_amcl` 取代。

managed runtime cleanup 继续只作用于 helper 以 `start_new_session=True` 创建的 PGID；artifact 必须
记录 expected PID、PGID identity、cleanup signals、remaining processes 与 `residual_count=0`。
该合同不启动 planner/controller/path，不调用 NavigateToPose、`/cmd_vel`、`/api/base/manual`，不打开
UART 或修改 LiDAR/硬件参数。即使 clean，proof boundary 仍为
`robot_runtime_o3_strict_no_motion_controlled_initialpose_localization_proof_only`；不证明真实物理位姿
准确、route execution、delivery、HIL 或 safe-to-control。

`2026-07-15 06:54` 起，dynamic TF freshness 改为 callback receipt-time 合同。`/tf` 与
`/tf_static` 的 rclpy callback 会在入口各取一次 `received_at_ms`，同一 TFMessage 内每条
transform 共享该值；CLI fallback、旧 artifact 或解析文本没有 callback receipt 事实时必须保持
`received_at_ms=null`，禁止使用命令 `finished_at_ms` 或 artifact `generated_at_ms` 回填。

`proof.tf_source_freshness.evaluated_at_ms` 记录 summary 判定时刻；每条 edge 同时输出：

- `header_age_at_receipt_ms = received_at_ms - header_stamp_epoch_ms`：dynamic clean gate 的唯一
  decision age；threshold 继续固定为 `3000ms`。
- `receipt_age_at_evaluation_ms = evaluated_at_ms - received_at_ms`：collector 收到消息后的剩余耗时，
  只作诊断，不能追加到 stale gate。
- `header_age_at_evaluation_ms = evaluated_at_ms - header_stamp_epoch_ms`：保留旧口径作兼容审计，
  但不再作为 dynamic freshness decision。

既有 `freshness.age_ms` 继续保留给旧 reader，但 dynamic edge 上它现在严格等于
`header_age_at_receipt_ms`，并以 `decision_basis=header_age_at_receipt_ms` 明示口径。因此 header 在
receipt 时不超过 `3000ms`，即使 collector 后续又运行数秒，仍可判为 fresh；header 到达 callback
时已经超过 `3000ms` 则仍为 stale。缺失/非法 receipt、header stamp 不可解析、非墙钟时间，或
header/receipt/evaluation 出现超出小量取整容差的逆序，都必须 `unknown` / fail-closed。

`/tf_static` 仍保持 latched/static source 语义，不把 zero/static stamp 套入 dynamic age gate；
source class、`timestamp` 和 unique AMCL publisher attribution 均保持原合同。该修复只是
read-only、no-topic-write、no-motion 的 freshness 证据语义，不授权 `/initialpose`、managed runtime
start/stop、planner/controller/path、NavigateToPose、`/cmd_vel`、`/api/base/manual`、UART 或运动，
也不证明定位 ground truth、route execution、delivery、HIL 或 safe-to-control。

`2026-07-15 08:12-08:14` 的真实上位机 capture 首次把该 receipt-time 合同带入 fresh
managed localization-only 窗口。local/remote helper SHA 均为
`78fd2e88aa6e272db52a45db8d8f5eef07108a4a010e73c50119bb23c18ca368`，final live run count 固定为
`1`；命令只包含 `--strict-no-motion --no-base-uart --managed-runtime-opt-in`、既有 LiDAR lifecycle
复用和 `/dev/ttyACM0@150000` 的当前现场参数，不包含 `--initialpose-opt-in` 或
`--path-generation-opt-in`。helper 只启动 map_server、AMCL、lifecycle manager 与必要 static TF，
没有启动 planner/controller。

artifact `sprints/2026.07.15_08-06_o3_live_tf_receipt_capture/artifacts/algorithm/runtime-proof.json`
自然 exit `2`，但证明 map_server/AMCL active、`/scan` fresh（`age_ms=21`），并让本轮 `/tf` /
`/tf_static` inventory 的 `3/3` transforms 都带整数 `received_at_ms`。观测到的 dynamic
`odom->base_link` 可复算：

- `1784074406732 - 1784074406726 = header_age_at_receipt_ms=6`；
- `1784074446409 - 1784074406732 = receipt_age_at_evaluation_ms=39677`；
- `1784074446409 - 1784074406726 = header_age_at_evaluation_ms=39683`。

decision 仍以 `header_age_at_receipt_ms` 对 `3000ms` threshold 判为 fresh；约 39.7 秒的 collector
后续耗时没有被错误追加到 freshness gate。目标 dynamic `map->odom` 在未发布 `/initialpose` 的本轮
没有出现，因此其 receipt/三类 age 均保持 `null`，exact blocker 为
`amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope` 与
`map_to_odom_dynamic_source_missing`，不能用相邻 `odom->base_link` edge 洗白。

本轮 `initialpose_publish_attempts=0`，path generation、UART、`/cmd_vel`、`/api/base/manual`、route、
delivery 与 HIL 全部为 false。helper-owned PGID identity 已核对，cleanup residual=`0`，post inventory
也没有 map_server/AMCL/lifecycle/static-TF/helper 残留。proof boundary 是
`live_strict_no_motion_localization_receipt_artifact_blocked_missing_map_to_odom`：它是 current-run live
sensor/localization artifact，不是定位 ready、route execution、delivery、HIL、safe-to-control 或
Mission Objective 0 完成证明。
