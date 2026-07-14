# Tech Plan - O3 Source-Amortized Graph Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Target: correct the graph timeout measurement layer by amortizing ROS/workspace source once per probe batch.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 需要真实 production/external evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或真实 cloud/external readback。近期 support-only、readback、wrapper、probe-only 和 readiness packet 已不允许继续计分。本轮可在当前环境推进的最低有效链路是 O3/O1 no-motion runtime graph / lifecycle / localization gate；该链路直接解锁后续 same-run path generation、route execution 和 delivery evidence。

## Direction Judgment

- 继续：O3/O1 supporting no-motion runtime graph root-cause diagnosis。
- 暂停：O5 support-only lane。
- 不调整：计划阶段不调整 O1/O5/O6/O7 百分比。
- 不归档：计划阶段没有完成 KR；closeout 只有在新 mission artifact delta 出现时才重新评估。

## Engineer Assignment

主责：`robot-algorithm-engineer`

单 owner 闭环。原因：文件范围集中在 Algorithm helper、Algorithm tests、导航文档和本 sprint artifacts，不需要并行拆给其他 owner。

## Implementation Scope

允许 Algorithm 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/tech-done.md`
- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/`

不允许 Algorithm 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 cloud/workstation code
- WAVE ROVER UART、底盘控制、硬件配置
- 与本 root-cause artifact 无关的历史 sprint 文件

## Current Input Facts

上一轮 live artifact 的关键事实：

- `board_source_preflight.source_stage.elapsed_ms` 约 5 秒
- `board_source_preflight.cli_invocation.command=ros2 --help >/dev/null`
- `board_source_preflight.cli_invocation.ok=true`
- `board_source_preflight.cli_invocation.elapsed_ms=4759`
- `board_source_preflight.rclpy_import_ok=true`
- `ros2_graph_timeout_root_cause.probes.ros2_node_list.timeout_s=2.5` 且 timeout
- `ros2_graph_timeout_root_cause.probes.ros2_node_list_help.timeout_s=5.0` 且 timeout
- `ros2_graph_timeout_root_cause.probes.workspace_environment.timeout_s=2.0` 且 timeout
- `ros2_graph_timeout_root_cause.probes.rclpy_graph_segments.timeout_s=4.0` 且 timeout
- `ros2_graph_timeout_root_cause.primary_candidate.reason=ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`

推断：逐条 `run_ros()` 重新 source ROS/workspace 可能污染 timeout 结论。本轮必须验证这个推断，而不是继续沿用上一轮 reason。

## Technical Plan

### 1. Add Source-Amortized Probe Batch

在 helper 中新增单次 sourced shell batch probe。建议字段：

- `ros2_graph_timeout_root_cause.probes.source_amortized_batch`

字段至少包含：

- `source_stage`：ROS setup、workspace setup、cd workdir 是否成功，耗时多少。
- `commands.ros2_node_list`
- `commands.ros2_node_list_no_daemon`
- `commands.ros2_daemon_status`
- `commands.ros2_node_list_help`
- `commands.ros2_topic_list`
- `workspace_environment.summary`
- `rclpy_graph_stage_stream`

每条 command 的 timeout 应是 command 自身预算，不包含 source 阶段。stdout/stderr 必须截断。

### 2. Stream rclpy Graph Stages

现有 `rclpy_graph_segment_probe_command()` 只在结束时打印 JSON，timeout 时 payload 为空。本轮改为或新增 stage-stream command：

- import start/done
- rclpy init start/done
- create node start/done
- graph wait start/done
- shutdown start/done

每个 stage 输出 JSONL 并 flush。timeout 时解析 partial stdout，写出 `last_completed_stage`、`last_started_stage`、`timed_out=true`、`boundary`。

### 3. Update Classification

`build_ros2_graph_timeout_root_cause()` 必须优先使用 source-amortized batch 结果：

- batched `ros2_node_list_help_ok` + graph commands timeout：优先 `ros2_daemon_or_dds_graph_discovery_timeout` 或 managed lifecycle remaining。
- batched `ros2_node_list_help_timeout` + stage-stream 在 import/init/create 前卡住：保留 `ros2_cli_plugin_or_import_timeout`，reason 要写具体 stage。
- batched source stage failed：主因可为 `workspace_source_or_env_mismatch`。
- graph blocked 时 `/tf_topic_missing` 继续是 secondary remaining candidate。

### 4. Preserve Existing Additive Schema

不能删除上一轮字段：

- `ros2_graph_timeout_root_cause.classification`
- `primary_candidate`
- `excluded_candidates`
- `remaining_candidates`
- `probes`
- `evidence_boundary`

新字段必须 additive，旧 consumer 不应破坏。

### 5. Documentation Sync

更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

说明 source-amortized batch 的读取顺序、字段含义和 no-motion 证据边界。

## Interface Impact

- Artifact schema：新增 additive source-amortized probe details。
- CLI：默认 helper 行为仍 fail-closed，不新增运动相关选项。
- Safety：无底盘控制接口影响，不触发 UART、`/cmd_vel`、`/api/base/manual` 或 NavigateToPose。

## No-Motion Boundary

必须严格满足：

- 不发布 `/cmd_vel`
- 不调用 `/api/base/manual`
- 不发送 NavigateToPose
- 不打开 WAVE ROVER UART
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generated=false`

## Verification Commands

Algorithm 必须运行并在 `tech-done.md` 写入结果：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

本地 helper fail-closed dry-run，输出到新 sprint artifacts：

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/local_o10_source_amortized_graph_probe.raw.json
```

如果真板可达，按既有 SSH/SCP 模式推送 helper、执行 no-motion helper、拉回 live artifact；必须不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART。

建议 live artifact 文件名：

- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`

最终 scoped diff check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_02-51_o3_source_amortized_graph_probe
```

## Acceptance Gate

Product 后续验收只接受以下形式之一：

1. source-amortized evidence 证明上一轮 per-command timeout 受 source overhead 污染，并给出新的 root-cause 分类。
2. source-amortized evidence 证明 subcommand help / rclpy graph 在单次 source 后仍 timeout，并定位到具体 stage 或候选。
3. 仍未唯一归因，但 artifact 输出新的 source-amortized `root_cause_unclassified_after_probe`，并列出已排除和未排除候选。

不接受：

- 只重复 `ros2_node_list_timeout`。
- 只重复 `ros2_node_list_help_timeout_and_rclpy_graph_segment_probe_timeout`。
- 只重复 `/tf_topic_missing`。
- 只输出 partial `current_command=ros2 node list`。
- 没有 no-motion false fields。
- 把 helper/readback/checklist 当成 path generation、route execution、delivery、HIL 或 production evidence。

## Risks

- 真板可能不可达或 SSH/SCP 失败；届时只能保留 local fail-closed 证据，OKR 不上调。
- 新 probe 可能暴露上一轮分类受测量方式影响；应按证据修正，不视为倒退。
- 即使 source-amortized probe 成功定位，仍可能只是 O3/O1 supporting diagnostic delta，不能证明 path generation 或 delivery success。
