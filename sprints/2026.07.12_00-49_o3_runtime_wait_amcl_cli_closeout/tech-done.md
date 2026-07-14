# Tech Done - O3 Runtime Wait + AMCL CLI Closeout

## Sprint 类型

- sprint_type: epic
- 更新时间：2026-07-12 01:24:53 CST
- Owner：robot-algorithm-engineer
- 目标：O3/O1 strict no-motion runtime wait + AMCL CLI fallback closeout。
- 边界：本轮不改 `OKR.md`、不改 `docs/process/okr_progress_log.md`、不写 `side2side_check.md` / `final.md`，不触碰 O5/O6/O7、Web/API 或硬件 UART 控制配置。

## 自主能力目标和本轮抓手

本轮抓手是 O1 current same-run path generation / Nav2 route execution 的前置门：先把 O3 no-motion managed runtime wait、AMCL/TF CLI fallback、path generation gate 做成可自然收口的 live artifact。

上一轮 `23-49` 已证明 true-board child Python graph probe 后 `ros2 node list` fallback 真实执行，但 artifact 仍停在 `partial_runtime_in_progress` 与 `current_command=ros2 node list`。本轮不再把“fallback 已执行”当作进展，而是要求：

- managed runtime wait 必须自然写出 final `managed_runtime_wait_result`。
- AMCL CLI fallback 必须在 true-board artifact 中给出可复核 closeout。
- gate 未 ready 时继续保持 `path_generation_attempted=false` / `path_generated=false`。
- 全程保持 no-motion，不发布 `/cmd_vel`、不调用 `/api/base/manual`、不发送 NavigateToPose、不打开 WAVE ROVER UART。

## 实际改动

### `onboard/scripts/o10_amcl_nav2_runtime_proof.py`

- 将 board ROS CLI invocation preflight 从 4.0s 调整为 6.0s，并用中文注释记录真板 `ros2 --help` 冷启动约 4.5s，避免把可用 CLI 误判为不可用。
- 为 `rclpy_node_names()` 增加 managed wait 场景下的短预算 child/fallback probe 参数，避免 `ros2 node list` fallback 单次拖穿外层 wait。
- 增加 managed graph wait summary、history cap 与 final reason/boundary 归因，区分 `ros2_node_list_timeout`、`ros2_node_list_empty_after_wait`、fallback observed、节点可见但 lifecycle 未 active 等状态。
- 增加 AMCL CLI fallback closeout：在 rclpy probe 不完整或不可用时，用短预算 CLI 采集 `/amcl`、`/tf`、`/tf_static` 和 AMCL params，并合并回 artifact。
- 当 managed runtime wait 已被 graph blocker 阻塞时，跳过后续慢速 TF/topic/lifecycle probes，写入明确 skipped boundary，避免 artifact 卡成 `partial_runtime_in_progress`。
- primary root cause 现在优先保留 managed runtime wait blocker，便于 O3 后续修复从 `ros2_node_list_timeout` 继续，而不是被后续探针覆盖。

### `onboard/tests/test_nav2_runtime_proof_helper.py`

- 新增 6.0s preflight 语义覆盖：`test_board_cli_layer_uses_six_second_invocation_budget`。
- 在 CLI invocation timeout 分类测试中断言 artifact 字段 `cli_invocation_timeout_s=6.0`。
- 增加/调整 managed wait、bounded fallback、downstream skip、AMCL CLI fallback 相关单测。

### `docs/navigation/field_route_evidence_preflight.md`

- 补充 2026-07-12 O3 runtime wait closeout 说明，记录 `managed_runtime_wait_result.graph_wait_summary`、AMCL CLI fallback 字段和 no-motion gate 判定。

### `docs/navigation/fixed_route_workflow.md`

- 补充 fixed route / planner-only 入口的读取规则：必须优先看 final wait reason 与 AMCL/TF fallback closeout；gate 未 ready 时不得尝试 path generation。

### Artifacts

- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/local_o10_runtime_wait_amcl_cli_closeout.raw.json`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/live_o10_runtime_wait_amcl_cli_closeout.raw.json`
- `sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/live_o10_runtime_wait_amcl_cli_closeout.partial.raw.json`

## 验证结果

### 本地静态与单测

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，退出码 0。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：

```text
Ran 81 tests in 2.221s
OK
```

### 本地 fail-closed artifact

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/local_o10_runtime_wait_amcl_cli_closeout.raw.json
```

结果：退出码 2，预期 fail-closed。macOS 本机没有 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard`，artifact 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "proof.last_phase": "final",
  "proof.artifact_closeout.primary_root_cause": {
    "layer": "canonical map proof",
    "reason": "map_lifecycle_latest_missing"
  },
  "proof.board_source_preflight.classification": "board_source_preflight_source_failed",
  "proof.board_source_preflight.cli_invocation_timeout_s": 6.0,
  "proof.managed_runtime_started": false,
  "proof.managed_runtime_wait_result.boundary": "managed_runtime_not_requested",
  "proof.path_generation_attempted": false,
  "proof.path_generated": false
}
```

### True-board no-motion validation

先推送 helper：

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，退出码 0。

执行 patched helper，外层由 Python `timeout=150` 包住，避免 SSH/helper 无限挂住：

```bash
ssh -p 37878 root@192.168.1.11 \
  'cd /root/rober/onboard && python3.10 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/live_o10_runtime_wait_amcl_cli_closeout.raw.json'
```

结果：

```text
ssh_returncode=2
elapsed_s=117.4
```

随后拉回 artifact：

```bash
scp -P 37878 root@192.168.1.11:/root/rober/onboard/runtime/live_o10_runtime_wait_amcl_cli_closeout.raw.json \
  sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout/artifacts/live_o10_runtime_wait_amcl_cli_closeout.raw.json
```

结果：通过，退出码 0。

最终 live artifact 关键字段：

```json
{
  "status": "blocked_with_root_cause",
  "proof.artifact_closeout.artifact_kind": "final",
  "proof.last_phase": "final",
  "proof.current_command": null,
  "proof.artifact_closeout.primary_root_cause": {
    "layer": "Managed runtime wait",
    "reason": "ros2_node_list_timeout"
  },
  "proof.board_source_preflight.classification": "board_source_preflight_ready",
  "proof.board_source_preflight.cli_invocation_timeout_s": 6.0,
  "proof.board_source_preflight.ros2_cli_invocation_ok": true,
  "proof.board_source_preflight.rclpy_import_ok": true,
  "proof.managed_runtime_started": true,
  "proof.managed_runtime_wait_result": {
    "ok": false,
    "reason": "ros2_node_list_timeout",
    "boundary": "ros2_node_list_timeout"
  },
  "proof.managed_runtime_wait_result.graph_wait_summary.latest_ros2_node_list_boundary": "ros2_node_list_timeout",
  "proof.managed_runtime_wait_result.graph_wait_summary.latest_ros2_node_list_timed_out": true,
  "proof.managed_runtime_wait_result.graph_wait_summary.fallback_used": true,
  "proof.managed_runtime_wait_result.graph_wait_summary.fallback_observed": false,
  "proof.managed_runtime_wait_result.graph_wait_summary.observed_node_names": [],
  "proof.tf_source_root_cause_detail.amcl_param_probe_boundary": "cli_amcl_inventory_observed_amcl_params",
  "proof.tf_source_root_cause_detail.reason": "/tf_topic_missing",
  "proof.tf_topics_observed": {
    "/tf": false,
    "/tf_static": false
  },
  "proof.commands.map_to_odom_tf.boundary": "tf_probe_skipped_after_managed_runtime_graph_wait_blocked",
  "proof.commands.scan_once.boundary": "scan_probe_skipped_after_managed_runtime_graph_wait_blocked",
  "proof.path_generation_attempted": false,
  "proof.path_generated": false
}
```

No-motion 字段：

```json
{
  "safe_to_control": false,
  "publishes_cmd_vel": false,
  "calls_base_manual": false,
  "robot_control_executed": false,
  "route_execution_success": false,
  "delivery_success": false,
  "hil_pass": false,
  "uses_base_uart": false
}
```

### scoped diff check

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_00-49_o3_runtime_wait_amcl_cli_closeout
```

结果：通过，退出码 0。

## 失败定位

patched 后 true-board 已不再阻塞于 `board_source_preflight_ros2_cli_invocation_timeout`：

- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `proof.board_source_preflight.cli_invocation_timeout_s=6.0`
- `proof.board_source_preflight.ros2_cli_invocation_ok=true`
- `proof.board_source_preflight.rclpy_import_ok=true`

当前阻塞已推进到 managed runtime graph wait：

- `proof.artifact_closeout.primary_root_cause.layer=Managed runtime wait`
- `proof.artifact_closeout.primary_root_cause.reason=ros2_node_list_timeout`
- `proof.managed_runtime_wait_result.boundary=ros2_node_list_timeout`
- `graph_wait_summary.latest_ros2_node_list_timed_out=true`
- `graph_wait_summary.observed_node_names=[]`

AMCL/TF closeout 也已经保留在 final artifact 中：

- `amcl_param_probe_boundary=cli_amcl_inventory_observed_amcl_params`
- `amcl_param_probe_ok=true`
- `tf_topics_observed./tf=false`
- `tf_topics_observed./tf_static=false`
- `tf_source_root_cause_detail.reason=/tf_topic_missing`

因此本轮从“preflight 误判 / partial current_command”推进到“final artifact 明确 managed runtime graph wait timeout + AMCL CLI closeout”。这仍然是 blocked proof，不是 path generation 成功。

## 剩余风险

- true-board `ros2 node list` 在 managed runtime wait 内持续 timeout，graph 不可观测，下一轮应优先定位 ROS daemon/DDS graph discovery 或 shell-sourced `ros2 node list` 在 managed runtime 后卡住的原因。
- `/tf` 与 `/tf_static` 仍未观测，AMCL dynamic `map->odom` 与 `map->base_link` gate 未 ready。
- `map_lifecycle_proof_not_clean`、map_server/amcl lifecycle inactive、包可用性检查 missing 仍在 root causes 中，需要后续拆分确认是 graph timeout 继发问题还是 install/lifecycle 真实缺口。
- `path_generation_attempted=false`、`path_generated=false` 保持正确；本轮没有 route execution、没有 HIL、没有任何底盘控制。
