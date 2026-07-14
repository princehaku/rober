# O3 ROS2 CLI Source Probe Repair Side-by-side Check

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Closeout date: 2026-07-11

## 用户价值和产品北极星

用户价值是把真实板 no-motion path generation 的下一条工程动作从“ROS2 CLI/source 泛化不可用”推进到“source/CLI 已 ready，继续处理 AMCL、TF、graph final artifact”。产品北极星仍是普通用户手机发车后，小车能沿固定路线生成路径、执行路线、完成送达并留下可消费证据；本 sprint 只验收 path generation 前置诊断修复，不验收送达闭环。

## OKR 映射和方向判断

- O5 仍是最低活跃 Objective，约 `85%`，但本轮不继续 O5 support-only/readback lane。
- O1/O3：`继续` no-motion localization/path readiness 链路；本轮已解除旧 `ros2_cli_ok=false` blocker。
- O6/O7：等待同轮 route/path/delivery/operator/production artifact 后再消费，不用 partial runtime material 包装增量。
- 方向判断：本轮 `继续` O3/O1 现场 no-motion blocker repair，`不调整` O1/O5/O6/O7 百分比，`不归档` KR。

## 验收对照

| 验收项 | 计划口径 | 实际结果 | Product 判断 |
| --- | --- | --- | --- |
| Plan docs | `pre_start.md`、`prd.md`、`tech-plan.md` 已存在 | 已存在并明确 no-motion、O5 support-only 暂停、百分比不调整 | 通过 |
| Algorithm 实现 | helper 拆 source/PATH/which/CLI invocation/rclpy 层 | `tech-done.md` 记录 helper、测试、导航文档和 local/live artifacts 已完成 | 通过 |
| 本地验证 | `py_compile`、targeted unittest、local helper fail-closed | `py_compile` exit `0`；`python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper` exit `0`，`Ran 65 tests in 2.221s OK`；local helper exit `2` fail-closed | 通过 |
| 板端传输与运行 | `scp`、live helper、artifact pull | `scp` exit `0`；live helper exit `255` / interrupted；partial artifact pull exit `0` | 有效但边界为 partial runtime material |
| Source/CLI blocker | 需要把 `ros2_cli_ok=false` 拆细或修复 | live artifact: `proof.board_source_preflight.classification=board_source_preflight_ready`、`ros2_cli_ok=true`、`rclpy_import_ok=true`、`source_stage_ok=true` | 通过，旧 blocker 已移动 |
| 下游 path generation | 只有定位/TF/lifecycle ready 才允许尝试 path | `last_successful_phase=graph_discovery`；`path_generation_requested=true`、`path_generation_attempted=false`、`path_generated=false` | 未通过，不计 OKR 增量 |
| 安全边界 | no-motion，所有危险字段 false | `safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | 通过 |

## Live Artifact 事实

`artifacts/live_o10_ros2_cli_source_probe_repair.raw.json` 当前是 `status=interrupted_before_final_artifact`、`evidence_type=partial_runtime_material`，不是 final success artifact。主节点只读验收确认：

- `proof.board_source_preflight.classification=board_source_preflight_ready`
- `ros2_cli_ok=true`
- `rclpy_import_ok=true`
- ROS setup 与 workspace setup 均存在并 source 成功
- `source_stage.elapsed_ms=2979`
- `command -v ros2` 输出 `/opt/ros/humble/bin/ros2`，耗时 `15ms`
- `type -a ros2` 正常，耗时 `14ms`
- `which ros2` 输出 `/opt/ros/humble/bin/ros2`，耗时 `16ms`
- `ros2 --help >/dev/null` 正常，耗时 `2604ms`
- `rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`

下游 blocker 已转移为：

- `/amcl_pose_once_not_observed`
- `map_to_odom_not_observed`
- `map_to_base_link_blocked_by_missing_map_to_odom`
- `sigterm_before_final_artifact`

## KR 拆解、更新或历史归档

本轮不产生已完成 KR。O1 的 `current same-run path generation success`、`Nav2 route execution success` 和 current live HIL 缺口仍在；O5 的 production external evidence 缺口仍在；O6/O7 仍缺可消费的 current live route/delivery/operator/production material。因此本轮不归档任何 KR。

## 风险、阻塞和需要补齐的证据链

- live artifact 是 partial/interrupted，不能证明 helper final artifact 稳定收口。
- `path_generated=false`，且 path generation 未实际 attempted，不能宣称路线、送达或 HIL 成功。
- AMCL、TF 与 graph probes 仍需分层限时，尤其是 `/amcl_pose`、`map->odom` 和 `map->base_link`。
- 下一轮需要产出 final artifact 或明确的 downstream fail-closed 分类；只有同轮 `path_generated=true`、route execution、delivery/operator acceptance、current live HIL 或 production external evidence 出现后，才可讨论 OKR 增量。

## 需要创建或更新的 sprint 文档

- 已完成：`side2side_check.md`
- 已完成：`final.md`
