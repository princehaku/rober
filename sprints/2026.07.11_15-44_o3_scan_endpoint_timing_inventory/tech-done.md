# O3 Scan Endpoint Timing Inventory Tech Done

## sprint_type

`sprint_type: epic`

## 自主能力目标和本轮抓手

本轮目标是把上一轮 `/scan_rclpy_child_timeout_after_import` 继续拆成 `/scan` publisher、endpoint QoS、child sample timing 和稳定 root-cause classification。抓手是 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 的 no-motion helper，不执行 `/cmd_vel`、底盘 UART、NavigateToPose 或路线执行。

本轮证据边界为 `software_proof_o3_scan_endpoint_timing_inventory_only` / live no-motion supporting evidence；不证明 `safe_to_control`、HIL、route execution 或 delivery success。

## 实际改动文件

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `/scan` child rclpy probe 新增 `child_runtime`、`endpoint_inventory`、`sample_timing`、`requested_qos_profile`。
  - `endpoint_info_to_artifact` 新增最小 QoS profile 摘要。
  - `localization_signal_freshness["/scan"]` 新增 `publisher_inventory`、`endpoint_inventory`、`sample_timing`、`managed_runtime_scan_status`、`probe.classification`。
  - root cause 优先读取 `/scan` 稳定分类，覆盖 `/scan_no_publisher`、`/scan_lidar_runtime_not_started`、`/scan_publisher_visible_but_no_sample`、`/scan_qos_or_window_timeout`、`/scan_rclpy_child_timeout_after_import`、`/scan_sample_observed`。
  - safety flags additive 增加 `route_execution_success=false`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 单测覆盖 6 个 `/scan` classification。
  - 单测覆盖 endpoint QoS、sample timing、child runtime shape。
  - 单测覆盖主进程 rclpy graph 失败时优先消费 child endpoint inventory。
- `docs/navigation/field_route_evidence_preflight.md`
  - 新增 15:44 artifact 读取顺序和证据边界。
- `docs/navigation/fixed_route_workflow.md`
  - 新增 fixed-route/no-motion 现场读取顺序：publisher inventory -> endpoint QoS -> sample timing -> classification -> AMCL/TF/path。
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/local_o10_scan_endpoint_timing_inventory.raw.json`
- `sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json`

## 接口影响

所有 JSON 变化都是 additive/backward-compatible。旧字段如 `publishers`、`subscribers`、`probe.attempts`、`probe.best_attempt`、`root_causes`、`path_generated` 保留。

新增字段集中在：

- `proof.localization_signal_freshness["/scan"].publisher_inventory`
- `proof.localization_signal_freshness["/scan"].endpoint_inventory`
- `proof.localization_signal_freshness["/scan"].sample_timing`
- `proof.localization_signal_freshness["/scan"].managed_runtime_scan_status`
- `proof.localization_signal_freshness["/scan"].probe.classification`
- `proof.localization_signal_freshness["/scan"].probe.child_runtime`
- `proof.localization_signal_freshness["/scan"].probe.requested_qos_profile`

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- exit `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- exit `0`
- `Ran 58 tests in 2.192s`
- `OK`

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/local_o10_scan_endpoint_timing_inventory.raw.json
```

- exit `2`
- 本地 Mac 无 `/opt/ros/humble/setup.bash`，按预期 fail-closed。
- local artifact：`status=blocked_with_root_cause`，root causes 为 `map_lifecycle_latest_missing`、`ros2_command_unavailable_after_bash_source`。
- local `/scan.probe.classification=/scan_no_publisher`，`path_generated=false`，所有 safety fields false。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- exit `0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

- exit `2`
- 真实板 no-motion helper fail-closed 并写出 `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json
```

- exit `0`

```bash
rg -n "publisher_inventory|endpoint_inventory|sample_timing|/scan|classification|safe_to_control=false|delivery_success=false|path_generated|map_to_odom" \
  sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- exit `0`
- 输出命中新字段、live/local artifact、文档和 helper；输出较长，终端侧截断但命令成功。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory
```

- exit `0`

## Live artifact 关键字段

Artifact：`sprints/2026.07.11_15-44_o3_scan_endpoint_timing_inventory/artifacts/live_o10_scan_endpoint_timing_inventory.raw.json`

`/scan` 关键字段：

- `publisher_inventory.topic_visible=true`
- `publisher_inventory.inventory_observed=true`
- `publisher_inventory.publisher_count=1`
- `publisher_inventory.publisher_nodes[0].node_name=lidar_driver`
- `endpoint_inventory.publisher_count=1`
- `endpoint_inventory.subscriber_count=2`
- publisher QoS：`reliability=RELIABLE`、`durability=VOLATILE`
- requested QoS：`reliability=BEST_EFFORT`、`durability=VOLATILE`、`history=KEEP_LAST`、`depth=5`
- `sample_timing.probe_window_sec=2.2`
- `sample_timing.sample_wait_started_at_ms=1783757366911`
- `sample_timing.timeout_boundary_ms=1783757369111`
- `sample_timing.sample_wait_finished_at_ms=1783757369160`
- `sample_timing.sample_count=0`
- `sample_timing.first_sample_latency_ms=null`
- `probe.child_runtime.import_ok=true`
- `probe.child_runtime.node_created=true`
- `probe.child_runtime.subscription_created=true`
- `probe.child_runtime.sample_wait_started=true`
- `probe.classification=/scan_qos_or_window_timeout`

Localization/path 关键字段：

- `proof.amcl_pose_observed=false`
- `proof.localization_tf_observed.map_to_odom=false`
- `proof.localization_tf_observed.map_to_base_link=false`
- `proof.path_generated=false`
- `proof.path_point_count=0`

Safety fields：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `route_execution_success=false`
- `hil_pass=false`

## 失败定位

本轮已证明旧的 `/scan_rclpy_child_timeout_after_import` 不再足够精确。最新 live root cause 为：

- `/scan_qos_or_window_timeout`
- `/amcl_pose_probe_timeout`
- `map_to_odom_dynamic_source_missing`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `localization_not_ready_for_path_generation`

更具体地说：`/scan` topic 和 `lidar_driver` publisher 可见，publisher QoS 为 `RELIABLE`，helper child subscriber 已创建并按 `BEST_EFFORT` 等待 2.2s，但 sample_count 仍为 0；两条 CLI fallback 也 timeout。因此下一轮不应再修旧 main-process rclpy ImportError，而应优先处理 LiDAR publisher sample delivery、QoS/window 或 DDS endpoint timing。

## 剩余风险

- 本轮没有拿到 `/scan_sample_observed`。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false` 仍阻塞 same-run path generation。
- AMCL rclpy param/source probe 仍有 `librcl_action.so` / `_rclpy_pybind11` import failure；本轮只把 `/scan` endpoint inventory 挪进 sourced child probe，未修 AMCL graph probe。
- 本轮没有 route CSV、keyframe、rosbag、Nav2 result、delivery record 或 operator confirmation，不调整 O1/O5/O6/O7 百分比，不归档 KR。
- 本轮没有执行真实运动控制、HIL 或 delivery；所有 safety fields 必须继续 false。

## 下一条现场执行命令

优先复跑更长 `/scan` window，并保留 endpoint inventory 对比：

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

如果仍是 `publisher_count=1` 且 `sample_count=0`，下一轮应把 `/scan` child probe 增加 publisher RELIABLE 订阅尝试或延长 child wait，并同时保留当前 BEST_EFFORT probe，确认是否是 QoS/window 还是 LiDAR driver 只注册 endpoint 不发样本。
