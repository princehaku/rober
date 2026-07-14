# O3 AMCL TF Final Artifact Bounded Probe Pre Start

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Start date: 2026-07-11
- Direction: O3/O1 no-motion localization and path readiness
- Status: planning ready for Algorithm single-owner execution

## 用户价值和产品北极星

产品北极星仍是普通用户把垃圾交给小车后，小车能沿固定路线完成送达，并留下可复盘的 current-run 证据链。本 sprint 的用户价值不是增加一个新的 wrapper，而是把真实板 no-motion 链路从 ROS2 source/CLI 前置条件继续推进到 AMCL、TF、graph final artifact 和 planner-only path readiness，尽量拿到可被下一轮路线执行消费的同轮定位/path 证据。

## OKR 当前判断

当前 `OKR.md` 4.1 节里最低 Objective 仍是 O5，进度约 `85%`。O5 的主要缺口是：

- 真实公网 HTTPS/TLS；
- 真实 4G/SIM；
- production DB/queue；
- production worker/cutover；
- OSS/CDN live traffic；
- 真实手机/browser 证据。

本 sprint 不直接针对 O5。理由是最近 O5 support-only/readback/cutover readiness 工作已经明确 `okr_credit_allowed=false`，且 proof boundary 固定为 `software_proof_support_only`。在没有真实 production/external evidence 的情况下继续做 O5，只会重复包装已有 readiness 或 readback 结论，不能产生主 OKR 增量。

本轮转向 O3/O1 no-motion localization/path readiness，是当前可推进、可验证、且不重复旧 blocker 的最低可动链路。它直接服务于后续 current-run path generation、Nav2 route execution、route/delivery/operator material 和 mission artifact 消费，但本轮不预设 OKR 百分比上调。

## 最近两轮 Blocker 扫描

最近两轮相关 sprint 结论：

- `sprints/2026.07.11_18-45_o3_board_ros_source_map_lifecycle_preflight/final.md`
  - blocker: `board_source_preflight_ros2_cli_unavailable`
  - 事实：`ros2_cli_ok=false`，`rclpy_import_ok=true`，map lifecycle preflight 因 ROS2 CLI 不可用被跳过。
- `sprints/2026.07.11_19-46_o3_ros2_cli_source_probe_repair/final.md`
  - blocker 已移动：`board_source_preflight_ready`
  - 事实：`ros2_cli_ok=true`，`rclpy_import_ok=true`，`source_stage_ok=true`，但 live artifact 为 `status=interrupted_before_final_artifact`。
  - 下游 blocker：`sigterm_before_final_artifact`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`。
  - path 状态：`path_generation_requested=true`，`path_generation_attempted=false`，`path_generated=false`。

因此本轮不触发同一 blocker 第三轮升级。旧 source/CLI blocker 已被 19-46 修到 ready；新的工作应转向 AMCL lifecycle、`/amcl_pose`、动态 `map->odom` 与 `map->base_link` 分层，以及 helper final artifact 有界收口。

## 本轮核心抓手

本轮抓手是让 Algorithm worker 在 no-motion 边界内完成一个有界的 AMCL/TF/final artifact probe：

1. 修复或收敛 `sigterm_before_final_artifact`，确保 helper 在超时或中断前写出足够结构化的 final/partial artifact。
2. 对 `/amcl` lifecycle、`/amcl_pose`、`map->odom`、`map->base_link` 做分层读数，避免把 downstream TF 缺失混成一个粗 blocker。
3. 在 localization ready 时仅执行 planner-only `ComputePathToPose` path probe；不发送 NavigateToPose goal。
4. 所有 safety/control/HIL/delivery 字段继续保持 false，除非只是 `starts_nav2`、`managed_runtime_started` 这类 no-motion runtime started 读数。

## Owner 和执行方式

本轮 owner 是 `robot-algorithm-engineer` 单线闭环。

理由：

- 文件范围集中在 Nav2/AMCL/TF helper、targeted tests、导航文档和本 sprint artifacts；
- 不涉及 cloud/O6/O7 UI；
- 不涉及 WAVE ROVER UART、底盘协议、电气、串口或硬件驱动配置；
- 接口耦合集中在 Algorithm helper 合同内，一个 owner 可以实现、验证、修复和更新 `tech-done.md`；
- 拆成多个 worker 会制造假并行，不会增加独立验收证据。

## No Motion 安全边界

禁止：

- 发布 `/cmd_vel`；
- 调用 `/api/base/manual`；
- 发送 NavigateToPose goal；
- 打开或使用 WAVE ROVER UART；
- 宣称 safe-to-control、HIL pass、route execution success 或 delivery success。

允许：

- lifecycle readback；
- map server / AMCL / planner server 状态读取；
- `/map`、`/scan`、`/amcl_pose`、`/tf`、`/tf_static` topic 和 freshness readback；
- TF edge 分层诊断；
- planner-only `ComputePathToPose` path probe；
- fail-closed local/live artifact 写出。

## 进入条件

- 19-46 sprint 已证明 `board_source_preflight_ready`；
- 本轮不再修旧 `ros2_cli_ok=false` 或 `rclpy_import_ok=false` blocker；
- worker 必须从 19-46 的 artifact 事实继续往下游推进；
- 任何 live 命令都必须保持 no-motion flags 和 false safety 字段。

## 退出条件

本 sprint 完成时至少要有：

- `tech-done.md` 记录实际改动、验证结果和剩余风险；
- local helper artifact；
- live helper artifact，或明确的 live 触达失败证据；
- AMCL lifecycle、`/amcl_pose`、`map->odom`、`map->base_link`、path generation requested/attempted/generated 的结构化结论；
- scoped `git diff --check` 通过；
- Product closeout 在 `side2side_check.md` 与 `final.md` 中判断是否可计入 OKR 进展。

## 需要补齐的证据链

本轮不要求 route execution 或 delivery success，但必须为下一步 current-run path material 打地基。理想证据顺序是：

1. `managed_runtime_started=true`；
2. `map_server_active=true`；
3. `amcl_active=true`；
4. `/amcl_pose` observed；
5. dynamic `map->odom` observed；
6. `map->base_link` 可由 `map->odom` 与 odom/base edge 推导；
7. planner-only path generation attempted；
8. `path_generated=true` 与 path point count 大于 0。

如果任何一步失败，artifact 必须写明最先失败的 root cause，不能用 historical latest 或 previous clean-baseline path 替代 current-run 证明。

## 风险和阻塞

- live helper 可能继续被 `sigterm_before_final_artifact` 打断，导致最终 artifact 不完整；
- AMCL 可能 active 但 `/amcl_pose` 不发布，需要区分 lifecycle ready、initial pose、scan freshness 与 particle update 之间的边界；
- `map->odom` 缺失会继续阻塞 `map->base_link` 和 path generation；
- planner-only path probe 即使成功，也不等于 NavigateToPose、route execution、HIL 或 delivery success；
- O5 仍缺真实 external production evidence，本轮不能替代 O5 验收。

## 需要创建或更新的 Sprint 文档

计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行和收口阶段由后续 owner/closeout 更新：

- `tech-done.md`
- `side2side_check.md`
- `final.md`
