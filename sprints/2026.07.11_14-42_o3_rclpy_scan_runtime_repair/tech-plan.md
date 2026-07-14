# O3 Rclpy Scan Runtime Repair Tech Plan

## 方案

本轮从上一轮 artifact 的具体失败点出发：`/scan.topic_type=sensor_msgs/msg/LaserScan` 已可见，但 `rclpy_sensor_data_once` 因 `ImportError` 失败，CLI fallback 也 timeout。因此方案不再扩展只读 surface，而是修复或绕开 `/scan` frame reader runtime。

Implementation owner 需要先在真实板或等价 ROS Humble runtime 中复现 `rclpy` import failure，确认以下边界：

- 是否缺少 `source /opt/ros/humble/setup.bash` 或 install overlay。
- 是否缺少 `LD_LIBRARY_PATH` / `PYTHONPATH` / `AMENT_PREFIX_PATH`。
- 是否 Python ABI 与 `_rclpy_pybind11` wheel / apt package 不匹配。
- 是否脚本执行环境绕过了 ROS shell setup。
- 是否 `librcl_action.so` 存在但 loader 不可见。

修复策略按保守优先级执行：

1. 优先让现有 `rclpy_sensor_data_once` 在 managed runtime 命令环境下成功 import 并订阅 `/scan`。
2. 如果板端 `rclpy` 修复风险过高，增加不依赖 Python `rclpy` 的 sensor-data frame reader fallback，例如通过更稳定的 shell wrapper / sourced ROS CLI / bounded Python subprocess，但 artifact 必须标注 fallback boundary。
3. 保持上一轮三段式 attempts 结构，新增 runtime diagnostics 字段，避免只输出裸 traceback。
4. `/scan` frame observed 后，同窗口继续复验 `/amcl_pose`、`map_to_odom`、`map_to_base_link` 和 path generation；失败时仍 fail-closed。

## 文件范围

本 planning 阶段允许改动且已限定为：

- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/pre_start.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/prd.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/tech-plan.md`

后续 implementation 阶段建议允许 `robot-algorithm-engineer` 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/tech-done.md`
- `sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/*`

禁止修改：

- `OKR.md`
- O5 relay / cloud production readiness 代码
- O6 archive / readback schema
- O7 workstation UI
- WAVE ROVER、UART、串口、引脚、电压、波特率、机械或 vendor docs
- 其他 sprint 目录

## 接口影响

O10 helper JSON 只允许 additive / backward-compatible 变化。建议新增或扩展：

- `proof.localization_signal_freshness["/scan"].probe.runtime_diagnostics`
- `proof.localization_signal_freshness["/scan"].probe.import_check`
- `proof.localization_signal_freshness["/scan"].probe.environment_check`
- `proof.localization_signal_freshness["/scan"].probe.fallback_boundary`
- `proof.localization_signal_freshness["/scan"].probe.frame_observed`
- `proof.localization_signal_freshness["/scan"].probe.frame_stamp`

Root cause 应优先表达为可执行 blocker，例如：

- `/scan_rclpy_import_failed_missing_shared_library`
- `/scan_rclpy_import_failed_python_abi_mismatch`
- `/scan_ros_environment_not_sourced`
- `/scan_cli_echo_timeout_after_rclpy_bypass`
- `/scan_frame_observed_amcl_pose_timeout`
- `map_to_odom_dynamic_source_missing`

所有 safety fields 必须保持：

- `safe_to_control=false`
- `robot_control_executed=false`
- `delivery_success=false`
- `hil_pass=false`

## 实施拆分

1. `robot-algorithm-engineer` 读取上一轮 live artifact，复现并最小化 `rclpy` import failure。
2. 修复 helper 的 ROS environment / sourced command / fallback reader，使 `/scan` attempt 输出更强 runtime diagnostics。
3. 更新 helper 单测，覆盖 import failure 分类、fallback boundary、frame observed、CLI timeout 和 false safety fields。
4. 更新 `docs/navigation/field_route_evidence_preflight.md` 与 `docs/navigation/fixed_route_workflow.md`，说明本轮 artifact 的阅读顺序。
5. 在本地跑 fail-closed 验证；真实板可达时必须跑 live no-motion helper并拉回 artifact。
6. 写 `tech-done.md`，记录实际改动、验证输出、live artifact 关键字段、失败定位和剩余风险。

## 验收命令

后续 implementation owner 必须运行并记录：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/local_o10_rclpy_scan_runtime_repair.raw.json
```

本地 Mac 没有 ROS 时允许 exit 2，但必须 fail-closed 且落盘 artifact。

真实板可达时必须运行：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/artifacts/live_o10_rclpy_scan_runtime_repair.raw.json
```

```bash
rg -n "rclpy|/scan|safe_to_control=false|delivery_success=false|path_generated|map_to_odom" \
  sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair
```

Planning 阶段验收命令为：

```bash
test -f sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/pre_start.md && test -f sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/prd.md && test -f sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair/tech-plan.md
```

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|/scan|rclpy|safe_to_control=false|delivery_success=false" sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair
```

```bash
git diff --check -- sprints/2026.07.11_14-42_o3_rclpy_scan_runtime_repair
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 中最低主 Objective 是 O5，约 `~85%`。O1、O6、O7 当前均约 `~93%`。

本 sprint 不直接针对 O5。理由：

- `sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/` 已证明 cutover readiness packet 是 support-only aggregator，固定 `okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence`、`production_ready=false`。
- `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/` 已 fail-closed，未找到新的 `field_execution_pack`、真实 production external evidence、Nav2 result、delivery record、operator confirmation 或 production readback。
- 继续 O5 readiness / probe / checklist / support-only 工作会重复消费同一 blocker，不能产生主 OKR 增量。

本 sprint 如何解锁 O1 current same-run path generation：

- `/scan` frame observed 是 AMCL 输出 `/amcl_pose` 的前置输入。
- `/amcl_pose` 与 dynamic `map->odom` 是 same-run no-motion path generation 的前置条件。
- 修复或绕开 `rclpy` runtime 读帧问题后，下一步可以在同一 helper 中直接复验 `amcl_pose_observed`、`map_to_odom=true` 和 `path_generated=true`。

本 sprint 如何解锁 O6/O7 current-run material：

- 一旦 O1/O3 产出 current-run scan/localization/path artifact，O6/O7 才能消费新的 same-task material，而不是继续复用 historical comparator。
- 后续 material 形态应落到 `task_id`、`map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、Nav2 result、delivery record 或 operator confirmation。
- 本轮不直接改 O6/O7 schema；只修上游 live evidence source，避免 O6/O7 继续做 observe-only wrapper。

## 风险

- 板端 `rclpy` import failure 可能来自系统安装或环境变量，修复可能需要现场命令权限或容器/overlay 调整。
- CLI fallback 也 timeout，说明 `rclpy` 修复不必然等于 `/scan` frame observed。
- `/scan` observed 后仍可能卡在 `/amcl_pose`、initial pose、AMCL 参数、map 质量或 TF source。
- 真实板不可达时只能得到 local fail-closed，不能声明 live no-motion artifact。
- 本轮不得打开 motion 或 safety fields；任何 `safe_to_control=true`、`delivery_success=true` 或 `hil_pass=true` 都必须视为验收失败，除非 CEO 另行提供真实安全验收材料。

## 输出要求

后续 implementation owner 必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果。
3. live artifact 关键字段，尤其是 `/scan` observed、`rclpy` runtime diagnostics、`/amcl_pose`、`map_to_odom`、`path_generated` 和 false safety fields。
4. 失败定位，如仍 blocked。
5. 剩余风险和下一条现场执行命令。
