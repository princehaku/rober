# Side-to-Side Check - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 06:25 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`
- Product result: accepted as O3/O1 supporting no-motion diagnostic delta; not accepted as mission progress.

## 用户价值和产品北极星

用户价值是把真实板 helper 主路径从“source/path lookup 还不可信”推进到“source、path lookup、`rclpy` import 已在同一个 sourced shell 中通过，下一跳收窄为 ROS2 CLI invocation timeout”。北极星仍是普通手机用户一键固定路线送垃圾；本轮只修进入定位/路径门前的诊断前置条件，不是路线执行或送达闭环。

## 计划口径对照

- 计划要求：把 source、ROS2 path lookup、CLI readiness 和目标 CLI invocation 放进同一个 amortized shell。
- 实际结果：true-board live artifact 证明 `source_and_cli_in_one_shell=true`、`per_command_source_overhead_eliminated=true`、`source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`。
- 计划要求：若仍 blocked，必须给出比 `workspace_source_or_env_mismatch` 更窄的下一跳。
- 实际结果：新的主分类为 `board_source_preflight_ros2_cli_invocation_timeout`，`cli_invocation.command="ros2 --help >/dev/null"` 在 `6.0s` budget 内 timeout；`cli_ready=false`、`runtime_ready=false`。
- 计划要求：local dry-run 必须 fail-closed。
- 实际结果：local artifact 为 `classification=board_source_preflight_source_failed`，符合 macOS 缺 `/opt/ros/humble/setup.bash` 的预期 fail-closed 边界。
- 计划要求：no-motion false fields 不得漂移。
- 实际结果：`path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## Artifact 对照

### Local dry-run

- Artifact: `artifacts/local_source_amortized_cli_preflight_dry_run.raw.json`
- `status=blocked_with_root_cause`
- `classification=board_source_preflight_source_failed`
- `source_and_cli_in_one_shell=true`
- `per_command_source_overhead_eliminated=false`
- `cli_ready=false`
- `runtime_ready=false`
- Product judgment: accepted only as local fail-closed proof, not as board/runtime proof.

### True-board live

- Artifact: `artifacts/live_o10_source_amortized_cli_preflight.raw.json`
- `status=blocked_with_root_cause`
- `board_source_preflight.source_amortized_cli_preflight_schema=trashbot.o10.source_amortized_cli_preflight.v1`
- `source_and_cli_in_one_shell=true`
- `per_command_source_overhead_eliminated=true`
- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `ros2_cli_invocation_ok=false`
- `cli_ready=false`
- `runtime_ready=false`
- `classification=board_source_preflight_ros2_cli_invocation_timeout`
- Additional blocker: `map_lifecycle_proof_not_clean`
- Product judgment: accepted as narrower true-board blocker; not accepted as localization/path proof.

## Blocker 重复消费判断

本轮不按与 `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/` 相同 blocker 处理。

理由：

- `04-51` 的 helper 主因仍是 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`，且 manual readback 只证明 graph visibility 可恢复。
- `05-52` 已在同一个 amortized shell 中通过 source、`command -v ros2`、`which ros2`、`type -a ros2` 和 child Python `rclpy import`。
- 新 primary blocker 是 `board_source_preflight.classification=board_source_preflight_ros2_cli_invocation_timeout`，也就是 `ros2 --help >/dev/null` invocation timeout。
- artifact 内 legacy root-cause 容器仍可能保留 `workspace_source_or_env_mismatch` 兼容字段，但 Product 判断以新的 `board_source_preflight.classification` 为主。

下一轮不得回到 source/path mismatch 或 O5 support-only；应直接处理 `ros2 --help` 冷启动预算、CLI plugin discovery 或更轻量 CLI readiness probe，然后回到 `map_lifecycle_proof_not_clean` / AMCL / TF / planner path gate。

## OKR 与验收结论

- O5：约 `85%`，`不调整`。本轮没有 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL、safe-to-control 或底盘控制执行。
- O6/O7：约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或 mission material。
- KR：`不归档`。没有完成可归档 KR。

Product acceptance: accepted with conservative boundary. This sprint is O3/O1 supporting no-motion diagnostic delta only; it is not path generation, route execution, delivery/operator acceptance, HIL, safe-to-control, or production cloud evidence.
