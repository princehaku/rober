# Tech Done - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 07:18 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`

## 实际改动

1. `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
   - 把 `board_source_preflight` 改成 additive 的 heavy/light/rclpy 三层：
     - heavy 继续记录 `ros2 --help >/dev/null`
     - lightweight 记录 `ros2 daemon status` + `ros2 node list`
     - `rclpy import` 仍单独记录 runtime 可用性
   - `ros2_cli_ok` / `cli_ready` 不再依赖 heavy help；只要 source/path + lightweight 成功就放行。
   - 新增 `lightweight_readiness`、`lightweight_cli_ready`、`ros2_lightweight_*` 命令摘要，保留旧字段兼容。
2. `onboard/tests/test_nav2_runtime_proof_helper.py`
   - 更新 amortized preflight mock payload。
   - 新增 lightweight timeout 用例。
   - 把 heavy help timeout 用例改成“diagnostic only，不阻塞 CLI ready”。
3. `docs/navigation/field_route_evidence_preflight.md`
   - 补充 `2026-07-12 06:54` lightweight CLI readiness 读法和最新 true-board artifact 边界。
4. `docs/navigation/fixed_route_workflow.md`
   - 补充 fixed-route/no-motion closeout 对 heavy/light/rclpy 三层的读取顺序。
5. `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/`
   - 新增本轮 local/live raw artifact。

## 实现说明

- 这轮没有碰 launch、UART、底盘控制、`/cmd_vel`、`/api/base/manual` 或 NavigateToPose。
- helper 现在优先用 true-board 已经证明可返回的 `ros2 node list` 作为 lightweight readiness 主信号。
- `ros2 --help` 仍保留在 artifact 里，方便继续追 CLI plugin discovery / help cold-start，但不再是唯一硬 gate。
- latest true-board `330s` artifact 已证明：
  - `source_stage_ok=true`
  - `ros2_cli_path_ok=true`
  - `lightweight_readiness.primary_label=ros2_node_list`
  - `lightweight_readiness.successful_labels=["ros2_node_list"]`
  - `cli_invocation.timed_out=true`
  - `cli_ready=true`
  - `runtime_ready=true`
- helper 已实际进入 downstream no-motion probes，最终 blocker 前移到：
  - `map_server_lifecycle_not_active_during_preflight`
  - `amcl_lifecycle_not_active_during_preflight`
  - `/scan_no_publisher`
  - `/map_once_not_observed`
  - `/tf_topic_missing`

## 验证命令与结果

### 1. 语法检查

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：`RC=0`

### 2. 定向单测

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- 结果：`Ran 97 tests in 2.260s OK`

### 3. local dry-run

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --strict-no-motion \
  --no-base-uart \
  --output-json sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/local_lightweight_cli_readiness_dry_run.raw.json
```

- 结果：`RC=2`
- 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_source_failed`
  - `lightweight_cli_ready=false`
  - `cli_ready=false`
  - `runtime_ready=false`
  - `path_generation_attempted=false`
  - `path_generated=false`
  - `safe_to_control=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `delivery_success=false`
  - `hil_pass=false`
  - `uses_base_uart=false`
- 失败定位：本机仍无 `/opt/ros/humble/setup.bash`，符合 macOS fail-closed 预期。

### 4. true-board 验收命令（按题面 240s）

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- 结果：`RC=0`

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 240s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --output-json /tmp/live_o10_lightweight_cli_readiness.raw.json'
```

- 结果：`RC=124`
- 关键字段（拉回 artifact 后读取）：
  - `status=interrupted_before_final_artifact`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `lightweight_readiness.primary_label=ros2_node_list`
  - `lightweight_readiness.successful_labels=["ros2_node_list"]`
  - `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
  - `ros2_cli_invocation_ok=false`
  - `cli_ready=true`
  - `runtime_ready=true`
  - `recent_commands` 已进入 `ros2 lifecycle get /map_server`、`ros2 lifecycle get /amcl`、`/scan` probes
  - 所有 no-motion false 字段继续固定为 `false`
- 失败定位：240s 外层 timeout 在 helper 完成后续 no-motion probes 之前打断了 closeout；本轮 primary blocker 已不再是 `ros2 --help`。

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_lightweight_cli_readiness.raw.json \
  sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness.raw.json
```

- 结果：`RC=0`

### 5. 补充 true-board 长窗口诊断（330s，只读 no-motion）

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && /usr/bin/timeout 330s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py --strict-no-motion --no-base-uart --output-json /tmp/live_o10_lightweight_cli_readiness_330s.raw.json'
```

- 结果：`RC=2`
- 关键字段：
  - `status=blocked_with_root_cause`
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `source_stage_ok=true`
  - `ros2_cli_path_ok=true`
  - `lightweight_cli_ready=true`
  - `cli_ready=true`
  - `runtime_ready=true`
  - `lightweight_readiness.primary_label=ros2_node_list`
  - `lightweight_readiness.successful_labels=["ros2_node_list"]`
  - `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
  - `ros2_cli_invocation_ok=false`
  - `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_and_amcl_inactive`
  - `amcl_readiness_summary.blocked_reason=amcl_lifecycle_not_active`
  - `tf_readiness_summary.blocked_reason=/tf_topic_missing`
  - `path_generation_attempted=false`
  - `path_generated=false`
  - `safe_to_control=false`
  - `publishes_cmd_vel=false`
  - `calls_base_manual=false`
  - `robot_control_executed=false`
  - `route_execution_success=false`
  - `delivery_success=false`
  - `hil_pass=false`
  - `uses_base_uart=false`
- 失败定位：
  - preflight 已通过；
  - downstream blocker 收窄为 `map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`；
  - `ros2 daemon status` 仍在 `3.0s` 内 timeout，但已降级为 lightweight 诊断项，不再挡住 CLI ready。

```bash
scp -P 37878 root@192.168.1.11:/tmp/live_o10_lightweight_cli_readiness_330s.raw.json \
  sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/artifacts/live_o10_lightweight_cli_readiness_330s.raw.json
```

- 结果：`RC=0`

### 6. scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate
```

- 结果：`RC=0`

## live/local artifact 关键字段

### local

- `artifacts/local_lightweight_cli_readiness_dry_run.raw.json`
- `classification=board_source_preflight_source_failed`
- `lightweight_cli_ready=false`
- `cli_ready=false`
- `runtime_ready=false`
- `path_generation_attempted=false`
- `path_generated=false`
- 全部 no-motion false 字段保持 `false`

### live 240s

- `artifacts/live_o10_lightweight_cli_readiness.raw.json`
- `status=interrupted_before_final_artifact`
- `classification=board_source_preflight_ready`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
- `cli_ready=true`
- `runtime_ready=true`
- `cli_invocation.timed_out=true`
- `map_lifecycle_proof_not_clean` 仍在 root cause 链上
- 全部 no-motion false 字段保持 `false`

### live 330s

- `artifacts/live_o10_lightweight_cli_readiness_330s.raw.json`
- `status=blocked_with_root_cause`
- `classification=board_source_preflight_ready`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `cli_ready=true`
- `runtime_ready=true`
- `cli_invocation.timed_out=true`
- `amcl_readiness_summary.blocked_reason=amcl_lifecycle_not_active`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

## 剩余风险

1. `ros2 daemon status` 仍在 `3.0s` 预算内 timeout，后续可能还要继续区分 daemon slow path 和 graph/runtime slow path。
2. true-board 240s 验收命令虽然已经证明 preflight 放行成功，但最终 closeout 仍容易被外层 timeout 打断；当前完整 blocker 依赖补充的 `330s` 只读诊断 artifact。
3. downstream 当前仍没有 `map_server_active=true`、`amcl_active=true`、`amcl_pose_observed=true`、dynamic `map->odom=true`、`path_generation_attempted=true` 或 `path_generated=true`。
4. 本轮仍是 O3/O1 supporting no-motion diagnostic delta，不是 path generation、route execution、delivery/operator acceptance、HIL 或 production evidence。

## 是否需要协同

- Product：需要用本轮新 blocker 更新验收口径，确认下一轮直接打 `map_server/amcl inactive`、`/scan_no_publisher`、`/tf_topic_missing`，不要回流 O5 support-only。
- Hardware：当前 `/scan_no_publisher` 可能涉及现场 LiDAR runtime/串口/进程状态，但本轮没有改硬件路径。
- Autonomy：下一轮若要继续压缩 `map_server/amcl inactive` 与 `/tf_topic_missing`，需要配合核对 Nav2/AMCL bringup 预期。
- Full-Stack：本轮不需要。
