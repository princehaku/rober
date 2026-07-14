# O3 Scan Probe QoS Repair Side2Side Check

## 验收结论

本轮验收通过，但结论仍是 fail-closed diagnostic improvement，不是 path proof，也不是 material success。

Algorithm owner 已按 `tech-plan.md` 把 `/scan` probe 从单次 CLI 尝试升级为 `rclpy_sensor_data_once -> cli_sensor_data_echo_once -> cli_default_echo_once` 三段式诊断，并把 attempt、source、timeout、error 与 best-attempt 摘要落入真实板 artifact。现场结论从上一轮的泛化 `/scan_probe_timeout` 进一步下钻为：

- `/scan.topic_type=sensor_msgs/msg/LaserScan`，topic type 可见；
- `best_attempt.label=rclpy_sensor_data_once`，但板端因 `ImportError` 失败；
- 两条 CLI `/scan` echo 均 timeout，当前窗口内仍未证明能稳定读到一帧；
- `/amcl_pose` 继续 timeout；
- `map->odom` dynamic source 仍缺失，`path_generated=false`。

## 与 PRD 对照

| PRD 要求 | 验收结果 |
| --- | --- |
| `/scan` probe 要比上一轮更具体，区分 QoS/CLI 尝试 | 通过，live artifact 已落 `attempts[]`、`best_attempt`、`qos_probe_boundary` |
| 真实板 artifact 必须结构化给出 root causes | 通过，已落 `artifacts/live_o10_scan_qos_repair.raw.json` |
| 若 `/scan` 仍不可读，要给出比 timeout 更可操作的 blocker | 通过，已下钻到 `/scan_rclpy_probe_failed` 与双 CLI timeout |
| no-motion safety fields 继续固定 false | 通过，`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false` |
| 本轮不把 support-only / historical comparator 计成 OKR 增量 | 通过，本轮只记 O3/O1-supporting 诊断推进，不调百分比 |

## 验证证据核对

Algorithm owner 已运行：

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

## Live Artifact 摘要

`artifacts/live_o10_scan_qos_repair.raw.json`：

```text
status=blocked_with_root_cause
/scan.topic_type=sensor_msgs/msg/LaserScan
/scan.probe.best_attempt.label=rclpy_sensor_data_once
/scan.probe.best_attempt.error.type=ImportError
/scan.probe.attempts[1].label=cli_sensor_data_echo_once
/scan.probe.attempts[2].label=cli_default_echo_once
/scan.probe.attempts[*].timed_out=[false,true,true]
/amcl_pose.probe.boundary=/amcl_pose_probe_not_observed
map_to_odom=false
path_generated=false
root_causes=[
  /scan_rclpy_probe_failed,
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

## 产品验收判断

本轮满足了“把 `/scan` blocker 说清楚”的验收目标，但没有跨过 `scan observed -> amcl_pose observed -> map_to_odom=true -> path_generated=true` 这条现场链路。因此本轮只能算 O3/O1-supporting 诊断推进，不能算 path/material success，也不能触发 O1/O5/O6/O7 百分比提升或 KR 归档。
