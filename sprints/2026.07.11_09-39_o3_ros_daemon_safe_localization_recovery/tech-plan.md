# O3 ROS Daemon-safe Localization Recovery Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节完成度最低的主 Objective 是 O5，约 `~85%`。
2. 本 sprint 不直接推进 O5。
3. 转向理由：O5 缺真实 production external evidence，继续 readiness/probe/support packet 会重复消费 `no_real_production_external_evidence`，且 `okr_credit_allowed=false`。本轮继续 O3 现场 lane，因为真实板 live raw JSON 已暴露 ROS2 CLI/daemon `!rclpy.ok()` 新根因，修复后可解锁同轮 localization/path material。

## Owner 与分工

- `robot-algorithm-engineer` 单线闭环：实现 daemon-safe live localization probe、复跑本地与真实板验证、修复失败、更新 `tech-done.md`。
- 主节点：派单、验收、更新收口文档。

## 文件范围

允许修改：

- `onboard/scripts/field_route_evidence_preflight.py`
- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_field_route_evidence_preflight.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/tech-done.md`
- `sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/**`

仅当 live evidence 证明 launch/runtime 参数漂移时，允许修改：

- `onboard/scripts/o11_nav2_lifecycle.sh`
- `onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py`
- `onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py`

不得修改：

- O5/O6/O7 relay、archive、PC workstation 或 cloud readiness 文件；
- WAVE ROVER 运动协议、串口参数、速度映射或任何底盘执行入口；
- 其他 sprint 目录，除非只读引用。

## 技术方案

1. 在 `field_route_evidence_preflight.py` 增加板端 ROS CLI/daemon health probe，捕获 `RuntimeError: !rclpy.ok()`、XMLRPC fault、daemon unavailable、topic CLI nonzero 等状态。
2. 对只读 ROS graph 命令增加 daemon-safe retry：第一次失败若命中 daemon fault，执行 `ros2 daemon stop` / 可选 `ros2 daemon start` 或等价 bypass，再重试原始 topic/lifecycle/TF 查询。
3. artifact 新增 `ros_daemon_health`、`ros_cli_retry_summary`、`daemon_fault_detected`、`daemon_recovered`、`retry_attempts`、`recovered_topics` 和 `unrecovered_blockers` 等短摘要；不得回显敏感路径、token、raw response body 或完整 traceback。
4. 若 daemon 恢复后 `/scan`、`/amcl_pose`、map/TF 仍不可见，root cause 必须转为定位链事实，不再停留在 generic topic missing。
5. `o10_amcl_nav2_runtime_proof.py` 只在需要时补同样的 ROS CLI daemon reset/retry，确保 `/api/nav2/proof/refresh` 的 proof 也不会被 daemon fault 污染。

## 接口边界

- daemon reset/retry 只能用于 ROS graph/topic/lifecycle/TF 只读查询。
- `/initialpose` 仍是唯一允许写入 ROS graph 的 topic，且只在 explicit opt-in 下用于 AMCL seed。
- 所有输出继续 fail-closed：`safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`hil_pass=false`。
- 不允许 `NavigateToPose`、`/cmd_vel`、`/api/base/manual` 或任何真实底盘运动。

## 验收命令

子 agent 必须运行并汇报结果：

```bash
python3 -m py_compile onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/scripts/upper_robot_api.py
```

```bash
python3 -m unittest onboard.tests.test_field_route_evidence_preflight onboard.tests.test_upper_robot_api
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test
```

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode local --dry-run --output sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/local_preflight.raw.json
```

若真实上位机可达，必须保持 no-motion stop/start/status/refresh/stop 安全序列，再运行：

```bash
python3 onboard/scripts/field_route_evidence_preflight.py --mode ssh --ssh-target root@192.168.1.11 --ssh-port 37878 --timeout-s 12 --output sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery/artifacts/live_daemon_safe_localization.raw.json
```

最后运行：

```bash
git diff --check -- onboard/scripts/field_route_evidence_preflight.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_field_route_evidence_preflight.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_09-39_o3_ros_daemon_safe_localization_recovery
```

如修改 launch/runtime 文件，追加：

```bash
git diff --check -- onboard/scripts/o11_nav2_lifecycle.sh onboard/src/ros2_trashbot_bringup/launch/autonomous.launch.py onboard/src/ros2_trashbot_bringup/test/test_launch_contract_static.py
```

## 风险与回滚

- 如果真实板不可达，只能保留 local dry-run 和 SSH 不可达原因，不宣称现场修复。
- 如果 daemon reset 失败，保持 fail-closed，并把 `daemon_recovered=false` 写入 artifact。
- 如果 daemon 恢复但定位链仍 blocked，不上调 OKR；下一轮按新 root cause 修 LiDAR、map server、AMCL 或 TF。
