# Pre-Start - O3 Lightweight CLI Readiness Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned start time: `2026-07-12 06:54 CST`
- Target lane: `O3/O1 strict no-motion runtime recovery`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_runtime_diagnostic_only`

## 用户价值和产品北极星

用户价值是把 true-board 现场 no-motion 诊断从“source/path/rclpy 已通，但 `ros2 --help >/dev/null` 6 秒超时卡死 helper readiness”推进到“helper 用更轻量的 CLI readiness gate 穿过 preflight，重新进入 `/map_server`、AMCL、TF 和 planner path gate”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮只做运行时前置门槛规划，不做运动、送达或 production 闭环。

## 上轮结果与本轮切入点

最新已完成 sprint `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/` 已收口确认：

- `source_stage_ok=true`
- `ros2_cli_path_ok=true`
- `rclpy_import_ok=true`
- `ros2_cli_invocation_ok=false`
- `cli_ready=false`
- `runtime_ready=false`
- `board_source_preflight.classification=board_source_preflight_ros2_cli_invocation_timeout`
- `cli_invocation.command="ros2 --help >/dev/null"`
- `cli_invocation.timeout_s=6.0`
- `map_lifecycle_proof_not_clean`

这说明 blocker 已不再是 source/path mismatch，也不应回去继续消费 O5 support-only readiness/credit/readback。当前最小有效动作是把 helper 的硬 readiness gate 从单一 `ros2 --help` 改成轻量、可分层、可 fail-closed 的 CLI readiness 组合：比较 heavy help、lightweight readiness 和 `rclpy` import，在 source/path/rclpy 已通过时尽量放行 `cli_ready=true` 进入下游 lifecycle/localization/path gate，或者至少输出比 `map_lifecycle_proof_not_clean` 更窄的下一跳 blocker。

## OKR 映射和方向判断

- O5：当前最低 Objective，约 `85%`，本轮 `不直接针对`。原因是 O5 当前仍缺真实 production external evidence；最近 readiness、credit、readback 已连续落在 support-only，不应继续重复消费同一 external blocker。
- O1：当前约 `93%`，本轮作为 supporting lane 继续推进 same-run path generation 之前的 helper/runtime gate。
- O3：本轮继续 strict no-motion runtime lane，目标是让 helper readiness 重新回到 lifecycle/localization/path gate。
- O6/O7：当前约 `93%`，本轮不新增 archive/readback/consumer surface。
- 方向判断：`继续` O3/O1 strict no-motion；`暂停` O5 support-only lane；`不调整` OKR 百分比；`不归档` KR。

## 本轮核心抓手

1. 为 `robot-software-engineer` 明确轻量 CLI readiness gate 的计划边界，避免继续把 `ros2 --help` 当唯一硬门槛。
2. 把 heavy help、lightweight readiness、`rclpy` import 与 downstream runtime gate 的关系写成结构化验收口径。
3. 把 no-motion 红线、允许修改范围、artifact 命名和 Product closeout 口径写死，保证后续实现仍是 O3/O1 supporting diagnostic delta。

## Owner 与边界

- Product owner：`product-okr-owner`
- Implementation owner：`robot-software-engineer`
- 本轮 implementation 仍是单 owner 闭环：helper、targeted tests、navigation docs、artifact、`tech-done.md` 都集中在一个软件 owner，可避免把同一 runtime blocker假并行拆散。

## No-Motion 红线

本轮及后续 implementation 严禁：

- 发送 NavigateToPose；
- 发布 `/cmd_vel`；
- 调用 `/api/base/manual`；
- 打开 WAVE ROVER UART；
- 把 `safe_to_control`、`publishes_cmd_vel`、`calls_base_manual`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass`、`uses_base_uart` 写成 true。

允许启动或观测 Nav2/ROS2 runtime，只要 artifact 明确 no-motion 且不触发底盘或路线执行。

## Product Closeout 口径

本轮只接受两类结果：

1. helper 在 source/path/rclpy 已通过时，用轻量 readiness gate 成功得到 `cli_ready=true`，并重新进入 `/map_server`、`/amcl_pose`、dynamic `map->odom` 或 planner path gate；
2. helper 仍 blocked，但能把 `board_source_preflight_ros2_cli_invocation_timeout` 进一步收窄为更具体、可执行的 lightweight CLI 或 runtime blocker。

除非出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，否则 closeout 时 `OKR.md` 百分比不调整，KR 不归档。

## 风险与阻塞

- 轻量 readiness gate 可能仍受 true-board ROS2 CLI 冷启动、plugin discovery 或 daemon 状态影响，`cli_ready=true` 不一定立刻得到 runtime ready。
- 通过 `cli_ready=true` 后，可能马上暴露 `map_lifecycle_proof_not_clean`、`/amcl_pose` timeout、dynamic `map->odom` missing 或 planner path not attempted。
- 本轮只是计划，不证明 path generation、route execution、delivery success、HIL、safe-to-control 或 production cloud。
