# Pre-Start - O3 Map Server On-Configure IO Order Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_14-54_o3_map_server_on_configure_io_order_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 14:54 CST`
- Target: true-board `/map_server` lifecycle clean/active, or a narrower strict no-motion root cause than `map_server_configure_return_failure_before_deferred_map_read_completed`

## 用户价值和产品北极星

用户价值是继续解除真实上位机 fixed-route/nav 的前置阻塞，让后续 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate 能回到同一现场证据链。产品北极星仍是普通手机用户一键发车送垃圾；本 sprint 只处理 `/map_server` lifecycle 前置 blocker，不交付路线执行、底盘运动、HIL、送达或生产云能力。

## 上轮事实输入

必须读取并以最近两个 sprint 的 closeout 为准：

- `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`
- `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`

13:54 accepted artifact 的当前事实：

- `proof.root_causes[0].reason=map_server_configure_return_failure_before_deferred_map_read_completed`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_configure_return_failure_before_deferred_map_read_completed`
- `runtime_log_window.events.map_read_after_state_change_failure=true`
- `runtime_log_window.dds_transport_error_text=""`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
- `/map_server` 仍未 lifecycle clean/active
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

## OKR 映射和方向判断

- O5 约 `85%`，仍是最低 Objective，但缺真实 production external evidence；继续 support-only packet、review、handoff、surface、readiness wrapper 不计分，方向为 `暂停 support-only`。
- O3/O1 strict no-motion 现场链路继续推进，因为 `/map_server` lifecycle 是 current same-run path generation 和 Nav2 route execution 的前置 blocker。
- O6/O7 继续等待 live route execution、delivery/operator 或 production readback；没有新材料时不新增 surface 工作。
- 本 sprint 默认 `不调整` OKR 百分比，`不归档` KR；只有出现 same-run path generation、route execution、current live HIL、delivery/operator acceptance 或 production external evidence，才由 Product Owner 在收口时重新判断。

## 本轮核心抓手

本轮抓手不是重复证明 configure failure，而是让 `robot-software-engineer` 沿源码与运行时 ordering 继续下钻：

1. 优先修复 `/map_server` lifecycle clean/active。
2. 如果不能修复，必须比 13:54 更窄地定位到 map_server `on_configure` return path、map IO completion ordering、lifecycle manager ChangeState response handling、executor timing、bond prerequisites、参数异常、源码异常或明确 RPC 行为。
3. 如果仍只重复 `map_server_configure_return_failure_before_deferred_map_read_completed` 且没有更窄 evidence，本 sprint 不可接受为进展，必须 `needs retry`；连续无法推进时下一步 `升级 CEO` 决策或切换 Objective。

## Strict No-Motion 红线

本 sprint 是 strict no-motion：

- 不得 NavigateToPose。
- 不得发布 `/cmd_vel`。
- 不得调用 `/api/base/manual`。
- 不得打开 WAVE ROVER UART。
- 不得修改硬件配置、串口、波特率、接线或 WAVE ROVER / ESP32 相关设置。
- 不得把 `/map_server` lifecycle clean/active 直接解释成 `safe_to_control=true`。

## Owner 和职责

- `product-okr-owner`：本轮只创建 `pre_start.md`、`prd.md`、`tech-plan.md`，定义用户价值、范围、验收口径和风险边界。
- `robot-software-engineer`：后续单 owner 闭环负责实现、测试、true-board strict no-motion 证明和 `tech-done.md` 留档。
- `robot-algorithm-engineer`：暂不介入；只有 `/map_server` lifecycle clean/active 后，才恢复 `/map`、AMCL、dynamic `map->odom` 和 planner-only path gate。
- `rober-hardware-engineer`：暂不介入；本轮不触碰 WAVE ROVER、ESP32、UART、串口、波特率或硬件配置。
- `full-stack-software-engineer`：不介入；本轮不改 API/UI/用户触点。

## 本轮验收口径

Accept：

- true-board artifact 证明 `/map_server` lifecycle clean/active；或
- true-board artifact 输出比 `map_server_configure_return_failure_before_deferred_map_read_completed` 更窄、可执行的 root cause。

Needs retry：

- artifact 仍只重复 `map_server_configure_return_failure_before_deferred_map_read_completed`，没有新的 callback、map IO、ChangeState、executor、bond、参数或源码级 evidence。
- primary blocker 被 cleanup/LiDAR/AMCL/TF/noise 覆盖，而不是 `/map_server` configure/root cause。

Reject：

- 发送 NavigateToPose、发布 `/cmd_vel`、调用 `/api/base/manual`、打开 WAVE ROVER UART、修改硬件配置，或把 no-motion proof 包装成 route execution / delivery / HIL。

## Sprint 文档计划

本阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续 Robot Software 实施完成后必须更新：

- `tech-done.md`
- `artifacts/`

Product 验收阶段再更新：

- `side2side_check.md`
- `final.md`
