# O3 ROS2 CLI Source Probe Repair Pre-start

## Sprint Type

- sprint_type: epic
- Sprint: `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Start date: 2026-07-11

## 用户价值和产品北极星

用户价值不是再生成一份 ROS 状态面板，而是把真实板 no-motion path generation 的下一条执行命令收敛到可修复问题。产品北极星仍是普通用户手机发车后，小车能在固定路线中生成路径、执行路线、完成送达并留下可消费证据；本 sprint 只处理 path generation 前置的 sourced shell / ROS2 CLI blocker。

本轮必须保持 no-motion 边界：不发布 `/cmd_vel`，不调用 `/api/base/manual`，不发送 `NavigateToPose`，不打开 WAVE ROVER 底盘 UART，不把 managed runtime startup 解释成运动或 HIL。

## 上轮证据摘要

最近两轮结论已经把 blocker 从泛化 runtime 问题压缩到 board sourced shell 分层：

- `sprints/2026.07.11_17-43_o3_managed_runtime_scan_attempt_recovery/final.md`：latest live artifact 输出 `status=blocked_with_root_cause`、`managed_runtime_started=true`，但 `map_server_active=false`、`amcl_active=false`、`/scan.probe.boundary=scan_probe_skipped_without_ros2`、`path_generated=false`；root causes 为 `map_lifecycle_proof_not_clean` 与 `ros2_command_unavailable_after_bash_source`。
- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/final.md`：`board_source_preflight` 证明 `ros2_cli_ok=false`，但 `rclpy_import_ok=true`、`python_executable=/usr/bin/python3`、`rclpy_file=/opt/ros/humble/local/lib/python3.10/dist-packages/rclpy/__init__.py`；`map_lifecycle_preflight` 因无 ROS2 CLI 被跳过，`path_generated=false`。

这说明当前不应再回到 O5 support-only/readback，也不应继续泛化写成 ROS runtime 不可用。本轮要把 `ros2_cli_ok=false` 拆到 source 阶段、PATH/which 阶段、ros2 CLI invocation 阶段、Python/rclpy 阶段，并优先修复 helper 误判或超时合同。

## OKR 映射和方向判断

- 最低 Objective：O5，约 `85%`。
- 本轮是否直接推进 O5：否。
- 不推进 O5 的理由：真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实手机/browser 证据缺失已多轮证明，继续 readiness / wrapper / readback 只能落入 `support_only`，不能安全计分。
- 本轮方向判断：`继续` O3 no-motion 现场诊断链，作为 O1/O3 path generation 前置 blocker 修复；`暂停` O5 support-only 包装；不调整 OKR 百分比，不归档 KR。

## 本轮核心抓手

把 helper 的 `board_source_preflight_ros2_cli_unavailable` 从单点结论改成可执行分层：

1. `source /opt/ros/humble/setup.bash` 和 workspace setup 是否自然返回。
2. `PATH`、`AMENT_PREFIX_PATH`、`PYTHONPATH`、`LD_LIBRARY_PATH` 是否包含预期 ROS/workspace 片段。
3. `command -v ros2`、`type -a ros2`、`which ros2` 的返回码、stdout、stderr、elapsed、timeout 是否分开记录。
4. `ros2 --help` 或等价最小 CLI invocation 是否与 `command -v ros2` 分开记录。
5. `python3 -c 'import rclpy'` 继续保留为独立对照，不把 rclpy 成功误判成 ros2 CLI 成功。

## 需要做什么

Algorithm owner 需要修改 helper 合同、补单测、跑本地和真实板命令，并同步导航文档。Product owner 本轮只创建计划文档；`tech-done.md`、`side2side_check.md`、`final.md` 留给实现与验收阶段。

若本轮最终仍停在同一 `ros2_cli_ok=false`，且没有把 root cause 进一步落到 source/PATH/which/CLI invocation 中任一更窄层级，`final.md` 必须按“同一 blocker 第三轮”升级给 CEO 决策：继续攻坚板端 ROS2 CLI、切换 Objective、或安排人工维护窗口。

## 优先级和验收口径

优先级：P0。它阻塞 `map_server`/`amcl` lifecycle、`/scan`、`/amcl_pose`、`map->odom` 和 path generation 的后续读数。

验收口径：

- local helper 仍能 fail-closed，并写出本 sprint artifact。
- 单测覆盖 source/PATH/which/ros2 invocation/rclpy 分层。
- live artifact 至少新增 `board_source_preflight` 的分层字段，能区分 source timeout、PATH missing、which missing、CLI invocation timeout/failed、rclpy import failed/ok。
- no-motion 安全字段继续固定为 `safe_to_control=false`、`robot_control_executed=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`。
- 如果 `ros2_cli_ok=true`，才允许继续读取 `map_lifecycle_preflight`、`/scan`、`/amcl_pose`、TF 与 path generation；否则下游必须 fail-closed skipped。

## 风险、阻塞和证据链缺口

- 真实板 SSH 或 runtime 可能抖动，导致 helper artifact 只能证明 timeout 分层，不证明修复完成。
- `rclpy_import_ok=true` 与 `ros2_cli_ok=false` 的分裂可能来自 PATH、shell init、workspace setup、CLI 包缺失或 helper timeout 合同，需避免先验归因。
- 即使本轮修复 `ros2_cli_ok`，仍可能继续阻塞在 `map_lifecycle_proof_not_clean`、`/scan`、`/amcl_pose`、`map_to_odom_not_observed` 或 `path_generated=false`。
- 本轮不产生 route execution、delivery/operator acceptance、current live HIL 或 production external evidence。

## KR 历史归档

本轮计划阶段不归档任何 KR。若实现阶段没有 `path_generated=true`、route execution、delivery/operator acceptance、current live HIL 或 production external evidence，`OKR.md` 百分比和 KR 归档应保持不变。

## 需要创建或更新的 sprint 文档

本计划阶段只创建：

- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/pre_start.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/prd.md`
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/tech-plan.md`

实现阶段再由 Algorithm owner 更新 `tech-done.md`；验收阶段再更新 `side2side_check.md` 和 `final.md`。
