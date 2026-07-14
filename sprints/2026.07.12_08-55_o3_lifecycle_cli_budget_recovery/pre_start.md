# Pre Start - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Start time: `2026-07-12 08:55 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`
- Direction: continue O3/O1 strict no-motion runtime recovery; pause O5 support-only/readback/wrapper work.

## 用户价值和产品北极星

用户价值是把真实上位机 no-motion runtime 从"lifecycle command timeout"推进到可执行、可复验的 lifecycle readback 事实：`/map_server` 与 `/amcl` 到底是 CLI 预算不足、inactive stdout、graph 可见但 lifecycle timeout，还是已经 active。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只恢复路径生成前的安全诊断链，不交付路线执行、底盘控制或送达闭环。

本轮必须避免把 support-only readiness、readback wrapper 或泛化 timeout 包装成 OKR 进展。只有同轮拿到 current-run path generation success、route execution、delivery/operator acceptance、current live HIL 或 external production evidence，Product closeout 才能讨论 OKR 百分比变化。

## 已读证据和上轮结论

- `AGENTS.md`：Epic sprint 必须按 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 留档；实现、测试和修复由 owner 子 agent 执行；本阶段只创建规划文档。
- `OKR.md`：O5 约 `85%` 是当前最低 Objective，但缺真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence；O1/O6/O7 约 `93%`。
- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/final.md`：上一轮已完成 Product acceptance，canonical artifact 证明 `board_source_preflight.classification=board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`，但 lifecycle readback 仍暴露 `map_server_lifecycle_command_timeout` 与 `amcl_lifecycle_command_timeout`。
- 上一轮下一步明确要求继续 O3/O1 strict no-motion：先处理 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` timeout，再处理 `/scan` publisher-visible sample timeout、`/map_topic_missing` 与 `/tf_topic_missing`。
- 安全边界继续固定：不得发送 NavigateToPose，不得发布 `/cmd_vel`，不得调用 `/api/base/manual`，不得打开 WAVE ROVER UART。

## OKR 映射和方向判断

- O5：`暂停`。虽然 O5 是当前最低约 `85%`，但当前缺口是 external production evidence；继续做 O5 support-only/readback/wrapper 不计分，也会重复消费同一 blocker。
- O3/O1：`继续`。本轮直接处理上轮留下的 lifecycle CLI timeout，是 current same-run path generation success 和 Nav2 route execution success 的前置条件。
- O6/O7：`不调整`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback 前，不安排 Full-stack surface、handoff、review 或 intake 小切片。
- KR 历史归档：本轮规划阶段不归档任何 KR；已完成 KR 历史区不更新。

方向判断：`继续` O3/O1 no-motion lifecycle CLI budget recovery；`暂停` O5 support-only；`不归档` KR；默认 `不调整` OKR 百分比。

## 本轮核心抓手

本轮核心抓手是让 `robot-software-engineer` 单 owner 在 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 及测试中增加 lifecycle CLI budget recovery、retry 与 command-summary 分层：

1. 区分 `lifecycle_command_timeout`、`inactive stdout`、`graph ok but lifecycle timeout`、`active`。
2. 对 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` 保留 command、timeout budget、stdout、stderr、returncode、elapsed 和 retry 结果。
3. lifecycle readback clean 后，才允许继续采集 `/scan_reliable_and_best_effort_timeout`、`/map_topic_missing`、`/tf_topic_missing`。
4. 仍不做 path generation 或 motion，必须保持 `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`。

## 范围和责任人

- Product owner：`product-okr-owner`，负责本 sprint 计划、验收口径、方向判断和收口边界。
- Implementation owner：`robot-software-engineer`，负责 helper、单测、navigation docs、raw artifact 和 `tech-done.md`。
- Hardware owner：本轮默认不介入。只有下一轮证据证明 LiDAR serial/runtime/接线事实时，才升级 `rober-hardware-engineer`，并必须先读 `docs/vendor/VENDOR_INDEX.md`。
- Algorithm owner：本轮默认不改代码；Robot Software 先把 source/runtime/lifecycle readback clean 后，再恢复 Algorithm 对 `/scan`、AMCL、TF 和 path readiness 的处理。

## 安全红线

本轮验收严格保持 no-motion：

- 禁止 NavigateToPose。
- 禁止发布 `/cmd_vel`。
- 禁止调用 `/api/base/manual`。
- 禁止打开或使用 WAVE ROVER UART。
- 禁止 route execution、delivery success、HIL pass 或 safe-to-control 宣称。
- 默认所有危险字段必须保持 `false`：`path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## 同一 Blocker 重复消费判断

本轮可以继续 O3/O1，但验收必须比 `07-53` 更窄，不能只重复"lifecycle timeout"。

不算重复消费的条件：

- artifact 新增 lifecycle command-summary / retry / budget 分层；
- 能明确区分 timeout 是 CLI 预算、graph visibility、inactive stdout、lifecycle manager 状态，还是 active 后的下游 topic/TF blocker；
- 如 timeout 仍存在，必须给出下一步精确 blocker，而不是再生成一层 wrapper。

不予验收为进展的情况：

- 只复述 `map_server_lifecycle_command_timeout` 与 `amcl_lifecycle_command_timeout`；
- 回退到 O5 support-only、source/path mismatch 或 `ros2 --help` readiness gate；
- 在 lifecycle readback 未 clean 时尝试 path generation、motion 或底盘控制。

## 需要创建或更新的 Sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Robot Software 实施后必须更新：`tech-done.md`。
- Product 验收后必须更新：`side2side_check.md`、`final.md`。
