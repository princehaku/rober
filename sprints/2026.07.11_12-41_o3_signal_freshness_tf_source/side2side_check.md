# O3 Signal Freshness TF Source Side2Side Check

## 验收结论

本轮验收通过，但结论是 fail-closed diagnostic improvement，不是 path proof。

Algorithm owner 已按 `tech-plan.md` 在 O10 helper 中新增 `proof.localization_signal_freshness` 与 `proof.tf_source_freshness`，并把 root cause 从上一轮泛化的 `/scan_once_not_observed`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed` 进一步拆成：

- `/scan` topic type 可见，但 once probe timeout；
- `/amcl_pose` topic type 可见，但 once probe timeout；
- `/odom` topic type 可见且 freshness 为 fresh；
- `/tf` 与 `/tf_static` topic type 可见；
- rclpy source inventory 未拿到 dynamic/static edge source；
- `map_to_odom=false`、`path_generated=false`。

## 与 PRD 对照

| PRD 要求 | 验收结果 |
| --- | --- |
| `/scan`、`/amcl_pose`、`/odom`、`/tf`、`/tf_static` freshness 摘要 | 通过，live artifact 已包含 `proof.localization_signal_freshness` |
| dynamic/static TF source 分层 | 部分通过，字段已落地；live artifact 显示 source inventory 未取到 edge，因此 fail-closed |
| root cause 优先使用新事实 | 通过，输出 `/scan_probe_timeout`、`/amcl_pose_probe_timeout`、`map_to_odom_dynamic_source_missing` |
| no-motion safety flags 固定 false | 通过，`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false` |
| 真实板 artifact | 通过，`artifacts/live_o10_signal_freshness.raw.json` 已落盘 |

## 验证证据核对

Algorithm owner 已运行：

```text
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
Ran 47 tests in 2.185s
OK
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/local_o10_signal_freshness.raw.json
exit 2, expected local fail-closed because Mac lacks /opt/ros/humble/setup.bash
```

```text
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
exit 2, status=blocked_with_root_cause
```

```text
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_12-41_o3_signal_freshness_tf_source
通过
```

## Live Artifact 摘要

`artifacts/live_o10_signal_freshness.raw.json`：

```text
status=blocked_with_root_cause
map_to_odom=false
path_generated=false
/scan.topic_type=sensor_msgs/msg/LaserScan
/scan.probe.timed_out=true
/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped
/amcl_pose.probe.timed_out=true
/odom.topic_type=nav_msgs/msg/Odometry
/odom.freshness.status=fresh
root_causes=[
  /scan_probe_timeout,
  /amcl_pose_probe_timeout,
  map_to_odom_dynamic_source_missing,
  map_to_base_link_blocked_by_missing_map_to_odom,
  localization_not_ready_for_path_generation
]
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

## OKR 判定

- O5 仍是最低 Objective，约 `85%`，但本轮没有真实 production external evidence，O5 不调整。
- O1/O6/O7 维持约 `93%`，因为本轮没有 `map_to_odom=true`、same-run path、route execution、delivery record、operator acceptance、production readback 或 HIL pass。
- 本轮不归档 KR，不调整任何 Objective 百分比。

## 下一轮建议

下一轮继续 O3 real-board no-motion lane，但不要再追泛化 path proof。先修 `/scan` once probe timeout：确认 LiDAR driver 是否持续发布、QoS 是否匹配 CLI echo、managed runtime 是否在 probe 窗口内稳定保活。`/scan` 稳定后再复验 `/amcl_pose` 与 AMCL dynamic `map->odom`。
