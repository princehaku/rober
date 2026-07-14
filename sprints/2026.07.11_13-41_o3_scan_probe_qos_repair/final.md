# O3 Scan Probe QoS Repair Final

## 复盘结论

本轮 `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/` 完成 epic sprint 收口。O5 仍是当前最低主 Objective，约 `~85%`，但最近 O5 external evidence lane 已 fail-closed，继续 O5 readiness / wrapper / support-only 工作不会产生主 OKR 增量。因此本轮继续现场 O3 lane，按上一轮建议优先压 `/scan` probe 诊断深度，再复验 `/amcl_pose` 与 AMCL dynamic `map->odom`。

结果是有效诊断推进，但仍 fail-closed。Algorithm owner 已把 `/scan` probe 升级为三段式尝试：`rclpy_sensor_data_once -> cli_sensor_data_echo_once -> cli_default_echo_once`。真实板 artifact 证明当前并不是“topic 不存在”，而是 `/scan.topic_type=sensor_msgs/msg/LaserScan` 已可见，但最佳尝试 `rclpy_sensor_data_once` 因 `ImportError`（`librcl_action.so` / `_rclpy_pybind11`）失败，两条 CLI `/scan` echo 都 timeout；`/amcl_pose` 仍未观测到，`map->odom` dynamic source 仍缺失，最终仍 `path_generated=false`。

## 实际改动

Algorithm owner 修改或新增：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/tech-done.md`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/local_o10_scan_qos_repair.raw.json`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json`

Product 同步新增或更新：

- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/side2side_check.md`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/final.md`
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
Ran 51 tests in 2.203s
OK
```

```text
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --output sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/local_o10_scan_qos_repair.raw.json
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
ssh -p 37878 root@192.168.1.11 'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' > sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json
exit 0
```

## Live Artifact 结论

`artifacts/live_o10_scan_qos_repair.raw.json` 输出：

```text
status=blocked_with_root_cause
/scan.topic_type=sensor_msgs/msg/LaserScan
/scan.probe.boundary=rclpy_scan_once_failed
/scan.probe.qos_probe_boundary=scan_probe_attempt_failed
/scan.probe.best_attempt.label=rclpy_sensor_data_once
/scan.probe.best_attempt.source=rclpy_subscription
/scan.probe.best_attempt.error.type=ImportError
/scan.probe.attempts[0].label=rclpy_sensor_data_once
/scan.probe.attempts[1].label=cli_sensor_data_echo_once
/scan.probe.attempts[2].label=cli_default_echo_once
/scan.probe.attempts[*].timed_out=[false,true,true]
/amcl_pose.probe.boundary=/amcl_pose_probe_not_observed
map_to_odom=false
path_generated=false
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
```

最终 root causes：

```text
/scan_rclpy_probe_failed
/amcl_pose_probe_timeout
map_to_odom_dynamic_source_missing
map_to_base_link_blocked_by_missing_map_to_odom
localization_not_ready_for_path_generation
```

## OKR 结论

- O5：保持约 `~85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic 或真实 phone/browser evidence。
- O1/O6/O7：保持约 `~93%`。本轮没有 current live HIL、`map_to_odom=true`、same-run path success、route/material 新增、delivery record、operator acceptance 或 production readback。
- 现场 O3 lane：新增 scan probe QoS / rclpy 依赖分层证据，但仍没有 path/material success。
- KR：本轮不归档 KR，不调整任何 Objective 百分比。

## Proof Boundary

本轮 proof boundary：

- `software_proof_real_board_scan_probe_qos_diagnostics_only`
- `blocked_scan_rclpy_probe_failed`
- `blocked_amcl_pose_probe_timeout`
- `blocked_map_to_odom_dynamic_source_missing`

本轮不证明：

- `scan_once_observed=true`
- `amcl_pose_observed=true`
- `map_to_odom=true`
- `map_to_base_link=true`
- same-run path generation success
- live route execution success
- safe-to-control
- HIL pass
- delivery success
- production cloud / DB / queue / OSS / CDN / phone/browser external proof

## 剩余风险

- 板端 `rclpy` / ROS Python 共享库导入缺口当前直接阻断了更稳的 in-process `/scan` sensor-data probe。
- 即便绕开 `rclpy`，两条 CLI `/scan` echo 仍 timeout，说明 LiDAR 连续发布、DDS QoS 或消费窗口仍未被当前证据证明可用。
- `/amcl_pose` 继续 timeout，`map->odom` dynamic source 仍未出现；当前不能把 topic type 可见误写成 localization ready。
- 本轮没有任何运动执行，必须继续保持 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

## 下一轮建议

下一轮仍优先现场 O3 lane，但先修板端 `rclpy` 依赖和 `/scan` 连续读帧，再压 `/amcl_pose` 与 `map->odom`。在拿到 `scan observed`、`amcl_pose observed`、`map_to_odom=true`、same-run path 或新路线材料之前，O6/O7 消费链继续冻结，O5 仍只在真实 external production evidence 到位时恢复主线推进。
