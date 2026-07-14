# Final - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 06:30 CST`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`
- Outcome: accepted as source-amortized helper preflight diagnostic delta; mission gates remain blocked.

## 用户价值和产品北极星

用户价值是把真实板现场执行链从“helper 还卡在 source/path lookup 是否可靠”推进到“source、ROS2 path lookup 和 `rclpy` import 已同 shell 通过，当前只剩 ROS2 CLI invocation timeout 这一更窄 blocker”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮不是送达闭环，只是进入 `/map_server`、AMCL、TF 和 planner path gate 之前的 no-motion runtime repair。

## OKR 映射和方向判断

- O5：保持约 `85%`，`不调整`。本轮没有真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：保持约 `93%`，`不调整`。本轮没有 current same-run path generation success、Nav2 route execution success、current live HIL、safe-to-control、底盘反馈增量或真实控制执行。
- O6/O7：保持约 `93%`，`不调整`。本轮没有新的 same-task route execution、delivery record、operator acceptance、production readback 或可消费 mission material。
- 方向判断：`继续` O3/O1 strict no-motion runtime recovery；`暂停` O5 support-only lane；`不归档` KR。

## KR 拆解、更新或历史归档

本轮 `不归档` 任何 KR。

原因：

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
- 没有 production cloud / external evidence
- 没有 delivery/operator acceptance 或 current live HIL

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据只作为 O3/O1 supporting diagnostic delta 记录在本 sprint 的 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` Key Results 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手和实际结果

本轮核心抓手是让 helper 把 source、path lookup、ROS2 CLI invocation 和 `rclpy` import 放进同一个 bounded shell，消除上一轮 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 的测量歧义。

Robot Software 实际改动由 `tech-done.md` 记录，Product 收口确认只涉及 helper、tests、navigation docs 和本 sprint artifacts。关键事实如下：

1. 新增 `trashbot.o10.source_amortized_cli_preflight.v1` 主路径，保留旧字段兼容。
2. Targeted unittest 通过：`Ran 96 tests in 2.251s OK`。
3. Local dry-run RC `2`，按预期 fail-closed，`classification=board_source_preflight_source_failed`，符合 macOS 无 `/opt/ros/humble/setup.bash` 边界。
4. True-board push RC `0`，strict no-motion run RC `2` 并写出 artifact，pull RC `0`。
5. Live artifact 明确 `source_and_cli_in_one_shell=true`、`per_command_source_overhead_eliminated=true`、`source_stage_ok=true`、`ros2_cli_path_ok=true`、`rclpy_import_ok=true`。
6. 新 primary blocker 为 `classification=board_source_preflight_ros2_cli_invocation_timeout`，`cli_invocation.command="ros2 --help >/dev/null"` 在 `6.0s` 内 timeout；`ros2_cli_invocation_ok=false`、`cli_ready=false`、`runtime_ready=false`。
7. Additional root cause 仍包含 `map_lifecycle_proof_not_clean`，但 helper 尚未进入 map/AMCL/TF/path gate。

Product closeout 实际改动：

- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/side2side_check.md`
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Robot Software 验证事实：

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py` RC `0`。
- `python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` RC `0`，输出 `Ran 96 tests in 2.251s OK`。
- Local fail-closed helper dry-run RC `2`，artifact written。
- True-board helper push RC `0`，strict no-motion run RC `2`，artifact written。
- True-board artifact pull RC `0`。
- Scoped `git diff --check` RC `0`。

Product closeout 验收命令：

```bash
rg -n "05-52|source_amortized_cli_preflight|board_source_preflight_ros2_cli_invocation_timeout|per_command_source_overhead_eliminated=true|source_stage_ok=true|ros2_cli_path_ok=true|rclpy_import_ok=true|cli_ready=false|runtime_ready=false|map_lifecycle_proof_not_clean|Ran 96|path_generation_attempted=false|path_generated=false|safe_to_control=false|不调整|不归档" OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

```bash
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair
```

## Live Artifact 结论

Artifact:

- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/artifacts/live_o10_source_amortized_cli_preflight.raw.json`

关键字段：

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
- `cli_invocation.command="ros2 --help >/dev/null"`
- `cli_invocation.timeout_s=6.0`
- `map_lifecycle_proof_not_clean`

No-motion 字段继续固定：

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

## Product Judgment

本轮满足 Product acceptance gate，但结论必须保守：

- Accepted：helper source/path/rclpy 层已经从上一轮 source/path lookup blocker 推进到 ROS2 CLI invocation timeout。
- Accepted：新主分类 `board_source_preflight_ros2_cli_invocation_timeout` 比 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 更窄、更可执行。
- Not accepted：没有进入 `/map_server`、`/amcl_pose`、dynamic `map->odom` 或 planner path gate，因为 `cli_ready=false`。
- Not accepted：不是 path generation、route execution、delivery/operator acceptance、current live HIL、safe-to-control 或 production cloud evidence。

artifact 内部分 legacy root-cause 容器仍保留 `workspace_source_or_env_mismatch` 兼容读法；Product 判断以新的 `board_source_preflight.classification=board_source_preflight_ros2_cli_invocation_timeout` 为主，不把旧兼容字段当成本轮 primary blocker。

## Blocker 重复消费判断

本轮不按与 `04-51` 同一 blocker 重复消费处理。

理由：

1. `04-51` helper 仍 blocked 在 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch`，下一跳是 source + path lookup + CLI invocation 同 shell amortization。
2. `05-52` 已证明同一 shell 内 source 成功、ROS2 path 可见、`rclpy_import_ok=true`，且 `per_command_source_overhead_eliminated=true`。
3. 当前 blocker 已移动到 `ros2 --help >/dev/null` invocation timeout，`cli_ready=false`、`runtime_ready=false`。

下一轮不能回到 source/path mismatch 或 O5 support-only。应由 `robot-software-engineer` 直接处理 `ros2 --help` 冷启动预算、CLI plugin discovery、或替换为更轻量 readiness invocation；`cli_ready=true` 后再回 `map_lifecycle_proof_not_clean`、AMCL、TF 和 planner path gate。

## 剩余风险

- `ros2 --help` 在 true-board 6 秒 budget 内 timeout，可能是 CLI plugin discovery 冷启动、环境加载后首次 invocation 慢、或 readiness probe 选型过重。
- `map_lifecycle_proof_not_clean` 仍存在，helper CLI ready 后还需要重新证明 map lifecycle、AMCL pose、dynamic `map->odom` 和 planner path。
- 本轮没有 path generation、NavigateToPose、route execution、delivery/operator acceptance、HIL pass、safe-to-control 或 production cloud。
- true-board artifact 是 strict no-motion diagnostic，只证明 source/path/rclpy 已穿过，且 CLI invocation timeout 是当前更窄 blocker。

## 下一轮建议

优先级 P0：继续 O3/O1 strict no-motion lane，由 `robot-software-engineer` 处理 `ros2 --help` invocation timeout。建议先比较 `ros2 --help` 冷启动预算与更轻量 readiness command，再决定是延长单次 CLI budget、预热 CLI plugin discovery，还是改用不会阻塞后续 lifecycle/path gate 的 readiness probe。

P1：当 `cli_ready=true` 后，立即回到 `map_lifecycle_proof_not_clean`、`/map_server`、`/amcl_pose`、dynamic `map->odom`、`map->base_link` 和 planner path gate。不得发送 NavigateToPose、发布 `/cmd_vel`、调用 `/api/base/manual` 或打开 WAVE ROVER UART。
