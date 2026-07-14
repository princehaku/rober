# Side-to-Side Check - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 07:31 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`
- Product result: accepted as O3/O1 supporting no-motion diagnostic delta; not accepted as mission progress.

## 用户价值和产品北极星

用户价值是把 true-board helper 主路径从“`ros2 --help` 单点硬 gate 卡死 readiness”推进到“`board_source_preflight_ready` 已成立，helper 能以 lightweight CLI readiness 进入 lifecycle/topic probes”。北极星仍是普通手机用户一键固定路线送垃圾；本轮只是 runtime 诊断门槛前移，不是路径执行、送达或 production 闭环。

## 计划口径对照

- 计划要求：不要再把 `ros2 --help` 当唯一硬 gate，要把 heavy/light/`rclpy` 三层 readiness 分开。
- 实际结果：true-board `330s` artifact 证明 `board_source_preflight.classification=board_source_preflight_ready`、`source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
- 计划要求：如果仍 blocked，必须把 blocker 收窄到 downstream runtime/lifecycle/topic 层，而不是继续停在 source/path mismatch 或 `ros2 --help`。
- 实际结果：latest final blocker 已前移到 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/tf_topic_missing`，并显式暴露 `/scan_no_publisher` 与 `/map_once_not_observed` 类 downstream no-motion blocker。
- 计划要求：240s true-board 验收若不足以自然收口，仍要给出结构化 artifact 证明是否已穿过 readiness。
- 实际结果：240s artifact 虽为 `status=interrupted_before_final_artifact`，但已明确 `lightweight_readiness.primary_label=ros2_node_list`，`cli_ready=true`、`runtime_ready=true`，且 `recent_commands` 已进入 lifecycle/topic probes。
- 计划要求：no-motion false fields 不得漂移。
- 实际结果：`path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## Artifact 对照

### Local dry-run

- Artifact: `artifacts/local_lightweight_cli_readiness_dry_run.raw.json`
- `status=blocked_with_root_cause`
- `classification=board_source_preflight_source_failed`
- `lightweight_cli_ready=false`
- `cli_ready=false`
- `runtime_ready=false`
- Product judgment: accepted only as macOS fail-closed proof, not as board/runtime proof.

### True-board 240s

- Artifact: `artifacts/live_o10_lightweight_cli_readiness.raw.json`
- `status=interrupted_before_final_artifact`
- `classification=board_source_preflight_ready`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
- `ros2_cli_invocation_ok=false`
- `cli_ready=true`
- `runtime_ready=true`
- `recent_commands` 已进入 `ros2 lifecycle get /map_server`、`ros2 lifecycle get /amcl`、`/scan` probes
- Product judgment: accepted as true-board readiness gate passed; not accepted as final blocker closeout because outer 240s timeout打断收口。

### True-board 330s

- Artifact: `artifacts/live_o10_lightweight_cli_readiness_330s.raw.json`
- `status=blocked_with_root_cause`
- `classification=board_source_preflight_ready`
- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `lightweight_cli_ready=true`
- `lightweight_readiness.primary_label=ros2_node_list`
- `lightweight_readiness.successful_labels=["ros2_node_list"]`
- `lightweight_readiness.timed_out_labels=["ros2_daemon_status"]`
- `ros2_cli_invocation_ok=false`
- `cli_ready=true`
- `runtime_ready=true`
- `map_lifecycle_preflight.classification=map_lifecycle_preflight_map_server_and_amcl_inactive`
- `amcl_readiness_summary.blocked_reason=amcl_lifecycle_not_active`
- `tf_readiness_summary.blocked_reason=/tf_topic_missing`
- Product judgment: accepted as the canonical closeout boundary for this sprint; not accepted as localization/path proof.

## Blocker 重复消费判断

本轮不按与 `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/` 相同 blocker 处理。

理由：

- `05-52` 的 primary blocker 仍是 `board_source_preflight_ros2_cli_invocation_timeout`，`cli_ready=false`、`runtime_ready=false`。
- `06-54` 已把 heavy help 降为诊断项，true-board canonical artifact 明确 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
- 新 primary blocker 已前移到 `map_server/amcl inactive`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`，helper 已实际进入 lifecycle/topic probes。

下一轮不得回到 O5 support-only、source/path mismatch 或 `ros2 --help` 单点 gate；应直接打 downstream runtime/lifecycle/topic blocker。

## OKR 与验收结论

- O5：约 `85%`，`不调整`。本轮没有 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL、safe-to-control 或底盘控制执行。
- O6/O7：约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或 mission material。
- KR：`不归档`。没有完成可归档 KR。

Product acceptance: accepted with conservative boundary. This sprint is O3/O1 supporting no-motion diagnostic delta only; it is not same-run path generation, route execution, delivery/operator acceptance, HIL, safe-to-control, or production cloud evidence.
