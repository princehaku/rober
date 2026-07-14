# PRD - O6/O7 Bounded Route Gate Intake

## Product Goal

把同一 `task_id` 的 fail-closed controlled route execution gate 与 bounded route command plan 接入 O6/O7 主证据链，让运营人员能在 selected task 里看到路线执行前 gate 已验证了哪些材料、还缺哪些 live safety evidence，以及为什么当前仍不能控制小车。

该能力只作为 `software_proof_o6_o7_bounded_route_gate_material_intake_only`，不声明 route execution、delivery、HIL 或 safe-to-control 完成。

## Problem

O3/O1 已在 07:07 和 08:09 形成两个强相关材料：

- `controlled_route_execution_gate_record.json`：验证 28-pose same-task replay packet 的 identity/count/hash，并 fail-closed 在缺 live safety gate。
- `bounded_route_command_plan.json`：形成 27 段 bounded command plan、11 项 global abort criteria，并固定 `execution_plan_status=blocked_pending_live_safety_gate`。

但 O6/O7 selected-task 主路径还不能把这两个材料作为同一任务的 route-execution precursor 消费和回读。继续做 O5 CDN/TLS、bundle export、query/readback 或 phone/browser wrapper 都无法增强 route execution 证据链。

## Scope

In scope:

- O6 local/mock archive 新增 `bounded_route_execution_gate_material` 安全 section 或等价 consumer detail alias。
- O7 selected-task 主路径新增 bounded route gate intake action 和 receipt 展示。
- 只接受本机回环 O6 base URL。
- 只保留 safe metadata：`packet_id`、`task_id`、`route_intent_id`、route counts、`segment_count`、`execution_plan_status`、abort criteria count、safe refs、blocked reasons、next required evidence 和 fixed false fields。
- 文档同步到 O6/O7 interface 与 product docs。

Out of scope:

- 真实 route execution、fixed-route movement、NavigateToPose、controller/BT。
- `/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、串口、底盘控制。
- delivery/operator acceptance、真实 delivery success、current live HIL、safe-to-control。
- 生产 cloud、production DB/queue、OSS/CDN upload/origin fetch、4G/SIM。
- 重新执行 O5 CDN/TLS probe 或 readiness packet consumption。

## Functional Requirements

1. O6 archive/readback
   - 新 section 建议：`bounded_route_execution_gate_material`。
   - 接受 selected task 的 `task_id` / `robot_id`，并校验 safe refs、same-task identity 和 fixed false fields。
   - 材料必须保留 `execution_plan_status=blocked_pending_live_safety_gate` 或等价 blocked status。
   - 回读必须固定 `safe_to_control=false`、`delivery_success=false`、`route_execution_success=false`、`hil_pass=false`、`robot_control_executed=false`。
   - 任意 raw local path、raw command body、`/cmd_vel`、`/api/base/manual`、NavigateToPose、serial/UART、WAVE ROVER、`route_execution_success=true`、`delivery_success=true`、`hil_pass=true` 均 fail closed。

2. O7 selected-task intake
   - 新 endpoint 建议：`POST /api/o7/consumer-read/tasks/:taskId/bounded-route-gate/intake?baseUrl=<local-loopback-url>`。
   - Body 只允许安全摘要，不接受 raw route CSV、raw JSONL、raw command 或 raw artifact body。
   - Adapter 必须校验 path/body task id 一致、baseUrl local-loopback-only、dangerous true fields、safe refs、route counts 和 status allowlist。
   - 成功 receipt 建议 schema：`trashbot.pc_tools_workstation.o7_bounded_route_gate_intake_result.v1`。
   - Receipt status 只允许 `local_mock_bounded_route_gate_written`、`local_mock_bounded_route_gate_updated` 或 `fail_closed`。

3. O7 readback/display
   - Selected task detail 加载后展示 bounded route gate status、same-task identity、counts、segment count、abort criteria count 和 next required evidence。
   - UI 不显示完整 local path、raw route body、raw JSONL、command payload、UART 或截图/DOM 类材料。
   - 该 action 不启用 start delivery、confirm dropoff、cancel、ACK、control、Nav2 或任何 primary action。

## Product Acceptance Criteria

- O6 targeted unit tests pass.
- O7 workstation test/build/lint pass.
- `rg` anchors 命中 endpoint/schema/proof boundary/false fields/docs/tech-done。
- Hostile payload fail-closed：非回环 URL、task mismatch、dangerous true、raw local path、raw command、control/HIL true 字段均不能写入成功 receipt。
- 成功 receipt 和 O6 readback 均包含 `software_proof_o6_o7_bounded_route_gate_material_intake_only` 或同等 proof boundary。
- Product closeout 必须保持 O5/O1/O6/O7 主百分比不调整，除非后续真实 route/delivery/HIL/production evidence 另行到位。

## OKR Mapping And Direction Judgment

- O5 是当前最低 Objective，约 `85%`，但最新 blocker 是 `blocked_http_status_not_success_class`，本 sprint 不继续 O5 是有证据的调整。
- O6/O7 约 `93%`，本 sprint 选择 distinct same-task route-execution precursor material intake，方向判断为继续 O6/O7 证据链，但不归档 KR。
- 若 Engineer 只能产出 local/mock receipt，本轮仍是 support-only software proof；如果未来接入真实 route execution、delivery/operator acceptance、current live HIL 或 production cloud，再重新评估 OKR 提升。
