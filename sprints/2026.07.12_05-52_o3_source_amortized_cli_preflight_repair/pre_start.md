# Pre-Start - O3 Source-Amortized CLI Preflight Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned start time: `2026-07-12 05:52 CST`
- Target lane: `O3/O1 strict no-motion runtime recovery`
- Proof boundary: `software_proof_o3_o1_no_motion_runtime_diagnostic_only`

## 用户价值和产品北极星

用户价值是把真实板现场调试从“manual graph readback 可见，但 helper 主路径仍 fail-closed”推进到“helper 自己能在同一个 sourced shell 中稳定完成 ROS2 CLI preflight，然后回到 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮只修 no-motion runtime helper 前置条件，不是路线执行或送达闭环。

## 上轮结果与本轮切入点

上一轮 `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/` 的 Product closeout 已确认：

- manual same-run strict no-motion graph readback 成功；
- `ros2 daemon status/stop/start`、`timeout 8 ros2 node list`、`timeout 8 ros2 topic list` 均 `RC=0`；
- graph 中观测到 `/amcl`、`/planner_server`、`/scan`、`/map`、`/tf`、`/tf_static`；
- helper latest artifact 仍 fail-closed 在 `board_source_preflight_ros2_cli_which_timeout`；
- root cause classification 仍是 `workspace_source_or_env_mismatch`；
- `daemon_safe_graph_readback.reset_skip_reason=skipped_without_sourced_ros2_cli_ready`；
- `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

本轮切入点不是继续包装 manual readback，也不是回到 O5 support-only。最小有效动作是让 helper 把 source、path lookup、`command -v` / `which` / `type -a ros2` 和目标 CLI invocation 放进同一个 amortized shell，减少分段 shell、重复 source 和 path/env 抖动。

## OKR 映射和方向判断

- O5：当前最低 Objective，约 `85%`，本轮 `不直接针对`。原因是 O5 当前缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence；近期 O5 已明确 `okr_credit_allowed=false` / support-only，继续做 wrapper 会重复消费同一 blocker。
- O1：当前约 `93%`，本轮作为 supporting lane 继续推进 `current same-run path generation success` 和 `Nav2 route execution success` 前的 helper/runtime blocker。
- O3：本轮继续 strict no-motion runtime lane，目标是恢复 helper preflight ready 后重回 localization/path gate。
- O6/O7：当前约 `93%`，本轮不新增 archive/readback/consumer surface。
- 方向判断：`继续` O3/O1 no-motion helper preflight repair；`暂停` O5 support-only lane；`不调整` OKR 百分比；`不归档` KR。

## 本轮核心抓手

1. Robot Software 修复 helper preflight：把 source、ROS2 path lookup 和 CLI readiness invocation 合并进同一个 amortized shell。
2. 本地 dry-run 必须 fail-closed 且不触发运动，证明缺 board 或缺 live runtime 时不会误报 ready。
3. 若 true board SSH 可达，执行 strict no-motion helper push/run/pull；若不可达，记录具体不可达原因。
4. 若 helper preflight ready，再继续观测 `/map_server`、`/amcl_pose`、dynamic `map->odom` 和 planner path gate。

## Owner 与边界

- Product owner：`product-okr-owner`
- Implementation owner：`robot-software-engineer`
- 本轮是单 owner 闭环。任务集中在 ROS2 helper、targeted unit tests、navigation docs、artifact 和 `tech-done.md`，不需要并行拆给 Algorithm、Hardware 或 Full-stack。

## No-Motion 红线

本轮严禁：

- 发送 NavigateToPose；
- 发布 `/cmd_vel`；
- 调用 `/api/base/manual`；
- 打开 WAVE ROVER UART；
- 把 `safe_to_control`、`publishes_cmd_vel`、`calls_base_manual`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass` 写成 true。

允许启动或观测 Nav2/ROS2 runtime，只要 helper 和 artifact 明确不发送运动命令、不走底盘串口、不执行 route。

## Product Closeout 口径

本轮只接受两类进展：

1. helper preflight 从 `board_source_preflight_ros2_cli_which_timeout` / `workspace_source_or_env_mismatch` 推进到 `board_source_preflight_ready` 或更窄、更可执行的 fail-closed blocker；
2. helper preflight ready 后，runtime gate 回到 `/map_server`、`/amcl_pose`、dynamic `map->odom` 或 planner path gate，并保留 no-motion false fields。

除非出现 same-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，否则 closeout 时 `OKR.md` 百分比不调整，KR 不归档。

## 风险与阻塞

- true board shell source 可能仍慢，single-shell amortization 也可能只把 blocker 前移到 CLI invocation timeout。
- manual graph readback 成功不等于 helper 主路径稳定，不能把 manual result 当 helper structured proof。
- helper preflight ready 也不等于 localization/path ready，仍可能 blocked 在 `/map_server` inactive、`/amcl_pose` timeout、dynamic `map->odom` missing 或 planner path not attempted。
- 本轮不证明 HIL、safe-to-control、route execution、delivery success 或 production cloud。
