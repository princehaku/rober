# Tech Done - O3 ROS2 Graph Timeout Root Cause

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/`
- Owner: `robot-algorithm-engineer`
- 收口时间: `2026-07-12 02:16:25 CST`

## 自主能力目标和本轮抓手

本轮目标是修复 O3 no-motion Nav2 runtime helper 的 `ros2_graph_timeout_root_cause` 分类：当现场事实已经证明 `board_source_preflight_ready`、`ros2 node list --help` 可用、`rclpy import` 可用，但 `ros2 node list`、`ros2 node list --no-daemon`、`ros2 daemon status`、`ros2 topic list` 都 timeout 时，主分类必须优先落到 `ros2_daemon_or_dds_graph_discovery_timeout`，不能再把 `board_source_preflight_ready` 当成 `workspace_source_or_env_mismatch` 的 primary reason。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 在 root-cause 分类器中把 `ros2_daemon_status_timeout` 纳入 graph discovery timeout 证据。
  - 当 `ros2_node_list_help_ok` 且 `board_source_preflight.rclpy_import_ok=true`，并且 managed runtime wait 已被 graph timeout 阻断时，优先输出 `ros2_daemon_or_dds_graph_discovery_timeout`。
  - 保留 `workspace_source_or_env_mismatch` 为 env 摘要缺失或 timeout 时的 remaining candidate，但不允许 `board_source_preflight_ready` 成为 workspace mismatch primary reason。
  - 继续把 `managed_process_lifecycle_not_ready` 和 `tf_runtime_secondary_after_graph_blocked` 放入 remaining candidates。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 `test_graph_timeout_root_cause_prefers_daemon_dds_when_board_source_ready`，覆盖当前 live artifact 的事实组合：board source ready、help/import ok、node/no-daemon/daemon/topic probes timeout。
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/local_o10_ros2_graph_timeout_root_cause.raw.json`
  - 已重新生成本地 fail-closed dry-run artifact。
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/tech-done.md`
  - 本文件记录最小收口、验证结果和 live 剩余缺口。

接口影响：只新增/修正 additive artifact 分类语义；不改变 CLI 参数、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不发送 NavigateToPose、不打开 WAVE ROVER UART。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，退出码 `0`，无输出。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 86 tests in 2.218s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/local_o10_ros2_graph_timeout_root_cause.raw.json
```

结果：按预期 fail-closed，退出码 `2`。本机没有 `/opt/ros/humble/setup.bash`、`/root/rober/onboard/install/setup.bash` 和 `/root/rober/onboard`，所以本地 artifact 分类仍为本地 source/env 缺失，不代表 live graph timeout 分类。

本地 artifact 关键字段：

```json
{
  "proof.status": "blocked_with_root_cause",
  "proof.board_source_preflight.classification": "board_source_preflight_source_failed",
  "proof.ros2_graph_timeout_root_cause.classification": "workspace_source_or_env_mismatch",
  "proof.ros2_graph_timeout_root_cause.primary_candidate.reason": "board_source_preflight_source_failed",
  "proof.managed_runtime_started": false,
  "proof.path_generation_attempted": false,
  "proof.path_generated": false,
  "proof.safe_to_control": false
}
```

## Live Artifact 状态

真板 SSH 短检查可达，helper 已成功推送到 `root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py`。随后 live helper 复跑进入 managed runtime 等待窗口；用户要求立即停止任何长等待后，已中断本地 SSH 等待，退出码 `130`，不再继续轮询真板。

因此本轮没有拉回新的 live artifact。当前本地文件 `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json` 仍是 `2026-07-12 02:07:01 CST` 的旧 artifact，尚未反映本轮分类修复。

旧 live artifact 当前关键字段仍为：

```json
{
  "proof.board_source_preflight.classification": "board_source_preflight_ready",
  "proof.board_source_preflight.cli_ready": true,
  "proof.board_source_preflight.rclpy_import_ok": true,
  "proof.ros2_graph_timeout_root_cause.classification": "workspace_source_or_env_mismatch",
  "proof.ros2_graph_timeout_root_cause.primary_candidate.reason": "board_source_preflight_ready",
  "proof.ros2_graph_timeout_root_cause.remaining_candidates": [
    "managed_process_lifecycle_not_ready",
    "tf_runtime_secondary_after_graph_blocked"
  ],
  "proof.managed_runtime_started": true,
  "proof.path_generation_attempted": false,
  "proof.path_generated": false,
  "proof.safe_to_control": false
}
```

这份旧 live artifact 是本轮未完成的复跑缺口，不能作为修复后 live 分类证据。

## 失败定位

- 已修复的失败：分类器此前允许 `board_source_preflight_ready` 在 env 摘要 timeout 时被提升成 `workspace_source_or_env_mismatch` primary reason。现在在 help/import ready 且 graph probes timeout 的场景下，daemon/DDS graph discovery 分类优先。
- 未完成的 live 验证：真板 helper 复跑被用户要求停止，未拉回新 artifact；当前 live 文件仍是旧分类。

## 剩余风险与下一步

- 需要短窗复跑真板 helper，并拉回 `live_o10_ros2_graph_timeout_root_cause.raw.json`，确认 live artifact 中 `classification=ros2_daemon_or_dds_graph_discovery_timeout`。
- 如果复跑后仍无法唯一归因，helper 应输出 `root_cause_unclassified_after_probe`，但当前单测覆盖的 live 事实组合应明确偏向 daemon/DDS graph discovery timeout。
- 本轮没有 path generation、route execution、delivery、HIL 或 production evidence；所有 no-motion safety 字段继续保持 false。

## Live 复跑附录 - 2026-07-12 02:23:13 CST

按 validation closeout 要求完成一次短窗口 live no-motion artifact 复跑；本附录只记录复跑事实，不改代码、不改测试、不改导航 docs、不改 OKR。

### 执行结果

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：推送完成，`timed_out=false`，`returncode=0`，`elapsed_s=1.528`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3.10 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/live_o10_ros2_graph_timeout_root_cause.raw.json'
```

结果：SSH wrapper 已返回，没有继续卡住；`timed_out=false`，`returncode=2`，`elapsed_s=139.004`。退出码 `2` 为 helper fail-closed blocked 结果，未作为运行异常处理。

```bash
scp -P 37878 \
  root@192.168.1.11:/root/rober/onboard/runtime/live_o10_ros2_graph_timeout_root_cause.raw.json \
  sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json
```

结果：拉回完成，`timed_out=false`，`returncode=0`，`elapsed_s=1.217`。

### 拉回 artifact 关键字段

```json
{
  "proof.status": "blocked_with_root_cause",
  "proof.board_source_preflight.classification": "board_source_preflight_ready",
  "proof.board_source_preflight.cli_ready": true,
  "proof.board_source_preflight.rclpy_import_ok": true,
  "proof.ros2_graph_timeout_root_cause.classification": "ros2_cli_plugin_or_import_timeout",
  "proof.ros2_graph_timeout_root_cause.primary_candidate": {
    "classification": "ros2_cli_plugin_or_import_timeout",
    "reason": "board_source_preflight_ready"
  },
  "proof.managed_runtime_started": true,
  "proof.managed_runtime_wait_result.reason": "ros2_node_list_timeout",
  "proof.managed_runtime_wait_result.graph_wait_summary.observed_node_names": [],
  "proof.managed_runtime_wait_result.graph_wait_summary.latest_ros2_node_list_timed_out": true,
  "proof.tf_topics_observed": {
    "/tf": false,
    "/tf_static": false
  },
  "proof.current_command": null,
  "proof.path_generation_attempted": false,
  "proof.path_generated": false,
  "proof.safe_to_control": false,
  "proof.publishes_cmd_vel": false,
  "proof.calls_base_manual": false,
  "proof.robot_control_executed": false,
  "proof.route_execution_success": false,
  "proof.delivery_success": false,
  "proof.hil_pass": false,
  "proof.uses_base_uart": false,
  "proof.sends_motion_commands": false,
  "proof.sends_base_motion_commands": false
}
```

### 结论和风险

- 新 live artifact 已产生并拉回，覆盖了前一段“仍是旧 artifact”的状态。
- 实际 live 分类是 `ros2_cli_plugin_or_import_timeout`，不是期望的 `ros2_daemon_or_dds_graph_discovery_timeout`；本轮按要求只记录实际值，不继续改代码。
- no-motion 安全边界保持成立：未生成 path，未执行 route/delivery/HIL，未发布 `/cmd_vel`，未调用 `/api/base/manual`，未使用底盘 UART。
- 剩余风险：分类修复在本地测试中通过，但 live 复跑仍没有落到期望分类；下一轮需要回到分类器或 probe 字段证据，解释为什么 `board_source_preflight_ready` 仍被归到 CLI/plugin/import timeout。

## Reason 修复补充收口 - 2026-07-12 02:29:31 CST

### 修复内容

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 修复 `ros2_cli_plugin_or_import_timeout` 分支的 `primary_candidate.reason` 选择逻辑。
  - 当 `cli_plugin_suspect` 由 `ros2_node_list_help_timeout`、`ros2_node_list_help_failed`、`rclpy_graph_segment_probe_timeout` 或 rclpy graph segment failure 触发时，reason 优先写具体 probe boundary。
  - 明确禁止把 `board_source_preflight_ready` 这类通过状态当成 CLI/plugin timeout 的 primary reason。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 live fact 回归用例：board source ready、`ros2 node list --help` timeout、rclpy graph segment timeout、graph probes timeout 时，分类保持 `ros2_cli_plugin_or_import_timeout`，但 primary reason 必须是 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`。

### 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，退出码 `0`。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 87 tests in 2.252s`，`OK`。

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/local_o10_ros2_graph_timeout_root_cause.raw.json
```

结果：按预期 fail-closed，退出码 `2`。本机没有 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard`，本地 artifact 仍为 source/env 缺失边界，不代表 live graph 分类。

本地 artifact 关键字段：

```json
{
  "proof.status": "blocked_with_root_cause",
  "proof.board_source_preflight.classification": "board_source_preflight_source_failed",
  "proof.ros2_graph_timeout_root_cause.classification": "workspace_source_or_env_mismatch",
  "proof.ros2_graph_timeout_root_cause.primary_candidate.reason": "board_source_preflight_source_failed",
  "proof.path_generation_attempted": false,
  "proof.path_generated": false,
  "proof.safe_to_control": false
}
```

### Live 复跑状态

- SSH 可达性检查通过：`ssh -p 37878 root@192.168.1.11 true` 退出码 `0`。
- helper 推送完成：`scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` 退出码 `0`。
- live no-motion helper 复跑已启动，但用户要求立即停止长等待；本地 SSH 等待已中断，退出码 `255`。
- 本轮没有拉回新的 live artifact。当前 `artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json` 不是本次 reason 修复后的 fresh live 证据。

### 剩余风险

- live rerun 未完成，尚未证明真板 artifact 已从 `primary_candidate.reason=board_source_preflight_ready` 修正为具体 timeout boundary。
- 代码和单测已覆盖目标 reason 逻辑；仍需下一轮短窗口 live 复跑并拉回 artifact 确认 `proof.ros2_graph_timeout_root_cause.primary_candidate.reason`。
- 本轮仍无 path generation、route execution、delivery、HIL、production cloud 或 safe-to-control success；no-motion 安全边界保持 false。

## Reason 修复后 Live-only Final Rerun - 2026-07-12 02:35:53 CST

本附录只做 validation closeout：推送当前 helper、用硬超时复跑真板 no-motion helper、拉回 fresh live artifact，并记录 artifact 摘录；没有改代码、测试、导航 docs、OKR、progress log 或历史 sprint。

### 执行结果

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：推送完成，`timed_out=false`，`returncode=0`，`elapsed_s=1.654`。

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && timeout 210s python3.10 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/live_o10_ros2_graph_timeout_root_cause.raw.json'
```

结果：本地 Python `subprocess.run(..., timeout=260)` wrapper 正常返回，`timed_out=false`，`returncode=2`，`elapsed_s=138.856`。退出码 `2` 是 helper fail-closed blocked artifact 结果，不是 SSH 或 wrapper timeout。

```bash
scp -P 37878 \
  root@192.168.1.11:/root/rober/onboard/runtime/live_o10_ros2_graph_timeout_root_cause.raw.json \
  sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json
```

结果：拉回完成，`timed_out=false`，`returncode=0`，`elapsed_s=1.574`。拉回文件大小 `191832` bytes，SHA256 `7f4f45b2303b33e1b112a39cc98440c9ade923af6bf4b50481fb9a5e4b26c645`。

### Fresh live artifact 摘录

```json
{
  "status": "blocked_with_root_cause",
  "proof.status": "blocked_with_root_cause",
  "proof.artifact_closeout.artifact_kind": "final",
  "proof.artifact_closeout.primary_root_cause": {
    "layer": "Managed runtime wait",
    "reason": "ros2_node_list_timeout"
  },
  "proof.current_command": null,
  "proof.ros2_graph_timeout_root_cause.classification": "ros2_cli_plugin_or_import_timeout",
  "proof.ros2_graph_timeout_root_cause.primary_candidate": {
    "classification": "ros2_cli_plugin_or_import_timeout",
    "reason": "ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout"
  },
  "proof.ros2_graph_timeout_root_cause.remaining_candidates": [
    {
      "classification": "workspace_source_or_env_mismatch",
      "reason": "workspace_environment_summary_not_observed_but_board_source_preflight_cli_ready"
    },
    {
      "classification": "managed_process_lifecycle_not_ready",
      "reason": "process_started_but_lifecycle_or_expected_nodes_not_proven_ready"
    },
    {
      "classification": "tf_runtime_secondary_after_graph_blocked",
      "reason": "/tf_topic_missing_recorded_as_secondary_readback_after_graph_blocked"
    }
  ],
  "proof.managed_runtime_started": true,
  "proof.managed_runtime_wait_result.reason": "ros2_node_list_timeout",
  "proof.path_generation_attempted": false,
  "proof.path_generated": false,
  "proof.safe_to_control": false,
  "proof.publishes_cmd_vel": false,
  "proof.calls_base_manual": false,
  "proof.robot_control_executed": false,
  "proof.route_execution_success": false,
  "proof.delivery_success": false,
  "proof.hil_pass": false,
  "proof.uses_base_uart": false,
  "proof.sends_motion_commands": false,
  "proof.sends_base_motion_commands": false
}
```

### 结论和风险

- Reason 修复后的 fresh live artifact 已覆盖旧文件；`primary_candidate.reason` 已从错误的 `board_source_preflight_ready` 变为具体边界 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`。
- Live 分类仍是 `ros2_cli_plugin_or_import_timeout`，不是更早预期的 `ros2_daemon_or_dds_graph_discovery_timeout`；本轮 closeout 按实际 artifact 收口，不继续改分类器。
- no-motion 安全边界保持成立：没有 path generation，没有 route/delivery/HIL，没有 `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART 或任何底盘运动命令。
- 剩余风险仍在 ROS2 CLI/plugin/import 与 graph probe timeout 边界；下一轮若继续推进，应优先解释 `ros2 node list --help` 与 rclpy graph segment probe 的 timeout 来源，而不是回到 `board_source_preflight_ready` 这个通过状态。
