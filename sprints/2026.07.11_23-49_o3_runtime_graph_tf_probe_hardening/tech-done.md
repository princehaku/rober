# O3 Runtime Graph TF Probe Hardening Tech Done

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/`
- Owner: `robot-algorithm-engineer`
- Finished at: `2026-07-12 00:04 CST`
- Scope boundary: strict no-motion localization/path readiness proof only. No `/cmd_vel`, no `/api/base/manual`, no NavigateToPose, no WAVE ROVER UART, no O5/O6/O7/UI/cloud changes.

## 自主能力目标和本轮抓手

本轮目标不是再包一层 `22-48` 的 same blocker，而是把 two-step graph/source probing
真正写进 helper：

1. `rclpy_node_names()` 在 child Python timeout / parse failure 后继续读 `ros2 node list`；
2. `collect_amcl_rclpy_probe()` 在 rclpy import/runtime failure 后继续回收 CLI inventory；
3. 保持 strict no-motion gate，不让 `path_generation_attempted` 越界变成 true。

## 改动文件和接口影响

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - `rclpy_node_names()` 新增 `ros2 node list` fallback，artifact 新增 `fallback_used`、`fallback.boundary` 和组合 boundary。
  - 新增 `collect_amcl_cli_probe()`、`cli_amcl_param_probe()`、`cli_topic_endpoint_summary()`，在 rclpy failure 时保留 `/tf`、`/tf_static`、`/amcl` 的 CLI inventory。
  - `collect_amcl_rclpy_probe()` 新增 `probe_mode`、`fallback_boundary`、`param_probe_boundary`、`rclpy_import_failure_classification` 等结构化字段。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 新增 node graph fallback 回归测试。
  - 新增 AMCL/TF CLI fallback 与 root-cause 收窄测试。
- `docs/navigation/field_route_evidence_preflight.md`
  - 补充 `ros2 node list` fallback 与 AMCL CLI inventory fallback 的 closeout 读取规则。
- `docs/navigation/fixed_route_workflow.md`
  - 补充 true-board latest/partial 里如何读取 fallback boundary，而不是继续把 blocker 写成旧 `rclpy_node_names_failed` 或泛化 `/tf_topic_missing`。
- `sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/artifacts/`
  - 新增本机 fail-closed artifact。
  - 新增真板 partial live artifact。

接口影响：只扩展 no-motion proof artifact 的 graph/source diagnostic 字段，不改变安全合同。
`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、
`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、
`hil_pass=false`、`uses_base_uart=false` 继续固定 false。`path_generation_requested=true`
但 gate 未 ready 前继续保持 `path_generation_attempted=false`。

## 实现内容

### 1. managed runtime graph probe 增加 CLI fallback

旧逻辑里一旦 sourced child Python node graph probe timeout，就只留下
`rclpy_node_names_failed` 或 parse failure。现在 helper 会继续执行 `ros2 node list`：

- 如果 CLI graph 能看到节点，boundary 会写成
  `rclpy_node_names_failed_with_ros2_node_list_fallback_observed` 这类组合边界；
- 如果 CLI 也失败，boundary 会继续带上 `ros2_node_list_timeout`、
  `ros2_node_list_failed` 或 `ros2_node_list_empty_after_wait`；
- `fallback_used=true` 固定写回 artifact，避免 closeout 看不出第二层 probe 是否真的执行。

### 2. AMCL/TF source probe 增加 CLI inventory fallback

旧逻辑里 `collect_amcl_rclpy_probe()` 只要被 `librcl_action.so`、
`_rclpy_pybind11` 或其他 runtime/import 问题打断，就只能回 `rclpy_amcl_probe_failed`。
现在 helper 会在异常后继续做：

- `ros2 topic list -t`
- `ros2 node info /amcl`
- `ros2 topic info /tf --verbose`
- `ros2 topic info /tf_static --verbose`
- `ros2 param get /amcl <key>`（best-effort）

artifact 因此新增：

- `probe_mode=ros2_cli_fallback`
- `fallback_used=true`
- `fallback_boundary=cli_amcl_inventory_*`
- `param_probe_boundary`
- `rclpy_import_failure_classification`

这样 `/tf` topic 已可见但参数仍缺时，closeout 可以收口成 `amcl_param_probe_failed`，
不必继续写死 `/tf_topic_missing`。

## 测试、dry-run 或上车验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

- Exit code: `0`

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

- Exit code: `0`
- 关键输出：

```text
Ran 77 tests in 2.220s
OK
```

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/artifacts/local_o10_runtime_graph_tf_probe_hardening.raw.json
```

- Exit code: `2`
- 本机预期 fail-closed：缺 `/opt/ros/humble/setup.bash` 与 `/root/rober/onboard/install/setup.bash`。
- 关键字段：
  - `board_source_preflight.classification=board_source_preflight_source_failed`
  - `managed_runtime_started=false`
  - `tf_source_probe.boundary=ros2_cli_unavailable_tf_source_probe_skipped`
  - `path_generation_requested=true`
  - `path_generation_attempted=false`
  - `path_generated=false`

```bash
scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py
ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && python3.10 scripts/o10_amcl_nav2_runtime_proof.py --timeout-s 18 --managed-timeout-s 60 --managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml --initialpose-opt-in --path-generation-opt-in --output /root/rober/onboard/runtime/live_o10_runtime_graph_tf_probe_hardening.raw.json'
scp -P 37878 root@192.168.1.11:/root/rober/onboard/runtime/live_o10_runtime_graph_tf_probe_hardening.raw.json sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening/artifacts/live_o10_runtime_graph_tf_probe_hardening.raw.json
```

- 第一次 `scp` push exit code: `0`
- 真板 helper 在 no-motion 运行中被人工中断回收 partial artifact，未自然退出 final closeout。
- 回收后的 live artifact 为 `partial_runtime_in_progress`，但已出现新的 fallback delta：
  - `board_source_preflight.classification=board_source_preflight_ready`
  - `board_source_preflight.cli_ready=true`
  - `board_source_preflight.runtime_ready=true`
  - `managed_runtime_started=true`
  - `last_phase=managed_runtime_started`
  - `current_command.command=ros2 node list`
  - `recent_commands[*].command` 交替出现 child Python graph probe 与 `ros2 node list`
  - `recent_commands[*].error.type=TimeoutExpired`，证明 fallback 已进入 true-board 执行链
  - `path_generation_requested=true`
  - `path_generation_attempted=false`
  - `path_generated=false`

```bash
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.11_23-49_o3_runtime_graph_tf_probe_hardening
```

- Exit code: `0`

## 数据、样本或调试输出变化

- `artifacts/local_o10_runtime_graph_tf_probe_hardening.raw.json`
  - 本机 fail-closed 样本，证明新字段没有破坏 no-motion 收口，且 `path_generation_attempted=false` 仍保持。
- `artifacts/live_o10_runtime_graph_tf_probe_hardening.raw.json`
  - 真板 partial artifact，证明：
    - helper 仍能到达 `board_source_preflight_ready`、`managed_runtime_started=true`
    - `rclpy_node_names()` 的 child Python probe 超时后，CLI fallback `ros2 node list` 确实被触发
    - 当前仍未到 TF source / AMCL CLI fallback 收口阶段，说明 blocker 继续前移到 graph wait 时间窗口本身

## 失败定位

1. **真板 helper 这次没有自然退出 final closeout**
   - live artifact 停在 `partial_runtime_in_progress`
   - `last_phase=managed_runtime_started`
   - 当前命令卡在 `ros2 node list`
2. **graph wait 仍然是第一层真实 blocker**
   - `recent_commands` 显示 child Python graph probe 与 `ros2 node list` 都在 6s 窗口内 timeout
   - 说明这轮已经不再是“fallback 没执行”，而是“fallback 也执行了，但 graph discovery 自身仍卡住”
3. **AMCL CLI fallback 代码已覆盖并通过单测，但 live 本轮还没跑到该阶段**
   - 因为 managed runtime wait 尚未结束，partial artifact 里还没有 `amcl_rclpy_probe.probe_mode`
   - 这属于 live runtime 时间窗口不足，不是 helper 逻辑缺失

## 与 22-48 相比是否产生新的 artifact delta

是，产生了新的 artifact delta，但仍属于 no-motion partial/live diagnostic delta，不是
path proof、route execution、HIL 或 delivery delta。

### 22-48 live 关键字段

- `managed_runtime_started=true`
- `managed_runtime_wait_result.reason=managed_runtime_wait_timeout`
- `managed_runtime_wait_result.history[*].node_list.boundary=rclpy_node_names_failed`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- `path_generation_attempted=false`
- `path_generated=false`

### 23-49 live 新增/变化字段

- `current_command.command=ros2 node list`
- `recent_commands[*].command` 新增 `ros2 node list`
- `recent_commands[*].command` 保留 child Python node graph probe
- `recent_commands[*].error.type=TimeoutExpired`
- `last_phase=managed_runtime_started`
- `managed_runtime_started=true`
- `path_generation_attempted=false`
- `path_generated=false`
- 所有 no-motion safety/control/HIL/delivery 字段继续为 false

这表示本轮把 “旧 `rclpy_node_names_failed` 之后没有第二层 graph 事实” 推进成了
“真板上第二层 `ros2 node list` fallback 已实际执行，只是它同样 timeout”。
这是比 22-48 更窄的 runtime graph blocker。

## 剩余风险和下一步能力建设建议

- 这轮 live 仍未拿到 final `managed_runtime_wait_result`，因此还不能声称已把 blocker 收口到
  `ros2_node_list_timeout` 的最终字段层。
- AMCL CLI fallback 虽已实现并通过回归测试，但还需要一次 true-board final artifact 才能证明
  `probe_mode=ros2_cli_fallback` 与 `amcl_param_probe_failed` 的现场收口。
- `path_generation_requested=true` 继续只是 request，不是 attempt；gate ready 前必须继续保持
  `path_generation_attempted=false`。

下一轮最小建议：

1. 继续由 `robot-algorithm-engineer` 单线闭环。
2. 优先把 true-board graph wait 收口到 final `managed_runtime_wait_result`，确认最终是
   `ros2_node_list_timeout`、`ros2_node_list_empty_after_wait` 还是 CLI graph 终于可见。
3. 只有 graph wait 能自然结束后，再消费 AMCL CLI fallback，验证 `/tf`、`/tf_static`、
   `/amcl` inventory 是否能把 root cause 从泛化 `/tf_topic_missing` 进一步收紧到
   `amcl_param_probe_failed`、`amcl_node_info_not_observed` 或 `amcl_map_to_odom_tf_not_observed_on_tf`。

## no-motion invariant check

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_requested=true`
- `path_generation_attempted=false`
- `path_generated=false`
