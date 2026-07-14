# Pre Start - O3 Daemon/DDS Graph Split

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/`
- Start time: `2026-07-12 03:52 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Target Objective: O3/O1 no-motion supporting chain for current same-run path generation readiness.
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## 上轮未完成项

上一轮 `sprints/2026.07.12_02-51_o3_source_amortized_graph_probe/` 已纠正测量层：

- `ros2 node list --help` 在 source-amortized batch 内可完成。
- rclpy graph stage stream 已观察到 21 个 node。
- `workspace_environment` 已观察到 ROS/workspace 摘要。
- 但 `ros2 node list`、`ros2 topic list`、`ros2 daemon status` 和 `ros2 node list --no-daemon` 仍 timeout。

当前 live artifact 主结论是 `ros2_daemon_or_dds_graph_discovery_timeout` / `ros2_node_list_timeout`，不是 path generation、route execution、delivery、HIL 或 production evidence。

## Blocker 重复消费判断

本轮不能只重复 `ros2_node_list_timeout`。必须把同一 blocker 拆到至少一个更具体的层级：

- ROS2 daemon 状态或 daemon reset 后行为；
- DDS discovery / `ROS_DOMAIN_ID` / `RMW_IMPLEMENTATION` / env mismatch；
- `--no-daemon` 是否真正可用或只是 Humble CLI 能力边界；
- managed process lifecycle visibility 是否仍被 graph timeout 遮蔽；
- graph command budget 是否不足以解释 timeout。

若本轮只复述上一轮分类，不得计 OKR 增量，也不得宣称 mission 进展。

## 本轮目标

在严格 no-motion 边界内，把 `ros2_daemon_or_dds_graph_discovery_timeout` 拆成可执行的下一步 root cause 证据。优先产出 true-board final artifact；真板不可达时保留 local fail-closed artifact 和明确风险。

## Owner

主责 owner：`robot-software-engineer`

选择 Robot Software 的理由：当前问题已从 Algorithm helper 分类移动到 ROS2 graph、daemon、DDS、runtime source 和 lifecycle 可观测性，属于 ROS2 主链路/bringup 运行时问题。

## 安全边界

本轮禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART
- 声称 `safe_to_control=true`

所有 artifact 必须继续固定：

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

## 预期留档

Epic sprint 必须完成：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`
- `tech-done.md`
- `side2side_check.md`
- `final.md`

Engineer 负责实现、验证、修复和 `tech-done.md`；Product 负责验收、OKR 判断、`side2side_check.md`、`final.md`、必要的 `OKR.md` 与 `docs/process/okr_progress_log.md` 更新。
