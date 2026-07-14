# O3 Rclpy Scan Runtime Repair Tech Done

## Sprint Type

- `sprint_type: epic`
- Owner: `robot-algorithm-engineer`
- 自主能力目标：把上一轮 `/scan.topic_type=sensor_msgs/msg/LaserScan` 可见但 rclpy 读帧 ImportError 的问题，推进到可复核的 runtime/env/QoS 层 root cause。
- 本轮抓手：将 `/scan` 的 `rclpy_sensor_data_once` 从 helper 主 Python 进程迁移到 ROS-sourced child Python probe，保留 CLI sensor-data/default fallback，并继续保持 no-motion safety fields false。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 新增 `rclpy_scan_child_python_command()`，让 `/scan` rclpy probe 通过 `run_ros()` 的 `bash -lc` sourced 环境启动 child Python。
  - 新增 `environment_check`、`import_check`、`runtime_diagnostics`、`fallback_boundary`、`frame_observed`、`frame_stamp` 等 additive artifact 字段。
  - 新增 `classify_rclpy_import_failure()` 与 `/scan` root cause 细分：shared library、Python ABI、未 source 环境、child timeout after import。
  - 保留三段 probe 顺序：`rclpy_sensor_data_once -> cli_sensor_data_echo_once -> cli_default_echo_once`，且不发送任何运动命令。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 child probe command、import failure 分类、child timeout after import root cause 单测。
  - 现有 no-motion、managed runtime、safety guard 测试继续覆盖。
- `docs/navigation/field_route_evidence_preflight.md`
  - 记录 2026-07-11 14:42 live artifact 的 `/scan` child rclpy runtime 诊断字段和 root cause。
- `docs/navigation/fixed_route_workflow.md`
  - 更新 fixed-route/no-motion 现场阅读顺序：优先读取 14:42 artifact 的 child rclpy import/runtime 结果。
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/local_o10_rclpy_scan_runtime_repair.raw.json`
  - 本地 Mac no ROS fail-closed artifact。
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`
  - 真实板 no-motion live artifact。

## 接口影响

- O10 helper JSON 仅 additive / backward-compatible 扩展。
- 新字段位于 `/scan` probe attempt 与 probe summary 内：
  - `runtime=ros_sourced_child_python`
  - `environment_check`
  - `import_check`
  - `runtime_diagnostics.child_process`
  - `fallback_boundary`
  - `frame_observed`
  - `frame_stamp`
- 顶层 safety fields 继续固定：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `hil_pass=false`

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：exit `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- 结果：`Ran 55 tests in 2.191s OK`

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/local_o10_rclpy_scan_runtime_repair.raw.json
```

- 结果：exit `2`，按预期 fail-closed 并落盘 artifact。
- 本地 root causes：`map_lifecycle_latest_missing`、`ros2_command_unavailable_after_bash_source`。
- 本地 safety fields：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：exit `0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

- 结果：exit `2`，真实板 no-motion proof fail-closed 并写出 `/root/rober/onboard/runtime/nav2_lifecycle_latest.json`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json
```

- 结果：exit `0`

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair
```

- 最终结果：exit `0`

## Live Artifact 关键字段

- Artifact: `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json`
- `status=blocked_with_root_cause`
- `/scan.topic_type=sensor_msgs/msg/LaserScan`
- `/scan.topic_present=true`
- `/scan.probe.observed=false`
- `/scan.probe.best_attempt.label=rclpy_sensor_data_once`
- `/scan.probe.best_attempt.runtime=ros_sourced_child_python`
- `/scan.probe.best_attempt.import_check.ok=true`
- `/scan.probe.best_attempt.import_check.rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`
- `/scan.probe.best_attempt.runtime_diagnostics.child_process.timed_out=true`
- Root cause: `/scan_rclpy_child_timeout_after_import`
- CLI fallback:
  - `cli_sensor_data_echo_once`: timeout
  - `cli_default_echo_once`: timeout
- `initialpose_published=true` via CLI fallback。
- `/amcl_pose`: `observed=false`，root cause `/amcl_pose_probe_timeout`。
- `map_to_odom=false`，root cause `map_to_odom_dynamic_source_missing`。
- `tf_chain_observed.odom_to_base_link=true`
- `tf_chain_observed.base_link_to_laser_frame=true`
- `tf_chain_observed.map_to_base_link=false`
- `path_generated=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

## 失败定位

上一轮 `/scan` 的 `rclpy_sensor_data_once` 失败点是主 Python 进程没有 ROS shared-library 环境，表现为 `librcl_action.so` / `_rclpy_pybind11` ImportError。

本轮 `/scan` child probe 已证明 sourced runtime 环境可 import rclpy：`import_check.ok=true`，`LD_LIBRARY_PATH`、`PYTHONPATH`、`AMENT_PREFIX_PATH` 均包含 `/opt/ros/humble` 与 workspace overlay。因此 `/scan` 的旧 ImportError 已从该 probe 上消除。

新的 blocker 是：child rclpy subscription 已 import 成功，但在 probe 窗口内没有读到 LaserScan frame，并被外层 child-process timeout/ExternalShutdown 收口；两条 ROS CLI echo fallback 也 timeout。当前 root cause 应按 `/scan_rclpy_child_timeout_after_import` 处理，而不是继续修主进程 import 环境。

## 剩余风险与下一步

- `/scan` 仍未 observed，不能声明 localization/path proof。
- `amcl_param_probe` 和 `initialpose` 的主进程 rclpy attempt 仍可见 ImportError，但 initialpose 已通过 CLI fallback 发布成功；本轮只修 `/scan` probe runtime，不扩大到所有 rclpy helper。
- `/amcl_pose=false`、`map_to_odom=false`、`path_generated=false`，O1 current same-run path generation 仍未达成。
- 下一轮建议优先把 child probe 的 endpoint/publisher inventory 提前到 `/scan` timeout 前，或直接检查 LiDAR publisher 在 managed runtime 窗口内是否实际 publish sample，再决定是否调 QoS/timeout/lidar driver。
