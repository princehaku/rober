# Tech Plan - O3 ROS2 Graph Timeout Root Cause

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Target: split final `ros2_node_list_timeout` into lower-level no-motion root-cause evidence.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 当前需要真实 production/external evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或真实 cloud/external readback。近期 support-only、readback、wrapper、probe-only 和 readiness packet 已不允许继续计分。本轮可在当前环境推进的最低有效链路是 O3/O1 no-motion runtime graph / TF root-cause isolation；该链路直接解锁后续 fixed route path generation、route execution 和 delivery evidence。

## Direction Judgment

- 继续：O3/O1 supporting no-motion runtime graph / TF diagnosis。
- 暂停：O5 support-only lane。
- 不调整：O1/O5/O6/O7 百分比。
- 不归档：本轮计划阶段没有完成 KR；后续只有新 mission artifact delta 才能重新评估。

## Engineer Assignment

主责：`robot-algorithm-engineer`

单 owner 闭环。原因：本轮文件范围集中在 Algorithm helper、Algorithm tests、导航文档和 sprint artifact，不需要并行拆给其他 owner。

## Implementation Scope

允许 Algorithm 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/tech-done.md`
- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/`

不允许本 sprint Algorithm 修改：

- `OKR.md`
- O5/O6/O7 cloud/workstation code
- WAVE ROVER UART、底盘控制、硬件配置
- 与本 root-cause artifact 无关的历史 sprint 文件

## Current Input Facts

Algorithm 必须从上一轮 final artifact 继续，而不是重新消费旧 blocker：

- `ros2_node_list_timeout`
- `/tf_topic_missing`
- `board_source_preflight_ready`
- `ros2_cli_invocation_ok=true`
- `rclpy_import_ok=true`
- `managed_runtime_started=true`
- `graph_wait_summary.observed_node_names=[]`
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`

## Technical Plan

### 1. Add Graph Timeout Root-Cause Contract

在 helper artifact 中增加 root-cause split 字段，建议命名：

- `ros2_graph_timeout_root_cause.classification`
- `ros2_graph_timeout_root_cause.primary_candidate`
- `ros2_graph_timeout_root_cause.excluded_candidates`
- `ros2_graph_timeout_root_cause.remaining_candidates`
- `ros2_graph_timeout_root_cause.probes`
- `ros2_graph_timeout_root_cause.evidence_boundary`

分类至少包括：

- `ros2_daemon_or_dds_graph_discovery_timeout`
- `ros2_cli_plugin_or_import_timeout`
- `workspace_source_or_env_mismatch`
- `managed_process_lifecycle_not_ready`
- `tf_runtime_secondary_after_graph_blocked`
- `root_cause_unclassified_after_probe`

### 2. Split ROS Daemon / DDS Graph Discovery

在 sourced shell 下执行低预算 graph discovery probes，记录每个 probe 的 command、timeout、returncode、stdout/stderr 摘要和 boundary。

建议 probe：

- `ros2 node list` 当前路径，保留上一轮语义。
- `ros2 node list --no-daemon`，如当前 ROS2 CLI 不支持该参数，则记录 `unsupported_option`，不要当作失败。
- `ros2 daemon status` 或等价 daemon read-only probe，用于区分 daemon 层异常与 DDS discovery 层异常。
- child Python rclpy graph probe，继续记录 import、init、node create、graph wait 的分段耗时。

验收重点：artifact 能说明是 daemon/DDS graph discovery 更可疑，还是 CLI/managed lifecycle 更可疑。

### 3. Split ROS2 CLI Plugin / Import Runtime

在不触发运动的前提下，增加短预算 CLI/plugin probes：

- `ros2 node list --help` 或等价 help probe。
- `ros2 topic list` 短预算 probe，用来判断是否只有 node graph 卡住。
- 捕获 `librcl_action.so`、`_rclpy_pybind11`、Python import、entrypoint loading、plugin import stderr。

如果 `ros2 --help` 可用、`rclpy_import_ok=true`，但 `ros2 node list` 独立 timeout，则不要回退成旧的 source/import blocker，必须写成更窄分类或未排除项。

### 4. Split Workspace Source / Environment Mismatch

记录 sourced shell 的最小环境摘要：

- `ROS_DISTRO`
- `ROS_DOMAIN_ID`
- `RMW_IMPLEMENTATION`
- `AMENT_PREFIX_PATH` 是否包含 `/ws/install` 或板端实际 workspace install。
- `PYTHONPATH` 是否包含 ROS/site-packages 和 workspace。
- `LD_LIBRARY_PATH` 是否包含 ROS/lib 和 workspace lib。
- `which ros2`
- `python3 -c "import rclpy"` 短预算结果。

只记录摘要和 basename/短路径，不泄露无关环境变量或凭证。

### 5. Split Managed Process Lifecycle

如果 `managed_runtime_started=true` 但 graph 空或 timeout，artifact 必须记录：

- managed process start command 摘要。
- process 是否仍存活。
- 最近 stdout/stderr tail 摘要。
- map_server / amcl lifecycle probe 是否实际执行，若因 graph timeout 被跳过，写明 skipped boundary。
- expected nodes 与 observed nodes 的差异。

如果 lifecycle probe 不能执行，不要写成 `map_server_active=false` 的强结论；应写成 `lifecycle_probe_skipped_after_ros2_graph_timeout` 或等价字段。

### 6. Keep TF Runtime Secondary Clear

继续保留 `/tf_topic_missing` 与 `/tf_static` observation，但必须明确：

- 如果 graph wait 已 blocked，TF probe 是 secondary/skipped/readback，不是主因。
- 如果 graph probe 恢复且 `/tf` 仍缺失，再把 root cause 继续转向 TF runtime。

### 7. Preserve Fail-Closed Final Artifact

helper 必须自然写出 final artifact：

- `status=blocked_with_root_cause` 或更具体 fail-closed 状态。
- `artifact_kind=final`
- `current_command=null`
- `path_generation_attempted=false`
- `path_generated=false`
- no-motion booleans 全部 false。

不得再次留下 partial `current_command=ros2 node list` 作为唯一结论。

## Interface Impact

- Artifact schema：新增 additive root-cause fields，不能破坏旧 consumer 字段。
- Existing fields：继续保留 `managed_runtime_wait_result`、`graph_wait_summary`、`tf_source_root_cause_detail`、`tf_topics_observed`、安全字段和 path fields。
- CLI：允许增加 helper 内部 probe 选项或 artifact 字段；默认行为必须 fail-closed。
- Docs：导航文档需要记录 root-cause split 字段和 no-motion 边界。
- Safety：无底盘控制接口影响。

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

本地 helper fail-closed dry-run，输出到新 sprint artifacts 下。建议命令：

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

如果真板可达，按既有 SSH/SCP 模式推送 helper、执行 no-motion helper、拉回 live artifact；必须不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 NavigateToPose，不打开 WAVE ROVER UART。

建议 live artifact 文件名：

- `sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause/artifacts/live_o10_ros2_graph_timeout_root_cause.raw.json`

最终 scoped diff check：

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_01-50_o3_ros2_graph_timeout_root_cause
```

## Acceptance Gate

Product 后续验收只接受以下形式之一：

1. `ros2_node_list_timeout` 被进一步归类到 ROS daemon/DDS、CLI/import、workspace source、managed lifecycle 或 TF/runtime secondary 中的一个主因，并给出 supporting probes。
2. 仍未唯一归因，但 artifact 明确输出 `root_cause_unclassified_after_probe`，且列出已排除和未排除候选。

不接受：

- 只重复 `ros2_node_list_timeout`。
- 只重复 `/tf_topic_missing`。
- 只输出 partial `current_command=ros2 node list`。
- 没有 no-motion false fields。
- 把 helper/readback/checklist 当成 path generation、route execution、delivery、HIL 或 production evidence。

## Risks

- 真板 SSH 或 helper 可能不可达；如果发生，Algorithm 必须写清本地 fail-closed 证据边界和 live 缺口。
- ROS2 CLI `--no-daemon` 可能在当前版本不可用；该情况必须记录为 unsupported，而不是失败。
- graph timeout 可能同时由 DDS discovery 和 managed lifecycle 引起；artifact 必须列出 primary/remaining candidates。
- O5 仍约 `85%` 且最低，但没有 external production evidence，本轮不应改回 O5 support-only。

## Required Output From Algorithm

Algorithm 完成后必须返回：

1. 实际改动的文件列表。
2. 验证命令输出结果，包括 unittest、local dry-run、live artifact 或 live 不可达原因。
3. 失败定位。
4. 剩余风险。
5. 新 artifact 中 root-cause split 字段的关键摘录。
