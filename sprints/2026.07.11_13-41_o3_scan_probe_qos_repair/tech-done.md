# O3 Scan Probe QoS Repair Tech Done

## sprint_type

`sprint_type: epic`

## 自主能力目标和本轮抓手

- 目标：把 O10 helper 的 `/scan` once probe 从单条布尔诊断升级为可复核的多尝试 QoS 诊断，优先确认 sensor-data 读法是否可行。
- 抓手：新增 `rclpy_sensor_data_once -> cli_sensor_data_echo_once -> cli_default_echo_once` 三段式 probe，并把 attempt/source/qos/timeout/error 全部落入 artifact。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `/scan` 多尝试 probe。
  - 新增 `attempts[]`、`best_attempt`、`qos_probe_boundary`、`source` artifact 字段。
  - 修正 endpoint inventory 缺失时的 root-cause 归因，避免默认 `publisher_count=0` 被误写成真实 `no_publishers`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 JSON stamp 解析、scan probe 优先级、endpoint inventory 缺失保护等测试。
  - 更新 `/scan` root-cause 断言，覆盖 sensor-data timeout 和 rclpy import fail 两条分支。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 `/scan` 多尝试 probe contract 与 live artifact 解读。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 fixed-route/no-motion 收口时对 `attempts[]`、`best_attempt`、`qos_probe_boundary` 的阅读顺序。
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/local_o10_scan_qos_repair.raw.json`
- `sprints/2026.07.11_13-41_o3_scan_probe_qos_repair/artifacts/live_o10_scan_qos_repair.raw.json`

## 接口影响

- additive only：
  - `proof.localization_signal_freshness["/scan"].probe.attempts[]`
  - `proof.localization_signal_freshness["/scan"].probe.best_attempt`
  - `proof.localization_signal_freshness["/scan"].probe.qos_probe_boundary`
  - `proof.localization_signal_freshness["/scan"].probe.source`
  - `proof.localization_signal_freshness["/scan"].endpoint_inventory_observed`
- safety fields 继续保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`

## 验证结果

### 本地

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

本地仍是预期 fail-closed：Mac 无 `/opt/ros/humble/setup.bash`，但 artifact 成功落盘，`/scan.probe.qos_probe_boundary=scan_probe_skipped_without_ros2`。

### 真实板

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

## Live Artifact 关键字段

`artifacts/live_o10_scan_qos_repair.raw.json` 关键输出：

```text
status=blocked_with_root_cause
/scan.topic_type=sensor_msgs/msg/LaserScan
/scan.probe.boundary=rclpy_scan_once_failed
/scan.probe.qos_probe_boundary=scan_probe_attempt_failed
/scan.probe.best_attempt.source=rclpy_subscription
/scan.probe.best_attempt.error.type=ImportError
/scan.probe.attempts[0].label=rclpy_sensor_data_once
/scan.probe.attempts[1].label=cli_sensor_data_echo_once
/scan.probe.attempts[2].label=cli_default_echo_once
/scan.probe.attempts[*].timed_out=[false,true,true]
/amcl_pose.probe.boundary=/amcl_pose_probe_not_observed
root_causes=/scan_rclpy_probe_failed,/amcl_pose_probe_timeout,map_to_odom_dynamic_source_missing,map_to_base_link_blocked_by_missing_map_to_odom,localization_not_ready_for_path_generation
safe_to_control=false
robot_control_executed=false
delivery_success=false
hil_pass=false
path_generated=false
```

补充观察：

- `/scan` 已明确不是“topic 名字不存在”；topic type 可见。
- 第一条 `rclpy` sensor-data 尝试直接命中板端 Python/ROS 共享库导入失败：
  `librcl_action.so` / `_rclpy_pybind11`。
- 两条 CLI `/scan` echo 都超时，说明仅靠 CLI 也没在窗口内读到一帧。
- `/amcl_pose` 仍未观测到，`map->odom` 仍无 dynamic source，path generation 继续 fail-closed。

## Proof Boundary

- `software_proof_real_board_scan_probe_qos_diagnostics_only`
- `blocked_scan_rclpy_probe_failed`
- `blocked_amcl_pose_probe_timeout`
- `blocked_map_to_odom_dynamic_source_missing`

本轮不证明：

- `map_to_odom=true`
- `map_to_base_link=true`
- same-run path generation success
- live route execution success
- safe-to-control
- HIL pass
- delivery success

## 剩余风险

- 板端 `rclpy`/ROS Python 运行时存在共享库导入缺口，当前直接阻断了更稳的 in-process sensor-data probe。
- `/scan` 的两条 CLI echo 都超时，说明即便绕开 rclpy，LiDAR 发布连续性、DDS QoS 或 topic 消费窗口仍未被证明可用。
- `/amcl_pose` 仍 timeout，`/tf` source inventory 继续失败，AMCL 的 `map->odom` dynamic broadcast 还没有现场证据。
- managed runtime cleanup 仍伴随 Nav2/shutdown 噪声日志，但本轮没有触发任何运动控制，所有安全字段继续保守 false。

## 下一步建议

1. 先修板端 `rclpy` 依赖缺口，使 `rclpy_sensor_data_once` 能真实订阅 `/scan`。
2. 在 `rclpy` 修复后复跑同一 helper，比较 `rclpy_sensor_data_once` 与 `cli_sensor_data_echo_once` 的差异。
3. 只有 `/scan` 真正 observed 后，再继续压 `/amcl_pose` 与 `map->odom` dynamic source blocker。
