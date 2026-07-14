# Pre Start - O3 Map Server On-Configure Return Source Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned start time: `2026-07-12 16:55 CST`
- Target objective: O3/O1 strict no-motion field lane
- Product status: ready for Robot Software implementation
- Proof boundary: planned `software_proof_o3_o1_strict_no_motion_map_server_on_configure_return_source_repair_only`

## Read-First Evidence

本轮开工前已读取并采用以下证据：

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/final.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/side2side_check.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/tech-done.md`
- `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/final.md`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/final.md`

## 用户价值和产品北极星

用户价值仍是把真实上位机 fixed-route/nav 链路推到可生成同 run path、后续可执行路线、最终可送达垃圾。`/map_server` lifecycle clean/active 是 `/map`、AMCL、dynamic `map->odom`、planner-only path generation 和 route execution 的上游 gate。

产品北极星仍是普通手机用户一键发车送垃圾。本 sprint 不交付手机新能力、不交付底盘运动、不交付送达能力，只推进真实现场 no-motion 链路中 `/map_server` configure failure 的最短解阻路径。

## OKR 映射和方向判断

- O5 当前约 `85%`，是数字最低项，但缺真实 external production evidence。继续做 O5 support-only packet、review、handoff、surface 或 readiness wrapper 会重复消费 `no_real_production_external_evidence` blocker，因此本轮暂停 O5 support-only。
- O1 当前约 `93%`，主要缺口包含 current same-run path generation success 与 Nav2 route execution success。本轮通过 O3 strict no-motion field lane 解除 `/map_server` lifecycle blocker，服务 O1 的 path/route evidence gate。
- O3 是已归档 Objective 的现场验证 lane，本轮临时激活，只允许作为 no-motion supporting evidence，不恢复为已完成 KR，也不自动提升 OKR 百分比。
- O6/O7 当前约 `93%`，等待 live route execution、delivery/operator 或 production readback；本轮不做触点 surface。

方向判断：继续 O3/O1 strict no-motion field lane；暂停 O5 support-only；不调整 OKR 百分比；不归档 KR。

## 上轮 Blocker 摘要

15:54 最新 accepted root cause：

- `map_server_changestate_response_false_before_map_io_completion`
- `lifecycle_manager_changestate_response_false_while_map_io_completed_later`

已知事实：

- lifecycle manager 已请求 configure。
- `/map_server` configure callback 已进入。
- YAML/image load 已开始。
- ChangeState response false 发生在 map IO 尚未完成的窗口内。
- map read 后续完成，且没有 service timeout 或 RPC error log。
- `/map_server active=false`。
- `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`calls_base_manual=false`、`uses_base_uart=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 同一 Blocker 红线

本轮不能只重复 15:54 的 root cause。如果工程输出仍只是 `map_server_changestate_response_false_before_map_io_completion`，且没有证明 `/map_server active`，也没有把 `on_configure` return false source、参数、异常、executor/service future、map IO sync/async ordering 或 lifecycle manager response handling 继续收窄，则 Product 验收失败并要求 Robot Software 返工。

如果返工后仍重复同一 blocker，下一轮必须二选一：

- 升级 CEO 请求方向决策；或
- 切换到不重复消费该 blocker 的 Objective。

## Owner 边界

- 主责 owner：`robot-software-engineer`。
- Algorithm 只能在 `/map_server` lifecycle clean/active 后介入 `/map`、AMCL、TF、planner path 或 route execution。
- Hardware 只有在 LiDAR serial/runtime/wiring 成为 primary root cause 时介入；届时必须先读 `docs/vendor/VENDOR_INDEX.md`，并以本地 vendor 资料为准。
- Full-Stack 不介入，本轮没有手机/Web/API/UI 交付。

## 严格 No-Motion 边界

本轮禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART
- 声称 safe-to-control、route execution、delivery、HIL 或 production success

安全和 mission booleans 必须 fail-closed，包括但不限于 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## 本轮核心抓手

Robot Software 需要 inspect/fix/narrow Nav2 map_server `on_configure` return false path，并解释为什么 lifecycle manager 在 map IO 尚未完成时拿到 ChangeState response false。优先抓手包括：

- `on_configure` 返回 `CallbackReturn::FAILURE` 的直接来源。
- map YAML/image 参数、路径、mode、metadata 或 image decode 异常。
- map IO sync/async ordering 与日志落点是否造成误判。
- executor/service future timing 是否提前返回 failure。
- lifecycle manager response handling 是否把 callback 中间态当成 terminal failure。
- 如果可以小修，则证明 `/map_server active=true`；如果不能小修，则输出比 15:54 更窄、可由下一轮直接修复的 primary root cause。

## 需要创建或更新的 Sprint 文档

本轮当前只创建产品计划三件套：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

工程完成后再由对应 owner 更新 `tech-done.md`；Product closeout 时再更新 `side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。
