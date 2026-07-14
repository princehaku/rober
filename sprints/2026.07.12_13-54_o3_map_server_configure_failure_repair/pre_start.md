# Pre Start - O3 Map Server Configure Failure Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_13-54_o3_map_server_configure_failure_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 13:54 CST`
- Target Objective: O3/O1 strict no-motion real-board localization/path prerequisite
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_configure_failure_repair_only`

## 上轮输入

上一轮 `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/` 已接受为 O3/O1 strict no-motion blocker narrowing only。最新 true-board artifact 明确：

- `proof.root_causes[0].reason=map_server_configure_callback_return_failure`
- `proof.root_causes[0].detail=lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed`
- `proof.map_server_transition_callback_probe.transition_sequence.observed_stage=configure`
- `service_rpc_timing.inferred_change_state_response=failure`
- `bond_timing.bond_stage=not_created_before_configure_return_failure`
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

## 本轮选择理由

O5 仍是当前最低 Objective，约 `85%`，但只靠真实 production external evidence 才可计分；继续 readiness packet、support-only wrapper 或 UI/readback 不应再提升 OKR。本轮继续 O3/O1 no-motion，是因为 `/map_server` lifecycle clean 是 current same-run path generation 与 Nav2 route execution 的前置条件。

本轮不是继续包装泛化 lifecycle blocker；必须修复 `/map_server` configure failure，或输出比 `map_server_configure_callback_return_failure` 更窄的 root cause。

## 同一 Blocker 红线

最近两轮 blocker 已从：

- `map_server_activate_callback_failed`
- `map_server_configure_callback_return_failure`

继续收窄。本轮允许继续一次，因为目标是具体 configure callback / ChangeState RPC / map IO / executor timing 层。若本轮仍停在完全相同 `map_server_configure_callback_return_failure` 且没有更窄参数、异常、map IO、RPC 或 executor evidence，下一轮必须升级 CEO 决策或切 Objective。

## Owner 和范围

单 owner：`robot-software-engineer`。

不派 Algorithm：`/map_server` lifecycle 未 clean 前，AMCL、TF 和 planner-only path gate 还不能成为主责。

不派 Hardware：本轮不触碰 WAVE ROVER、ESP32、UART、串口、波特率、接线或硬件配置。若实现中出现硬件事实依赖，必须停止并改派 Hardware 读取 `docs/vendor/VENDOR_INDEX.md`。

## 验收边界

接受条件：

- true-board artifact 证明 `/map_server` lifecycle clean/active；或
- true-board artifact 输出比 `map_server_configure_callback_return_failure` 更窄的 configure callback exception、parameter、map IO ordering、ChangeState RPC、executor timing 或 bond prerequisite root cause。

禁止条件：

- 不发送 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不把 `/map_server` active 误写成 safe-to-control、route execution 或 delivery success。
