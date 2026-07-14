# O3 Managed Runtime Scan Attempt Recovery Tech Done

## Sprint Type

sprint_type: epic

## 自主能力目标和本轮抓手

本轮目标不是继续扩展 `/scan` QoS 合同，而是把 latest true-board helper 无法回到 `/scan` attempt 层的问题前移到更早的 runtime/lifecycle blocker。

本轮抓手有两条：

1. helper 在 managed runtime 已经由 lifecycle CLI 证明 ready 时，直接返回当前 localization blocker，不再重复把 latest artifact 卡进 `/scan` 长等待；
2. helper 的 ROS2 CLI 超时回收改成有限等待，避免 `tf2_echo` 或 child probe 被杀后父进程继续卡死在 pipe drain，导致 artifact 长时间停在 `partial_runtime_in_progress`。

## 实际改动文件

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json`
- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/live_o10_managed_runtime_scan_attempt_recovery.raw.json`

## 接口影响

- O10 helper 新增 `managed_runtime_cli_localization_fast_path`，当 lifecycle CLI 已证明 `/map_server` 和 `/amcl` active 时，允许直接返回 `managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path`，并保留 `scan_probe_skipped_after_managed_runtime_lifecycle_ready` / `map_probe_skipped_after_managed_runtime_lifecycle_ready` 边界。
- ROS2 CLI timeout 回收继续保持 no-motion，只修改超时后的进程回收路径，不新增任何 `/cmd_vel`、`/api/base/manual`、`NavigateToPose` 或底盘串口动作。
- 导航文档同步明确：读 latest artifact 时先看 managed runtime / lifecycle readiness，再决定是否解释 BEST_EFFORT / RELIABLE `/scan` attempts。

## 实现内容

### 1. helper fast-path 补齐 lifecycle CLI 证明分支

此前 `managed_runtime_localization_fast_path` 只在 `managed_runtime.wait_result` 里已经观测到 `/map_server`、`/amcl` 时才会生效。真板这次的实际情况是：

- wait 阶段没有稳定留下 `observed_node_names`
- 但后续 `ros2 lifecycle get /map_server`、`ros2 lifecycle get /amcl` 已经能给出 active 事实

旧逻辑因此会继续掉回 `/scan` probe，latest artifact 容易卡成 partial。本轮新增 `managed_runtime_cli_localization_fast_path`，让 helper 在 CLI 已确认 lifecycle ready 时也能直接回到 localization blocker 收口。

### 2. ROS2 CLI timeout 回收 fail-closed

`run_ros()` 过去在 timeout 后会尝试：

- `SIGTERM`
- `SIGKILL`
- 无 timeout 的 `process.communicate()`

现场 `tf2_echo` / child probe 偶发会让最后一步无限等待，helper 虽然已经写了 partial artifact，但主进程自己不返回。本轮把最后的 pipe drain 也改成有限等待；即使板端 CLI 被杀后仍短暂占着 pipe，helper 也会直接返回 timeout 结果并继续收口。

## 验证结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，无输出。

### 2. 定向单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：

```text
Ran 60 tests in 2.214s
OK
```

### 3. 本地 fail-closed artifact

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --output sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json
```

结果：按预期 exit `2`，并落盘 fail-closed artifact。

关键字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `managed_runtime_started=false`
- `/scan.probe.boundary=scan_probe_skipped_without_ros2`
- `best_effort_attempt=false`
- `reliable_attempt=false`
- `path_generated=false`
- `root_causes=[map_lifecycle_latest_missing, ros2_command_unavailable_after_bash_source]`
- 顶层安全字段保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `route_execution_success=false`
  - `hil_pass=false`

### 4. 真板 helper 下发与执行

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/nav2_lifecycle_latest.json'
```

结果：本轮自然返回，exit `2`，并生成最新 live artifact。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cat /root/rober/onboard/runtime/nav2_lifecycle_latest.json' \
  > sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/live_o10_managed_runtime_scan_attempt_recovery.raw.json
```

结果：通过。

关键 live 字段：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_path_generation_runtime_no_motion`
- `managed_runtime_wait_result.boundary=managed_runtime_wait_timeout`
- `map_server_active=false`
- `amcl_active=false`
- `amcl_pose_observed=false`
- `/scan.probe.boundary=scan_probe_skipped_without_ros2`
- `best_effort_attempt=false`
- `reliable_attempt=false`
- `path_generation_boundary=path_generation_requested_but_ros2_unavailable`
- `path_generated=false`
- `root_causes` 前移为：
  - `canonical map proof -> map_lifecycle_proof_not_clean`
  - `ROS install/source -> ros2_command_unavailable_after_bash_source`
- 顶层安全字段继续保持：
  - `safe_to_control=false`
  - `robot_control_executed=false`
  - `delivery_success=false`
  - `route_execution_success=false`
  - `hil_pass=false`

现场日志片段显示 blocker 已经从 `/scan` attempt 层前移到 managed runtime / map_server / ROS2 source：

```text
[ERROR] [lifecycle_manager]: Failed to change state for node: map_server
[ERROR] [lifecycle_manager]: Failed to bring up all requested nodes. Aborting bringup.
```

以及：

```text
ros2_check timed out after 6.0 seconds
managed_runtime_wait_result.boundary=managed_runtime_wait_timeout
wait history node_list boundary=rclpy_node_names_failed
error=ModuleNotFoundError: No module named 'rclpy'
```

这说明本轮 latest live artifact 没有重新进入 BEST_EFFORT / RELIABLE `/scan` attempt 层，但 root cause 已经前移到更早的 runtime/lifecycle blocker，满足 sprint 允许的第二种验收口径。

### 5. 文本检索与 diff 检查

```bash
rg -n "managed runtime|ROS2 source|/scan|best_effort|reliable|partial_runtime_in_progress|safe_to_control|robot_control_executed|delivery_success|hil_pass" \
  sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py
```

结果：通过，检索到新增 fast-path 文档与 helper/test 关键字。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery
```

结果：通过，无 whitespace / conflict 标记。

## 数据、样本或调试输出变化

- 新增本轮 local artifact：
  - `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/local_o10_managed_runtime_scan_attempt_recovery.raw.json`
- 新增本轮 live artifact：
  - `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/artifacts/live_o10_managed_runtime_scan_attempt_recovery.raw.json`
- live artifact 不再长时间停在 `partial_runtime_in_progress`；本轮能自然收口成 `blocked_with_root_cause`
- live log tail 新增 `map_server` lifecycle bringup failure 与 `managed_runtime_wait_timeout` / `rclpy_node_names_failed` 证据

## 失败定位

本轮 true-board 没有恢复到 `/scan` BEST_EFFORT/RELIABLE attempt 层，当前更前置 blocker 已收敛为：

1. `managed_runtime_wait_timeout`
   - wait 历史反复记录 `rclpy_node_names_failed`
   - 错误为 `ModuleNotFoundError: No module named 'rclpy'`
2. `ros2_command_unavailable_after_bash_source`
   - `command -v ros2` 在 helper 的 sourced shell 中仍超时 6 秒
3. `map_server` lifecycle bringup 失败
   - `Failed to change state for node: map_server`
   - `Failed to bring up all requested nodes. Aborting bringup.`

因此本轮结论不是 `/scan_qos_or_window_timeout`，而是：

- 板端 managed runtime 已被启动；
- LiDAR serial 也曾启动；
- 但 ROS2 source / Python runtime / map_server lifecycle 仍不稳定；
- 所以 `/scan` attempt 在本轮被 fail-closed 跳过，继续保持 no-motion false safety fields。

## 剩余风险

- helper 的最新 live root cause 已前移，但 `ros2` sourced shell 超时与 `rclpy` 缺失是否来自同一环境漂移，仍需现场单独确认。
- `map_lifecycle_latest.json` 当前仍是 `blocked_with_root_cause`，所以 canonical map proof 自身也在拖低本轮输入 readiness。
- 本轮没有得到 `best_effort_attempt` / `reliable_attempt` 现场事实，因此 `/scan` QoS/sample timeout 层暂时不能继续计分。

## 下一步能力建设建议

- 下一轮优先拆分并修复 board 侧 ROS2 source / Python site-packages 漂移，再单独复验 `map_server` lifecycle 是否能 clean active。
- 只有当 `managed_runtime_wait_result` 不再 timeout，且 `ros2_check.ok=true`、`map_server_active=true`、`amcl_active=true` 时，才值得再次进入 `/scan` BEST_EFFORT / RELIABLE attempt。

## 下一条现场执行命令

```bash
ssh -p 37878 root@192.168.1.11 \
  'time bash -lc "source /opt/ros/humble/setup.bash; [ -f /root/rober/onboard/install/setup.bash ] && source /root/rober/onboard/install/setup.bash || true; command -v ros2; python3 -c \"import rclpy,sys; print(rclpy.__file__); print(sys.path[:8])\""'
```

这条命令优先验证当前最前置 blocker：board 侧 sourced shell 是否真的能同时拿到 `ros2` CLI 和 `rclpy` Python 运行时。
