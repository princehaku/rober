# Tech Plan - O3 Daemon/DDS Graph Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target: split `ros2_daemon_or_dds_graph_discovery_timeout` into daemon, DDS/domain/env, lifecycle visibility, or graph budget candidates.

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective：O5，约 `85%`。
2. 本 sprint 不直接针对 O5。
3. 不针对 O5 的理由：O5 需要真实 production/external evidence，包括公网 HTTPS/TLS、4G/SIM、production DB/queue、worker/cutover、OSS/CDN live traffic、真实手机/browser 或真实 cloud/external readback。近期 O5 support-only、readback、wrapper、probe-only 和 readiness packet 已不允许继续计分。本轮可在当前环境推进的最低有效链路是 O3/O1 no-motion runtime graph / daemon / DDS / lifecycle gate；该链路直接解锁后续 same-run path generation、route execution 和 delivery evidence。

## Direction Judgment

- 继续：O3/O1 supporting no-motion runtime graph recovery。
- owner 切换：从 `robot-algorithm-engineer` 切到 `robot-software-engineer`，因为当前 blocker 是 ROS2 graph/daemon/DDS/runtime layer。
- 暂停：O5 support-only lane、O6/O7 独立 consumer surface。
- 不调整：计划阶段不调整 O1/O5/O6/O7 百分比。
- 不归档：计划阶段没有完成 KR；closeout 只有在新 mission artifact delta 出现时才重新评估。

## Engineer Assignment

主责：`robot-software-engineer`

单 owner 闭环。原因：文件范围集中在 ROS2 runtime helper、targeted tests、导航文档和本 sprint artifacts；不需要并行拆给其他 owner。

## Implementation Scope

允许 Robot Software 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/tech-done.md`
- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/`

不允许 Robot Software 修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- O5/O6/O7 cloud/workstation code
- WAVE ROVER UART、底盘控制、硬件配置
- 与本 root-cause artifact 无关的历史 sprint 文件

## Current Input Facts

上一轮 final live artifact：

- `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/artifacts/live_o10_source_amortized_graph_probe.raw.json`

关键事实：

- `status=blocked_with_root_cause`
- `artifact_kind=final`
- `current_command=null`
- `classification=ros2_daemon_or_dds_graph_discovery_timeout`
- `primary_candidate.reason=ros2_node_list_timeout`
- `evidence_priority=source_amortized_batch`
- `ros2_node_list.boundary=ros2_node_list_timeout`
- `ros2_node_list_no_daemon.boundary=ros2_node_list_no_daemon_timeout`
- `ros2_daemon_status.boundary=ros2_daemon_status_timeout`
- `ros2_node_list_help.boundary=ros2_node_list_help_ok`
- `ros2_topic_list.boundary=ros2_topic_list_timeout`
- `workspace_environment.boundary=workspace_environment_observed`
- `source_amortized_batch.boundary=source_amortized_batch_completed`
- source stage elapsed about `5984ms`
- rclpy graph stage stream observed `21` nodes
- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`

## Technical Plan

### 1. Add Daemon/DDS Split Contract

Extend `proof.ros2_graph_timeout_root_cause` with an additive split section, for example:

- `daemon_dds_split.schema=trashbot.o10.daemon_dds_graph_split.v1`
- `daemon_dds_split.primary_candidate`
- `daemon_dds_split.excluded_candidates`
- `daemon_dds_split.remaining_candidates`
- `daemon_dds_split.next_live_command`

Candidate names should be stable:

- `ros2_daemon_state_timeout`
- `dds_discovery_or_domain_mismatch`
- `workspace_source_or_env_mismatch`
- `managed_process_lifecycle_visibility_blocked`
- `graph_command_budget_insufficient`
- `ros2_cli_no_daemon_unsupported`

### 2. Probe Daemon State Without Motion

Inside the existing source-amortized batch or a new read-only batch, collect bounded summaries for:

- `ros2 daemon status`
- optional daemon-safe `ros2 daemon stop` then `ros2 daemon start` then graph command retry, only if existing helper precedent already supports daemon-safe retry and no motion side effects
- `ros2 node list` after daemon restart
- `ros2 topic list` after daemon restart
- daemon command return codes, elapsed time, timeout, stdout/stderr tail

If daemon restart is skipped, artifact must say why.

### 3. Probe DDS/Domain/Env

Record safe env summary only:

- `ROS_DOMAIN_ID`
- `RMW_IMPLEMENTATION`
- `ROS_DISTRO`
- `which ros2`
- compact `AMENT_PREFIX_PATH` / `PYTHONPATH` / `LD_LIBRARY_PATH` contains ROS and onboard workspace booleans
- managed process env comparison if available, without dumping full env or secrets

Classify DDS/domain/env as excluded only when the artifact shows compatible values; otherwise keep as remaining candidate with concrete next command.

### 4. Preserve Existing Artifact Schema

Do not delete or rename existing fields:

- `ros2_graph_timeout_root_cause.classification`
- `primary_candidate`
- `excluded_candidates`
- `remaining_candidates`
- `probes`
- `evidence_boundary`
- `source_amortized_batch`

All new fields must be additive and old tests/readers must still pass.

### 5. Documentation Sync

Update:

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

Docs must explain:

- daemon/DDS split reading order;
- which fields are safe summaries;
- how to interpret daemon reset success/failure;
- why no-motion diagnostic does not prove path generation, route execution, delivery, HIL, or production cloud.

## Interface Impact

- Artifact schema: additive daemon/DDS split section only.
- CLI: default helper behavior remains fail-closed.
- Safety: no movement, no base UART, no manual-control API.

## No-Motion Boundary

Must remain true:

- no `/cmd_vel`
- no `/api/base/manual`
- no NavigateToPose
- no WAVE ROVER UART
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_attempted=false`
- `path_generated=false`

## Verification Commands

Robot Software must run and write results to `tech-done.md`:

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

Local helper fail-closed dry-run:

```bash
python3 onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  --timeout-s 18 \
  --managed-timeout-s 60 \
  --managed-runtime-opt-in \
  --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml \
  --initialpose-opt-in \
  --path-generation-opt-in \
  --output sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/local_o10_daemon_dds_graph_split.raw.json
```

If true board is reachable, use the existing SSH/SCP pattern to push helper, execute the no-motion helper, and pull:

- `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/artifacts/live_o10_daemon_dds_graph_split.raw.json`
- stdout/stderr or incomplete artifact if command times out

Final scoped diff check:

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_03-52_o3_daemon_dds_graph_split
```

## Acceptance Gate

Product accepts this sprint only if one of these is true:

1. artifact excludes or confirms daemon state as the primary candidate;
2. artifact excludes or confirms DDS/domain/env mismatch as a remaining or primary candidate;
3. artifact proves managed lifecycle visibility remains blocked after graph split and gives the next live command;
4. artifact proves command budget is the blocker and records exact budgets used.

Product rejects this sprint if it only repeats:

- `ros2_node_list_timeout`
- `ros2_daemon_or_dds_graph_discovery_timeout`
- `source_amortized_batch_completed`
- `/tf_topic_missing`

without a new daemon/DDS/domain/env/lifecycle/budget split.

## Risks

- True board may be unreachable or slow; OKR percentage should not increase on local-only evidence.
- `ros2 daemon stop/start` may not be supported or may timeout; that is acceptable if safely recorded as a root-cause split, not hidden.
- DDS/domain mismatch may require system-level board access beyond helper scope; record next command instead of over-claiming.
- Even a successful split is only O3/O1 supporting diagnostic delta unless it leads to path generation or route execution proof.
