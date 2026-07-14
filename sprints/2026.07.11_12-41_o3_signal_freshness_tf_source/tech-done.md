# O3 Signal Freshness TF Source Tech Done

## sprint_type

`sprint_type: epic`

## 自主能力目标和本轮抓手

本轮目标是把 O3 real-board no-motion localization blocker 从泛化的
`map_to_odom_not_observed` 继续下钻到 signal freshness / TF source 分层事实，服务 O1
same-run path generation 和后续 O6/O7 material consumption。

实际抓手：

- 在 O10 helper artifact 中新增 `proof.localization_signal_freshness`，覆盖 `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static`。
- 新增 `proof.tf_source_freshness`，按 `map_to_odom`、`odom_to_base_link`、`base_link_to_laser_frame` 记录 dynamic/static source。
- root cause 优先使用 signal probe timeout、topic presence、TF source edge 缺口等新事实。
- 全程保持 no-motion safety flags 为 false。

## 实际改动文件

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/local_o10_signal_freshness.raw.json`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/tech-done.md`

## 接口影响

O10 helper JSON 为向后兼容的 additive fields：

- `proof.localization_signal_freshness.<topic>.topic_type`
- `proof.localization_signal_freshness.<topic>.probe.executed/observed/elapsed_ms/timeout_s/timed_out`
- `proof.localization_signal_freshness.<topic>.timestamp`
- `proof.localization_signal_freshness.<topic>.freshness`
- `proof.tf_source_freshness.edges.<edge>.source_class/source_topic/dynamic_source_observed/static_source_observed`

未改变 public safety 语义。输出继续固定：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

## 实现内容

- `run_ros` 结果新增 `started_at_ms`、`finished_at_ms`、`timeout_s`、`timed_out`，用于 artifact 直接记录 probe timing。
- rclpy graph probe 新增 targeted topic endpoint 摘要，限定在 `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static`。
- 新增 ROS header stamp 解析与 freshness 判断：墙钟 stamp 用 `3000ms` 阈值判断 fresh/stale；zero/sim-time-like stamp 标为 `unknown`；static TF 不按 age gate。
- 新增 `/odom` once probe；`/scan` 和 `/amcl_pose` timeout 不再被泛化为成功或只写旧 root cause。
- root cause 现在优先输出 `/scan_probe_timeout`、`/amcl_pose_probe_timeout`、`map_to_odom_dynamic_source_missing` 等分层原因。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
# exit 0
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
# Ran 47 tests in 2.185s
# OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/local_o10_signal_freshness.raw.json
# exit 2
# status=blocked_with_root_cause
# root_causes=map_lifecycle_latest_missing, ros2_command_unavailable_after_bash_source
```

本地 run 的 `exit 2` 是预期 fail-closed：当前 Mac 环境没有 `/opt/ros/humble/setup.bash`，只能生成 local software proof blocker artifact。

真实板 SSH 可达，已执行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
# exit 0
```

```bash
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
# exit 2
# status=blocked_with_root_cause
```

```bash
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json
# exit 0
```

live artifact 关键结果：

- `status=blocked_with_root_cause`
- `root_causes=/scan_probe_timeout,/amcl_pose_probe_timeout,map_to_odom_dynamic_source_missing,map_to_base_link_blocked_by_missing_map_to_odom,localization_not_ready_for_path_generation`
- `/scan.topic_type=sensor_msgs/msg/LaserScan`
- `/scan.probe.timed_out=true`
- `/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped`
- `/amcl_pose.probe.timed_out=true`
- `/odom.topic_type=nav_msgs/msg/Odometry`
- `/odom.freshness.status=fresh`
- `localization_tf_observed.map_to_odom=false`
- `path_generated=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

## 失败定位

本轮没有拿到 path proof。失败位置比上一轮更细：

- `/scan` topic type 可见，但 once probe 在 8s 窗口内未收到消息。
- `/amcl_pose` topic type 可见，但 post-initialpose once probe 在 10s 窗口内未收到消息。
- `/odom` 可观测且 fresh，说明底层 odom signal 不再是本轮主 blocker。
- `map_to_odom` dynamic source 未观测，`map_to_base_link` 仍被 missing `map_to_odom` 阻塞。
- rclpy source inventory 在板端裸 Python 进程中仍命中 ROS shared library import 问题，因此 `/tf`/`/tf_static` topic type 可见，但 dynamic/static edge source inventory 未能用 rclpy 采到。

## 剩余风险和下一步

- 本轮是更细的 fail-closed root cause，不是 OKR 计分型 path/material success。
- 下一轮优先修 `/scan` once probe timeout：确认 LiDAR driver 当前是否持续发布 LaserScan、QoS 是否与 CLI echo 匹配、managed runtime 是否在 probe 窗口内稳定保活。
- 然后修 AMCL 输出：在 `/scan` 可稳定读到后，再验证 `/amcl_pose` 是否产生，以及 AMCL 是否广播 dynamic `map->odom`。
- 若继续依赖 rclpy source inventory，需要处理板端裸 Python rclpy shared library import 环境，或增加更轻的 CLI source inventory fallback。

## 本轮结论

本轮没有拿到 `map_to_odom=true`，也没有拿到 `path_generated=true`。产出的是更细的 real-board no-motion fail-closed root cause：`/scan` 与 `/amcl_pose` 是 timeout，`/odom` fresh，`map_to_odom` dynamic source missing。
