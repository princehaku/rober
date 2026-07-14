# Pre Start - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Start time: `2026-07-12 07:53 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`
- Direction: continue O3/O1 strict no-motion runtime recovery; pause O5 support-only work.

## 用户价值和产品北极星

用户价值是把真实板 no-motion runtime 从“CLI/source 已可用”推进到“地图、AMCL、scan、TF downstream blocker 可定位并可复验”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只恢复路径生成前的安全诊断链，不证明送达闭环。

本轮必须避免把 support-only readiness/readback 包装成业务进展。只有同轮拿到 `path_generated=true`、route execution、delivery/operator acceptance、current live HIL 或 external production evidence 时，后续 Product closeout 才能讨论 OKR 百分比变化。

## 已读证据和上轮结论

- `AGENTS.md`：Epic sprint 需要 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`；实现、测试和修复由 owner 子 agent 执行；主节点只做拆解、派单和验收。
- `OKR.md`：O5 约 `85%` 是当前最低 Objective，但缺真实 external production evidence；O1/O6/O7 约 `93%`，O3 作为 current-run mission/no-motion supporting lane 继续服务送达证据链。
- `sprints/2026.07.12_05-52_o3_source_amortized_cli_preflight_repair/final.md`：source、ROS2 path 和 `rclpy` import 已同 shell 通过，旧 `workspace_source_or_env_mismatch` 不再是主 blocker；当时 primary blocker 是 `board_source_preflight_ros2_cli_invocation_timeout`。
- `sprints/2026.07.12_06-54_o3_lightweight_cli_readiness_gate/tech-done.md` 和 `final.md`：helper 已从 `ros2 --help` 单点 hard gate 推进到 lightweight CLI readiness；canonical artifact 证明 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`。
- 最新 canonical blocker：`map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`。

## OKR 映射和方向判断

- O5：`暂停`。O5 当前最低约 `85%`，但近几轮只有 support-only readiness/readback 包装，缺真实 production cloud、production DB/queue、HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实手机/browser 或 external production evidence。继续做 O5 会重复消费同一 blocker。
- O3/O1：`继续`。本轮目标是 strict no-motion 下游恢复，服务 O1 缺口里的 current same-run path generation success 和 Nav2 route execution success 的前置条件。
- O6/O7：`不调整`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback 前，不安排独立 surface/checklist/readback。
- KR 历史归档：本轮计划阶段不归档任何 KR；已完成 KR 历史区不更新。

## 本轮核心抓手

本轮核心抓手是让 `robot-software-engineer` 单线处理 true-board helper 的 downstream recovery：

1. 保持 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
2. 把 `map_server/amcl inactive` 与 `/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing` 分层记录为可执行 root cause。
3. 只有在 lifecycle、topic、TF 和 localization readiness 都满足时，才允许进入 planner-only no-motion path gate；仍禁止任何运动或底盘控制。

## 范围和责任人

- Product owner：`product-okr-owner`，负责本 sprint 计划、验收口径、OKR 方向判断和收口边界。
- Implementation owner：`robot-software-engineer`，负责 helper、单测、navigation docs、raw artifact 和 `tech-done.md`。
- Hardware owner：本轮默认不介入。若 `/scan_no_publisher` 落到 LiDAR runtime、串口、波特率、WAVE ROVER 或上车硬件事实，再由 `rober-hardware-engineer` 读取 `docs/vendor/VENDOR_INDEX.md` 后补充事实。
- Algorithm owner：本轮默认不改代码；若 Robot Software 已证明 source/runtime/lifecycle clean，后续再交给 `robot-algorithm-engineer` 继续 AMCL/TF/path 能力。

## 安全红线

本轮验收严格保持 no-motion：

- 禁止 NavigateToPose。
- 禁止发布 `/cmd_vel`。
- 禁止调用 `/api/base/manual`。
- 禁止打开或使用 WAVE ROVER UART。
- 默认所有危险字段必须保持 `false`：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。
- 唯一例外：如果后续进入 planner-only no-motion path gate，`path_generation_attempted` 可以为 `true`，但 artifact 必须清楚证明没有 NavigateToPose、没有 `/cmd_vel`、没有 `/api/base/manual`、没有 UART、没有 route execution、没有 delivery success。

## 同一 Blocker 重复消费判断

本轮不允许回退到以下已处理或已暂停 blocker：

- O5 support-only readiness/readback 包装。
- source/path mismatch。
- `ros2 --help` 单点 readiness gate。
- 仅复述 `board_source_preflight_ready` 而不进入 map/AMCL/scan/TF downstream 事实。

如果 Robot Software 返回的 artifact 没有比 `06-54` 更清楚地区分 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing`，Product 不应验收为进展。

## 需要创建或更新的 Sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Robot Software 实施后必须更新：`tech-done.md`。
- Product 验收后必须更新：`side2side_check.md`、`final.md`。
