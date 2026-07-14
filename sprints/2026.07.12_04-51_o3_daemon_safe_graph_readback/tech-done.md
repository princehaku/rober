# Tech Done - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Implementation owner: `robot-software-engineer`
- Correction pass time: `2026-07-12 05:32 CST`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## 修正结论

验收指出的问题成立：上一版 `tech-done.md` 把 live helper artifact 写成
`managed_process_lifecycle_not_ready`、`dds_discovery_or_domain_mismatch` 和
`daemon_safe_retry_summary_missing_from_batch`，这不符合验收时实际 artifact。验收时 artifact
事实是：

- `proof.board_source_preflight.classification=board_source_preflight_source_timeout`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_source_timeout`
- `daemon_dds_split.primary_candidate.candidate=workspace_source_or_env_mismatch`
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`
- `daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`

本修正 pass 做了一个低风险 helper 修复：把 `SOURCE_PREFLIGHT_TIMEOUT_S` 从 `8.0` 放宽到
`12.0`，因为实际 source stage 在 `8040ms` 被 8 秒边界切断。复跑 true-board helper 后，
source timeout 已被越过，但 latest helper artifact 仍 fail-closed，最新事实变为：

- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`
- `proof.board_source_preflight.source_stage_timeout_s=12.0`
- `proof.board_source_preflight.commands.source_stage.elapsed_ms=9223`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout`
- `daemon_dds_split.primary_candidate.candidate=workspace_source_or_env_mismatch`
- `daemon_dds_split.primary_candidate.reason=board_source_preflight_cli_not_ready`
- `daemon_safe_graph_readback.reset_attempted=false`
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`
- `daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`

因此 helper artifact 仍 blocked 在 source/CLI preflight 层，不能包装成 helper 已结构化证明
daemon-safe graph readback 恢复。

## 实际改动

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
  - 保留上一轮新增的 additive `daemon_safe_graph_readback` 合同、8s node/topic retry budget、
    whole-stdout batch parse fallback 和 no-motion boundary。
  - 本修正 pass 追加低风险修复：`SOURCE_PREFLIGHT_TIMEOUT_S=12.0`，避免 true-board source
    stage 8 秒边界抖动被误判成 `board_source_preflight_source_timeout`。
- `onboard/tests/test_nav2_runtime_proof_helper.py`
  - 更新 preflight timeout 断言为 `12.0`。
- `docs/navigation/field_route_evidence_preflight.md`
  - 保留 `daemon_safe_graph_readback` 读取顺序说明。
- `docs/navigation/fixed_route_workflow.md`
  - 保留 fixed-route/no-motion closeout 对 `daemon_safe_graph_readback` 的读取边界。
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/`
  - `live_o10_daemon_safe_graph_readback.raw.json` 已被修正后 true-board helper 复跑结果覆盖。
  - `live_daemon_safe_graph_readback_manual.summary.json` 与 stdout/stderr log 保留 strict no-motion
    manual readback 事实。

## 验证结果

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
```

结果：通过，无输出。

```bash
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper
```

结果：通过，`Ran 94 tests in 2.238s OK`。

true-board helper 修正后复跑：

- `scp -P 37878 onboard/scripts/o10_amcl_nav2_runtime_proof.py root@192.168.1.11:/root/rober/onboard/scripts/o10_amcl_nav2_runtime_proof.py` exit `0`
- `ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && /usr/bin/timeout 240s /usr/bin/python3.10 scripts/o10_amcl_nav2_runtime_proof.py ...'` exit `2`
- artifact 拉回 exit `0`

修正后 latest helper artifact：

- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.board_source_preflight.classification=board_source_preflight_ros2_cli_which_timeout`
- `proof.ros2_graph_timeout_root_cause.classification=workspace_source_or_env_mismatch`
- `proof.ros2_graph_timeout_root_cause.primary_candidate.reason=board_source_preflight_ros2_cli_which_timeout`
- `daemon_dds_split.primary_candidate.candidate=workspace_source_or_env_mismatch`
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`
- `daemon_safe_graph_readback.primary_conclusion=daemon_reset_not_executed`
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

manual same-run readback 仍是有效证据，但边界必须写清：

- `live_daemon_safe_graph_readback_manual.summary.json`
- `primary_conclusion=manual_daemon_safe_graph_readback_recovered_graph_visibility`
- `ros2 daemon status`、`ros2 daemon stop`、`ros2 daemon start` 均 `RC=0`
- `timeout 8 ros2 node list` 为 `RC=0`，观测到 `/amcl`、`/planner_server`、`/scan` 对应运行链路节点
- `timeout 8 ros2 topic list` 为 `RC=0`，观测到 `/amcl_pose`、`/map`、`/scan`、`/tf`、`/tf_static`
- `/cmd_vel` 只是 topic graph 可见，不代表发布过运动命令

manual readback 只能证明 strict no-motion daemon-safe graph visibility 恢复；不能说 helper artifact
已经结构化恢复，也不能说 lifecycle/localization/path 已 ready。

修正 pass 验收命令：

```bash
rg -n "board_source_preflight_source_timeout|workspace_source_or_env_mismatch|manual_daemon_safe_graph_readback_recovered_graph_visibility|skipped_without_sourced_ros2_cli_ready|path_generation_attempted=false|safe_to_control=false|Ran 94" \
  sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/tech-done.md \
  sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_o10_daemon_safe_graph_readback.raw.json \
  sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/live_daemon_safe_graph_readback_manual.summary.json
```

结果：通过。关键命中包括：

- `tech-done.md` 命中 `board_source_preflight_source_timeout`、`workspace_source_or_env_mismatch`、
  `skipped_without_sourced_ros2_cli_ready`、`path_generation_attempted=false`、`safe_to_control=false`
  和 `Ran 94 tests in 2.238s OK`。
- `live_o10_daemon_safe_graph_readback.raw.json` 命中 `workspace_source_or_env_mismatch` 与
  `skipped_without_sourced_ros2_cli_ready`。
- `live_daemon_safe_graph_readback_manual.summary.json` 命中
  `manual_daemon_safe_graph_readback_recovered_graph_visibility`。

```bash
git diff --check -- \
  onboard/scripts/o10_amcl_nav2_runtime_proof.py \
  onboard/tests/test_nav2_runtime_proof_helper.py \
  docs/navigation/field_route_evidence_preflight.md \
  docs/navigation/fixed_route_workflow.md \
  sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback
```

结果：通过，无输出。

## 失败定位

- helper 修正前：`board_source_preflight_source_timeout`，source stage 在 8 秒边界附近被切断。
- helper 修正后：source stage 可越过 8 秒边界，但 `ros2_cli_which` 层仍 timeout，artifact 继续
  fail-closed 到 `workspace_source_or_env_mismatch`。
- manual readback 证明同一真板上手工 source 后 daemon-safe graph readback 可成功；因此现场 graph
  本身不是当前唯一 blocker，helper 的 source/CLI preflight 仍有时序或预算漂移。

## 剩余风险

- 还没有把 manual daemon-safe readback 完整结构化进 helper artifact；latest helper artifact 仍是
  `workspace_source_or_env_mismatch`。
- source preflight timeout 已从 8s 推到 12s，但 CLI path/which 层仍有 timeout；下一轮需要继续把
  source 与 CLI path lookup 放进同一个 amortized shell，减少重复 source 和 shell 启动抖动。
- 本轮仍无 same-run path generation success、route execution、delivery/operator acceptance、HIL 或
  production external evidence，不能上调 OKR 或归档 KR。

## 协同需求

- Product：closeout 时应写成 helper artifact 仍 blocked 在 source/CLI preflight，而 manual readback
  证明 daemon-safe graph visibility 恢复。
- Autonomy / Robot Software：下一轮应继续修 helper source/CLI preflight 接线，随后回到
  lifecycle/localization gate。
- Hardware：未触碰 WAVE ROVER UART、底盘控制或硬件配置，无需介入。
- Full-Stack：无协同需求。
