# O3 Signal Freshness TF Source Final

## 复盘结论

本轮 `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/` 完成 epic sprint 收口。O5 仍是当前最低主 Objective，约 `~85%`，但最近 O5 external evidence lane 已 fail-closed，继续 O5 readiness / wrapper / support-only 工作不会产生主 OKR 增量。因此本轮继续现场 O3 lane，按上一轮建议把 `/scan`、`/amcl_pose`、`/odom`、`/tf` 和 `/tf_static` 的单条 probe freshness 与 dynamic/static TF source 分层落盘。

结果是有效诊断推进，但仍 fail-closed。Algorithm owner 已新增 `proof.localization_signal_freshness` 与 `proof.tf_source_freshness`，真实板 artifact 证明当前不是单纯“看不到 topic”：`/scan` 与 `/amcl_pose` 的 topic type 可见但 once probe timeout，`/odom` 可见且 fresh，`/tf` 与 `/tf_static` topic type 可见但 source inventory 未取到 dynamic/static edge。最终仍 `map_to_odom=false`、`path_generated=false`。

## 实际改动

Algorithm owner 修改或新增：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/tech-done.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/local_o10_signal_freshness.raw.json`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json`

主节点新增：

- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/pre_start.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/prd.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/tech-plan.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/side2side_check.md`
- `sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/final.md`

Product 同步更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证证据

子 agent 已交付验证：

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
exit 2
status=blocked_with_root_cause
root_causes=map_lifecycle_latest_missing, ros2_command_unavailable_after_bash_source
```

本地 `exit 2` 是预期 fail-closed：当前 Mac 没有 `/opt/ros/humble/setup.bash`，不能证明 ROS live runtime。

真实板验证：

```text
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
exit 0
```

```text
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
exit 2
status=blocked_with_root_cause
```

```text
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_12-41_o3_signal_freshness_tf_source/artifacts/live_o10_signal_freshness.raw.json
exit 0
```

Diff hygiene：

```text
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_12-41_o3_signal_freshness_tf_source
通过
```

## Live Artifact 结论

`artifacts/live_o10_signal_freshness.raw.json` 输出：

```text
status=blocked_with_root_cause
/scan.topic_type=sensor_msgs/msg/LaserScan
/scan.probe.timed_out=true
/amcl_pose.topic_type=geometry_msgs/msg/PoseWithCovarianceStamped
/amcl_pose.probe.timed_out=true
/odom.topic_type=nav_msgs/msg/Odometry
/odom.freshness.status=fresh
/tf.topic_type=tf2_msgs/msg/TFMessage
/tf_static.topic_type=tf2_msgs/msg/TFMessage
map_to_odom=false
path_generated=false
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

最终 root causes：

```text
/scan_probe_timeout
/amcl_pose_probe_timeout
map_to_odom_dynamic_source_missing
map_to_base_link_blocked_by_missing_map_to_odom
localization_not_ready_for_path_generation
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、`map_to_odom=true`、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 signal freshness / TF source 分层证据，但仍没有 path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_signal_freshness_tf_source_only`
- `blocked_scan_amcl_pose_probe_timeout`
- `blocked_map_to_odom_dynamic_source_missing`

本轮不证明：

- `map_to_odom=true`
- `map_to_base_link=true`
- same-run path generation success
- live route execution success
- safe-to-control
- HIL pass
- delivery success
- production cloud / DB / queue / OSS / CDN / phone/browser external proof

## 剩余风险

- `/scan` 与 `/amcl_pose` topic type 可见但 once probe timeout，仍需确认 LiDAR driver 发布连续性、QoS 和 managed runtime 保活窗口。
- `/odom` fresh 只说明 odom signal 本轮可读，不等于底盘运动或 HIL pass。
- rclpy source inventory 在板端仍未拿到 dynamic/static edge source，可能需要修板端 Python/rclpy shared library 环境，或增加 CLI source inventory fallback。
- 当前没有任何运动执行，必须继续保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## 下一轮建议

下一轮继续现场 O3 lane，优先修 `/scan` once probe timeout。只有 `/scan` 可稳定读到后，再复验 `/amcl_pose` 和 AMCL dynamic `map->odom`。在拿到 `map_to_odom=true`、same-run path 或新路线材料之前，O6/O7 消费链继续冻结，O5 仍只在真实 external production evidence 到位时恢复主线推进。
